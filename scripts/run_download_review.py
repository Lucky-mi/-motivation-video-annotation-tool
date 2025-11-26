#!/usr/bin/env python3
# scripts/run_download_review.py
"""
从已保存的搜索结果中下载和审核视频
用于断点续传或分离搜索和下载流程
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import argparse
from backend.downloader import VideoDownloader
from backend.content_filter import ContentFilter

# 导入配置
sys.path.insert(0, str(project_root / "config"))
from search_config import (
    ENABLE_AI_REVIEW,
    STRICT_MODE,
    AUTO_DELETE_REJECTED,
    AI_REVIEW_WORKERS
)


def load_search_results(file_path: str) -> list:
    """加载搜索结果"""
    result_file = Path(file_path)
    if not result_file.exists():
        print(f"❌ 搜索结果文件不存在: {file_path}")
        return []

    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 兼容新旧格式
    if isinstance(data, list):
        # 旧格式：直接是视频列表
        videos = data
        print(f"📂 加载了 {len(videos)} 个搜索结果（旧格式）")
    elif isinstance(data, dict) and "videos" in data:
        # 新格式：包含元数据的字典
        videos = data["videos"]
        search_time = data.get("search_time", "未知")
        print(f"📂 加载了 {len(videos)} 个搜索结果")
        print(f"   搜索时间: {search_time}")
        if "statistics" in data:
            stats = data["statistics"]
            print(f"   原始搜索: {stats.get('total_searched', 0)} 个")
            print(f"   去重后: {stats.get('after_dedup', 0)} 个")
            print(f"   评分保留: {stats.get('after_scoring', 0)} 个")
    else:
        print(f"❌ 搜索结果格式错误")
        return []

    return videos


def filter_already_processed(videos: list, downloader: VideoDownloader) -> list:
    """过滤已经处理过的视频"""
    existing_urls = {v["url"] for v in downloader.links_db["videos"]}

    new_videos = [v for v in videos if v['url'] not in existing_urls]

    skipped = len(videos) - len(new_videos)
    if skipped > 0:
        print(f"⏭️ 跳过 {skipped} 个已处理的视频")

    return new_videos


def main():
    parser = argparse.ArgumentParser(description="从搜索结果下载和审核视频")
    parser.add_argument(
        "--input",
        default="data/search_results.json",
        help="搜索结果JSON文件路径"
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="开始处理的索引（支持断点续传）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="处理的视频数量限制（留空处理全部）"
    )
    parser.add_argument(
        "--skip-review",
        action="store_true",
        help="只下载不审核"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("📦 YouTube视频下载与审核工具")
    print("=" * 80)

    # 加载搜索结果
    all_videos = load_search_results(args.input)
    if not all_videos:
        return

    # 初始化组件
    print("\n📦 初始化组件...")
    downloader = VideoDownloader()
    content_filter = ContentFilter() if ENABLE_AI_REVIEW and not args.skip_review else None

    # 过滤已处理的视频
    videos_to_process = filter_already_processed(all_videos, downloader)

    if not videos_to_process:
        print("✅ 所有视频都已处理完成！")
        return

    # 应用start和limit
    start_idx = args.start
    end_idx = len(videos_to_process) if args.limit is None else min(start_idx + args.limit, len(videos_to_process))
    videos_to_process = videos_to_process[start_idx:end_idx]

    print(f"\n📊 处理范围: 第 {start_idx + 1} 到 {end_idx} 个 (共 {len(videos_to_process)} 个)")

    # 确认继续
    print(f"\n配置:")
    print(f"  - AI审核: {'启用' if content_filter else '禁用'}")
    print(f"  - 自动删除拒绝: {'是' if AUTO_DELETE_REJECTED else '否'}")
    print(f"  - 并发审核: {AI_REVIEW_WORKERS} 个")

    response = input("\n确认继续? (y/n): ")
    if response.lower() != 'y':
        print("❌ 已取消")
        return

    # 流水线处理
    print("\n" + "=" * 80)
    print(f"📍 开始下载与审核 (批次大小: {AI_REVIEW_WORKERS})")
    print("=" * 80)

    approved_count = 0
    rejected_count = 0
    failed_count = 0

    batch_size = AI_REVIEW_WORKERS
    total_batches = (len(videos_to_process) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        batch_start = batch_idx * batch_size
        batch_end = min(batch_start + batch_size, len(videos_to_process))
        batch = videos_to_process[batch_start:batch_end]

        absolute_start = start_idx + batch_start + 1
        absolute_end = start_idx + batch_end

        print(f"\n📦 批次 {batch_idx + 1}/{total_batches} (视频 {absolute_start}-{absolute_end})")

        # 1. 批量下载（增加延迟，避免套接字耗尽）
        downloaded = []
        for idx, video_info in enumerate(batch, start=absolute_start):
            print(f"  [{idx}/{start_idx + len(videos_to_process)}] 下载: {video_info['title'][:50]}...")
            try:
                download_result = downloader.download_from_url(video_info['url'])

                # 检查是否跳过
                if download_result.get('skipped', False):
                    print(f"    ⏭️ 已存在，跳过")
                    continue

                downloaded.append({
                    'info': video_info,
                    'path': download_result['video_path'],
                    'duration': download_result['duration']
                })
                print(f"    ✅ 成功")

                # 关键优化：下载成功后等待，让系统释放套接字资源
                import time
                time.sleep(2)  # 等待2秒，让连接完全关闭

            except Exception as e:
                failed_count += 1
                error_msg = str(e)

                # 如果是套接字错误，增加等待时间
                if "10055" in error_msg or "套接字" in error_msg or "缓冲区" in error_msg:
                    print(f"    ⚠️ 系统资源不足，等待释放...")
                    import time
                    time.sleep(10)  # 等待10秒让系统恢复
                # 如果是速率限制错误，提示用户
                elif "速率限制" in error_msg:
                    print(f"    ⚠️ 遇到速率限制，已自动减速")
                    print(f"    💡 提示: 可以用 --start {idx - 1} 从此处继续")
                else:
                    print(f"    ❌ 失败: {e}")

        if not downloaded:
            print(f"  ⚠️ 本批次无成功下载")
            continue

        # 2. 并行AI审核
        if content_filter:
            print(f"  🤖 并行审核 {len(downloaded)} 个视频...")
            video_paths = [v['path'] for v in downloaded]

            try:
                review_results = content_filter.batch_check(
                    video_paths,
                    strict_mode=STRICT_MODE,
                    max_workers=AI_REVIEW_WORKERS
                )

                # 3. 处理结果
                batch_approved = 0
                batch_rejected = 0

                for video_data in downloaded:
                    video_info = video_data['info']
                    video_path = video_data['path']
                    review_result = review_results.get(video_path, {"pass": False, "reason": "审核失败"})

                    approved = review_result.get('pass', False)

                    # 入库（关键修复：传入video_path）
                    downloader.add_video_link(
                        url=video_info['url'],
                        title=video_info['title'],
                        duration=video_data['duration'],
                        keyword=video_info.get('search_keyword', 'Unknown'),
                        approved=approved,
                        review_reason=review_result.get('reason', ''),
                        video_path=video_path  # 🔧 修复：记录视频文件路径
                    )

                    if approved:
                        approved_count += 1
                        batch_approved += 1
                    else:
                        rejected_count += 1
                        batch_rejected += 1
                        # 立即删除不通过的视频
                        if AUTO_DELETE_REJECTED:
                            Path(video_path).unlink(missing_ok=True)

                print(f"  📊 本批: ✅ {batch_approved} | ❌ {batch_rejected}")

            except Exception as e:
                print(f"  ❌ 审核出错: {e}")
                failed_count += len(downloaded)

        else:
            # 不审核，直接入库
            for video_data in downloaded:
                video_info = video_data['info']
                video_path = video_data['path']
                downloader.add_video_link(
                    url=video_info['url'],
                    title=video_info['title'],
                    duration=video_data['duration'],
                    keyword=video_info.get('search_keyword', 'Unknown'),
                    approved=None,
                    video_path=video_path  # 🔧 修复：记录视频文件路径
                )

    # 最终统计
    print(f"\n{'='*80}")
    print(f"✅ 处理完成")
    print(f"{'='*80}")

    if content_filter:
        total_reviewed = approved_count + rejected_count
        if total_reviewed > 0:
            print(f"通过: {approved_count} ({approved_count/total_reviewed*100:.1f}%)")
            print(f"拒绝: {rejected_count} ({rejected_count/total_reviewed*100:.1f}%)")
        print(f"失败: {failed_count}")
    else:
        print(f"下载: {len(videos_to_process) - failed_count}")
        print(f"失败: {failed_count}")

    print(f"\n📁 输出:")
    print(f"  - 链接数据库: data/youtube_links.json")
    print(f"  - 视频目录: data/Youtube_videos/")

    # 如果还有剩余视频，提示继续命令
    if end_idx < len(all_videos):
        remaining = len(all_videos) - end_idx
        print(f"\n💡 还有 {remaining} 个视频未处理")
        print(f"   继续命令: python scripts/run_download_review.py --start {end_idx}")

    print("\n" + "=" * 80)
    print("🎉 完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()
