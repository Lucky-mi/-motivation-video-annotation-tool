# backend/downloader.py
"""
视频下载器 & 搜索器 - 基于 yt-dlp
专注于心智理论（Theory of Mind）相关的视频内容搜索和下载
"""
import yt_dlp
from pathlib import Path
import uuid
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoDownloader:
    """YouTube视频下载器 - 专注于心智理论研究视频"""

    # 心智理论相关的核心搜索关键词（更专业、更全面）
    THEORY_OF_MIND_KEYWORDS = [
        # 社交互动与心理推理
        "social interaction theory of mind",
        "people understanding emotions",
        "human interaction psychology",
        "interpersonal communication psychology",
        "emotional intelligence social",
        "reading facial expressions",
        "body language interpretation",
        "social cues understanding",

        # 情绪与动机推理
        "understanding human motivation",
        "human desire and intention",
        "implicit motivation psychology",
        "emotional reasoning",
        "intention recognition psychology",
        "goal-directed behavior",
        "mental states understanding",

        # 日常生活场景
        "everyday social situations",
        "real life social dilemmas",
        "human behavior psychology daily",
        "social decision making",
        "moral reasoning scenarios",
        "helping behavior psychology",
        "conflict resolution interaction",

        # 戏剧与叙事
        "short drama psychological",
        "psychology mini movie",
        "character motivation film",
        "psychological short film",
        "social experiment video",
        "human nature story",

        # 实验与教育
        "psychology experiment social",
        "theory of mind demonstration",
        "false belief task video",
        "perspective taking exercise",
        "empathy training video",
        "cognitive psychology demonstration"
    ]

    def __init__(self, output_dir: str = "data/Youtube_videos", links_file: str = "data/youtube_links.json"):
        """
        初始化下载器

        Args:
            output_dir: 视频保存目录
            links_file: 链接记录文件路径
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.links_file = Path(links_file)
        self.links_file.parent.mkdir(parents=True, exist_ok=True)

        # 加载已有链接记录
        self.links_db = self._load_links_database()

    def _load_links_database(self) -> Dict:
        """加载链接数据库"""
        if self.links_file.exists():
            try:
                with open(self.links_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载链接数据库失败: {e}，创建新数据库")

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

    def _save_links_database(self):
        """保存链接数据库"""
        self.links_db["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(self.links_file, 'w', encoding='utf-8') as f:
            json.dump(self.links_db, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 链接数据库已保存到: {self.links_file}")

    def add_video_link(self, url: str, title: str, duration: float,
                      keyword: str, approved: Optional[bool] = None,
                      review_reason: Optional[str] = None) -> bool:
        """
        添加视频链接到数据库

        Args:
            url: 视频URL
            title: 视频标题
            duration: 视频时长（秒）
            keyword: 搜索关键词
            approved: AI审核是否通过
            review_reason: 审核理由

        Returns:
            是否成功添加（False表示重复）
        """
        # 检查是否已存在
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
            "downloaded": False,
            "video_path": None,
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
        """
        从URL下载视频

        Args:
            url: 视频URL
            video_id: 可选的自定义视频ID

        Returns:
            包含下载信息的字典
        """
        if not video_id:
            video_id = str(uuid.uuid4())

        # 输出模板：data/Youtube_videos/{video_id}.mp4
        out_tmpl = str(self.output_dir / f"{video_id}.%(ext)s")

        # 使用更宽松和稳定的格式选择策略
        ydl_opts = {
            # 格式选择：尝试多种备选方案，确保总能下载到视频
            'format': (
                'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/'
                'bestvideo[height<=720]+bestaudio/best[height<=720]/'
                'best'  # 最后的兜底选项
            ),
            'outtmpl': out_tmpl,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,  # 不忽略错误，以便我们能捕获并处理
            # 添加字幕下载
            'writesubtitles': False,  # 暂时禁用字幕下载，避免额外错误
            'writeautomaticsub': False,
            # 使用最稳定的配置
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],  # android最稳定，web作为备选
                    'skip': ['hls', 'dash']  # 跳过复杂流媒体格式
                }
            },
            # 添加这些选项提高成功率
            'http_chunk_size': 10485760,  # 10MB chunks
            'retries': 3,  # 重试3次
        }

        try:
            logger.info(f"⬇️ 开始下载: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 1. 提取信息并下载
                info = ydl.extract_info(url, download=True)

                # 2. 获取实际文件名
                filename = ydl.prepare_filename(info)
                final_path = Path(filename)

                logger.info(f"✅ 下载完成: {final_path.name}")

                result = {
                    "video_id": video_id,
                    "video_path": str(final_path).replace('\\', '/'),
                    "title": info.get('title', 'Unknown'),
                    "duration": info.get('duration', 0),
                    "uploader": info.get('uploader', 'Unknown'),
                    "description": info.get('description', '')[:500],
                    "view_count": info.get('view_count', 0),
                    "like_count": info.get('like_count', 0)
                }

                # 更新数据库中的下载状态
                for video in self.links_db["videos"]:
                    if video["url"] == url:
                        video["downloaded"] = True
                        video["video_path"] = result["video_path"]
                        self.links_db["metadata"]["downloaded_count"] += 1
                        break

                self._save_links_database()
                return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ 下载失败: {error_msg}")

            # 如果是格式问题，尝试使用最简单的格式
            if "Requested format is not available" in error_msg:
                logger.info("  🔄 尝试使用备用格式...")
                try:
                    # 使用最简单的格式选择
                    fallback_opts = ydl_opts.copy()
                    fallback_opts['format'] = 'best'  # 最简单的选择

                    with yt_dlp.YoutubeDL(fallback_opts) as ydl_fallback:
                        info = ydl_fallback.extract_info(url, download=True)
                        filename = ydl_fallback.prepare_filename(info)
                        final_path = Path(filename)

                        logger.info(f"✅ 备用格式下载成功: {final_path.name}")

                        result = {
                            "video_id": video_id,
                            "video_path": str(final_path).replace('\\', '/'),
                            "title": info.get('title', 'Unknown'),
                            "duration": info.get('duration', 0),
                            "uploader": info.get('uploader', 'Unknown'),
                            "description": info.get('description', '')[:500],
                            "view_count": info.get('view_count', 0),
                            "like_count": info.get('like_count', 0)
                        }

                        for video in self.links_db["videos"]:
                            if video["url"] == url:
                                video["downloaded"] = True
                                video["video_path"] = result["video_path"]
                                self.links_db["metadata"]["downloaded_count"] += 1
                                break

                        self._save_links_database()
                        return result

                except Exception as e2:
                    logger.error(f"❌ 备用格式也失败: {str(e2)}")
                    raise ValueError(f"下载失败（已尝试备用格式）: {str(e2)}")

            raise ValueError(f"下载失败: {error_msg}")

    def search_videos(self, keyword: str, limit: int = 5,
                     min_duration: int = 30, max_duration: int = 300) -> List[Dict]:
        """
        根据关键词搜索视频链接（带时长过滤）

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量
            min_duration: 最小时长（秒）
            max_duration: 最大时长（秒，默认5分钟）

        Returns:
            符合条件的视频列表
        """
        logger.info(f"🔍 正在搜索: {keyword} (Limit: {limit}, Duration: {min_duration}-{max_duration}s)")
        links = []

        # yt-dlp 配置：只提取信息，不下载（使用更稳定的配置）
        ydl_opts = {
            'quiet': True,
            'extract_flat': 'in_playlist',  # 使用flat模式，只获取基本信息
            'skip_download': True,
            'no_warnings': True,
            'ignoreerrors': True,  # 忽略单个视频错误
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],  # 使用android客户端最稳定
                    'skip': ['hls', 'dash']  # 跳过复杂格式
                }
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # 多搜一些作为备选，方便过滤
                fetch_count = min(limit * 5, 100)  # 增加备选数量以弥补flat模式信息不全
                search_query = f"ytsearch{fetch_count}:{keyword}"

                result = ydl.extract_info(search_query, download=False)

                if 'entries' in result:
                    for entry in result['entries']:
                        if not entry:  # 跳过空条目
                            continue

                        # flat模式下可能没有duration，需要单独获取
                        video_id = entry.get('id')
                        if not video_id:
                            continue

                        # 构建完整URL
                        video_url = f"https://www.youtube.com/watch?v={video_id}"

                        # 尝试获取详细信息（包括时长）
                        try:
                            # 只获取时长信息，不下载
                            detail_opts = {
                                'quiet': True,
                                'skip_download': True,
                                'no_warnings': True,
                                'extractor_args': {
                                    'youtube': {
                                        'player_client': ['android']
                                    }
                                }
                            }
                            with yt_dlp.YoutubeDL(detail_opts) as detail_ydl:
                                info = detail_ydl.extract_info(video_url, download=False)
                                duration = info.get('duration', 0)

                                # 检查时长是否符合要求
                                if duration and (min_duration <= duration <= max_duration) and not info.get('is_live', False):
                                    links.append({
                                        "url": video_url,
                                        "id": video_id,
                                        "title": info.get('title') or entry.get('title', 'Unknown'),
                                        "duration": duration,
                                        "channel": info.get('uploader') or entry.get('uploader', 'Unknown'),
                                        "view_count": info.get('view_count', 0),
                                        "description": info.get('description', '')[:200]
                                    })

                                    # 凑够数量就停
                                    if len(links) >= limit:
                                        break
                        except Exception as e:
                            # 单个视频获取失败，继续下一个
                            logger.debug(f"跳过视频 {video_id}: {e}")
                            continue

            except Exception as e:
                logger.error(f"搜索出错: {e}")

        logger.info(f"✅ 搜索完成，筛选出 {len(links)} 个视频")
        return links

    def batch_search(self, keywords: Optional[List[str]] = None,
                    videos_per_keyword: int = 3,
                    enable_smart_dedup: bool = True,
                    allow_same_series: bool = False,
                    max_per_series: int = 2) -> List[Dict]:
        """
        批量搜索多个关键词（支持智能去重）

        Args:
            keywords: 关键词列表（None则使用默认的心智理论关键词）
            videos_per_keyword: 每个关键词搜索的视频数量
            enable_smart_dedup: 是否启用智能去重（识别同一剧集/电影）
            allow_same_series: 是否允许同一剧集的多个片段
            max_per_series: 同一剧集最多保留几个片段

        Returns:
            所有搜索结果的列表
        """
        if keywords is None:
            keywords = self.THEORY_OF_MIND_KEYWORDS

        all_videos = []
        logger.info(f"🚀 开始批量搜索，共 {len(keywords)} 个关键词")
        logger.info(f"⚙️ 智能去重: {'启用' if enable_smart_dedup else '禁用'} | 同剧集片段: {'允许(最多{})'.format(max_per_series) if allow_same_series else '不允许'}")

        for idx, keyword in enumerate(keywords, 1):
            logger.info(f"[{idx}/{len(keywords)}] 搜索关键词: {keyword}")
            try:
                videos = self.search_videos(keyword, limit=videos_per_keyword)
                for video in videos:
                    video['search_keyword'] = keyword
                all_videos.extend(videos)
            except Exception as e:
                logger.error(f"搜索关键词 '{keyword}' 失败: {e}")
                continue

        logger.info(f"📊 搜索完成: 共找到 {len(all_videos)} 个候选视频")

        # 智能去重
        if enable_smart_dedup:
            try:
                from .deduplicator import VideoDeduplicator
                deduplicator = VideoDeduplicator()

                # 执行智能去重
                unique_videos = deduplicator.deduplicate_list(
                    all_videos,
                    allow_same_series=allow_same_series,
                    max_per_series=max_per_series
                )

                # 显示统计
                stats = deduplicator.get_statistics()
                logger.info(f"🎯 智能去重完成:")
                logger.info(f"   - 总视频: {len(all_videos)} 个")
                logger.info(f"   - 去重后: {len(unique_videos)} 个")
                logger.info(f"   - 移除重复: {len(all_videos) - len(unique_videos)} 个")
                logger.info(f"   - 唯一剧集/电影: {stats['unique_series']} 部")

                return unique_videos

            except ImportError:
                logger.warning("⚠️ 无法导入去重模块，使用基础去重")

        # 基础去重（仅基于URL）
        seen_urls = set()
        unique_videos = []
        for video in all_videos:
            if video['url'] not in seen_urls:
                seen_urls.add(video['url'])
                unique_videos.append(video)

        logger.info(f"🎉 批量搜索完成！总共找到 {len(all_videos)} 个视频，去重后 {len(unique_videos)} 个")
        return unique_videos

    def get_pending_review_videos(self) -> List[Dict]:
        """获取待审核的视频列表"""
        return [v for v in self.links_db["videos"] if v["approved"] is None]

    def get_approved_videos(self, downloaded_only: bool = False) -> List[Dict]:
        """获取已通过审核的视频列表"""
        approved = [v for v in self.links_db["videos"] if v["approved"] is True]
        if downloaded_only:
            return [v for v in approved if v["downloaded"]]
        return approved

    def update_video_status(self, url: str, approved: bool, review_reason: str = ""):
        """更新视频审核状态"""
        for video in self.links_db["videos"]:
            if video["url"] == url:
                old_status = video["approved"]
                video["approved"] = approved
                video["review_reason"] = review_reason

                # 更新统计
                if old_status is None:
                    if approved:
                        self.links_db["metadata"]["approved_count"] += 1
                    else:
                        self.links_db["metadata"]["rejected_count"] += 1

                self._save_links_database()
                logger.info(f"✅ 已更新视频状态: {approved} - {video['title'][:50]}")
                return True

        logger.warning(f"⚠️ 未找到视频: {url}")
        return False


if __name__ == "__main__":
    # 测试代码
    dl = VideoDownloader()

    # 测试搜索单个关键词
    # videos = dl.search_videos("social interaction psychology", limit=2)
    # print(json.dumps(videos, indent=2, ensure_ascii=False))

    # 测试批量搜索（小规模测试）
    # test_keywords = dl.THEORY_OF_MIND_KEYWORDS[:3]
    # results = dl.batch_search(keywords=test_keywords, videos_per_keyword=2)
    # print(f"找到 {len(results)} 个视频")