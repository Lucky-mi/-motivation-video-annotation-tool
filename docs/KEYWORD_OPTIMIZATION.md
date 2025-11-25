# 关键词优化建议 - 提高审核通过率

## 📊 当前问题分析

**审核通过率：25% (19/76)**
**审核拒绝率：75% (57/76)** ❌

### 主要拒绝原因

1. **硬字幕/水印** (多次) - 视频包含内嵌字幕
2. **Reaction Video** (多次) - 观看反应视频，不是原始场景
3. **3D动画/游戏** - 非真人实拍
4. **访谈/播客** - 缺少行为展示
5. **剪辑合集** - 多个片段拼接

---

## 🎯 优化策略

### 策略 1️⃣：添加排除词 (Negative Keywords)

在搜索时主动排除容易出现的低质量视频类型：

#### 建议添加到 `search_config.py`：

```python
# 搜索时排除的关键词
EXCLUDE_KEYWORDS = [
    "reaction",      # 排除 reaction videos
    "compilation",   # 排除合集
    "tiktok",        # 排除 TikTok 搬运
    "shorts",        # 排除 YouTube Shorts
    "meme",          # 排除 meme 视频
    "anime",         # 排除动画
    "cartoon",       # 排除卡通
    "gameplay",      # 排除游戏
    "minecraft",     # 排除游戏
    "roblox",        # 排除游戏
    "fortnite",      # 排除游戏
    "review",        # 排除评论视频
    "explained",     # 排除解说视频
    "tutorial",      # 排除教程
    "how to",        # 排除教程
]
```

### 策略 2️⃣：优化关键词，增加"真实场景"修饰词

#### 当前问题关键词：
```python
"emotional reaction"  # ❌ 容易搜到 reaction videos
"crying moment"       # ❌ 容易搜到剪辑合集
"surprise reaction"   # ❌ 容易搜到反应视频
```

#### 改进建议：
```python
# 添加 "caught on camera", "real", "actual" 等修饰词
"caught on camera emotional"
"real argument caught on camera"
"actual fight video"
"security camera footage"
"body cam footage"
"dash cam video"
"street confrontation real"
"public freakout real"
```

---

## 💡 推荐的新关键词集

### 选项 A：真实场景重点（推荐）

```python
KEYWORDS_REAL_SCENES = [
    # 安全监控类（高质量）
    "security camera fight",
    "caught on camera argument",
    "dash cam road rage",
    "body cam police",

    # 公共场所真实冲突
    "public freakout caught on camera",
    "street fight real",
    "karen freakout",
    "restaurant argument caught",
    "store confrontation real",

    # 真实情感场景
    "proposal reaction real",
    "surprise reunion caught",
    "emotional reunion soldier",
    "breakup caught on camera",

    # 纪录片风格
    "real life drama caught",
    "caught in the act real",
    "confrontation caught on camera",
    "altercation footage"
]
```

### 选项 B：电视剧/电影片段（已有）

```python
# 使用 KEYWORD_SET = "tv_drama" 或 "movie_clips"
# 优点：质量稳定，无字幕
# 缺点：可能是演员表演，不是"真实"行为
```

### 选项 C：混合策略（最优）

```python
KEYWORDS_MIXED = [
    # 真实场景 (50%)
    "caught on camera fight",
    "security footage argument",
    "dash cam confrontation",
    "public argument real",
    "street fight caught",
    "karen freakout",

    # 电视剧场景 (30%)
    "tv show argument scene",
    "drama emotional scene",
    "movie fight scene",

    # 纪录片/真人秀 (20%)
    "reality show argument",
    "documentary confrontation",
    "real couples therapy"
]
```

---

## 🔧 实施步骤

### 步骤 1：修改 `config/search_config.py`

添加新的关键词集：

```python
# 在 search_config.py 末尾添加

# 真实场景优化关键词（2025-11-25 优化）
KEYWORDS_REAL_OPTIMIZED = [
    # 监控摄像头类（无字幕，真实）
    "security camera fight",
    "caught on camera argument",
    "dash cam road rage",
    "cctv footage fight",

    # 公共冲突（真实性高）
    "public freakout real",
    "karen freakout",
    "street confrontation",
    "restaurant fight caught",

    # 真实情感（避免 reaction）
    "proposal caught on camera",
    "emotional reunion real",
    "soldier reunion surprise",
    "breakup caught",

    # 电视真人秀（质量稳定）
    "reality show argument",
    "couples therapy fight",
    "real housewives argument",

    # 新闻/纪录片
    "altercation caught on tape",
    "confrontation footage",
    "incident caught on camera"
]
```

