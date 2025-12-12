# 🎯 Video Question Answering 完整工作流程

从视频标注到问答数据集的完整流程。

---

## 📋 工作流程概览

```
第一阶段：视频标注
data/videos/video_001.mp4
    ↓ [V3 标注]
data/annotations_v3/video_001.json
    ↓ [记录时间区间 + desire 转变]
包含完整的标注信息

第二阶段：VQA 数据生成
data/annotations_v3/video_001.json
    ↓ [提取时间区间]
找到关键时刻（如：12s-18s 发生 desire 转变）
    ↓ [生成问题]
"为什么人物A的 desire 发生了转变？"
    ↓ [截取视频片段]
提取 12s-18s 的视频片段（或连续关键帧）
    ↓ [保存 VQA 数据]
data/vqa/video_001_vqa.json + video_clips/ + frame_sequences/

第三阶段：模型问答
VQA 数据 + 视频片段/帧序列
    ↓ [给 AI 看片段 + 问题]
AI 观看 12s-18s 的连续内容
    ↓ [AI 回答]
"因为接到了批评电话，从追求成就感转变为寻求安全感"
```

---

## 🚀 使用步骤

### 步骤 1: 标注视频（V3 格式）

```bash
# 使用 V3 标注视频（AI 看完整视频）
python scripts/annotate_with_v3.py data/videos/video_001.mp4

# 输出：data/annotations_v3/video_001.json
# 包含：
# - 场景描述
# - 人物描述
# - 属性变化（desire 转变）⭐ 关键
# - 开放式推断
# - 行为序列（包含时间戳）⭐ 关键
```

**关键**：确保标注中包含时间信息！
- `observable_behaviors` 字段要有 `timestamp`
- `open_inferences` 的 `supporting_evidence` 要能关联到行为

### 步骤 2: 生成 VQA 数据

```bash
# 从标注生成 VQA 数据（自动提取片段）
python backend/vqa_processor.py \
    data/videos/video_001.mp4 \
    data/annotations_v3/video_001.json

# 输出：
# 1. data/vqa/questions/video_001_vqa.json  # 问题数据
# 2. data/vqa/video_clips/*.mp4             # 视频片段
# 3. data/vqa/frame_sequences/*/            # 关键帧序列
```

**输出内容**：

```json
{
  "video_id": "video_001",
  "questions": [
    {
      "id": "inference_0_why",
      "question": "为什么人物A的焦虑水平上升？",
      "time_span": {
        "start": 12.0,  // 包含前2秒上下文
        "end": 18.0,    // 包含后1秒上下文
        "key_moment": 15.2
      },
      "video_clip_path": "data/vqa/video_clips/video_001_inference_0_why.mp4",
      "frame_sequence_dir": "data/vqa/frame_sequences/video_001_inference_0_why/",
      "answer_hint": "因为接到催促电话，压力增加"
    }
  ]
}
```

### 步骤 3: 使用 VQA 数据

#### 选项 A: 给 AI 看视频片段（推荐）⭐

```python
import google.generativeai as genai

# 1. 加载 VQA 数据
with open('data/vqa/questions/video_001_vqa.json') as f:
    vqa_data = json.load(f)

# 2. 遍历问题
for question in vqa_data['questions']:
    # 上传视频片段（只有几秒，不是完整视频）
    video_clip = genai.upload_file(question['video_clip_path'])

    # 等待处理
    while video_clip.state.name == "PROCESSING":
        time.sleep(2)
        video_clip = genai.get_file(video_clip.name)

    # 提问
    prompt = f"""
    请观看这段视频片段（{question['time_span']['start']:.1f}s - {question['time_span']['end']:.1f}s）

    问题：{question['question']}

    请基于视频内容详细回答。
    """

    response = model.generate_content([video_clip, prompt])

    print(f"Q: {question['question']}")
    print(f"A: {response.text}")
    print()
```

**优点**：
- ✅ AI 看到连续的视频片段（有音频）
- ✅ 上下文完整（包含前后几秒）
- ✅ API 成本低（只传片段，不是完整视频）

#### 选项 B: 给 AI 看关键帧序列（成本更低）

```python
# 1. 读取帧序列
frame_dir = Path(question['frame_sequence_dir'])
frames = sorted(frame_dir.glob('*.jpg'))

# 2. 上传帧序列
uploaded_frames = [genai.upload_file(str(f)) for f in frames]

# 3. 提问
prompt = f"""
这是一段视频的连续关键帧序列（{len(frames)} 帧）
时间范围：{question['time_span']['start']:.1f}s - {question['time_span']['end']:.1f}s

问题：{question['question']}

请基于这些帧回答。
"""

response = model.generate_content(uploaded_frames + [prompt])
```

