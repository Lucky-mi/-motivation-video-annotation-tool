# 常见问题解决指南

## 🔴 VSCode 类型检查报错问题

### 问题1: `google.generativeai` 模块报错

**现象**：
```
❌ 未从模块"google.generativeai"导出"GenerativeModel"
❌ 未从模块"google.generativeai"导出"configure"
```

**原因**：
1. `google-generativeai` 库可能未安装
2. VSCode 的 Pylance 类型检查器无法正确识别这个库的类型定义

**解决方案**：

#### 方法1: 安装依赖（必须）
```bash
pip install -r requirements.txt
```

或者单独安装：
```bash
pip install google-generativeai>=0.3.0
```

#### 方法2: 添加类型注释（已修复）
在代码中添加 `# type: ignore` 注释来忽略类型检查：

```python
# ✅ 修复后的代码
try:
    import google.generativeai as genai  # type: ignore
except ImportError:
    genai = None
```

使用时也加上类型忽略：
```python
if gemini_api_key and genai is not None:
    genai.configure(api_key=gemini_api_key)  # type: ignore
    self.model = genai.GenerativeModel('gemini-1.5-flash')  # type: ignore
```

---

### 问题2: `config.get()` 方法飘红

**现象**：
```
❌ config.get() 方法无法识别
```

