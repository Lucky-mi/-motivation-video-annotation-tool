#!/usr/bin/env python3
# scripts/run_search.py
"""
简化的YouTube视频搜索和AI审核脚本
使用 config/search_config.py 中的配置
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from datetime import datetime
from backend.downloader import VideoDownloader
from backend.content_filter import ContentFilter
from backend.video_scorer import VideoScorer

# 导入配置
sys.path.insert(0, str(project_root / "config"))
from search_config import (
    get_keywords,
    get_estimated_video_count,
    VIDEOS_PER_KEYWORD,
    MIN_DURATION,
    MAX_DURATION,
    ENABLE_AI_REVIEW,
    STRICT_MODE,
    AUTO_DELETE_REJECTED,
    print_config
)


def main():
    """主流程"""

    # 显示配置
    print_config()

    # 确认继续
    print("\n⚠️ 提示: 搜索和下载需要一定时间，AI审核会消耗API配额")
    response = input("确认继续? (y/n): ")
    if response.lower() != 'y':
        print("❌ 已取消")
        return

    # 初始化
    print("\n📦 初始化组件...")
    downloader = VideoDownloader()
    content_filter = ContentFilter() if ENABLE_AI_REVIEW else None
    scorer = VideoScorer()  # 初始化评分系统

    # 显示学习到的模式
    if scorer.channel_stats:
        print("  ✅ 评分系统已加载历史数据")
        scorer.print_statistics()
    else:
        print("  ⚠️ 评分系统无历史数据，将使用默认规则")

    # 获取关键词
    keywords = get_keywords()

    # 阶段1: 批量搜索
    print("\n" + "=" * 80)
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

    # 保存搜索结果
    search_result_file = Path("data/search_results.json")
    with open(search_result_file, 'w', encoding='utf-8') as f:
        json.dump(scored_videos, f, ensure_ascii=False, indent=2)
    print(f"💾 搜索结果已保存: {search_result_file}")

    # 更新要处理的视频列表
    unique_videos = scored_videos

    # 阶段2: 下载和AI审核
    print("\n" + "=" * 80)
    print(f"📍 阶段 2/3: 下载视频{'并AI审核' if ENABLE_AI_REVIEW else ''}")
    print("=" * 80)

    approved_count = 0
    rejected_count = 0
    failed_count = 0

    for idx, video_info in enumerate(unique_videos, 1):
        print(f"\n[{idx}/{len(unique_videos)}]")
        print(f"  标题: {video_info['title'][:70]}...")
        print(f"  时长: {video_info['duration']}秒 | 关键词: {video_info['search_keyword']}")

        try:
            # 下载
            download_result = downloader.download_from_url(video_info['url'])
            video_path = download_result['video_path']

            # AI审核
            if ENABLE_AI_REVIEW and content_filter:
                review_result = content_filter.check_video_content(
                    video_path,
                    strict_mode=STRICT_MODE
                )

                approved = review_result.get('pass', False)

                # 添加到数据库
                downloader.add_video_link(
                    url=video_info['url'],
                    title=video_info['title'],
                    duration=video_info['duration'],
                    keyword=video_info['search_keyword'],
                    approved=approved,
                    review_reason=review_result.get('reason', '')
                )

                if approved:
                    approved_count += 1
                    print(f"  ✅ 通过 | {review_result.get('reason', '')}")
                    print(f"     置信度: {review_result.get('confidence', 0):.2f} | 价值: {review_result.get('分析价值', '')}")
                else:
                    rejected_count += 1
                    print(f"  ❌ 拒绝 | {review_result.get('reason', '')}")

                    if AUTO_DELETE_REJECTED:
                        Path(video_path).unlink()
                        print("  🗑️ 已删除")
            else:
                downloader.add_video_link(
                    url=video_info['url'],
                    title=video_info['title'],
                    duration=video_info['duration'],
                    keyword=video_info['search_keyword'],
                    approved=None
                )
                print("  ✅ 已下载（未审核）")

        except Exception as e:
            failed_count += 1
            print(f"  ❌ 失败: {e}")

    # 阶段3: 统计
    print("\n" + "=" * 80)
    print("📊 最终统计")
    print("=" * 80)
    print(f"搜索: {len(unique_videos)} 个视频")

    if ENABLE_AI_REVIEW:
        total_reviewed = approved_count + rejected_count
        if total_reviewed > 0:
            print(f"通过: {approved_count} ({approved_count/total_reviewed*100:.1f}%)")
            print(f"拒绝: {rejected_count} ({rejected_count/total_reviewed*100:.1f}%)")
        print(f"失败: {failed_count}")
    else:
        print(f"下载: {len(unique_videos) - failed_count}")
        print(f"失败: {failed_count}")

    print(f"\n📁 输出:")
    print(f"  - 搜索结果: data/search_results.json")
    print(f"  - 链接数据库: data/youtube_links.json")
    print(f"  - 视频目录: data/Youtube_videos/")

    print("\n" + "=" * 80)
    print("🎉 完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()
