# config/search_config.py
"""
YouTube搜索和审核配置
可以在这里轻松调整参数
"""

# ==================== 搜索配置 ====================

# 选择要使用的关键词集合（可以修改这里来改变搜索数量）
# 基础选项: "minimal", "standard", "extensive", "full", "tv_drama", "movie_clips", "documentary", "mega"
# 优化选项: "real_optimized" (推荐!), "film_focused", "hybrid_best"
# 生理需求与二阶Desire: "physiological" (仅生理), "second_order" (仅二阶), "desire_extended" (推荐，全部)
KEYWORD_SET = "desire_extended"  # 推荐使用优化关键词，预期通过率 50-60%

# 自定义关键词（如果不为None，则使用自定义关键词而不是预设）
CUSTOM_KEYWORDS = None  # 例如: ["psychology video", "social behavior"]

# 每个关键词搜索的视频数量（增加这个数字可以得到更多候选视频）
# 建议值: 3-5 (避免被限制), 10+ (快速收集但风险高)
VIDEOS_PER_KEYWORD = 5  # 推荐：保守配置，避免触发反爬虫

# 视频时长过滤（秒）
MIN_DURATION = 30   # 最短30秒
MAX_DURATION = 300  # 最长5分钟

# ==================== 搜索重试策略配置 ====================

# 搜索重试次数配置
# 🎯 说明：当单次搜索无法找到足够的新视频时，会自动扩大搜索范围并重试
#
# 场景分析：
# 1. 新关键词（历史搜索少）：通常 1-2 次就能找到足够视频
# 2. 热门关键词（历史搜索多）：可能需要 5-8 次才能找到足够新视频
# 3. 已完全搜索的关键词：即使 10 次也可能找不到新视频
#
# 💡 建议配置：
# - 轻度使用：MAX_SEARCH_ATTEMPTS = 5（默认，平衡速度和覆盖）
# - 中度使用：MAX_SEARCH_ATTEMPTS = 8（推荐，确保找到足够视频）
# - 重度使用：MAX_SEARCH_ATTEMPTS = 10-15（深度挖掘，但耗时较长）
#
MAX_SEARCH_ATTEMPTS = 8  # 最大搜索尝试次数（从 5 增加到 8）

# 搜索范围倍数配置
# 🎯 说明：每次搜索会请求 "limit × SEARCH_MULTIPLIER_INITIAL" 个结果
#
# 计算示例（假设 VIDEOS_PER_KEYWORD = 5）：
#   第1次: 5 × 3 = 15 个结果
#   第2次: 5 × 5 = 25 个结果
#   第3次: 5 × 7 = 35 个结果
#   第4次: 5 × 9 = 45 个结果
#   ...
#
# 💡 建议配置：
# - 保守策略：INITIAL=3, INCREMENT=2（默认，逐步扩大）
# - 激进策略：INITIAL=5, INCREMENT=3（快速扩大，适合已搜索多的关键词）
# - 超激进：INITIAL=10, INCREMENT=5（快速深度搜索，可能触发限制）
#
SEARCH_MULTIPLIER_INITIAL = 3  # 初始搜索倍数
SEARCH_MULTIPLIER_INCREMENT = 2  # 每次失败后增加的倍数

# ==================== AI审核配置 ====================

# 是否启用AI审核
ENABLE_AI_REVIEW = True

# 审核模式（True=严格模式，False=标准模式）- 仅用于 standard 模式
STRICT_MODE = True

# 筛选模式（Filter Mode）
# - "standard": 标准社交互动审核（适用于 KEYWORDS_FULL 等社交互动关键词）
# - "strict": 严格社交互动审核（更高标准，通过率更低）
# - "physiological_desire": 生理需求和二阶desire审核（推荐用于 KEYWORDS_DESIRE_EXTENDED）
#
# 💡 使用建议：
#   - 当使用 KEYWORDS_DESIRE_EXTENDED / KEYWORDS_PHYSIOLOGICAL / KEYWORDS_SECOND_ORDER 时：
#     设置 FILTER_MODE = "physiological_desire"
#   - 当使用 KEYWORDS_FULL / KEYWORDS_REAL_OPTIMIZED 等社交互动关键词时：
#     设置 FILTER_MODE = "standard" 或 "strict"
#
FILTER_MODE = "physiological_desire"  # 选项: "standard", "strict", "physiological_desire"

