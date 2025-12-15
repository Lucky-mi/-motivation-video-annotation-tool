#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新审核 ai_check_errors 目录中的视频
审核通过的视频会被移动到 Youtube_videos 目录
"""
import sys
from pathlib import Path
import shutil

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 显式加载 .env 文件
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import argparse
from backend.content_filter import ContentFilter
from backend.downloader import VideoDownloader
from config.search_config import STRICT_MODE, FILTER_MODE, AUTO_DELETE_REJECTED, AI_REVIEW_WORKERS

def main():
    parser = argparse.ArgumentParser(description="重新审核失败的视频")
    parser.add_argument(
        "--max-count",
        type=int,
        default=None,
        help="最多审核多少个视频（留空审核全部）"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("🔄 重新审核失败视频工具")
    print("=" * 80)

    # 目录配置
    error_dir = Path("data/ai_check_errors")
    success_dir = Path("data/Youtube_videos")
    error_dir.mkdir(parents=True, exist_ok=True)
    success_dir.mkdir(parents=True, exist_ok=True)

    # 查找待审核视频
    video_files = list(error_dir.glob("*.mp4"))

    if not video_files:
        print("✅ ai_check_errors 目录中没有待审核的视频")
        return

    # 限制数量
    if args.max_count:
        video_files = video_files[:args.max_count]

    print(f"\n📂 找到 {len(video_files)} 个待审核视频")
    print(f"   错误目录: {error_dir}")
    print(f"   目标目录: {success_dir}")

    # 确认继续
    response = input(f"\n确认重新审核? (y/n): ")
    if response.lower() != 'y':
        print("❌ 已取消")
        return

    # 初始化组件
    print("\n📦 初始化AI审核组件...")
    content_filter = ContentFilter()
    downloader = VideoDownloader()

    # 批量审核
    print(f"\n🚀 开始审核 (filter_mode: {FILTER_MODE})...")
    print("=" * 80)

    video_paths = [str(vf) for vf in video_files]

    try:
        review_results = content_filter.batch_check(
            video_paths,
            strict_mode=STRICT_MODE,
            max_workers=AI_REVIEW_WORKERS,
            filter_mode=FILTER_MODE
        )
    except Exception as e:
        print(f"❌ 批量审核失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 处理结果
    approved_count = 0
    rejected_count = 0
    error_count = 0

    print(f"\n📊 处理审核结果...")
    print("=" * 80)

    for video_path in video_paths:
        video_file = Path(video_path)
        result = review_results.get(video_path, {"pass": False, "reason": "审核失败"})

        # 检查错误
        is_parsing_error = result.get('parsing_error', False)
        is_system_error = "error" in result or "异常" in result.get("reason", "")

        if is_parsing_error or is_system_error:
            # 仍然出错，保留在错误文件夹
            error_count += 1
            error_type = "AI解析异常" if is_parsing_error else "系统错误"
            print(f"⚠️ {error_type}: {video_file.name} - 保留在错误文件夹")
            continue

        approved = result.get('pass', False)
        reason = result.get('reason', '')
        category = result.get('category', 'N/A')

        if approved:
            # 审核通过 -> 移动到成功文件夹
            try:
                target_path = success_dir / video_file.name
                shutil.move(str(video_file), str(target_path))
                approved_count += 1
                print(f"✅ 通过: {video_file.name}")
                print(f"   ↳ 类别: {category}, 理由: {reason[:60]}")
                print(f"   ↳ 已移至: {target_path.name}")

                # 🔧 更新数据库记录
                downloader.update_video_by_path(
                    old_path=str(video_path),
                    new_path=str(target_path),
                    approved=True,
                    review_reason=reason
                )
            except Exception as move_err:
                print(f"❌ 移动文件失败: {video_file.name} - {move_err}")
        else:
            # 审核拒绝
            rejected_count += 1
            print(f"❌ 拒绝: {video_file.name}")
            print(f"   ↳ 理由: {reason[:80]}")

            if AUTO_DELETE_REJECTED:
                # 删除被拒绝的视频
                try:
                    video_file.unlink()
                    print(f"   ↳ 已删除")

                    # 🔧 更新数据库：标记为拒绝
                    downloader.update_video_by_path(
                        old_path=str(video_path),
                        new_path=None,  # 文件已删除
                        approved=False,
                        review_reason=reason
                    )
                except Exception as del_err:
                    print(f"   ↳ 删除失败: {del_err}")
            else:
                print(f"   ↳ 保留在错误文件夹")

                # 🔧 更新数据库：标记为拒绝但保留文件
                downloader.update_video_by_path(
                    old_path=str(video_path),
                    new_path=str(video_path),  # 路径不变
                    approved=False,
                    review_reason=reason
                )

    # 统计
    print(f"\n{'='*80}")
    print(f"✅ 重新审核完成")
    print(f"{'='*80}")
    print(f"✅ 通过: {approved_count} (已移至 Youtube_videos)")
    print(f"❌ 拒绝: {rejected_count}")
    print(f"⚠️ 仍有错误: {error_count} (保留在 ai_check_errors)")

    remaining = list(error_dir.glob("*.mp4"))
    if remaining:
        print(f"\n💡 ai_check_errors 中还有 {len(remaining)} 个视频")
        print(f"   可能需要检查AI配置或手动审核")
    else:
        print(f"\n🎉 ai_check_errors 目录已清空!")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