然后修改：
```python
KEYWORD_SET = "real_optimized"  # 使用优化后的关键词
```

### 步骤 2：增强搜索过滤

修改 `backend/downloader.py` 的搜索方法，添加标题过滤：

```python
def should_skip_video(self, title: str, description: str) -> bool:
    """检查是否应该跳过视频（基于标题和描述）"""
    skip_keywords = [
        'reaction', 'compilation', 'tiktok', 'shorts',
        'meme', 'anime', 'cartoon', 'gameplay',
        'minecraft', 'roblox', 'review', 'explained'
    ]

    title_lower = title.lower()
    desc_lower = description.lower()

    for keyword in skip_keywords:
        if keyword in title_lower or keyword in desc_lower:
            return True

    return False
```

### 步骤 3：调整评分系统

修改 `backend/video_scorer.py`，增加对"真实场景"的偏好：

```python
# 真实场景标记词（加分）
REAL_SCENE_MARKERS = [
    'caught', 'camera', 'footage', 'real', 'actual',
    'security', 'dash cam', 'body cam', 'cctv'
]

# 低质量标记词（扣分）
LOW_QUALITY_MARKERS = [
    'reaction', 'compilation', 'tiktok', 'meme',
    'anime', 'cartoon', 'gameplay'
]
```

---

## 📈 预期效果

### 当前表现
- 通过率：**25%**
- 每搜索 120 个视频 → 30 个通过

### 优化后预期
- 通过率：**50-60%**
- 每搜索 120 个视频 → 60-72 个通过

**效率提升：2-3倍！**

---

## 🚀 快速实施

### 方案 A：最小改动（推荐新手）

```bash
# 1. 修改配置文件
vim config/search_config.py

# 将 KEYWORD_SET 改为 "documentary"
KEYWORD_SET = "documentary"  # 使用纪录片关键词

# 2. 重新搜索
python scripts/run_search.py --search-only
```

### 方案 B：完整优化（推荐）

```bash
# 1. 备份当前配置
cp config/search_config.py config/search_config_backup.py

# 2. 添加优化关键词（见上方代码）

# 3. 修改关键词集
KEYWORD_SET = "real_optimized"

# 4. 重新搜索
python scripts/run_search.py --search-only
```

---

## 🔍 分析工具

### 查看拒绝原因分布

```bash
python -c "
import json
data = json.load(open('data/youtube_links.json', 'r', encoding='utf-8'))
rejected = [v for v in data['videos'] if v.get('approved') == False]

# 分类拒绝原因
categories = {
    '字幕问题': ['字幕', 'subtitle', '硬字幕'],
    'Reaction视频': ['reaction', '反应'],
    '动画/游戏': ['3D', '动画', 'anime', 'cartoon', 'gameplay'],
    '访谈/播客': ['访谈', '播客', 'interview', 'podcast'],
    '其他': []
}

for v in rejected:
    reason = v.get('review_reason', '')
    categorized = False
    for cat, keywords in categories.items():
        if any(kw in reason for kw in keywords):
            print(f'[{cat}] {v[\"title\"][:50]}')
            categorized = True
            break
    if not categorized:
        print(f'[其他] {v[\"title\"][:50]}: {reason[:100]}')
"
```

---

## 💾 备用方案

如果优化后通过率仍然不理想：

### 方案 1：使用电影/电视剧片段
```python
KEYWORD_SET = "tv_drama"  # 或 "movie_clips"
```
- 优点：质量稳定，较少字幕
- 缺点：是表演，不是真实行为

### 方案 2：专注特定来源
```python
# 搜索特定频道/系列
CUSTOM_KEYWORDS = [
    "What Would You Do ABC",          # ABC 真人实验节目
    "Undercover Boss",                # 真人秀
    "Kitchen Nightmares Gordon Ramsay",  # 真实餐厅冲突
    "Cops TV show",                   # 警察真实出警
]
```

### 方案 3：降低标准
修改 `config/search_config.py`：
```python
STRICT_MODE = False  # 从严格模式改为标准模式
```

---

## ✅ 总结

**立即可做的改进**：

1. ✅ 使用 `KEYWORD_SET = "documentary"` - 最简单
2. ✅ 添加 `KEYWORDS_REAL_OPTIMIZED` - 最有效
3. ✅ 启用标题过滤 - 减少明显低质量视频
4. ✅ 调整评分权重 - 提前筛选

**预期结果**：
- 审核通过率从 25% → 50-60%
- 搜索效率提升 2-3 倍
- 减少 API 审核成本

需要我帮你实施这些优化吗？
