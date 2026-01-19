"""
Authentication API endpoints for QR code login.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from app.services.qrcode_login import (
    create_login_session,
    check_session_status,
    cancel_login_session
)
from app.config import settings

router = APIRouter()


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
async def save_cookie(request: CookieRequest):
    """
    Manually save a cookie string.
    Use this if automatic QR code login doesn't work.
    """
    try:
        cookie = request.cookie.strip()
        if not cookie:
            return CookieResponse(success=False, message="Cookie 不能为空")

        # Save to .env file
        from pathlib import Path
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

        return CookieResponse(success=True, message="Cookie 保存成功")

    except Exception as e:
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
