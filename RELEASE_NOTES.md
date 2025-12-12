# 📦 视频标注系统 - 发布包说明

## 🎉 发布包已准备完成！

所有发布相关的文件都在 `release_packages/` 目录中。

---

## 📂 目录结构

```
release_packages/
├── v3_lite/                    # 轻量版模板文件
│   ├── README.md              # 轻量版完整文档
│   ├── requirements.txt       # 最小依赖
│   └── .env.example           # 配置模板
│
├── full_version/               # 完整版模板文件
│   └── README.md              # 完整版文档
│
├── QUICK_START.md             # 快速入门指南（5分钟）
├── DISTRIBUTION_GUIDE.md      # 发布和分发指南
└── SUMMARY.md                 # 总体说明（本文档）
```

---

## 🚀 快速开始

### 第一步：构建发布包

```bash
# 构建两个版本
python scripts/build_release.py --version both

# 或单独构建
python scripts/build_release.py --version lite  # 仅轻量版
python scripts/build_release.py --version full  # 仅完整版
```

### 第二步：查看输出

构建完成后，发布包位于 `releases/` 目录：

```
releases/
├── video_annotation_v3_lite_20250105.zip    # 轻量版
├── video_annotation_v3_lite_20250105/       # 轻量版目录
├── video_annotation_full_20250105.zip       # 完整版
└── video_annotation_full_20250105/          # 完整版目录
```

### 第三步：分发给用户

将 ZIP 文件分享给用户，或上传到 GitHub Release。

---

## 📚 文档说明

### 给用户的文档

1. **[QUICK_START.md](release_packages/QUICK_START.md)** ⭐
   - 快速入门指南
   - 5 分钟上手
   - 适合初次使用

2. **轻量版 README** ([release_packages/v3_lite/README.md](release_packages/v3_lite/README.md))
   - 完整的功能说明
   - 详细的使用教程
   - 故障排除

3. **完整版 README** ([release_packages/full_version/README.md](release_packages/full_version/README.md))
   - 所有功能详解
   - Web 界面使用
   - 高级配置

### 给维护者的文档

1. **[SUMMARY.md](release_packages/SUMMARY.md)** ⭐
   - 发布包总体说明
   - 构建流程
   - 自定义指南

2. **[DISTRIBUTION_GUIDE.md](release_packages/DISTRIBUTION_GUIDE.md)**
   - 详细的分发指南
   - GitHub 发布流程
   - 版本管理
   - 用户支持建议

---

## 🎯 两个版本的区别

### 轻量版 (V3 Lite)

**适合**:
- 只需要标注功能
- 学术研究
- 快速实验

**包含**:
- ✅ V3 自动标注
- ✅ 核心后端代码
- ✅ 最小依赖
- ✅ 命令行工具

**大小**: ~500KB (ZIP)

### 完整版 (Full)

**适合**:
- 需要全套功能
- 数据集构建
- 长期项目

**包含**:
- ✅ 所有标注功能
- ✅ Web 可视化界面
- ✅ 视频采集工具
- ✅ 批量处理

**大小**: ~2-3MB (ZIP)

---

## 🛠️ 构建脚本说明

### 自动构建脚本

位置: `scripts/build_release.py`

功能:
- ✅ 自动复制所需文件
- ✅ 创建目录结构
- ✅ 生成配置文件
- ✅ 创建快速启动脚本
- ✅ 打包为 ZIP

使用:
```bash
python scripts/build_release.py --help

# 选项:
#   --version {lite,full,both}  要构建的版本 (默认: both)
```

### 自定义构建

如需修改发布包内容，编辑 `scripts/build_release.py`:

- `build_lite_version()` - 轻量版构建逻辑
- `build_full_version()` - 完整版构建逻辑

---

## 📋 发布检查清单

### 构建前

- [ ] 代码已测试
- [ ] 文档已更新
- [ ] 版本号正确
- [ ] 移除敏感信息

### 构建后

- [ ] ZIP 文件生成成功
- [ ] 解压测试通过
- [ ] 目录结构正确
- [ ] 快速启动脚本可用

### 分发前