# 审核失败的视频是否自动删除
AUTO_DELETE_REJECTED = True

# AI审核并发数（同时审核的视频数量）
#
# 🎯 渐进式并发配置建议（从低到高逐步尝试）：
#
# 阶段 1 - 保守模式（推荐新手/调试）：
#   AI_REVIEW_WORKERS = 1
#   优点: 最稳定，资源占用最低，适合调试
#   缺点: 速度较慢（每个视频 30-60 秒）
#   适用: Windows 系统初次使用，或遇到套接字错误时
#
# 阶段 2 - 标准模式（推荐日常使用）：
#   AI_REVIEW_WORKERS = 2-3
#   优点: 速度提升 2-3 倍，资源占用可控
#   缺点: 可能偶尔出现套接字资源不足
#   适用: Windows 系统稳定运行后，网络良好
#   注意: 需要定期监控，如果出错降回 1
#
# 阶段 3 - 高速模式（推荐高配机器）：
#   AI_REVIEW_WORKERS = 5-8
#   优点: 速度快，批量处理效率高
#   缺点: 资源占用高，Windows 上容易出错
#   适用: Linux/Mac 系统，或 Windows 高配机器 + 稳定网络
#   注意: 可能触发 Google API 速率限制
#
# 阶段 4 - 极速模式（仅限高级用户）：
#   AI_REVIEW_WORKERS = 10+
#   优点: 极快的处理速度
#   缺点: 极易触发限制，需要代理池和 API 配额管理
#   适用: 专业部署环境，配合代理轮换和多账号
#
# 💡 使用建议：
# 1. 从 1 开始测试，确保能稳定运行 10+ 个视频
# 2. 逐步提高到 2-3，观察是否有错误
# 3. 如果出现 "WinError 10055" 或 "套接字"错误，立即降回 1
# 4. Linux/Mac 用户可以直接从 3 开始
# 5. 使用代理可以提高稳定性，允许更高并发
#
AI_REVIEW_WORKERS = 5  # 当前配置：保守模式（修改此值来调整并发）

# ==================== 关键词预设 ====================

# 最小集合（6个关键词，快速测试）
# 重点：真实行为展现，非科普讲解
KEYWORDS_MINIMAL = [
    "people arguing",
    "emotional reaction",
    "surprise moment",
    "friends talking",
    "family conversation",
    "couple disagreement"
]

# 标准集合（12个关键词，平衡速度和覆盖）
# 重点：日常互动场景，情感真实展现
KEYWORDS_STANDARD = [
    # 冲突与争执（真实情感爆发）
    "people arguing",
    "couple fight",
    "family argument",

    # 强烈情感表达
    "emotional reaction",
    "crying moment",
    "surprise reaction",

    # 日常对话互动
    "friends talking",
    "deep conversation",
    "awkward moment",

    # 复杂情感关系
    "jealousy moment",
    "betrayal reaction",
    "heartbreak moment"
]

# 扩展集合（24个关键词，更全面）
# 重点：各种真实人际互动场景
KEYWORDS_EXTENSIVE = [
    # 冲突争执（6个）
    "people arguing",
    "couple fight",
    "family argument",
    "friends conflict",
    "heated debate",
    "confrontation moment",

    # 情感爆发（6个）
    "emotional reaction",
    "crying moment",
    "surprise reaction",
    "angry outburst",
    "emotional breakdown",
    "frustration moment",

    # 日常互动（6个）
    "friends talking",
    "deep conversation",
    "awkward moment",
    "embarrassing situation",
    "uncomfortable silence",
    "tension moment",

    # 复杂关系（6个）
    "jealousy moment",
    "betrayal reaction",
    "heartbreak moment",
    "breakup scene",
    "apology moment",
    "reconciliation scene"
]

