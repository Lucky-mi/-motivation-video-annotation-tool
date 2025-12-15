#!/usr/bin/env python3
# scripts/review_videos.py
"""
独立的视频审核脚本 (修复版)
✅ 修复 ImportError
✅ 支持 Asyncio 异步调用
✅ 支持 --limit 参数
✅ 支持 --mode physiological
"""
import sys
import asyncio
import argparse
import json
from pathlib import Path
from datetime import datetime

# ================= 🔧 路径修复核心 =================
# 1. 获取项目根目录
project_root = Path(__file__).resolve().parent.parent
# 2. 只把项目根目录加入 path，不要加 backend！
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 3. 通过包名导入 (这是修复 ImportError 的关键)
from backend.content_filter import ContentFilter
from backend.downloader import VideoDownloader # 用于更新数据库状态
# ===================================================

async def process_video(content_filter, video_path, args):
    """处理单个视频的协程"""
    try:
        # 映射命令行参数到 API 参数
        filter_mode = args.mode
        if args.mode == "physiological":
            # 如果是生理模式，内部其实是 auto + 特殊 prompt
            filter_mode = "physiological"
        
        # 异步调用 AI (关键修复)
        review_result = await content_filter.check_video_content(
            str(video_path),
            strict_mode=(args.mode == 'strict'),
            filter_mode=filter_mode
        )
        return review_result
    except Exception as e:
        return {"pass": False, "reason": f"System Error: {e}", "confidence": 0.0}

async def main_async():
    parser = argparse.ArgumentParser(description="审核已下载的视频")
    parser.add_argument(
        "--mode",
        choices=["strict", "standard", "physiological"], # 新增 physiological
        default="standard",
        help="审核模式：physiological(生理需求), strict(严格), standard(标准)"
    )
    parser.add_argument("--limit", type=int, help="限制审核数量 (例如 50)")
    parser.add_argument("--delete-rejected", action="store_true", help="自动删除未通过的视频")
    parser.add_argument("--video-dir", default="data/Youtube_videos", help="视频目录路径")
    parser.add_argument("--update-db", action="store_true", default=True, help="是否更新 youtube_links.json")

    args = parser.parse_args()

    print("=" * 80)
    print("📹 视频补审脚本 (Async Fixed)")
    print("=" * 80)
    print(f"模式: {args.mode}")
    print(f"限制: {args.limit if args.limit else '无'}")
    
    # 检查目录
    video_dir = project_root / args.video_dir
    if not video_dir.exists():
        print(f"❌ 视频目录不存在: {video_dir}")
        return

    # 1. 扫描文件
    all_videos = list(video_dir.glob("*.mp4")) + list(video_dir.glob("*.mkv")) + list(video_dir.glob("*.webm"))
    print(f"📁 扫描到本地视频: {len(all_videos)} 个")

    # 2. (可选) 过滤掉已经审核过的视频
    # 这里为了简单，我们假设只要运行这个脚本就是想重审，或者审漏网之鱼
    # 如果你想只审“未审核”的，需要加载数据库对比。
    # 这里简单处理：直接取前 N 个
    
    target_videos = all_videos
    if args.limit:
        target_videos = all_videos[:args.limit]
    
    print(f"🎯 本次将审核: {len(target_videos)} 个视频")

    # 初始化组件
    print("\n📦 初始化 AI & 数据库...")
    content_filter = ContentFilter()
    downloader = VideoDownloader() # 用来更新 JSON 数据库

    approved_count = 0
    results = []

    print("\n🚀 开始流水线...")
    for idx, video_path in enumerate(target_videos, 1):
        print(f"\n[{idx}/{len(target_videos)}] 正在审核: {video_path.name}")
        
        # 执行审核
        result = await process_video(content_filter, video_path, args)
        
        is_pass = result.get('pass', False)
        icon = "✅" if is_pass else "❌"
        print(f"  {icon} {result.get('reason', '无理由')}")
        
        # 记录统计
        if is_pass: approved_count += 1
        
        # 更新数据库 (youtube_links.json)
        if args.update_db:
            # 我们需要反查 URL，这有点麻烦，但可以用文件名(VideoID)匹配
            # 假设文件名就是 video_id
            video_id = video_path.stem
            # 在数据库里找这个 ID 对应的条目并更新
            # 注意：VideoDownloader 的 update 逻辑通常基于 URL，这里我们尝试遍历匹配
            found = False
            for v in downloader.links_db["videos"]:
                # 尝试匹配路径或ID
                if video_id in v.get("url", "") or video_id in v.get("video_path", ""):
                    v["approved"] = is_pass
                    v["review_reason"] = result.get("reason", "")
                    # 如果有新的元数据字段，也可以存进去
                    if "physiological_type" in result:
                        v["physiological_type"] = result["physiological_type"]
                    found = True
                    break
            
            if found:
                downloader._save_links_database()
                print("  💾 数据库状态已更新")
            else:
                print("  ⚠️ 数据库中未找到此视频记录，仅本地审核")

        # 删除文件逻辑
        if not is_pass and args.delete_rejected:
            try:
                video_path.unlink()
                print("  🗑️ 文件已删除")
            except Exception as e:
                print(f"  ⚠️ 删除失败: {e}")

    print("\n" + "=" * 80)
    print(f"🎉 完成！通过率: {approved_count}/{len(target_videos)}")

def main():
    # 解决 Windows 下 asyncio 的一些兼容性问题
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main_async())

if __name__ == "__main__":
    main()