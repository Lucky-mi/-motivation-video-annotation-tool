# 🤖 AI辅助视频动机标注系统

一个基于**AI辅助 + 人机协同（Human-in-the-Loop）**的视频内容标注与分析工具。

## 📋 项目概述

本系统旨在帮助研究者高效地标注视频中人物的**动机（Motivation）**和**渴望（Desire）**，特别是区分：
- **What**: 客观可见的动作和事件（AI自动识别）
- **Why**: 深层的动机和渴望（AI推断 + 人工审核）

### 核心特性

- ✅ **AI自动分析**: 使用Gemini VLM自动识别关键帧、动作、场景
- ✅ **智能预标注**: AI推断显性动机和隐性渴望
- ✅ **人机协同**: 人工审核、修改和确认AI标注
- ⭐ **两阶段质量控制** (NEW): 智能预审机制自动筛选低质量视频，节省标注成本
- ✅ **RESTful API**: 支持FastAPI后端，易于集成
- ✅ **直观界面**: Streamlit前端，简单易用

## 🚀 快速开始

### 1. 环境要求

- Python 3.9+
- 推荐使用虚拟环境

### 2. 安装依赖

```bash
# 进入项目目录
cd video_anno

# 创建虚拟环境（可选但推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置API Key

获取Gemini API Key: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

```bash
# 设置环境变量
# Windows:
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac:
export GEMINI_API_KEY=your_api_key_here
```

### 4. 启动系统

#### 方法1: 使用主启动脚本（推荐）

```bash
python main.py
```

然后选择：
- `1` - 启动完整系统（后端 + 前端）
- `2` - 仅启动后端API
- `3` - 仅启动前端界面
- `4` - 测试Gemini API连接

#### 方法2: 分别启动

```bash
# 终端1: 启动后端
python -m uvicorn backend.api:app --reload --port 8000

# 终端2: 启动前端
streamlit run frontend/app.py --server.port 8501
```

### 5. 访问系统

- **前端界面**: [http://localhost:8501](http://localhost:8501)
- **API文档**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📖 使用指南

### 完整工作流程

```
1. 上传视频
   ↓
2. AI分析 (选择智能提取或均匀采样)
   ↓
3. AI自动标注 (What + Why)
   ↓
4. 人工审核和修改
   ↓
5. 导出标注数据
```

### 详细步骤

#### Step 1: 上传视频

1. 在左侧栏选择视频文件（支持 MP4, AVI, MOV, MKV）
2. 点击"上传到服务器"

#### Step 2: AI分析

选择提取模式：
- **🧠 智能提取**: AI自动识别关键时刻（适合动作密集的视频）
- **⏱️ 均匀采样**: 按固定间隔提取（适合均匀标注）

点击"开始AI分析"，等待1-2分钟

#### Step 3: 审核标注

AI将自动生成：
- **What (客观描述)**:
  - 动作描述
  - 视觉场景
  - 物体和角色

- **Why (动机推断)**:
  - 显性动机（Explicit Motivation）
  - 隐性渴望（Implicit Desire）
  - 渴望类型（基于马斯洛需求层次）
  - 动机类型（内在/外在/混合）
  - 隐性程度（1-5级）

#### Step 4: 人工修改

- 阅读AI生成的标注
- 修改不准确的内容
- 补充AI遗漏的细节
- 点击"确认此标注"或"标记为已修改"

#### Step 5: 导出数据

标注数据自动保存在 `data/annotations/` 目录，格式为JSON

## 📁 项目结构

```
video_anno/
├── frontend/          # 前端界面
│   ├── app.py        # 主应用
│   └── annotation_editor.py  # 标注编辑器
├── backend/          # 后端处理
│   ├── video_processor_v2.py  # 视频处理
│   └── annotation_schema.py   # 数据结构
├── config/           # 配置管理
├── data/             # 数据目录
│   ├── videos/       # 视频文件
│   ├── keyframes/    # 关键帧图片
│   └── annotations/  # 标注数据
└── requirements.txt  # 依赖列表
```

## 📊 标注数据格式

标注结果保存在 `data/annotations/` 目录，JSON 格式：

```json
{
  "video_info": {
    "video_name": "example.mp4",
    "created_at": "2025-01-01T10:00:00"
  },
  "keyframes": [
    {
      "timestamp": 5.0,
      "explicit_motivation": "想要完成工作任务",
      "implicit_desire": "渴望被认可和肯定",
      "implicit_level": 4,
      "visual_cues": ["皱眉", "紧握拳头"],
      "is_transition": true
    }
  ],
  "overall_trajectory": "从自信完成任务 → 焦虑逃避 → 重新振作"
}
```

## 🛠️ 工具脚本

- `check_env.py` - 环境检查脚本
- `run.bat` / `run.sh` - 一键启动脚本

## 📚 文档

### 基础文档
- [快速上手指南](QUICKSTART.md) - 5 分钟快速入门
- [完整使用教程](README_USAGE.md) - 详细功能说明
- [故障排除指南](TROUBLESHOOTING.md) - 常见问题解决
- [部署说明](DEPLOYMENT_FIX.md) - 部署相关问题

### 高级功能 (NEW)
- ⭐ [两阶段标注流程指南](docs/ANNOTATION_PIPELINE_GUIDE.md) - 智能质量预审机制
- 📝 [Prompt设计文档](backend/prompts/README.md) - 标注prompt模板说明

## ❓ 常见问题

**Q: 如何处理大视频文件？**
A: 建议使用均匀采样模式，调整采样间隔来控制关键帧数量。

**Q: Gemini 分析失败？**
A: 检查 API Key 是否正确，视频文件不要太大（建议 < 50MB）。

**Q: 标注数据丢失？**
A: 每次点击"保存当前帧"都会自动保存，检查 `data/annotations/` 目录。

## 📝 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**🎬 开始你的标注之旅！**
