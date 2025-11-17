# VLM Motivation 标注平台 - 使用指南

## 📚 目录
- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [安装步骤](#安装步骤)
- [使用教程](#使用教程)
- [常见问题](#常见问题)

## 项目简介

这是一个基于 Streamlit 的视频标注平台，专门用于标注视频中人物的：
- **显性 Motivation**（表面动机）
- **隐性 Desire**（深层渴望）

支持两种关键帧提取模式：
1. **均匀采样**：按时间间隔提取关键帧
2. **Gemini 智能提取**：使用 Google Gemini 1.5 Flash 模型智能分析视频并提取关键时刻

## 功能特性

### ✨ 核心功能
- 📤 **视频上传**：支持多种格式（MP4, AVI, MOV, MKV）
- 🎯 **关键帧提取**：
  - 均匀采样模式（可配置间隔和最大帧数）
  - Gemini AI 智能提取（自动识别关键时刻）
- ✏️ **标注编辑器**：
  - 显性 Motivation 标注
  - 隐性 Desire 标注
  - 隐性程度评级（1-5）
  - 视觉线索记录
  - Motivation 转变点标记
- 💾 **数据保存**：JSON 格式，方便后续分析
- 📊 **时间轴预览**：可视化 Motivation 演变过程

### 🎨 界面特色
- 直观的三栏布局
- 实时进度跟踪
- 快捷键导航
- 自动保存功能

## 安装步骤

### 1. 环境要求
- Python 3.8+
- pip

### 2. 克隆项目
```bash
cd video_anno
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置 API Key（如果使用 Gemini 模式）

**方式一：环境变量（推荐）**
```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export GEMINI_API_KEY=your_api_key_here
```

**方式二：在界面中输入**
启动应用后，在侧边栏的"Gemini配置"中输入

## 使用教程

### 启动应用
```bash
cd video_anno
streamlit run frontend/app.py
```

浏览器会自动打开 `http://localhost:8501`

### 工作流程

#### 步骤 1：上传视频
有两种方式：

**方式 A：文件上传**
1. 点击侧边栏"📤 上传视频文件"
2. 选择一个或多个视频文件
3. 点击"💾 保存上传的视频"

**方式 B：从本地文件夹加载**
1. 在"📂 从本地文件夹加载"中输入文件夹路径
2. 点击"🔄 刷新视频列表"

#### 步骤 2：选择视频
1. 在"📋 视频列表"中选择要标注的视频
2. 点击"▶️ 加载选中视频"

#### 步骤 3：提取关键帧

**均匀采样模式：**
1. 在侧边栏选择"均匀采样"
2. 调整采样间隔（默认 5 秒）
3. 设置最大帧数（默认 50）
4. 点击"🔍 提取关键帧"

**Gemini 智能模式：**
1. 在侧边栏选择"Gemini智能提取"
2. 确保已配置 API Key
3. 点击"🔍 提取关键帧"
4. 等待 AI 分析（可能需要几分钟）

#### 步骤 4：开始标注
1. 关键帧提取完成后，点击"📝 开始标注"
2. 进入标注编辑器界面

#### 步骤 5：标注关键帧
对每一帧进行标注：

1. **显性 Motivation**：人物表面表现的动机
   - 例如："想要完成工作任务"

2. **隐性 Desire**：人物内心真正的渴望
   - 例如："渴望被认可和肯定"

3. **隐性程度**：选择 1-5
   - 1 = 非常显性（容易从画面看出）
   - 5 = 非常隐性（需要深度推理）

4. **视觉线索**：列出帮助推断的画面细节
   - 例如："皱眉, 紧握拳头, 避免眼神接触"

5. **转变点标记**（如适用）：
   - 勾选"标记为转变点"
   - 填写触发事件
   - 记录转变前后的 Motivation 和 Desire

6. 点击"✅ 保存当前帧"（会自动保存）

#### 步骤 6：导航和保存
- 使用"⬅️ 上一帧" / "➡️ 下一帧"切换
- 使用底部滑块快速跳转
- 查看进度条了解完成情况
- 点击"💾 保存"手动保存所有标注

### 标注技巧

#### 💡 如何区分显性和隐性？
- **显性 Motivation**：可以直接从对话、行为观察到的
- **隐性 Desire**：需要结合上下文、微表情、肢体语言推理的

#### 示例对比

| 场景 | 显性 Motivation | 隐性 Desire | 隐性程度 |
|------|----------------|-------------|----------|
| 加班工作 | 完成项目任务 | 渴望获得晋升机会 | 4 |
| 拒绝聚会邀请 | 说自己太累了 | 害怕社交、渴望独处 | 5 |
| 主动帮助同事 | 想帮同事解决问题 | 渴望被需要和认可 | 3 |

#### 🔄 转变点识别
关注以下时刻：
- 情绪突然变化
- 决策转折点
- 外部事件冲击
- 内心独白（如有）

## 数据输出

### 标注文件位置
```
data/annotations/{视频名称}.json
```

### JSON 格式示例
```json
{
  "video_info": {
    "video_path": "data/videos/example.mp4",
    "video_name": "example.mp4",
    "created_at": "2025-01-01T10:00:00",
    "status": "in_progress"
  },
  "keyframes": [
    {
      "frame_id": 0,
      "timestamp": 5.0,
      "timestamp_formatted": "0:00:05",
      "frame_path": "data/keyframes/example/frame_0000_t5.00s.jpg",
      "explicit_motivation": "想要完成工作任务",
      "implicit_desire": "渴望被认可和肯定",
      "implicit_level": 4,
      "visual_cues": ["皱眉", "紧握拳头"],
      "notes": "",
      "is_transition": true,
      "transition_info": {
        "trigger_event": "接到批评电话",
        "motivation_before": "自信完成任务",
        "motivation_after": "担心无法达标",
        "desire_before": "展示能力",
        "desire_after": "避免失败"
      }
    }
  ],
  "overall_trajectory": "从自信完成任务 → 焦虑逃避 → 重新振作"
}
```

## 常见问题

### Q1: Gemini 分析失败怎么办？
**A:**
- 检查 API Key 是否正确
- 确认网络连接
- 视频文件不要太大（建议 < 50MB）
- 查看错误信息，可能需要等待后重试

### Q2: 关键帧太多/太少？
**A:**
- **太多**：增大采样间隔或减小最大帧数
- **太少**：减小采样间隔或增大最大帧数
- 使用 Gemini 模式自动优化

### Q3: 如何批量处理多个视频？
**A:**
1. 将所有视频放入 `data/videos/` 文件夹
2. 从文件夹加载
3. 逐个选择并标注
4. 标注文件会自动保存在 `data/annotations/`

### Q4: 标注数据丢失了？
**A:**
- 每次点击"保存当前帧"都会自动保存
- 检查 `data/annotations/` 目录
- 查看是否有配置文件权限问题

### Q5: 视频格式不支持？
**A:**
- 使用 ffmpeg 转换为 MP4：
  ```bash
  ffmpeg -i input.xxx -c:v libx264 -c:a aac output.mp4
  ```

## 项目结构
```
video_anno/
├── frontend/           # 前端界面
│   ├── app.py         # 主应用
│   └── annotation_editor.py  # 标注编辑器
├── backend/           # 后端处理
│   ├── video_processor_v2.py  # 视频处理
│   └── annotation_schema.py   # 数据结构
├── config/            # 配置管理
│   └── config.py
├── data/              # 数据目录
│   ├── videos/        # 视频文件
│   ├── keyframes/     # 提取的关键帧
│   └── annotations/   # 标注数据
└── requirements.txt   # 依赖包
```

## 技术栈
- **前端**：Streamlit
- **视频处理**：OpenCV
- **AI 分析**：Google Gemini 1.5 Flash
- **数据格式**：JSON
- **配置管理**：YAML

## 许可证
MIT License

## 联系方式
如有问题，请提交 Issue 或联系开发团队。

---
🎬 Happy Annotating!
