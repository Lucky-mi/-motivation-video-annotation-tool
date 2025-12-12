# Annotation Pipeline User Guide
# 二阶段标注流程使用指南

**Version:** 1.0
**Last Updated:** 2025-01-15

---

## 📖 概述

本系统实现了**两阶段智能标注流程**，通过质量预审机制降低标注成本，提高数据集质量：

```
┌─────────────────────────────────────────────────────────────┐
│                   视频输入 (Video Input)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │  Stage 1: 质量预审          │
         │  Quality Assessment         │
         │  - 快速评估 (轻量prompt)    │
         │  - 4维度打分               │
         │  - 决策建议                │
         └──────────┬──────────────────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
    ✅ PASS              ❌ REJECT
  (score ≥ 65)        (score < 55)
          │                   │
          │                   ├─→ rejected_videos.json
          │                   │
          ▼                   ▼
┌─────────────────┐   ⚠️ BORDERLINE
│  Stage 2:       │     (55-64)
│  完整标注       │          │
│  Full           │          └─→ borderline_videos.json
│  Annotation     │
└────────┬────────┘
         │
         ▼
  full_annotations/
  {video_name}_annotation.json
```

---

## 🎯 核心优势

### 1. **成本优化**
- **质量预审**: ~500 tokens (轻量评估)
- **完整标注**: ~2000+ tokens (深度分析)
- **节省成本**: 对不合格视频避免昂贵的完整标注

### 2. **质量保证**
- **4维度评估**: 可观察行为、心理价值、标注可行性、研究伦理
- **明确阈值**: 自动化决策，减少主观性
- **失败追踪**: 记录拒绝原因，反馈优化搜索策略

### 3. **可追溯性**
- **拒绝日志**: `rejected_videos.json` - 记录所有被拒绝的视频
- **边界日志**: `borderline_videos.json` - 需人工复审的边界案例
- **质量报告**: 每个视频的详细评估结果

---

## 🚀 快速开始

### 安装依赖

```bash
# 确保已安装所有依赖
pip install -r requirements.txt

# 配置API密钥
export GEMINI_API_KEY="your-api-key"
# 或在 .env 文件中配置
```

### 单视频标注示例

```python
from backend.annotation_pipeline import AnnotationPipeline
from backend.ai_providers.gemini_provider import GeminiProvider
import os

# 1. 初始化管道
pipeline = AnnotationPipeline(
    output_dir="data/annotations",
    quality_threshold=65,        # 质量分数阈值
    auto_reject_threshold=55     # 自动拒绝阈值
)

# 2. 初始化AI提供者
ai_provider = GeminiProvider(
    api_key=os.getenv("GEMINI_API_KEY"),
    model_name="gemini-2.0-flash-exp"
)

# 3. 执行两阶段标注
result = pipeline.annotate_with_quality_check(
    video_path="data/videos/example.mp4",
    ai_provider=ai_provider
)

# 4. 查看结果
print(f"Status: {result['status']}")
if result['status'] == 'completed':
    print("✓ Annotation successful!")
    print(f"Quality Score: {result['quality_assessment']['overall_score']}")
elif result['status'] == 'rejected':
    print("✗ Video rejected")
    print(f"Reasons: {result['rejection_info']['reasons']}")
```

### 批量标注示例

```python
from pathlib import Path

# 获取所有视频
video_dir = Path("data/videos")
video_paths = list(video_dir.glob("*.mp4"))

# 批量处理
results = pipeline.batch_annotate(
    video_paths=[str(p) for p in video_paths],
    ai_provider=ai_provider,
    max_concurrent=3,           # 并发数（控制API调用速率）
    force_annotate=False        # False=启用质量检查
)

# 统计结果
for result in results:
    status = result['status']
    video_name = Path(result['video_path']).name
    print(f"{video_name}: {status}")
```

---

## 📊 质量评估标准

### 评估维度

| 维度 | 阈值 | 权重 | 说明 |
|------|------|------|------|
| **Observable Behavior** | ≥60 | 35% | 是否有清晰可见的人类行为 |
| **Psychological Value** | ≥55 | 35% | 是否能推断心理状态 |
| **Annotation Feasibility** | ≥50 | 20% | 视频质量和时长是否适合 |
| **Research Ethics** | ≥70 | 10% | 内容是否符合研究伦理 |

### 决策逻辑

```python
if overall_score >= 65 and all_thresholds_pass:
    action = "PROCEED_FULL_ANNOTATION"  # 进入完整标注
elif 55 <= overall_score < 65:
    action = "BORDERLINE_MANUAL_REVIEW"  # 人工复审
elif overall_score < 55:
    action = "REJECT_LOW_QUALITY"        # 自动拒绝
elif ethics_score < 70:
    action = "REJECT_INAPPROPRIATE"      # 伦理拒绝
```

### 示例评分

**✅ 高质量视频 (Score: 87)**
```json
{
  "observable_behavior": 92,  // 多人，清晰表情
  "psychological_value": 88,   // 复杂情绪转变
  "annotation_feasibility": 85, // 高清，45秒
  "research_ethics": 95         // 完全合规
}
→ PROCEED_FULL_ANNOTATION
```

**❌ 低质量视频 (Score: 28)**
```json
{
  "observable_behavior": 10,   // 无人类
  "psychological_value": 15,   // 无心理内容
  "annotation_feasibility": 70, // 技术质量尚可
  "research_ethics": 95         // 无伦理问题
}
→ REJECT_LOW_QUALITY (风景视频)
```

---

## 📁 输出文件结构

