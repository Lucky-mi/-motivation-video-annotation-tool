"""
最简测试版 - 用于调试
"""
import streamlit as st
from pathlib import Path
import json

st.set_page_config(
    page_title="测试",
    page_icon="✅",
    layout="wide"
)

st.title("🎯 测试页面")

# 测试路径
DATA_ROOT = Path("data")
ANNOTATIONS_DIR = DATA_ROOT / "annotations"

st.write(f"数据根目录: {DATA_ROOT.absolute()}")
st.write(f"标注目录: {ANNOTATIONS_DIR.absolute()}")
st.write(f"标注目录存在: {ANNOTATIONS_DIR.exists()}")

# 测试列出文件
if ANNOTATIONS_DIR.exists():
    files = list(ANNOTATIONS_DIR.glob("*.json"))
    st.write(f"找到 {len(files)} 个标注文件:")
    for f in files[:5]:
        st.write(f"  - {f.name}")
else:
    st.warning("标注目录不存在")

# 测试侧边栏
st.sidebar.title("侧边栏测试")
page = st.sidebar.radio("选择页面", ["页面1", "页面2", "页面3"])

st.markdown("---")
st.success(f"当前页面: {page}")
st.balloons()
