#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
并发数测试脚本
==============
自动测试不同并发数的稳定性，找到最佳配置
"""
import sys
import os
from pathlib import Path
import time

# 修复 Windows 编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.downloader import VideoDownloader
from backend.content_filter import ContentFilter
import json

def test_concurrency_level(worker_count: int, test_videos: list, strict_mode: bool = True):
    """
    测试指定并发数的稳定性

    Args:
        worker_count: 并发数
        test_videos: 测试视频路径列表
        strict_mode: 是否使用严格模式

    Returns:
        (success, duration, error_msg)
    """
    print(f"\n{'='*60}")
    print(f"🧪 测试并发数: {worker_count}")
    print(f"{'='*60}")

    try:
        content_filter = ContentFilter()

        start_time = time.time()

        print(f"⏱️  开始审核 {len(test_videos)} 个视频...")
        results = content_filter.batch_check(
            test_videos,
            strict_mode=strict_mode,
            max_workers=worker_count
        )

        duration = time.time() - start_time

        # 统计结果
        passed = sum(1 for r in results.values() if r.get("pass", False))
        failed = len(results) - passed

        print(f"\n✅ 测试成功!")
        print(f"   耗时: {duration:.1f} 秒")
        print(f"   平均: {duration/len(test_videos):.1f} 秒/视频")
        print(f"   通过: {passed}/{len(test_videos)}")
        print(f"   失败: {failed}/{len(test_videos)}")

        return True, duration, None

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 测试失败: {error_msg[:200]}")

        # 判断错误类型
        if "10055" in error_msg or "套接字" in error_msg or "buffer space" in error_msg:
            print(f"   ⚠️  检测到套接字资源耗尽")
            return False, 0, "socket_exhaustion"
        elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
            print(f"   ⚠️  检测到 API 速率限制")
            return False, 0, "rate_limit"
        else:
            print(f"   ⚠️  其他错误")
            return False, 0, "other"

def find_optimal_concurrency():
    """自动寻找最佳并发数"""

    print("="*60)
    print("🎯 并发数自动测试工具")
    print("="*60)
    print("\n本工具将自动测试不同并发数，找到最佳配置")
    print("测试方法：使用已下载的视频进行审核测试")
    print()

    # 查找测试视频
    video_dir = Path("data/Youtube_videos")
    test_videos = list(video_dir.glob("*.mp4"))[:5]  # 使用 5 个视频测试

    if len(test_videos) < 3:
        print("❌ 测试视频不足（至少需要 3 个）")
        print(f"   当前只找到 {len(test_videos)} 个视频")
        print(f"\n💡 请先下载一些视频:")
        print(f"   python scripts/run_download_review.py --limit 5 --skip-review")
        return

    test_videos = [str(v) for v in test_videos]

    print(f"✅ 找到 {len(test_videos)} 个测试视频")
    for i, path in enumerate(test_videos, 1):
        print(f"   {i}. {Path(path).name}")

    print(f"\n⏳ 开始测试，请稍候...")

    # 测试配置：从 1 开始，逐步翻倍
    test_levels = [1, 2, 3, 5, 8]
    results = {}

    for worker_count in test_levels:
        success, duration, error = test_concurrency_level(
            worker_count,
            test_videos,
            strict_mode=True
        )

        results[worker_count] = {
            "success": success,
            "duration": duration,
            "error": error
        }

        # 如果失败，停止测试更高的并发
        if not success:
            print(f"\n⚠️  并发数 {worker_count} 失败，停止测试更高并发")
            break

        # 短暂等待，避免触发限制
        if worker_count < test_levels[-1]:
            print(f"\n⏳ 等待 5 秒后继续下一轮测试...")
            time.sleep(5)

    # 分析结果
    print(f"\n{'='*60}")
    print("📊 测试结果总结")
    print(f"{'='*60}")

    successful_levels = [w for w, r in results.items() if r["success"]]

    if not successful_levels:
        print("❌ 所有并发级别都失败了")
        print("\n💡 建议:")
        print("   1. 检查网络连接")
        print("   2. 检查 API 配额")
        print("   3. 重启系统释放资源")
        return

    print(f"\n✅ 成功的并发级别: {successful_levels}")

    # 找到最佳配置
    best_worker = max(successful_levels)
    best_duration = results[best_worker]["duration"]

    print(f"\n🎯 推荐配置:")
    print(f"   AI_REVIEW_WORKERS = {best_worker}")
    print(f"   预期速度: {best_duration/len(test_videos):.1f} 秒/视频")

    # 性能对比
    if 1 in results and results[1]["success"]:
        baseline_duration = results[1]["duration"]
        speedup = baseline_duration / best_duration if best_duration > 0 else 0
        print(f"   速度提升: {speedup:.1f}x (相比单线程)")

    # 详细结果
    print(f"\n📋 详细测试结果:")
    print(f"{'并发数':<10} {'状态':<10} {'总耗时':<15} {'平均耗时':<15} {'错误类型'}")
    print("-" * 70)

    for worker, result in sorted(results.items()):
        status = "✅ 成功" if result["success"] else "❌ 失败"
        duration = f"{result['duration']:.1f}s" if result["success"] else "N/A"
        avg = f"{result['duration']/len(test_videos):.1f}s" if result["success"] else "N/A"
        error = result["error"] or "-"

        print(f"{worker:<10} {status:<10} {duration:<15} {avg:<15} {error}")

    # 生成配置建议
    print(f"\n📝 配置建议:")
    print(f"   修改 config/search_config.py:")
    print(f"   AI_REVIEW_WORKERS = {best_worker}")

    if best_worker == 1:
        print(f"\n   💡 系统资源有限，建议保持单线程")
    elif best_worker <= 3:
        print(f"\n   💡 标准配置，适合日常使用")
    else:
        print(f"\n   💡 高性能配置，适合批量处理")

    print(f"\n{'='*60}")
    print("✅ 测试完成!")
    print(f"{'='*60}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="并发数测试工具")
    parser.add_argument(
        "--test",
        type=int,
        help="测试指定的并发数（不指定则自动测试）"
    )
    parser.add_argument(
        "--videos",
        type=int,
        default=5,
        help="使用多少个视频测试（默认 5）"
    )

    args = parser.parse_args()

    if args.test:
        # 测试指定并发数
        video_dir = Path("data/Youtube_videos")
        test_videos = [str(v) for v in list(video_dir.glob("*.mp4"))[:args.videos]]

        if len(test_videos) < 3:
            print(f"❌ 测试视频不足（至少需要 3 个，找到 {len(test_videos)} 个）")
            return

        success, duration, error = test_concurrency_level(
            args.test,
            test_videos,
            strict_mode=True
        )

        if success:
            print(f"\n✅ 并发数 {args.test} 测试成功，可以使用")
        else:
            print(f"\n❌ 并发数 {args.test} 测试失败，建议降低")
    else:
        # 自动测试
        find_optimal_concurrency()

if __name__ == "__main__":
    main()
