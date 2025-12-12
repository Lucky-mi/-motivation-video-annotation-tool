# 🎬 Theory of Mind 视频标注系统 V3（轻量版）

基于 AI 的视频心理动机标注系统，专注于分析视频中人物的动机、渴望和心理状态。

## ✨ 特点

- ✅ **AI 自动分析**：使用 Google Gemini 3.0 自动分析视频内容
- ✅ **属性动态标注**：记录人物属性（情绪、信任度、焦虑等）的上升/下降变化
- ✅ **开放式推断**：不使用固定标签，而是进行开放式心理学推理
- ✅ **Theory of Mind**：基于心智理论进行深度心理分析
- ✅ **完整视频支持**：保留音频信息，用于多模态分析
- ✅ **纯净视频筛选**：自动识别无字幕、特效的原始视频

## 🎯 标注内容

系统会对视频进行以下维度的标注：

### 1. 场景描述
- 地点和环境
- 社交情境
- 氛围（紧张、轻松、冲突等）
- 关键物品

### 2. 人物描述
- 外观特征
- 初始/最终状态
- 在互动中的角色
- **属性变化**（核心功能）

### 3. 属性变化（重要！）
记录可观察的心理/情绪属性变化，例如：
- 愤怒程度：上升 ↑
- 信任度：下降 ↓
- 焦虑水平：上升 ↑
- 警惕性：保持 →

每个属性变化都包含：
- 变化方向（上升/下降/保持/波动）
- 起始和结束水平（高/中/低）
- 行为证据（表情、动作、语气）
- 确定性（高/中/低）

### 4. 行为序列
按时间顺序记录：
- 表情变化
- 肢体动作
- 眼神交流
- 语气变化
- 身体距离
- 对话内容

### 5. 开放式推断
模型的自由心理推理，包括：
- 人物的真实意图
- 情感状态的复杂性
- 人物对他人的看法
- 信念和假设
- 动机和渴望
- 隐藏信息

每个推断包含：
- 详细的推理过程
- 支持证据
- 确定性评估
- 其他可能的解释

### 6. 心理学知识应用
参考的主流心理学概念：
- 虚假信念（False Belief）
- 意图隐藏（Intention Concealment）
- 情绪调节（Emotion Regulation）
- 社会参照（Social Referencing）
- 情绪感染（Emotional Contagion）
- 归因偏差（Attribution Bias）
- 去中心化（Decentering）
- 心智化（Mentalization）

## 📋 系统要求

- **Python**: 3.8 或更高版本
- **内存**: 建议 8GB 以上
- **API Key**: Google Gemini API Key（必须）
- **操作系统**: Windows / Linux / macOS

## 🚀 快速开始

### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 2: 配置 API Key

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的 Gemini API Key：
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

