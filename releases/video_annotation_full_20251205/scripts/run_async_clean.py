#!/usr/bin/env python
import sys, os
from pathlib import Path
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
import asyncio, json, time, argparse, logging
sys.path.insert(0, str(project_root / "config"))
from search_config import ENABLE_AI_REVIEW, STRICT_MODE, AUTO_DELETE_REJECTED, AI_REVIEW_WORKERS
from backend.downloader import VideoDownloader
from backend.content_filter import ContentFilter
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncVideoProcessor:
    def __init__(self, downloader, content_filter=None, download_concurrency=2, review_concurrency=3):
        self.downloader = downloader
        self.content_filter = content_filter
        self.download_sem = asyncio.Semaphore(download_concurrency)
        self.review_sem = asyncio.Semaphore(review_concurrency)
        self.stats = {'downloaded': 0, 'download_failed': 0, 'reviewed': 0, 'approved': 0, 'rejected': 0, 'skipped': 0}
    
    async def download_video(self, video_info, index, total):
        async with self.download_sem:
            try:
                logger.info(f"[{index}/{total}] Downloading...")
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.downloader.download_from_url, video_info['url'])
                if result.get('skipped', False):
                    self.stats['skipped'] += 1
                    return None
                self.stats['downloaded'] += 1
                result['video_info'] = video_info
                return result
            except Exception as e:
                self.stats['download_failed'] += 1
                logger.error(f"[{index}/{total}] Download failed: {e}")
                return None
    
    async def review_video(self, download_result, index, total):
        async with self.review_sem:
            video_path = download_result['video_path']
            video_info = download_result['video_info']
            try:
                logger.info(f"[{index}/{total}] Reviewing...")
                review_result = await self.content_filter.check_video_content(video_path, strict_mode=STRICT_MODE)
                self.stats['reviewed'] += 1
                approved = review_result.get('pass', False)
                if approved:
                    self.stats['approved'] += 1
                else:
                    self.stats['rejected'] += 1
                self.downloader.add_video_link(url=video_info['url'], title=video_info['title'], duration=download_result['duration'], keyword=video_info.get('search_keyword', 'Unknown'), approved=approved, review_reason=review_result.get('reason', ''), video_path=video_path)
                if not approved and AUTO_DELETE_REJECTED:
                    Path(video_path).unlink(missing_ok=True)
                return {'approved': approved}
            except Exception as e:
                self.stats['review_failed'] += 1
                logger.error(f"[{index}/{total}] Review failed: {e}")
                return {'approved': False}
    
    async def process_video_pipeline(self, video_info, index, total):
        download_result = await self.download_video(video_info, index, total)
        if download_result is None:
            return None
        if self.content_filter:
            return await self.review_video(download_result, index, total)
        else:
            self.downloader.add_video_link(url=video_info['url'], title=video_info['title'], duration=download_result['duration'], keyword=video_info.get('search_keyword', 'Unknown'), approved=None, video_path=download_result['video_path'])
            return download_result
    
    async def process_batch(self, videos):
        total = len(videos)
        tasks = [self.process_video_pipeline(video, idx + 1, total) for idx, video in enumerate(videos)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if r is not None and not isinstance(r, Exception)]
    
    def print_stats(self):
        print("\nStatistics:")
        print(f"Downloaded: {self.stats['downloaded']} | Skipped: {self.stats['skipped']} | Failed: {self.stats['download_failed']}")
        if self.content_filter:
            print(f"Reviewed: {self.stats['reviewed']} | Approved: {self.stats['approved']} | Rejected: {self.stats['rejected']}")
            if self.stats['reviewed'] > 0:
                print(f"Approval Rate: {self.stats['approved'] / self.stats['reviewed'] * 100:.1f}%")

def load_search_results(file_path):
    path = Path(file_path)
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get('videos', [])

async def main_async(args):
    print("Async Video Processing System")
    videos = load_search_results(args.input)
    if not videos:
        return
    downloader = VideoDownloader(proxy=args.proxy)
    content_filter = ContentFilter() if ENABLE_AI_REVIEW and not args.skip_review else None
    existing = {v['url'] for v in downloader.links_db['videos']}
    videos = [v for v in videos if v['url'] not in existing]
    videos = videos[args.start:args.start + args.limit if args.limit else None]
    print(f"Config: Download={args.download_workers}, Review={args.review_workers}, Videos={len(videos)}")
    if not args.yes and input("Continue? (y/n): ").lower() != 'y':
        return
    processor = AsyncVideoProcessor(downloader, content_filter, args.download_workers, args.review_workers)
    print("Starting...")
    start = time.time()
    await processor.process_batch(videos)
    duration = time.time() - start
    processor.print_stats()
    print(f"Total time: {duration:.1f}s")

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', default='data/search_results.json')
    p.add_argument('--start', type=int, default=0)
    p.add_argument('--limit', type=int)
    p.add_argument('--download-workers', type=int, default=2)
    p.add_argument('--review-workers', type=int, default=AI_REVIEW_WORKERS)
    p.add_argument('--skip-review', action='store_true')
    p.add_argument('--proxy')
    p.add_argument('-y', '--yes', action='store_true')
    asyncio.run(main_async(p.parse_args()))

if __name__ == '__main__':
    main()
