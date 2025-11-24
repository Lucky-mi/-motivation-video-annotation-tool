# 项目结构说明

## 📂 完整目录树

```
video_anno/
│
├── 📄 run.bat                      # Windows 启动脚本
├── 📄 run.sh                       # Linux/Mac 启动脚本
├── 📄 requirements.txt             # Python 依赖列表
├── 📄 .gitignore                   # Git 忽略规则
│
├── 📖 README_USAGE.md              # 完整使用指南
├── 📖 QUICKSTART.md                # 5分钟快速上手
├── 📖 BUGFIX_REPORT.md             # Bug 修复报告
├── 📖 PROJECT_STRUCTURE.md         # 本文档
│
├── 📁 frontend/                    # 前端界面模块
│   ├── __init__.py
│   ├── app.py                      # 主应用入口
│   └── annotation_editor.py        # 标注编辑器组件
│
├── 📁 backend/                     # 后端处理模块
│   ├── __init__.py
│   ├── video_processor_v2.py       # 视频处理器（支持Gemini）
│   └── annotation_schema.py        # 标注数据结构定义
│
├── 📁 config/                      # 配置管理模块
│   ├── __init__.py
│   ├── config.py                   # 配置管理类
│   └── config.yaml                 # 配置文件（自动生成）
│
├── 📁 data/                        # 数据目录
│   ├── 📁 videos/                  # 视频文件存储
│   │   └── .gitkeep
│   ├── 📁 keyframes/               # 提取的关键帧图片
│   │   └── .gitkeep
│   └── 📁 annotations/             # 标注结果（JSON格式）
│       └── .gitkeep
│
└── 📁 venv/                        # Python 虚拟环境（自动创建）
    └── ...
```

---

## 📄 核心文件说明

### 启动脚本

| 文件 | 用途 | 使用方法 |
|------|------|----------|
| `run.bat` | Windows 启动脚本 | 双击运行 |
| `run.sh` | Linux/Mac 启动脚本 | `chmod +x run.sh && ./run.sh` |

**功能**:
- 自动检测 Python 环境
- 创建虚拟环境（首次运行）
- 安装依赖包
- 启动 Streamlit 应用

---

### 前端模块 (`frontend/`)

#### `app.py` - 主应用
**责任**: 整个应用的入口和主界面

**核心功能**:
- 视频上传和管理
- 配置界面（采样模式、参数调整）
- 关键帧提取触发
- 视频列表展示
- 主界面布局

**关键函数**:
```python
main()                          # 主函数，渲染整个应用
load_videos_from_folder()       # 从文件夹加载视频列表
show_video_processing_area()    # 显示视频处理区域
extract_keyframes()             # 提取关键帧（分发到不同模式）
show_keyframes()                # 展示关键帧网格
```

**Session State 管理**:
```python
st.session_state.current_video          # 当前选中的视频路径
st.session_state.keyframes              # 提取的关键帧列表
st.session_state.video_list             # 可用视频列表
st.session_state.show_annotation_editor # 是否显示标注编辑器
st.session_state.current_annotation     # 当前标注数据
```

---

#### `annotation_editor.py` - 标注编辑器
**责任**: 标注界面和交互逻辑

**核心功能**:
- 关键帧浏览和导航
- 标注表单（Motivation、Desire、视觉线索等）
- 转变点标记
- 时间轴可视化
- 自动保存

**关键类和方法**:
```python
class AnnotationEditor:
    load_or_create_annotation()    # 加载或创建标注
    save_current_annotation()       # 保存标注到JSON
    render()                        # 渲染编辑器界面
    _render_toolbar()               # 顶部工具栏
    _render_frame_viewer()          # 关键帧查看器
    _render_annotation_panel()      # 标注面板
    _render_timeline()              # 时间轴
```

**标注数据结构**:
```python
{
    "explicit_motivation": str,     # 显性动机
    "implicit_desire": str,         # 隐性渴望
    "implicit_level": int (1-5),    # 隐性程度
    "visual_cues": list[str],       # 视觉线索
    "is_transition": bool,          # 是否为转变点
    "transition_info": dict,        # 转变详情
    "notes": str                    # 备注
}
```

