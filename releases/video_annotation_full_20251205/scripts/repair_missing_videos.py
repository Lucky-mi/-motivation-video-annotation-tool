#!/usr/bin/env python3
"""
修复缺失视频文件的脚本
重新下载审核通过但文件路径缺失的视频
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from backend.downloader import VideoDownloader
from backend.content_filter import ContentFilter

# 导入配置
sys.path.insert(0, str(Path(__file__).parent.parent / "config"))
from search_config import ENABLE_AI_REVIEW, STRICT_MODE, AI_REVIEW_WORKERS

def main():
    print("=" * 80)
    print("🔧 修复缺失视频文件工具")
    print("=" * 80)

    # 加载数据库
    links_file = Path("data/youtube_links.json")
    if not links_file.exists():
        print("❌ youtube_links.json 不存在")
        return

    with open(links_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    videos = data['videos']

    # 找出审核通过但缺失文件的视频
    missing_videos = []
    for video in videos:
        if video.get('approved') == True:
            video_path = video.get('video_path')
            if video_path is None:
                # 路径为空
                missing_videos.append(video)
            elif not Path(video_path).exists():
                # 文件不存在
                missing_videos.append(video)

    if not missing_videos:
        print("✅ 所有审核通过的视频文件都存在！")
        return

    print(f"\n📊 发现 {len(missing_videos)} 个审核通过但文件缺失的视频：\n")
    for idx, video in enumerate(missing_videos, 1):
        print(f"{idx}. {video['title'][:60]}")
        print(f"   URL: {video['url']}")
        print(f"   原因: {'路径为空' if video.get('video_path') is None else '文件已删除'}")
        print()

    # 确认操作
    print("=" * 80)
    print("🔄 操作说明:")
    print("  1. 从数据库中删除这些记录")
    print("  2. 重新下载这些视频")
    print("  3. 重新进行AI审核（会重新验证）")
    print("=" * 80)

    response = input("\n确认继续? (y/n): ")
    if response.lower() != 'y':
        print("❌ 已取消")
        return

    # 初始化下载器
    downloader = VideoDownloader()

    print("\n📦 步骤 1/3: 从数据库中删除缺失视频的记录...")

    # 获取要删除的URL集合
    urls_to_remove = {v['url'] for v in missing_videos}

    # 过滤掉这些记录
    original_count = len(data['videos'])
    data['videos'] = [v for v in data['videos'] if v['url'] not in urls_to_remove]
    removed_count = original_count - len(data['videos'])

    # 更新元数据
    data['metadata']['total_count'] = len(data['videos'])
    data['metadata']['approved_count'] = sum(1 for v in data['videos'] if v.get('approved') == True)
    data['metadata']['rejected_count'] = sum(1 for v in data['videos'] if v.get('approved') == False)

    # 保存更新后的数据库
    with open(links_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 已删除 {removed_count} 条记录")

    # 重新下载
    print("\n📦 步骤 2/3: 重新下载视频...")

    downloaded = []
    failed = []

    for idx, video in enumerate(missing_videos, 1):
        url = video['url']
        title = video['title'][:60]

        print(f"  [{idx}/{len(missing_videos)}] 下载: {title}...")

        try:
            result = downloader.download_from_url(url)
            downloaded.append({
                'video': video,
                'path': result['video_path'],
                'duration': result['duration']
            })
            print(f"    ✅ 成功")
        except Exception as e:
            print(f"    ❌ 失败: {e}")
            failed.append({'video': video, 'error': str(e)})

    if not downloaded:
        print("\n⚠️ 没有成功下载任何视频")
        return

    # 重新审核（可选）
    if ENABLE_AI_REVIEW:
        print(f"\n📦 步骤 3/3: 重新AI审核 {len(downloaded)} 个视频...")

        content_filter = ContentFilter()

        video_paths = [v['path'] for v in downloaded]
        review_results = content_filter.batch_check(
            video_paths,
            strict_mode=STRICT_MODE,
            max_workers=AI_REVIEW_WORKERS
        )

        # 入库
        approved_count = 0
        rejected_count = 0

        for video_data in downloaded:
            video = video_data['video']
            video_path = video_data['path']
            review_result = review_results.get(video_path, {"pass": False, "reason": "审核失败"})

            approved = review_result.get('pass', False)

            # 重新添加到数据库
            downloader.add_video_link(
                url=video['url'],
                title=video['title'],
                duration=video_data['duration'],
                keyword=video.get('keyword', 'Unknown'),
                approved=approved,
                review_reason=review_result.get('reason', ''),
                video_path=video_path
            )

            if approved:
                approved_count += 1
            else:
                rejected_count += 1
                # 删除未通过的视频
                Path(video_path).unlink(missing_ok=True)

        print(f"\n  📊 审核结果: ✅ {approved_count} | ❌ {rejected_count}")
    else:
        print("\n📦 步骤 3/3: 添加到数据库（跳过审核）...")

        for video_data in downloaded:
            video = video_data['video']
            downloader.add_video_link(
                url=video['url'],
                title=video['title'],
                duration=video_data['duration'],
                keyword=video.get('keyword', 'Unknown'),
                approved=None,
                video_path=video_data['path']
            )

    # 最终统计
    print("\n" + "=" * 80)
    print("✅ 修复完成")
    print("=" * 80)
    print(f"\n📊 统计:")
    print(f"  • 需要修复: {len(missing_videos)} 个")
    print(f"  • 成功下载: {len(downloaded)} 个")
    print(f"  • 下载失败: {len(failed)} 个")

    if ENABLE_AI_REVIEW:
        print(f"  • 审核通过: {approved_count} 个")
        print(f"  • 审核拒绝: {rejected_count} 个")

    if failed:
        print(f"\n⚠️ 下载失败的视频:")
        for item in failed:
            print(f"  - {item['video']['title'][:60]}")
            print(f"    原因: {item['error']}")

    print(f"\n💾 更新后的数据库已保存到: {links_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()
