"""
QR Code Login Service for Douyin using Playwright.
Uses creator.douyin.com which has QR code login.
"""
import asyncio
import base64
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

from loguru import logger

login_sessions: Dict[str, Dict[str, Any]] = {}
ESSENTIAL_COOKIES = ["sessionid", "sessionid_ss", "ttwid", "LOGIN_STATUS"]

STEALTH_JS = """
Object.defineProperty(navigator, "webdriver", {get: () => undefined, configurable: true});
Object.defineProperty(navigator, "plugins", {
    get: () => {
        const p = [{name:"Chrome PDF Plugin"},{name:"Chrome PDF Viewer"},{name:"Native Client"}];
        p.item = (i) => p[i]; p.namedItem = (n) => p.find(x => x.name === n); p.refresh = () => {};
        return p;
    }, configurable: true
});
Object.defineProperty(navigator, "languages", {get: () => ["zh-CN","zh","en-US","en"], configurable: true});
Object.defineProperty(navigator, "platform", {get: () => "Win32", configurable: true});
window.chrome = {runtime:{connect:()=>{},sendMessage:()=>{},onMessage:{addListener:()=>{}}},loadTimes:()=>{},csi:()=>{},app:{}};
"""


class QRCodeLoginService:
    # Use creator platform - has QR code login
    DOUYIN_LOGIN_URL = "https://creator.douyin.com/"

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def start_login_session(self, session_id: str, max_retries: int = 3) -> Dict[str, Any]:
        last_error = None
        display = os.environ.get("DISPLAY")
        use_headless = display is None

        if use_headless:
            try:
                import subprocess
                result = subprocess.run(["pgrep", "-x", "Xvfb"], capture_output=True, text=True)
                if result.returncode == 0:
                    os.environ["DISPLAY"] = ":99"
                    use_headless = False
                    logger.info("Detected Xvfb, setting DISPLAY=:99")
            except Exception:
                pass

        for attempt in range(max_retries):
            try:
                from playwright.async_api import async_playwright

                logger.info(f"Starting QR login session: {session_id} (attempt {attempt + 1}/{max_retries})")
                playwright = await async_playwright().start()

                chrome_ver = random.randint(120, 130)
                ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/{chrome_ver}.0.0.0 Safari/537.36"

                self.browser = await playwright.chromium.launch(
                    headless=use_headless,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled",
                          "--disable-dev-shm-usage", "--window-size=1920,1080", f"--user-agent={ua}"]
                )

                self.context = await self.browser.new_context(
                    user_agent=ua, viewport={"width": 1920, "height": 1080},
                    locale="zh-CN", timezone_id="Asia/Shanghai"
                )
                await self.context.add_init_script(STEALTH_JS)
                self.page = await self.context.new_page()

                logger.info("Navigating to Douyin Creator...")
                await self.page.goto(self.DOUYIN_LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5)

                await self.page.screenshot(path=f"/tmp/step1_creator_{session_id}.png")
                logger.info("Step 1: Page loaded")

                # Click "我是创作者" button/tab using JavaScript (more reliable)
                clicked_creator = await self.page.evaluate("""() => {
                    const els = document.querySelectorAll('*');
                    for (const el of els) {
                        const text = el.innerText || el.textContent || '';
                        if (text.trim() === '我是创作者' && el.offsetParent !== null) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }""")
                if clicked_creator:
                    logger.info("Clicked '我是创作者' via JS")
                    await asyncio.sleep(3)

                # Click "扫码登录" tab using JavaScript (this triggers QR code loading)
                clicked_qr = await self.page.evaluate("""() => {
                    const els = document.querySelectorAll('*');
                    for (const el of els) {
                        const text = el.innerText || el.textContent || '';
                        if (text.trim() === '扫码登录' && el.offsetParent !== null && el.offsetWidth > 20) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }""")
                if clicked_qr:
                    logger.info("Clicked '扫码登录' tab via JS")
                    await asyncio.sleep(3)

                await self.page.screenshot(path=f"/tmp/step2_afterlogin_{session_id}.png")

                # Wait for QR code to actually load - poll until canvas has content
                logger.info("Waiting for QR code to load...")
                for wait_attempt in range(10):
                    await asyncio.sleep(2)
                    # Check if any canvas has actual content
                    has_qr = await self.page.evaluate("""() => {
                        const canvases = document.querySelectorAll('canvas');
                        for (const canvas of canvases) {
                            if (canvas.width > 100 && canvas.height > 100) {
                                const ctx = canvas.getContext('2d');
                                if (ctx) {
                                    const data = ctx.getImageData(0, 0, 10, 10).data;
                                    // Check if there's actual pixel data (not all zeros)
                                    for (let i = 0; i < data.length; i++) {
                                        if (data[i] !== 0 && data[i] !== 255) return true;
                                    }
                                }
                            }
                        }
                        return false;
                    }""")
                    if has_qr:
                        logger.info(f"QR code loaded after {(wait_attempt + 1) * 2} seconds")
                        break
                    logger.debug(f"QR not ready yet, waiting... ({wait_attempt + 1}/10)")

                await self.page.screenshot(path=f"/tmp/step3_qrpage_{session_id}.png")
                logger.info("Step 3: Looking for QR code")

                # Capture QR code
                qr_image_base64 = await self._capture_qr_code(session_id)

                if qr_image_base64:
                    login_sessions[session_id] = {
                        "status": "waiting", "qr_image": qr_image_base64,
                        "created_at": datetime.now(), "service": self, "playwright": playwright
                    }
                    return {"success": True, "session_id": session_id, "qr_image": qr_image_base64,
                            "message": "请使用抖音 App 扫描二维码登录"}
                else:
                    screenshot_path = f"/tmp/step3_qrpage_{session_id}.png"
                    with open(screenshot_path, "rb") as f:
                        screenshot_base64 = base64.b64encode(f.read()).decode()
                    login_sessions[session_id] = {
                        "status": "waiting", "qr_image": screenshot_base64,
                        "created_at": datetime.now(), "service": self, "playwright": playwright
                    }
                    return {"success": True, "session_id": session_id, "qr_image": screenshot_base64,
                            "message": "请在页面中找到二维码并扫描登录"}

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                await self.cleanup()
                if attempt < max_retries - 1:
                    await asyncio.sleep((attempt + 1) * 2)

        return {"success": False, "error": str(last_error), "message": "启动登录会话失败"}

    async def _capture_qr_code(self, session_id: str) -> Optional[str]:
        """Capture QR code image - must be actual QR code, not decorative images."""
        try:
            # Method 1: Look for img elements with data:image src (most reliable for QR codes)
            logger.info("Looking for QR code images...")
            images = await self.page.query_selector_all("img")
            for img in images:
                try:
                    box = await img.bounding_box()
                    if box and 140 < box["width"] < 320 and 140 < box["height"] < 320:
                        ratio = box["width"] / box["height"]
                        if 0.9 < ratio < 1.1:
                            src = await img.get_attribute("src") or ""
                            # Real QR codes as base64 PNG are typically > 2000 chars
                            # The QR code we need should be a large data:image
                            if src.startswith("data:image/png") and len(src) > 2000:
                                logger.info(f"Found QR image: {box['width']:.0f}x{box['height']:.0f}, src length: {len(src)}")
                                screenshot = await img.screenshot()
                                return base64.b64encode(screenshot).decode()
                except Exception:
                    continue

            # Method 2: Look for canvas that contains actual QR code (black/white pattern)
            logger.info("Looking for QR code canvas...")
            canvases = await self.page.query_selector_all("canvas")
            for canvas in canvases:
                try:
                    box = await canvas.bounding_box()
                    if box and 140 < box["width"] < 320 and 140 < box["height"] < 320:
                        ratio = box["width"] / box["height"]
                        if 0.9 < ratio < 1.1:
                            # Check if canvas has QR-like content (black and white, not colorful)
                            is_qr = await self.page.evaluate("""(canvas) => {
                                const ctx = canvas.getContext('2d');
                                if (!ctx) return false;
                                const w = canvas.width, h = canvas.height;
                                const data = ctx.getImageData(0, 0, w, h).data;
                                let blackCount = 0, whiteCount = 0, colorCount = 0;
                                for (let i = 0; i < data.length; i += 4) {
                                    const r = data[i], g = data[i+1], b = data[i+2];
                                    if (r < 50 && g < 50 && b < 50) blackCount++;
                                    else if (r > 200 && g > 200 && b > 200) whiteCount++;
                                    else colorCount++;
                                }
                                const total = w * h;
                                // QR codes are mostly black and white with very few colors
                                return (blackCount + whiteCount) / total > 0.9 && colorCount / total < 0.1;
                            }""", canvas)
                            if is_qr:
                                logger.info(f"Found QR canvas (verified): {box['width']:.0f}x{box['height']:.0f}")
                                screenshot = await canvas.screenshot()
                                return base64.b64encode(screenshot).decode()
                            else:
                                logger.debug(f"Canvas {box['width']:.0f}x{box['height']:.0f} is decorative, skipping")
                except Exception as e:
                    logger.debug(f"Canvas check failed: {e}")
                    continue

            # Method 3: Look for img in QR-specific containers
            logger.info("Looking for QR code in containers...")
            qr_selectors = [
                'div[class*="qrcode"] img',
                'div[class*="QRCode"] img',
                'div[class*="qr-code"] img',
            ]
            for selector in qr_selectors:
                try:
                    elements = self.page.locator(selector)
                    count = await elements.count()
                    for i in range(count):
                        el = elements.nth(i)
                        box = await el.bounding_box()
                        if box and 140 < box["width"] < 320 and 140 < box["height"] < 320:
                            src = await el.get_attribute("src") or ""
                            if src.startswith("data:image") and len(src) > 2000:
                                logger.info(f"Found QR in container: {selector}")
                                screenshot = await el.screenshot()
                                return base64.b64encode(screenshot).decode()
                except Exception:
                    continue

            logger.warning("QR code not found - page may not have loaded QR code")
            return None
        except Exception as e:
            logger.error(f"Capture error: {e}")
            return None

    async def check_login_status(self, session_id: str) -> Dict[str, Any]:
        session = login_sessions.get(session_id)
        if not session:
            return {"status": "expired", "message": "登录会话已过期"}

        if datetime.now() - session["created_at"] > timedelta(minutes=5):
            await self.cleanup_session(session_id)
            return {"status": "expired", "message": "登录会话已过期"}

        service = session.get("service")
        if not service or not service.page:
            return {"status": "error", "message": "登录会话异常"}

        try:
            cookies = await service.context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}

            is_logged_in = False
            if cookie_dict.get("LOGIN_STATUS") == "1":
                is_logged_in = True
            if cookie_dict.get("sessionid"):
                is_logged_in = True

            if is_logged_in:
                cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                session["status"] = "success"
                await self._save_cookie(cookie_string)
                await self.cleanup_session(session_id)
                return {"status": "success", "message": "登录成功！Cookie已保存",
                        "cookie": cookie_string[:100] + "..."}

            return {"status": "waiting", "message": "等待扫码..."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _save_cookie(self, cookie: str):
        try:
            env_path = Path(__file__).parent.parent.parent / ".env"
            env_content = ""
            if env_path.exists():
                with open(env_path, "r") as f:
                    env_content = f.read()

            if "DOUYIN_COOKIE=" in env_content:
                lines = env_content.split("\n")
                new_lines = [f'DOUYIN_COOKIE="{cookie}"' if l.startswith("DOUYIN_COOKIE=") else l for l in lines]
                env_content = "\n".join(new_lines)
            else:
                env_content += f'\nDOUYIN_COOKIE="{cookie}"\n'

            with open(env_path, "w") as f:
                f.write(env_content)
            logger.info("Cookie saved")
            from app.config import settings
            settings.douyin_cookie = cookie
        except Exception as e:
            logger.error(f"Save error: {e}")

    async def cleanup_session(self, session_id: str):
        session = login_sessions.pop(session_id, None)
        if session:
            service = session.get("service")
            if service:
                await service.cleanup()
            playwright = session.get("playwright")
            if playwright:
                await playwright.stop()

    async def cleanup(self):
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


qrcode_login_service = QRCodeLoginService()

async def create_login_session() -> Dict[str, Any]:
    session_id = str(uuid.uuid4())
    service = QRCodeLoginService()
    return await service.start_login_session(session_id)

async def check_session_status(session_id: str) -> Dict[str, Any]:
    session = login_sessions.get(session_id)
    if not session:
        return {"status": "expired", "message": "会话不存在"}
    service = session.get("service")
    if service:
        return await service.check_login_status(session_id)
    return {"status": "error", "message": "会话异常"}

async def cancel_login_session(session_id: str):
    session = login_sessions.get(session_id)
    if session:
        service = session.get("service")
        if service:
            await service.cleanup_session(session_id)
