# frontend/app_v2_simple.py
"""
简洁版AI视频标注系统前端 - 只包含核心功能
"""
import streamlit as st
from pathlib import Path
import sys
import json
import requests
from typing import Dict, List, Optional
from PIL import Image
import io
import time

sys.path.append(str(Path(__file__).parent.parent))

from frontend.components.question_verification import render_question_verification_page
from frontend.components.keyframe_viewer import KeyframeViewer

# 页面配置
st.set_page_config(
    page_title="AI视频标注与问题生成系统",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000"

# ============= Session State初始化 =============

def init_session_state():
    """初始化session state"""
    defaults = {
        'selected_provider': 'gemini',
        'current_page': 'upload',  # upload, review, question
        'current_video_id': None,
        'current_frame_idx': 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============= 辅助函数 =============

def check_api_health():
    """检查API健康状态"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_available_providers():
    """获取可用的AI Provider"""
    try:
        response = requests.get(f"{API_BASE_URL}/providers/list", timeout=5)
        if response.status_code == 200:
            return response.json()['providers']
    except:
        pass
    return []

# ============= 侧边栏 =============

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title("🎬 视频标注系统")

        # API状态
        if check_api_health():
            st.success("✅ API连接正常")
        else:
            st.error("❌ API未连接")
            st.info("请先启动后端服务:\n`python -m uvicorn backend.api_v2:app --port 8000`")
            st.stop()

        st.markdown("---")

        # AI Provider选择
        st.subheader("🤖 AI模型")
        providers = get_available_providers()

        if providers:
            available_providers = [p['name'] for p in providers if p['available']]

            if available_providers:
                selected = st.selectbox(
                    "选择模型",
                    options=available_providers,
                    index=0,
                    key='provider_select'
                )
                st.session_state.selected_provider = selected
            else:
                st.error("请配置API Key")

        st.markdown("---")

        # 导航菜单
        st.subheader("📋 功能")

        if st.button("📤 视频标注", width="stretch", type="primary" if st.session_state.current_page == 'upload' else "secondary"):
            st.session_state.current_page = 'upload'
            st.rerun()

        if st.button("✅ 标注校验", width="stretch", type="primary" if st.session_state.current_page == 'review' else "secondary"):
            st.session_state.current_page = 'review'
            st.rerun()

        if st.button("📝 问题生成", width="stretch", type="primary" if st.session_state.current_page == 'question' else "secondary"):
            st.session_state.current_page = 'question'
            st.rerun()

# ============= 页面1: 视频上传和标注 =============

def render_upload_page():
    """视频上传和AI分析页面"""
    st.header("📤 视频上传与AI标注")

    col1, col2 = st.columns([2, 1])

    with col1:
        # 文件上传
        uploaded_file = st.file_uploader(
            "上传视频文件",
            type=['mp4', 'avi', 'mov', 'mkv'],
            key='video_upload'
        )

        if uploaded_file is not None:
            st.success(f"✅ 已选择: {uploaded_file.name}")

            # 开始分析按钮
            if st.button("🚀 开始AI分析", type="primary", width="stretch"):
                with st.spinner("正在上传视频..."):
                    # 1. 上传视频
                    files = {'file': (uploaded_file.name, uploaded_file, 'video/mp4')}
                    upload_response = requests.post(
                        f"{API_BASE_URL}/videos/upload",
                        files=files,
                        timeout=300
                    )

                    if upload_response.status_code == 200:
                        video_info = upload_response.json()
                        video_id = video_info['video_id']
                        video_path = video_info['video_path']

                        st.success(f"✅ 视频上传成功!")

                        # 2. 开始AI分析
                        with st.spinner("AI正在分析视频，请稍候..."):
                            analysis_request = {
                                "video_path": video_path,
                                "analyze_actions": True,
                                "analyze_emotions": True,
                                "analyze_objects": True,
                                "suggest_motivations": True
                            }

                            analysis_response = requests.post(
                                f"{API_BASE_URL}/analyze/video",
                                json=analysis_request,
                                timeout=600
                            )

                            if analysis_response.status_code == 200:
                                result = analysis_response.json()
                                st.success("✅ AI分析完成!")

                                # 显示结果
                                st.subheader("分析结果")
                                col_r1, col_r2, col_r3 = st.columns(3)
                                with col_r1:
                                    st.metric("处理时间", f"{result.get('processing_time', 0):.1f}秒")
                                with col_r2:
                                    st.metric("关键帧", len(result.get('keyframes', [])))
                                with col_r3:
                                    st.metric("使用模型", result.get('model_used', '')[:15])

                                # 跳转按钮
                                if st.button("前往校验标注", type="primary"):
                                    st.session_state.current_page = 'review'
                                    st.session_state.current_video_id = video_id
                                    st.rerun()
                            else:
                                st.error(f"❌ 分析失败: {analysis_response.text}")
                    else:
                        st.error(f"❌ 上传失败: {upload_response.text}")

    with col2:
        st.info("""
        **使用说明:**

        1. 上传2-3分钟的视频
        2. AI自动提取关键帧
        3. 智能标注动机和渴望
        4. 人工校验标注结果

        **支持格式:**
        MP4, AVI, MOV, MKV
        """)


# ============= 页面2: 标注校验 =============

def render_review_page():
    """标注校验页面"""
    st.header("✅ 标注校验")

    # 1. 获取视频列表 (带缓存)
    # 使用 ttl=2 确保列表能及时更新（例如last_modified变化后）
    @st.cache_data(ttl=2)
    def get_cached_video_list():
        try:
            return requests.get(f"{API_BASE_URL}/annotations/list", timeout=2).json().get('annotations', [])
        except:
            return []

    annotations = get_cached_video_list()

    if not annotations:
        st.warning("还没有标注数据，请先上传并分析视频")
        return

    # === 修复核心：使用视频名称(str)作为选项，避免对象比对导致的重置 ===
    # 提取所有视频名称
    video_names = [a['video_name'] for a in annotations]
    
    # 找出当前选中的索引（防止刷新重置）
    # 如果 session_state 中记录的名字还在列表里，就保持选中它
    current_index = 0
    if st.session_state.get('last_selected_video_name') in video_names:
        current_index = video_names.index(st.session_state.last_selected_video_name)

    selected_video_name = st.selectbox(
        "选择视频", 
        video_names,
        index=current_index,
        key="video_selector"
    )
    
    # 记录当前选择，防止跑丢
    st.session_state.last_selected_video_name = selected_video_name

    # 根据名称找回对应的数据对象
    selected_annotation = next((a for a in annotations if a['video_name'] == selected_video_name), None)

    if selected_annotation:
        video_id = selected_annotation['video_id']
        
        # 检测视频切换：只有当 ID 真的变了才重置帧索引
        # 如果是因为保存导致的列表刷新，ID 是不会变的，所以不会重置帧
        if 'last_video_id' not in st.session_state or st.session_state.last_video_id != video_id:
            st.session_state.last_video_id = video_id
            st.session_state.current_frame_idx = 0

        # 3. 获取标注详情 (带缓存)
        # _timestamp 参数是一个技巧，传入不同的值可以强制刷新缓存
        @st.cache_data(show_spinner=False)
        def get_cached_annotation(vid, _timestamp): 
            try:
                return requests.get(f"{API_BASE_URL}/annotations/{vid}", timeout=5).json()
            except:
                return None

        # 获取数据（初始 _timestamp 为 0）
        annotation_data = get_cached_annotation(video_id, 0) 

        if not annotation_data:
            st.error("加载标注失败")
            return

        keyframes = annotation_data.get('keyframes', [])

        if not keyframes:
            st.warning("该视频没有关键帧数据")
            return

        # 显示关键帧查看器
        current_idx, edited_data = KeyframeViewer.render_complete_viewer(
            keyframes,
            current_idx=st.session_state.get('current_frame_idx', 0),
            editable=True,
            base_url=API_BASE_URL
        )
        
        # 务必更新 session_state，保证导航生效
        st.session_state.current_frame_idx = current_idx

        # 保存按钮
        if edited_data and st.button("💾 保存修改", type="primary"):
            try:
                # 合并数据
                if current_idx < len(keyframes):
                    # 更新本地对象以防万一
                    if 'action' in edited_data:
                        keyframes[current_idx].setdefault('action', {}).update(edited_data['action'])
                    if 'motivation' in edited_data:
                        keyframes[current_idx].setdefault('motivation', {}).update(edited_data['motivation'])
                    
                    # 发送请求到后端
                    response = requests.post(
                        f"{API_BASE_URL}/annotations/{video_id}/keyframe/{current_idx}",
                        json=keyframes[current_idx]['motivation']
                    )
                    
                    if response.status_code == 200:
                        st.toast("✅ 保存成功", icon="🎉")
                        
                        # 关键步骤：清除缓存！
                        # 1. 清除详情缓存，以便下次读取到最新的修改
                        get_cached_annotation.clear()
                        # 2. 清除列表缓存，因为 last_modified 字段变了
                        get_cached_video_list.clear()
                    else:
                        st.error(f"保存失败: {response.text}")
                
            except Exception as e:
                st.error(f"保存出错: {e}")


# ============= 主应用 =============

def main():
    """主应用"""
    render_sidebar()

    # 根据当前页面渲染
    page = st.session_state.get('current_page', 'upload')

    if page == 'upload':
        render_upload_page()
    elif page == 'review':
        render_review_page()
    elif page == 'question':
        render_question_verification_page()
    else:
        st.error("未知页面")


if __name__ == "__main__":
    main()
