# 📚 完整系统指南 - YouTube视频采集与AI审核系统

## 🎯 系统概述

这是一个专为**心智理论(Theory of Mind)**研究设计的YouTube视频采集系统，具备：

✅ **智能搜索** - 111个专业关键词，涵盖日常互动、电视剧、电影、纪录片
✅ **AI审核** - Gemini 2.0驱动的专业内容审核，两种模式可选
✅ **自动去重** - 智能识别同一剧集/电影的重复片段
✅ **灵活配置** - 配置文件轻松调整，4个预设规模可选
✅ **完整记录** - JSON数据库追踪所有链接和审核结果

---

## 🚀 快速开始（三步）

### 第一步：配置搜索参数

编辑 [config/search_config.py](../config/search_config.py)：

```python
# 选择关键词集合（新增电视剧/电影关键词）
KEYWORD_SET = "tv_drama"  # 选项见下表

# 每个关键词搜索的视频数量
VIDEOS_PER_KEYWORD = 10

# AI审核设置
ENABLE_AI_REVIEW = True
STRICT_MODE = True  # True=严格，False=宽松
AUTO_DELETE_REJECTED = True
```

**关键词集合选项：**

| 集合名称 | 关键词数 | 说明 | 10个/词时总量 |
|---------|---------|------|--------------|
| `minimal` | 6 | 最小测试集 | 60个 |
| `standard` | 12 | 标准ToM关键词 | 120个 |
| `extensive` | 24 | 扩展ToM关键词 | 240个 |
| `full` | 36 | 完整ToM关键词 | 360个 |
| **`tv_drama`** ⭐ | 25 | **电视剧片段** | **250个** |
| **`movie_clips`** ⭐ | 15 | **电影片段** | **150个** |
| **`documentary`** | 10 | 纪录片 | 100个 |
| **`mega`** 🚀 | 111 | **全部关键词** | **1110个** |

### 第二步：查看配置

```bash
# 激活虚拟环境
cd d:\Desire-VQA\video_anno
.\venv\Scripts\activate

# 预览配置
python config/search_config.py
```

### 第三步：运行搜索

```bash
python scripts/run_search.py
```

---

## 🎬 电视剧/电影采集（新功能）

### 为什么采集电视剧/电影片段？

电视剧和电影是**极佳**的心智理论研究素材：

✅ **丰富的人物互动** - 对话、冲突、情感表达
✅ **复杂的心理动机** - 角色目标、隐藏意图、情感变化
✅ **多样的社交情境** - 家庭、职场、友情、爱情
✅ **专业的剧本编排** - 精心设计的情节和人物弧线
✅ **高质量的视听效果** - 清晰的画面和音频

### 智能去重系统

**问题：** 电视剧片段容易重复（同一剧集的多个场景）

**解决方案：** 自动识别同一剧集，智能去重

**工作原理：**

```python
# 这些会被识别为同一剧集
"Breaking Bad - Best Scene"
"Breaking Bad S01E05 - Intense Moment"
"Breaking Bad (2008) - Final Scene"

# 结果：只保留第一个，其他自动过滤
```

**配置示例：**

```python
# 在 run_search.py 或直接调用时
downloader.batch_search(
    keywords=keywords,
    videos_per_keyword=10,
    enable_smart_dedup=True,     # 启用智能去重
    allow_same_series=False,     # 不允许同剧集的多个片段
    max_per_series=1             # 每个剧集最多1个片段
)
```

**去重效果对比：**

| 配置 | 搜索量 | 去重后 | 独特剧集数 |
|-----|-------|--------|-----------|
| 不使用去重 | 250个 | 250个 | ~50部（大量重复） |
| 严格去重 | 250个 | 165个 | 165部 ✅ |
| 宽松去重 (max=3) | 250个 | 210个 | ~100部 |

详细说明见：[TV_DRAMA_GUIDE.md](TV_DRAMA_GUIDE.md)

---

## 📊 不同使用场景

### 场景1：快速测试（60个视频）

```python
# config/search_config.py
KEYWORD_SET = "minimal"
VIDEOS_PER_KEYWORD = 10
ENABLE_AI_REVIEW = True
STRICT_MODE = True
```

