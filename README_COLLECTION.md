# 视频采集系统使用指南

## ⚠️ 重要说明

**请只使用 `scripts/run_search.py`，这是唯一推荐的脚本！**

其他脚本（youtube_collector.py, youtube_collector_concurrent.py）已过时，请忽略。

---

## 快速开始

### 1. 配置关键词

编辑 [config/search_config.py](config/search_config.py)：

```python
# 选择关键词集合
KEYWORD_SET = "minimal"  # minimal(6个) | standard(12个) | extensive(24个) | full(36个) | mega(100+)

# 每个关键词搜索的视频数量
VIDEOS_PER_KEYWORD = 5

# AI并发审核数（同时审核的视频数量）
AI_REVIEW_WORKERS = 5  # 建议 3-5
```

### 2. 查看配置

```bash
# 查看当前配置
python config/search_config.py
```

### 3. 运行采集

```bash
python scripts/run_search.py
```

## 系统架构

`run_search.py` 是**唯一推荐的脚本**，包含完整的采集流程：

```
阶段1: 批量搜索
  ↓
阶段1.5: 智能评分预筛选 (VideoScorer)
  ├─ 高分视频: 优先处理 ⭐
  ├─ 中等视频: 正常处理
  └─ 低分视频: 跳过 ⏭️ (节省API成本)
  ↓
阶段2: 流水线处理 (分批)
  ├─ 批量下载 (batch_size 个)
  ├─ 并发AI审核 (max_workers 个线程)
  └─ 立即删除未通过 (释放磁盘)
  ↓
阶段3: 统计报告
```

## 核心功能

### ✅ 智能评分系统
- 自动学习历史数据，识别高质量频道
- 跳过低质量视频，节省API成本
- 优先处理高分视频

### ✅ 并发AI审核
- 批量并发审核，速度提升5-10倍
- 可配置并发数（AI_REVIEW_WORKERS）

### ✅ 流水线处理
- 边下载边审核边删除
- 立即释放未通过视频的磁盘空间
- 分批处理，减少内存占用

### ✅ 配置驱动
- 所有配置集中在 `search_config.py`
- 无需修改代码即可调整参数

## 关键词配置详解

### minimal (6个) - 快速测试
```python
KEYWORDS_MINIMAL = [
    "people arguing",
    "emotional reaction",
    "surprise moment",
    "friends talking",
    "family conversation",
    "couple disagreement"
]
```
- **用途**: 快速测试系统
- **预计时间**: 3-5分钟
- **预计视频**: 约30个候选

### standard (12个) - 推荐日常使用
- **用途**: 日常采集，平衡速度和覆盖
- **预计时间**: 5-10分钟
- **预计视频**: 约60个候选

### extensive (24个) - 更全面
- **用途**: 需要更多样化的场景
- **预计时间**: 15-25分钟
- **预计视频**: 约120个候选

### mega (100+个) - 大规模采集
- **用途**: 一次性大规模采集
- **预计时间**: 1-2小时
- **预计视频**: 约500个候选
- **组成**: full + tv_drama + movie_clips + documentary

## 性能优化

### 1. 调整并发数

```python
# config/search_config.py
AI_REVIEW_WORKERS = 5  # 建议值
```

- **3个**: 稳定，适合网络不稳定
- **5个**: 推荐，速度和稳定性平衡
- **7个**: 最快，可能触发API限制

### 2. 预筛选节省成本

VideoScorer 会自动：
- 跳过低质量视频（节省API调用）
- 优先处理高质量视频
- 学习历史数据，越用越准

### 3. 延迟优化

已完全移除搜索延迟：
- 搜索速度提升 10倍
- 不再有不必要的等待
- 仅在大量请求时极小延迟

## 输出文件

| 文件 | 说明 |
|------|------|
| `data/search_results.json` | 搜索结果（包含评分） |
| `data/youtube_links.json` | 视频数据库（包含审核结果） |
| `data/Youtube_videos/` | 下载的视频文件 |
| `data/video_scores.json` | 评分系统学习数据 |

## 常见问题

### Q: 为什么有些视频被跳过？
A: VideoScorer 评分低于阈值会自动跳过，节省API成本。

### Q: 如何调整评分阈值？
A: 编辑 `backend/video_scorer.py` 中的 `SCORE_THRESHOLD`。

### Q: 并发数设置多少合适？
A: 建议从3开始，如果稳定可以增加到5-7。

### Q: 速度还是很慢？
A: 检查：
1. 网络连接是否稳定
2. 是否触发YouTube限制
3. API配额是否充足

### Q: 其他脚本呢？
A: 请忽略其他脚本（youtube_collector.py, youtube_collector_concurrent.py），只使用 `run_search.py`。

## 完整配置示例

```python
# config/search_config.py

# === 搜索配置 ===
KEYWORD_SET = "standard"        # 使用标准关键词集
VIDEOS_PER_KEYWORD = 5          # 每个关键词搜索5个
MIN_DURATION = 30               # 最短30秒
MAX_DURATION = 300              # 最长5分钟

# === AI审核配置 ===
ENABLE_AI_REVIEW = True         # 启用AI审核
STRICT_MODE = True              # 严格模式
AUTO_DELETE_REJECTED = True     # 自动删除未通过
AI_REVIEW_WORKERS = 5           # 5个并发审核

# 自定义关键词（可选）
# CUSTOM_KEYWORDS = ["people crying", "angry moment"]
```

## 监控运行

```bash
# 保存日志
python scripts/run_search.py 2>&1 | tee collection.log

# 实时监控
tail -f collection.log
```

## 数据统计

运行后会显示：
```
📊 最终统计
================================
搜索: 60 个视频
通过: 25 (41.7%)
拒绝: 30 (50.0%)
失败: 5
```

## 最佳实践

1. **首次运行**: 使用 `minimal` 测试系统
2. **日常采集**: 使用 `standard` 或 `extensive`
3. **大规模采集**: 使用 `mega`，分多次运行
4. **调整并发**: 从3开始，逐步增加
5. **定期检查**: 查看 `video_scores.json` 了解学习情况

---

**记住**: 只使用 `scripts/run_search.py`，其他脚本已过时！