- [ ] 在干净环境测试
- [ ] 安装依赖成功
- [ ] 运行标注成功
- [ ] 文档链接正确

---

## 🎬 使用示例

### 用户下载后的使用流程

#### 轻量版

```bash
# 1. 解压
unzip video_annotation_v3_lite_20250105.zip
cd video_annotation_v3_lite_20250105

# 2. 快速启动（自动配置）
./quick_start.sh   # Mac/Linux
# or
quick_start.bat    # Windows

# 3. 配置 API Key
nano .env          # 填入 GEMINI_API_KEY

# 4. 标注视频
python scripts/annotate_with_v3.py data/videos/your_video.mp4
```

#### 完整版

```bash
# 1. 解压
unzip video_annotation_full_20250105.zip
cd video_annotation_full_20250105

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
cp .env.example .env
nano .env          # 填入 API Key

# 4. 启动 Web 界面
./start_web.sh     # Mac/Linux
# or
start_web.bat      # Windows

# 浏览器访问 http://localhost:8501
```

---

## 🌐 分发方式

### 方式 1: 云盘分享（简单）

1. 上传 ZIP 到云盘（Google Drive, OneDrive, 百度云等）
2. 生成分享链接
3. 附上 `QUICK_START.md`

### 方式 2: GitHub Release（推荐）

1. 创建 GitHub 仓库
2. 推送代码
3. 创建 Release (tag: v1.0.0)
4. 上传 ZIP 文件
5. 填写 Release Notes

详细步骤: [DISTRIBUTION_GUIDE.md](release_packages/DISTRIBUTION_GUIDE.md)

### 方式 3: PyPI（高级）

作为 Python 包发布，用户可通过 `pip install` 安装。

详见 DISTRIBUTION_GUIDE.md 的 "Python Package" 章节。

---

## 📞 获取帮助

### 构建问题

- 查看: [SUMMARY.md](release_packages/SUMMARY.md)
- 检查: `scripts/build_release.py`

### 分发问题

- 查看: [DISTRIBUTION_GUIDE.md](release_packages/DISTRIBUTION_GUIDE.md)
- 包含: GitHub 发布、版本管理、用户支持

### 使用问题

- 轻量版: [release_packages/v3_lite/README.md](release_packages/v3_lite/README.md)
- 完整版: [release_packages/full_version/README.md](release_packages/full_version/README.md)
- 快速入门: [release_packages/QUICK_START.md](release_packages/QUICK_START.md)

---

## 🎉 现在可以做什么？

1. **立即构建**:
   ```bash
   python scripts/build_release.py --version both
   ```

2. **测试发布包**:
   - 解压到新目录
   - 按 README 测试
   - 确认功能正常

3. **分享给用户**:
   - 上传到云盘或 GitHub
   - 提供下载链接
   - 附上快速入门指南

4. **持续维护**:
   - 收集用户反馈
   - 定期更新版本
   - 改进文档

---

## 💡 重要提示

### 不要包含在发布包中

- ❌ `.env` 文件（包含真实 API Key）
- ❌ `data/videos/` 中的视频
- ❌ `data/annotations/` 中的标注数据
- ❌ `venv/` 虚拟环境
- ❌ `__pycache__/` 缓存文件

### 必须包含在发布包中

- ✅ `.env.example`（配置模板）
- ✅ `requirements.txt`（依赖清单）
- ✅ `README.md`（完整文档）
- ✅ 快速启动脚本
- ✅ 数据目录结构（空目录）

---

## 📊 预期效果

构建完成后，你将得到：

### 轻量版
- 文件: `releases/video_annotation_v3_lite_YYYYMMDD.zip`
- 大小: ~500KB
- 用户: 学术研究、快速实验
- 功能: V3 标注、命令行工具

### 完整版
- 文件: `releases/video_annotation_full_YYYYMMDD.zip`
- 大小: ~2-3MB
- 用户: 数据集构建、生产环境
- 功能: 全套功能、Web 界面、视频采集

---

**祝你的标注系统被广泛使用！** 🚀

如有问题，请参考 `release_packages/` 目录下的详细文档。
