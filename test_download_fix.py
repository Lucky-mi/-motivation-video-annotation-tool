#!/usr/bin/env python3
"""
测试下载修复 - 验证格式问题是否已解决
"""
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

from backend.downloader import VideoDownloader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_download():
    """测试下载功能"""
    dl = VideoDownloader(
        output_dir="data/test_downloads",
        request_delay=(1, 2)
    )

    # 测试之前失败的视频
    test_urls = [
        "https://www.youtube.com/watch?v=WHMl50cUDME",  # How to cry in 1 minute
        "https://www.youtube.com/watch?v=CR1TvxyLS_M",  # Are You Okay?
    ]

    results = []
    for idx, url in enumerate(test_urls, 1):
        print(f"\n{'='*60}")
        print(f"测试 {idx}/{len(test_urls)}: {url}")
        print('='*60)

        try:
            result = dl.download_from_url(url)
            print(f"✅ 成功: {result['title']}")
            print(f"   路径: {result['video_path']}")
            results.append({"url": url, "status": "success", "result": result})
        except Exception as e:
            print(f"❌ 失败: {e}")
            results.append({"url": url, "status": "failed", "error": str(e)})

    # 汇总
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print('='*60)
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"成功: {success_count}/{len(results)}")
    print(f"失败: {len(results) - success_count}/{len(results)}")

    for r in results:
        status_icon = "✅" if r['status'] == 'success' else "❌"
        print(f"{status_icon} {r['url']}")
        if r['status'] == 'failed':
            print(f"   错误: {r['error']}")


if __name__ == "__main__":
    test_download()
