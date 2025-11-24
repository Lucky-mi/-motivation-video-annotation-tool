#!/usr/bin/env python3
# scripts/show_scorer_stats.py
"""
显示视频评分系统学到的模式
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from backend.video_scorer import VideoScorer

def main():
    """显示评分系统统计"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(message)s'
    )

    # 初始化评分器
    scorer = VideoScorer(youtube_links_path="data/youtube_links.json")

    # 显示统计
    scorer.print_statistics()

    # 显示白名单/黑名单
    whitelist = scorer.get_channel_whitelist(min_approval_rate=0.7, min_samples=2)
    blacklist = scorer.get_channel_blacklist(max_approval_rate=0.3, min_samples=2)

    if whitelist:
        print(f"\n✅ 频道白名单 (通过率≥70%, 样本≥2):")
        for channel in whitelist:
            stats = scorer.channel_stats[channel]
            print(f"  - {channel}: {stats['approval_rate']:.1%} ({stats['approved']}/{stats['total_reviews']})")

    if blacklist:
        print(f"\n❌ 频道黑名单 (通过率≤30%, 样本≥2):")
        for channel in blacklist:
            stats = scorer.channel_stats[channel]
            print(f"  - {channel}: {stats['approval_rate']:.1%} ({stats['approved']}/{stats['total_reviews']})")

    # 测试评分示例
    print(f"\n" + "=" * 80)
    print("🧪 评分示例")
    print("=" * 80)

    test_videos = [
        {
            'channel': '未知频道',
            'duration': 120,
            'title': 'people arguing emotional moment',
            'view_count': 50000
        },
        {
            'channel': '未知频道',
            'duration': 600,
            'title': 'tutorial how to video',
            'view_count': 1000
        }
    ]

    for i, video in enumerate(test_videos, 1):
        result = scorer.score_video(video)
        print(f"\n视频 {i}:")
        print(f"  标题: {video['title']}")
        print(f"  分数: {result['score']:.3f} ({result['recommendation']})")
        print(f"  置信度: {result['confidence']}")
        print(f"  原因:")
        for reason in result['reasons']:
            print(f"    - {reason}")


if __name__ == "__main__":
    main()
