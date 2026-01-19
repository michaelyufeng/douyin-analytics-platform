"""
QR Code Login Service for Douyin using Playwright.
Allows users to scan QR code with Douyin app to automatically obtain cookies.
"""
import asyncio
import base64
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

from loguru import logger

# Store active login sessions
login_sessions: Dict[str, Dict[str, Any]] = {}


class QRCodeLoginService:
    """Service for handling QR code login flow."""

    DOUYIN_LOGIN_URL = "https://www.douyin.com/"
    QR_CODE_SELECTOR = "div.qrcode-image img, div.web-login-scan-code img, img[alt*='二维码'], canvas.qrcode"
    LOGIN_SUCCESS_INDICATOR = "//div[contains(@class, 'avatar')]"

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def start_login_session(self, session_id: str) -> Dict[str, Any]:
        """
        Start a new QR code login session.
        Returns the QR code image as base64.
        """
        try:
            from playwright.async_api import async_playwright

            logger.info(f"Starting QR code login session: {session_id}")

            # Initialize Playwright
            playwright = await async_playwright().start()

            # Launch browser (headless mode)
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            # Create context with common user agent
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )

            # Create page
            self.page = await self.context.new_page()

            # Navigate to Douyin
            logger.info("Navigating to Douyin...")
            await self.page.goto(self.DOUYIN_LOGIN_URL, wait_until="networkidle", timeout=60000)

            # Wait a bit for page to stabilize
            await asyncio.sleep(2)

            # Try to click login button if exists
            try:
                login_btn = await self.page.query_selector("button:has-text('登录'), div:has-text('登录'):not(:has(*))")
                if login_btn:
                    await login_btn.click()
                    await asyncio.sleep(2)
            except Exception as e:
                logger.debug(f"No login button found or click failed: {e}")

            # Try to find and click QR code login tab
            try:
                qr_tab = await self.page.query_selector("div:has-text('扫码登录'), span:has-text('扫码登录')")
                if qr_tab:
                    await qr_tab.click()
                    await asyncio.sleep(2)
            except Exception as e:
                logger.debug(f"No QR tab found: {e}")

            # Take screenshot of the page for debugging
            screenshot_path = f"/tmp/douyin_login_{session_id}.png"
            await self.page.screenshot(path=screenshot_path, full_page=False)

            # Try to capture QR code
            qr_image_base64 = await self._capture_qr_code()

            if qr_image_base64:
                # Store session info
                login_sessions[session_id] = {
                    "status": "waiting",
                    "qr_image": qr_image_base64,
                    "created_at": datetime.now(),
                    "service": self,
                    "playwright": playwright
                }

                return {
                    "success": True,
                    "session_id": session_id,
                    "qr_image": qr_image_base64,
                    "message": "请使用抖音 App 扫描二维码登录"
                }
            else:
                # If can't find QR code, return the screenshot
                with open(screenshot_path, "rb") as f:
                    screenshot_base64 = base64.b64encode(f.read()).decode()

                login_sessions[session_id] = {
                    "status": "waiting",
                    "qr_image": screenshot_base64,
                    "created_at": datetime.now(),
                    "service": self,
                    "playwright": playwright
                }

                return {
                    "success": True,
                    "session_id": session_id,
                    "qr_image": screenshot_base64,
                    "message": "请在页面中找到二维码并使用抖音 App 扫描登录"
                }

        except Exception as e:
            logger.error(f"Failed to start login session: {e}")
            await self.cleanup()
            return {
                "success": False,
                "error": str(e),
                "message": "启动登录会话失败，请确保服务器已安装 Playwright 浏览器"
            }

    async def _capture_qr_code(self) -> Optional[str]:
        """Capture QR code image from the page."""
        try:
            # Try different selectors for QR code
            selectors = [
                "div.qrcode-image img",
                "div.web-login-scan-code img",
                "img[alt*='二维码']",
                "img[src*='qrcode']",
                "canvas.qrcode",
                "div[class*='qrcode'] img",
                "div[class*='QRCode'] img",
                "#qrcode img",
                "div.login-qrcode img"
            ]

            for selector in selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        # Get bounding box
                        box = await element.bounding_box()
                        if box and box["width"] > 50 and box["height"] > 50:
                            # Screenshot the element
                            screenshot = await element.screenshot()
                            return base64.b64encode(screenshot).decode()
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            # If no specific QR code found, try to find any reasonably sized image
            images = await self.page.query_selector_all("img")
            for img in images:
                try:
                    box = await img.bounding_box()
                    if box and 100 < box["width"] < 400 and 100 < box["height"] < 400:
                        src = await img.get_attribute("src")
                        if src and ("qr" in src.lower() or "code" in src.lower() or "login" in src.lower()):
                            screenshot = await img.screenshot()
                            return base64.b64encode(screenshot).decode()
                except:
                    continue

            return None

        except Exception as e:
            logger.error(f"Failed to capture QR code: {e}")
            return None

    async def check_login_status(self, session_id: str) -> Dict[str, Any]:
        """Check if user has scanned and logged in."""
        session = login_sessions.get(session_id)
        if not session:
            return {"status": "expired", "message": "登录会话已过期"}

        # Check if session is too old (5 minutes timeout)
        if datetime.now() - session["created_at"] > timedelta(minutes=5):
            await self.cleanup_session(session_id)
            return {"status": "expired", "message": "登录会话已过期，请重新获取二维码"}

        service = session.get("service")
        if not service or not service.page:
            return {"status": "error", "message": "登录会话异常"}

        try:
            # Check for login success indicators
            # Look for user avatar, nickname, or changed page content

            # Method 1: Check if cookie contains key login indicators
            cookies = await service.context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}

            # Douyin uses these cookies after login
            login_cookies = ["sessionid", "sessionid_ss", "passport_csrf_token", "ttwid"]
            has_login_cookie = any(c in cookie_dict for c in login_cookies if cookie_dict.get(c))

            if has_login_cookie and cookie_dict.get("sessionid"):
                # User is logged in! Extract cookies
                cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

                # Update session status
                session["status"] = "success"
                session["cookie"] = cookie_string

                # Save cookie to config file
                await self._save_cookie(cookie_string)

                # Cleanup
                await self.cleanup_session(session_id)

                return {
                    "status": "success",
                    "message": "登录成功！Cookie 已自动保存",
                    "cookie": cookie_string[:100] + "..." if len(cookie_string) > 100 else cookie_string
                }

            # Method 2: Check page content for login success
            try:
                # Check if page has navigated away from login or shows user info
                current_url = service.page.url
                page_content = await service.page.content()

                if "login" not in current_url.lower() and ("头像" in page_content or "avatar" in page_content.lower()):
                    # Might be logged in, check cookies again
                    pass
            except:
                pass

            return {"status": "waiting", "message": "等待扫码..."}

        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return {"status": "error", "message": str(e)}

    async def _save_cookie(self, cookie: str):
        """Save cookie to .env file."""
        try:
            env_path = Path(__file__).parent.parent.parent / ".env"

            # Read existing .env content
            env_content = ""
            if env_path.exists():
                with open(env_path, "r") as f:
                    env_content = f.read()

            # Update or add DOUYIN_COOKIE
            if "DOUYIN_COOKIE=" in env_content:
                lines = env_content.split("\n")
                new_lines = []
                for line in lines:
                    if line.startswith("DOUYIN_COOKIE="):
                        new_lines.append(f'DOUYIN_COOKIE="{cookie}"')
                    else:
                        new_lines.append(line)
                env_content = "\n".join(new_lines)
            else:
                env_content += f'\nDOUYIN_COOKIE="{cookie}"\n'

            # Write back
            with open(env_path, "w") as f:
                f.write(env_content)

            logger.info("Cookie saved to .env file")

            # Also update runtime config
            from app.config import settings
            settings.douyin_cookie = cookie

        except Exception as e:
            logger.error(f"Failed to save cookie: {e}")

    async def cleanup_session(self, session_id: str):
        """Clean up a specific session."""
        session = login_sessions.pop(session_id, None)
        if session:
            service = session.get("service")
            if service:
                await service.cleanup()
            playwright = session.get("playwright")
            if playwright:
                await playwright.stop()

    async def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global service instance
qrcode_login_service = QRCodeLoginService()


async def create_login_session() -> Dict[str, Any]:
    """Create a new login session and return QR code."""
    session_id = str(uuid.uuid4())
    service = QRCodeLoginService()
    return await service.start_login_session(session_id)


async def check_session_status(session_id: str) -> Dict[str, Any]:
    """Check the status of a login session."""
    session = login_sessions.get(session_id)
    if not session:
        return {"status": "expired", "message": "登录会话不存在或已过期"}

    service = session.get("service")
    if service:
        return await service.check_login_status(session_id)

    return {"status": "error", "message": "会话异常"}


async def cancel_login_session(session_id: str):
    """Cancel and cleanup a login session."""
    session = login_sessions.get(session_id)
    if session:
        service = session.get("service")
        if service:
            await service.cleanup_session(session_id)
