"""
Utility helper functions.
"""
import re
import time
import random
import string
from typing import Optional, Any, Dict
from datetime import datetime


def extract_sec_uid(url: str) -> Optional[str]:
    """Extract sec_uid from Douyin user URL."""
    patterns = [
        r'sec_uid=([^&]+)',
        r'/user/([A-Za-z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_aweme_id(url: str) -> Optional[str]:
    """Extract aweme_id from Douyin video URL."""
    patterns = [
        r'/video/(\d+)',
        r'item_ids=(\d+)',
        r'aweme_id=(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_room_id(url: str) -> Optional[str]:
    """Extract room_id from Douyin live URL."""
    patterns = [
        r'live\.douyin\.com/(\d+)',
        r'room_id=(\d+)',
        r'web_rid=(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def gen_random_str(length: int = 16) -> str:
    """Generate a random string."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def get_timestamp_ms() -> int:
    """Get current timestamp in milliseconds."""
    return int(time.time() * 1000)


def format_number(num: int) -> str:
    """Format large numbers for display (e.g., 1000 -> 1K)."""
    if num < 1000:
        return str(num)
    elif num < 10000:
        return f"{num / 1000:.1f}K"
    elif num < 100000000:
        return f"{num / 10000:.1f}万"
    else:
        return f"{num / 100000000:.1f}亿"


def timestamp_to_datetime(ts: int) -> datetime:
    """Convert Unix timestamp to datetime."""
    if ts > 10000000000:  # milliseconds
        ts = ts / 1000
    return datetime.fromtimestamp(ts)


def datetime_to_timestamp(dt: datetime) -> int:
    """Convert datetime to Unix timestamp."""
    return int(dt.timestamp())


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage."""
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '_', filename)
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename.strip()


def merge_dict(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries, update overrides base."""
    result = base.copy()
    for key, value in update.items():
        if value is not None:
            result[key] = value
    return result


def calculate_engagement_rate(
    likes: int,
    comments: int,
    shares: int,
    views: int
) -> float:
    """Calculate engagement rate as percentage."""
    if views == 0:
        return 0.0
    total_engagement = likes + comments + shares
    return round((total_engagement / views) * 100, 2)
