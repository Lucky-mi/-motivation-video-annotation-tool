# frontend/app.py
"""
AI辅助人机协同标注平台 - 主界面
支持What(AI生成) + Why(人工标注)的协同工作流
"""
import streamlit as st
from pathlib import Path
import sys
import json
import requests
from typing import Dict, List, Optional
import time

sys.path.append(str(Path(__file__).parent.parent))

from config.config import config
from backend.models import AnnotationStatus, DesireCategory, MotivationType

# 页面配置
st.set_page_config(
    page_title="AI协同标注平台",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API配置
API_BASE_URL = "http://localhost:8000"

# 初始化session_state
if 'current_video_id' not in st.session_state:
    st.session_state.current_video_id = None
if 'annotation_data' not in st.session_state:
    st.session_state.annotation_data = None
if 'current_frame_idx' not in st.session_state:
    st.session_state.current_frame_idx = 0
if 'show_ai_reasoning' not in st.session_state:
    st.session_state.show_ai_reasoning = True


def check_api_connection():
    """检查API连接"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def main():
    st.title("🤖 AI辅助视频动机标注平台")
    st.markdown("**人机协同工作流**: AI分析What → 人工标注Why → 高质量数据集")

    # 检查API连接
    if not check_api_connection():
        st.error("❌ 无法连接到后端API服务")
        st.info("请先启动后端服务: `python -m uvicorn backend.api:app --reload`")
        st.stop()

    st.markdown("---")

    # 侧边栏
    with st.sidebar:
        render_sidebar()

    # 主区域
    if st.session_state.annotation_data is not None:
        render_annotation_workspace()
    else:
        render_welcome_page()


def render_sidebar():
    """侧边栏"""
    st.header("📁 工作流程")

    # Step 1: 上传视频
    with st.expander("1️⃣ 上传视频", expanded=True):
        uploaded_file = st.file_uploader(
            "选择视频文件",
            type=['mp4', 'avi', 'mov', 'mkv'],
            key='file_uploader'
        )

        if uploaded_file:
            if st.button("📤 上传到服务器", use_container_width=True):
                with st.spinner("上传中..."):
                    files = {"file": uploaded_file}
                    try:
                        response = requests.post(f"{API_BASE_URL}/videos/upload", files=files)
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ 上传成功: {data['video_name']}")
                            st.session_state.current_video_id = data['video_id']
                            st.rerun()
                        else:
                            st.error(f"上传失败: {response.text}")
                    except Exception as e:
                        st.error(f"连接失败: {str(e)}")

    # Step 2: AI分析
    if st.session_state.current_video_id:
        with st.expander("2️⃣ AI分析视频", expanded=True):
            st.markdown("**AI将自动识别:**")
            st.markdown("- 🎬 关键动作 (What)")
            st.markdown("- 🎭 场景物体")
            st.markdown("- 💭 动机推断 (Why)")

            col1, col2 = st.columns(2)
            with col1:
                extraction_mode = st.selectbox(
                    "提取模式",
                    options=['smart', 'uniform'],
                    format_func=lambda x: "🧠 智能提取" if x == 'smart' else "⏱️ 均匀采样"
                )

            with col2:
                max_frames = st.number_input("最大帧数", 10, 100, 20)

            if st.button("🚀 开始AI分析", type="primary", use_container_width=True):
                run_ai_analysis(extraction_mode, max_frames)

    # Step 3: 查看已有标注
    st.markdown("---")
    with st.expander("3️⃣ 已有标注", expanded=False):
        try:
            response = requests.get(f"{API_BASE_URL}/annotations/list")
            if response.status_code == 200:
                annotations = response.json()['annotations']
                if annotations:
                    for ann in annotations:
                        progress = ann['annotated_frames'] / ann['total_frames'] if ann['total_frames'] > 0 else 0

                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.text(f"{ann['video_name'][:20]}")
                            st.progress(progress, text=f"{ann['annotated_frames']}/{ann['total_frames']}")
                        with col2:
                            if st.button("📂", key=f"load_{ann['video_id']}", use_container_width=True):
                                load_annotation(ann['video_id'])
                else:
                    st.info("暂无标注")
        except:
            st.warning("无法连接到API服务")


def run_ai_analysis(extraction_mode: str, max_frames: int):
    """运行AI分析"""
    video_id = st.session_state.current_video_id

    # 获取视频文件列表
    try:
        response = requests.get(f"{API_BASE_URL}/videos/list")
        videos = response.json()['videos']
        video_info = next((v for v in videos if v['video_id'] == video_id), None)

        if not video_info:
            st.error("无法找到视频文件")
            return

        video_path = video_info['video_path']
    except Exception as e:
        st.error(f"获取视频信息失败: {e}")
        return

    request_data = {
        "video_path": video_path,
        "extraction_mode": extraction_mode,
        "interval_seconds": 5.0,
        "max_frames": max_frames,
        "analyze_actions": True,
        "analyze_emotions": True,
        "analyze_objects": True,
        "suggest_motivations": True
    }

    with st.spinner("🤖 AI分析中... 这可能需要1-2分钟"):
        try:
            response = requests.post(
                f"{API_BASE_URL}/analyze/video",
                json=request_data,
                timeout=300
            )

            if response.status_code == 200:
                st.success("✅ AI分析完成!")
                st.session_state.annotation_data = response.json()
                st.session_state.current_frame_idx = 0
                st.rerun()
            else:
                st.error(f"分析失败: {response.text}")
        except Exception as e:
            st.error(f"错误: {str(e)}")


def load_annotation(video_id: str):
    """加载已有标注"""
    try:
        response = requests.get(f"{API_BASE_URL}/annotations/{video_id}")
        if response.status_code == 200:
            st.session_state.annotation_data = response.json()
            st.session_state.current_video_id = video_id
            st.session_state.current_frame_idx = 0
            st.success("✅ 加载成功")
            st.rerun()
    except Exception as e:
        st.error(f"加载失败: {str(e)}")


def render_welcome_page():
    """欢迎页面"""
    st.markdown("## 👋 欢迎使用AI协同标注平台")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 1️⃣ 上传视频")
        st.markdown("从左侧上传你的视频文件")
        st.markdown("支持格式: MP4, AVI, MOV, MKV")

    with col2:
        st.markdown("### 2️⃣ AI分析")
        st.markdown("AI自动识别关键帧和动机")
        st.markdown("- 智能提取关键帧")
        st.markdown("- 分析动作和场景")
        st.markdown("- 推断动机和渴望")

    with col3:
        st.markdown("### 3️⃣ 人工标注")
        st.markdown("审核和完善AI标注的Why")
        st.markdown("- 确认AI标注")
        st.markdown("- 修改和补充")
        st.markdown("- 导出数据集")

    st.markdown("---")
    st.info("💡 **提示**: 请从左侧栏开始你的工作流程")

    # 显示系统信息
    with st.expander("ℹ️ 系统信息"):
        try:
            response = requests.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                health = response.json()
                st.json(health)
        except:
            st.warning("无法获取系统信息")


def render_annotation_workspace():
    """标注工作区"""
    data = st.session_state.annotation_data
    keyframes = data.get('keyframes', [])

    if not keyframes:
        st.warning("⚠️ 没有关键帧数据")
        return

    # 顶部工具栏
    render_toolbar(keyframes)

    st.markdown("---")

    # 主工作区 - 左右分栏
    col_frame, col_annotation = st.columns([1.5, 1])

    with col_frame:
        render_frame_viewer(keyframes)

    with col_annotation:
        render_annotation_panel(keyframes)

    st.markdown("---")

    # 底部时间轴
    render_timeline(keyframes)


def render_toolbar(keyframes: List):
    """顶部工具栏"""
    cols = st.columns([2, 1, 1, 1, 1, 2])

    with cols[0]:
        st.markdown(f"### 帧 {st.session_state.current_frame_idx + 1} / {len(keyframes)}")

    with cols[1]:
        if st.button("⬅️ 上一帧", use_container_width=True):
            if st.session_state.current_frame_idx > 0:
                st.session_state.current_frame_idx -= 1
                st.rerun()

    with cols[2]:
        if st.button("➡️ 下一帧", use_container_width=True):
            if st.session_state.current_frame_idx < len(keyframes) - 1:
                st.session_state.current_frame_idx += 1
                st.rerun()

    with cols[3]:
        if st.button("✅ 批量确认", use_container_width=True):
            confirm_all_ai_annotations()

    with cols[4]:
        if st.button("💾 保存", type="primary", use_container_width=True):
            st.success("✅ 已自动保存")

    with cols[5]:
        # 进度显示
        confirmed = sum(
            1 for kf in keyframes
            if kf.get('motivation', {}).get('status') in ['human_confirmed', 'human_modified']
        )
        progress = confirmed / len(keyframes) if keyframes else 0
        st.progress(progress, text=f"人工审核: {confirmed}/{len(keyframes)}")


def render_frame_viewer(keyframes: List):
    """关键帧查看器"""
    idx = st.session_state.current_frame_idx
    current_frame = keyframes[idx]

    st.subheader("🖼️ 关键帧")

    # 显示图片
    frame_path = current_frame['frame_path']
    video_id = st.session_state.current_video_id
    frame_filename = Path(frame_path).name

    # 尝试从API获取图片
    try:
        image_url = f"{API_BASE_URL}/keyframes/{video_id}/{frame_filename}"
        st.image(image_url, use_container_width=True)
    except:
        # 降级到本地路径
        if Path(frame_path).exists():
            st.image(frame_path, use_container_width=True)
        else:
            st.warning("⚠️ 无法加载图片")

    # 时间信息
    action = current_frame.get('action', {})
    st.caption(f"⏱️ {action.get('timestamp_formatted', '')} ({action.get('timestamp', 0):.2f}s)")

    # AI识别的内容 (What)
    with st.expander("🤖 AI识别内容 (What)", expanded=st.session_state.show_ai_reasoning):
        st.markdown("**动作描述:**")
        st.info(action.get('action_description', '未识别'))

        st.markdown("**视觉上下文:**")
        st.text(action.get('visual_context', ''))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**物体:**")
            objects = action.get('objects', [])
            if objects:
                for obj in objects:
                    st.markdown(f"- {obj}")
            else:
                st.caption("无")

        with col2:
            st.markdown("**角色:**")
            characters = action.get('characters', [])
            if characters:
                for char in characters:
                    st.markdown(f"- {char}")
            else:
                st.caption("无")

        st.markdown(f"**场景:** {action.get('scene', '未知')}")
        st.markdown(f"**AI置信度:** {action.get('confidence', 0)*100:.1f}%")


def render_annotation_panel(keyframes: List):
    """标注面板 - 人工标注Why"""
    idx = st.session_state.current_frame_idx
    current_frame = keyframes[idx]
    motivation = current_frame.get('motivation', {})

    st.subheader("✏️ 动机标注 (Why)")

    # 显示标注状态
    status = motivation.get('status', 'ai_generated')
    status_colors = {
        'ai_generated': '🤖',
        'human_confirmed': '✅',
        'human_modified': '✏️',
        'human_created': '👤'
    }
    st.caption(f"状态: {status_colors.get(status, '❓')} {status}")

    st.markdown("---")

    # AI建议 (可编辑)
    st.markdown("### 💭 动机分析")

    explicit_motivation = st.text_area(
        "显性动机 (Explicit Motivation)",
        value=motivation.get('explicit_motivation', ''),
        height=80,
        placeholder="表面上的行为动机，例如：完成工作任务",
        help="AI生成，可修改",
        key=f'explicit_{idx}'
    )

    implicit_desire = st.text_area(
        "隐性渴望 (Implicit Desire)",
        value=motivation.get('implicit_desire', ''),
        height=80,
        placeholder="深层的心理需求，例如：获得认可和成就感",
        help="AI推断，建议人工审核",
        key=f'implicit_{idx}'
    )

    st.markdown("---")

    # 分类标签
    st.markdown("### 🏷️ 分类")

    col1, col2 = st.columns(2)

    with col1:
        desire_category_values = [e.value for e in DesireCategory]
        current_category = motivation.get('desire_category', 'other')
        if current_category not in desire_category_values:
            current_category = 'other'

        desire_category = st.selectbox(
            "渴望类型",
            options=desire_category_values,
            index=desire_category_values.index(current_category),
            format_func=lambda x: {
                'physiological': '🍽️ 生理需求',
                'safety': '🛡️ 安全需求',
                'belonging': '👥 归属需求',
                'esteem': '🏆 尊重需求',
                'self_actualization': '🌟 自我实现',
                'other': '❓ 其他'
            }.get(x, str(x)),
            key=f'desire_{idx}'
        )

    with col2:
        motivation_type_values = [e.value for e in MotivationType]
        current_type = motivation.get('motivation_type', 'mixed')
        if current_type not in motivation_type_values:
            current_type = 'mixed'

        motivation_type = st.selectbox(
            "动机类型",
            options=motivation_type_values,
            index=motivation_type_values.index(current_type),
            format_func=lambda x: {
                'intrinsic': '🔥 内在动机',
                'extrinsic': '🎁 外在动机',
                'mixed': '🔄 混合动机'
            }.get(x, str(x)),
            key=f'type_{idx}'
        )

    implicit_level = st.select_slider(
        "隐性程度",
        options=[1, 2, 3, 4, 5],
        value=motivation.get('implicit_level', 3),
        format_func=lambda x: {
            1: "😊 很显性",
            2: "🙂 较显性",
            3: "😐 中等",
            4: "🤔 较隐性",
            5: "🎭 很隐性"
        }[x],
        key=f'level_{idx}'
    )

    st.markdown("---")

    # 操作按钮
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ 确认此标注", use_container_width=True, type="primary"):
            save_frame_annotation(idx, {
                'explicit_motivation': explicit_motivation,
                'implicit_desire': implicit_desire,
                'desire_category': desire_category,
                'motivation_type': motivation_type,
                'implicit_level': implicit_level,
                'status': 'human_confirmed'
            })

    with col2:
        if st.button("✏️ 标记为已修改", use_container_width=True):
            save_frame_annotation(idx, {
                'explicit_motivation': explicit_motivation,
                'implicit_desire': implicit_desire,
                'desire_category': desire_category,
                'motivation_type': motivation_type,
                'implicit_level': implicit_level,
                'status': 'human_modified'
            })


def render_timeline(keyframes: List):
    """时间轴视图"""
    st.subheader("📊 标注时间轴")

    timeline_data = []
    for idx, kf in enumerate(keyframes):
        action = kf.get('action', {})
        motivation = kf.get('motivation', {})

        status = motivation.get('status', 'ai_generated')
        status_icon = {
            'ai_generated': '🤖',
            'human_confirmed': '✅',
            'human_modified': '✏️',
            'human_created': '👤'
        }.get(status, '❓')

        timeline_data.append({
            "帧": idx + 1,
            "时间": action.get('timestamp_formatted', ''),
            "状态": status_icon,
            "动作(What)": (action.get('action_description', '')[:40] + "...") if len(action.get('action_description', '')) > 40 else action.get('action_description', ''),
            "显性动机": (motivation.get('explicit_motivation', '')[:30] + "...") if len(motivation.get('explicit_motivation', '')) > 30 else motivation.get('explicit_motivation', ''),
            "隐性渴望": (motivation.get('implicit_desire', '')[:30] + "...") if len(motivation.get('implicit_desire', '')) > 30 else motivation.get('implicit_desire', ''),
            "隐性程度": "🎭" * motivation.get('implicit_level', 3)
        })

    st.dataframe(
        timeline_data,
        use_container_width=True,
        height=300
    )


def save_frame_annotation(frame_idx: int, updated_motivation: Dict):
    """保存单帧标注"""
    video_id = st.session_state.current_video_id

    try:
        response = requests.post(
            f"{API_BASE_URL}/annotations/{video_id}/keyframe/{frame_idx}",
            json=updated_motivation
        )

        if response.status_code == 200:
            # 更新本地数据
            st.session_state.annotation_data['keyframes'][frame_idx]['motivation'].update(updated_motivation)
            st.success("✅ 保存成功")

            # 自动跳转到下一帧
            if frame_idx < len(st.session_state.annotation_data['keyframes']) - 1:
                st.session_state.current_frame_idx = frame_idx + 1
                time.sleep(0.5)
                st.rerun()
        else:
            st.error(f"保存失败: {response.text}")
    except Exception as e:
        st.error(f"错误: {str(e)}")


def confirm_all_ai_annotations():
    """批量确认所有AI标注"""
    video_id = st.session_state.current_video_id

    try:
        response = requests.post(f"{API_BASE_URL}/annotations/{video_id}/confirm-all")
        if response.status_code == 200:
            st.success("✅ 已批量确认所有AI标注")
            # 重新加载数据
            load_annotation(video_id)
    except Exception as e:
        st.error(f"错误: {str(e)}")


if __name__ == "__main__":
    main()
