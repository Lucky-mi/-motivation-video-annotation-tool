#!/usr/bin/env python3
"""
检查视频文件完整性并修复问题
"""
import json
from pathlib import Path
import subprocess

def check_video_with_ffprobe(video_path: Path) -> bool:
    """使用ffprobe检查视频是否完整"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_format', '-show_streams', str(video_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0 and len(result.stdout) > 0
    except:
        return False

def check_video_basic(video_path: Path) -> bool:
    """基础检查：文件存在且大小合理"""
    if not video_path.exists():
        return False

    size_mb = video_path.stat().st_size / (1024 * 1024)
    # 视频文件应该大于1MB
    return size_mb > 1.0

def main():
    print("=" * 80)
    print("Video Integrity Check & Fix Tool")
    print("=" * 80)

    # 1. 加载数据库
    links_file = Path("data/youtube_links.json")
    with open(links_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. 找出所有视频文件
    video_dir = Path("data/Youtube_videos")
    all_files = set(f.name for f in video_dir.glob("*.mp4"))
    print(f"\nTotal video files on disk: {len(all_files)}")

    # 3. 找出数据库中的视频
    db_videos = []
    for video in data['videos']:
        if video.get('video_path'):
            db_videos.append(video)

    print(f"Videos with path in database: {len(db_videos)}")

    # 4. 检查数据库中记录的视频文件
    print("\n" + "=" * 80)
    print("Checking database videos...")
    print("=" * 80)

    missing_files = []
    small_files = []

    for video in db_videos:
        video_path = Path(video['video_path'])

        if not video_path.exists():
            missing_files.append(video)
            print(f"MISSING: {video_path.name}")
            print(f"  Title: {video['title'][:60]}")
            print(f"  URL: {video['url']}")
            print()
        else:
            size_mb = video_path.stat().st_size / (1024 * 1024)
            if size_mb < 1.0:
                small_files.append({'video': video, 'size': size_mb})
                print(f"SMALL: {video_path.name} ({size_mb:.2f} MB)")
                print(f"  Title: {video['title'][:60]}")
                print()

    # 5. 找出孤立文件（在磁盘上但不在数据库中）
    db_filenames = set()
    for video in db_videos:
        path = Path(video['video_path'])
        db_filenames.add(path.name)

    orphan_files = all_files - db_filenames

    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Database videos with missing files: {len(missing_files)}")
    print(f"Database videos with suspiciously small files: {len(small_files)}")
    print(f"Orphan files (on disk but not in DB): {len(orphan_files)}")

    # 6. 显示孤立文件
    if orphan_files:
        print("\nOrphan files (first 10):")
        for filename in list(orphan_files)[:10]:
            filepath = video_dir / filename
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"  {filename} ({size_mb:.2f} MB)")

    # 7. 问题文件列表
    problem_videos = []

    # 缺失文件的视频
    for video in missing_files:
        problem_videos.append({
            'url': video['url'],
            'title': video['title'],
            'reason': 'File missing',
            'approved': video.get('approved', False)
        })

    # 文件太小的视频
    for item in small_files:
        video = item['video']
        problem_videos.append({
            'url': video['url'],
            'title': video['title'],
            'reason': f'File too small ({item["size"]:.2f} MB)',
            'approved': video.get('approved', False)
        })

    # 8. 保存问题视频列表
    if problem_videos:
        from datetime import datetime
        problem_file = Path(f"data/problem_videos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(problem_file, 'w', encoding='utf-8') as f:
            json.dump(problem_videos, f, ensure_ascii=False, indent=2)

        print(f"\nProblem videos saved to: {problem_file}")

        approved_problems = [v for v in problem_videos if v['approved']]
        print(f"\nApproved videos with problems: {len(approved_problems)}")

        if approved_problems:
            print("\nOptions:")
            print("1. Re-download these approved videos (recommended)")
            print("2. Remove them from database")
            print("3. Do nothing")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
