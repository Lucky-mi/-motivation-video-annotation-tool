# config/search_config.py
"""
YouTube搜索和审核配置
可以在这里轻松调整参数
"""

# ==================== 搜索配置 ====================

# 选择要使用的关键词集合（可以修改这里来改变搜索数量）
# 基础选项: "minimal", "standard", "extensive", "full", "tv_drama", "movie_clips", "documentary", "mega"
# 优化选项: "real_optimized" (推荐!), "film_focused", "hybrid_best"
KEYWORD_SET = "full"  # 推荐使用优化关键词，预期通过率 50-60%

# 自定义关键词（如果不为None，则使用自定义关键词而不是预设）
CUSTOM_KEYWORDS = None  # 例如: ["psychology video", "social behavior"]

# 每个关键词搜索的视频数量（增加这个数字可以得到更多候选视频）
# 建议值: 3-5 (避免被限制), 10+ (快速收集但风险高)
VIDEOS_PER_KEYWORD = 5  # 推荐：保守配置，避免触发反爬虫

# 视频时长过滤（秒）
MIN_DURATION = 30   # 最短30秒
MAX_DURATION = 300  # 最长5分钟

# ==================== AI审核配置 ====================

# 是否启用AI审核
ENABLE_AI_REVIEW = True

# 审核模式（True=严格模式，False=标准模式）
STRICT_MODE = True

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
AI_REVIEW_WORKERS = 3  # 当前配置：保守模式（修改此值来调整并发）

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
        # 新增优化关键词集
        "real_optimized": KEYWORDS_REAL_OPTIMIZED,
        "film_focused": KEYWORDS_FILM_FOCUSED,
        "hybrid_best": KEYWORDS_HYBRID_BEST
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
    print(f"AI审核: {'启用 (' + ('严格模式' if STRICT_MODE else '标准模式') + ')' if ENABLE_AI_REVIEW else '禁用'}")
    if ENABLE_AI_REVIEW:
        print(f"AI并发数: {AI_REVIEW_WORKERS} (同时审核{AI_REVIEW_WORKERS}个视频)")
    print(f"自动删除未通过: {'是' if AUTO_DELETE_REJECTED else '否'}")
    print("=" * 60)
    print(f"\n关键词列表:")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i:2d}. {kw}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
