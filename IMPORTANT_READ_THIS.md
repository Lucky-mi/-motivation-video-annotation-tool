# ⚠️ 重要：请先阅读此文档

## 唯一推荐的脚本

**请只使用以下脚本进行视频采集：**

```bash
python scripts/run_search.py
```

## 为什么只用这一个脚本？

`run_search.py` 是**最完整、最优化**的版本，包含：

✅ **所有最新优化**
- 完全移除不必要的延迟（速度提升10倍）
- 跳过已存在视频（避免重复下载）
- 修复了格式兼容性问题

✅ **智能评分系统** (VideoScorer)
- 自动学习历史数据
- 跳过低质量视频，节省API成本
- 优先处理高质量视频

✅ **并发AI审核** (已内置)
- 使用 `ContentFilter.batch_check()`
- 可配置并发数（默认5个）
- 比串行快5-10倍

✅ **流水线处理**
- 下载 → 并发审核 → 立即删除未通过
- 分批处理，节省内存
- 自动释放磁盘空间

✅ **配置驱动**
- 使用 `config/search_config.py` 配置
- **不使用旧的理论性关键词**
- 使用实际场景关键词（如 "people arguing", "emotional reaction"）

## 其他脚本的状态

| 脚本 | 状态 | 说明 |
|------|------|------|
| `run_search.py` | ✅ **推荐使用** | 最完整、最优化的版本 |
| `youtube_collector.py` | ⚠️ 已过时 | 缺少智能评分和并发优化 |
| `youtube_collector_concurrent.py` | ⚠️ 半成品 | 缺少智能评分系统 |
| 其他脚本 | ❌ 忽略 | 实验性或已废弃 |

## 配置文件位置

**统一配置文件**：[config/search_config.py](config/search_config.py)

```python
# 选择关键词集合
KEYWORD_SET = "minimal"  # 选项: minimal, standard, extensive, full, mega

# 每个关键词搜索的视频数量
VIDEOS_PER_KEYWORD = 5

# AI并发审核数
AI_REVIEW_WORKERS = 5
```

## 关键词说明

**当前使用的是实际场景关键词，NOT 理论性关键词！**

### ✅ 正确的关键词（来自 search_config.py）
```python
KEYWORDS_MINIMAL = [
    "people arguing",          # 人们争吵
    "emotional reaction",      # 情感反应
    "surprise moment",         # 惊讶时刻
    "friends talking",         # 朋友交谈
    "family conversation",     # 家庭对话
    "couple disagreement"      # 情侣分歧
]
```

### ❌ 旧的理论性关键词（已废弃，不再使用）
```python
# 这些关键词在 VideoDownloader 类中，但不会被 run_search.py 使用
"social interaction theory of mind"
"people understanding emotions"
# ... 等等
```

## 快速开始

### 1. 查看配置
```bash
python config/search_config.py
```

### 2. 运行采集
```bash
python scripts/run_search.py
```

### 3. 查看结果
```bash
# 搜索结果（包含评分）
cat data/search_results.json

# 视频数据库（包含审核结果）
cat data/youtube_links.json

# 下载的视频
ls data/Youtube_videos/
```

## 性能对比

| 配置 | 关键词数 | 并发审核 | 预计时间 | 预计视频数 |
|------|---------|---------|---------|-----------|
| minimal | 6 | 5个 | 3-5分钟 | ~30个 |
| standard | 12 | 5个 | 5-10分钟 | ~60个 |
| extensive | 24 | 5个 | 15-25分钟 | ~120个 |
| mega | 100+ | 5个 | 1-2小时 | ~500个 |

## 核心优化说明

### 1. 延迟优化
- ✅ 已完全移除搜索时的视频详情延迟
- ✅ 搜索速度提升约10倍
- ✅ 仅在大量请求时极小延迟（每50个请求0.5秒）

### 2. 跳过已存在
- ✅ 下载前检查数据库和文件系统
- ✅ 搜索时自动跳过已有URL
- ✅ 避免重复下载和API调用

### 3. 并发审核
- ✅ 使用 `ContentFilter.batch_check()`
- ✅ 默认5个线程并发审核
- ✅ 可配置并发数（AI_REVIEW_WORKERS）

### 4. 智能评分
- ✅ 自动学习历史数据
- ✅ 跳过低分视频（节省API成本）
- ✅ 优先处理高分视频

### 5. 格式兼容性
- ✅ 简化为 `'format': 'best'`
- ✅ 修复 "Requested format is not available" 错误
- ✅ 添加备用下载方法

## 文件结构

```
video_anno/
├── config/
│   └── search_config.py          ← 唯一配置文件
├── scripts/
│   └── run_search.py              ← 唯一推荐脚本
├── backend/
│   ├── downloader.py              ← 已优化（移除延迟、跳过已存在）
│   ├── content_filter.py          ← 已优化（批量并发审核）
│   └── video_scorer.py            ← 智能评分系统
├── data/
│   ├── search_results.json        ← 搜索结果（包含评分）
│   ├── youtube_links.json         ← 视频数据库
│   ├── video_scores.json          ← 评分学习数据
│   └── Youtube_videos/            ← 下载的视频
└── README_COLLECTION.md           ← 详细使用指南
```

## 常见问题

### Q: 为什么不用并发脚本？
A: `run_search.py` 已经内置了并发审核（通过 `ContentFilter.batch_check()`），并且包含智能评分等额外功能。

### Q: 如何确认使用的是正确的关键词？
A: 运行 `python config/search_config.py` 查看当前关键词列表。

### Q: 如何调整并发数？
A: 编辑 `config/search_config.py` 中的 `AI_REVIEW_WORKERS`。

### Q: 速度还是很慢？
A: 检查：
1. `KEYWORD_SET` 是否设置过大（建议从 "minimal" 开始）
2. `AI_REVIEW_WORKERS` 是否太小（建议5个）
3. 网络连接是否稳定

## 下一步

1. ✅ 查看配置：`python config/search_config.py`
2. ✅ 运行采集：`python scripts/run_search.py`
3. ✅ 查看详细文档：[README_COLLECTION.md](README_COLLECTION.md)

---

**记住**：只使用 `scripts/run_search.py`！
