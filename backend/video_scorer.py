# backend/video_scorer.py
"""
视频评分系统 - 基于历史数据预测视频质量
不需要训练，直接从youtube_links.json学习模式
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


class VideoScorer:
    """基于历史数据的视频评分器"""

    def __init__(self, youtube_links_path: str = "data/youtube_links.json"):
        self.links_path = Path(youtube_links_path)
        self.channel_stats = {}
        self.keyword_stats = {"good": set(), "bad": set()}
        self.duration_stats = {"good": [], "bad": []}

        if self.links_path.exists():
            self._analyze_historical_data()

    def _analyze_historical_data(self):
        """分析历史数据，学习模式"""
        try:
            with open(self.links_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            videos = data.get('videos', [])

            # 统计频道表现
            channel_approvals = defaultdict(lambda: {"approved": 0, "rejected": 0})

            for video in videos:
                if 'reviewed' not in video:
                    continue

                channel = video.get('channel', 'Unknown')
                approved = video.get('approved', False)
                duration = video.get('duration', 0)
                title = video.get('title', '').lower()

                # 频道统计
                if approved:
                    channel_approvals[channel]["approved"] += 1
                    self.duration_stats["good"].append(duration)
                    self._extract_keywords(title, is_good=True)
                else:
                    channel_approvals[channel]["rejected"] += 1
                    self.duration_stats["bad"].append(duration)
                    self._extract_keywords(title, is_good=False)

            # 计算频道通过率
            for channel, stats in channel_approvals.items():
                total = stats["approved"] + stats["rejected"]
                if total >= 2:  # 至少2个样本才可靠
                    approval_rate = stats["approved"] / total
                    self.channel_stats[channel] = {
                        "approval_rate": approval_rate,
                        "total_reviews": total,
                        "approved": stats["approved"]
                    }

            logger.info(f"📊 分析了 {len(videos)} 个历史视频")
            logger.info(f"   - {len(self.channel_stats)} 个频道有足够数据")
            logger.info(f"   - {len(self.keyword_stats['good'])} 个好关键词")
            logger.info(f"   - {len(self.keyword_stats['bad'])} 个坏关键词")

        except Exception as e:
            logger.warning(f"⚠️ 无法分析历史数据: {e}")
    # 在 VideoScorer 类中添加这个新方法
    def save_score_to_db(self, video_url: str, score_result: Dict):
        """将评分结果保存回数据库"""
        if not self.links_path.exists():
            return
            
        try:
            with open(self.links_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            updated = False
            for video in data.get('videos', []):
                if video['url'] == video_url:
                    # 保存分数和理由
                    video['ai_score'] = score_result['score']
                    video['score_reason'] = "; ".join(score_result['reasons'])
                    video['score_recommendation'] = score_result['recommendation']
                    updated = True
                    break
            
            if updated:
                with open(self.links_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                # logger.info(f"💾 分数已保存: {video_url[:30]}...")
                
        except Exception as e:
            logger.error(f"保存分数失败: {e}")
    def _extract_keywords(self, title: str, is_good: bool):
        """提取标题关键词"""
        # 简单的关键词提取（可以改进）
        words = re.findall(r'\b\w{3,}\b', title.lower())

        # 只保留出现频率高的词
        target_set = self.keyword_stats["good"] if is_good else self.keyword_stats["bad"]

        for word in words:
            # 过滤常见词
            if word not in ['the', 'and', 'for', 'with', 'this', 'that', 'from', 'video']:
                target_set.add(word)

    def score_video(self, video_metadata: Dict) -> Dict:
        """
        评分视频（0-1之间）

        Args:
            video_metadata: 包含 channel, duration, title, view_count 等

        Returns:
            {
                'score': float,  # 0-1之间
                'confidence': str,  # 高/中/低
                'reasons': List[str],  # 评分原因
                'recommendation': str  # 建议：skip/download/priority
            }
        """
        score = 0.5  # 基础分
        reasons = []
        confidence = "中"

        # 1. 频道历史表现 (权重: 0.4)
        channel = video_metadata.get('channel', '')
        if channel in self.channel_stats:
            stats = self.channel_stats[channel]
            approval_rate = stats['approval_rate']
            total_reviews = stats['total_reviews']

            # 频道分数
            channel_score = approval_rate * 0.4
            score += channel_score

            # 置信度
            if total_reviews >= 5:
                confidence = "高"

            reasons.append(
                f"频道'{channel}'历史通过率: {approval_rate:.1%} "
                f"({stats['approved']}/{total_reviews})"
            )
        else:
            reasons.append(f"频道'{channel}'无历史记录")

        # 2. 时长偏好 (权重: 0.2)
        duration = video_metadata.get('duration', 0)

        if self.duration_stats["good"]:
            # 计算好视频的平均时长
            good_durations = self.duration_stats["good"]
            avg_good = sum(good_durations) / len(good_durations)

            # 在理想范围内加分
            if 0.7 * avg_good <= duration <= 1.3 * avg_good:
                score += 0.15
                reasons.append(f"时长{duration}秒接近理想范围")
            elif 0.5 * avg_good <= duration <= 1.5 * avg_good:
                score += 0.08
                reasons.append(f"时长{duration}秒在可接受范围")
            else:
                score -= 0.05
                reasons.append(f"时长{duration}秒偏离理想范围")
        else:
            # 默认偏好
            if 60 <= duration <= 180:
                score += 0.1
                reasons.append(f"时长{duration}秒在常规范围")

        # 3. 标题关键词 (权重: 0.2)
        title = video_metadata.get('title', '').lower()

        good_keyword_count = sum(1 for kw in self.keyword_stats["good"] if kw in title)
        bad_keyword_count = sum(1 for kw in self.keyword_stats["bad"] if kw in title)

        if good_keyword_count > 0:
            keyword_score = min(good_keyword_count * 0.05, 0.15)
            score += keyword_score
            reasons.append(f"标题包含{good_keyword_count}个正面关键词")

        if bad_keyword_count > 0:
            keyword_penalty = min(bad_keyword_count * 0.05, 0.15)
            score -= keyword_penalty
            reasons.append(f"标题包含{bad_keyword_count}个负面关键词")

        # 4. 观看次数 (权重: 0.1)
        view_count = video_metadata.get('view_count', 0)

        if view_count > 100000:
            score += 0.05
            reasons.append(f"高观看量: {view_count:,}")
        elif view_count < 1000:
            score -= 0.05
            reasons.append(f"低观看量: {view_count:,}")

        # 确保分数在 [0, 1] 范围内
        score = max(0.0, min(1.0, score))

        # 生成建议
        if score >= 0.7:
            recommendation = "priority"  # 优先下载
        elif score >= 0.4:
            recommendation = "download"  # 正常下载
        else:
            recommendation = "skip"  # 跳过

        return {
            'score': round(score, 3),
            'confidence': confidence,
            'reasons': reasons,
            'recommendation': recommendation,
            'channel_known': channel in self.channel_stats
        }

    def get_channel_whitelist(self, min_approval_rate: float = 0.8, min_samples: int = 3) -> List[str]:
        """获取高质量频道白名单"""
        whitelist = []

        for channel, stats in self.channel_stats.items():
            if (stats['approval_rate'] >= min_approval_rate and
                stats['total_reviews'] >= min_samples):
                whitelist.append(channel)

        return whitelist

    def get_channel_blacklist(self, max_approval_rate: float = 0.2, min_samples: int = 3) -> List[str]:
        """获取低质量频道黑名单"""
        blacklist = []

        for channel, stats in self.channel_stats.items():
            if (stats['approval_rate'] <= max_approval_rate and
                stats['total_reviews'] >= min_samples):
                blacklist.append(channel)

        return blacklist

    def print_statistics(self):
        """打印统计信息"""
        print("\n" + "="*80)
        print("📊 视频评分系统 - 学习到的模式")
        print("="*80)

        # 频道统计
        if self.channel_stats:
            print(f"\n🎬 频道统计 (共 {len(self.channel_stats)} 个):")

            # 按通过率排序
            sorted_channels = sorted(
                self.channel_stats.items(),
                key=lambda x: (x[1]['approval_rate'], x[1]['total_reviews']),
                reverse=True
            )

            print("\n  ✅ Top 5 高质量频道:")
            for channel, stats in sorted_channels[:5]:
                print(f"    - {channel}: {stats['approval_rate']:.1%} "
                      f"({stats['approved']}/{stats['total_reviews']})")

            print("\n  ❌ Top 5 低质量频道:")
            for channel, stats in sorted_channels[-5:]:
                print(f"    - {channel}: {stats['approval_rate']:.1%} "
                      f"({stats['approved']}/{stats['total_reviews']})")

        # 时长统计
        if self.duration_stats["good"]:
            avg_good = sum(self.duration_stats["good"]) / len(self.duration_stats["good"])
            print(f"\n⏱️ 理想视频时长: {avg_good:.0f}秒 "
                  f"(基于 {len(self.duration_stats['good'])} 个好视频)")

        # 关键词统计
        print(f"\n🔑 标题关键词:")
        print(f"  - 正面关键词: {len(self.keyword_stats['good'])} 个")
        if self.keyword_stats['good']:
            print(f"    示例: {list(self.keyword_stats['good'])[:10]}")

        print(f"  - 负面关键词: {len(self.keyword_stats['bad'])} 个")
        if self.keyword_stats['bad']:
            print(f"    示例: {list(self.keyword_stats['bad'])[:10]}")

        print("\n" + "="*80)


def main():
    """测试评分系统"""
    import argparse

    parser = argparse.ArgumentParser(description="视频评分系统")
    parser.add_argument(
        "--links-file",
        default="data/youtube_links.json",
        help="youtube_links.json路径"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="显示统计信息"
    )

    args = parser.parse_args()

    # 初始化评分器
    scorer = VideoScorer(youtube_links_path=args.links_file)

    if args.stats:
        scorer.print_statistics()

        # 显示白名单/黑名单
        whitelist = scorer.get_channel_whitelist()
        blacklist = scorer.get_channel_blacklist()

        print(f"\n✅ 频道白名单 (通过率≥80%, 样本≥3):")
        for channel in whitelist:
            print(f"  - {channel}")

        print(f"\n❌ 频道黑名单 (通过率≤20%, 样本≥3):")
        for channel in blacklist:
            print(f"  - {channel}")
    else:
        # 测试评分
        test_video = {
            'channel': 'Test Channel',
            'duration': 120,
            'title': 'People arguing in public',
            'view_count': 50000
        }

        result = scorer.score_video(test_video)

        print(f"\n测试视频评分:")
        print(f"  分数: {result['score']:.3f}")
        print(f"  置信度: {result['confidence']}")
        print(f"  建议: {result['recommendation']}")
        print(f"\n  原因:")
        for reason in result['reasons']:
            print(f"    - {reason}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    main()
