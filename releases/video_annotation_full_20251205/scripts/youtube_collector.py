#!/usr/bin/env python3
# scripts/youtube_collector.py
"""
YouTube视频采集主流程脚本
自动化完成：搜索 -> AI审核 -> 下载 的完整流程
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import logging
from typing import List, Optional
import argparse
from datetime import datetime

from backend.downloader import VideoDownloader
from backend.content_filter import ContentFilter

# 确保日志目录存在（必须在配置日志之前）
Path("logs").mkdir(exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/youtube_collector_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class YouTubeCollector:
    """YouTube视频采集器 - 完整的搜索、审核、下载流程"""

    def __init__(self, output_dir: str = "data/Youtube_videos", strict_mode: bool = True):
        """
        初始化采集器

        Args:
            output_dir: 视频保存目录
            strict_mode: 是否使用严格的审核模式
        """
        self.downloader = VideoDownloader(output_dir=output_dir)
        self.content_filter = ContentFilter()
        self.strict_mode = strict_mode

    def run_full_pipeline(self,
                         keywords: Optional[List[str]] = None,
                         videos_per_keyword: int = 3,
                         auto_download: bool = False,
                         max_downloads: int = 10) -> dict:
        """
        运行完整的采集流程

        Args:
            keywords: 搜索关键词列表（None则使用默认关键词）
            videos_per_keyword: 每个关键词搜索的视频数量
            auto_download: 是否自动下载通过审核的视频
            max_downloads: 最大下载数量

        Returns:
            统计信息字典
        """
        logger.info("=" * 80)
        logger.info("🚀 YouTube视频采集流程启动")
        logger.info(f"⚙️ 配置: 严格模式={'是' if self.strict_mode else '否'}, 自动下载={'是' if auto_download else '否'}")
        logger.info("=" * 80)

        stats = {
            "searched": 0,
            "approved": 0,
            "rejected": 0,
            "downloaded": 0,
            "failed": 0
        }

        # 阶段1: 批量搜索视频
        logger.info("\n📍 阶段 1/3: 批量搜索视频")
        logger.info("-" * 80)

        search_results = self.downloader.batch_search(
            keywords=keywords,
            videos_per_keyword=videos_per_keyword
        )
        stats["searched"] = len(search_results)

        if not search_results:
            logger.warning("⚠️ 未搜索到任何视频，流程终止")
            return stats

        logger.info(f"✅ 搜索完成: 共找到 {len(search_results)} 个候选视频\n")

        # 阶段2: AI审核视频（先下载少量视频进行审核）
        logger.info("\n📍 阶段 2/3: AI审核视频内容")
        logger.info("-" * 80)

        reviewed_videos = []

        for idx, video_info in enumerate(search_results, 1):
            logger.info(f"\n[{idx}/{len(search_results)}] 处理视频:")
            logger.info(f"  标题: {video_info['title']}")
            logger.info(f"  时长: {video_info['duration']}秒")
            logger.info(f"  频道: {video_info['channel']}")
            logger.info(f"  关键词: {video_info['search_keyword']}")

            try:
                # 先下载视频到临时位置进行审核
                logger.info("  ⬇️ 下载视频用于审核...")
                download_result = self.downloader.download_from_url(video_info['url'])
                video_path = download_result['video_path']

                # AI审核
                logger.info("  🤖 提交AI审核...")
                review_result = self.content_filter.check_video_content(
                    video_path,
                    strict_mode=self.strict_mode
                )

                # 记录审核结果
                approved = review_result.get('pass', False)
                video_info['review_result'] = review_result
                video_info['video_path'] = video_path
                video_info['approved'] = approved

                # 添加到数据库
                self.downloader.add_video_link(
                    url=video_info['url'],
                    title=video_info['title'],
                    duration=video_info['duration'],
                    keyword=video_info['search_keyword'],
                    approved=approved,
                    review_reason=review_result.get('reason', '')
                )

                if approved:
                    stats["approved"] += 1
                    logger.info(f"  ✅ 审核通过! (置信度: {review_result.get('confidence', 0):.2f})")
                    logger.info(f"     理由: {review_result.get('reason', '')}")
                    reviewed_videos.append(video_info)
                else:
                    stats["rejected"] += 1
                    logger.info(f"  ❌ 审核未通过")
                    logger.info(f"     理由: {review_result.get('reason', '')}")
                    # 删除未通过审核的视频
                    try:
                        Path(video_path).unlink()
                        logger.info("  🗑️ 已删除视频文件")
                    except Exception as e:
                        logger.warning(f"  删除文件失败: {e}")

            except Exception as e:
                logger.error(f"  ❌ 处理失败: {e}", exc_info=True)
                stats["failed"] += 1
                continue

        # 保存审核报告
        self._save_review_report(search_results, stats)

        logger.info("\n" + "=" * 80)
        logger.info("📊 审核统计:")
        logger.info(f"  搜索到: {stats['searched']} 个视频")
        logger.info(f"  通过审核: {stats['approved']} 个 ({stats['approved']/stats['searched']*100:.1f}%)")
        logger.info(f"  未通过: {stats['rejected']} 个 ({stats['rejected']/stats['searched']*100:.1f}%)")
        logger.info(f"  处理失败: {stats['failed']} 个")
        logger.info("=" * 80 + "\n")

        # 阶段3: 自动下载（可选）
        if auto_download and reviewed_videos:
            logger.info("\n📍 阶段 3/3: 下载通过审核的视频")
            logger.info("-" * 80)
            logger.info(f"💡 注意: 视频已在审核阶段下载，此阶段跳过")
            stats["downloaded"] = stats["approved"]
        else:
            logger.info("\n📍 阶段 3/3: 下载阶段")
            logger.info("-" * 80)
            logger.info("⏭️ 跳过自动下载（auto_download=False）")
            logger.info("💡 提示: 视频已在审核阶段下载完成")

        logger.info("\n" + "=" * 80)
        logger.info("🎉 采集流程完成!")
        logger.info("=" * 80)

        return stats

    def _save_review_report(self, videos: List[dict], stats: dict):
        """保存审核报告"""
        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"review_report_{timestamp}.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "videos": videos
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 审核报告已保存: {report_file}")

    def show_statistics(self):
        """显示当前统计信息"""
        db = self.downloader.links_db
        metadata = db['metadata']

        logger.info("\n" + "=" * 80)
        logger.info("📊 当前数据库统计")
        logger.info("=" * 80)
        logger.info(f"总视频数: {metadata['total_count']}")
        logger.info(f"通过审核: {metadata['approved_count']} ({metadata['approved_count']/max(metadata['total_count'], 1)*100:.1f}%)")
        logger.info(f"未通过: {metadata['rejected_count']}")
        logger.info(f"已下载: {metadata['downloaded_count']}")
        logger.info(f"最后更新: {metadata['last_updated']}")
        logger.info("=" * 80 + "\n")

    def download_approved_videos(self, max_count: Optional[int] = None):
        """下载所有通过审核但未下载的视频"""
        approved = self.downloader.get_approved_videos(downloaded_only=False)
        to_download = [v for v in approved if not v['downloaded']]

        if not to_download:
            logger.info("✅ 所有通过审核的视频都已下载")
            return

        if max_count:
            to_download = to_download[:max_count]

        logger.info(f"📥 开始下载 {len(to_download)} 个视频...")

        for idx, video in enumerate(to_download, 1):
            logger.info(f"[{idx}/{len(to_download)}] 下载: {video['title'][:50]}...")
            try:
                self.downloader.download_from_url(video['url'])
                logger.info("  ✅ 下载完成")
            except Exception as e:
                logger.error(f"  ❌ 下载失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="YouTube视频采集工具 - 心智理论研究专用")
    parser.add_argument("--mode", choices=["search", "review", "download", "full", "stats"],
                       default="full", help="运行模式")
    parser.add_argument("--keywords", nargs="+", help="自定义搜索关键词")
    parser.add_argument("--per-keyword", type=int, default=3, help="每个关键词搜索视频数")
    parser.add_argument("--max-downloads", type=int, default=10, help="最大下载数量")
    parser.add_argument("--no-strict", action="store_true", help="使用标准审核模式（非严格）")
    parser.add_argument("--auto-download", action="store_true", help="自动下载通过审核的视频")

    args = parser.parse_args()

    # 创建采集器
    collector = YouTubeCollector(strict_mode=not args.no_strict)

    if args.mode == "stats":
        # 仅显示统计信息
        collector.show_statistics()

    elif args.mode == "full":
        # 完整流程
        stats = collector.run_full_pipeline(
            keywords=args.keywords,
            videos_per_keyword=args.per_keyword,
            auto_download=args.auto_download,
            max_downloads=args.max_downloads
        )
        collector.show_statistics()

    elif args.mode == "search":
        # 仅搜索
        logger.info("🔍 搜索模式")
        results = collector.downloader.batch_search(
            keywords=args.keywords,
            videos_per_keyword=args.per_keyword
        )
        logger.info(f"找到 {len(results)} 个视频")

    elif args.mode == "download":
        # 仅下载已审核通过的视频
        logger.info("📥 下载模式")
        collector.download_approved_videos(max_count=args.max_downloads)

    else:
        logger.error(f"未知模式: {args.mode}")


if __name__ == "__main__":
    main()
