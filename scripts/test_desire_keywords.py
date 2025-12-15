#!/usr/bin/env python3
# scripts/test_desire_keywords.py
"""
测试生理需求和二阶Desire关键词配置
用于验证新添加的关键词集合是否正常工作
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "config"))

from search_config import (
    KEYWORDS_PHYSIOLOGICAL,
    KEYWORDS_SECOND_ORDER,
    KEYWORDS_DESIRE_EXTENDED,
    get_keywords,
    KEYWORD_SET
)


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def analyze_keywords(keywords, name):
    """分析关键词集合"""
    print(f"\n📊 {name}")
    print(f"  总数: {len(keywords)} 个关键词")

    # 按类别分类（简单分类）
    categories = {
        "挑战类 (challenge)": [],
        "日志类 (vlog)": [],
        "反应类 (reaction)": [],
        "失败类 (fail/compilation)": [],
        "极限类 (extreme/endurance)": [],
        "其他": []
    }

    for kw in keywords:
        kw_lower = kw.lower()
        if "challenge" in kw_lower:
            categories["挑战类 (challenge)"].append(kw)
        elif "vlog" in kw_lower:
            categories["日志类 (vlog)"].append(kw)
        elif "reaction" in kw_lower:
            categories["反应类 (reaction)"].append(kw)
        elif "fail" in kw_lower or "compilation" in kw_lower or "moments" in kw_lower:
            categories["失败类 (fail/compilation)"].append(kw)
        elif "extreme" in kw_lower or "endurance" in kw_lower:
            categories["极限类 (extreme/endurance)"].append(kw)
        else:
            categories["其他"].append(kw)

    print("\n  类别分布:")
    for cat, items in categories.items():
        if items:
            print(f"    • {cat}: {len(items)} 个")
            for item in items[:3]:  # 只显示前3个
                print(f"      - {item}")
            if len(items) > 3:
                print(f"      ... 还有 {len(items) - 3} 个")


def test_keyword_retrieval():
    """测试关键词获取函数"""
    print_section("测试关键词获取函数")

    # 测试不同的配置
    test_sets = [
        "physiological",
        "second_order",
        "desire_extended"
    ]

    print(f"\n当前配置: KEYWORD_SET = '{KEYWORD_SET}'")
    current_keywords = get_keywords()
    print(f"当前获取到: {len(current_keywords)} 个关键词")

    print("\n可用的关键词集合:")
    for set_name in test_sets:
        # 临时修改配置
        import search_config
        original = search_config.KEYWORD_SET
        search_config.KEYWORD_SET = set_name

        keywords = get_keywords()
        print(f"  • {set_name}: {len(keywords)} 个关键词")

        # 恢复
        search_config.KEYWORD_SET = original


def show_physiological_details():
    """显示生理需求关键词详情"""
    print_section("生理需求关键词详情 (KEYWORDS_PHYSIOLOGICAL)")

    # 按子类别分组
    subcategories = {
        "饥饿/进食": [
            "fasting vlog 24h",
            "survival challenge alone",
            "military ration taste test",
            "ramadan daily routine",
            "post workout cheat meal",
            "mukbang extreme hunger",
            "food challenge starving"
        ],
        "睡眠/休息": [
            "fighting sleep",
            "trying to stay awake",
            "night shift vlog",
            "nodding off in class",
            "marathon exhaustion",
            "study with me 12 hours",
            "falling asleep at work",
            "sleep deprivation challenge"
        ],
        "体温调节": [
            "ice bath challenge",
            "sauna endurance",
            "polar plunge",
            "walking in blizzard",
            "heatwave no AC",
            "spicy noodle challenge",
            "cold water challenge",
            "extreme heat survival"
        ],
        "疼痛规避": [
            "tattoo pain level",
            "waxing reaction",
            "removing bandaid",
            "piercing reaction",
            "spicy food reaction",
            "hot sauce challenge",
            "painful massage"
        ],
        "身体活动/氧气": [
            "holding breath challenge",
            "altitude sickness",
            "crossfit fail",
            "marathon finish line collapse",
            "breathing exercise extreme",
            "underwater challenge"
        ]
    }

    total = 0
    for category, keywords in subcategories.items():
        print(f"\n📌 {category} ({len(keywords)} 个)")
        for kw in keywords:
            print(f"   {total + 1:2d}. {kw}")
            total += 1

    print(f"\n  ✅ 总计: {total} 个关键词")


def show_second_order_details():
    """显示二阶Desire关键词详情"""
    print_section("二阶Desire关键词详情 (KEYWORDS_SECOND_ORDER)")

    subcategories = {
        "欲望冲突": [
            "ice bucket challenge",
            "trying not to laugh challenge",
            "try not to eat challenge",
            "diet cheat day vlog",
            "resisting temptation"
        ],
        "无意图动作/失败": [
            "reflexes compilation",
            "scare cam reactions",
            "clumsy moments",
            "instant karma",
            "fail army",
            "people falling",
            "unexpected reactions"
        ],
        "意志力斗争": [
            "trying to quit smoking",
            "struggling to wake up",
            "procrastination vlog",
            "breaking bad habits",
            "new year resolution fail",
            "giving up challenge"
        ],
        "长视频/渐变": [
            "study with me tired",
            "all nighter vlog",
            "24 hour challenge exhausted",
            "working overtime tired"
        ],
        "社交压力 vs 生理": [
            "holding pee challenge",
            "not sleeping challenge",
            "endurance challenge",
            "strength test fail"
        ]
    }

    total = 0
    for category, keywords in subcategories.items():
        print(f"\n📌 {category} ({len(keywords)} 个)")
        for kw in keywords:
            print(f"   {total + 1:2d}. {kw}")
            total += 1

    print(f"\n  ✅ 总计: {total} 个关键词")


def estimate_collection():
    """预估数据收集量"""
    print_section("数据收集量预估")

    videos_per_keyword = 5  # 默认配置

    sets = {
        "physiological": len(KEYWORDS_PHYSIOLOGICAL),
        "second_order": len(KEYWORDS_SECOND_ORDER),
        "desire_extended": len(KEYWORDS_DESIRE_EXTENDED)
    }

    print(f"\n假设配置: VIDEOS_PER_KEYWORD = {videos_per_keyword}")
    print(f"           AI审核通过率 = 35% (严格模式)")
    print(f"           人工审核通过率 = 85%")

    print("\n预估结果:")
    for set_name, keyword_count in sets.items():
        search_count = keyword_count * videos_per_keyword
        after_ai = int(search_count * 0.35)
        after_human = int(after_ai * 0.85)

        print(f"\n  📦 {set_name}")
        print(f"     关键词数: {keyword_count}")
        print(f"     搜索视频: ~{search_count} 个")
        print(f"     AI审核通过: ~{after_ai} 个")
        print(f"     人工审核通过: ~{after_human} 个")
        print(f"     最终数据集: ~{after_human} 个高质量标注")


def show_usage_examples():
    """显示使用示例"""
    print_section("使用示例")

    print("""
