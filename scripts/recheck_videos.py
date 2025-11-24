#!/usr/bin/env python3
# scripts/recheck_videos.py
"""
重新审核已下载但未审核的视频
适用于网络中断或审核失败的情况
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from backend.content_filter import ContentFilter
from backend.downloader import VideoDownloader

# 导入配置
sys.path.insert(0, str(project_root / "config"))
from search_config import STRICT_MODE, AUTO_DELETE_REJECTED, AI_REVIEW_WORKERS


def find_unreviewed_videos(youtube_links_path="data/youtube_links.json",
                           video_dir="data/Youtube_videos"):
    """
    查找已下载但未审核的视频

    Returns:
        需要审核的视频列表 [(video_info, video_path), ...]
    """
    links_file = Path(youtube_links_path)
    if not links_file.exists():
        print("❌ 找不到 youtube_links.json 文件")
        return []

    with open(links_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    videos = data.get('videos', [])
    video_dir = Path(video_dir)

    # 查找未审核的视频
    unreviewed = []

    for video in videos:
        # 检查是否未审核（reviewed 为 False 或不存在）
        if video.get('reviewed', False):
            continue  # 已审核，跳过

        # 检查视频文件是否存在
        video_id = video.get('video_id')
        if not video_id:
            continue

        # 可能的文件扩展名
        for ext in ['.mp4', '.mkv', '.webm', '.avi']:
            video_path = video_dir / f"{video_id}{ext}"
            if video_path.exists():
                unreviewed.append((video, str(video_path)))
                break

    return unreviewed


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="重新审核已下载但未审核的视频")
    parser.add_argument(
        "--links-file",
        default="data/youtube_links.json",
        help="youtube_links.json 文件路径"
    )
    parser.add_argument(
        "--video-dir",
        default="data/Youtube_videos",
        help="视频目录路径"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=AI_REVIEW_WORKERS,
        help=f"批次大小（默认: {AI_REVIEW_WORKERS}）"
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="只列出未审核的视频，不进行审核"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("🔍 查找未审核的视频")
    print("=" * 80)

    unreviewed = find_unreviewed_videos(args.links_file, args.video_dir)

    if not unreviewed:
        print("\n✅ 所有已下载的视频都已审核！")
        return

    print(f"\n📊 找到 {len(unreviewed)} 个未审核的视频")

    if args.list_only:
        print("\n未审核视频列表:")
        for idx, (video_info, video_path) in enumerate(unreviewed, 1):
            print(f"  {idx}. {video_info['title'][:60]}...")
            print(f"     路径: {video_path}")
        return

    # 确认继续
    print(f"\n⚠️ 将对这 {len(unreviewed)} 个视频进行AI审核")
    print(f"   - 批次大小: {args.batch_size}")
    print(f"   - 严格模式: {'是' if STRICT_MODE else '否'}")
    print(f"   - 自动删除未通过: {'是' if AUTO_DELETE_REJECTED else '否'}")

    response = input("\n确认继续? (y/n): ")
    if response.lower() != 'y':
        print("❌ 已取消")
        return

    # 初始化
    print("\n📦 初始化AI审核器...")
    content_filter = ContentFilter()
    downloader = VideoDownloader()

    # 分批处理
    print("\n" + "=" * 80)
    print(f"🚀 开始审核 (批次大小: {args.batch_size})")
    print("=" * 80)

    approved_count = 0
    rejected_count = 0
    failed_count = 0

    batch_size = args.batch_size
    total_batches = (len(unreviewed) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(unreviewed))
        batch = unreviewed[start_idx:end_idx]

        print(f"\n📦 批次 {batch_idx + 1}/{total_batches} (视频 {start_idx + 1}-{end_idx})")

        # 提取路径
        video_paths = [video_path for _, video_path in batch]

        # 并行审核
        print(f"  🤖 并行审核 {len(batch)} 个视频...")

        try:
            review_results = content_filter.batch_check(
                video_paths,
                strict_mode=STRICT_MODE,
                max_workers=batch_size
            )

            # 处理结果
            batch_approved = 0
            batch_rejected = 0

            for video_info, video_path in batch:
                review_result = review_results.get(video_path, {"pass": False, "reason": "审核失败"})
                approved = review_result.get('pass', False)

                # 更新数据库
                video_info['reviewed'] = True
                video_info['approved'] = approved
                video_info['review_reason'] = review_result.get('reason', '')

                # 保存（通过 downloader 的方法更新）
                downloader.add_video_link(
                    url=video_info['url'],
                    title=video_info['title'],
                    duration=video_info['duration'],
                    keyword=video_info.get('keyword', 'Recheck'),
                    approved=approved,
                    review_reason=review_result.get('reason', '')
                )

                if approved:
                    approved_count += 1
                    batch_approved += 1
                else:
                    rejected_count += 1
                    batch_rejected += 1

                    # 删除未通过的视频
                    if AUTO_DELETE_REJECTED:
                        Path(video_path).unlink(missing_ok=True)

            print(f"  📊 本批: ✅ {batch_approved} | ❌ {batch_rejected}")

        except Exception as e:
            print(f"  ❌ 批次审核失败: {e}")
            failed_count += len(batch)

    # 最终统计
    print("\n" + "=" * 80)
    print("📊 审核完成统计")
    print("=" * 80)
    print(f"总计: {len(unreviewed)} 个视频")
    print(f"✅ 通过: {approved_count}")
    print(f"❌ 拒绝: {rejected_count}")
    if failed_count > 0:
        print(f"⚠️ 失败: {failed_count}")

    if approved_count + rejected_count > 0:
        pass_rate = approved_count / (approved_count + rejected_count) * 100
        print(f"\n通过率: {pass_rate:.1f}%")

    print("\n✅ 完成！")


if __name__ == "__main__":
    main()
