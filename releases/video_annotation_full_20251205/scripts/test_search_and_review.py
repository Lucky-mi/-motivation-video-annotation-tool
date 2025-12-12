#!/usr/bin/env python3
# scripts/test_search_and_review.py
"""
测试搜索和AI审核功能
可以自定义搜索数量和关键词
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from backend.downloader import VideoDownloader
from backend.content_filter import ContentFilter


def main():
    """主测试流程"""

    # === 配置参数 ===
    # 搜索配置
    SEARCH_KEYWORDS = [
        "social interaction psychology",
        "people understanding emotions",
        "human interaction",
        "emotional intelligence social",
        "psychology short film",
        "theory of mind"
    ]

    VIDEOS_PER_KEYWORD = 5  # 每个关键词搜索5个视频（可以改成10、20等）

    # 是否启用AI审核（如果没有配置Gemini API，设为False）
    ENABLE_AI_REVIEW = True
    STRICT_MODE = True  # 严格审核模式

    # 是否自动删除未通过的视频
    AUTO_DELETE_REJECTED = True

    print("=" * 80)
    print("🎬 YouTube视频搜索与AI审核测试")
    print("=" * 80)
    print(f"📋 配置:")
    print(f"  - 关键词数量: {len(SEARCH_KEYWORDS)}")
    print(f"  - 每个关键词搜索: {VIDEOS_PER_KEYWORD} 个视频")
    print(f"  - 预计搜索总数: {len(SEARCH_KEYWORDS) * VIDEOS_PER_KEYWORD} 个")
    print(f"  - AI审核: {'启用' if ENABLE_AI_REVIEW else '禁用'}")
    print(f"  - 审核模式: {'严格' if STRICT_MODE else '标准'}")
    print("=" * 80)

    # 初始化
    downloader = VideoDownloader()
    content_filter = ContentFilter() if ENABLE_AI_REVIEW else None

    # 阶段1: 批量搜索
    print("\n📍 阶段 1/3: 批量搜索视频")
    print("-" * 80)

    all_videos = downloader.batch_search(
        keywords=SEARCH_KEYWORDS,
        videos_per_keyword=VIDEOS_PER_KEYWORD
    )

    if not all_videos:
        print("❌ 未搜索到任何视频")
        return

    print(f"✅ 搜索完成: 找到 {len(all_videos)} 个候选视频")

    # 保存搜索结果
    search_result_file = Path("data/search_results.json")
    with open(search_result_file, 'w', encoding='utf-8') as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=2)
    print(f"💾 搜索结果已保存到: {search_result_file}")

    # 阶段2: 下载视频（用于AI审核）
    print(f"\n📍 阶段 2/3: 下载视频并{'AI审核' if ENABLE_AI_REVIEW else '保存'}")
    print("-" * 80)

    approved_count = 0
    rejected_count = 0
    failed_count = 0

    for idx, video_info in enumerate(all_videos, 1):
        print(f"\n[{idx}/{len(all_videos)}] 处理视频:")
        print(f"  标题: {video_info['title'][:60]}...")
        print(f"  时长: {video_info['duration']}秒")
        print(f"  关键词: {video_info['search_keyword']}")

        try:
            # 下载视频
            print("  ⬇️ 下载中...")
            download_result = downloader.download_from_url(video_info['url'])
            video_path = download_result['video_path']
            print(f"  ✅ 下载完成: {Path(video_path).name}")

            # AI审核
            if ENABLE_AI_REVIEW and content_filter:
                print("  🤖 AI审核中...")
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
                    print(f"  ✅ 审核通过!")
                    print(f"     理由: {review_result.get('reason', '')}")
                    print(f"     类别: {review_result.get('category', '')}")
                    print(f"     置信度: {review_result.get('confidence', 0):.2f}")
                    print(f"     分析价值: {review_result.get('分析价值', '')}")
                else:
                    rejected_count += 1
                    print(f"  ❌ 审核未通过")
                    print(f"     理由: {review_result.get('reason', '')}")

                    # 删除未通过的视频
                    if AUTO_DELETE_REJECTED:
                        try:
                            Path(video_path).unlink()
                            print("  🗑️ 已删除视频文件")
                        except Exception as e:
                            print(f"  ⚠️ 删除失败: {e}")
            else:
                # 不审核，直接标记为待审核
                downloader.add_video_link(
                    url=video_info['url'],
                    title=video_info['title'],
                    duration=video_info['duration'],
                    keyword=video_info['search_keyword'],
                    approved=None,
                    review_reason="未启用AI审核"
                )
                print("  ⏭️ 跳过AI审核")

        except Exception as e:
            failed_count += 1
            print(f"  ❌ 处理失败: {e}")
            continue

    # 阶段3: 统计报告
    print("\n" + "=" * 80)
    print("📊 最终统计报告")
    print("=" * 80)
    print(f"搜索结果: {len(all_videos)} 个视频")

    if ENABLE_AI_REVIEW:
        print(f"审核通过: {approved_count} 个 ({approved_count/len(all_videos)*100:.1f}%)")
        print(f"审核拒绝: {rejected_count} 个 ({rejected_count/len(all_videos)*100:.1f}%)")
        print(f"处理失败: {failed_count} 个")
        print(f"\n通过率: {approved_count/(approved_count+rejected_count)*100:.1f}%")
    else:
        print(f"已下载: {len(all_videos) - failed_count} 个")
        print(f"失败: {failed_count} 个")

    print("\n📁 输出文件:")
    print(f"  - 搜索结果: data/search_results.json")
    print(f"  - 链接数据库: data/youtube_links.json")
    print(f"  - 下载视频: data/Youtube_videos/")

    if ENABLE_AI_REVIEW:
        print(f"\n💡 提示:")
        print(f"  - 查看详细数据库: cat data/youtube_links.json")
        print(f"  - 仅查看通过的视频: python -c \"from backend.downloader import VideoDownloader; dl = VideoDownloader(); print(dl.get_approved_videos())\"")

    print("=" * 80)
    print("🎉 测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()