### 场景2：标准采集 - 日常互动（120个视频）⭐

```python
KEYWORD_SET = "standard"      # 日常互动关键词
VIDEOS_PER_KEYWORD = 10
ENABLE_AI_REVIEW = True
STRICT_MODE = True
```

### 场景3：电视剧片段采集（250个视频）🎬

```python
KEYWORD_SET = "tv_drama"      # 电视剧关键词
VIDEOS_PER_KEYWORD = 10
ENABLE_AI_REVIEW = True
STRICT_MODE = False           # 电视剧用标准模式
```

### 场景4：大规模综合采集（555个视频）🚀

```python
KEYWORD_SET = "mega"          # 全部111个关键词
VIDEOS_PER_KEYWORD = 5
ENABLE_AI_REVIEW = True
STRICT_MODE = False           # 大规模用标准模式
```

---

## 🔧 核心功能详解

### 1. 搜索功能

**特性：**
- 111个专业关键词（可自定义）
- 自动过滤时长（30-300秒）
- 自动去除直播和无效视频
- 错误容忍（单个失败不影响整体）

**使用方法：**

```python
from backend.downloader import VideoDownloader

dl = VideoDownloader()
videos = dl.search_videos(
    keyword="tv series emotional scene",
    limit=10,
    min_duration=30,
    max_duration=300
)
```

### 2. AI审核系统

**两种模式：**

| 模式 | 标准 | 适用场景 | 通过率 |
|-----|------|---------|--------|
| **严格模式** | 4项全部达标 | 需要高质量样本 | 30-50% |
| **标准模式** | 大部分达标 | 需要数量和多样性 | 50-70% |

**审核维度：**
1. ⭐⭐⭐ 真实人类出现
2. ⭐⭐⭐ 社交互动或心理活动
3. ⭐⭐ 可分析的情境
4. ⭐ 视频质量

**输出示例：**

```json
{
  "pass": true,
  "reason": "包含两人对话，情感表达明确，适合心智理论研究",
  "confidence": 0.85,
  "类别": "社交互动",
  "互动类型": "对话",
  "分析价值": "高",
  "情感强度": "中等"
}
```

### 3. 智能去重（新功能）

**三重检查机制：**

1. **视频ID去重** - 完全相同的视频
2. **频道+标题去重** - 相同的上传
3. **剧集名称去重** - 同一剧集的不同片段（85%相似度阈值）

**技术实现：**

```python
from backend.deduplicator import VideoDeduplicator

dedup = VideoDeduplicator()

# 提取剧名
series_name = dedup.extract_series_name("Breaking Bad S01E05 - Scene")
# 结果: "breaking bad"

# 检查重复
is_dup = dedup.is_duplicate(video_info)
```

### 4. 数据管理

**自动保存到：**

- `data/search_results.json` - 所有搜索结果
- `data/youtube_links.json` - 链接数据库（含审核结果）
- `data/Youtube_videos/` - 下载的视频文件

**数据库格式：**

```json
{
  "videos": [
    {
      "url": "https://www.youtube.com/watch?v=...",
      "title": "视频标题",
      "duration": 242,
      "keyword": "搜索关键词",
      "approved": true,
      "review_reason": "包含两人对话，情感表达明确",
      "downloaded": true,
      "video_path": "data/Youtube_videos/abc123.mp4",
      "added_time": "2025-11-24T14:00:00"
    }
  ],
  "metadata": {
    "total_count": 120,
    "approved_count": 68,
    "rejected_count": 48
  }
}
```

---

## 📖 关键词详解

### 标准ToM关键词（12个）

```python
# 核心互动
"social interaction psychology"
"people understanding emotions"
"facial expression psychology"

# 认知过程
"theory of mind"
"perspective taking psychology"
"empathy in action"

# 复杂推理
"social cognition experiment"
"false belief task"
"mind reading psychology"

# 实际应用
"emotional intelligence examples"
"reading body language"
"understanding others feelings"
```

### 电视剧关键词（25个）⭐ 新增

**分类1: 情感剧情（5个）**
```python
"tv series emotional scene"
"drama series relationship conflict"
"tv show character development"
"series emotional moments"
"drama series psychological scene"
```

