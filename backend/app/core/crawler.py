"""
Douyin API Crawler Engine.
Handles all HTTP requests to Douyin's APIs.
"""
import httpx
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from loguru import logger

from app.config import settings
from app.core.signature import SignatureManager


class DouyinEndpoints:
    """Douyin API endpoints."""
    BASE = "https://www.douyin.com"
    API_BASE = "https://www.douyin.com/aweme/v1/web"

    # User endpoints
    USER_PROFILE = f"{API_BASE}/user/profile/other/"
    USER_POST = f"{API_BASE}/aweme/post/"
    USER_LIKE = f"{API_BASE}/aweme/favorite/"
    USER_FOLLOWING = f"{API_BASE}/user/following/list/"
    USER_FOLLOWER = f"{API_BASE}/user/follower/list/"
    USER_MIX = f"{API_BASE}/mix/list/"

    # Video endpoints
    VIDEO_DETAIL = f"{API_BASE}/aweme/detail/"
    VIDEO_COMMENTS = f"{API_BASE}/comment/list/"
    COMMENT_REPLIES = f"{API_BASE}/comment/list/reply/"
    RELATED_VIDEOS = f"{API_BASE}/aweme/related/"

    # Live endpoints
    LIVE_INFO = "https://live.douyin.com/webcast/room/web/enter/"
    LIVE_RANKING = "https://live.douyin.com/webcast/ranklist/hot/"

    # Search endpoints
    SEARCH_VIDEO = f"{API_BASE}/general/search/single/"
    SEARCH_USER = f"{API_BASE}/search/user/"
    SEARCH_LIVE = f"{API_BASE}/search/live/"
    SEARCH_SUGGEST = f"{API_BASE}/search/suggest/"

    # Hot list endpoints
    HOT_SEARCH = f"{API_BASE}/hot/search/list/"
    HOT_VIDEO = f"{API_BASE}/hot/search/video/list/"