---

### 后端模块 (`backend/`)

#### `video_processor_v2.py` - 视频处理器
**责任**: 视频分析和关键帧提取

**核心功能**:
- 读取视频元信息（时长、分辨率、帧率）
- 均匀采样提取关键帧
- Gemini AI 智能分析
- 根据时间戳提取指定帧

**关键类和方法**:
```python
class SmartVideoProcessor:
    __init__(output_dir, gemini_api_key)  # 初始化

    get_video_info(video_path)            # 获取视频信息
    # 返回: {fps, frame_count, duration, width, height}

    extract_uniform_frames(                # 均匀采样
        video_path,
        interval_seconds=5.0,
        max_frames=50
    )
    # 返回: [{frame_id, timestamp, frame_path, ...}]

    analyze_video_with_gemini(video_path)  # Gemini分析
    # 返回: {key_moments, overall_trajectory, suggested_timestamps}

    extract_suggested_frames(              # 提取AI建议的帧
        video_path,
        timestamps
    )
```

**依赖**:
- `cv2` (OpenCV): 视频读取和帧提取
- `google.generativeai`: Gemini API 调用

---

#### `annotation_schema.py` - 数据结构定义
**责任**: 标注数据的创建、验证、序列化

**核心功能**:
- 定义标注数据结构
- 创建空白标注模板
- JSON 序列化/反序列化

**关键方法**:
```python
class AnnotationSchema:
    @staticmethod
    create_empty_annotation(         # 创建空白标注
        video_path,
        keyframes
    )

    @staticmethod
    create_transition_info(          # 创建转变点信息
        trigger_event,
        motivation_before,
        motivation_after,
        ...
    )

    @staticmethod
    save_annotation(                 # 保存到JSON
        annotation,
        output_path
    )

    @staticmethod
    load_annotation(annotation_path) # 从JSON加载
```

**输出格式** (JSON):
```json
{
  "video_info": {
    "video_path": "...",
    "created_at": "2025-01-01T10:00:00",
    "status": "in_progress"
  },
  "keyframes": [...],
  "overall_trajectory": "..."
}
```

---

### 配置模块 (`config/`)

#### `config.py` - 配置管理
**责任**: 应用配置的读取、写入、管理

**核心功能**:
- YAML 配置文件管理
- 点号路径访问（`paths.videos`）
- API Key 管理（优先从环境变量读取）
- 默认配置生成

**关键类和方法**:
```python
class Config:
    __init__(config_path)           # 初始化，加载配置

    get(key, default=None)          # 获取配置值
    # 示例: config.get('paths.videos')

    set(key, value)                 # 设置配置值
    # 示例: config.set('extraction.mode', 'gemini')

    get_api_key(service)            # 获取API密钥
    # 优先级: 环境变量 > 配置文件

    set_api_key(service, api_key)   # 设置API密钥

# 全局实例
config = Config()
```

**配置文件示例** (`config.yaml`):
```yaml
paths:
  videos: data/videos
  keyframes: data/keyframes
  annotations: data/annotations

extraction:
  mode: uniform              # 'uniform' 或 'gemini'
  interval_seconds: 5.0
  max_frames: 50

api_keys:
  gemini: null               # 或从环境变量读取
  openai: null
```

---

## 🔄 数据流程图

### 1. 视频上传流程
```
用户上传视频
    ↓
保存到 data/videos/
    ↓
加载到 st.session_state.video_list
    ↓
用户选择 → st.session_state.current_video
```

### 2. 关键帧提取流程

**均匀采样模式**:
```
用户点击"提取关键帧"
    ↓
SmartVideoProcessor.extract_uniform_frames()
    ↓
按间隔读取视频帧
    ↓
保存到 data/keyframes/{video_name}/
    ↓
返回关键帧列表 → st.session_state.keyframes
```

**Gemini 智能模式**:
```
用户点击"提取关键帧"
    ↓
SmartVideoProcessor.analyze_video_with_gemini()
    ↓
上传视频到 Gemini API
    ↓
解析 AI 返回的建议时间戳
    ↓
SmartVideoProcessor.extract_suggested_frames()
    ↓
保存到 data/keyframes/{video_name}/
    ↓
返回关键帧列表 + AI分析结果
```

