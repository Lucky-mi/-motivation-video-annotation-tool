# 📦 发布包分发指南

如何将视频标注系统分享给其他人使用。

## 🎯 发布包说明

我们提供了两个版本的发布包：

### 1. 轻量版 (V3 Lite)
**文件**: `video_annotation_v3_lite_YYYYMMDD.zip`

**适用场景**:
- 只需要标注功能
- 学术研究
- 快速实验
- 单视频标注

**包含内容**:
- V3 标注脚本
- 核心后端代码
- 最小依赖
- 完整文档

**优点**:
- ✅ 体积小（约 100KB 代码）
- ✅ 依赖少
- ✅ 安装快速
- ✅ 易于理解

### 2. 完整版 (Full)
**文件**: `video_annotation_full_YYYYMMDD.zip`

**适用场景**:
- 需要全套功能
- 数据集构建
- 长期项目
- 团队协作

**包含内容**:
- 所有标注功能
- Web 可视化界面
- 视频采集工具
- 批量处理脚本
- 完整文档

**优点**:
- ✅ 功能完整
- ✅ Web 界面友好
- ✅ 自动化程度高
- ✅ 适合生产环境

---

## 🔨 构建发布包

### 自动构建（推荐）

```bash
# 构建轻量版
python scripts/build_release.py --version lite

# 构建完整版
python scripts/build_release.py --version full

# 构建两个版本
python scripts/build_release.py --version both
```

构建完成后，发布包位于 `releases/` 目录。

### 手动构建

如果需要手动构建，参考以下结构：

#### 轻量版目录结构

```
video_annotation_v3_lite/
├── scripts/
│   └── annotate_with_v3.py
├── backend/
│   ├── __init__.py
│   ├── annotation_schema_v3.py
│   ├── vlm_analyzer.py
│   ├── models.py
│   └── ai_providers/
│       ├── __init__.py
│       ├── base_provider.py
│       ├── gemini_provider.py
│       └── prompt_templates.py
├── config/
│   ├── __init__.py
│   ├── config.py
│   └── config.yaml
├── data/
│   ├── videos/.gitkeep
│   ├── keyframes/.gitkeep
│   └── annotations_v3/.gitkeep
├── requirements.txt
├── .env.example
├── README.md
├── quick_start.bat      # Windows 快速启动
└── quick_start.sh       # Linux/Mac 快速启动
```

#### 完整版目录结构

```
video_annotation_full/
├── scripts/              # 所有脚本
├── backend/              # 完整后端
├── frontend/             # Web 界面
├── config/               # 配置
├── data/                 # 数据目录
│   ├── videos/
│   ├── keyframes/
│   ├── annotations/
│   ├── annotations_v3/
│   └── metadata/
├── annotation.py
├── requirements.txt
├── .env.example
├── README.md
├── start_web.bat        # Windows Web 启动
└── start_web.sh         # Linux/Mac Web 启动
```

---

## 📤 分发方式

### 方式 1: 直接分享 ZIP 文件

最简单的方式，适合小范围分享。

**步骤**:
1. 构建发布包
2. 上传到云盘（Google Drive, OneDrive, 百度云等）
3. 分享下载链接
4. 附上 `QUICK_START.md` 快速入门指南

**优点**:
- ✅ 简单直接
- ✅ 无需额外平台

**缺点**:
- ❌ 版本管理困难
- ❌ 更新麻烦

### 方式 2: GitHub 发布（推荐）

适合开源或团队项目。

**步骤**:

1. **初始化仓库**:
```bash
cd video_anno
git init
git add .
git commit -m "Initial commit"
```

2. **创建 .gitignore**:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/