**解决方案**（已修复）：
在 [config/config.py:83](config/config.py#L83) 添加类型提示：

```python
# ✅ 修复后
config: Config = Config()  # 明确告诉 VSCode config 的类型
```

---

## 📦 依赖安装问题

### 问题: `ModuleNotFoundError`

**现象**：
```bash
ModuleNotFoundError: No module named 'xxx'
```

**解决步骤**：

#### 步骤1: 检查 Python 环境
```bash
python --version
# 应该是 Python 3.8 或更高
```

#### 步骤2: 安装依赖
```bash
# Windows
pip install -r requirements.txt

# Linux/Mac（如果有权限问题）
pip install --user -r requirements.txt
```

#### 步骤3: 验证安装
```bash
pip list | grep streamlit
pip list | grep opencv
pip list | grep google-generativeai
```

**常见依赖列表**：
```
streamlit>=1.28.0
opencv-python-headless>=4.8.1.78
google-generativeai>=0.3.0
numpy>=1.24.0
pillow>=10.0.0
pyyaml>=6.0.0
```

---

## 🔧 VSCode 配置优化

### 问题: 类型检查过于严格

如果你不想看到类型警告，可以配置 VSCode：

#### 方法1: 项目级配置（推荐）

创建 `.vscode/settings.json`：
```json
{
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.diagnosticSeverityOverrides": {
    "reportGeneralTypeIssues": "none",
    "reportOptionalMemberAccess": "none"
  }
}
```

#### 方法2: 全局配置

打开 VSCode 设置 (Ctrl+,)，搜索 "Type Checking Mode"，设置为 "basic" 或 "off"。

---

## 🚀 启动问题

### 问题: Streamlit 启动失败

**现象**：
```bash
streamlit: command not found
```

**解决方案**：

#### 检查1: 是否在虚拟环境中
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 验证
which streamlit  # 应该显示 venv 中的路径
```

#### 检查2: 重新安装 Streamlit
```bash
pip uninstall streamlit
pip install streamlit>=1.28.0
```

#### 检查3: 使用 python -m 运行
```bash
python -m streamlit run frontend/app.py
```

---

### 问题: 端口被占用

**现象**：
```
OSError: [Errno 98] Address already in use
```

**解决方案**：

#### 方法1: 更换端口
```bash
streamlit run frontend/app.py --server.port 8502
```

#### 方法2: 杀掉占用进程
```bash
# Windows
netstat -ano | findstr :8501
taskkill /PID <进程ID> /F

# Linux/Mac
lsof -i :8501
kill -9 <进程ID>
```

---

## 🎥 视频处理问题

### 问题: 无法打开视频文件

**现象**：
```
ValueError: 无法打开视频文件
```

**可能原因**：
1. 视频文件损坏
2. 视频编解码器不支持
3. 文件路径包含中文或特殊字符

**解决方案**：

#### 方法1: 转换视频格式
```bash
# 使用 ffmpeg 转换为标准 MP4
ffmpeg -i input.mov -c:v libx264 -c:a aac output.mp4
```

#### 方法2: 避免路径中的中文
- 将视频移到纯英文路径
- 或重命名文件为英文名

#### 方法3: 测试视频是否正常
```bash
# 使用 ffmpeg 检查
ffmpeg -i your_video.mp4

# 使用 Python 测试
python -c "import cv2; cap = cv2.VideoCapture('your_video.mp4'); print(cap.isOpened())"
```

---

## 🤖 Gemini API 问题

### 问题: API Key 无效

**现象**：
```
API key not valid
```

**解决步骤**：

1. **检查 API Key 格式**
   - 应该是 `AIza...` 开头的长字符串
   - 没有多余空格

2. **重新生成 API Key**
   - 访问：https://aistudio.google.com/app/apikey
   - 创建新的 API Key

3. **配置环境变量**
   ```bash
   # Windows
   set GEMINI_API_KEY=你的密钥

   # Linux/Mac
   export GEMINI_API_KEY=你的密钥
   ```

---

### 问题: 视频上传失败

**现象**：
```
Upload failed: File too large
```

**原因**：视频文件过大（Gemini 有大小限制）

**解决方案**：

#### 方法1: 压缩视频
```bash
# 使用 ffmpeg 压缩
ffmpeg -i input.mp4 -vcodec h264 -acodec aac -crf 28 output.mp4
```

#### 方法2: 裁剪视频
```bash
# 只取前 60 秒
ffmpeg -i input.mp4 -t 60 -c copy output.mp4
```

#### 方法3: 降低分辨率
```bash
# 缩小到 720p
ffmpeg -i input.mp4 -vf scale=1280:720 output.mp4
```

---

## 💾 数据保存问题

### 问题: 标注数据未保存

**检查清单**：

1. **检查文件夹权限**
   ```bash
   # Linux/Mac
   chmod -R 755 data/annotations/
   ```

2. **检查磁盘空间**
   ```bash
   # Windows
   dir d:\

   # Linux/Mac
   df -h
   ```

3. **检查路径是否存在**
   ```bash
   ls -la data/annotations/
   ```

4. **手动测试保存**
   ```python
   from backend.annotation_schema import AnnotationSchema
   schema = AnnotationSchema()
   # 测试保存
   ```

---

## 🔍 调试技巧

### 技巧1: 查看 Session State
在任何 Streamlit 页面中添加：
```python
st.write("Debug Info:", st.session_state)
```

### 技巧2: 捕获详细错误
```python
try:
    your_code_here()
except Exception as e:
    st.error(f"错误: {e}")
    import traceback
    st.code(traceback.format_exc())
```

### 技巧3: 查看配置
```python
from config.config import config
st.json(config.config)
```

### 技巧4: 清除缓存
```bash
# 删除 Streamlit 缓存
rm -rf .streamlit/

# 或在界面中按 'C' 键清除缓存
```

---

## 📝 日志查看

### Streamlit 日志位置
```bash
# Windows
%USERPROFILE%\.streamlit\logs\

# Linux/Mac
~/.streamlit/logs/
```

### 查看最新日志
```bash
# Linux/Mac
tail -f ~/.streamlit/logs/streamlit.log

# Windows（使用 PowerShell）
Get-Content $env:USERPROFILE\.streamlit\logs\streamlit.log -Wait
```

---

## 🆘 获取帮助

如果以上方法都无法解决问题：

1. **检查是否是已知问题**
   - 查看 [BUGFIX_REPORT.md](BUGFIX_REPORT.md)

2. **收集错误信息**
   - 完整的错误堆栈
   - Python 版本
   - 操作系统版本
   - 依赖包版本

3. **查看官方文档**
   - Streamlit: https://docs.streamlit.io
   - OpenCV: https://docs.opencv.org
   - Gemini: https://ai.google.dev/docs

4. **搜索类似问题**
   - GitHub Issues
   - Stack Overflow

---

## ✅ 快速自检清单

运行这个脚本来自动检查环境：

```python
# check_env.py
import sys

def check_environment():
    print("=== 环境检查 ===\n")

    # 1. Python 版本
    print(f"✓ Python 版本: {sys.version}")

    # 2. 依赖包
    packages = [
        'streamlit',
        'cv2',
        'google.generativeai',
        'yaml',
        'numpy',
        'PIL'
    ]

    for pkg in packages:
        try:
            if pkg == 'cv2':
                __import__('cv2')
            elif pkg == 'PIL':
                __import__('PIL')
            else:
                __import__(pkg)
            print(f"✓ {pkg}: 已安装")
        except ImportError:
            print(f"✗ {pkg}: 未安装")

    # 3. 目录结构
    from pathlib import Path
    dirs = ['data/videos', 'data/keyframes', 'data/annotations']
    for d in dirs:
        if Path(d).exists():
            print(f"✓ {d}: 存在")
        else:
            print(f"✗ {d}: 不存在")

    print("\n=== 检查完成 ===")

if __name__ == "__main__":
    check_environment()
```

运行：
```bash
python check_env.py
```

---

**最后更新**: 2025-11-17
