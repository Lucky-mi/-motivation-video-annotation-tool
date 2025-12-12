#!/usr/bin/env python3
"""
自动下载缺失的审核通过视频
"""
import json
from pathlib import Path
import sys

# 检查导入
try:
    import yt_dlp
    print("OK: yt_dlp imported")
except ImportError:
    print("ERROR: yt_dlp not found")
    sys.exit(1)

def main():
    print("="*80)
    print("Auto-download missing approved videos")
    print("="*80)

    # 1. 加载数据库
    links_file = Path("data/youtube_links.json")
    with open(links_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. 找出审核通过但缺失文件的视频
    approved_missing = []
    for v in data['videos']:
        if v.get('approved') == True:
            video_path = v.get('video_path')
            if not video_path or not Path(video_path).exists():
                approved_missing.append(v)

    print(f"\nFound {len(approved_missing)} approved videos with missing files")

    if not approved_missing:
        print("All approved videos are OK!")
        return

    # 3. 显示列表
    print("\nList:")
    for i, v in enumerate(approved_missing, 1):
        try:
            print(f"{i}. {v['title'][:60]}")
        except UnicodeEncodeError:
            print(f"{i}. [Title with special characters]")

    # 4. 确认
    print("\n" + "="*80)
    response = input(f"\nDownload these {len(approved_missing)} videos? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    # 5. 下载
    print("\nDownloading...")
    output_dir = Path("data/Youtube_videos")
    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    failed_count = 0
    downloaded_info = []

    for idx, video in enumerate(approved_missing, 1):
        url = video['url']
        title = video['title'][:50]

        try:
            print(f"\n[{idx}/{len(approved_missing)}] {title}...")
        except UnicodeEncodeError:
            print(f"\n[{idx}/{len(approved_missing)}] [Video with special characters]...")

        try:
            import uuid
            video_id = str(uuid.uuid4())
            out_tmpl = str(output_dir / f"{video_id}.%(ext)s")

            # 使用和downloader.py完全相同的配置
            ydl_opts = {
                'format': 'best',
                'outtmpl': out_tmpl,
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'ignoreerrors': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                duration = info.get('duration', 0)

                # 获取实际文件路径
                filename = ydl.prepare_filename(info)
                output_path = Path(filename)

            if output_path.exists():
                print(f"  SUCCESS: {output_path.name}")
                success_count += 1

                downloaded_info.append({
                    'url': url,
                    'title': video['title'],
                    'video_path': str(output_path),
                    'duration': duration,
                    'keyword': video.get('keyword', 'Unknown')
                })
            else:
                print(f"  FAILED: File not created")
                failed_count += 1

        except Exception as e:
            print(f"  ERROR: {str(e)[:100]}")
            failed_count += 1

    # 6. 更新数据库
    if downloaded_info:
        print("\n" + "="*80)
        print("Updating database...")

        # 删除旧记录
        urls_to_update = {v['url'] for v in downloaded_info}
        data['videos'] = [v for v in data['videos'] if v['url'] not in urls_to_update]

        # 添加新记录
        from datetime import datetime
        for info in downloaded_info:
            data['videos'].append({
                'url': info['url'],
                'title': info['title'],
                'duration': info['duration'],
                'keyword': info['keyword'],
                'approved': True,  # 保持原来的审核结果
                'review_reason': 'Re-downloaded (previously approved)',
                'downloaded': True,
                'video_path': info['video_path'],
                'added_time': datetime.now().isoformat()
            })

        # 更新元数据
        data['metadata']['total_count'] = len(data['videos'])
        data['metadata']['approved_count'] = sum(1 for v in data['videos'] if v.get('approved') == True)
        data['metadata']['downloaded_count'] = sum(1 for v in data['videos'] if v.get('downloaded') == True)

        # 保存
        with open(links_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  Database updated: {links_file}")

    # 7. 总结
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    print(f"Success: {success_count}")
    print(f"Failed:  {failed_count}")
    print(f"Total:   {len(approved_missing)}")
    print("="*80)

if __name__ == "__main__":
    main()