**分类2: 人物互动（5个）**
```python
"tv series dialogue scene"
"drama confrontation scene"
"tv show argument scene"
"series character interaction"
"drama emotional conversation"
```

**分类3: 心理戏份（5个）**
```python
"tv series psychological drama"
"drama series betrayal scene"
"tv show moral dilemma"
"series character motivation"
"drama decision making scene"
```

**分类4: 关系动力学（5个）**
```python
"tv series family dynamics"
"drama friendship conflict"
"tv show romantic tension"
"series trust issues"
"drama power dynamics"
```

**分类5: 特定类型（5个）**
```python
"psychological thriller series scene"
"crime drama interrogation"
"legal drama courtroom scene"
"medical drama ethical dilemma"
"political drama negotiation"
```

### 电影关键词（15个）⭐ 新增

**经典场景（5个）**
```python
"movie scene emotional breakthrough"
"film clip character revelation"
"movie dialogue psychology"
"film scene moral choice"
"movie clip relationship moment"
```

**心理分析（5个）**
```python
"movie analysis psychology"
"film scene breakdown psychology"
"movie character psychology"
"film psychology explained"
"cinema therapy scene analysis"
```

**特定类型（5个）**
```python
"indie film emotional scene"
"drama film intense scene"
"psychological film analysis"
"character study film clip"
"movie scene theory of mind"
```

### 纪录片关键词（10个）⭐ 新增

```python
"documentary human behavior"
"documentary social psychology"
"real life psychology experiment"
"documentary emotional intelligence"
"human nature documentary"
"psychology documentary clip"
"social experiment documentary"
"behavioral science documentary"
"documentary theory of mind"
"documentary cognitive psychology"
```

---

## 🎛️ 高级配置

### 自定义关键词

```python
# 在 config/search_config.py 中
CUSTOM_KEYWORDS = [
    "your custom keyword 1",
    "your custom keyword 2",
    # ... 更多自定义关键词
]

# 在代码中使用
keywords = get_keywords()  # 会优先使用 CUSTOM_KEYWORDS
```

### 调整去重策略

```python
# 严格去重（最大多样性）
enable_smart_dedup = True
allow_same_series = False
max_per_series = 1

# 宽松去重（允许优质剧集多个片段）
enable_smart_dedup = True
allow_same_series = True
max_per_series = 3

# 仅基础去重（只去除完全相同的）
enable_smart_dedup = False
```

### 调整AI审核标准

```python
# 如果通过率太低（<30%）
STRICT_MODE = False  # 切换到标准模式

# 如果需要最高质量（>70%可能标准太宽松）
STRICT_MODE = True  # 使用严格模式

# 查看拒绝原因
# 检查 data/youtube_links.json 中的 review_reason
```

---

## 📈 性能与配额

### 时间估算

| 阶段 | 耗时 |
|-----|------|
| 搜索 | 1-2分钟/关键词 |
| 下载 | 30秒-2分钟/视频 |
| AI审核 | 10-30秒/视频 |

**总时间参考：**
- 60个视频：约30-60分钟
- 120个视频：约1-2小时
- 480个视频：约4-6小时

### API配额

**Gemini 2.0 Flash免费版限制：**
- 每分钟请求数：有限制
- 建议分批处理（每批60-120个）
- 查看配额：https://aistudio.google.com/

---

## 🆘 常见问题

### Q1: 为什么有些剧集没被识别为重复？

**A:** 如果标题差异太大（如不同语言），可能无法识别。

**解决方案：**
- 调整 `max_per_series` 为 2-3
- 或手动检查 `data/youtube_links.json`

### Q2: 电视剧片段通过率低怎么办？

**A:** 电视剧片段通常质量很高，通过率低可能是审核太严格。

**解决方案：**
```python
STRICT_MODE = False  # 切换到标准模式
```

### Q3: 如何完全禁用去重？

**A:**
```python
enable_smart_dedup = False
```

### Q4: 搜索不到视频？

**A:** 检查：
1. 网络连接
2. 更新 yt-dlp：`pip install -U yt-dlp`
3. 尝试更通用的关键词

