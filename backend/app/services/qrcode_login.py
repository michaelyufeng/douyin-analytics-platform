"""
QR Code Login Service for Douyin using Playwright.
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
Object.defineProperty(navigator, "hardwareConcurrency", {get: () => 8, configurable: true});
Object.defineProperty(navigator, "deviceMemory", {get: () => 8, configurable: true});
window.chrome = {runtime:{connect:()=>{},sendMessage:()=>{},onMessage:{addListener:()=>{}}},loadTimes:()=>{},csi:()=>{},app:{}};
"""


class QRCodeLoginService:
    DOUYIN_LOGIN_URL = "https://www.douyin.com/"

    QR_CODE_SELECTORS = [
        "div#login-pannel img",
        'div[class*="qrcode"] img',
        'div[class*="QRCode"] img',
        "div.login-pannel img",
        'div[class*="web-login"] img',
        'div[class*="scan-code"] img',
        'img[class*="qrcode"]',
        'img[alt*="二维码"]',
        "canvas",
    ]

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

                logger.info("Navigating to Douyin...")
                await self.page.goto(self.DOUYIN_LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)

                # Save initial screenshot
                await self.page.screenshot(path=f"/tmp/douyin_1_initial_{session_id}.png")

                # Click login button - try multiple methods
                logger.info("Clicking login button...")
                try:
                    # Method 1: Direct click on login button in header
                    login_btn = self.page.locator("text=登录").first
                    await login_btn.click(timeout=5000)
                    logger.info("Clicked login via locator")
                except Exception as e:
                    logger.debug(f"Locator click failed: {e}")
                    # Method 2: JavaScript click
                    await self.page.evaluate("""() => {
                        const btns = document.querySelectorAll("button, div, span, a");
                        for (const btn of btns) {
                            if (btn.innerText === "登录" && btn.offsetParent !== null) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    }""")
                    logger.info("Clicked login via JS")

                await asyncio.sleep(3)
                await self.page.screenshot(path=f"/tmp/douyin_2_after_login_{session_id}.png")

                # Try to click QR code tab
                logger.info("Looking for QR tab...")
                try:
                    qr_tab = self.page.locator("text=扫码登录").first
                    await qr_tab.click(timeout=3000)
                    logger.info("Clicked QR tab")
                except Exception:
                    await self.page.evaluate("""() => {
                        const els = document.querySelectorAll("*");
                        for (const el of els) {
                            if (el.innerText && el.innerText.includes("扫码") && el.offsetParent) {
                                el.click();
                                return true;
                            }
                        }
                        return false;
                    }""")

                await asyncio.sleep(2)
                await self.page.screenshot(path=f"/tmp/douyin_3_qr_tab_{session_id}.png")

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
                    # Fallback: return full screenshot
                    screenshot_path = f"/tmp/douyin_3_qr_tab_{session_id}.png"
                    with open(screenshot_path, "rb") as f:
                        screenshot_base64 = base64.b64encode(f.read()).decode()
                    login_sessions[session_id] = {
                        "status": "waiting", "qr_image": screenshot_base64,
                        "created_at": datetime.now(), "service": self, "playwright": playwright
                    }
                    return {"success": True, "session_id": session_id, "qr_image": screenshot_base64,
                            "message": "请在页面中找到二维码并使用抖音 App 扫描登录"}

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                await self.cleanup()
                if attempt < max_retries - 1:
                    await asyncio.sleep((attempt + 1) * 2)

        return {"success": False, "error": str(last_error), "message": "启动登录会话失败"}

    async def _capture_qr_code(self, session_id: str) -> Optional[str]:
        try:
            for selector in self.QR_CODE_SELECTORS:
                try:
                    logger.debug(f"Trying selector: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=3000, state="visible")
                    if element:
                        box = await element.bounding_box()
                        if box and box["width"] > 80 and box["height"] > 80:
                            w = box["width"]
                            h = box["height"]
                            logger.info(f"Found QR with: {selector}, size: {w}x{h}")
                            screenshot = await element.screenshot()
                            return base64.b64encode(screenshot).decode()
                except Exception as e:
                    logger.debug(f"Selector failed: {e}")
                    continue

            # Fallback: find square images
            images = await self.page.query_selector_all("img")
            for img in images:
                try:
                    box = await img.bounding_box()
                    if box and 100 < box["width"] < 400 and 100 < box["height"] < 400:
                        src = await img.get_attribute("src") or ""
                        if "data:image" in src or "qr" in src.lower():
                            screenshot = await img.screenshot()
                            return base64.b64encode(screenshot).decode()
                except Exception:
                    continue

            logger.warning("Could not find QR code")
            return None
        except Exception as e:
            logger.error(f"Failed to capture QR: {e}")
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
            is_logged_in = False
            try:
                ls = await service.page.evaluate("() => window.localStorage")
                if ls and ls.get("HasUserLogin") == "1":
                    is_logged_in = True
            except Exception:
                pass

            cookies = await service.context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            if cookie_dict.get("LOGIN_STATUS") == "1" or cookie_dict.get("sessionid"):
                is_logged_in = True

            if is_logged_in:
                cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                session["status"] = "success"
                session["cookie"] = cookie_string
                await self._save_cookie(cookie_string)
                await self.cleanup_session(session_id)
                return {"status": "success", "message": "登录成功！Cookie已保存",
                        "cookie": cookie_string[:100] + "..." if len(cookie_string) > 100 else cookie_string}

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
            logger.error(f"Failed to save cookie: {e}")

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
        return {"status": "expired", "message": "登录会话不存在或已过期"}
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
