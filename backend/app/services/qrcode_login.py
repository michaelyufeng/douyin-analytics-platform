"""
QR Code Login Service for Douyin using Playwright.
Allows users to scan QR code with Douyin app to automatically obtain cookies.

Based on MediaCrawler's proven approach for Douyin login.
Optimized with anti-detection measures for server-side operation with xvfb.
"""
import asyncio
import base64
import json
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

from loguru import logger

# Store active login sessions
login_sessions: Dict[str, Dict[str, Any]] = {}

# Essential cookies that must be present for successful login
ESSENTIAL_COOKIES = ["sessionid", "sessionid_ss", "ttwid", "LOGIN_STATUS"]

# Anti-detection stealth script - removes webdriver fingerprints
STEALTH_JS = """
// Remove webdriver property
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
    configurable: true
});

// Override navigator.plugins to look like a real browser
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const plugins = [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
        ];
        plugins.item = (i) => plugins[i];
        plugins.namedItem = (name) => plugins.find(p => p.name === name);
        plugins.refresh = () => {};
        return plugins;
    },
    configurable: true
});

// Override navigator.languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en-US', 'en'],
    configurable: true
});

// Override navigator.platform
Object.defineProperty(navigator, 'platform', {
    get: () => 'Win32',
    configurable: true
});

// Override navigator.hardwareConcurrency
Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => 8,
    configurable: true
});

// Override navigator.deviceMemory
Object.defineProperty(navigator, 'deviceMemory', {
    get: () => 8,
    configurable: true
});

// Remove automation-related properties from window
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

// Override chrome runtime
window.chrome = {
    runtime: {
        connect: () => {},
        sendMessage: () => {},
        onMessage: { addListener: () => {} }
    },
    loadTimes: () => {},
    csi: () => {},
    app: {}
};

// Override Permissions API
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// Canvas fingerprint randomization
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function(type) {
    if (type === 'image/png' || type === undefined) {
        const context = this.getContext('2d');
        if (context) {
            const imageData = context.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] = imageData.data[i] ^ 1;
            }
            context.putImageData(imageData, 0, 0);
        }
    }
    return originalToDataURL.apply(this, arguments);
};

// WebGL vendor/renderer spoofing
const getParameterProto = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Intel Inc.';
    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
    return getParameterProto.apply(this, arguments);
};

console.log('Anti-detection stealth script loaded');
"""


