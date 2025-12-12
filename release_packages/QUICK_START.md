# 🚀 快速入门指南

5 分钟上手视频标注系统！

## 📦 选择版本

### 轻量版（推荐新手）
- ✅ 只需要标注功能
- ✅ 简单快速
- ✅ 核心依赖少
- 👉 **适合**: 学术研究、快速实验、单视频标注

### 完整版
- ✅ 包含所有功能
- ✅ Web 可视化界面
- ✅ 视频采集和批量处理
- 👉 **适合**: 数据集构建、长期项目、团队协作

---

## ⚡ 轻量版快速开始

### Windows 用户

```cmd
# 1. 解压文件
# 双击解压 video_annotation_v3_lite_YYYYMMDD.zip

# 2. 双击运行
quick_start.bat

# 3. 配置 API Key
# 编辑 .env 文件，填入你的 Gemini API Key

# 4. 标注视频
python scripts/annotate_with_v3.py data/videos/your_video.mp4
```

### Mac/Linux 用户

```bash
# 1. 解压文件
unzip video_annotation_v3_lite_YYYYMMDD.zip
cd video_annotation_v3_lite_YYYYMMDD

# 2. 运行快速启动
./quick_start.sh

# 3. 配置 API Key
nano .env
# 填入: GEMINI_API_KEY=your_key_here

# 4. 标注视频
python3 scripts/annotate_with_v3.py data/videos/your_video.mp4
```

---

## 🌐 完整版快速开始

### Windows 用户

```cmd
# 1. 解压文件
# 双击解压 video_annotation_full_YYYYMMDD.zip

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
copy .env.example .env
# 编辑 .env 填入 API Key

# 4. 启动 Web 界面
start_web.bat
```

### Mac/Linux 用户

```bash
# 1. 解压
unzip video_annotation_full_YYYYMMDD.zip
cd video_annotation_full_YYYYMMDD

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 配置
cp .env.example .env
nano .env  # 填入 API Key

# 4. 启动 Web 界面
./start_web.sh
```

---

## 🔑 获取 API Key

### Google Gemini（必须）

1. 访问：https://makersuite.google.com/app/apikey
2. 点击 "Create API Key"
3. 复制 API Key
4. 粘贴到 `.env` 文件：
   ```
   GEMINI_API_KEY=your_key_here
   ```

免费额度：每分钟 15 个请求，足够个人使用！

---

## 📝 第一次标注

### 准备视频

将视频放入 `data/videos/` 目录：

```bash
# 推荐视频特征：
# ✅ 时长: 30秒 - 3分钟
# ✅ 内容: 人物对话、互动场景
# ✅ 清晰度: 480p 以上
# ✅ 无字幕、无水印（最佳）
```

### 运行标注

```bash
# 轻量版
python scripts/annotate_with_v3.py data/videos/your_video.mp4

# 完整版（命令行）
python annotation.py

# 完整版（Web界面）
streamlit run frontend/app_v2.py
# 浏览器访问 http://localhost:8501
```

### 查看结果

```bash
# 标注结果位置
data/annotations_v3/your_video.json

# 查看内容（Windows）
type data\annotations_v3\your_video.json

# 查看内容（Mac/Linux）
cat data/annotations_v3/your_video.json

# 格式化查看（需要 jq）
cat data/annotations_v3/your_video.json | jq '.'
```

---

## 🎯 标注结果示例

```json
{
  "video_id": "conversation_001",
  "duration": 45.2,
  "is_clean_video": true,

  "scene": {
    "location": "办公室",
    "atmosphere": "紧张对立"
  },

  "characters": [
    {
      "character_id": "A",
      "appearance": "30岁男性，西装",
      "attribute_changes": [
        {
          "attribute_name": "自信心",
          "direction": "下降",
          "evidence": ["语速变快", "眼神回避"]
        }
      ]
    }
  ],

  "open_inferences": [
    {
      "inference_aspect": "人物A的真实意图",
      "conclusion": "表面说'只是建议'，实际是施加压力",
      "confidence": "高"
    }
  ]
}
```

---

## 🆘 遇到问题？

### 问题 1: "No module named 'google.generativeai'"

**解决**:
```bash
pip install google-generativeai
```

### 问题 2: "API Key 无效"

**检查**:
1. `.env` 文件存在且正确命名
2. API Key 没有多余空格
3. API Key 有效且有配额

### 问题 3: 视频处理失败

**尝试**:
```bash
# 转换视频格式
ffmpeg -i input.mov -c:v libx264 output.mp4

# 或使用在线转换: cloudconvert.com
```

### 问题 4: 标注质量不佳

**改进**:
1. 使用更清晰的视频
2. 选择互动性强的场景
3. 在 `.env` 中改用 `gemini-1.5-pro`

---

## 📚 下一步

### 学习更多

- **轻量版**: 阅读 `README.md`
- **完整版**: 阅读 `README.md` 的完整功能章节
- **定制**: 查看 `backend/annotation_schema_v3.py`

### 批量标注

```bash
# 批量处理多个视频
for video in data/videos/*.mp4; do
    python scripts/annotate_with_v3.py "$video"
done
```

### 使用 Web 界面（完整版）

```bash
streamlit run frontend/app_v2.py
```

功能：
- 📤 拖拽上传视频
- 🎬 自动 AI 标注
- ✏️ 可视化编辑
- 💾 导出结果

### 视频采集（完整版）

```bash
# 从 YouTube 自动下载和标注
python scripts/run_async.py --limit 20 -y
```

---

## 💡 最佳实践

### 视频选择

✅ **好的视频**:
- 清晰的人物面部
- 明显的情绪变化
- 人际互动场景
- 无字幕遮挡

❌ **不推荐的视频**:
- 静态画面为主
- 人物面部模糊
- 过多特效或字幕
- 过长（>5分钟）

### 提高标注质量

1. **视频预处理**: 裁剪到关键部分
2. **使用更强模型**: `gemini-1.5-pro`
3. **人工审核**: 使用 Web 界面修改 AI 标注
4. **多次标注**: 对重要视频标注多次取平均

---

## 🎉 完成！

你已经学会了基本使用方法！

**接下来可以**:
- ✅ 标注更多视频
- ✅ 探索 Web 界面（完整版）
- ✅ 批量处理数据集
- ✅ 自定义标注 Schema

有问题？查看完整 README 或提交 Issue！

开始你的标注之旅！🚀
