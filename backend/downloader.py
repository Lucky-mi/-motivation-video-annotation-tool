# backend/downloader.py
"""
视频下载器 & 搜索器 - 基于 yt-dlp
修复版：解决 NoneType 错误 + 自动重试
"""
import yt_dlp
from pathlib import Path
import uuid
import logging
import json
import time
import random
from typing import List, Dict, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoDownloader:
    """YouTube视频下载器"""

    THEORY_OF_MIND_KEYWORDS = [
        "social interaction theory of mind",
        "people understanding emotions",
        "human interaction psychology",
        "interpersonal communication psychology",
        "emotional intelligence social",
        "reading facial expressions",
        "body language interpretation",
        "social cues understanding",
        "understanding human motivation",
        "human desire and intention",
        "implicit motivation psychology",
        "emotional reasoning",
        "intention recognition psychology",
        "goal-directed behavior",
        "mental states understanding",
        "everyday social situations",
        "real life social dilemmas",
        "human behavior psychology daily",
        "social decision making",
        "moral reasoning scenarios",
        "helping behavior psychology",
        "conflict resolution interaction",
        "short drama psychological",
        "psychology mini movie",
        "character motivation film",
        "psychological short film",
        "social experiment video",
        "human nature story",
        "psychology experiment social",
        "theory of mind demonstration",
        "false belief task video",
        "perspective taking exercise",
        "empathy training video",
        "cognitive psychology demonstration"
    ]

    def __init__(self, output_dir: str = "data/Youtube_videos",
                 links_file: str = "data/youtube_links.json",
                 search_history_file: str = "data/searched_history.json",
                 request_delay: tuple = (1, 3)):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.links_file = Path(links_file)
        self.links_file.parent.mkdir(parents=True, exist_ok=True)

        # 搜索历史文件（记录所有搜索过的视频URL）
        self.search_history_file = Path(search_history_file)
        self.search_history_file.parent.mkdir(parents=True, exist_ok=True)

        self.request_delay = request_delay
        self._request_count = 0
        self._rate_limited = False
        self._consecutive_rate_limits = 0

        self.links_db = self._load_links_database()
        self.search_history = self._load_search_history()

    def _apply_rate_limit(self):
        """自适应请求延迟"""
        self._request_count += 1

        if self._rate_limited:
            base_delay = random.uniform(2.0, 4.0)
            time.sleep(base_delay)
            if self._request_count % 5 == 0:
                extra_delay = random.uniform(5.0, 10.0)
                logger.info(f"  ⏳ [限流模式] 休息 {extra_delay:.1f}s")
                time.sleep(extra_delay)
        else:
            if self._request_count % 10 == 0:
                time.sleep(random.uniform(1, 2))

    def _handle_rate_limit_error(self):
        """处理速率限制"""
        self._consecutive_rate_limits += 1
        if not self._rate_limited:
            logger.warning(f"⚠️ 检测到YouTube速率限制！切换到慢速模式...")
            self._rate_limited = True

        wait_time = min(30 * self._consecutive_rate_limits, 180)
        logger.warning(f"  💤 等待 {wait_time}s 后继续...")
        time.sleep(wait_time)

    def _reset_rate_limit(self):
        """重置速率限制状态"""
        if self._consecutive_rate_limits > 0:
            self._consecutive_rate_limits = max(0, self._consecutive_rate_limits - 1)
            if self._consecutive_rate_limits == 0 and self._rate_limited:
                logger.info("  ✅ 速率限制已解除")
                self._rate_limited = False

    def _get_base_opts(self) -> dict:
        opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'retries': 5,
            'socket_timeout': 30,
            'sleep_interval': 3,
            'max_sleep_interval': 10,
            'sleep_interval_requests': 1,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        cookies_path = Path("cookies.txt")
        if cookies_path.exists():
            opts['cookiefile'] = str(cookies_path)
            
        return opts

    def _load_links_database(self) -> Dict:
        if self.links_file.exists():
            try:
                with open(self.links_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载链接数据库失败: {e}")

        return {
            "videos": [],
            "metadata": {
                "total_count": 0,
                "approved_count": 0,
                "rejected_count": 0,
                "downloaded_count": 0,
                "last_updated": None
            }
        }

    def _load_search_history(self) -> Dict:
        """加载搜索历史（记录所有搜索过的视频URL，防止重复搜索）"""
        if self.search_history_file.exists():
            try:
                with open(self.search_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载搜索历史失败: {e}")

        return {
            "searched_urls": {},  # {url: {"title": ..., "first_seen": ..., "keyword": ...}}
            "metadata": {
                "total_searched": 0,
                "last_updated": None
            }
        }

    def _save_search_history(self):
        """保存搜索历史"""
        self.search_history["metadata"]["last_updated"] = datetime.now().isoformat()
        self.search_history["metadata"]["total_searched"] = len(self.search_history["searched_urls"])

        with open(self.search_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.search_history, f, ensure_ascii=False, indent=2)

    def add_to_search_history(self, video_info: Dict, keyword: str):
        """将视频添加到搜索历史"""
        url = video_info['url']
        if url not in self.search_history["searched_urls"]:
            self.search_history["searched_urls"][url] = {
                "title": video_info.get('title', 'Unknown'),
                "channel": video_info.get('channel', 'Unknown'),
                "duration": video_info.get('duration', 0),
                "first_seen": datetime.now().isoformat(),
                "keyword": keyword
            }

    def is_searched_before(self, url: str) -> bool:
        """检查URL是否已经搜索过"""
        return url in self.search_history["searched_urls"]

    def _save_links_database(self):
        self.links_db["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(self.links_file, 'w', encoding='utf-8') as f:
            json.dump(self.links_db, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 链接数据库已保存")

    def add_video_link(self, url: str, title: str, duration: float,
                      keyword: str, approved: Optional[bool] = None,
                      review_reason: Optional[str] = None,
                      video_path: Optional[str] = None) -> bool:
        """
        添加视频链接到数据库

        Args:
            video_path: 视频文件路径（如果已下载）
        """
        if any(v["url"] == url for v in self.links_db["videos"]):
            logger.info(f"⚠️ 视频已存在: {url}")
            return False

        video_entry = {
            "url": url,
            "title": title,
            "duration": duration,
            "keyword": keyword,
            "approved": approved,
            "review_reason": review_reason,
            "downloaded": video_path is not None,  # 如果有路径，说明已下载
            "video_path": video_path,
            "added_time": datetime.now().isoformat()
        }

        self.links_db["videos"].append(video_entry)
        self.links_db["metadata"]["total_count"] += 1

        if approved is True:
            self.links_db["metadata"]["approved_count"] += 1
        elif approved is False:
            self.links_db["metadata"]["rejected_count"] += 1

        logger.info(f"✅ 已添加视频: {title[:50]}...")
        return True

    def download_from_url(self, url: str, video_id: Optional[str] = None) -> dict:
        """从URL下载视频（集成质量检查）"""
        # ... (前面的查重逻辑保持不变) ...
        # 检查是否已下载
        for video in self.links_db["videos"]:
            if video["url"] == url and video.get("downloaded", False):
                video_path = Path(video.get("video_path", ""))
                if video_path.exists():
                    logger.info(f"⏭️ 视频已存在，跳过: {video_path.name}")
                    return {
                        "video_id": video.get("video_id", str(uuid.uuid4())),
                        "video_path": str(video_path).replace('\\', '/'),
                        "title": video.get("title", "Unknown"),
                        "duration": video.get("duration", 0),
                        "uploader": video.get("channel", "Unknown"),
                        "skipped": True
                    }

        self._apply_rate_limit()

        if not video_id:
            video_id = str(uuid.uuid4())

        out_tmpl = str(self.output_dir / f"{video_id}.%(ext)s")

        # 使用最佳兼容性配置
        ydl_opts = self._get_base_opts()
        ydl_opts.update({
            'format': 'best[ext=mp4]/best',     # 下载最佳单一文件(含音频)，避免合并
            'outtmpl': out_tmpl,
            'noplaylist': True,
            'ignoreerrors': False, # 既然要检查质量，就不要忽略错误
            'writesubtitles': False,
        })

        try:
            logger.info(f"⬇️ 开始下载: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if info is None:
                    raise Exception("无法获取视频信息")

                self._reset_rate_limit()

                filename = ydl.prepare_filename(info)
                final_path = Path(filename)

                # ================= 🔍 新增：质量检查环节 =================
                if not self._verify_download(str(final_path), min_size_mb=0.5): # 0.5MB 是最低底线
                    # 校验失败，尝试删除坏文件
                    if final_path.exists():
                        final_path.unlink()
                    raise Exception("下载文件校验失败（文件损坏或为空）")
                # =======================================================

                logger.info(f"✅ 下载成功且校验通过: {final_path.name}")

                result = {
                    "video_id": video_id,
                    "video_path": str(final_path).replace('\\', '/'),
                    "title": info.get('title', 'Unknown'),
                    "duration": info.get('duration', 0),
                    "uploader": info.get('uploader', 'Unknown'),
                    "description": (info.get('description') or '')[:500],
                    "view_count": info.get('view_count', 0),
                    "like_count": info.get('like_count', 0)
                }

                # 更新数据库
                for video in self.links_db["videos"]:
                    if video["url"] == url:
                        video["downloaded"] = True
                        video["video_path"] = str(final_path)
                        self.links_db["metadata"]["downloaded_count"] += 1
                        break

                self._save_links_database()
                return result

        except Exception as e:
            # ... (错误处理逻辑保持不变) ...
            error_msg = str(e)
            if "rate-limited" in error_msg.lower():
                self._handle_rate_limit_error()
                raise Exception("速率限制")
            
            # 如果是校验失败抛出的异常，直接上报
            if "校验失败" in error_msg:
                 raise

            # 尝试 fallback
            if "format" in error_msg.lower() or "not available" in error_msg.lower():
                logger.info(f"  🔄 尝试备用下载...")
                return self._download_fallback(url, video_id, out_tmpl)
            
            raise
    def _verify_download(self, file_path: str, min_size_mb: float = 1.0) -> bool:
        """
        验证下载的文件是否有效
        1. 检查文件是否存在
        2. 检查文件大小是否正常 (默认最小 1MB)
        3. 检查文件头是否合法 (简单的视频格式验证)
        """
        path = Path(file_path)
        
        # 1. 检查存在性
        if not path.exists():
            logger.error(f"❌ 校验失败: 文件不存在 {path}")
            return False
            
        # 2. 检查文件大小
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb < min_size_mb:
            logger.error(f"❌ 校验失败: 文件过小 ({file_size_mb:.2f} MB < {min_size_mb} MB) -> {path.name}")
            return False
            
        # 3. 检查文件头 (Magic Numbers) - 避免下载成纯文本报错信息
        # 常见的视频容器头部签名
        valid_signatures = {
            'mp4': [b'\x00\x00\x00\x18ftyp', b'\x00\x00\x00\x20ftyp', b'\x00\x00\x00\x14ftyp'], # MP4/MOV
            'mkv': [b'\x1A\x45\xDF\xA3'], # Matroska/WebM
            'avi': [b'RIFF'],
        }
        
        try:
            with open(path, 'rb') as f:
                header = f.read(16) # 读取前16个字节
                
                is_valid = False
                for fmt, sigs in valid_signatures.items():
                    for sig in sigs:
                        if header.startswith(sig):
                            is_valid = True
                            break
                    if is_valid: break
                
                if not is_valid:
                    # 宽松检查：如果大小足够大，但头不对，可能只是格式特殊，打个警告但通过
                    if file_size_mb > 5.0:
                        logger.warning(f"⚠️ 文件头未知，但大小正常，予以通过: {header.hex()[:8]}...")
                        return True
                        
                    logger.error(f"❌ 校验失败: 无效的视频文件头 {header.hex()[:16]}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 校验出错: {e}")
            return False
            
        return True
    def _download_fallback(self, url: str, video_id: str, out_tmpl: str) -> dict:
        """备用下载"""
        ydl_opts = {
            'format': 'best',
            'outtmpl': out_tmpl,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
        }
        
        cookies_path = Path("cookies.txt")
        if cookies_path.exists():
            ydl_opts['cookiefile'] = str(cookies_path)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if info is None:
                    raise Exception("备用方式也无法下载")

                self._reset_rate_limit()

                filename = ydl.prepare_filename(info)
                final_path = Path(filename)

                logger.info(f"✅ 备用下载成功: {final_path.name}")

                return {
                    "video_id": video_id,
                    "video_path": str(final_path).replace('\\', '/'),
                    "title": info.get('title', 'Unknown'),
                    "duration": info.get('duration', 0),
                    "uploader": info.get('uploader', 'Unknown'),
                    "description": (info.get('description') or '')[:500],
                    "view_count": info.get('view_count', 0),
                    "like_count": info.get('like_count', 0)
                }

        except Exception as e:
            error_msg = str(e)
            if "rate-limited" in error_msg.lower():
                self._handle_rate_limit_error()
            raise Exception(f"下载失败: {e}")

    def search_videos(self, keyword: str, limit: int = 10,
                     min_duration: int = 30, max_duration: int = 300,
                     skip_searched: bool = True) -> List[Dict]:
        """
        搜索YouTube视频（改进版：确保找到足够数量的新视频）

        Args:
            keyword: 搜索关键词
            limit: 需要找到的新视频数量
            min_duration: 最小时长（秒）
            max_duration: 最大时长（秒）
            skip_searched: 是否跳过搜索历史中的视频（默认True）

        Returns:
            新视频列表（未在搜索历史中的）
        """
        self._apply_rate_limit()

        logger.info(f"🔍 正在搜索: {keyword} (目标: {limit} 个新视频, 时长: {min_duration}-{max_duration}s)")
        links = []

        if not hasattr(self, 'links_db') or "videos" not in self.links_db:
            self.links_db = {"videos": []}

        if not hasattr(self, 'search_history') or "searched_urls" not in self.search_history:
            self.search_history = {"searched_urls": {}}

        # 获取已搜索过的URL集合（防止重复搜索）
        searched_urls = set(self.search_history["searched_urls"].keys()) if skip_searched else set()

        # 动态扩大搜索范围，直到找到足够的新视频
        search_multiplier = 3
        max_search_attempts = 5

        ydl_opts = self._get_base_opts()
        ydl_opts.update({
            'extract_flat': True,
            'skip_download': True,
            'ignoreerrors': True,
        })

        # 统计信息
        total_found = 0
        skipped_searched = 0

        for search_attempt in range(max_search_attempts):
            if len(links) >= limit:
                logger.info(f"✅ 已找到足够的新视频: {len(links)}/{limit}")
                break

            # 动态增加搜索数量
            search_count = limit * search_multiplier
            search_query = f"ytsearch{search_count}:{keyword}"

            logger.info(f"  🔄 搜索尝试 {search_attempt + 1}/{max_search_attempts}: 请求 {search_count} 个结果")

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        result = ydl.extract_info(search_query, download=False)

                        # 空值检查
                        if result is None:
                            if attempt < max_retries - 1:
                                wait_time = (attempt + 1) * 10
                                logger.warning(f"⚠️ 搜索返回空，{wait_time}秒后重试... ({attempt + 1}/{max_retries})")
                                time.sleep(wait_time)
                                continue
                            else:
                                logger.error(f"❌ 搜索失败，请检查网络/VPN")
                                return []

                        # 获取entries
                        entries = result.get('entries')
                        if entries is None:
                            logger.warning(f"⚠️ 无搜索结果")
                            break

                        # 遍历结果（加强防护）
                        for entry in entries:
                            if len(links) >= limit:
                                break

                            # 跳过None或非字典条目
                            if entry is None or not isinstance(entry, dict):
                                continue

                            try:
                                video_id = entry.get('id')
                                if not video_id:
                                    continue

                                video_url = f"https://www.youtube.com/watch?v={video_id}"
                                total_found += 1

                                # 跳过已搜索过的视频（关键改进！）
                                if video_url in searched_urls:
                                    skipped_searched += 1
                                    continue

                                duration = entry.get('duration')
                                if duration is None:
                                    continue

                                if min_duration <= duration <= max_duration:
                                    # 安全获取各字段
                                    title = entry.get('title')
                                    if title is None:
                                        title = 'Unknown'

                                    channel = entry.get('uploader')
                                    if channel is None:
                                        channel = 'Unknown'

                                    view_count = entry.get('view_count')
                                    if view_count is None:
                                        view_count = 0

                                    desc = entry.get('description')
                                    if desc is None or not isinstance(desc, str):
                                        desc = ''
                                    else:
                                        desc = desc[:200]

                                    video_info = {
                                        "url": video_url,
                                        "id": video_id,
                                        "title": title,
                                        "duration": duration,
                                        "channel": channel,
                                        "view_count": view_count,
                                        "description": desc
                                    }

                                    links.append(video_info)

                                    # 立即添加到搜索历史（防止同一轮搜索中重复）
                                    self.add_to_search_history(video_info, keyword)

                            except Exception as entry_error:
                                logger.debug(f"跳过异常条目: {entry_error}")
                                continue

                        # 成功，跳出重试
                        break

                except Exception as e:
                    error_msg = str(e)

                    if "rate-limited" in error_msg.lower() or "try again later" in error_msg.lower():
                        self._handle_rate_limit_error()
                        if attempt < max_retries - 1:
                            continue

                    logger.error(f"❌ 搜索异常: {error_msg[:100]}")

                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        logger.info(f"  🔄 {wait_time}秒后重试...")
                        time.sleep(wait_time)
                    else:
                        break

            # 如果本次搜索没有找到足够的新视频，增加下次搜索范围
            if len(links) < limit:
                search_multiplier += 2

        # 保存搜索历史
        self._save_search_history()

        # 输出统计信息
        logger.info(f"✅ 搜索完成: 找到 {len(links)} 个新视频")
        if skipped_searched > 0:
            logger.info(f"   ⏭️  跳过 {skipped_searched} 个已搜索过的视频")
        if len(links) < limit:
            logger.warning(f"   ⚠️  未达到目标数量 ({len(links)}/{limit})，可能需要更换关键词")

        return links

    def batch_search(self, keywords: Optional[List[str]] = None,
                    videos_per_keyword: int = 3,
                    enable_smart_dedup: bool = True,
                    allow_same_series: bool = False,
                    max_per_series: int = 2) -> List[Dict]:
        """批量搜索"""
        if keywords is None:
            keywords = self.THEORY_OF_MIND_KEYWORDS

        all_videos = []
        logger.info(f"🚀 开始批量搜索，共 {len(keywords)} 个关键词")

        for idx, keyword in enumerate(keywords, 1):
            logger.info(f"[{idx}/{len(keywords)}] 搜索: {keyword}")
            try:
                videos = self.search_videos(keyword, limit=videos_per_keyword)
                for video in videos:
                    video['search_keyword'] = keyword
                all_videos.extend(videos)
            except Exception as e:
                logger.error(f"搜索 '{keyword}' 失败: {e}")
                continue

        logger.info(f"📊 搜索完成: {len(all_videos)} 个")

        if enable_smart_dedup:
            try:
                from .deduplicator import VideoDeduplicator
                deduplicator = VideoDeduplicator()
                return deduplicator.deduplicate_list(
                    all_videos,
                    allow_same_series=allow_same_series,
                    max_per_series=max_per_series
                )
            except ImportError:
                pass

        seen_urls = set()
        unique_videos = []
        for video in all_videos:
            if video['url'] not in seen_urls:
                seen_urls.add(video['url'])
                unique_videos.append(video)

        logger.info(f"🎉 去重后 {len(unique_videos)} 个")
        return unique_videos

    def get_pending_review_videos(self) -> List[Dict]:
        return [v for v in self.links_db["videos"] if v["approved"] is None]

    def get_approved_videos(self, downloaded_only: bool = False) -> List[Dict]:
        approved = [v for v in self.links_db["videos"] if v["approved"] is True]
        if downloaded_only:
            return [v for v in approved if v["downloaded"]]
        return approved

    def update_video_status(self, url: str, approved: bool, review_reason: str = ""):
        for video in self.links_db["videos"]:
            if video["url"] == url:
                old_status = video["approved"]
                video["approved"] = approved
                video["review_reason"] = review_reason

                if old_status is None:
                    if approved:
                        self.links_db["metadata"]["approved_count"] += 1
                    else:
                        self.links_db["metadata"]["rejected_count"] += 1

                self._save_links_database()
                logger.info(f"✅ 已更新视频状态: {approved}")
                return True

        logger.warning(f"⚠️ 未找到视频: {url}")
        return False


if __name__ == "__main__":
    dl = VideoDownloader()
    print("✅ 下载器初始化成功")