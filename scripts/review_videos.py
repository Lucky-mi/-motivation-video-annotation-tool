#!/usr/bin/env python3
# scripts/review_videos.py
"""
独立的视频审核脚本
直接审核 data/Youtube_videos/ 目录下已下载的视频
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 直接导入，避免通过 backend/__init__.py
sys.path.insert(0, str(project_root / "backend"))
from content_filter import ContentFilter


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="审核已下载的视频")
    parser.add_argument(
        "--mode",
        choices=["strict", "standard"],
        default="standard",
        help="审核模式：strict(严格) 或 standard(标准)"
    )
    parser.add_argument(
        "--delete-rejected",
        action="store_true",
        help="自动删除未通过的视频"
    )
    parser.add_argument(
        "--video-dir",
        default="data/Youtube_videos",
        help="视频目录路径"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("📹 视频审核脚本")
    print("=" * 80)
    print(f"审核模式: {'严格' if args.mode == 'strict' else '标准'}")
    print(f"视频目录: {args.video_dir}")
    print(f"自动删除未通过: {'是' if args.delete_rejected else '否'}")
    print("=" * 80)

    # 检查目录
    video_dir = Path(args.video_dir)
    if not video_dir.exists():
        print(f"❌ 视频目录不存在: {video_dir}")
        return

    # 获取所有视频文件
    video_files = list(video_dir.glob("*.mp4"))
    if not video_files:
        print(f"❌ 目录中没有找到视频文件: {video_dir}")
        return

    print(f"\n找到 {len(video_files)} 个视频文件")

    # 初始化审核器
    print("\n📦 初始化AI审核器...")
    content_filter = ContentFilter()
    strict_mode = (args.mode == "strict")

    # 逐个审核
    results = []
    approved_count = 0
    rejected_count = 0
    failed_count = 0

    print("\n" + "=" * 80)
    print("🤖 开始AI审核")
    print("=" * 80)

    for idx, video_path in enumerate(video_files, 1):
        print(f"\n[{idx}/{len(video_files)}] {video_path.name}")

        try:
            # AI审核
            review_result = content_filter.check_video_content(
                str(video_path),
                strict_mode=strict_mode
            )

            approved = review_result.get('pass', False)

            # 记录结果
            result = {
                'video_path': str(video_path),
                'video_name': video_path.name,
                'approved': approved,
                'review_result': review_result,
                'reviewed_time': datetime.now().isoformat()
            }
            results.append(result)

            # 显示结果
            if approved:
                approved_count += 1
                print(f"  ✅ 通过 | {review_result.get('reason', '')}")
                print(f"     置信度: {review_result.get('confidence', 0):.2f}")
                print(f"     分析价值: {review_result.get('分析价值', '')}")
            else:
                rejected_count += 1
                print(f"  ❌ 拒绝 | {review_result.get('reason', '')}")

                # 删除未通过的视频
                if args.delete_rejected:
                    video_path.unlink()
                    print("  🗑️ 已删除")

        except Exception as e:
            failed_count += 1
            print(f"  ❌ 审核失败: {e}")
            results.append({
                'video_path': str(video_path),
                'video_name': video_path.name,
                'approved': None,
                'error': str(e),
                'reviewed_time': datetime.now().isoformat()
            })

    # 保存审核报告
    print("\n" + "=" * 80)
    print("💾 保存审核报告")
    print("=" * 80)

    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)

    report_file = report_dir / f"review_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    report = {
        'reviewed_time': datetime.now().isoformat(),
        'mode': args.mode,
        'total_videos': len(video_files),
        'approved': approved_count,
        'rejected': rejected_count,
        'failed': failed_count,
        'results': results
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"✅ 报告已保存: {report_file}")

    # 统计
    print("\n" + "=" * 80)
    print("📊 审核统计")
    print("=" * 80)
    print(f"总视频数: {len(video_files)}")

    total_reviewed = approved_count + rejected_count
    if total_reviewed > 0:
        print(f"通过: {approved_count} ({approved_count/total_reviewed*100:.1f}%)")
        print(f"拒绝: {rejected_count} ({rejected_count/total_reviewed*100:.1f}%)")

    print(f"失败: {failed_count}")

    # 按类别统计
    if approved_count > 0:
        print("\n📈 通过视频的分类统计:")
        categories = {}
        for result in results:
            if result.get('approved'):
                category = result['review_result'].get('类别', '未知')
                categories[category] = categories.get(category, 0) + 1

        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}个")

    print("\n" + "=" * 80)
    print("🎉 审核完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()