### 3. 标注流程
```
用户点击"开始标注"
    ↓
AnnotationEditor.load_or_create_annotation()
    ↓
检查是否存在已有标注
    ├─ 存在 → 加载 JSON
    └─ 不存在 → 创建空白模板
    ↓
st.session_state.current_annotation
    ↓
显示标注编辑器
    ↓
用户填写标注字段
    ↓
点击"保存当前帧"
    ↓
AnnotationEditor.save_current_annotation()
    ↓
保存到 data/annotations/{video_name}.json
```

---

## 🔌 依赖关系

### 模块间依赖
```
frontend/app.py
    ├─ import config.config
    ├─ import backend.video_processor_v2
    └─ import frontend.annotation_editor

frontend/annotation_editor.py
    ├─ import backend.annotation_schema
    └─ import config.config

backend/video_processor_v2.py
    ├─ import cv2
    └─ import google.generativeai

backend/annotation_schema.py
    └─ import json

config/config.py
    └─ import yaml
```

### 外部库依赖 (`requirements.txt`)
```
streamlit          # Web 界面框架
opencv-python      # 视频处理
google-generativeai # Gemini API
numpy              # 数值计算（OpenCV依赖）
pillow             # 图像处理
pyyaml             # YAML配置文件
```

---

## 🗄️ 数据存储

### 视频文件
**位置**: `data/videos/`
**格式**: `.mp4`, `.avi`, `.mov`, `.mkv`
**命名**: 用户上传时的原文件名

### 关键帧图片
**位置**: `data/keyframes/{video_name}/`
**格式**: `.jpg`
**命名**: `frame_{序号:04d}_t{时间戳:.2f}s.jpg`
**示例**: `frame_0001_t5.00s.jpg`

### 标注数据
**位置**: `data/annotations/`
**格式**: `.json`
**命名**: `{video_name}.json`
**编码**: UTF-8（支持中文）

---

## 🚀 启动流程

### 首次启动
```
1. 运行 run.bat / run.sh
2. 检测 Python 环境
3. 创建虚拟环境 (venv/)
4. 安装依赖包 (pip install -r requirements.txt)
5. 启动 Streamlit (streamlit run frontend/app.py)
6. 浏览器打开 http://localhost:8501
7. 加载配置 (config/config.yaml，不存在则创建默认)
8. 初始化 session_state
9. 扫描视频目录
10. 渲染界面
```

### 后续启动
```
1. 运行 run.bat / run.sh
2. 激活虚拟环境
3. 启动 Streamlit
4. 浏览器打开应用
```

---

## 🔧 配置优先级

### API Key 读取顺序
```
1. 环境变量 (GEMINI_API_KEY)
   ↓ 不存在
2. 配置文件 (config/config.yaml)
   ↓ 不存在
3. 界面输入
```

### 配置参数来源
```
1. 用户在界面中修改
   ↓ 保存到
2. config/config.yaml
   ↓ 重启后加载
3. 应用到运行时
```

---

## 📝 开发建议

### 添加新功能
1. 确定功能属于前端还是后端
2. 在相应模块中添加代码
3. 如需配置项，在 `config.py` 中添加
4. 更新文档

### 调试技巧
```python
# 在 Streamlit 中查看变量
st.write(st.session_state)

# 查看配置
st.json(config.config)

# 捕获异常
try:
    ...
except Exception as e:
    st.error(f"错误: {e}")
    import traceback
    st.code(traceback.format_exc())
```

### 性能优化
- 使用 `@st.cache_data` 缓存数据
- 使用 `@st.cache_resource` 缓存模型
- 避免在循环中调用 Streamlit 组件

---

## 📚 扩展阅读

- **Streamlit 文档**: https://docs.streamlit.io
- **OpenCV 教程**: https://docs.opencv.org/4.x/
- **Gemini API**: https://ai.google.dev/docs

---

**最后更新**: 2025-11-17
