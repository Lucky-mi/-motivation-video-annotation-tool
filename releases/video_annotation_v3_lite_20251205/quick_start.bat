@echo off
echo ====================================
echo Theory of Mind 视频标注系统 V3
echo ====================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查 .env
if not exist .env (
    echo 首次运行，需要配置...
    if not exist .env.example (
        echo 错误: 未找到 .env.example
        pause
        exit /b 1
    )
    copy .env.example .env
    echo 已创建 .env 文件
    echo 请编辑 .env 填入你的 Gemini API Key
    echo 然后重新运行此脚本
    pause
    exit /b 0
)

REM 检查依赖
echo 检查依赖...
pip install -r requirements.txt

echo.
echo 系统已就绪！
echo.
echo 使用方法：
echo 1. 将视频放入 data/videos/ 目录
echo 2. 运行: python scripts/annotate_with_v3.py data/videos/your_video.mp4
echo 3. 查看结果: data/annotations_v3/your_video.json
echo.
pause
