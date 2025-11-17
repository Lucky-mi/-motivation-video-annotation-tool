# 快速开始指南

## 🚀 5 分钟快速上手

### Windows 用户

1. **双击运行** `run.bat`
   - 首次运行会自动创建虚拟环境并安装依赖
   - 后续运行会直接启动应用

2. **浏览器打开** `http://localhost:8501`

### Linux/Mac 用户

1. **运行启动脚本**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

2. **浏览器打开** `http://localhost:8501`

### 手动启动

```bash
# 1. 安装依赖（仅首次）
pip install -r requirements.txt

# 2. 启动应用
streamlit run frontend/app.py
```

## 📖 第一次使用

### 测试流程（5分钟）

1. **上传测试视频**
   - 准备一个短视频（< 1 分钟）
   - 在侧边栏点击"📤 上传视频文件"
   - 选择视频并保存

2. **提取关键帧**
   - 选择"均匀采样"模式
   - 设置间隔 3 秒
   - 点击"🔍 提取关键帧"

3. **开始标注**
   - 点击"📝 开始标注"
   - 为第一帧填写：
     - 显性 Motivation（简单描述即可）
     - 隐性 Desire（尝试推理）
     - 选择隐性程度
   - 点击"✅ 保存当前帧"

4. **查看结果**
   - 查看时间轴表格
   - 检查 `data/annotations/` 目录下的 JSON 文件

## 🎯 核心概念（1分钟理解）

| 术语 | 含义 | 示例 |
|------|------|------|
| **显性 Motivation** | 表面可见的动机 | "想完成工作" |
| **隐性 Desire** | 深层真实渴望 | "渴望被认可" |
| **隐性程度** | 需要推理的难度 | 1=显而易见，5=需深度思考 |
| **转变点** | Motivation 改变的时刻 | 接到批评电话后态度转变 |

## 📁 目录结构（知道文件在哪）

```
video_anno/
├── run.bat / run.sh    ← 启动脚本（双击运行）
├── frontend/app.py     ← 主程序
├── data/
│   ├── videos/         ← 放视频文件
│   ├── keyframes/      ← 自动生成的关键帧图片
│   └── annotations/    ← 标注结果（JSON）
└── config/config.yaml  ← 自动生成的配置
```

## ⚙️ Gemini AI 模式（可选）

如果想使用 AI 智能提取关键帧：

1. **获取 API Key**
   - 访问 https://aistudio.google.com/app/apikey
   - 创建 API Key

2. **配置方式**

   **方式一：环境变量（推荐）**
   ```bash
   # Windows
   set GEMINI_API_KEY=你的密钥

   # Linux/Mac
   export GEMINI_API_KEY=你的密钥
   ```

   **方式二：界面输入**
   - 在侧边栏选择"Gemini智能提取"
   - 输入 API Key

## ❓ 遇到问题？

### 常见错误解决

**错误：找不到模块 'streamlit'**
```bash
pip install -r requirements.txt
```

**错误：无法打开视频**
- 确认视频格式（支持 MP4, AVI, MOV, MKV）
- 尝试用其他播放器测试视频是否损坏

**错误：权限不足**
```bash
# Linux/Mac
chmod +x run.sh
chmod -R 755 data/
```

**界面显示异常**
- 刷新浏览器（Ctrl+F5）
- 清除 Streamlit 缓存：删除 `.streamlit/` 目录

## 📚 下一步

- 阅读 [完整使用指南](README_USAGE.md)
- 了解标注技巧和最佳实践
- 批量处理多个视频

---

💡 **提示**：建议先用短视频熟悉流程，再处理长视频！