class QRCodeLoginService:
    """Service for handling QR code login flow."""

    DOUYIN_LOGIN_URL = "https://www.douyin.com/"

    # MediaCrawler's proven QR code selector - this is the most reliable selector
    QR_CODE_SELECTORS = [
        "xpath=//div[@id='animate_qrcode_container']//img",  # MediaCrawler's selector
        "xpath=//div[contains(@class, 'qrcode')]//img",
        "xpath=//img[contains(@src, 'qrcode')]",
        "div#animate_qrcode_container img",
        "div.web-login-scan-code__content img",
        "div[class*='qrcode'] img",
        "img[alt*='二维码']",
    ]

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def start_login_session(self, session_id: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Start a new QR code login session.
        Returns the QR code image as base64.

        Uses headless=False with xvfb virtual display and comprehensive
        anti-detection measures to avoid being blocked by Douyin.
        Falls back to headless mode if no display is available.
        """
        last_error = None

        # Check if DISPLAY is available (for non-headless mode)
        display = os.environ.get('DISPLAY')
        use_headless = display is None

        # Try to set DISPLAY if Xvfb might be running on :99
        if use_headless:
            # Check if Xvfb is running on :99
            try:
                import subprocess
                result = subprocess.run(['pgrep', '-x', 'Xvfb'], capture_output=True, text=True)
                if result.returncode == 0:
                    os.environ['DISPLAY'] = ':99'
                    use_headless = False
                    logger.info("Detected Xvfb running, setting DISPLAY=:99")
            except Exception:
                pass

        if use_headless:
            logger.warning("No display available, falling back to headless mode (may be detected by Douyin)")
        else:
            logger.info(f"Using display: {os.environ.get('DISPLAY')}")

        for attempt in range(max_retries):
            try:
                from playwright.async_api import async_playwright

                logger.info(f"Starting QR code login session: {session_id} (attempt {attempt + 1}/{max_retries}, headless={use_headless})")

                # Initialize Playwright
                playwright = await async_playwright().start()

                # Launch browser with anti-detection configuration
                self.browser = await playwright.chromium.launch(
                    headless=use_headless,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-infobars',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--window-size=1920,1080',
                        '--start-maximized',
                        '--disable-extensions',
                        '--disable-plugins-discovery',
                        '--disable-default-apps',
                        '--disable-background-networking',
                        '--disable-sync',
                        '--disable-translate',
                        '--hide-scrollbars',
                        '--metrics-recording-only',
                        '--mute-audio',
                        '--no-first-run',
                        '--safebrowsing-disable-auto-update',
                        f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(120, 125)}.0.0.0 Safari/537.36',
                    ]
                )

                # Create context with realistic browser fingerprint
                self.context = await self.browser.new_context(
                    user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(120, 125)}.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                    timezone_id="Asia/Shanghai",
                    geolocation={"latitude": 39.9042, "longitude": 116.4074},  # Beijing
                    permissions=["geolocation"],
                    color_scheme="light",
                    device_scale_factor=1,
                    is_mobile=False,
                    has_touch=False,
                )

                # Add anti-detection stealth script before page creation
                await self.context.add_init_script(STEALTH_JS)

                # Create page
                self.page = await self.context.new_page()

                # Additional page-level anti-detection
                await self.page.evaluate("""() => {
                    // Ensure webdriver is undefined
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                }""")

                # Navigate to Douyin
                logger.info("Navigating to Douyin...")
                # Use domcontentloaded instead of networkidle to avoid timeout on long-loading resources
                await self.page.goto(self.DOUYIN_LOGIN_URL, wait_until="domcontentloaded", timeout=30000)

                # Wait for page to stabilize and load dynamic content
                await asyncio.sleep(3)

                # Wait for the page to be ready by checking for common elements
                try:
                    await self.page.wait_for_selector("body", state="attached", timeout=5000)
                except Exception:
                    pass

                # Try to click login button using JavaScript for better reliability
                login_clicked = await self.page.evaluate("""() => {
                    // Find all elements containing "登录" text
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        if (el.innerText === '登录' && el.offsetParent !== null) {
                            // Check if it's a clickable element (button, link, or has click handler)
                            const tag = el.tagName.toLowerCase();
                            const isClickable = tag === 'button' || tag === 'a' ||
                                el.onclick || el.getAttribute('role') === 'button' ||
                                el.classList.contains('login') || el.classList.contains('btn');
                            if (isClickable || el.offsetWidth > 30) {
                                el.click();
                                return true;
                            }
                        }
                    }
                    // Try clicking any element with "登录" in its text
                    for (const el of elements) {
                        if (el.innerText && el.innerText.includes('登录') &&
                            !el.innerText.includes('扫码') && el.offsetParent !== null &&
                            el.offsetWidth > 30 && el.offsetWidth < 200) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }""")

                if login_clicked:
                    logger.info("Clicked login button via JavaScript")
                    await asyncio.sleep(3)
                else:
                    logger.warning("Could not find login button, trying to look for QR code directly")

                # Try to find and click QR code login tab using JavaScript
                qr_tab_clicked = await self.page.evaluate("""() => {
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        if (el.innerText && el.innerText.includes('扫码登录') && el.offsetParent !== null) {
                            el.click();
                            return true;
                        }
                    }
                    // Also try clicking elements with qrcode-related classes
                    const qrElements = document.querySelectorAll('[class*="qrcode"], [class*="scan"], [class*="QRCode"]');
                    for (const el of qrElements) {
                        if (el.offsetParent !== null) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }""")

                if qr_tab_clicked:
                    logger.info("Clicked QR tab via JavaScript")
                    await asyncio.sleep(2)

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
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                await self.cleanup()

                if attempt < max_retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)

        # All retries failed
        logger.error(f"Failed to start login session after {max_retries} attempts: {last_error}")
        return {
            "success": False,
            "error": str(last_error) if last_error else "Unknown error",
            "message": "启动登录会话失败，请确保服务器已安装 Playwright 浏览器并配置了 xvfb 虚拟显示"
        }

    async def _capture_qr_code(self) -> Optional[str]:
        """
        Capture QR code image from the page using MediaCrawler's proven selectors.
        Returns base64-encoded image data.
        """
        try:
            # Try each selector in order of reliability
            for selector in self.QR_CODE_SELECTORS:
                try:
                    logger.debug(f"Trying QR code selector: {selector}")

                    # Wait for element with timeout
                    if selector.startswith("xpath="):
                        element = await self.page.locator(selector).first.element_handle(timeout=3000)
                    else:
                        element = await self.page.wait_for_selector(selector, timeout=3000, state="visible")

                    if element:
                        # Get bounding box to validate element size
                        box = await element.bounding_box()
                        if box and box["width"] > 80 and box["height"] > 80:
                            logger.info(f"Found QR code with selector: {selector}, size: {box['width']}x{box['height']}")
                            # Screenshot the element
                            screenshot = await element.screenshot()
                            return base64.b64encode(screenshot).decode()
                        else:
                            logger.debug(f"Element too small: {box}")
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            # Fallback: Try to find any reasonably sized image that might be QR code
            logger.debug("Trying fallback: searching for QR-like images")
            images = await self.page.query_selector_all("img")
            for img in images:
                try:
                    box = await img.bounding_box()
                    if box and 100 < box["width"] < 400 and 100 < box["height"] < 400:
                        src = await img.get_attribute("src") or ""
                        alt = await img.get_attribute("alt") or ""
                        # Check if this looks like a QR code
                        if any(keyword in (src + alt).lower() for keyword in ["qr", "code", "login", "scan", "二维码"]):
                            logger.info(f"Found QR-like image with size: {box['width']}x{box['height']}")
                            screenshot = await img.screenshot()
                            return base64.b64encode(screenshot).decode()
                except Exception as e:
                    logger.debug(f"Error checking image: {e}")
                    continue

            logger.warning("Could not find QR code on page")
            return None

        except Exception as e:
            logger.error(f"Failed to capture QR code: {e}")
            return None

    async def check_login_status(self, session_id: str) -> Dict[str, Any]:
        """
        Check if user has scanned and logged in.

        Uses MediaCrawler's proven login detection methods:
        1. Check localStorage.HasUserLogin == "1"
        2. Check LOGIN_STATUS cookie == "1"
        3. Check for sessionid cookie presence
        """
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
            is_logged_in = False

            # Method 1: Check localStorage.HasUserLogin (MediaCrawler's primary method)
            try:
                local_storage = await service.page.evaluate("() => window.localStorage")
                if local_storage and local_storage.get("HasUserLogin") == "1":
                    logger.info("Login detected via localStorage.HasUserLogin")
                    is_logged_in = True
            except Exception as e:
                logger.debug(f"localStorage check failed: {e}")

            # Method 2: Check cookies
            cookies = await service.context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}

            # Check LOGIN_STATUS cookie (MediaCrawler's secondary method)
            if cookie_dict.get("LOGIN_STATUS") == "1":
                logger.info("Login detected via LOGIN_STATUS cookie")
                is_logged_in = True

            # Method 3: Check for sessionid cookie (essential for API calls)
            if cookie_dict.get("sessionid"):
                logger.info("Login detected via sessionid cookie")
                is_logged_in = True

            if is_logged_in:
                # Build cookie string with essential cookies
                cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

                # Verify we have the essential cookies
                missing_essential = [c for c in ESSENTIAL_COOKIES if c not in cookie_dict or not cookie_dict[c]]
                if missing_essential:
                    logger.warning(f"Missing some essential cookies: {missing_essential}")

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
