# backend/deduplicator.py
"""
视频去重系统 - 避免同一剧集/电影的重复片段
使用多种策略识别相似或重复的内容
"""
import re
from typing import List, Dict, Set
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class VideoDeduplicator:
    """智能视频去重器 - 识别和过滤重复内容"""

    def __init__(self):
        # 已见过的频道+标题组合
        self.seen_channel_titles: Set[str] = set()
        # 已见过的剧集/电影名称
        self.seen_series: Set[str] = set()
        # 已见过的视频ID
        self.seen_ids: Set[str] = set()

    def extract_series_name(self, title: str) -> str:
        """
        从标题中提取剧集/电影名称

        Examples:
            "Breaking Bad - Best Scene" -> "breaking bad"
            "Friends S01E05 - Funny Moment" -> "friends"
            "The Office (US) - Jim and Pam" -> "the office us"
        """
        # 转小写
        title_lower = title.lower()

        # 移除常见的片段标识词
        remove_patterns = [
            r'\s*-\s*.*$',  # 破折号后的内容
            r'\s*\|.*$',    # 竖线后的内容
            r'\s*\(.*?\)',  # 括号内容
            r'\s*\[.*?\]',  # 方括号内容
            r's\d{1,2}e\d{1,2}',  # 剧集编号 S01E05
            r'season\s*\d+',      # Season 1
            r'episode\s*\d+',     # Episode 5
            r'scene\s*\d*',       # Scene
            r'clip\s*\d*',        # Clip
            r'moment\s*\d*',      # Moment
            r'part\s*\d+',        # Part 1
        ]

        cleaned = title_lower
        for pattern in remove_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # 清理多余空格
        cleaned = ' '.join(cleaned.split())

        # 只保留前50个字符（通常剧名不会太长）
        return cleaned[:50].strip()

    def is_duplicate(self, video: Dict) -> bool:
        """
        判断视频是否重复

        Args:
            video: 视频信息字典（必须包含 'id', 'title', 'channel'）

        Returns:
            True if 重复，False if 不重复
        """
        video_id = video.get('id', '')
        title = video.get('title', '')
        channel = video.get('channel', 'Unknown')

        # 检查1: 视频ID重复
        if video_id in self.seen_ids:
            logger.debug(f"重复ID: {video_id}")
            return True

        # 检查2: 频道+标题完全相同
        channel_title_key = f"{channel}::{title}".lower()
        if channel_title_key in self.seen_channel_titles:
            logger.debug(f"重复频道+标题: {channel_title_key}")
            return True

        # 检查3: 剧集名称重复
        series_name = self.extract_series_name(title)
        if series_name:
            # 计算与已有剧集的相似度
            for seen_series in self.seen_series:
                similarity = SequenceMatcher(None, series_name, seen_series).ratio()
                if similarity > 0.85:  # 85%以上相似度认为是同一剧集
                    logger.debug(f"重复剧集: {series_name} ~= {seen_series} (相似度: {similarity:.2f})")
                    return True

        return False

    def add_video(self, video: Dict):
        """
        添加视频到已见列表

        Args:
            video: 视频信息字典
        """
        video_id = video.get('id', '')
        title = video.get('title', '')
        channel = video.get('channel', 'Unknown')

        # 记录ID
        if video_id:
            self.seen_ids.add(video_id)

        # 记录频道+标题
        channel_title_key = f"{channel}::{title}".lower()
        self.seen_channel_titles.add(channel_title_key)

        # 记录剧集名称
        series_name = self.extract_series_name(title)
        if series_name:
            self.seen_series.add(series_name)

    def deduplicate_list(self, videos: List[Dict],
                        allow_same_series: bool = False,
                        max_per_series: int = 1) -> List[Dict]:
        """
        对视频列表进行去重

        Args:
            videos: 视频列表
            allow_same_series: 是否允许同一剧集的多个片段
            max_per_series: 同一剧集最多保留几个片段（如果 allow_same_series=True）

        Returns:
            去重后的视频列表
        """
        unique_videos = []
        series_count = {}  # 记录每个剧集已添加的片段数

        for video in videos:
            # 基础去重（ID和完全相同的标题）
            if self.is_duplicate(video):
                continue

            # 剧集数量限制
            if allow_same_series and max_per_series > 1:
                series_name = self.extract_series_name(video.get('title', ''))
                if series_name:
                    count = series_count.get(series_name, 0)
                    if count >= max_per_series:
                        logger.debug(f"剧集 '{series_name}' 已达到最大数量 {max_per_series}")
                        continue
                    series_count[series_name] = count + 1

            # 添加到结果
            unique_videos.append(video)
            self.add_video(video)

        logger.info(f"去重: {len(videos)} -> {len(unique_videos)} ({len(videos) - len(unique_videos)} 个重复)")
        return unique_videos

    def get_statistics(self) -> Dict:
        """获取去重统计信息"""
        return {
            "unique_videos": len(self.seen_ids),
            "unique_series": len(self.seen_series),
            "unique_channel_titles": len(self.seen_channel_titles)
        }


# 快速测试
if __name__ == "__main__":
    dedup = VideoDeduplicator()

    # 测试数据
    test_videos = [
        {"id": "1", "title": "Breaking Bad - Best Scene", "channel": "Channel A"},
        {"id": "2", "title": "Breaking Bad - Another Scene", "channel": "Channel A"},
        {"id": "3", "title": "Friends S01E05 - Funny Moment", "channel": "Channel B"},
        {"id": "4", "title": "The Office - Jim's Prank", "channel": "Channel C"},
        {"id": "1", "title": "Breaking Bad - Best Scene", "channel": "Channel A"},  # 重复ID
        {"id": "5", "title": "Friends Season 2 - Ross and Rachel", "channel": "Channel B"},  # 同剧集
    ]

    # 测试去重
    unique = dedup.deduplicate_list(test_videos, allow_same_series=True, max_per_series=2)

    print(f"\n原始: {len(test_videos)} 个")
    print(f"去重后: {len(unique)} 个")
    print("\n保留的视频:")
    for v in unique:
        print(f"  - {v['title']}")

    print(f"\n统计: {dedup.get_statistics()}")
