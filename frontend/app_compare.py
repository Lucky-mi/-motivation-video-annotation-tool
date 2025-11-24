import streamlit as st
import json
from pathlib import Path

# 路径配置
DATA_ROOT = Path("data")
DIR_V2 = DATA_ROOT / "annotations"  # 原数据
# 请确保这个目录名正确
DIR_V3 = DATA_ROOT / "annotations_gemini-3-pro-preview" 

st.set_page_config(layout="wide", page_title="模型效果对比台")
st.title("⚔️ 模型大对决: 2.5 Flash vs 3.0(Thinking)")

# 1. 检查目录
if not DIR_V3.exists():
    st.error(f"找不到实验数据目录: {DIR_V3}")
    st.stop()

# 2. 获取文件列表
files_v2 = sorted(list(DIR_V2.glob("*.json")))
files_v3 = sorted(list(DIR_V3.glob("*.json")))

if not files_v3:
    st.warning("实验数据目录为空")
    st.stop()

# 3. 侧边栏选择
with st.sidebar:
    st.header("选择文件")
    selected_file_v3 = st.selectbox(
        "选择新模型结果 (V3)", 
        files_v3, 
        format_func=lambda x: x.name
    )
    
    # 尝试自动匹配旧文件
    try:
        default_v2_index = [f.name for f in files_v2].index(selected_file_v3.name)
    except ValueError:
        default_v2_index = 0
    
    selected_file_v2 = st.selectbox(
        "选择对比基准 (V2)", 
        files_v2, 
        index=default_v2_index,
        format_func=lambda x: x.name
    )

# 4. 加载数据
try:
    with open(selected_file_v2, 'r', encoding='utf-8') as f:
        data_v2 = json.load(f)
    with open(selected_file_v3, 'r', encoding='utf-8') as f:
        data_v3 = json.load(f)
except Exception as e:
    st.error(f"读取失败: {e}")
    st.stop()

# 5. 界面展示
st.header(f"📺 视频: {data_v3.get('video_name', 'Unknown')}")

# 叙事对比
with st.expander("📝 整体叙事对比", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"🤖 旧版 ({selected_file_v2.name})")
        st.write(data_v2.get('overall_trajectory', '无数据'))
    with c2:
        st.success(f"🧠 新版 ({selected_file_v3.name})")
        st.write(data_v3.get('overall_trajectory', '无数据'))

st.markdown("---")
st.subheader("🖼️ 关键帧深度对比")

frames_v3 = data_v3.get('keyframes', [])
frames_v2 = data_v2.get('keyframes', [])

if not frames_v3:
    st.warning("新模型未提取到关键帧")
else:
    for i, kf3 in enumerate(frames_v3):
        # 获取新版时间戳
        ts3 = kf3.get('timestamp_seconds')
        if ts3 is None and 'action' in kf3: ts3 = kf3['action'].get('timestamp')
        if ts3 is None: ts3 = 0
        
        # === 🔥 核心算法优化：寻找最近邻 ===
        match_v2 = None
        min_diff = float('inf')
        
        for kf2 in frames_v2:
            ts2 = kf2.get('timestamp_seconds')
            if ts2 is None and 'action' in kf2: ts2 = kf2['action'].get('timestamp')
            if ts2 is None: continue
            
            diff = abs(ts2 - ts3)
            if diff < min_diff:
                min_diff = diff
                match_v2 = kf2
        
        # 只有偏差在 5秒 内才算匹配成功
        is_matched = match_v2 is not None and min_diff <= 5.0
        # =================================
        
        with st.expander(f"⏱️ 时间点: {int(ts3)}s", expanded=True):
            col_img, col_v2, col_v3 = st.columns([1.5, 2, 2])
            
            with col_img:
                # 显示图片 (V3)
                path = kf3.get('frame_path')
                if path and Path(path).exists():
                    st.image(str(path), caption=f"新版截图 ({ts3:.1f}s)", width=350)
                else:
                    st.caption("新版图片缺失")
            
            with col_v2:
                if is_matched:
                    # 显示匹配信息
                    match_ts = match_v2.get('timestamp_seconds') or match_v2['action']['timestamp']
                    st.markdown(f"#### 🤖 旧版分析")
                    st.caption(f"匹配到帧: {int(match_ts)}s (偏差: {min_diff:.1f}s)")
                    
                    mot = match_v2.get('motivation', {})
                    st.markdown(f"**显性**: {mot.get('explicit_motivation')}")
                    st.markdown(f"**隐性**: {mot.get('implicit_desire')}")
                    if mot.get('reasoning'):
                        st.info(f"推理: {mot.get('reasoning')}")
                else:
                    st.warning(f"#### 🚫 旧版未覆盖")
                    st.caption(f"旧版在 {ts3}s 附近(±5s)没有提取关键帧")

            with col_v3:
                st.markdown("#### 🧠 新版分析")
                mot = kf3.get('motivation', {})
                st.markdown(f"**显性**: {mot.get('explicit_motivation')}")
                st.markdown(f"**隐性**: {mot.get('implicit_desire')}")
                if mot.get('reasoning'):
                    st.success(f"推理: {mot.get('reasoning')}")