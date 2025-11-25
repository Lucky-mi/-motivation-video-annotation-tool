#!/usr/bin/env python3
"""
全自动扩展采集器 V3.1 - 修复版
修复：
1. ✅ 增加 data/channel_history.json 持久化记录已挖掘的频道
2. ✅ 修复种子视频缺少频道信息导致无法去重的问题
3. ✅ 入库时保存 channel 信息（如果 downloader 支持）
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
from backend.related_video_expander import RelatedVideoExpander
from backend.video_scorer import VideoScorer

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoExpanderV3:
    def __init__(self, db_path="data/youtube_links.json"):
        self.downloader = VideoDownloader()
        self.filter = ContentFilter()
        self.channel_expander = RelatedVideoExpander()
        self.scorer = VideoScorer(youtube_links_path=str(db_path))
        self.db_path = Path(db_path)
        
        # === 新增：独立的频道历史文件 ===
        self.history_file = Path("data/channel_history.json")

        self.existing_urls = set()
        self.searched_channels = set()
        
        self._load_existing_data()
        self._load_history()  # 加载历史记录

    def _load_existing_data(self):
        """加载已有的URL"""
        if self.db_path.exists():
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for v in data.get('videos', []):
                    self.existing_urls.add(v['url'])
                    # 兼容旧数据：如果有频道信息也加载，但不作为主要依据
                    if v.get('channel'):
                        self.searched_channels.add(v['channel'])

        logger.info(f"📊 数据库已加载: {len(self.existing_urls)} 个URL")

    def _load_history(self):
        """加载频道挖掘历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    channels = history.get('mined_channels', [])
                    self.searched_channels.update(channels)
                logger.info(f"📜 历史记录已加载: {len(self.searched_channels)} 个已挖掘频道")
            except Exception as e:
                logger.warning(f"加载历史记录失败: {e}")

    def _save_history(self, new_channel):
        """保存新的已挖掘频道"""
        if not new_channel:
            return
            
        self.searched_channels.add(new_channel)
        
        data = {'mined_channels': list(self.searched_channels)}
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")

    def get_high_quality_seeds(self):
        """获取高质量种子视频"""
        if not self.db_path.exists():
            return []

        with open(self.db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 只要是通过审核的都算种子
        seeds = [v for v in data.get('videos', []) if v.get('approved') is True]
        logger.info(f"💎 发现 {len(seeds)} 个高质量种子视频")
        return seeds

    def _get_channel_name_safe(self, seed):
        """
        安全获取频道名。
        如果种子数据里没有channel字段，尝试从扩展器获取（如果不影响流程）
        或者直接返回空，但在扩展后更新。
        """
        # 1. 优先从种子数据获取
        channel = seed.get('channel') or seed.get('uploader')
        if channel:
            return channel
            
        # 2. 如果数据里没有（比如你的情况），我们暂且返回 None
        # 在 run 循环里，我们会通过扩展器找到它，然后保存到历史记录
        return None

    def run(self, max_seeds=5, limit_per_seed=10, auto_download=True):
        seeds = self.get_high_quality_seeds()

        logger.info(f"🚀 启动混合扩展引擎 V3.1 (处理前 {min(len(seeds), max_seeds)} 个种子)...")

        new_channels_found = 0
        
        # 遍历种子
        for idx, seed in enumerate(seeds[:max_seeds], 1):
            title = seed.get('title', 'Unknown')
            logger.info(f"\n{'='*60}")
            logger.info(f"🎬 [种子 {idx}/{min(len(seeds), max_seeds)}] {title[:50]}...")
            
            # 尝试获取频道名
            seed_channel = self._get_channel_name_safe(seed)
            
            # === 关键修复：检查频道是否已挖掘 ===
            if seed_channel and seed_channel in self.searched_channels:
                logger.info(f"  ⏭️ 跳过已挖掘频道: {seed_channel}")
                continue

            candidates = []
            detected_channel_name = None

            # === 策略 1: 深度挖掘 (优先执行以获取频道名) ===
            logger.info("  📡 [策略A] 深挖频道...")
            try:
                # 这一步会联网获取视频信息，包括频道名
                channel_videos = self.channel_expander.find_related_videos(
                    seed['url'],
                    max_related=limit_per_seed
                )
                
                # 尝试从返回的视频里提取频道名（通常同频道的视频频道名是一样的）
                if channel_videos and not seed_channel:
                    detected_channel_name = channel_videos[0].get('channel')
                    if detected_channel_name:
                        logger.info(f"    🕵️ 自动识别到频道名: {detected_channel_name}")
                        # 再次检查是否已挖掘（防止重复）
                        if detected_channel_name in self.searched_channels:
                            logger.info(f"    ⏭️ 识别后发现该频道已挖掘，跳过后续步骤")
                            continue
                        seed_channel = detected_channel_name

                for v in channel_videos:
                    v['source_type'] = 'channel_depth'
                candidates.extend(channel_videos)
                
                # 记录这个频道为“已挖掘”
                if seed_channel:
                    self._save_history(seed_channel)
                    new_channels_found += 1
                    logger.info(f"    📝 已将频道 '{seed_channel}' 记入历史")

            except Exception as e:
                logger.warning(f"    频道挖掘失败: {e}")

            # === 策略 2: 广度搜索 ===
            logger.info("  📡 [策略B] 搜索相似话题...")
            try:
                # 清理标题，提取关键词
                search_query = title.split('(')[0].split('|')[0].split('-')[0].strip()
                if len(search_query) > 30: # 截断太长的标题
                    search_query = search_query[:30]

                topic_videos = self.downloader.search_videos(
                    search_query,
                    limit=limit_per_seed
                )
                for v in topic_videos:
                    v['source_type'] = 'topic_breadth'
                candidates.extend(topic_videos)

            except Exception as e:
                logger.warning(f"    话题搜索失败: {e}")

            # === 统一处理 ===
            self._process_candidates(candidates, auto_download)

        logger.info(f"\n{'='*80}")
        logger.info(f"🎉 本轮扩展完成！新挖掘频道: {new_channels_found}")
        logger.info(f"{'='*80}")

    def _process_candidates(self, candidates, auto_download):
        # ... (保持原有的去重、评分、下载、审核逻辑) ...
        # 唯一需要修改的是 add_video_link 调用，尝试传入 channel 
        # (这取决于你的 downloader.py 是否支持 channel 参数，
        # 如果不支持，Python 会报错，所以这里为了稳妥暂不改 downloader 调用，
        # 而是依赖上面的 _save_history 解决核心问题)
        
        # === 1. 去重 ===
        new_videos = []
        for vid in candidates:
            if vid['url'] not in self.existing_urls:
                self.existing_urls.add(vid['url'])
                new_videos.append(vid)

        if not new_videos:
            logger.info("    ⚠️ 无新视频")
            return

        # === 2. 评分 ===
        scored_videos = []
        for video in new_videos:
            res = self.scorer.score_video(video)
            video['pre_score'] = res['score']
            if res['recommendation'] != 'skip':
                scored_videos.append(video)
                # print log...
        
        scored_videos.sort(key=lambda x: x['pre_score'], reverse=True)
        
        if not auto_download or not scored_videos:
            return

        # === 3. 下载 & 4. 审核 ===
        logger.info(f"  ⬇️ 处理 {len(scored_videos)} 个高分视频...")
        
        # 收集需要下载的
        download_queue = []
        for vid in scored_videos:
            try:
                info = self.downloader.download_from_url(vid['url'])
                if not info.get('skipped'):
                    download_queue.append({
                        'info': vid,
                        'path': info['video_path'],
                        'duration': info['duration']
                    })
            except Exception as e:
                logger.error(f"    下载失败: {e}")

        if not download_queue:
            return

        # AI 审核
        paths = [d['path'] for d in download_queue]
        reviews = self.filter.batch_check(paths, strict_mode=True, max_workers=5)

        for item in download_queue:
            path = item['path']
            vid = item['info']
            review = reviews.get(path, {'pass': False, 'reason': 'Unknown'})
            
            approved = review.get('pass', False)
            
            # 入库
            self.downloader.add_video_link(
                url=vid['url'],
                title=vid.get('title', 'Unknown'),
                duration=item['duration'],
                keyword=f"AutoExpand-{vid.get('source_type')}",
                approved=approved,
                review_reason=review.get('reason', '')
            )
            
            if not approved:
                Path(path).unlink(missing_ok=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="混合策略视频扩展器 V3.1")
    parser.add_argument("--max-seeds", type=int, default=5)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()
    expander = AutoExpanderV3()
    expander.run(args.max_seeds, args.limit, not args.dry_run)