# 完整集合（36个关键词，全面覆盖）
# 重点：全方位真实人类行为和情感展现
KEYWORDS_FULL = [
    # 冲突争执场景（9个）
    "people arguing",
    "couple fight",
    "family argument",
    "friends conflict",
    "heated debate",
    "confrontation moment",
    "verbal fight",
    "workplace conflict",
    "neighbor dispute",

    # 情感表达爆发（9个）
    "emotional reaction",
    "crying moment",
    "surprise reaction",
    "angry outburst",
    "emotional breakdown",
    "frustration moment",
    "panic attack",
    "laughter moment",
    "scared reaction",

    # 日常对话互动（9个）
    "friends talking",
    "deep conversation",
    "awkward moment",
    "embarrassing situation",
    "uncomfortable silence",
    "tension moment",
    "gossip moment",
    "secret revealed",
    "confession moment",

    # 复杂人际关系（9个）
    "jealousy moment",
    "betrayal reaction",
    "heartbreak moment",
    "breakup scene",
    "apology moment",
    "reconciliation scene",
    "romantic proposal",
    "first date awkward",
    "relationship drama"
]

# 电视剧与影视片段集合（新增！）⭐
# 重点：电视剧中的真实行为展现片段
KEYWORDS_TV_DRAMA = [
    # 冲突争吵（5个）
    "tv show fight scene",
    "drama argument scene",
    "tv series conflict scene",
    "drama characters arguing",
    "tv show confrontation",

    # 情感爆发（5个）
    "tv series crying scene",
    "drama emotional breakdown",
    "tv show angry scene",
    "drama shocked reaction",
    "tv series betrayal scene",

    # 对话互动（5个）
    "tv show conversation scene",
    "drama dialogue scene",
    "tv series confession scene",
    "drama secret revealed",
    "tv show awkward moment",

    # 关系场景（5个）
    "tv series breakup scene",
    "drama romantic scene",
    "tv show jealousy scene",
    "drama apology scene",
    "tv series reunion scene",

    # 特定剧集类型（5个）
    "crime drama interrogation scene",
    "medical drama emergency scene",
    "family drama dinner scene",
    "romantic drama kiss scene",
    "thriller drama tense scene"
]

# 电影片段集合（精选场景）
# 重点：电影中的真实行为和情感展现
KEYWORDS_MOVIE_CLIPS = [
    # 情感场景（5个）
    "movie fight scene",
    "film crying scene",
    "movie argument scene",
    "film emotional scene",
    "movie angry scene",

    # 对话互动（5个）
    "movie conversation scene",
    "film dialogue scene",
    "movie confession scene",
    "film confrontation scene",
    "movie awkward scene",

    # 关系场景（5个）
    "movie breakup scene",
    "film romantic scene",
    "movie betrayal scene",
    "film reunion scene",
    "movie proposal scene"
]

# 纪录片与真实场景（新增）
# 重点：真实人类行为记录
KEYWORDS_DOCUMENTARY = [
    "real people arguing",
    "real life conflict",
    "real emotional moment",
    "candid reaction",
    "real couple fight",
    "real family moment",
    "street interview emotional",
    "real life drama",
    "caught on camera emotional",
    "real confrontation moment"
]

# 综合超大集合（推荐用于大规模采集）
KEYWORDS_MEGA = (
    KEYWORDS_FULL +
    KEYWORDS_TV_DRAMA +
    KEYWORDS_MOVIE_CLIPS +
    KEYWORDS_DOCUMENTARY
)

# ==================== 优化关键词集 (2025-11-25) ====================
# 重点：避免 reaction 视频、硬字幕、动画，提高审核通过率

# 真实场景优化版（推荐！预期通过率 50-60%）
KEYWORDS_REAL_OPTIMIZED = [
    # 监控摄像头类（无字幕，真实场景）
    "security camera fight",
    "caught on camera argument",
    "dash cam road rage",
    "cctv footage confrontation",

    # 公共冲突（真实性高，行为明显）
    "public freakout real",
    "karen freakout caught",
    "street confrontation real",
    "restaurant argument caught",

    # 真实情感场景（避免 "reaction" 词）
    "proposal caught on camera",
    "surprise reunion soldier",
    "emotional reunion real",
    "breakup caught on video",

    # 电视真人秀（质量稳定）
    "reality show argument",
    "real housewives fight",
    "couples therapy session",

    # 新闻/纪录片镜头
    "confrontation footage",
    "altercation caught on tape",
    "incident caught on camera"
]

# 电影/剧集专注版（稳定质量，较少字幕）
KEYWORDS_FILM_FOCUSED = [
    # 电影情感场景
    "movie argument scene",
    "film emotional breakdown",
    "cinema fight scene",
    "movie couple fight",

    # 电视剧冲突
    "tv show argument",
    "drama confrontation scene",
    "tv series fight",
    "drama emotional scene",

    # 特定类型剧集
    "crime drama interrogation",
    "medical drama emergency",
    "family drama conflict",
    "thriller confrontation",

    # 经典剧集
    "Breaking Bad scene",
    "Game of Thrones scene",
    "The Office scene",
    "Friends scene"
]