```
data/annotations/
├── quality_assessments/          # 质量评估结果
│   ├── video001_quality.json
│   ├── video002_quality.json
│   └── ...
├── full_annotations/              # 完整标注结果
│   ├── video001_annotation.json
│   ├── video003_annotation.json   # 仅通过预审的视频
│   └── ...
├── rejected_videos.json           # 被拒绝的视频日志
└── borderline_videos.json         # 边界情况日志
```

### rejected_videos.json 结构

```json
{
  "metadata": {
    "created_at": "2025-01-15T10:00:00Z",
    "last_updated": "2025-01-15T15:30:00Z",
    "total_count": 45,
    "log_type": "rejected"
  },
  "statistics": {
    "No human subjects present in the video": 18,
    "Video quality makes behavioral observation impossible": 12,
    "Content is pure landscape footage": 8,
    "Duration < 2 seconds": 7
  },
  "videos": [
    {
      "video_id": "landscape_001",
      "video_path": "data/videos/landscape_001.mp4",
      "logged_at": "2025-01-15T11:05:00Z",
      "quality_assessment": {
        "is_suitable": false,
        "overall_score": 28,
        "rejection_reasons": [
          "No human subjects present in the video",
          "Content is pure landscape footage"
        ],
        "brief_content_summary": "Aerial drone footage of mountains",
        ...
      }
    }
  ]
}
```

---

## 🔧 配置选项

### AnnotationPipeline 参数

```python
pipeline = AnnotationPipeline(
    # 输出目录
    output_dir="data/annotations",

    # 日志文件路径（可选，默认在output_dir下）
    rejected_log_path="data/logs/rejected.json",
    borderline_log_path="data/logs/borderline.json",

    # 质量阈值配置
    quality_threshold=65,        # 通过标准（建议: 60-70）
    auto_reject_threshold=55     # 自动拒绝线（建议: 50-60）
)
```

### 阈值调优建议

| 场景 | quality_threshold | auto_reject_threshold |
|------|-------------------|------------------------|
| **高质量数据集** | 70 | 60 | 仅接受高质量视频 |
| **平衡模式** (推荐) | 65 | 55 | 质量与数量平衡 |
| **快速收集** | 60 | 50 | 优先数量 |

---

## 📈 统计分析

### 查看管道统计

```python
# 获取统计信息
stats = pipeline.get_statistics()

print(json.dumps(stats, indent=2))
```

**输出示例:**
```json
{
  "rejected": {
    "No human subjects present": 18,
    "Low video quality": 12,
    "Too short duration": 7
  },
  "rejected_count": 45,
  "borderline": {
    "borderline_case": 12
  },
  "borderline_count": 12,
  "total_processed": 57,
  "rejection_rate": 0.789
}
```

### 分析拒绝原因

通过查看 `rejected_videos.json` 的统计数据，可以：

1. **优化搜索策略**: 如果大量视频因"无人类"被拒绝，调整搜索关键词
2. **调整过滤器**: 根据时长统计优化duration过滤
3. **改进下载配置**: 根据质量问题调整yt-dlp参数

---

## 🎨 高级用法

### 1. 跳过质量检查（强制标注）

```python
# 对已知高质量视频，跳过Stage 1直接标注
result = pipeline.annotate_with_quality_check(
    video_path="curated_video.mp4",
    ai_provider=ai_provider,
    force_annotate=True  # 跳过质量检查
)
```

### 2. 仅执行质量评估

```python
# 只评估质量，不执行完整标注
assessment = pipeline.assess_video_quality(
    video_path="test_video.mp4",
    ai_provider=ai_provider,
    save_result=True
)

print(f"Score: {assessment['overall_score']}")
print(f"Action: {assessment['recommended_action']}")
```

### 3. 自定义AI提供者

```python
# 使用OpenAI替代Gemini
from backend.ai_providers.openai_provider import OpenAIProvider

ai_provider = OpenAIProvider(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="gpt-4-vision-preview"
)

result = pipeline.annotate_with_quality_check(
    video_path="video.mp4",
    ai_provider=ai_provider
)
```

---

## 🔍 调试与排错

### 启用详细日志

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG查看详细信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 常见问题

**Q1: 所有视频都被拒绝怎么办？**
```python
# 检查阈值是否过严
stats = pipeline.get_statistics()
print(f"Rejection rate: {stats['rejection_rate']}")

# 如果 > 0.8，考虑降低阈值
pipeline.quality_threshold = 60
pipeline.auto_reject_threshold = 50
```

**Q2: 质量评估结果不准确？**
```python
# 检查评估结果
assessment = pipeline.assess_video_quality(
    video_path="problem_video.mp4",
    ai_provider=ai_provider
)

# 查看详细评分
print(assessment['criteria_scores'])
print(assessment['rejection_reasons'])

# 如果AI评估不合理，可以使用force_annotate跳过
```

**Q3: JSON解析错误？**
```python
# AI返回的JSON可能包含markdown，pipeline会自动处理
# 如果仍有问题，检查AI返回的原始文本
try:
    result = pipeline.annotate_with_quality_check(...)
except json.JSONDecodeError as e:
    print(f"JSON Error: {e}")
    # 检查 quality_assessments/ 目录中的原始输出
```

---

## 📚 相关文档

- [Prompt设计指南](./prompts/README.md)
- [批量标注脚本](../scripts/batch_annotate.py)
- [数据集质量控制](./QUALITY_CONTROL.md)

---

## 🤝 贡献

发现问题或有改进建议？欢迎提交Issue或Pull Request！

---

**License:** MIT
**Project:** Desire-VQA Theory of Mind Video Dataset
