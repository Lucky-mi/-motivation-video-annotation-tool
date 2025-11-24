# YouTube视频采集系统使用指南

## 📋 系统简介

这是一个专为**心智理论（Theory of Mind）研究**设计的YouTube视频自动化采集系统。系统会：
1. 🔍 根据专业关键词搜索YouTube视频
2. 🤖 使用AI（Gemini）自动审核视频内容
3. 📥 下载符合研究要求的高质量视频

## 🎯 核心功能

### 1. 智能搜索
- 内置**36个专业关键词**，涵盖：
  - 社交互动与心理推理
  - 情绪与动机推理
  - 日常生活场景
  - 戏剧与叙事
  - 心理学实验

### 2. AI智能审核
- 严格模式：确保视频包含真实人类、社交互动、可分析情境
- 标准模式：较宽松的筛选标准
- 自动排除：游戏、教程、风景、纯技能展示等

### 3. 自动化流程
- 支持批量搜索 → AI审核 → 自动下载
- 链接数据库管理（自动去重、状态跟踪）
- 详细的审核报告和日志

## 🚀 快速开始

### 前置准备

1. **安装依赖**
```bash
pip install yt-dlp google-generativeai
```

2. **配置API密钥**
在 `.env` 文件中设置：
```bash
GEMINI_API_KEY=your_api_key_here
```

### 基础使用

#### 方式1: 使用主脚本（推荐）

```bash
# 完整流程：搜索 + 审核（默认严格模式）
python scripts/youtube_collector.py --mode full --per-keyword 2

# 使用自定义关键词
python scripts/youtube_collector.py --mode full --keywords "social interaction" "psychology experiment" --per-keyword 3

# 标准审核模式（较宽松）
python scripts/youtube_collector.py --mode full --no-strict

# 查看统计信息
python scripts/youtube_collector.py --mode stats
```

#### 方式2: 在代码中使用

```python
from backend.downloader import VideoDownloader
from backend.content_filter import ContentFilter

# 初始化
downloader = VideoDownloader()
content_filter = ContentFilter()

# 1. 搜索视频
videos = downloader.search_videos("social interaction psychology", limit=5)
print(f"找到 {len(videos)} 个视频")

# 2. 批量搜索（使用内置关键词）
all_videos = downloader.batch_search(videos_per_keyword=3)

# 3. 下载并审核
for video in videos:
    # 下载
    result = downloader.download_from_url(video['url'])
    video_path = result['video_path']

    # AI审核
    review = content_filter.check_video_content(video_path, strict_mode=True)

    if review['pass']:
        print(f"✅ 通过: {review['reason']}")
        # 更新数据库状态
        downloader.add_video_link(
            url=video['url'],
            title=video['title'],
            duration=video['duration'],
            keyword="social interaction psychology",
            approved=True,
            review_reason=review['reason']
        )
    else:
        print(f"❌ 未通过: {review['reason']}")
```

## 📊 数据管理

### 链接数据库

系统自动维护一个JSON数据库（`data/youtube_links.json`），包含：
- 视频URL、标题、时长
- 搜索关键词
- AI审核结果
- 下载状态
- 统计信息

查看数据库：
```python
from backend.downloader import VideoDownloader

dl = VideoDownloader()

# 查看所有通过审核的视频
approved = dl.get_approved_videos()
print(f"通过审核: {len(approved)} 个")

# 查看待审核的视频
pending = dl.get_pending_review_videos()
print(f"待审核: {len(pending)} 个")

# 查看统计信息
print(dl.links_db['metadata'])
```

### 审核报告

每次运行完整流程后，会在 `reports/` 目录生成详细报告：
- 时间戳
- 搜索/审核统计
- 每个视频的详细审核结果

## 🔧 高级配置

### 自定义搜索参数

```python
# 调整时长范围
videos = downloader.search_videos(
    keyword="psychology experiment",
    limit=10,
    min_duration=60,    # 最少1分钟
    max_duration=600    # 最多10分钟
)
```

### 自定义审核标准

修改 `backend/content_filter.py` 中的 `_build_filter_prompt()` 方法，调整审核标准。

### 批量处理现有视频

```python
from backend.content_filter import ContentFilter
from pathlib import Path

filter = ContentFilter()

# 获取所有视频
video_dir = Path("data/Youtube_videos")
video_files = list(video_dir.glob("*.mp4"))

# 批量审核
results = filter.batch_check(
    video_paths=[str(f) for f in video_files],
    strict_mode=True
)

# 统计结果
passed = sum(1 for r in results.values() if r['pass'])
print(f"通过率: {passed}/{len(results)}")
```

## 📝 内置关键词列表

系统内置了36个专业关键词，分为4大类：