> 💡 **如何获取 API Key?**
>
> 访问 [Google AI Studio](https://makersuite.google.com/app/apikey) 免费申请

### 步骤 3: 准备视频

将待标注的视频放入 `data/videos/` 目录：

```bash
mkdir -p data/videos
cp your_video.mp4 data/videos/
```

### 步骤 4: 运行标注

```bash
python scripts/annotate_with_v3.py data/videos/your_video.mp4
```

### 步骤 5: 查看结果

标注结果保存在 `data/annotations_v3/your_video.json`

## 📖 使用示例

### 基础用法

```bash
# 标注单个视频
python scripts/annotate_with_v3.py data/videos/conversation.mp4

# 指定输出路径
python scripts/annotate_with_v3.py data/videos/conversation.mp4 \
    --output results/my_annotation.json

# 指定视频 ID
python scripts/annotate_with_v3.py data/videos/conversation.mp4 \
    --video-id "conversation_001"
```

### 输出示例

标注结果是一个 JSON 文件，结构如下：

```json
{
  "video_id": "conversation_001",
  "video_path": "data/videos/conversation.mp4",
  "duration": 45.2,
  "is_clean_video": true,

  "scene": {
    "location": "办公室会议室",
    "atmosphere": "紧张对立",
    "social_context": "工作场合的冲突讨论"
  },

  "characters": [
    {
      "character_id": "A",
      "appearance": "30岁左右男性，西装，站立姿态",
      "initial_state": "自信、主导性强",
      "final_state": "防御、不安",
      "attribute_changes": [
        {
          "attribute_name": "自信心",
          "direction": "下降",
          "start_level": "高",
          "end_level": "中",
          "evidence": [
            "语速变快，出现停顿",
            "眼神开始回避",
            "手势从张开变为收紧"
          ],
          "confidence": "高"
        }
      ]
    }
  ],

  "observable_behaviors": [
    {
      "timestamp": "0:05-0:10",
      "character_id": "A",
      "behavior_category": "肢体动作",
      "detailed_description": "双手张开，向前指向对方，显示主导性",
      "intensity": "强"
    }
  ],

  "open_inferences": [
    {
      "inference_aspect": "人物A的真实意图与表面说辞的一致性",
      "reasoning_process": "虽然A口头上说'只是建议'，但其肢体语言（手指指向、身体前倾、打断对方）显示出强烈的控制欲...",
      "supporting_evidence": [
        "多次打断对方发言",
        "身体前倾侵入对方空间",
        "语气坚定不容置疑"
      ],
      "conclusion": "A表面说'只是建议'，实际是在施加压力要求对方服从",
      "confidence": "高",
      "alternative_interpretations": [
        "A可能确实认为自己只是建议，但沟通方式过于强势"
      ]
    }
  ]
}
```

## 📊 标注质量说明

### 输出的确定性

标注系统会为每个推断标注确定性等级：

- **高**：有明确的行为证据支持
- **中**：有一定证据，但存在其他解释可能
- **低**：基于微弱线索的推测

### 最佳实践

为了获得最佳标注质量：

1. **视频质量**：
   - 使用清晰度高的视频（480p 以上）
   - 避免有字幕、水印的视频
   - 人物面部清晰可见

2. **视频长度**：
   - 推荐 30 秒 - 3 分钟
   - 过长视频建议切分

3. **内容选择**：
   - 包含人际互动的场景
   - 有明显的情绪变化或冲突
   - 避免纯静态画面

## 🗂️ 目录结构

```
video_annotation_v3/
├── scripts/
│   └── annotate_with_v3.py       # 标注主程序
│
├── backend/
│   ├── annotation_schema_v3.py   # V3 数据结构
│   ├── vlm_analyzer.py           # AI 分析器
│   ├── models.py                 # 数据模型
│   ├── ai_providers/             # AI 接口封装
│   └── ...
│
├── config/
│   ├── config.py                 # 配置管理
│   └── config.yaml               # 配置文件
│
├── data/
│   ├── videos/                   # 输入：原始视频
│   ├── keyframes/                # 输出：关键帧图片（如需要）
│   └── annotations_v3/           # 输出：标注结果
│
├── .env                          # 环境变量（你的 API Key）
├── .env.example                  # 环境变量模板
├── requirements.txt              # Python 依赖
└── README.md                     # 本文件
```

## ⚙️ 高级配置

### 修改模型

编辑 `.env` 文件：

```env
# 使用更强大但更慢的模型
GEMINI_MODEL=gemini-1.5-pro

# 使用更快但质量稍低的模型（默认）
GEMINI_MODEL=gemini-2.0-flash
```

### 自定义输出目录

编辑 `config/config.yaml`：

```yaml
paths:
  videos: 'data/videos'
  keyframes: 'data/keyframes'
  annotations: 'data/annotations_v3'
```

## 🔧 故障排除

### 常见问题

**Q: 提示 API Key 错误？**

A: 检查 `.env` 文件是否正确配置，确保：
1. 文件名是 `.env`（不是 `.env.txt`）
2. API Key 正确复制（无多余空格）
3. API Key 有效且有足够配额

**Q: 视频处理失败？**

A: 可能原因：
1. 视频格式不支持 → 转换为 MP4
2. 视频损坏 → 使用其他视频测试
3. 视频过大 → 压缩或切分视频

**Q: 标注结果不准确？**

A: 改进方法：
1. 使用 `gemini-1.5-pro` 模型（更准确）
2. 确保视频清晰且人物面部可见
3. 选择互动性强的场景

**Q: 安装依赖出错？**

A: 尝试：
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像（中国用户）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 获取帮助

如遇到问题，请：
1. 查看错误日志
2. 确认依赖版本正确
3. 提供视频样本和错误信息

## 📚 数据格式说明

### V3 Schema

完整的 Schema 定义见 `backend/annotation_schema_v3.py`

核心数据模型：
- `VideoAnnotationV3`: 完整标注
- `SceneDescription`: 场景描述
- `CharacterDescription`: 人物描述
- `AttributeChange`: 属性变化（核心）
- `ObservableBehavior`: 可观察行为
- `OpenInference`: 开放式推断
- `PsychologyReference`: 心理学参考

## 🎓 心理学背景

本系统基于以下心理学理论：

### Theory of Mind（心智理论）
理解他人有独立的心智状态（信念、欲望、意图）的能力。

### 关键概念
- **虚假信念**：理解他人的信念可能与现实不符
- **意图隐藏**：识别表面行为与真实意图的差异
- **情绪调节**：观察个体如何控制情绪表达
- **心智化**：将行为理解为心理状态驱动的过程

## 📄 许可证

MIT License

## 🙏 致谢

- Google Gemini API
- OpenCV
- Pydantic

---

## 快速命令参考

```bash
# 安装
pip install -r requirements.txt

# 配置
cp .env.example .env
# 编辑 .env 填入 API Key

# 运行
python scripts/annotate_with_v3.py data/videos/your_video.mp4

# 查看结果
cat data/annotations_v3/your_video.json
```

开始你的视频标注之旅！🚀
