import streamlit as st
import requests
from typing import List, Dict, Optional
import sys
from pathlib import Path

# Add parent directory to path
frontend_path = Path(__file__).parent.parent.parent
sys.path.append(str(frontend_path))

from frontend.components.keyframe_viewer import KeyframeViewer
from frontend.components.question_display import QuestionDisplay
from frontend.utils.cache import DataCache, ImageCache
from config.config import config

API_BASE_URL = "http://localhost:8000"

def render_question_verification_page():
    """渲染问题校验页面"""
    st.title("📝 问题生成与校验")

    # 1. 视频选择 - 不使用侧边栏，改用主内容区
    st.subheader("1️⃣ 选择视频")

    # 获取所有有问题的视频 (Mock: 暂时获取所有视频，实际应过滤)
    # TODO: Add API to list videos with questions
    try:
        videos = requests.get(f"{API_BASE_URL}/review/list").json().get('annotations', [])
    except Exception as e:
        st.error(f"无法连接API: {e}")
        return

    if not videos:
        st.warning("还没有已标注的视频，请先上传并分析视频")
        return

    video_options = {v['video_name']: v['video_id'] for v in videos}
    selected_video_name = st.selectbox(
        "选择视频",
        list(video_options.keys()),
        key='question_video_select'
    )

    if not selected_video_name:
        st.info("请选择一个视频")
        return

    video_id = video_options[selected_video_name]

    st.markdown("---")

    # 2. 加载数据
    if 'current_video_id' not in st.session_state or st.session_state.current_video_id != video_id:
        st.session_state.current_video_id = video_id
        st.session_state.current_q_index = 0
        # Clear caches
        ImageCache.clear()
        
    # 获取问题集
    try:
        q_response = requests.get(f"{API_BASE_URL}/questions/{video_id}")
        if q_response.status_code == 404:
            # 如果没有问题集，显示生成界面
            render_generation_ui(video_id)
            return
        question_set = q_response.json()
    except Exception as e:
        st.error(f"加载问题集失败: {e}")
        return

    # 获取标注数据(用于显示关键帧)
    try:
        anno_response = requests.get(f"{API_BASE_URL}/annotations/{video_id}")
        annotation_data = anno_response.json()
        keyframes = annotation_data.get('keyframes', [])
    except Exception as e:
        st.error(f"加载标注数据失败: {e}")
        return

    # 3. 主界面布局
    questions = question_set.get('questions', [])
    if not questions:
        st.warning("该视频没有问题数据")
        return

    # 进度条
    total_q = len(questions)
    current_idx = st.session_state.get('current_q_index', 0)
    progress = (current_idx + 1) / total_q
    st.progress(progress, text=f"进度: {current_idx + 1}/{total_q}")

    # 导航栏
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ 上一题", disabled=(current_idx <= 0), width="stretch"):
            st.session_state.current_q_index -= 1
            st.rerun()
            
    with col_next:
        if st.button("下一题 ➡️", disabled=(current_idx >= total_q - 1), width="stretch"):
            st.session_state.current_q_index += 1
            st.rerun()

    st.divider()

    # 核心内容区
    current_question = questions[current_idx]
    
    # 左侧：关键帧查看器
    # 右侧：问题详情
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("📺 关联关键帧")
        related_ids = current_question.get('related_frame_ids', [])
        
        # 找到对应的关键帧索引
        target_frame_idx = 0
        if related_ids:
            target_id = related_ids[0]
            for idx, kf in enumerate(keyframes):
                if kf.get('frame_id') == target_id:
                    target_frame_idx = idx
                    break
        
        # 使用KeyframeViewer
        KeyframeViewer.render_complete_viewer(
            keyframes,
            current_idx=target_frame_idx,
            editable=False,
            base_url=API_BASE_URL
        )

    with col_right:
        st.subheader("❓ 问题详情")
        
        def handle_verify(q_id, action, data):
            # 调用API保存校验结果
            try:
                payload = {
                    "action": action,
                    "modifications": data,
                    "notes": ""
                }
                requests.put(f"{API_BASE_URL}/questions/{q_id}/verify", params=payload)
                
                if action == "approved":
                    st.toast("✅ 已通过", icon="✅")
                elif action == "modified":
                    st.toast("💾 已保存修改", icon="💾")
                elif action == "rejected":
                    st.toast("🗑️ 已废弃", icon="🗑️")
                
                # 自动跳到下一题
                if current_idx < total_q - 1:
                    st.session_state.current_q_index += 1
                    st.rerun()
                    
            except Exception as e:
                st.error(f"保存失败: {e}")

        QuestionDisplay.render_question_card(
            current_question,
            current_idx,
            total_q,
            editable=True,
            on_verify=handle_verify
        )

def render_generation_ui(video_id: str):
    """渲染生成界面"""
    st.info("该视频暂无问题集")
    
    with st.form("gen_form"):
        st.write("### 生成配置")
        num_q = st.number_input("生成数量", min_value=1, max_value=20, value=5)
        provider = st.selectbox("AI模型", ["gemini", "openai"], index=0)
        
        if st.form_submit_button("🚀 开始生成"):
            with st.spinner("正在生成问题... (可能需要几分钟)"):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/questions/generate/{video_id}",
                        params={"num_questions": num_q, "provider": provider}
                    )
                    if response.status_code == 200:
                        st.success("生成成功!")
                        st.rerun()
                    else:
                        st.error(f"生成失败: {response.text}")
                except Exception as e:
                    st.error(f"请求失败: {e}")
