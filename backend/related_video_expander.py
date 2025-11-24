# backend/related_video_expander.py
"""
相关视频扩展器 - 基于高质量视频查找相关内容
"""
import yt_dlp
import logging
from typing import List, Dict, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class RelatedVideoExpander:
    """根据高质量视频扩展相关视频"""

    def __init__(self):
        self.ydl_opts_base = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android']
                }
            }
        }

    def find_related_videos(
        self,
        video_url: str,
        max_related: int = 10,
        min_duration: int = 30,
        max_duration: int = 300
    ) -> List[Dict]:
        """
        查找相关视频

        Args:
            video_url: 原始视频URL
            max_related: 最多返回多少个相关视频
            min_duration: 最小时长（秒）
            max_duration: 最大时长（秒）

        Returns:
            相关视频列表
        """
        related_videos = []

        try:
            # 获取视频详细信息
            with yt_dlp.YoutubeDL(self.ydl_opts_base) as ydl:
                logger.info(f"🔍 获取视频信息: {video_url}")
                info = ydl.extract_info(video_url, download=False)

                # 获取频道ID
                channel_id = info.get('channel_id')
                channel_url = info.get('channel_url')
                uploader = info.get('uploader', '')

                logger.info(f"  频道: {uploader}")

                # 方法1: 搜索同频道的类似视频
                if channel_url:
                    channel_videos = self._get_channel_videos(
                        channel_url,
                        max_videos=max_related * 2,  # 获取更多以便筛选
                        min_duration=min_duration,
                        max_duration=max_duration
                    )
                    related_videos.extend(channel_videos)

                # 方法2: 使用YouTube的相关视频推荐（如果API提供）
                # 注意：yt-dlp可能不直接提供related videos，需要额外处理

            # 去重（排除原始视频）
            seen_ids = {self._extract_video_id(video_url)}
            unique_videos = []

            for video in related_videos:
                video_id = self._extract_video_id(video['url'])
                if video_id not in seen_ids:
                    seen_ids.add(video_id)
                    unique_videos.append(video)
                    if len(unique_videos) >= max_related:
                        break

            logger.info(f"✅ 找到 {len(unique_videos)} 个相关视频")
            return unique_videos

        except Exception as e:
            logger.error(f"❌ 查找相关视频失败: {e}")
            return []

    def _get_channel_videos(
        self,
        channel_url: str,
        max_videos: int,
        min_duration: int,
        max_duration: int
    ) -> List[Dict]:
        """获取频道的视频"""
        videos = []

        try:
            # 获取频道的视频列表
            search_opts = self.ydl_opts_base.copy()
            search_opts['playlistend'] = max_videos

            with yt_dlp.YoutubeDL(search_opts) as ydl:
                logger.info(f"  获取频道视频列表...")
                playlist_info = ydl.extract_info(f"{channel_url}/videos", download=False)

                if not playlist_info or 'entries' not in playlist_info:
                    return videos

                # 逐个获取视频详情
                detail_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'skip_download': True,
                }

                for entry in playlist_info['entries']:
                    if not entry:
                        continue

                    try:
                        video_url = f"https://www.youtube.com/watch?v={entry['id']}"

                        with yt_dlp.YoutubeDL(detail_opts) as detail_ydl:
                            video_info = detail_ydl.extract_info(video_url, download=False)

                            duration = video_info.get('duration', 0)

                            # 时长过滤
                            if duration < min_duration or duration > max_duration:
                                continue

                            # 排除直播
                            if video_info.get('is_live') or video_info.get('was_live'):
                                continue

                            videos.append({
                                'url': video_url,
                                'title': video_info.get('title', ''),
                                'duration': duration,
                                'channel': video_info.get('uploader', ''),
                                'view_count': video_info.get('view_count', 0)
                            })

                            if len(videos) >= max_videos:
                                break

                    except Exception as e:
                        logger.debug(f"  跳过视频 {entry.get('id')}: {e}")
                        continue

        except Exception as e:
            logger.error(f"  获取频道视频失败: {e}")

        return videos

    def _extract_video_id(self, url: str) -> str:
        """从URL提取视频ID"""
        if 'youtube.com/watch?v=' in url:
            return url.split('watch?v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            return url.split('youtu.be/')[1].split('?')[0]
        return url


def expand_from_approved_videos(
    youtube_links_path: str = "data/youtube_links.json",
    confidence_threshold: float = 0.8,
    value_threshold: str = "高",
    max_related_per_video: int = 5
) -> List[Dict]:
    """
    从已通过的高质量视频扩展相关视频

    Args:
        youtube_links_path: youtube_links.json路径
        confidence_threshold: 置信度阈值
        value_threshold: 分析价值阈值（"高"或"中"）
        max_related_per_video: 每个视频最多扩展多少相关视频

    Returns:
        扩展的视频列表
    """
    logger.info("="*80)
    logger.info("📈 从高质量视频扩展相关视频")
    logger.info("="*80)

    # 读取已有的链接数据库
    links_file = Path(youtube_links_path)
    if not links_file.exists():
        logger.error(f"❌ 文件不存在: {youtube_links_path}")
        return []

    with open(links_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    videos = data.get('videos', [])

    # 筛选高质量视频
    high_quality_videos = []
    for video in videos:
        if not video.get('approved'):
            continue

        # 解析审核结果
        review_reason = video.get('review_reason', '')

        # 简单的质量判断（可以改进）
        # 这里假设review_reason包含置信度和价值信息
        # 实际应该解析结构化的审核结果

        # 临时：如果审核通过就认为是高质量
        high_quality_videos.append(video)

    logger.info(f"找到 {len(high_quality_videos)} 个已通过审核的视频")

    if not high_quality_videos:
        logger.warning("⚠️ 没有找到已通过审核的视频")
        return []

    # 扩展相关视频
    expander = RelatedVideoExpander()
    all_related_videos = []
    seen_urls = {v['url'] for v in videos}  # 已有的URL

    for idx, video in enumerate(high_quality_videos, 1):
        logger.info(f"\n[{idx}/{len(high_quality_videos)}] 扩展来自: {video['title'][:60]}...")

        try:
            related = expander.find_related_videos(
                video['url'],
                max_related=max_related_per_video,
                min_duration=30,
                max_duration=300
            )

            # 过滤已存在的
            new_videos = [v for v in related if v['url'] not in seen_urls]

            logger.info(f"  新增 {len(new_videos)} 个相关视频")

            for new_video in new_videos:
                new_video['source'] = 'related_expansion'
                new_video['source_video'] = video['url']
                seen_urls.add(new_video['url'])

            all_related_videos.extend(new_videos)

        except Exception as e:
            logger.error(f"  扩展失败: {e}")
            continue

    logger.info(f"\n✅ 总共扩展了 {len(all_related_videos)} 个新视频")
    return all_related_videos


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="从高质量视频扩展相关视频")
    parser.add_argument(
        "--links-file",
        default="data/youtube_links.json",
        help="youtube_links.json路径"
    )
    parser.add_argument(
        "--max-per-video",
        type=int,
        default=5,
        help="每个视频最多扩展多少相关视频"
    )
    parser.add_argument(
        "--output",
        default="data/expanded_videos.json",
        help="输出文件路径"
    )

    args = parser.parse_args()

    # 扩展视频
    expanded_videos = expand_from_approved_videos(
        youtube_links_path=args.links_file,
        max_related_per_video=args.max_per_video
    )

    if expanded_videos:
        # 保存结果
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True, parents=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(expanded_videos, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 已保存到: {output_path}")

        # 显示统计
        channels = {}
        for video in expanded_videos:
            channel = video.get('channel', 'Unknown')
            channels[channel] = channels.get(channel, 0) + 1

        logger.info(f"\n📊 频道分布 (Top 10):")
        for channel, count in sorted(channels.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {channel}: {count}个视频")

    else:
        logger.warning("\n⚠️ 没有扩展到新视频")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    main()
