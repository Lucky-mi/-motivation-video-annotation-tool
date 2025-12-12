#!/usr/bin/env python3
"""
简单的视频修复脚本
导出缺失视频的URL，供手动或重新下载使用
"""
import json
from pathlib import Path
from datetime import datetime

def main():
    print("=" * 80)
    print("🔧 视频缺失检查和导出工具")
    print("=" * 80)

    # 加载数据库
    links_file = Path("data/youtube_links.json")
    if not links_file.exists():
        print("❌ youtube_links.json 不存在")
        return

    with open(links_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    videos = data['videos']

    # 分类统计
    approved_with_file = []
    approved_missing_file = []

    for video in videos:
        if video.get('approved') == True:
            video_path = video.get('video_path')
            if video_path and Path(video_path).exists():
                approved_with_file.append(video)
            else:
                approved_missing_file.append(video)

    # 显示统计
    print(f"\n📊 统计信息:")
    print(f"  • 审核通过的视频: {len(approved_with_file) + len(approved_missing_file)} 个")
    print(f"  • 文件完整: {len(approved_with_file)} 个 ✅")
    print(f"  • 文件缺失: {len(approved_missing_file)} 个 ❌")

    if not approved_missing_file:
        print("\n✅ 所有审核通过的视频文件都存在！")
        return

    # 显示缺失的视频
    print(f"\n⚠️ 文件缺失的视频列表:\n")
    for idx, video in enumerate(approved_missing_file, 1):
        print(f"{idx}. {video['title']}")
        print(f"   URL: {video['url']}")
        print(f"   关键词: {video.get('keyword', 'Unknown')}")
        video_path = video.get('video_path')
        if video_path is None:
            print(f"   问题: 路径为空")
        else:
            print(f"   问题: 文件不存在 ({video_path})")
        print()

    # 导出URL列表
    export_data = []
    for video in approved_missing_file:
        export_data.append({
            'url': video['url'],
            'title': video['title'],
            'keyword': video.get('keyword', 'Unknown'),
            'duration': video.get('duration', 0),
            'reason': 'path is None' if video.get('video_path') is None else 'file not found'
        })

    # 保存导出文件
    export_file = Path(f"data/missing_videos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(export_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"💾 缺失视频信息已导出到: {export_file}")

    # 提供修复选项
    print("\n" + "=" * 80)
    print("🔧 修复选项:")
    print("=" * 80)
    print("\n1️⃣ 从数据库中删除这些记录（清理数据库）")
    print("2️⃣ 保留记录，稍后手动下载")
    print("3️⃣ 取消，不做任何操作")

    choice = input("\n请选择 (1/2/3): ").strip()

    if choice == '1':
        # 删除缺失记录
        print("\n正在从数据库中删除缺失记录...")

        urls_to_remove = {v['url'] for v in approved_missing_file}
        original_count = len(data['videos'])

        data['videos'] = [v for v in data['videos'] if v['url'] not in urls_to_remove]

        # 更新元数据
        data['metadata']['total_count'] = len(data['videos'])
        data['metadata']['approved_count'] = sum(1 for v in data['videos'] if v.get('approved') == True)
        data['metadata']['rejected_count'] = sum(1 for v in data['videos'] if v.get('approved') == False)
        data['metadata']['last_updated'] = datetime.now().isoformat()

        # 备份原文件
        backup_file = Path(f"data/youtube_links_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump({'videos': data['videos']}, f, ensure_ascii=False, indent=2)
        print(f"  💾 原数据库已备份到: {backup_file}")

        # 保存更新后的数据库
        with open(links_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        removed_count = original_count - len(data['videos'])
        print(f"  ✅ 已删除 {removed_count} 条记录")
        print(f"  💾 数据库已更新: {links_file}")

        print(f"\n💡 提示:")
        print(f"  • 缺失视频的URL已保存到: {export_file}")
        print(f"  • 你可以使用这些URL重新下载视频")
        print(f"  • 或者运行新的搜索找到更多视频")

    elif choice == '2':
        print(f"\n✅ 已保留所有记录")
        print(f"💾 缺失视频信息已保存到: {export_file}")
        print(f"\n💡 稍后你可以:")
        print(f"  1. 手动访问这些URL下载视频")
        print(f"  2. 或者运行: python scripts/run_download_review.py")

    else:
        print("\n❌ 已取消，未做任何修改")

    print("\n" + "=" * 80)
    print("🎉 完成!")
    print("=" * 80)

if __name__ == "__main__":
    main()