# 数据文件
data/videos/*.mp4
data/videos/*.avi
data/keyframes/*
data/annotations/*.json
data/annotations_v3/*.json
data/metadata/*.json

# 配置
.env
cookies.txt

# 发布包
releases/
release_packages/*/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 临时文件
*.log
*.tmp
.DS_Store
Thumbs.db
```

3. **推送到 GitHub**:
```bash
# 在 GitHub 创建新仓库
git remote add origin https://github.com/yourusername/video-annotation.git
git branch -M main
git push -u origin main
```

4. **创建 Release**:
```bash
# 创建标签
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 在 GitHub 网页上:
# 1. 进入 Releases 页面
# 2. 点击 "Draft a new release"
# 3. 选择 tag v1.0.0
# 4. 上传构建好的 ZIP 文件
# 5. 填写 Release Notes
# 6. 点击 "Publish release"
```

**Release Notes 模板**:
```markdown
## 🎉 视频标注系统 v1.0.0

### ✨ 功能特点

- ✅ V3 自动标注（属性动态 + 开放式推断）
- ✅ Web 可视化编辑器
- ✅ YouTube 视频采集
- ✅ 批量处理支持

### 📦 下载

- **轻量版**: [video_annotation_v3_lite_20250101.zip](url)
  - 适合: 学术研究、快速实验
  - 大小: ~500KB

- **完整版**: [video_annotation_full_20250101.zip](url)
  - 适合: 数据集构建、生产环境
  - 大小: ~2MB

### 📚 文档

- [快速入门](QUICK_START.md)
- [完整文档](README.md)

### 🔧 系统要求

- Python 3.8+
- Google Gemini API Key
- 8GB+ RAM（推荐）

### 🚀 快速开始

**轻量版**:
```bash
unzip video_annotation_v3_lite_*.zip
cd video_annotation_v3_lite_*
./quick_start.sh  # Mac/Linux
# or
quick_start.bat   # Windows
```

**完整版**:
```bash
unzip video_annotation_full_*.zip
cd video_annotation_full_*
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 API Key
streamlit run frontend/app_v2.py
```

### 📝 更新日志

#### 新功能
- V3 标注 Schema
- 属性变化追踪
- 开放式心理推断
- Web 可视化编辑器

#### 改进
- 提升 AI 标注质量
- 优化批量处理性能
- 改进错误处理

#### 修复
- 修复协程调用错误
- 修复 YouTube 下载问题
- 修复关键帧缺失问题

### 🆘 获取帮助

- [提交 Issue](https://github.com/yourusername/video-annotation/issues)
- [查看文档](README.md)
```

### 方式 3: Python Package（高级）

适合作为库被其他项目使用。

**步骤**:

1. **创建 setup.py**:
```python
from setuptools import setup, find_packages

setup(
    name="video-annotation-tom",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Theory of Mind video annotation system",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/video-annotation",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "google-generativeai>=0.3.0",
        "opencv-python-headless>=4.8.1.78",
        "numpy>=1.24.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.0",
    ],
    entry_points={
        "console_scripts": [
            "video-annotate=scripts.annotate_with_v3:main",
        ],
    },
)
```

2. **发布到 PyPI**:
```bash
# 构建
python setup.py sdist bdist_wheel

