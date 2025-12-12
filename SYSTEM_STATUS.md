# 📊 系统现状总结

## ✅ 已完成的工作

### 1. 发布包系统 ✅
位置：`release_packages/` 和 `scripts/build_release.py`

**功能**：
- ✅ 轻量版和完整版的发布包模板
- ✅ 自动构建脚本（一键打包）
- ✅ 完整的 README 和使用文档
- ✅ 快速启动脚本

**使用方法**：
```bash
# 构建发布包
python scripts/build_release.py --version both

# 输出位置
releases/video_annotation_v3_lite_YYYYMMDD.zip
releases/video_annotation_full_YYYYMMDD.zip
```

详见：[RELEASE_NOTES.md](RELEASE_NOTES.md)

---

### 2. VQA 处理系统 ✅（新增！）
位置：`backend/vqa_processor.py`

**功能**：
- ✅ 从 V3 标注中提取时间区间
- ✅ 根据标注生成问题
- ✅ 自动截取视频片段（包含上下文）
- ✅ 提取连续关键帧序列
- ✅ 生成完整的 VQA 数据包

**工作流程**：
```
视频标注（V3）
    ↓
提取时间区间（desire 转变的前后几秒）
    ↓
生成问题（"为什么发生转变？"）
    ↓
截取视频片段（10s-18s 的连续内容）
    ↓
VQA 数据（问题 + 片段 + 答案提示）
```

**使用方法**：
```bash
# 第一步：V3 标注视频
python scripts/annotate_with_v3.py data/videos/your_video.mp4

# 第二步：生成 VQA 数据
python backend/vqa_processor.py \
    data/videos/your_video.mp4 \
    data/annotations_v3/your_video.json

# 输出：
# - data/vqa/questions/your_video_vqa.json  # 问题数据
# - data/vqa/video_clips/*.mp4              # 视频片段
# - data/vqa/frame_sequences/*/             # 关键帧序列
```

详见：[doc/VQA_WORKFLOW.md](doc/VQA_WORKFLOW.md)

---

### 3. 连续关键帧提取策略 ✅（新增！）
位置：`backend/keyframe_strategy.py`

**功能**：
- ✅ 混合策略：固定间隔 + AI 关键帧
- ✅ 上下文感知：关键时刻前后补充帧
- ✅ 密集采样：高连续性
- ✅ 智能去重和限制数量

**三种策略对比**：

| 策略 | 适用场景 | 帧数 | 连续性 |
|------|----------|------|--------|
| 混合策略 | 日常标注 | 8-12 | 高 |
| 上下文感知 | VQA/问答 | 10-15 | 极高 |
| 密集采样 | 详细分析 | 15-20 | 最高 |

**使用方法**（在标注时自动应用）：
```python
from backend.keyframe_strategy import ContinuousFrameExtractor

# 使用混合策略提取
extracted = ContinuousFrameExtractor.extract_with_strategy(
    video_path,
    ai_timestamps=[5, 15, 30],  # AI 建议的关键时刻
    output_dir,
    strategy="hybrid",  # 或 "context_aware", "dense"
    base_interval=8.0   # 基础间隔
)
```

---

## 🎯 你当前的需求

### 场景：Video Question Answering

**你的工作流程**：
1. ✅ 从 YouTube 下载视频（已完成，有 AI 审核）
2. ✅ 使用 V3 标注视频（AI 看完整视频）
3. ✅ 根据标注生成问题（如："哪里发生了 desire 转变？"）
4. ✅ **关键**：给 AI 看那一段的**连续内容**，而不是单帧
5. ✅ AI 回答问题

### 解决方案：VQA 处理系统

**完美匹配你的需求**！

```bash
# 步骤 1: 标注（AI 看完整视频，生成高质量标注）
python scripts/annotate_with_v3.py data/videos/youtube_001.mp4
# 输出：data/annotations_v3/youtube_001.json
# 包含：desire 转变、属性变化、时间戳等

# 步骤 2: 生成 VQA 数据（自动提取连续片段）
python backend/vqa_processor.py \
    data/videos/youtube_001.mp4 \
    data/annotations_v3/youtube_001.json
# 输出：
# - 问题列表（JSON）
# - 视频片段（desire 转变的前后几秒）⭐
# - 关键帧序列（连续的帧）⭐

# 步骤 3: 使用片段进行问答
# 你的 VQA 脚本可以读取片段，给 AI 看
```