# 混合最优策略（平衡真实与质量）
KEYWORDS_HYBRID_BEST = [
    # 真实场景 (40%)
    "caught on camera fight",
    "security footage argument",
    "public argument real",
    "dash cam confrontation",
    "karen freakout",
    "street fight caught",

    # 电视剧/电影 (40%)
    "tv show argument scene",
    "movie fight scene",
    "drama emotional scene",
    "cinema confrontation",
    "tv series conflict",
    "film breakdown scene",

    # 真人秀/纪录片 (20%)
    "reality show fight",
    "Kitchen Nightmares scene",
    "What Would You Do"
]

# 综合超大集合（推荐用于大规模采集）
KEYWORDS_MEGA = (
    KEYWORDS_FULL +
    KEYWORDS_TV_DRAMA +
    KEYWORDS_MOVIE_CLIPS +
    KEYWORDS_DOCUMENTARY
)

# ==================== 生理需求与二阶Desire关键词 (2025-12-14) ====================
# 🎯 目标：收集生理需求（饥饿、睡眠、体温、疼痛）和二阶desire（欲望冲突）的视频
# 策略：搜索情境化关键词，而非直接搜索欲望本身

# 生理需求关键词集（Physiological Desires）
KEYWORDS_PHYSIOLOGICAL = [
    # 饥饿/进食（Hunger/Eating）
    # 视觉特征：眼神呆滞、吞咽口水、进食速度极快、对食物凝视
    "fasting vlog 24h",
    "survival challenge alone",
    "military ration taste test",
    "ramadan daily routine",
    "post workout cheat meal",
    "mukbang extreme hunger",
    "food challenge starving",

    # 睡眠/休息（Sleep/Rest）
    # 视觉特征：头部下垂、频繁眨眼、打哈欠、揉眼睛
    "fighting sleep",
    "trying to stay awake",
    "night shift vlog",
    "nodding off in class",
    "marathon exhaustion",
    "study with me 12 hours",
    "falling asleep at work",
    "sleep deprivation challenge",

    # 体温调节/舒适（Temperature/Comfort）
    # 视觉特征：颤抖、大量出汗、皮肤发红、蜷缩身体
    "ice bath challenge",
    "sauna endurance",
    "polar plunge",
    "walking in blizzard",
    "heatwave no AC",
    "spicy noodle challenge",
    "cold water challenge",
    "extreme heat survival",

    # 疼痛规避（Pain Avoidance）
    # 视觉特征：畏缩、流泪、尖叫、屏住呼吸、肌肉紧绷
    "tattoo pain level",
    "waxing reaction",
    "removing bandaid",
    "piercing reaction",
    "spicy food reaction",
    "hot sauce challenge",
    "painful massage",

    # 身体活动/氧气（Physical Activity/Oxygen）
    # 视觉特征：大口喘气、面色潮红、无法说话、身体瘫软
    "holding breath challenge",
    "altitude sickness",
    "crossfit fail",
    "marathon finish line collapse",
    "breathing exercise extreme",
    "underwater challenge"
]

# 二阶Desire关键词集（Second-Order Desires - 欲望冲突）
# 🎯 目标：捕捉意志力斗争、犹豫、自我约束、后悔等复杂心理状态
KEYWORDS_SECOND_ORDER = [
    # 欲望冲突场景（Desire Conflicts）
    # 特点：多重desire冲突，生理本能 vs 社会动机
    "ice bucket challenge",              # 社交认可 vs 身体舒适
    "trying not to laugh challenge",     # 自我控制 vs 本能反应
    "try not to eat challenge",          # 意志力 vs 食欲
    "diet cheat day vlog",               # 自律 vs 欲望
    "resisting temptation",              # 克制 vs 诱惑

    # 无意图动作与失败集锦（Unintentional Actions）
    # 特点：社会面具脱落，真实本能反应
    "reflexes compilation",
    "scare cam reactions",
    "clumsy moments",
    "instant karma",
    "fail army",
    "people falling",
    "unexpected reactions",

    # 意志力斗争（Willpower Struggles）
    # 特点：犹豫、自我约束、事后后悔
    "trying to quit smoking",
    "struggling to wake up",
    "procrastination vlog",
    "breaking bad habits",
    "new year resolution fail",
    "giving up challenge",

    # 长视频切片（渐变状态）
    # 特点：从专注到疲惫的转变过程
    "study with me tired",
    "all nighter vlog",
    "24 hour challenge exhausted",
    "working overtime tired",

    # 社交压力 vs 生理需求
    "holding pee challenge",
    "not sleeping challenge",
    "endurance challenge",
    "strength test fail"
]