**优点**：
- ✅ API 成本更低（传图片）
- ✅ 处理更快
- ❌ 没有音频信息

---

## 📊 VQA 数据示例

### 输入：标注数据（V3 格式）

```json
{
  "video_id": "conversation_001",
  "duration": 30.5,

  "characters": [
    {
      "character_id": "A",
      "attribute_changes": [
        {
          "attribute_name": "焦虑水平",
          "direction": "上升",
          "start_level": "中",
          "end_level": "高",
          "evidence": [
            "语速加快",
            "手不停摆弄物品",
            "眉头紧锁"
          ]
        }
      ]
    }
  ],

  "observable_behaviors": [
    {
      "timestamp": "0:12",  // ← 关键：时间戳
      "character_id": "A",
      "detailed_description": "接听电话，面部表情突然变化"
    },
    {
      "timestamp": "0:15",
      "character_id": "A",
      "detailed_description": "放下电话后开始来回踱步"
    }
  ],

  "open_inferences": [
    {
      "inference_aspect": "人物A的焦虑转变",
      "conclusion": "从平静状态转为高度焦虑",
      "supporting_evidence": [
        "接电话后表情变化",
        "语速明显加快",
        "肢体动作增多"
      ]
    }
  ]
}
```

### 输出：VQA 数据

```json
{
  "video_id": "conversation_001",
  "time_spans": [
    {
      "id": "attr_change_0_0",
      "aspect": "A: 焦虑水平的上升",
      "start": 10.0,   // 12s - 2s（前置上下文）
      "end": 18.0,     // 17s + 1s（后置上下文）
      "key_moment": 14.5,
      "conclusion": "从中等变为高",
      "evidence": ["语速加快", "手不停摆弄物品", "眉头紧锁"]
    }
  ],

  "questions": [
    {
      "id": "attr_change_0_0_why",
      "question": "为什么A: 焦虑水平的上升？",
      "question_type": "why",
      "time_span": {
        "start": 10.0,
        "end": 18.0,
        "key_moment": 14.5
      },
      "video_clip_path": "data/vqa/video_clips/conversation_001_attr_change_0_0_why.mp4",
      "frame_sequence_dir": "data/vqa/frame_sequences/conversation_001_attr_change_0_0_why/",
      "frame_count": 5,
      "answer_hint": "从中等变为高。证据：语速加快, 手不停摆弄物品, 眉头紧锁"
    }
  ]
}
```

### AI 看到的内容

**视频片段**（10s-18s，共8秒）：
```
[10s] 人物A平静地坐在桌前
[12s] 接听电话 ← 关键时刻前
[14.5s] 表情突变，开始焦虑 ← 关键转折点
[15s] 放下电话，开始踱步
[17s] 语速加快，手势增多
[18s] 持续焦虑状态 ← 关键时刻后
```

**或关键帧序列**：
```
frame_000_t10.00s.jpg  (转变前)
frame_001_t12.00s.jpg  (接电话)
frame_002_t14.00s.jpg  (关键时刻)
frame_003_t16.00s.jpg  (转变中)
frame_004_t18.00s.jpg  (转变后)
```

AI 能够看到**完整的故事**：
- ✅ 为什么焦虑（接电话）
- ✅ 如何焦虑（表情、动作变化）
- ✅ 焦虑后的状态（踱步、手势）

---

## 🔧 高级配置

### 自定义时间区间

如果自动提取的时间区间不准确，可以手动修改标注：

```json
{
  "open_inferences": [
    {
      "inference_aspect": "desire 转变",
      "conclusion": "从追求成就感转为寻求安全感",

      // ✅ 手动添加时间区间
      "time_span": {
        "start": 10.0,
        "end": 20.0,
        "key_moment": 15.2
      }
    }
  ]
}
```

然后 VQA 处理器会优先使用这个手动指定的区间。

### 调整上下文窗口

```bash
# 修改 vqa_processor.py 中的默认值
# 前置上下文：从 2秒 改为 3秒
'start': max(0, start - 3.0),

# 后置上下文：从 1秒 改为 2秒
'end': end + 2.0,
```

### 调整帧密度

```bash
# 修改帧间隔（默认 2秒一帧）
frame_paths = self.extract_frame_sequence(
    video_path,
    span['start'],
    span['end'],
    clip_name,
    interval=1.0  # 改为 1秒一帧，更密集
)
```

