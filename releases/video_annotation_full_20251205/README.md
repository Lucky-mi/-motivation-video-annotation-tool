# 🎬 Theory of Mind 视频标注系统（完整版）

基于 AI 的完整视频标注平台，支持视频采集、自动标注、Web 可视化编辑等全流程功能。

## ✨ 核心功能

### 🎯 标注功能
- ✅ **V3 自动标注**：属性动态 + 开放式心理推断
- ✅ **V2 兼容标注**：传统显性/隐性动机标注
- ✅ **关键帧提取**：智能提取关键时刻
- ✅ **批量处理**：支持大规模视频标注

### 🌐 Web 界面
- ✅ **可视化编辑器**：友好的标注审核界面
- ✅ **视频上传**：拖拽上传，自动处理
- ✅ **实时预览**：查看标注结果和关键帧
- ✅ **批量管理**：统一管理所有标注任务

### 📥 视频采集
- ✅ **YouTube 下载**：自动搜索和下载视频
- ✅ **内容过滤**：AI 自动筛选高质量视频
- ✅ **智能评分**：根据心理学价值评分
- ✅ **防封禁机制**：代理支持，速率限制

### 🚀 高级特性
- ✅ **异步处理**：高效的并发下载和标注
- ✅ **智能重命名**：根据内容自动生成描述性文件名
- ✅ **断点续传**：支持任务中断恢复
- ✅ **数据修复**：自动检测和修复缺失数据

## 📋 系统要求

- **Python**: 3.8+
- **内存**: 8GB+（推荐 16GB）
- **存储**: 至少 20GB 可用空间
- **API Key**: Google Gemini API Key（必须）
- **网络**: 稳定的互联网连接（用于 YouTube 下载）

## 🚀 快速开始

### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 2: 配置环境

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env，填入 API Key
# GEMINI_API_KEY=your_key_here
```

### 步骤 3: 选择使用方式

#### 方式 A: Web 界面（推荐新手）

```bash
# 启动 Web 服务
streamlit run frontend/app_v2.py

# 浏览器访问 http://localhost:8501
```

#### 方式 B: 命令行标注

```bash
# V3 格式标注
python scripts/annotate_with_v3.py data/videos/your_video.mp4

# 批量自动标注
python annotation.py
```

#### 方式 C: 视频采集 + 标注

```bash
# 异步下载和标注（推荐）
python scripts/run_async.py --limit 20 -y

# 安全模式下载
python scripts/safe_download.py --keywords 3 --per-keyword 5
```

## 📖 功能详解

### 1. V3 自动标注

最新的标注 Schema，支持开放式心理推断。

```bash
python scripts/annotate_with_v3.py data/videos/conversation.mp4
```

**输出内容**：
- 场景描述（地点、氛围、社交情境）
- 人物描述（外观、状态、角色）
- 属性变化（情绪、信任度等的上升/下降）
- 行为序列（按时间记录）
- 开放式推断（详细的心理分析）
- 心理学知识参考

### 2. Web 可视化编辑器

启动 Web 界面后，可以：

1. **上传视频**：拖拽上传或选择文件
2. **AI 标注**：自动分析并生成标注
3. **审核编辑**：浏览关键帧，修改标注内容
4. **导出数据**：下载标注结果（JSON 格式）

```bash
streamlit run frontend/app_v2.py
```

访问功能：
- 📤 上传视频：单个或批量上传
- 🔍 审核标注：查看和编辑 AI 标注结果
- 📦 批量处理：批量标注多个视频
- ✏️ 视频重命名：智能重命名视频文件

### 3. 批量自动标注

自动处理 `data/videos/` 目录下的所有视频。

```bash
python annotation.py
```

功能：
- ✅ 扫描所有未标注视频
- ✅ AI 自动分析内容
- ✅ 提取关键帧图片
- ✅ 生成标注数据
- ✅ 智能重命名视频
- ✅ 修复缺失关键帧

### 4. YouTube 视频采集

从 YouTube 搜索并下载视频，自动筛选高质量内容。

#### 异步高速模式（推荐）

```bash
# 下载 20 个视频
python scripts/run_async.py --limit 20 -y

# 自定义并发（下载2个，审核3个）
python scripts/run_async.py \
    --download-workers 2 \
    --review-workers 3 \
    --limit 50 \
    -y

# 使用代理
python scripts/run_async.py \
    --proxy http://127.0.0.1:7890 \
    --limit 50 \
    -y
```

#### 安全下载模式

```bash
# 保守下载（适合初次使用）
python scripts/safe_download.py \
    --keywords 3 \
    --per-keyword 5 \
    --delay 10
