import asyncio
import yt_dlp
import os
from bilibili_api import search
from config import Config

class BilibiliService:
    def __init__(self):
        self.temp_dir = Config.TEMP_DIR
    
    async def search_videos(self, keyword: str, page: int = 1) -> list:
        """search_videos -
        搜索B站视频"""
        try:
            result = await search.search_by_type(
                keyword=keyword,
                search_type=search.SearchObjectType.VIDEO,
                page=page,
                page_size=20
            )

            videos_info = []
            for item in result["result"]:
                videos_info.append({
                    "title": item.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
                    "bvid": item.get("bvid"),
                    "url": f"https://www.bilibili.com/video/{item.get('bvid')}",
                    "author": item.get("author", "未知"),
                    "play_count": item.get("play", 0),
                    "duration": item.get("duration", "未知"),
                    "description": item.get("description", ""),
                    "pic": "https:" + item.get("pic", ""),
                })
            return videos_info

        except Exception as e:
            print(f"❌ 搜索出错: {e}")
            return []
    
    async def download_video(self, url: str) -> str:
        """download_video -
        下载视频到临时文件"""
        temp_file = os.path.join(self.temp_dir, "temp_video.mp4")
        ydl_opts = {
            "format": Config.VIDEO_QUALITY,
            "outtmpl": temp_file,
            "quiet": False,
            "merge_output_format": "mp4",
        }

        loop = asyncio.get_event_loop()

        def run_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)

        await loop.run_in_executor(None, run_download)
        return temp_file
    
    def get_video_size(self, file_path: str) -> float:
        """get_video_size -
        获取视频文件大小（MB）"""
        return os.path.getsize(file_path) / (1024 * 1024)
    
    def cleanup_temp_file(self, file_path: str):
        """cleanup_temp_file -
        清理临时文件"""
        if os.path.exists(file_path):
            os.remove(file_path)