---

## 📝 最佳实践

### 1. 标注阶段

**确保记录时间信息**：
- ✅ 每个 `observable_behavior` 都要有 `timestamp`
- ✅ 时间戳格式：`"0:15"` 或 `"0:12-0:18"`（区间）

**示例标注**：
```json
{
  "observable_behaviors": [
    {
      "timestamp": "0:12",  // ✅ 明确的时间戳
      "character_id": "A",
      "behavior_category": "表情变化",
      "detailed_description": "接电话后面部表情突然僵硬"
    }
  ]
}
```

### 2. VQA 生成阶段

**选择合适的提取方式**：
- 预算充足 → 提取视频片段（有音频）
- 预算有限 → 提取关键帧序列

```bash
# 只提取视频片段
python backend/vqa_processor.py video.mp4 annotation.json --no-frames

# 只提取关键帧
python backend/vqa_processor.py video.mp4 annotation.json --no-clips

# 两者都提取（默认）
python backend/vqa_processor.py video.mp4 annotation.json
```

### 3. 问答阶段

**构造清晰的 Prompt**：

```python
prompt = f"""
视频片段信息：
- 时间范围：{start:.1f}s - {end:.1f}s
- 场景：{scene_description}
- 人物：{characters}

问题：{question}

回答要求：
1. 基于视频中可观察的行为
2. 说明推理过程
3. 指出关键证据（动作、表情、语气等）
"""
```

---

## 🎯 完整示例

```bash
# ========== 步骤 1: 标注视频 ==========
python scripts/annotate_with_v3.py data/videos/conversation.mp4
# 输出：data/annotations_v3/conversation.json

# ========== 步骤 2: 生成 VQA 数据 ==========
python backend/vqa_processor.py \
    data/videos/conversation.mp4 \
    data/annotations_v3/conversation.json

# 输出：
# - data/vqa/questions/conversation_vqa.json
# - data/vqa/video_clips/conversation_*.mp4
# - data/vqa/frame_sequences/conversation_*/

# ========== 步骤 3: 使用 VQA 数据 ==========
# 编写你的 VQA 脚本，读取问题并让 AI 回答
python scripts/run_vqa.py data/vqa/questions/conversation_vqa.json
```

---

## 💡 常见问题

### Q1: 时间区间提取不准确怎么办？

**A**: 手动在标注中添加 `time_span` 字段：

```json
{
  "open_inferences": [
    {
      "inference_aspect": "...",
      "conclusion": "...",
      "time_span": {  // ← 手动指定
        "start": 10.0,
        "end": 20.0
      }
    }
  ]
}
```

### Q2: 视频片段太短，看不懂上下文？

**A**: 调整上下文窗口：

```python
# 在 vqa_processor.py 中
'start': max(0, start - 5.0),  # 增加到前5秒
'end': end + 3.0,               # 增加到后3秒
```

### Q3: 关键帧太稀疏，画面不连贯？

**A**: 降低帧间隔：

```python
frame_paths = self.extract_frame_sequence(
    ...,
    interval=1.0  # 从 2秒 改为 1秒
)
```

### Q4: 想给 AI 看完整视频而不是片段？

**A**: 不需要 VQA 处理器，直接用 V3 标注：

```python
# V3 标注已经是基于完整视频的
# 问题直接基于标注内容生成即可
```

---

## 📊 数据统计

一个 30秒视频的预期输出：

| 项目 | 数量 |
|------|------|
| 时间区间 | 3-5 个 |
| 生成问题 | 12-20 个（每个区间4种问题） |
| 视频片段 | 12-20 个（每个约 5-8 秒） |
| 关键帧序列 | 12-20 个（每个约 3-5 帧） |

预计磁盘占用：
- 视频片段：原视频的 30-50%
- 关键帧：约 5-10MB

---

## 🚀 总结

**你的工作流程现在是**：

1. ✅ V3 标注视频（AI 看完整视频）
2. ✅ VQA 处理器自动提取时间区间
3. ✅ 生成问题 + 截取视频片段/帧序列
4. ✅ 给 AI 看片段 + 问题 → 获得答案

**核心优势**：
- ✅ AI 看到的是**连续的上下文**，不是孤立的单帧
- ✅ 包含转折**前后**的画面，能理解因果
- ✅ API 成本低（只传片段，不是完整视频）
- ✅ 自动化程度高

开始你的 VQA 标注之旅！🎉
