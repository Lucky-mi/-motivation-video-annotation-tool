#!/bin/bash

echo "===================================="
echo "Theory of Mind 视频标注系统 V3"
echo "===================================="
echo

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

# 检查 .env
if [ ! -f .env ]; then
    echo "首次运行，需要配置..."
    if [ ! -f .env.example ]; then
        echo "错误: 未找到 .env.example"
        exit 1
    fi
    cp .env.example .env
    echo "已创建 .env 文件"
    echo "请编辑 .env 填入你的 Gemini API Key"
    echo "然后重新运行此脚本"
    exit 0
fi

# 检查依赖
echo "检查依赖..."
pip3 install -r requirements.txt

echo
echo "系统已就绪！"
echo
echo "使用方法："
echo "1. 将视频放入 data/videos/ 目录"
echo "2. 运行: python3 scripts/annotate_with_v3.py data/videos/your_video.mp4"
echo "3. 查看结果: data/annotations_v3/your_video.json"
echo
