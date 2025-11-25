#!/usr/bin/env python3
"""
检查视频文件完整性
找出损坏或无法播放的视频
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import cv2
from pathlib import Path

def check_video_file(video_path):
    """检查单个视频文件是否可以正常打开"""
    try:
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            return False, "无法打开视频文件"

        # 尝试读取第一帧
        ret, frame = cap.read()

        if not ret or frame is None:
            cap.release()
            return False, "无法读取视频帧"

        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        cap.release()

        if fps == 0 or frame_count == 0:
            return False, "视频元数据异常（fps=0或frame_count=0）"

        return True, f"OK (分辨率:{width}x{height}, FPS:{fps:.1f}, 帧数:{frame_count})"

    except Exception as e:
        return False, f"检查出错: {str(e)}"

def main():
    # 加载视频数据库
    links_file = Path("data/youtube_links.json")
    if not links_file.exists():
        print("❌ youtube_links.json 不存在")
        return

    with open(links_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    videos = data['videos']

    # 只检查已下载且审核通过的视频
    approved_videos = [v for v in videos if v.get('approved') == True and v.get('video_path')]

    print(f"📊 开始检查 {len(approved_videos)} 个审核通过的视频...\n")

    ok_count = 0
    corrupted_count = 0
    missing_count = 0

    corrupted_videos = []

    for idx, video in enumerate(approved_videos, 1):
        video_path = Path(video['video_path'])
        title = video.get('title', 'Unknown')[:60]

        if not video_path.exists():
            print(f"[{idx}/{len(approved_videos)}] ❌ 文件不存在: {title}")
            missing_count += 1
            continue

        # 检查文件大小
        file_size = video_path.stat().st_size / 1024 / 1024  # MB

        # 检查视频完整性
        is_ok, msg = check_video_file(video_path)

        if is_ok:
            print(f"[{idx}/{len(approved_videos)}] ✅ {title} ({file_size:.1f}MB)")
            ok_count += 1
        else:
            print(f"[{idx}/{len(approved_videos)}] ⚠️  {title} ({file_size:.1f}MB)")
            print(f"     原因: {msg}")
            corrupted_count += 1
            corrupted_videos.append({
                'path': str(video_path),
                'title': title,
                'size_mb': file_size,
                'error': msg,
                'url': video.get('url')
            })

    # 统计结果
    print("\n" + "=" * 80)
    print("📊 检查结果统计")
    print("=" * 80)
    print(f"✅ 正常视频: {ok_count}")
    print(f"⚠️  损坏视频: {corrupted_count}")
    print(f"❌ 缺失文件: {missing_count}")
    print(f"总计: {len(approved_videos)}")

    if corrupted_videos:
        print("\n" + "=" * 80)
        print("⚠️  损坏的视频列表:")
        print("=" * 80)
        for v in corrupted_videos:
            print(f"\n标题: {v['title']}")
            print(f"文件: {v['path']}")
            print(f"大小: {v['size_mb']:.2f}MB")
            print(f"错误: {v['error']}")
            print(f"URL: {v['url']}")

        # 保存损坏视频列表
        corrupted_file = Path("data/corrupted_videos.json")
        with open(corrupted_file, 'w', encoding='utf-8') as f:
            json.dump(corrupted_videos, f, ensure_ascii=False, indent=2)
        print(f"\n💾 损坏视频列表已保存到: {corrupted_file}")

        print("\n💡 建议操作:")
        print("  1. 重新下载这些视频:")
        print("     for url in <损坏视频URL>; do")
        print("       # 使用下载脚本重新下载")
        print("     done")
        print("\n  2. 或者从数据库中删除这些记录")

if __name__ == "__main__":
    main()
