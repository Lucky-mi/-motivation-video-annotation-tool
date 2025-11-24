# 🚀 快速开始指南

## 📝 三步完成视频采集

### 第一步：配置参数

编辑 [config/search_config.py](../config/search_config.py)：

```python
# 选择关键词集合
KEYWORD_SET = "standard"  # 选项: "minimal"(6个), "standard"(12个), "extensive"(24个), "full"(36个)

# 每个关键词搜索的视频数量
VIDEOS_PER_KEYWORD = 5  # 增加这个数字可以搜索更多

# 是否启用AI审核
ENABLE_AI_REVIEW = True

# 审核模式
STRICT_MODE = True  # True=严格，False=宽松
```

### 第二步：查看将要搜索的数量

```bash
# 预览配置
python config/search_config.py
```

输出示例：
```
====================================================================
📋 当前搜索配置
====================================================================
关键词集合: standard
关键词数量: 12
每个关键词搜索: 5 个视频
预计搜索总数: 60 个视频
视频时长范围: 30-300 秒
AI审核: 启用 (严格模式)
自动删除未通过: 是
====================================================================
```

### 第三步：运行搜索

```bash
# 运行主脚本
python scripts/run_search.py
```

系统会：
1. 显示配置信息
2. 要求确认
3. 自动搜索、下载、AI审核
4. 生成统计报告

---

## 🎯 快速调整搜索数量

### 方案1：修改配置文件（推荐）

编辑 `config/search_config.py`：

```python
# 要搜索更多视频，有两种方式：

# 方式1: 增加每个关键词的搜索数量
VIDEOS_PER_KEYWORD = 10  # 从5改成10，搜索量翻倍

# 方式2: 使用更多关键词
KEYWORD_SET = "extensive"  # 从standard(12个)改成extensive(24个)
```

### 方案2：使用自定义关键词

```python
# 在 search_config.py 中设置
CUSTOM_KEYWORDS = [
    "psychology experiment",
    "social behavior",
    "emotional intelligence",
    "theory of mind",
    "human interaction"
]
```

---

## 📊 不同配置的搜索量对比

| 配置 | 关键词数 | 每词5个 | 每词10个 | 每词20个 |
|------|----------|---------|----------|----------|
| minimal | 6 | 30 | 60 | 120 |
| **standard** | **12** | **60** | **120** | **240** |
| extensive | 24 | 120 | 240 | 480 |
| full | 36 | 180 | 360 | 720 |

**推荐配置：**
- 快速测试：`minimal` + 5个/词 = 30个视频
- 标准采集：`standard` + 10个/词 = 120个视频 ✅
- 大规模采集：`extensive` + 20个/词 = 480个视频

---

## 🔧 高级用法

### 只搜索不审核（快速收集链接）

```python
# 在 search_config.py 中设置
ENABLE_AI_REVIEW = False
```

这样会快速下载所有视频，稍后再批量审核。

### 批量审核已下载的视频

```python
# 创建新脚本或使用Python交互模式
from backend.content_filter import ContentFilter
from pathlib import Path

cf = ContentFilter()
video_dir = Path("data/Youtube_videos")
videos = list(video_dir.glob("*.mp4"))

# 批量审核
results = cf.batch_check([str(v) for v in videos], strict_mode=True)

# 查看结果
passed = [v for v, r in results.items() if r['pass']]
print(f"通过: {len(passed)}/{len(videos)}")
```

### 查看审核统计

```bash
python scripts/youtube_collector.py --mode stats
```

---

## 📁 输出文件说明

运行后会生成以下文件：

```
data/
├── search_results.json      # 搜索到的所有视频信息
├── youtube_links.json       # 链接数据库（含审核结果）
└── Youtube_videos/          # 下载的视频文件
    ├── uuid1.mp4
    ├── uuid2.mp4
    └── ...

reports/
└── review_report_*.json     # 详细审核报告

logs/
└── youtube_collector_*.log  # 运行日志
```

---

## ⚡ 常见场景

### 场景1：快速测试（搜索30个）

```python
# search_config.py
KEYWORD_SET = "minimal"
VIDEOS_PER_KEYWORD = 5
ENABLE_AI_REVIEW = True
```

### 场景2：标准采集（搜索120个）⭐

```python
# search_config.py
KEYWORD_SET = "standard"
VIDEOS_PER_KEYWORD = 10
ENABLE_AI_REVIEW = True
STRICT_MODE = True
```

### 场景3：大规模采集（搜索480个）

```python
# search_config.py
KEYWORD_SET = "extensive"
VIDEOS_PER_KEYWORD = 20
ENABLE_AI_REVIEW = True
STRICT_MODE = False  # 使用标准模式提高通过率
```

### 场景4：收集链接（不下载）

目前系统会先下载再审核。如果只想收集链接，可以：

```bash
# 使用搜索模式
python scripts/youtube_collector.py --mode search --keywords "psychology" --per-keyword 20
```

然后查看 `data/search_results.json`

---

## 💡 优化建议

### 1. 减少警告

安装 ffmpeg 可以减少大部分警告：
```bash
# Windows (使用 Scoop)
scoop install ffmpeg

# 验证
ffmpeg -version
```

### 2. 提高通过率

如果AI审核通过率太低：
- 设置 `STRICT_MODE = False`（使用标准模式）
- 调整关键词，使用更具体的描述
- 查看 `data/youtube_links.json` 中的 `review_reason` 了解拒绝原因

### 3. 节省API配额

- 先用 `VIDEOS_PER_KEYWORD = 3` 小规模测试
- 确认通过率合理后再增加数量
- 考虑分批处理，避免一次性审核太多

---

## 🆘 故障排查

### 问题1: 搜索不到视频

**可能原因：** 网络问题或关键词太特殊

**解决方案：**
- 检查网络连接
- 尝试更通用的关键词
- 更新 yt-dlp: `pip install -U yt-dlp`

### 问题2: AI审核失败

**可能原因：** API密钥未配置或配额用尽

**解决方案：**
- 检查 `.env` 文件中的 `GEMINI_API_KEY`
- 查看 Gemini API 配额: https://aistudio.google.com/
- 临时禁用AI审核: `ENABLE_AI_REVIEW = False`

### 问题3: 全部被拒绝

**可能原因：** 严格模式太严格或关键词不合适

**解决方案：**
- 切换到标准模式: `STRICT_MODE = False`
- 查看拒绝理由: `cat data/youtube_links.json | grep "review_reason"`
- 调整关键词，使用更符合研究需求的词

---

## 📞 需要帮助？

- 查看完整文档: [docs/youtube_collection_guide.md](youtube_collection_guide.md)
- 查看配置说明: [config/search_config.py](../config/search_config.py)
- 查看日志文件: `logs/youtube_collector_*.log`

---

**🎉 现在就开始采集你的视频数据吧！**