```

#### 搜索配置

编辑 `config/search_config.py` 自定义搜索：

```python
# 关键词集合
KEYWORD_SET = "full"  # full / core / test

# 每个关键词下载视频数
VIDEOS_PER_KEYWORD = 5

# 视频时长限制（秒）
MIN_DURATION = 30
MAX_DURATION = 300

# AI 审核
ENABLE_AI_REVIEW = True
STRICT_MODE = True
```

### 5. 视频智能重命名

根据视频内容自动生成描述性文件名。

```bash
# 批量重命名（在 annotation.py 中自动执行）
python annotation.py
```

示例：
- `yt_abc123.mp4` → `办公室冲突_同事争执讨论.mp4`
- `video_001.mp4` → `餐厅道歉_情侣和解场景.mp4`

### 6. 数据修复工具

修复缺失的关键帧图片。

```bash
# 检查并修复
python scripts/check_and_fix_videos.py

# 简单修复
python scripts/simple_repair.py
```

## 🗂️ 完整目录结构

```
video_annotation_full/
├── scripts/                         # 脚本工具
│   ├── annotate_with_v3.py         # V3 标注
│   ├── run_async.py                # 异步下载+标注
│   ├── run_search.py               # 视频搜索
│   ├── safe_download.py            # 安全下载
│   ├── fix_youtube_ban.py          # YouTube 诊断
│   ├── check_and_fix_videos.py     # 数据修复
│   └── ...
│
├── backend/                         # 后端逻辑
│   ├── annotation_schema.py        # V2 Schema
│   ├── annotation_schema_v3.py     # V3 Schema
│   ├── vlm_analyzer.py             # AI 分析器
│   ├── models.py                   # 数据模型
│   ├── downloader.py               # 视频下载
│   ├── content_filter.py           # 内容过滤
│   │
│   └── ai_providers/               # AI 接口
│       ├── gemini_provider.py
│       ├── openai_provider.py
│       └── prompt_templates.py
│
├── frontend/                        # Web 前端
│   ├── app_v2.py                   # 主应用
│   ├── app_complete.py             # 完整版
│   ├── app_minimal.py              # 精简版
│   │
│   ├── components/                 # UI 组件
│   │   └── annotation_editor.py
│   │
│   ├── pages/                      # 页面模块
│   │   ├── upload_page.py
│   │   ├── review_page.py
│   │   ├── batch_page.py
│   │   └── rename_page.py
│   │
│   └── utils/                      # 工具函数
│       ├── api_client.py
│       ├── data_cache.py
│       └── image_cache.py
│
├── config/                          # 配置文件
│   ├── config.py                   # 配置管理
│   ├── config.yaml                 # 主配置
│   └── search_config.py            # 搜索配置
│
├── data/                            # 数据目录
│   ├── videos/                     # 原始视频
│   ├── keyframes/                  # 关键帧图片
│   ├── annotations/                # V2 标注
│   ├── annotations_v3/             # V3 标注
│   └── metadata/                   # 元数据
│
├── annotation.py                    # 批量标注主程序
├── .env                            # 环境变量
├── .env.example                    # 配置模板
├── requirements.txt                # Python 依赖
├── cookies.txt                     # YouTube Cookies
└── README.md                       # 本文件
```

## ⚙️ 配置说明

### 环境变量 (.env)

```env
# Google Gemini API Key (必须)
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash

# OpenAI API Key (可选)
OPENAI_API_KEY=your_key_here

# 服务端口
BACKEND_PORT=8000
FRONTEND_PORT=8501
```

### 搜索配置 (config/search_config.py)

```python
# 关键词设置
KEYWORD_SET = "full"  # full, core, test
VIDEOS_PER_KEYWORD = 5

# 视频筛选
MIN_DURATION = 30      # 最短 30 秒
MAX_DURATION = 300     # 最长 5 分钟
MIN_VIEWS = 1000       # 最少观看数

# AI 审核
ENABLE_AI_REVIEW = True
STRICT_MODE = True
AUTO_DELETE_REJECTED = True

# 并发设置
DOWNLOAD_WORKERS = 2   # 下载并发数
AI_REVIEW_WORKERS = 3  # 审核并发数
```

### YouTube Cookies (cookies.txt)

用于绕过 YouTube 限制：

1. 安装浏览器扩展：[Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)
2. 访问 YouTube 并登录
3. 导出 cookies 保存为 `cookies.txt`

## 🎓 使用场景

### 场景 1: 学术研究

研究人员标注视频数据集用于 Theory of Mind 研究：

```bash
# 1. 下载研究所需视频
python scripts/run_async.py --limit 100 -y

