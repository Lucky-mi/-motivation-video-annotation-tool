# ffmpeg 和 Node.js 安装指南

## 📦 为什么需要这些工具？

### ffmpeg
- **作用：** 音视频处理工具，用于合并音视频流、转换格式
- **影响：** 没有它可能下载不到最佳质量的视频
- **优先级：** ⭐⭐⭐ 强烈推荐

### Node.js
- **作用：** JavaScript运行时，用于解析YouTube的JavaScript代码
- **影响：** 某些视频格式可能无法解析
- **优先级：** ⭐⭐ 建议安装

---

## 🪟 Windows 安装指南

### 方式1: 使用 Scoop (推荐，最简单)

```bash
# 1. 安装 Scoop (如果还没有)
# 在 PowerShell 中运行：
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# 2. 安装 ffmpeg 和 Node.js
scoop install ffmpeg nodejs

# 3. 验证安装
ffmpeg -version
node --version
```

### 方式2: 手动安装

#### 安装 ffmpeg

**选项A: 使用 winget (Windows 10/11)**
```bash
winget install Gyan.FFmpeg
```

**选项B: 手动下载**
1. 访问 https://www.gyan.dev/ffmpeg/builds/
2. 下载 `ffmpeg-release-essentials.zip`
3. 解压到 `C:\ffmpeg`
4. 添加到环境变量：
   - 打开"系统环境变量"
   - 编辑 `Path`
   - 添加 `C:\ffmpeg\bin`
5. 重启命令行，运行 `ffmpeg -version` 验证

#### 安装 Node.js
1. 访问 https://nodejs.org/
2. 下载并安装 LTS 版本（推荐 18.x 或 20.x）
3. 安装过程中勾选"Add to PATH"
4. 重启命令行，运行 `node --version` 验证

---

## 🐧 Linux 安装指南

### Ubuntu/Debian
```bash
# 安装 ffmpeg
sudo apt update
sudo apt install ffmpeg

# 安装 Node.js (使用 NodeSource)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs

# 验证
ffmpeg -version
node --version
```

### CentOS/RHEL
```bash
# 安装 ffmpeg
sudo yum install epel-release
sudo yum install ffmpeg

# 安装 Node.js
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install nodejs

# 验证
ffmpeg -version
node --version
```

---

## 🍎 macOS 安装指南

### 使用 Homebrew (推荐)
```bash
# 安装 Homebrew (如果还没有)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 ffmpeg 和 Node.js
brew install ffmpeg node

# 验证
ffmpeg -version
node --version
```

---

## ✅ 验证安装

运行以下命令检查是否安装成功：

```bash
# 检查 ffmpeg
ffmpeg -version

# 检查 Node.js
node --version

# 应该看到版本号而不是错误
```

---

## 🔍 如果不想安装

如果你决定不安装这些工具，系统仍然可以正常工作，只是会有以下限制：

### 不安装 ffmpeg 的影响：
- ✅ 可以下载视频（使用单一流）
- ❌ 可能无法获得最高质量
- ❌ 字幕转换功能受限
- ❌ 某些格式转换不可用

### 不安装 Node.js 的影响：
- ✅ 大部分视频可以正常下载
- ❌ 极少数特殊视频可能无法解析
- ❌ 某些新格式支持受限

### 临时方案：修改下载选项

如果确实不想安装，可以使用简化配置：

```python
# 在 backend/downloader.py 中修改 ydl_opts
ydl_opts = {
    'format': 'best',  # 简化格式选择
    'outtmpl': out_tmpl,
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'writesubtitles': False,  # 禁用字幕下载
    'extractor_args': {
        'youtube': {
            'player_client': ['ios']  # 使用iOS客户端
        }
    }
}
```

---

## 🎯 推荐配置（按需选择）

### 配置1: 基础研究（最小安装）
- ✅ Python + yt-dlp
- ❌ ffmpeg
- ❌ Node.js
- **适用于：** 快速测试，对视频质量要求不高

### 配置2: 标准研究（推荐）⭐
- ✅ Python + yt-dlp
- ✅ ffmpeg
- ❌ Node.js
- **适用于：** 大部分研究场景，平衡质量和便利性

### 配置3: 完整配置（专业）
- ✅ Python + yt-dlp
- ✅ ffmpeg
- ✅ Node.js
- **适用于：** 需要最高质量，处理各种视频格式

---

## 📞 常见问题

### Q: 安装后仍然有警告？
A: 重启命令行/终端，确保环境变量生效

### Q: ffmpeg 无法识别？
A: 检查是否添加到系统 PATH 环境变量

### Q: 一定要安装吗？
A: 不是必需的，但**强烈建议安装 ffmpeg** 以获得最佳效果

### Q: 安装时间和空间需求？
A:
- ffmpeg: ~100MB，5分钟
- Node.js: ~50MB，3分钟

---

## 🚀 快速测试

安装后运行这个命令测试：

```bash
# 测试下载单个视频（应该没有警告了）
python scripts/youtube_collector.py --keywords "psychology experiment" --per-keyword 1 --mode full
```

如果还有警告，请查看日志文件 `logs/youtube_collector_*.log` 进行诊断。