### 1. 社交互动与心理推理 (8个)
- social interaction theory of mind
- people understanding emotions
- human interaction psychology
- interpersonal communication psychology
- emotional intelligence social
- reading facial expressions
- body language interpretation
- social cues understanding

### 2. 情绪与动机推理 (7个)
- understanding human motivation
- human desire and intention
- implicit motivation psychology
- emotional reasoning
- intention recognition psychology
- goal-directed behavior
- mental states understanding

### 3. 日常生活场景 (7个)
- everyday social situations
- real life social dilemmas
- human behavior psychology daily
- social decision making
- moral reasoning scenarios
- helping behavior psychology
- conflict resolution interaction

### 4. 戏剧与叙事 (6个)
- short drama psychological
- psychology mini movie
- character motivation film
- psychological short film
- social experiment video
- human nature story

### 5. 实验与教育 (6个)
- psychology experiment social
- theory of mind demonstration
- false belief task video
- perspective taking exercise
- empathy training video
- cognitive psychology demonstration

## 🎯 AI审核标准

### 严格模式（推荐用于研究）

必须同时满足：
1. ⭐⭐⭐ **真实人类出现**
   - 非动画、游戏、AI生成
   - 面部清晰可见
   - 合理画面比例

2. ⭐⭐⭐ **社交互动或心理活动**
   - 多人：对话、眼神、肢体互动
   - 单人：情绪表达、决策过程
   - 可观察的心理状态

3. ⭐⭐ **可分析的情境**
   - 明确背景
   - 动机/意图/欲望表现
   - 因果关系

4. ⭐ **视频质量**
   - 画面稳定清晰
   - 音频可理解
   - 无大量无关内容

### 标准模式

较为宽松，只要有人类出现、有互动或情感、基本可分析即可。

### 自动排除

- 纯风景/动物/建筑
- 游戏录屏/软件教程
- 纯技能展示（烹饪、化妆等无情感交流）
- 幻灯片/文字滚动
- 纯音乐MV（无剧情）
- 纯搞笑/恶作剧（无分析价值）

## 🔍 审核结果字段说明

```json
{
  "pass": true,                           // 是否通过
  "reason": "包含两人对话，情感表达明确",  // 理由
  "category": "social_interaction",        // 类别
  "confidence": 0.85,                     // 置信度 (0-1)
  "人物数量": 2,                           // 人数
  "互动类型": "对话/眼神交流",              // 互动方式
  "情感强度": "高",                        // 情感程度
  "分析价值": "高",                        // 研究价值
  "关键场景描述": "两人在咖啡厅讨论决策"    // 场景描述
}
```

## 📁 文件结构

```
video_anno/
├── backend/
│   ├── downloader.py          # 视频下载和搜索
│   ├── content_filter.py      # AI内容审核
│   └── vlm_analyzer.py        # VLM分析器（基础）
├── scripts/
│   └── youtube_collector.py   # 主流程脚本
├── data/
│   ├── Youtube_videos/        # 下载的视频
│   └── youtube_links.json     # 链接数据库
├── reports/                   # 审核报告
└── logs/                      # 运行日志
```

## ⚠️ 注意事项

1. **API配额**：Gemini API有免费配额限制，建议分批处理
2. **下载速度**：YouTube下载速度取决于网络环境
3. **存储空间**：确保有足够空间存储视频
4. **版权问题**：仅用于研究目的，遵守YouTube服务条款
5. **审核误差**：AI审核不是100%准确，建议人工复核重要样本

## 🐛 常见问题

### Q: 搜索不到视频？
A: 检查网络连接，确认yt-dlp已更新到最新版本：`pip install -U yt-dlp`

### Q: AI审核失败？
A: 检查Gemini API密钥是否正确配置，确认API配额未超限

### Q: 视频下载失败？
A: 某些视频可能有地区限制或年龄限制，系统会自动跳过

### Q: 如何提高审核通过率？
A: 使用 `--no-strict` 切换到标准模式，或自定义关键词使搜索更精准

## 📞 技术支持

如遇问题，请检查：
1. 日志文件 `logs/youtube_collector_*.log`
2. 审核报告 `reports/review_report_*.json`
3. 链接数据库 `data/youtube_links.json`

## 📈 推荐工作流程

```bash
# 1. 小规模测试（每个关键词2个视频）
python scripts/youtube_collector.py --mode full --per-keyword 2

# 2. 查看统计和结果
python scripts/youtube_collector.py --mode stats

# 3. 如果效果好，扩大规模
python scripts/youtube_collector.py --mode full --per-keyword 5

# 4. 定期备份数据库
cp data/youtube_links.json data/youtube_links_backup_$(date +%Y%m%d).json
```

祝研究顺利！ 🎓
