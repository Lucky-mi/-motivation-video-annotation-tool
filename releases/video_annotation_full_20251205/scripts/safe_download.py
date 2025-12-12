#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全下载脚本 - 带速率限制和错误恢复
====================================
"""
import sys
import os
from pathlib import Path
import time

# 修复 Windows 编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.downloader import VideoDownloader
from config.search_config import get_keywords, VIDEOS_PER_KEYWORD

def safe_search_and_download(
    keyword_limit: int = 5,
    videos_per_keyword: int = 3,
    delay_between_keywords: int = 5,
    proxy: str = None
):
    """
    安全搜索和下载

    Args:
        keyword_limit: 最多使用多少个关键词
        videos_per_keyword: 每个关键词搜索多少个视频
        delay_between_keywords: 关键词之间的延迟（秒）
        proxy: 代理地址，如 'http://127.0.0.1:7890'
    """
    print("="*60)
    print("🛡️ 安全下载模式")
    print("="*60)
    print(f"关键词数量: {keyword_limit}")
    print(f"每关键词视频数: {videos_per_keyword}")
    print(f"关键词间延迟: {delay_between_keywords}秒")
    if proxy:
        print(f"使用代理: {proxy}")
    print("="*60)

    # 初始化下载器
    dl = VideoDownloader(proxy=proxy)

    # 获取关键词
    all_keywords = get_keywords()
    keywords = all_keywords[:keyword_limit]

    print(f"\n📋 将使用以下关键词:")
    for i, kw in enumerate(keywords, 1):
        print(f"   {i}. {kw}")

    # 统计
    total_found = 0
    total_downloaded = 0
    failed_count = 0

    # 逐个关键词搜索
    for idx, keyword in enumerate(keywords, 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{len(keywords)}] 正在搜索: {keyword}")
        print(f"{'='*60}")

        try:
            # 搜索视频
            videos = dl.search_videos(
                keyword=keyword,
                limit=videos_per_keyword,
                skip_searched=True
            )

            if not videos:
                print(f"⚠️ 未找到新视频，跳过")
                continue

            total_found += len(videos)
            print(f"✅ 找到 {len(videos)} 个新视频")

            # 尝试下载
            for video in videos:
                try:
                    print(f"\n⬇️ 下载: {video['title'][:50]}...")
                    result = dl.download_from_url(video['url'])

                    if result and not result.get('skipped'):
                        total_downloaded += 1
                        print(f"✅ 成功下载")

                    # 下载间隔
                    time.sleep(2)

                except Exception as e:
                    failed_count += 1
                    error_msg = str(e)

                    if "Sign in to confirm" in error_msg or "not a bot" in error_msg:
                        print(f"❌ 人机验证失败！")
                        print(f"💡 建议:")
                        print(f"   1. 更新 cookies.txt")
                        print(f"   2. 等待 30 分钟后重试")
                        print(f"   3. 使用代理/VPN")
                        return

                    elif "速率限制" in error_msg or "rate-limited" in error_msg.lower():
                        print(f"❌ 触发速率限制，休息 30 秒...")
                        time.sleep(30)

                    else:
                        print(f"❌ 下载失败: {error_msg[:100]}")

            # 关键词之间延迟
            if idx < len(keywords):
                print(f"\n⏳ 休息 {delay_between_keywords} 秒...")
                time.sleep(delay_between_keywords)

        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断")
            break

        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            failed_count += 1

    # 总结
    print("\n" + "="*60)
    print("📊 下载总结")
    print("="*60)
    print(f"关键词搜索: {idx}/{len(keywords)}")
    print(f"视频找到: {total_found}")
    print(f"成功下载: {total_downloaded}")
    print(f"失败数量: {failed_count}")
    print("="*60)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="安全下载脚本")
    parser.add_argument('--keywords', type=int, default=5, help='使用多少个关键词')
    parser.add_argument('--per-keyword', type=int, default=3, help='每关键词搜索视频数')
    parser.add_argument('--delay', type=int, default=5, help='关键词间延迟（秒）')
    parser.add_argument('--proxy', type=str, help='代理地址 (如 http://127.0.0.1:7890)')

    args = parser.parse_args()

    safe_search_and_download(
        keyword_limit=args.keywords,
        videos_per_keyword=args.per_keyword,
        delay_between_keywords=args.delay,
        proxy=args.proxy
    )

if __name__ == "__main__":
    main()
