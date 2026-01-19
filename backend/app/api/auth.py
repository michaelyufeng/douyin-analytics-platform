"""
Authentication API endpoints for QR code login.
"""
import logging
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

from app.services.qrcode_login import (
    create_login_session,
    check_session_status,
    cancel_login_session
)
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Path to the local login scripts
SCRIPT_PATH = Path(__file__).parent.parent.parent / "scripts" / "get_cookie.py"
SCRIPT_AUTO_PATH = Path(__file__).parent.parent.parent / "scripts" / "get_cookie_auto.py"

# Essential cookies that should be present for a valid session
ESSENTIAL_COOKIES = ["sessionid", "sessionid_ss", "ttwid", "LOGIN_STATUS"]


class LoginResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    qr_image: Optional[str] = None
    message: str
    error: Optional[str] = None


class StatusResponse(BaseModel):
    status: str
    message: str
    cookie: Optional[str] = None


class CookieRequest(BaseModel):
    cookie: str


class CookieResponse(BaseModel):
    success: bool
    message: str
    validation: Optional[dict] = None


def validate_cookie(cookie: str) -> dict:
    """
    Validate cookie format and check for essential cookies.
    Returns a dict with validation results.
    """
    result = {
        "is_valid": True,
        "has_essential": False,
        "missing_cookies": [],
        "cookie_count": 0,
        "warnings": []
    }

    if not cookie or not cookie.strip():
        result["is_valid"] = False
        result["warnings"].append("Cookie 字符串为空")
        return result

    # Parse cookies
    cookie_pairs = [c.strip() for c in cookie.split(";") if c.strip()]
    result["cookie_count"] = len(cookie_pairs)

    # Extract cookie names
    cookie_names = set()
    for pair in cookie_pairs:
        if "=" in pair:
            name = pair.split("=", 1)[0].strip()
            cookie_names.add(name)

    # Check for essential cookies
    missing = [c for c in ESSENTIAL_COOKIES if c not in cookie_names]
    result["missing_cookies"] = missing
    result["has_essential"] = len(missing) == 0

    if missing:
        result["warnings"].append(f"缺少部分关键 Cookie: {', '.join(missing)}")

    # Basic format validation
    if result["cookie_count"] < 3:
        result["warnings"].append("Cookie 数量较少，可能不完整")

    # Check for common issues
    if "sessionid=" not in cookie and "sessionid_ss=" not in cookie:
        result["warnings"].append("未找到 sessionid，登录状态可能无效")

    return result


@router.post("/qrcode/create", response_model=LoginResponse)
async def create_qrcode_login():
    """
    Create a new QR code login session.
    Returns a QR code image (base64 encoded) for the user to scan.
    """
    try:
        result = await create_login_session()
        return LoginResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/qrcode/status/{session_id}", response_model=StatusResponse)
async def get_login_status(session_id: str):
    """
    Check the status of a QR code login session.
    Call this endpoint periodically to check if the user has logged in.
    """
    try:
        result = await check_session_status(session_id)
        return StatusResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qrcode/cancel/{session_id}")
async def cancel_login(session_id: str, background_tasks: BackgroundTasks):
    """Cancel a QR code login session."""
    background_tasks.add_task(cancel_login_session, session_id)
    return {"success": True, "message": "登录会话已取消"}


@router.post("/cookie/save", response_model=CookieResponse)
async def save_cookie(request: CookieRequest, req: Request):
    """
    Manually save a cookie string.
    Use this if automatic QR code login doesn't work.
    Also used by the auto-upload script.
    """
    try:
        cookie = request.cookie.strip()

        # Get client info for logging
        client_ip = req.client.host if req.client else "unknown"
        user_agent = req.headers.get("user-agent", "unknown")

        # Validate cookie
        validation = validate_cookie(cookie)

        if not validation["is_valid"]:
            logger.warning(f"Invalid cookie submission from {client_ip}")
            return CookieResponse(
                success=False,
                message="Cookie 不能为空",
                validation=validation
            )

        # Log the operation
        logger.info(
            f"Cookie save request from {client_ip}, "
            f"cookie_count={validation['cookie_count']}, "
            f"has_essential={validation['has_essential']}"
        )

        # Save to .env file
        env_path = Path(__file__).parent.parent.parent / ".env"

        env_content = ""
        if env_path.exists():
            with open(env_path, "r") as f:
                env_content = f.read()

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

        with open(env_path, "w") as f:
            f.write(env_content)

        # Update runtime config
        settings.douyin_cookie = cookie

        # Build response message
        if validation["has_essential"]:
            message = "Cookie 保存成功"
        else:
            message = "Cookie 保存成功，但缺少部分关键 Cookie，功能可能受限"

        logger.info(f"Cookie saved successfully from {client_ip}")

        return CookieResponse(
            success=True,
            message=message,
            validation=validation
        )

    except Exception as e:
        logger.error(f"Failed to save cookie: {str(e)}")
        return CookieResponse(success=False, message=f"保存失败: {str(e)}")


@router.get("/cookie/status")
async def get_cookie_status():
    """Check if a valid cookie is configured."""
    cookie = settings.douyin_cookie
    if cookie and len(cookie) > 10:
        # Mask the cookie for security
        masked = cookie[:20] + "..." + cookie[-20:] if len(cookie) > 50 else cookie[:10] + "..."
        return {
            "has_cookie": True,
            "cookie_preview": masked,
            "message": "Cookie 已配置"
        }
    return {
        "has_cookie": False,
        "cookie_preview": None,
        "message": "未配置 Cookie，请先登录"
    }


@router.get("/script", response_class=PlainTextResponse)
async def download_login_script():
    """
    Download the local login script (basic version).
    This script can be run locally to get cookies when the server-side QR code doesn't work.
    """
    try:
        if SCRIPT_PATH.exists():
            return SCRIPT_PATH.read_text(encoding="utf-8")
        else:
            raise HTTPException(status_code=404, detail="Script file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/script-auto", response_class=PlainTextResponse)
async def download_auto_upload_script():
    """
    Download the auto-upload version of the login script.
    This script can automatically upload cookies to the server after successful login.
    """
    try:
        if SCRIPT_AUTO_PATH.exists():
            return SCRIPT_AUTO_PATH.read_text(encoding="utf-8")
        else:
            raise HTTPException(status_code=404, detail="Script file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Browser console command to extract cookies
CONSOLE_COMMAND = """
(function() {
    var cookies = document.cookie.split(';').map(c => c.trim()).join('; ');
    console.log('='.repeat(60));
    console.log('抖音 Cookie:');
    console.log('='.repeat(60));
    console.log(cookies);
    console.log('='.repeat(60));
    prompt('请复制下面的 Cookie (Ctrl+C):', cookies);
})();
""".strip()


@router.get("/console-command")
async def get_console_command():
    """
    Get the browser console command for extracting cookies.
    Users can run this command in the browser console after logging in to Douyin.
    """
    return {
        "command": CONSOLE_COMMAND,
        "instructions": [
            "1. 在浏览器中打开 https://www.douyin.com 并登录",
            "2. 按 F12 打开开发者工具",
            "3. 切换到 Console (控制台) 标签",
            "4. 粘贴并执行上面的命令",
            "5. 在弹出的对话框中复制 Cookie",
            "6. 粘贴到设置页面的 Cookie 输入框中"
        ]
    }
