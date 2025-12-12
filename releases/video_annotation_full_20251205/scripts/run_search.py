#!/usr/bin/env python3
# scripts/run_search.py
"""
YouTube视频搜索和AI审核脚本
支持两种模式:
1. 仅搜索模式 (--search-only): 只搜索并保存结果，不下载
2. 完整流程模式 (默认): 搜索 + 下载 + AI审核

使用 config/search_config.py 中的配置
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import argparse
import logging
from datetime import datetime
from backend.downloader import VideoDownloader
from backend.content_filter import ContentFilter
from backend.video_scorer import VideoScorer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入配置
sys.path.insert(0, str(project_root / "config"))
from search_config import (
    get_keywords,
    get_estimated_video_count,
    VIDEOS_PER_KEYWORD,
    MIN_DURATION,
    MAX_DURATION,
    MAX_SEARCH_ATTEMPTS,
    SEARCH_MULTIPLIER_INITIAL,
    SEARCH_MULTIPLIER_INCREMENT,
    ENABLE_AI_REVIEW,
    STRICT_MODE,
    AUTO_DELETE_REJECTED,
    AI_REVIEW_WORKERS,
    print_config
)


def main():
    """主流程"""
    parser = argparse.ArgumentParser(
        description="YouTube视频搜索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 仅搜索（推荐用于大批量，避免速率限制丢失结果）
  python scripts/run_search.py --search-only

  # 完整流程（搜索 + 下载 + AI审核）
  python scripts/run_search.py

配合使用:
  1. 先搜索: python scripts/run_search.py --search-only
  2. 后下载: python scripts/run_download_review.py
        """
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="只搜索不下载（结果保存到data/search_results.json）"
    )
    args = parser.parse_args()

    # 显示配置
    print("=" * 80)
    print("🎬 YouTube视频搜索与审核系统")
    print("=" * 80)

    print_config()

    # 显示模式
    print("\n" + "=" * 80)
    if args.search_only:
        print("💡 运行模式: 仅搜索")
        print("=" * 80)
        print("  ✓ 搜索视频")
        print("  ✓ 智能评分预筛选")
        print("  ✓ 保存结果到 data/search_results.json")
        print("  ✗ 不下载视频")
        print("  ✗ 不进行AI审核")
        print("\n  💡 后续步骤:")
        print("     python scripts/run_download_review.py")
    else:
        print("💡 运行模式: 完整流程")
        print("=" * 80)
        print("  ✓ 搜索视频")
        print("  ✓ 智能评分预筛选")
        print("  ✓ 保存搜索结果")
        print("  ✓ 下载视频")
        print(f"  ✓ AI审核 ({'启用' if ENABLE_AI_REVIEW else '禁用'})")
        print(f"  ✓ 自动删除拒绝视频 ({'是' if AUTO_DELETE_REJECTED else '否'})")
    print("=" * 80)

    # 确认继续
    print("\n⚠️  注意事项:")
    print("  • 搜索可能遇到YouTube速率限制（系统会自动处理）")
    if not args.search_only:
        print("  • 下载和AI审核会消耗时间和API配额")
        print("  • 建议先用 --search-only 测试")

    response = input("\n确认继续? (y/n): ")
    if response.lower() != 'y':
        print("❌ 已取消")
        return

    search_only = args.search_only

    # 初始化组件
    print("\n📦 初始化组件...")
    downloader = VideoDownloader()

    # 只在完整流程模式下初始化AI审核组件
    content_filter = None
    if not search_only and ENABLE_AI_REVIEW:
        content_filter = ContentFilter()
        print("  ✅ AI审核组件已加载")

    scorer = VideoScorer()  # 初始化评分系统

    # 显示学习到的模式
    if scorer.channel_stats:
        print("  ✅ 评分系统已加载历史数据")
        if not search_only:
            scorer.print_statistics()
    else:
        print("  ⚠️ 评分系统无历史数据，将使用默认规则")

    # 获取关键词
    keywords = get_keywords()

    # 阶段1: 批量搜索
    print("\n" + "=" * 80)
    if search_only:
        print("📍 阶段 1/2: 批量搜索视频")
    else:
        print("📍 阶段 1/3: 批量搜索视频")
    print("=" * 80)

    all_videos = []
    for idx, keyword in enumerate(keywords, 1):
        print(f"\n[{idx}/{len(keywords)}] 搜索关键词: {keyword}")
        try:
            videos = downloader.search_videos(
                keyword,
                limit=VIDEOS_PER_KEYWORD,
                min_duration=MIN_DURATION,
                max_duration=MAX_DURATION
            )
            for video in videos:
                video['search_keyword'] = keyword
            all_videos.extend(videos)
            print(f"  ✅ 找到 {len(videos)} 个视频")
        except Exception as e:
            print(f"  ❌ 搜索失败: {e}")
            continue

    # 去重
    seen_urls = set()
    unique_videos = []
    for video in all_videos:
        if video['url'] not in seen_urls:
            seen_urls.add(video['url'])
            unique_videos.append(video)

    print(f"\n✅ 搜索完成: 总共 {len(all_videos)} 个，去重后 {len(unique_videos)} 个")

    if not unique_videos:
        print("❌ 未搜索到任何视频")
        return

    # 阶段1.5: 智能评分和预筛选
    print("\n" + "=" * 80)
    if search_only:
        print("📍 阶段 2/2: 智能评分预筛选")
    else:
        print("📍 阶段 1.5/3: 智能评分预筛选")
    print("=" * 80)

    scored_videos = []
    skip_count = 0

    for video in unique_videos:
        score_result = scorer.score_video(video)
        video['pre_score'] = score_result['score']
        video['pre_recommendation'] = score_result['recommendation']
        video['score_reasons'] = score_result['reasons']

        if score_result['recommendation'] == 'skip':
            skip_count += 1
            print(f"⏭️ 跳过低分视频 (分数: {score_result['score']:.2f}): {video['title'][:60]}...")
        else:
            scored_videos.append(video)
            priority_mark = "⭐" if score_result['recommendation'] == 'priority' else "  "
            print(f"{priority_mark} 保留 (分数: {score_result['score']:.2f}): {video['title'][:60]}...")

    print(f"\n📊 预筛选结果:")
    print(f"  - 保留: {len(scored_videos)} 个")
    print(f"  - 跳过: {skip_count} 个")
    print(f"  - 节省AI成本: {skip_count * 100 / len(unique_videos):.1f}%")

    # 按分数排序（优先处理高分视频）
    scored_videos.sort(key=lambda x: x['pre_score'], reverse=True)

    # 保存搜索结果（只保存本轮新搜索的结果，不追加历史）
    # 注意：搜索历史已经由 downloader 自动记录到 searched_history.json
    search_result_file = Path("data/search_results.json")

    # 添加时间戳到搜索结果
    search_results_data = {
        "search_time": datetime.now().isoformat(),
        "total_videos": len(scored_videos),
        "videos": scored_videos,
        "statistics": {
            "total_searched": len(all_videos),
            "after_dedup": len(unique_videos),
            "after_scoring": len(scored_videos),
            "skipped_by_score": skip_count
        }
    }

    with open(search_result_file, 'w', encoding='utf-8') as f:
        json.dump(search_results_data, f, ensure_ascii=False, indent=2)
    print(f"💾 搜索结果已保存: {search_result_file}")

    # 另外保存一份带时间戳的归档（可选，方便追溯）
    archive_file = Path(f"data/search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(archive_file, 'w', encoding='utf-8') as f:
        json.dump(search_results_data, f, ensure_ascii=False, indent=2)
    print(f"📦 归档副本已保存: {archive_file}")

    # 如果只搜索，到此结束
    if search_only:
        print("\n" + "=" * 80)
        print("✅ 搜索完成！")
        print("=" * 80)
        print(f"\n📊 统计信息:")
        print(f"  • 搜索到视频: {len(all_videos)} 个")
        print(f"  • 去重后: {len(unique_videos)} 个")
        print(f"  • 预筛选保留: {len(scored_videos)} 个")
        print(f"  • 预筛选跳过: {skip_count} 个")
        print(f"  • 节省AI成本: {skip_count * 100 / len(unique_videos):.1f}%")

        print(f"\n💾 输出文件:")
        print(f"  • 搜索结果: {search_result_file}")
        print(f"    (已按评分排序，高分视频优先)")

        print(f"\n💡 下一步操作:")
        print(f"  1. 查看搜索结果:")
        print(f"     cat {search_result_file}")
        print(f"\n  2. 下载和审核所有视频:")
        print(f"     python scripts/run_download_review.py")
        print(f"\n  3. 下载前N个高分视频:")
        print(f"     python scripts/run_download_review.py --limit 20")
        print(f"\n  4. 只下载不审核:")
        print(f"     python scripts/run_download_review.py --skip-review")

        print("\n" + "=" * 80)
        print("🎉 完成!")
        print("=" * 80)
        return

    # 更新要处理的视频列表
    unique_videos = scored_videos

    # 阶段2-3: 流水线处理（下载 → 审核 → 删除，批次处理）
    print("\n" + "=" * 80)
    print(f"📍 阶段 2/3: 流水线处理 (批次大小: {AI_REVIEW_WORKERS})")
    print(f"💡 边下载边审核，立即释放不通过视频的磁盘空间")
    print("=" * 80)

    approved_count = 0
    rejected_count = 0
    failed_count = 0

    # 分批处理，每批 = AI_REVIEW_WORKERS 个视频
    batch_size = AI_REVIEW_WORKERS
    total_batches = (len(unique_videos) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(unique_videos))
        batch = unique_videos[start_idx:end_idx]

        print(f"\n📦 批次 {batch_idx + 1}/{total_batches} (视频 {start_idx + 1}-{end_idx})")

        # 1. 批量下载
        downloaded = []
        for idx, video_info in enumerate(batch, start=start_idx + 1):
            print(f"  [{idx}/{len(unique_videos)}] 下载: {video_info['title'][:50]}...")
            try:
                download_result = downloader.download_from_url(video_info['url'])

                # 检查是否跳过（已存在）
                if download_result.get('skipped', False):
                    print(f"    ⏭️ 已存在，跳过")
                    continue

                downloaded.append({
                    'info': video_info,
                    'path': download_result['video_path'],
                    'duration': download_result['duration']
                })
                print(f"    ✅ 成功")
            except Exception as e:
                failed_count += 1
                error_msg = str(e)

                # 如果是速率限制，提示用户可以使用断点续传脚本
                if "速率限制" in error_msg:
                    print(f"    ⚠️ 遇到速率限制")
                    print(f"\n💡 提示: 已搜索的结果保存在 {search_result_file}")
                    print(f"   可以等待后使用以下命令继续:")
                    print(f"   python scripts/run_download_review.py --start {idx - 1}")
                else:
                    print(f"    ❌ 失败: {e}")

        if not downloaded:
            print(f"  ⚠️ 本批次无成功下载")
            continue

        # 2. 并行AI审核
        if ENABLE_AI_REVIEW and content_filter:
            print(f"  🤖 并行审核 {len(downloaded)} 个视频...")
            video_paths = [v['path'] for v in downloaded]

            review_results = content_filter.batch_check(
                video_paths,
                strict_mode=STRICT_MODE,
                max_workers=AI_REVIEW_WORKERS
            )

            # 3. 处理结果并立即删除拒绝的视频
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
                    keyword=video_info['search_keyword'],
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
                    # 立即删除不通过的视频，释放空间
                    if AUTO_DELETE_REJECTED:
                        Path(video_path).unlink(missing_ok=True)
                        logger.info(f"🗑️  已删除不通过视频: {Path(video_path).name}")

            print(f"  📊 本批: ✅ {batch_approved} | ❌ {batch_rejected}")

        else:
            # 不审核，直接入库
            for video_data in downloaded:
                video_info = video_data['info']
                video_path = video_data['path']
                downloader.add_video_link(
                    url=video_info['url'],
                    title=video_info['title'],
                    duration=video_data['duration'],
                    keyword=video_info['search_keyword'],
                    approved=None,
                    video_path=video_path  # 🔧 修复：记录视频文件路径
                )

    print(f"\n{'='*80}")
    print(f"✅ 流水线处理完成")
    print(f"{'='*80}")

    # 阶段3: 统计
    print("\n" + "=" * 80)
    print("📊 最终统计")
    print("=" * 80)

    print(f"\n搜索阶段:")
    print(f"  • 搜索到: {len(all_videos)} 个视频")
    print(f"  • 去重后: {len(unique_videos)} 个")
    print(f"  • 预筛选保留: {len(scored_videos)} 个")
    print(f"  • 预筛选跳过: {skip_count} 个")

    print(f"\n下载与审核:")
    total_processed = approved_count + rejected_count + failed_count

    if ENABLE_AI_REVIEW and content_filter:
        total_reviewed = approved_count + rejected_count
        if total_reviewed > 0:
            print(f"  • 审核通过: {approved_count} ({approved_count/total_reviewed*100:.1f}%)")
            print(f"  • 审核拒绝: {rejected_count} ({rejected_count/total_reviewed*100:.1f}%)")
        print(f"  • 下载失败: {failed_count}")

        if approved_count > 0:
            print(f"\n✅ 成功获得 {approved_count} 个高质量视频！")
    else:
        downloaded_count = total_processed - failed_count
        print(f"  • 下载成功: {downloaded_count}")
        print(f"  • 下载失败: {failed_count}")

    print(f"\n📁 输出文件:")
    print(f"  • 搜索结果: data/search_results.json")
    print(f"  • 链接数据库: data/youtube_links.json")
    print(f"  • 视频目录: data/Youtube_videos/")

    if failed_count > 0:
        print(f"\n💡 提示: 有 {failed_count} 个视频下载失败")
        print(f"   可使用以下命令重试:")
        print(f"   python scripts/run_download_review.py")

    print("\n" + "=" * 80)
    print("🎉 完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()