# 上传到 TestPyPI（测试）
twine upload --repository testpypi dist/*

# 上传到 PyPI（正式）
twine upload dist/*
```

3. **用户安装**:
```bash
pip install video-annotation-tom
```

---

## 📋 分发清单

### 必须包含

- ✅ 源代码
- ✅ `requirements.txt`
- ✅ `.env.example`
- ✅ `README.md`
- ✅ `LICENSE`（如开源）

### 推荐包含

- ✅ `QUICK_START.md`（快速入门）
- ✅ `CHANGELOG.md`（更新日志）
- ✅ 快速启动脚本（`.bat` / `.sh`）
- ✅ 示例视频（可选）
- ✅ 示例标注结果（JSON）

### 不应包含

- ❌ `.env`（包含真实 API Key）
- ❌ `data/videos/`（用户视频）
- ❌ `data/annotations/`（标注数据）
- ❌ `venv/`（虚拟环境）
- ❌ `__pycache__/`（缓存文件）
- ❌ `.git/`（Git 历史，除非克隆仓库）

---

## 📝 使用许可

### 选择许可证

推荐的开源许可证：

1. **MIT License**（最宽松）
   - ✅ 允许商业使用
   - ✅ 允许修改
   - ✅ 允许分发
   - ✅ 仅需保留版权声明

2. **Apache 2.0**（包含专利授权）
   - ✅ 明确的专利授权
   - ✅ 商业友好

3. **GPL v3**（强制开源）
   - ✅ 衍生作品必须开源
   - ❌ 不适合商业闭源使用

**添加 LICENSE 文件**:
```bash
# MIT License 示例
# 创建 LICENSE 文件，内容：

MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🆘 用户支持

### 提供帮助渠道

1. **文档**:
   - README.md（完整文档）
   - QUICK_START.md（快速入门）
   - FAQ.md（常见问题）

2. **Issue Tracker**:
   - GitHub Issues
   - 提供 Issue 模板

3. **讨论区**:
   - GitHub Discussions
   - Discord / Slack 频道

4. **邮件**:
   - 提供联系邮箱

### Issue 模板

创建 `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug Report
about: 报告一个 Bug
title: '[BUG] '
labels: bug
assignees: ''
---

## 问题描述
清晰简洁地描述问题

## 复现步骤
1. 执行命令 '...'
2. 使用文件 '...'
3. 出现错误 '...'

## 期望行为
描述你期望发生什么

## 实际行为
描述实际发生了什么

## 环境信息
- OS: [如 Windows 11]
- Python 版本: [如 3.10.0]
- 版本: [如 v1.0.0]

## 附加信息
添加截图、日志等
```

---

## 🔄 版本更新

### 语义化版本

遵循 [Semantic Versioning](https://semver.org/):

- `主版本号.次版本号.修订号`
- 例如: `1.2.3`

**规则**:
- **主版本号**: 不兼容的 API 修改
- **次版本号**: 向下兼容的功能新增
- **修订号**: 向下兼容的问题修正

**示例**:
- `1.0.0`: 首次发布
- `1.0.1`: Bug 修复
- `1.1.0`: 新增功能
- `2.0.0`: 重大更新，不兼容旧版

### 发布新版本

```bash
# 1. 更新版本号
# 编辑 setup.py, __init__.py 等

# 2. 更新 CHANGELOG.md
# 记录本次更新内容

# 3. 提交更改
git add .
git commit -m "Bump version to 1.1.0"

# 4. 创建标签
git tag -a v1.1.0 -m "Release v1.1.0"

# 5. 推送
git push origin main --tags

# 6. 构建发布包
python scripts/build_release.py --version both

# 7. 在 GitHub 创建 Release
# 上传新构建的 ZIP 文件
```

---

## 📊 跟踪使用情况（可选）

如果需要了解使用情况：

1. **GitHub Stars/Forks**
2. **下载统计**（GitHub Releases）
3. **PyPI 下载量**（如发布到 PyPI）
4. **Google Analytics**（如有文档网站）

**注意**: 不要在代码中添加追踪，尊重用户隐私！

---

## ✅ 发布检查清单

### 发布前

- [ ] 代码测试通过
- [ ] 文档更新完整
- [ ] 版本号正确
- [ ] LICENSE 文件存在
- [ ] .env.example 正确配置
- [ ] requirements.txt 包含所有依赖
- [ ] README.md 包含完整说明
- [ ] 移除敏感信息（API Key 等）
- [ ] 移除调试代码
- [ ] 移除临时文件

### 发布后

- [ ] 验证下载链接可用
- [ ] 在干净环境测试安装
- [ ] 检查文档链接正确
- [ ] 宣布发布（社交媒体、论坛等）
- [ ] 准备好回应用户问题

---

## 🎉 总结

**推荐流程**:

1. ✅ 使用自动构建脚本
2. ✅ 发布到 GitHub
3. ✅ 创建 Release 附上 ZIP 文件
4. ✅ 提供清晰的文档
5. ✅ 建立 Issue Tracker

**关键点**:
- 清晰的文档
- 简单的安装流程
- 快速入门指南
- 及时的用户支持

祝你的标注系统被广泛使用！🚀