**关键优势**：
- ✅ AI 看到的是**连续的视频片段**（10s-18s），不是单帧
- ✅ 包含**上下文**（desire 转变前后的画面）
- ✅ **自动化**：从标注自动提取时间区间
- ✅ API **成本低**：只传片段，不是完整视频

---

## 📂 系统目录结构

```
video_anno/
├── backend/
│   ├── vqa_processor.py            # ⭐ VQA 处理器（新增）
│   ├── keyframe_strategy.py        # ⭐ 关键帧策略（新增）
│   ├── annotation_schema_v3.py     # V3 标注格式
│   ├── vlm_analyzer.py             # AI 分析器
│   └── ...
│
├── scripts/
│   ├── annotate_with_v3.py         # V3 标注脚本
│   ├── build_release.py            # 发布包构建
│   └── ...
│
├── doc/
│   └── VQA_WORKFLOW.md             # ⭐ VQA 完整流程文档（新增）
│
├── release_packages/
│   ├── v3_lite/                    # 轻量版模板
│   ├── full_version/               # 完整版模板
│   ├── QUICK_START.md              # 快速入门
│   ├── DISTRIBUTION_GUIDE.md       # 发布指南
│   └── SUMMARY.md                  # 发布包总结
│
├── data/
│   ├── videos/                     # 原始视频
│   ├── annotations_v3/             # V3 标注
│   └── vqa/                        # ⭐ VQA 数据（新）
│       ├── questions/              #    问题列表
│       ├── video_clips/            #    视频片段⭐
│       └── frame_sequences/        #    关键帧序列⭐
│
├── RELEASE_NOTES.md                # 发布包说明
├── SYSTEM_STATUS.md                # 本文件
└── ...
```

---

## 🚀 快速开始（针对你的需求）

### 方案：完整 VQA 流程

```bash
# ========== 步骤 1: 批量标注 YouTube 视频 ==========
# 将审核过的 YouTube 视频放入 data/videos/

# 批量标注（V3 格式）
for video in data/videos/*.mp4; do
    python scripts/annotate_with_v3.py "$video"
done

# 输出：data/annotations_v3/*.json

# ========== 步骤 2: 生成 VQA 数据 ==========
# 对每个标注生成 VQA 数据

for video in data/videos/*.mp4; do
    video_id=$(basename "$video" .mp4)
    python backend/vqa_processor.py \
        "$video" \
        "data/annotations_v3/${video_id}.json"
done

# 输出：
# - data/vqa/questions/*.json          # 问题
# - data/vqa/video_clips/*.mp4         # 视频片段
# - data/vqa/frame_sequences/*/        # 关键帧序列

# ========== 步骤 3: 使用 VQA 数据 ==========
# 编写你的 VQA 脚本
# 读取问题 → 加载视频片段 → 给 AI → 获得答案
```

### 示例：回答一个问题

```python
import json
import google.generativeai as genai
from pathlib import Path

# 1. 加载 VQA 数据
with open('data/vqa/questions/youtube_001_vqa.json') as f:
    vqa_data = json.load(f)

# 2. 选择一个问题
question = vqa_data['questions'][0]
print(f"问题: {question['question']}")
print(f"时间: {question['time_span']['start']:.1f}s - {question['time_span']['end']:.1f}s")

# 3. 上传对应的视频片段（只有几秒）
video_clip = genai.upload_file(question['video_clip_path'])

# 等待处理
import time
while video_clip.state.name == "PROCESSING":
    time.sleep(2)
    video_clip = genai.get_file(video_clip.name)

# 4. 提问
model = genai.GenerativeModel('gemini-2.0-flash')
response = model.generate_content([
    video_clip,
    f"问题：{question['question']}\n\n请基于视频内容详细回答。"
])

print(f"\nAI 回答: {response.text}")
```

**AI 看到的**：
- 不是单帧图片
- 不是完整视频（30秒）
- 而是：**desire 转变那一段的连续视频**（10s-18s，包含前后上下文）

---

## 🔧 系统配置建议

### 针对 YouTube 视频标注

#### 1. 标注阶段配置

```env
# .env 文件
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash  # 推荐，速度快+质量好
```

#### 2. VQA 生成配置

