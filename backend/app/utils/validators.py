"""
Input validation utilities.
"""
import re
from typing import Optional


def is_valid_sec_uid(sec_uid: str) -> bool:
    """Validate sec_uid format."""
    if not sec_uid:
        return False
    # sec_uid is typically base64-like string
    pattern = r'^MS4wLjABAAAA[A-Za-z0-9_-]{32,64}$'
    return bool(re.match(pattern, sec_uid))


def is_valid_aweme_id(aweme_id: str) -> bool:
    """Validate aweme_id format."""
    if not aweme_id:
        return False
    # aweme_id is a numeric string
    return aweme_id.isdigit() and len(aweme_id) >= 10


def is_valid_room_id(room_id: str) -> bool:
    """Validate room_id format."""
    if not room_id:
        return False
    return room_id.isdigit()


def is_valid_douyin_url(url: str) -> bool:
    """Validate if URL is a valid Douyin URL."""
    if not url:
        return False
    patterns = [
        r'https?://(www\.)?douyin\.com',
        r'https?://v\.douyin\.com',
        r'https?://live\.douyin\.com',
    ]
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    return False


def extract_and_validate_sec_uid(input_str: str) -> Optional[str]:
    """Extract sec_uid from URL or return if already valid."""
    if is_valid_sec_uid(input_str):
        return input_str

    # Try to extract from URL
    patterns = [
        r'sec_uid=([^&]+)',
        r'/user/([A-Za-z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            sec_uid = match.group(1)
            if is_valid_sec_uid(sec_uid):
                return sec_uid

    return None


def extract_and_validate_aweme_id(input_str: str) -> Optional[str]:
    """Extract aweme_id from URL or return if already valid."""
    if is_valid_aweme_id(input_str):
        return input_str

    # Try to extract from URL
    patterns = [
        r'/video/(\d+)',
        r'item_ids=(\d+)',
        r'aweme_id=(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)

    return None


def sanitize_search_keyword(keyword: str) -> str:
    """Sanitize search keyword."""
    if not keyword:
        return ""
    # Remove potentially harmful characters
    keyword = re.sub(r'[<>"\']', '', keyword)
    # Limit length
    return keyword[:100].strip()