### Q5: AI审核全部拒绝？

**A:** 检查：
1. 切换到标准模式：`STRICT_MODE = False`
2. 查看拒绝原因：检查 `data/youtube_links.json`
3. 调整关键词，使用更具体的描述

---

## 📂 完整文件结构

```
video_anno/
├── backend/
│   ├── downloader.py          # 核心下载和搜索
│   ├── content_filter.py      # AI审核系统
│   └── deduplicator.py        # 智能去重 (新)
│
├── config/
│   └── search_config.py       # 搜索配置文件
│
├── scripts/
│   ├── run_search.py          # 主运行脚本 (推荐)
│   └── youtube_collector.py   # 完整流程脚本
│
├── docs/
│   ├── COMPLETE_SYSTEM_GUIDE.md     # 本文档 (新)
│   ├── TV_DRAMA_GUIDE.md            # 电视剧采集指南 (新)
│   ├── FINAL_SUMMARY.md             # 系统总结
│   ├── QUICK_START.md               # 快速开始
│   ├── youtube_collection_guide.md  # 完整指南
│   ├── ERROR_FIX.md                 # 错误修复
│   └── setup_ffmpeg_nodejs.md       # 工具安装
│
├── data/
│   ├── search_results.json    # 搜索结果
│   ├── youtube_links.json     # 链接数据库
│   └── Youtube_videos/        # 视频文件
│
└── .env                        # API密钥配置
```

---

## 🎓 推荐工作流

### 工作流1：测试新关键词

```bash
# 1. 小规模测试电视剧关键词
# 编辑 config/search_config.py:
#   KEYWORD_SET = "tv_drama"
#   VIDEOS_PER_KEYWORD = 3
#   STRICT_MODE = False

# 2. 运行搜索
python scripts/run_search.py

# 3. 检查结果
# 查看 data/youtube_links.json 中的通过率和拒绝原因

# 4. 调整并扩大规模
# 如果效果好，增加 VIDEOS_PER_KEYWORD 到 10
```

### 工作流2：大规模数据采集

```bash
# 阶段1: 日常互动（120个）
KEYWORD_SET = "standard"
VIDEOS_PER_KEYWORD = 10
STRICT_MODE = True

# 阶段2: 电视剧片段（250个）
KEYWORD_SET = "tv_drama"
VIDEOS_PER_KEYWORD = 10
STRICT_MODE = False

# 阶段3: 综合采集（555个）
KEYWORD_SET = "mega"
VIDEOS_PER_KEYWORD = 5
STRICT_MODE = False
```

### 工作流3：分批处理（避免API配额限制）

```python
# 方式1: 分多次运行
# 第一次: VIDEOS_PER_KEYWORD = 5
# 第二次: VIDEOS_PER_KEYWORD = 5 (使用不同关键词集)

# 方式2: 先搜索后审核
# 第一步: ENABLE_AI_REVIEW = False（快速下载）
# 第二步: 批量审核已下载视频
```

---

## 🎉 总结

现在你拥有一个功能完善的YouTube视频采集系统：

✅ **111个专业关键词** - 涵盖日常互动、电视剧、电影、纪录片
✅ **智能去重系统** - 自动识别同剧集片段
✅ **专业AI审核** - 两种模式，多维度评估
✅ **灵活配置** - 配置文件轻松调整
✅ **稳定可靠** - 自动错误恢复
✅ **完整记录** - JSON数据库追踪

**立即开始：**

```bash
cd d:\Desire-VQA\video_anno
.\venv\Scripts\activate

# 编辑配置
notepad config\search_config.py

# 运行搜索
python scripts\run_search.py
```

祝研究顺利！ 🚀

---

## 📞 相关文档

- [快速开始](QUICK_START.md) - 三步快速上手
- [电视剧采集指南](TV_DRAMA_GUIDE.md) - 电视剧/电影关键词和去重详解
- [完整使用指南](youtube_collection_guide.md) - 详细功能说明
- [错误修复指南](ERROR_FIX.md) - 常见错误解决方案
- [系统总结](FINAL_SUMMARY.md) - 开发历程和技术细节
