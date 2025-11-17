#!/bin/bash
# VLM Motivation 标注平台 - Linux/Mac 启动脚本

echo "========================================"
echo "VLM Motivation 标注平台"
echo "========================================"
echo

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.8+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "[提示] 未检测到虚拟环境，正在创建..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[错误] 创建虚拟环境失败"
        exit 1
    fi
    echo "[成功] 虚拟环境创建完成"
    echo
fi

# 激活虚拟环境
echo "[提示] 正在激活虚拟环境..."
source venv/bin/activate

# 检查依赖
if ! pip show streamlit &> /dev/null; then
    echo "[提示] 正在安装依赖包..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
    echo "[成功] 依赖安装完成"
    echo
fi

# 启动应用
echo "[启动] 正在启动标注平台..."
echo
streamlit run frontend/app.py
