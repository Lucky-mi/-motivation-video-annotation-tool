#!/usr/bin/env python3
# scripts/auto_expand_v2.py
"""
全自动扩展采集器 (V2 融合版)
策略：
1. 深度挖掘 (Depth): 扫描高质量博主的频道
2. 广度搜索 (Breadth): 使用高质量标题搜索相似视频
3. 自动闭环: 发现 -> 下载 -> AI审核 -> 入库
"""
import sys
import json
import logging
import argparse
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.downloader import VideoDownloader
from backend.content_filter import ContentFilter
from backend.related_video_expander import RelatedVideoExpander # 你的代码

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoExpanderV2:
    def __init__(self, db_path="data/youtube_links.json"):
        self.downloader = VideoDownloader()
        self.filter = ContentFilter()
        self.channel_expander = RelatedVideoExpander() # 你的频道扩展器
        self.db_path = Path(db_path)

        # 加载已有URL和频道用于去重
        self.existing_urls = set()
        self.searched_channels = set()  # 新增：已搜索的频道
        self._load_existing_data()

    def _load_existing_data(self):
        """加载已有的URL和频道信息"""
        if self.db_path.exists():
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for v in data.get('videos', []):
                    self.existing_urls.add(v['url'])
                    # 收集已处理过的频道
                    if 'channel' in v:
                        self.searched_channels.add(v['channel'])

        logger.info(f"📊 已加载: {len(self.existing_urls)} 个URL, {len(self.searched_channels)} 个频道")

    def get_high_quality_seeds(self):
        """获取高质量种子视频"""
        if not self.db_path.exists():
            return []
        
        with open(self.db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 筛选标准：已通过人工或AI审核的视频
        seeds = [v for v in data.get('videos', []) if v.get('approved') is True]
        logger.info(f"💎 发现 {len(seeds)} 个高质量种子视频")
        return seeds

    def run(self, max_seeds=5, limit_per_seed=3, auto_download=True):
        """执行混合扩展策略"""
        seeds = self.get_high_quality_seeds()

        # 如果种子太多，随机取样或取最新的，避免每次都跑很久
        # seeds = seeds[-max_seeds:]

        logger.info(f"🚀 启动混合扩展引擎 (处理前 {min(len(seeds), max_seeds)} 个种子)...")

        new_channels_found = 0  # 统计新搜索的频道数

        for idx, seed in enumerate(seeds[:max_seeds], 1):
            logger.info(f"\n🎬 [种子 {idx}] {seed['title'][:40]}...")

            # 检查频道是否已搜索过
            seed_channel = seed.get('channel', '')
            if seed_channel in self.searched_channels:
                logger.info(f"  ⏭️ 跳过已搜索频道: {seed_channel}")
                continue

            candidates = []

            # === 策略 1: 深度挖掘 (基于你的代码) ===
            logger.info("  📡 [策略A] 正在深挖博主频道...")
            try:
                channel_videos = self.channel_expander.find_related_videos(
                    seed['url'],
                    max_related=limit_per_seed
                )
                for v in channel_videos:
                    v['source_type'] = 'channel_depth'
                candidates.extend(channel_videos)

                # 标记频道为已搜索
                if seed_channel:
                    self.searched_channels.add(seed_channel)
                    new_channels_found += 1
                    logger.info(f"  ✅ 已标记频道: {seed_channel}")

            except Exception as e:
                logger.warning(f"    频道挖掘失败: {e}")

            # === 策略 2: 广度搜索 (基于我的建议) ===
            logger.info("  📡 [策略B] 正在搜索相似话题...")
            try:
                # 清理标题作为关键词
                search_query = seed['title'].split('(')[0].split('|')[0].strip()
                topic_videos = self.downloader.search_videos(
                    search_query, 
                    limit=limit_per_seed
                )
                for v in topic_videos:
                    v['source_type'] = 'topic_breadth'
                candidates.extend(topic_videos)
            except Exception as e:
                logger.warning(f"    话题搜索失败: {e}")

            # === 统一处理候选视频 ===
            self._process_candidates(candidates, auto_download)

        # 输出最终统计
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 扩展完成统计:")
        logger.info(f"  - 本次搜索新频道: {new_channels_found} 个")
        logger.info(f"  - 累计已搜索频道: {len(self.searched_channels)} 个")
        logger.info(f"  - 累计视频URL: {len(self.existing_urls)} 个")
        logger.info(f"{'='*60}")

    def _process_candidates(self, candidates, auto_download):
        """去重、下载与审核"""
        new_count = 0
        for vid in candidates:
            url = vid['url']
            title = vid.get('title', 'Unknown')
            source = vid.get('source_type', 'unknown')

            # 1. 去重
            if url in self.existing_urls:
                continue
            
            self.existing_urls.add(url) # 标记为已处理
            new_count += 1
            
            logger.info(f"  Found: [{source}] {title[:30]}...")

            if not auto_download:
                continue

            # 2. 下载 & 审核流程
            try:
                # 下载
                dl_info = self.downloader.download_from_url(url)
                video_path = dl_info['video_path']
                
                # AI 审核
                review = self.filter.check_video_content(video_path, strict_mode=True)
                approved = review.get('pass', False)
                
                # 入库
                self.downloader.add_video_link(
                    url=url,
                    title=title,
                    duration=dl_info['duration'],
                    keyword=f"AutoExpand-{source}", # 标记来源
                    approved=approved,
                    review_reason=review.get('reason', '')
                )
                
                if approved:
                    logger.info(f"    ✅ 审核通过! ({review.get('reason')})")
                else:
                    logger.info(f"    ❌ 审核拒绝. ({review.get('reason')})")
                    Path(video_path).unlink(missing_ok=True) # 删除垃圾文件

            except Exception as e:
                logger.error(f"    处理异常: {e}")

        if new_count == 0:
            logger.info("    (没有发现新视频)")

def main():
    parser = argparse.ArgumentParser(description="混合策略视频扩展器")
    parser.add_argument("--max-seeds", type=int, default=5, help="使用的种子视频数量")
    parser.add_argument("--limit", type=int, default=3, help="每个策略获取的视频数")
    parser.add_argument("--dry-run", action="store_true", help="仅搜索不下载")
    parser.add_argument("--show-channels", action="store_true", help="显示已搜索的频道列表")

    args = parser.parse_args()

    expander = AutoExpanderV2()

    # 如果只是查看频道列表
    if args.show_channels:
        logger.info(f"\n{'='*60}")
        logger.info(f"📺 已搜索频道列表 (共 {len(expander.searched_channels)} 个):")
        logger.info(f"{'='*60}")
        for idx, channel in enumerate(sorted(expander.searched_channels), 1):
            logger.info(f"  {idx}. {channel}")
        logger.info(f"{'='*60}")
        return

    expander.run(
        max_seeds=args.max_seeds,
        limit_per_seed=args.limit,
        auto_download=not args.dry_run
    )

if __name__ == "__main__":
    main()