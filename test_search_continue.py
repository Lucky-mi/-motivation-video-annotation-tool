#!/usr/bin/env python3
"""
测试新的搜索逻辑：持续搜索直到找到足够的新视频
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.downloader import VideoDownloader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_continuous_search():
    """测试持续搜索功能"""
    dl = VideoDownloader()

    print("\n" + "="*60)
    print("测试：持续搜索直到找到足够的新视频")
    print("="*60)

    # 显示数据库状态
    existing_count = len(dl.links_db["videos"])
    print(f"数据库中已有视频: {existing_count} 个\n")

    # 测试搜索
    keyword = "people arguing"
    target = 5

    print(f"搜索关键词: {keyword}")
    print(f"目标数量: {target} 个新视频\n")

    results = dl.search_videos(keyword, limit=target)

    print("\n" + "="*60)
    print("搜索结果")
    print("="*60)
    print(f"找到新视频: {len(results)} 个")

    if results:
        print("\n新视频列表:")
        for i, video in enumerate(results, 1):
            print(f"  {i}. {video['title'][:60]}...")
            print(f"     时长: {video['duration']}秒 | 频道: {video['channel']}")

    # 验证是否达到目标
    if len(results) >= target:
        print(f"\n✅ 成功：找到了 {len(results)} 个新视频（目标: {target}）")
    else:
        print(f"\n⚠️ 警告：只找到 {len(results)} 个新视频（目标: {target}）")
        print("   可能是因为：")
        print("   1. 搜索结果中大部分已存在")
        print("   2. 很多视频时长不符合要求")
        print("   3. 达到了最大搜索数量限制")

    print("\n" + "="*60)


if __name__ == "__main__":
    test_continuous_search()