```bash
# 如果预算充足，提取视频片段（有音频）
python backend/vqa_processor.py video.mp4 annotation.json

# 如果预算有限，只提取关键帧
python backend/vqa_processor.py video.mp4 annotation.json --no-clips

# 自定义上下文窗口（修改 vqa_processor.py）
'start': max(0, start - 3.0),  # 前3秒
'end': end + 2.0,               # 后2秒
```

#### 3. 关键帧策略配置

```python
# 在 backend/keyframe_strategy.py 中
# 使用"上下文感知"策略，最适合 VQA
KeyframeStrategy.generate_continuous_timestamps(
    duration,
    ai_timestamps,
    strategy="context_aware",  # 上下文感知
    context_window=3.0         # 前后各3秒
)
```

---

## 📊 预期效果

### 输入：1 个 30秒的 YouTube 视频

### 输出：

| 项目 | 数量/大小 |
|------|----------|
| V3 标注文件 | 1 个 JSON（约 50KB） |
| 时间区间 | 3-5 个 |
| VQA 问题 | 12-20 个 |
| 视频片段 | 12-20 个（每个 5-8秒） |
| 关键帧序列 | 12-20 个目录（每个 3-5 帧） |
| 总大小 | 原视频的 30-50% |

### 质量对比：

| 方式 | AI 看到什么 | 能否理解 desire 转变？ |
|------|-------------|------------------------|
| ❌ 传统单帧 | 15s 的一张图 | ❌ 不能，缺少前因后果 |
| ❌ 完整视频 | 0-30s 全部内容 | ✅ 能，但 API 成本高 |
| ✅ VQA 片段 | 10s-18s 连续片段 | ✅ 能，成本低，效果好 ⭐ |

---

## 💡 推荐工作流程

### 第一次处理（小批量测试）

```bash
# 1. 测试单个视频
python scripts/annotate_with_v3.py data/videos/test_video.mp4

# 2. 生成 VQA 数据
python backend/vqa_processor.py \
    data/videos/test_video.mp4 \
    data/annotations_v3/test_video.json

# 3. 检查输出
# - 查看问题：cat data/vqa/questions/test_video_vqa.json
# - 查看片段：ls data/vqa/video_clips/
# - 查看帧序列：ls data/vqa/frame_sequences/

# 4. 确认效果满意后，批量处理
```

### 批量处理（正式生产）

```bash
# 创建批量处理脚本
cat > batch_process.sh << 'EOF'
#!/bin/bash
for video in data/videos/*.mp4; do
    video_id=$(basename "$video" .mp4)

    echo "处理: $video_id"

    # V3 标注
    if [ ! -f "data/annotations_v3/${video_id}.json" ]; then
        python scripts/annotate_with_v3.py "$video"
    fi

    # VQA 生成
    if [ ! -f "data/vqa/questions/${video_id}_vqa.json" ]; then
        python backend/vqa_processor.py \
            "$video" \
            "data/annotations_v3/${video_id}.json"
    fi

    echo "完成: $video_id"
    echo "---"
done
EOF

chmod +x batch_process.sh
./batch_process.sh
```

---

## 🎉 总结

### 当前系统状态：✅ 完全满足你的需求

你需要的功能：
- ✅ V3 标注（AI 看完整视频，生成高质量标注）
- ✅ 提取时间区间（desire 转变的位置）
- ✅ 生成问题
- ✅ **关键**：截取连续视频片段（包含上下文）
- ✅ 给 AI 看片段 + 问题 → 回答

### 系统已具备：

1. ✅ **V3 标注系统** - 对完整视频进行标注
2. ✅ **VQA 处理器** - 自动提取时间区间 + 生成问题 + 截取片段
3. ✅ **连续关键帧策略** - 确保帧的连续性（如需使用帧而非视频）
4. ✅ **完整文档** - VQA 工作流程、使用示例、最佳实践

### 下一步：

```bash
# 1. 开始标注你的 YouTube 视频
python scripts/annotate_with_v3.py data/videos/your_first_video.mp4

# 2. 生成 VQA 数据
python backend/vqa_processor.py \
    data/videos/your_first_video.mp4 \
    data/annotations_v3/your_first_video.json

# 3. 查看生成的问题和片段
cat data/vqa/questions/your_first_video_vqa.json

# 4. 编写你的 VQA 脚本，使用这些数据！
```

**你的想法完全正确，系统已经完美支持！** 🎉

有任何问题随时告诉我！