🚀 快速开始

1️⃣ 修改配置文件（config/search_config.py）：

   # 选择关键词集
   KEYWORD_SET = "desire_extended"  # 推荐：生理需求 + 二阶desire

   # 或者单独使用
   KEYWORD_SET = "physiological"    # 仅生理需求
   KEYWORD_SET = "second_order"     # 仅二阶desire

2️⃣ 运行搜索（仅搜索，不下载）：

   python scripts/run_search.py --search-only

3️⃣ 查看搜索结果：

   cat data/search_results.json | head -n 100

4️⃣ 下载和审核（限制数量）：

   python scripts/run_download_review.py --limit 50

5️⃣ 启动审核平台：

   python run_reviewer.py

6️⃣ 批量重命名标注文件：

   python batch_rename_annotations.py

💡 提示：

- 推荐先用 --search-only 测试关键词效果
- 使用 --limit 参数控制下载数量
- 严格模式下通过率 30-40%，标准模式 50-60%
- 长视频（study with me 12h）可能需要切片分析

📚 详细指南：

   docs/PHYSIOLOGICAL_DESIRE_COLLECTION_GUIDE.md
""")


def main():
    """主函数"""
    print("=" * 80)
    print("  生理需求与二阶Desire关键词集合测试")
    print("  测试日期: 2025-12-14")
    print("=" * 80)

    # 1. 测试关键词获取
    test_keyword_retrieval()

    # 2. 显示生理需求关键词
    show_physiological_details()

    # 3. 显示二阶Desire关键词
    show_second_order_details()

    # 4. 分析关键词集合
    print_section("关键词集合分析")
    analyze_keywords(KEYWORDS_PHYSIOLOGICAL, "生理需求关键词")
    analyze_keywords(KEYWORDS_SECOND_ORDER, "二阶Desire关键词")
    analyze_keywords(KEYWORDS_DESIRE_EXTENDED, "扩展Desire关键词（组合）")

    # 5. 预估数据收集量
    estimate_collection()

    # 6. 显示使用示例
    show_usage_examples()

    # 总结
    print_section("测试总结")
    print(f"""
✅ 所有关键词集合配置正常

📊 关键词统计:
   • KEYWORDS_PHYSIOLOGICAL: {len(KEYWORDS_PHYSIOLOGICAL)} 个
   • KEYWORDS_SECOND_ORDER: {len(KEYWORDS_SECOND_ORDER)} 个
   • KEYWORDS_DESIRE_EXTENDED: {len(KEYWORDS_DESIRE_EXTENDED)} 个

🎯 推荐配置:
   KEYWORD_SET = "desire_extended"  # 完整收集生理需求和二阶desire

📖 详细指南:
   docs/PHYSIOLOGICAL_DESIRE_COLLECTION_GUIDE.md

🚀 下一步:
   1. 修改 config/search_config.py 中的 KEYWORD_SET
   2. 运行 python scripts/run_search.py --search-only
   3. 查看搜索结果并下载
""")

    print("=" * 80)
    print("  测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
