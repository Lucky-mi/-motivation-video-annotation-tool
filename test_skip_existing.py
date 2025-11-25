#!/usr/bin/env python3
"""
测试跳过已存在视频的功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.downloader import VideoDownloader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_skip_existing():
    """测试跳过已存在视频"""
    dl = VideoDownloader(
        output_dir="data/Youtube_videos",
        links_file="data/youtube_links.json"
    )

    print("\n" + "="*60)
    print("测试1: 检查搜索时是否跳过数据库中已有的视频")
    print("="*60)

    # 显示数据库统计
    db_stats = dl.links_db["metadata"]
    print(f"数据库状态:")
    print(f"  总视频数: {db_stats.get('total_count', 0)}")
    print(f"  已下载: {db_stats.get('downloaded_count', 0)}")

    # 搜索一个关键词
    print(f"\n开始搜索...")
    results = dl.search_videos("people crying", limit=3)
    print(f"搜索结果: {len(results)} 个新视频")

    print("\n" + "="*60)
    print("测试2: 尝试重复下载已存在的视频")
    print("="*60)

    # 获取一个已下载的视频
    downloaded_videos = [v for v in dl.links_db["videos"] if v.get("downloaded", False)]

    if downloaded_videos:
        test_video = downloaded_videos[0]
        print(f"测试视频: {test_video['title'][:50]}")
        print(f"URL: {test_video['url']}")

        try:
            result = dl.download_from_url(test_video['url'])
            if result.get('skipped', False):
                print("✅ 成功跳过已下载的视频")
            else:
                print("⚠️ 视频被重新下载（应该被跳过）")
        except Exception as e:
            print(f"❌ 错误: {e}")
    else:
        print("⚠️ 数据库中没有已下载的视频，跳过此测试")

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    test_skip_existing()