# 扩展Desire关键词集（组合生理需求 + 二阶desire）
# 推荐用于专门收集生理和复杂心理数据
KEYWORDS_DESIRE_EXTENDED = KEYWORDS_PHYSIOLOGICAL + KEYWORDS_SECOND_ORDER

# ==================== 辅助函数 ====================

def get_keywords():
    """获取当前配置的关键词列表"""
    if CUSTOM_KEYWORDS is not None:
        return CUSTOM_KEYWORDS

    keyword_sets = {
        "minimal": KEYWORDS_MINIMAL,
        "standard": KEYWORDS_STANDARD,
        "extensive": KEYWORDS_EXTENSIVE,
        "full": KEYWORDS_FULL,
        "tv_drama": KEYWORDS_TV_DRAMA,
        "movie_clips": KEYWORDS_MOVIE_CLIPS,
        "documentary": KEYWORDS_DOCUMENTARY,
        "mega": KEYWORDS_MEGA,
        # 优化关键词集
        "real_optimized": KEYWORDS_REAL_OPTIMIZED,
        "film_focused": KEYWORDS_FILM_FOCUSED,
        "hybrid_best": KEYWORDS_HYBRID_BEST,
        # 生理需求与二阶Desire关键词集 (2025-12-14)
        "physiological": KEYWORDS_PHYSIOLOGICAL,
        "second_order": KEYWORDS_SECOND_ORDER,
        "desire_extended": KEYWORDS_DESIRE_EXTENDED
    }

    return keyword_sets.get(KEYWORD_SET, KEYWORDS_STANDARD)


def get_estimated_video_count():
    """估算将要搜索的视频数量"""
    keywords = get_keywords()
    return len(keywords) * VIDEOS_PER_KEYWORD


def print_config():
    """打印当前配置"""
    keywords = get_keywords()
    estimated_count = get_estimated_video_count()

    print("=" * 60)
    print("📋 当前搜索配置")
    print("=" * 60)
    print(f"关键词集合: {KEYWORD_SET}")
    print(f"关键词数量: {len(keywords)}")
    print(f"每个关键词搜索: {VIDEOS_PER_KEYWORD} 个视频")
    print(f"预计搜索总数: {estimated_count} 个视频")
    print(f"视频时长范围: {MIN_DURATION}-{MAX_DURATION} 秒")
    print(f"\n搜索重试策略:")
    print(f"  • 最大尝试次数: {MAX_SEARCH_ATTEMPTS}")
    print(f"  • 初始搜索倍数: {SEARCH_MULTIPLIER_INITIAL}x")
    print(f"  • 每次增加倍数: +{SEARCH_MULTIPLIER_INCREMENT}x")
    print(f"  • 预计搜索范围: {VIDEOS_PER_KEYWORD * SEARCH_MULTIPLIER_INITIAL} → {VIDEOS_PER_KEYWORD * (SEARCH_MULTIPLIER_INITIAL + (MAX_SEARCH_ATTEMPTS - 1) * SEARCH_MULTIPLIER_INCREMENT)} 个结果/关键词")
    print(f"\nAI审核: {'启用' if ENABLE_AI_REVIEW else '禁用'}")
    if ENABLE_AI_REVIEW:
        print(f"  • 筛选模式: {FILTER_MODE}")
        if FILTER_MODE == "standard" or FILTER_MODE == "strict":
            print(f"  • 严格程度: {'严格' if STRICT_MODE else '标准'}")
        print(f"  • 并发数: {AI_REVIEW_WORKERS} (同时审核{AI_REVIEW_WORKERS}个视频)")
    print(f"自动删除未通过: {'是' if AUTO_DELETE_REJECTED else '否'}")
    print("=" * 60)
    print(f"\n关键词列表:")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i:2d}. {kw}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