class DouyinCrawler:
    """
    Async crawler for Douyin API.
    Handles request signing, rate limiting, and error handling.
    """

    def __init__(self):
        self.user_agent = settings.douyin_user_agent
        self.cookie = settings.douyin_cookie
        self.timeout = settings.request_timeout
        self.max_retries = settings.max_retries
        self.retry_delay = settings.retry_delay
        self.signature = SignatureManager(self.user_agent)

        self.headers = {
            "User-Agent": self.user_agent,
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie": self.cookie,
        }

        # Default request parameters
        self.default_params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "cookie_enabled": "true",
            "browser_language": "zh-CN",
            "browser_platform": "Win32",
            "browser_name": "Chrome",
            "browser_version": "120.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "engine_version": "120.0.0.0",
            "os_name": "Windows",
            "os_version": "10",
            "cpu_core_num": "12",
            "device_memory": "8",
            "platform": "PC",
            "version_code": "170400",
            "version_name": "17.4.0",
        }

    def _build_params(self, extra_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Build request parameters with defaults."""
        params = self.default_params.copy()
        params["msToken"] = self.signature.gen_mstoken()
        params["webid"] = self.signature.gen_webid()
        if extra_params:
            params.update(extra_params)
        return params

    async def _request(
        self,
        method: str,
        url: str,
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        sign: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Make an async HTTP request with retry logic.

        Args:
            method: HTTP method (GET or POST)
            url: Request URL
            params: URL parameters
            data: POST data
            sign: Whether to sign the request

        Returns:
            Response JSON or None if failed
        """
        if params is None:
            params = {}

        full_params = self._build_params(params)

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if sign:
                        query_string = urlencode(full_params)
                        signed_params, xbogus, _ = self.signature.xbogus.get_xbogus(query_string)
                        full_url = f"{url}?{signed_params}"
                    else:
                        full_url = f"{url}?{urlencode(full_params)}"

                    if method.upper() == "GET":
                        response = await client.get(full_url, headers=self.headers)
                    else:
                        response = await client.post(
                            full_url,
                            headers=self.headers,
                            json=data
                        )

                    if response.status_code == 200:
                        return response.json()
                    else:
                        logger.warning(f"Request failed with status {response.status_code}")

            except httpx.TimeoutException:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")

            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        return None

    # User methods
    async def get_user_profile(self, sec_uid: str) -> Optional[Dict[str, Any]]:
        """Get user profile by sec_uid."""
        params = {"sec_user_id": sec_uid}
        result = await self._request("GET", DouyinEndpoints.USER_PROFILE, params)

        if result and result.get("status_code") == 0:
            user_info = result.get("user", {})
            return {
                "sec_uid": sec_uid,
                "uid": user_info.get("uid"),
                "nickname": user_info.get("nickname"),
                "unique_id": user_info.get("unique_id"),
                "signature": user_info.get("signature"),
                "avatar_url": user_info.get("avatar_larger", {}).get("url_list", [None])[0],
                "follower_count": user_info.get("follower_count", 0),
                "following_count": user_info.get("following_count", 0),
                "total_favorited": user_info.get("total_favorited", 0),
                "aweme_count": user_info.get("aweme_count", 0),
                "is_verified": user_info.get("custom_verify") is not None,
                "verify_info": user_info.get("custom_verify"),
                "region": user_info.get("ip_location"),
            }
        return None

    async def get_user_posts(self, sec_uid: str, cursor: int = 0, count: int = 20) -> Optional[Dict[str, Any]]:
        """Get user's video posts."""
        params = {
            "sec_user_id": sec_uid,
            "max_cursor": cursor,
            "count": count,
        }
        result = await self._request("GET", DouyinEndpoints.USER_POST, params)

        if result and result.get("status_code") == 0:
            videos = []
            for item in result.get("aweme_list", []):
                videos.append(self._parse_video(item))
            return {
                "videos": videos,
                "cursor": result.get("max_cursor", 0),
                "has_more": result.get("has_more", False)
            }
        return None

    async def get_user_likes(self, sec_uid: str, cursor: int = 0, count: int = 20) -> Optional[Dict[str, Any]]:
        """Get user's liked videos."""
        params = {
            "sec_user_id": sec_uid,
            "max_cursor": cursor,
            "count": count,
        }
        result = await self._request("GET", DouyinEndpoints.USER_LIKE, params)

        if result and result.get("status_code") == 0:
            videos = []
            for item in result.get("aweme_list", []):
                videos.append(self._parse_video(item))
            return {
                "videos": videos,
                "cursor": result.get("max_cursor", 0),
                "has_more": result.get("has_more", False)
            }
        return None

    async def get_user_collections(self, sec_uid: str, cursor: int = 0, count: int = 20) -> Optional[Dict[str, Any]]:
        """Get user's collections."""
        # Collections require POST with authentication
        return {"collections": [], "cursor": 0, "has_more": False}

    async def get_user_following(self, sec_uid: str, cursor: int = 0, count: int = 20) -> Optional[Dict[str, Any]]:
        """Get user's following list."""
        params = {
            "sec_user_id": sec_uid,
            "offset": cursor,
            "count": count,
            "source_type": "1",
        }
        result = await self._request("GET", DouyinEndpoints.USER_FOLLOWING, params)

        if result and result.get("status_code") == 0:
            users = []
            for item in result.get("followings", []):
                users.append({
                    "sec_uid": item.get("sec_uid"),
                    "nickname": item.get("nickname"),
                    "avatar_url": item.get("avatar_larger", {}).get("url_list", [None])[0],
                })
            return {
                "users": users,
                "cursor": result.get("offset", 0),
                "has_more": result.get("has_more", False)
            }
        return None

    async def get_user_followers(self, sec_uid: str, cursor: int = 0, count: int = 20) -> Optional[Dict[str, Any]]:
        """Get user's followers list."""
        params = {
            "sec_user_id": sec_uid,
            "offset": cursor,
            "count": count,
            "source_type": "1",
        }
        result = await self._request("GET", DouyinEndpoints.USER_FOLLOWER, params)

        if result and result.get("status_code") == 0:
            users = []
            for item in result.get("followers", []):
                users.append({
                    "sec_uid": item.get("sec_uid"),
                    "nickname": item.get("nickname"),
                    "avatar_url": item.get("avatar_larger", {}).get("url_list", [None])[0],
                })
            return {
                "users": users,
                "cursor": result.get("offset", 0),
                "has_more": result.get("has_more", False)
            }
        return None

    async def get_user_mixes(self, sec_uid: str, cursor: int = 0, count: int = 20) -> Optional[Dict[str, Any]]:
        """Get user's video mixes/collections."""
        params = {
            "sec_user_id": sec_uid,
            "cursor": cursor,
            "count": count,
        }
        result = await self._request("GET", DouyinEndpoints.USER_MIX, params)

        if result and result.get("status_code") == 0:
            return {
                "mixes": result.get("mix_infos", []),
                "cursor": result.get("cursor", 0),
                "has_more": result.get("has_more", False)
            }
        return None

    # Video methods
    async def get_video_detail(self, aweme_id: str) -> Optional[Dict[str, Any]]:
        """Get video detail by aweme_id."""
        params = {"aweme_id": aweme_id}
        result = await self._request("GET", DouyinEndpoints.VIDEO_DETAIL, params)

        if result and result.get("status_code") == 0:
            item = result.get("aweme_detail", {})
            return self._parse_video(item)
        return None

    async def get_video_comments(self, aweme_id: str, cursor: int = 0, count: int = 20) -> Optional[Dict[str, Any]]:
        """Get video comments."""
        params = {
            "aweme_id": aweme_id,
            "cursor": cursor,
            "count": count,
        }
        result = await self._request("GET", DouyinEndpoints.VIDEO_COMMENTS, params)

        if result and result.get("status_code") == 0:
            comments = []
            for item in result.get("comments", []):
                comments.append({
                    "cid": item.get("cid"),
                    "content": item.get("text"),
                    "digg_count": item.get("digg_count", 0),
                    "reply_count": item.get("reply_comment_total", 0),
                    "user": {
                        "uid": item.get("user", {}).get("uid"),
                        "nickname": item.get("user", {}).get("nickname"),
                    },
                    "create_time": item.get("create_time"),
                    "ip_label": item.get("ip_label"),
                })
            return {
                "comments": comments,
                "cursor": result.get("cursor", 0),
                "has_more": result.get("has_more", False),
                "total": result.get("total", len(comments))
            }
        return None

    async def get_comment_replies(self, comment_id: str, cursor: int = 0, count: int = 20) -> Optional[Dict[str, Any]]:
        """Get comment replies."""
        params = {
            "comment_id": comment_id,
            "cursor": cursor,
            "count": count,
        }
        result = await self._request("GET", DouyinEndpoints.COMMENT_REPLIES, params)

        if result and result.get("status_code") == 0:
            return {
                "replies": result.get("comments", []),
                "cursor": result.get("cursor", 0),
                "has_more": result.get("has_more", False)
            }
        return None

    async def get_related_videos(self, aweme_id: str, count: int = 20) -> Optional[Dict[str, Any]]:
        """Get related videos."""
        params = {
            "aweme_id": aweme_id,
            "count": count,
        }
        result = await self._request("GET", DouyinEndpoints.RELATED_VIDEOS, params)

        if result and result.get("status_code") == 0:
            videos = []
            for item in result.get("aweme_list", []):
                videos.append(self._parse_video(item))
            return {"videos": videos}
        return None

    async def get_mix_videos(self, mix_id: str, cursor: int = 0, count: int = 20) -> Optional[Dict[str, Any]]:
        """Get videos from a mix/collection."""
        params = {
            "mix_id": mix_id,
            "cursor": cursor,
            "count": count,
        }
        result = await self._request("GET", DouyinEndpoints.USER_MIX, params)

        if result and result.get("status_code") == 0:
            videos = []
            for item in result.get("aweme_list", []):
                videos.append(self._parse_video(item))
            return {
                "videos": videos,
                "cursor": result.get("cursor", 0),
                "has_more": result.get("has_more", False)
            }
        return None

    async def parse_video_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse video URL to extract video info."""
        import re

        # Extract aweme_id from URL
        patterns = [
            r'/video/(\d+)',
            r'item_ids=(\d+)',
            r'aweme_id=(\d+)',
        ]

        aweme_id = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                aweme_id = match.group(1)
                break

        if aweme_id:
            return await self.get_video_detail(aweme_id)
        return None

    async def download_video(self, aweme_id: str, quality: str = "high") -> Optional[Dict[str, Any]]:
        """Download video (returns download info, actual download handled separately)."""
        video = await self.get_video_detail(aweme_id)
        if video and video.get("video_url"):
            return {
                "status": "ready",
                "aweme_id": aweme_id,
                "video_url": video["video_url"],
                "message": "Video URL retrieved"
            }
        return {"status": "failed", "message": "Could not get video URL"}

    # Live methods
    async def get_live_info(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get live room information."""
        params = {
            "web_rid": room_id,
            "room_id_str": room_id,
        }
        result = await self._request("GET", DouyinEndpoints.LIVE_INFO, params, sign=False)

        if result and result.get("status_code") == 0:
            data = result.get("data", {})
            room = data.get("room", {})
            return {
                "room_id": room_id,
                "title": room.get("title"),
                "cover_url": room.get("cover", {}).get("url_list", [None])[0],
                "stream_url": None,  # Stream URL requires special handling
                "user_count": room.get("user_count_str"),
                "status": room.get("status"),
            }
        return None

    async def get_live_by_user(self, sec_uid: str) -> Optional[Dict[str, Any]]:
        """Get live room by user sec_uid."""
        # This requires checking if user is live
        return None

    async def get_live_ranking(self, count: int = 50) -> Optional[Dict[str, Any]]:
        """Get live room ranking."""
        params = {"count": count}
        result = await self._request("GET", DouyinEndpoints.LIVE_RANKING, params, sign=False)

        if result:
            return {
                "lives": result.get("data", []),
                "total": len(result.get("data", []))
            }
        return None

    # Search methods
    async def search_video(
        self,
        keyword: str,
        cursor: int = 0,
        count: int = 20,
        sort_type: int = 0,
        publish_time: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Search for videos."""
        params = {
            "keyword": keyword,
            "offset": cursor,
            "count": count,
            "sort_type": sort_type,
            "publish_time": publish_time,
            "search_source": "normal_search",
        }
        result = await self._request("GET", DouyinEndpoints.SEARCH_VIDEO, params)

        if result and result.get("status_code") == 0:
            videos = []
            for item in result.get("data", []):
                aweme = item.get("aweme_info", {})
                if aweme:
                    videos.append(self._parse_video(aweme))
            return {
                "videos": videos,
                "cursor": result.get("cursor", 0),
                "has_more": result.get("has_more", False)
            }
        return None

    async def search_user(self, keyword: str, cursor: int = 0, count: int = 20) -> Optional[Dict[str, Any]]:
        """Search for users."""
        params = {
            "keyword": keyword,
            "offset": cursor,
            "count": count,
            "search_source": "normal_search",
        }
        result = await self._request("GET", DouyinEndpoints.SEARCH_USER, params)

        if result and result.get("status_code") == 0:
            users = []
            for item in result.get("user_list", []):
                user_info = item.get("user_info", {})
                users.append({
                    "sec_uid": user_info.get("sec_uid"),
                    "nickname": user_info.get("nickname"),
                    "avatar_url": user_info.get("avatar_larger", {}).get("url_list", [None])[0],
                    "follower_count": user_info.get("follower_count", 0),
                })
            return {
                "users": users,
                "cursor": result.get("cursor", 0),
                "has_more": result.get("has_more", False)
            }
        return None

    async def search_live(self, keyword: str, cursor: int = 0, count: int = 20) -> Optional[Dict[str, Any]]:
        """Search for live streams."""
        params = {
            "keyword": keyword,
            "offset": cursor,
            "count": count,
        }
        result = await self._request("GET", DouyinEndpoints.SEARCH_LIVE, params)

        if result and result.get("status_code") == 0:
            return {
                "lives": result.get("data", []),
                "cursor": result.get("cursor", 0),
                "has_more": result.get("has_more", False)
            }
        return None

    async def get_search_suggest(self, keyword: str) -> Optional[Dict[str, Any]]:
        """Get search suggestions."""
        params = {"keyword": keyword}
        result = await self._request("GET", DouyinEndpoints.SEARCH_SUGGEST, params)

        if result and result.get("status_code") == 0:
            return {"suggestions": result.get("sug_list", [])}
        return None

    async def get_trending_searches(self) -> Optional[Dict[str, Any]]:
        """Get trending search keywords."""
        result = await self._request("GET", DouyinEndpoints.HOT_SEARCH, {})

        if result and result.get("status_code") == 0:
            return {"trends": result.get("data", {}).get("word_list", [])}
        return None

    # Hot list methods
    async def get_board_list(self) -> Optional[Dict[str, Any]]:
        """Get available ranking boards."""
        return None  # Would need specific API endpoint

    async def get_hot_list(self, board_type: str) -> Optional[Dict[str, Any]]:
        """Get hot list by board type."""
        endpoint = DouyinEndpoints.HOT_SEARCH if board_type == "hot_search" else DouyinEndpoints.HOT_VIDEO
        result = await self._request("GET", endpoint, {})

        if result and result.get("status_code") == 0:
            return {
                "items": result.get("data", {}).get("word_list", []),
                "board_type": board_type
            }
        return None

    async def get_video_ranking(self, count: int = 50) -> Optional[Dict[str, Any]]:
        """Get video ranking."""
        result = await self._request("GET", DouyinEndpoints.HOT_VIDEO, {"count": count})

        if result and result.get("status_code") == 0:
            return {
                "videos": result.get("data", []),
                "total": len(result.get("data", []))
            }
        return None

    # Helper methods
    def _parse_video(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse video item from API response."""
        video = item.get("video", {})
        statistics = item.get("statistics", {})

        # Get video URL
        video_url = None
        play_addr = video.get("play_addr", {})
        if play_addr:
            url_list = play_addr.get("url_list", [])
            video_url = url_list[0] if url_list else None

        # Get cover URL
        cover_url = None
        cover = video.get("cover", {}) or item.get("video", {}).get("origin_cover", {})
        if cover:
            url_list = cover.get("url_list", [])
            cover_url = url_list[0] if url_list else None

        return {
            "aweme_id": item.get("aweme_id"),
            "desc": item.get("desc"),
            "video_url": video_url,
            "cover_url": cover_url,
            "music_url": item.get("music", {}).get("play_url", {}).get("url_list", [None])[0],
            "duration": video.get("duration", 0),
            "play_count": statistics.get("play_count", 0),
            "digg_count": statistics.get("digg_count", 0),
            "comment_count": statistics.get("comment_count", 0),
            "share_count": statistics.get("share_count", 0),
            "collect_count": statistics.get("collect_count", 0),
            "create_time": item.get("create_time"),
        }