# 2. 批量 V3 标注
for video in data/videos/*.mp4; do
    python scripts/annotate_with_v3.py "$video"
done

# 3. 导出数据分析
python scripts/export_for_analysis.py
```

### 场景 2: 数据集构建

构建大规模视频理解数据集：

```bash
# 1. 配置搜索关键词
# 编辑 config/search_config.py

# 2. 异步批量采集
python scripts/run_async.py \
    --download-workers 3 \
    --review-workers 5 \
    --limit 500 \
    -y

# 3. 质量检查
python scripts/check_video_integrity.py

# 4. 统计分析
python scripts/show_scorer_stats.py
```

### 场景 3: 手动精细标注

使用 Web 界面进行高质量手动标注：

```bash
# 1. 启动 Web 服务
streamlit run frontend/app_v2.py

# 2. 在浏览器中：
#    - 上传视频
#    - AI 初步标注
#    - 人工审核修改
#    - 导出最终数据
```

### 场景 4: 视频内容分析

快速分析单个视频内容：

```bash
# V3 深度分析
python scripts/annotate_with_v3.py your_video.mp4

# 查看结果
cat data/annotations_v3/your_video.json | jq '.'
```

## 🔧 故障排除

### YouTube 下载问题

**问题**：下载失败或被封禁

**解决方案**：
```bash
# 1. 运行诊断工具
python scripts/fix_youtube_ban.py

# 2. 更新 cookies
# 使用浏览器导出最新 cookies.txt

# 3. 使用代理
python scripts/run_async.py --proxy http://127.0.0.1:7890

# 4. 降低并发
python scripts/run_async.py --download-workers 1
```

### AI 标注问题

**问题**：标注质量不佳

**解决方案**：
```python
# 1. 使用更强模型（.env）
GEMINI_MODEL=gemini-1.5-pro

# 2. 确保视频质量
# - 清晰度 480p+
# - 人物面部可见
# - 避免字幕遮挡
```

### 内存不足

**问题**：处理大量视频时内存溢出

**解决方案**：
```bash
# 1. 降低并发数
python scripts/run_async.py \
    --download-workers 1 \
    --review-workers 2

# 2. 分批处理
python scripts/run_async.py --limit 20 -y
# 等待完成后再运行下一批

# 3. 清理缓存
rm -rf data/temp/*
```

### Web 界面卡顿

**问题**：Streamlit 界面响应慢

**解决方案**：
```bash
# 使用精简版界面
streamlit run frontend/app_minimal.py

# 或仅用于审核
streamlit run frontend/app_verification_only.py
```

## 📊 性能参考

### 标注速度

- **V3 标注**：30秒视频约需 10-30 秒
- **批量处理**：100 个视频约需 1-2 小时
- **异步下载**：每小时可下载 50-100 个视频

### 并发建议

| 系统配置 | Download Workers | Review Workers |
|----------|------------------|----------------|
| 普通PC   | 1-2              | 2-3            |
| 高配PC   | 2-3              | 3-5            |
| 服务器   | 3-5              | 5-8            |

## 📚 进阶功能

### 自定义 Prompt

编辑 `backend/ai_providers/prompt_templates.py` 自定义 AI 提示词：

```python
@staticmethod
def get_custom_prompt(video_context):
    return f"""
    自定义的标注指令...
    {video_context}
    """
```

### 扩展数据模型

修改 `backend/annotation_schema_v3.py` 添加新的标注字段：

```python
class CustomAnnotation(BaseModel):
    custom_field: str = Field(..., description="自定义字段")
    # 添加更多字段...
```

### 批量导出

```bash
# 导出为 CSV
python scripts/export_to_csv.py

# 导出为 Excel
python scripts/export_to_excel.py
```

## 📄 许可证

MIT License

## 🙏 致谢

- Google Gemini API
- OpenCV
- Streamlit
- yt-dlp
- Pydantic

---

## 快速命令参考卡

```bash
# ==== 安装配置 ====
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 API Key

# ==== Web 界面 ====
streamlit run frontend/app_v2.py

# ==== 单视频标注 ====
python scripts/annotate_with_v3.py data/videos/video.mp4

# ==== 批量标注 ====
python annotation.py

# ==== 视频采集 ====
# 异步高速
python scripts/run_async.py --limit 20 -y

# 安全模式
python scripts/safe_download.py --keywords 3 --per-keyword 5

# ==== 工具 ====
# YouTube 诊断
python scripts/fix_youtube_ban.py

# 数据修复
python scripts/check_and_fix_videos.py

# 统计信息
python scripts/show_scorer_stats.py
```

开始你的视频标注项目！🚀
