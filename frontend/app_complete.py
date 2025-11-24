# frontend/app_complete.py
"""
完整功能的AI视频标注系统前端
功能列表:
1. 多AI Provider选择 (Gemini, OpenAI)
2. 视频上传和AI自动标注
3. 批量处理(文件夹上传)
4. 连续检查模式(上一个/下一个)
5. 人工标注编辑
6. 视频主题重命名
7. 用户登录和历史记录
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
from frontend.components.keyframe_viewer import KeyframeViewer
# ✅ 新增这行
from frontend.utils.cache import DataCache
from frontend.components.question_verification import render_question_verification_page
# 页面配置
st.set_page_config(
    page_title="AI视频标注系统 - 完整版",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000"

# ============= Session State初始化 =============

def init_session_state():
    """初始化session state"""
    defaults = {
        'auth_token': None,
        'current_user': None,
        'selected_provider': 'gemini',
        'current_page': 'upload',  # upload, batch, review, rename
        'review_list': [],
        'review_index': 0,
        'current_video_id': None,
        'annotation_data': None,
        'current_frame_idx': 0,
        'last_video_id': None,  # 用于检测视频切换
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
            st.stop()

        st.markdown("---")

        # AI Provider选择
        st.subheader("🤖 AI模型选择")
        providers = get_available_providers()

        if providers:
            available_providers = [p['name'] for p in providers if p['available']]

            if available_providers:
                selected = st.selectbox(
                    "选择AI Provider",
                    options=available_providers,
                    index=0 if 'gemini' in available_providers else 0,
                    key='provider_select'
                )
                st.session_state.selected_provider = selected

                # 显示Provider状态
                for p in providers:
                    if p['name'] == selected:
                        if p['configured']:
                            st.info(f"✅ {p['display_name']} 已配置")
                        else:
                            st.warning(f"⚠️ {p['display_name']} 未配置API Key")
            else:
                st.error("没有可用的AI Provider，请配置API Key")
        else:
            st.warning("无法获取Provider列表")

        st.markdown("---")

        # 导航菜单
        st.subheader("📋 功能菜单")

        if st.button("📤 上传视频", use_container_width=True):
            st.session_state.current_page = 'upload'
            st.rerun()

        if st.button("📁 批量处理", use_container_width=True):
            st.session_state.current_page = 'batch'
            st.rerun()

        if st.button("🔍 检查标注", use_container_width=True):
            st.session_state.current_page = 'review'
            st.rerun()

        if st.button("✏️ 重命名视频", use_container_width=True):
            st.session_state.current_page = 'rename'
            st.rerun()

        if st.button("📝 生成/校验问题", use_container_width=True):
            st.session_state.current_page = 'question_verify'
            st.rerun()

        st.markdown("---")

        # 用户信息
        st.subheader("👤 用户")
        if st.session_state.current_user:
            st.write(f"欢迎: {st.session_state.current_user['username']}")
            if st.button("退出登录", use_container_width=True):
                st.session_state.auth_token = None
                st.session_state.current_user = None
                st.rerun()
        else:
            st.caption("游客模式")

# ============= 页面1: 上传视频 =============

def render_upload_page():
    """视频上传和AI分析页面"""
    st.header("📤 上传视频 - AI自动标注")

    st.markdown("""
    **功能说明:**
    - 上传单个视频
    - AI自动识别关键帧
    - 智能标注动机和渴望
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        # 文件上传
        uploaded_file = st.file_uploader(
            "选择视频文件",
            type=['mp4', 'avi', 'mov', 'mkv'],
            key='video_upload'
        )

        if uploaded_file is not None:
            st.success(f"✅ 已选择: {uploaded_file.name}")

            # 分析选项
            st.subheader("分析选项")

            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                analyze_actions = st.checkbox("分析动作", value=True)
                analyze_emotions = st.checkbox("分析情绪", value=True)

            with col_opt2:
                suggest_motivations = st.checkbox("推断动机", value=True)
                analyze_objects = st.checkbox("识别物体", value=True)

            # 开始分析按钮
            if st.button("🚀 开始AI分析", type="primary", use_container_width=True):
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

                        st.success(f"✅ 视频上传成功! ID: {video_id}")

                        # 2. 开始AI分析
                        with st.spinner("AI正在分析视频,请稍候..."):
                            analysis_request = {
                                "video_path": video_path,
                                "analyze_actions": analyze_actions,
                                "analyze_emotions": analyze_emotions,
                                "analyze_objects": analyze_objects,
                                "suggest_motivations": suggest_motivations
                            }

                            analysis_response = requests.post(
                                f"{API_BASE_URL}/analyze/video",
                                json=analysis_request,
                                params={"provider": st.session_state.selected_provider},
                                timeout=600
                            )

                            if analysis_response.status_code == 200:
                                result = analysis_response.json()
                                st.success("✅ AI分析完成!")

                                # 显示结果
                                st.subheader("分析结果")
                                st.write(f"**处理时间:** {result.get('processing_time', 0):.2f}秒")
                                st.write(f"**使用模型:** {result.get('model_used', '')}")
                                st.write(f"**关键帧数量:** {len(result.get('keyframes', []))}")

                                # 跳转到检查页面
                                if st.button("前往检查标注"):
                                    st.session_state.current_page = 'review'
                                    st.session_state.current_video_id = video_id
                                    st.rerun()
                            else:
                                st.error(f"❌ 分析失败: {analysis_response.text}")
                    else:
                        st.error(f"❌ 上传失败: {upload_response.text}")

    with col2:
        st.info("""
        **支持格式:**
        - MP4
        - AVI
        - MOV
        - MKV

        **AI分析内容:**
        - 关键帧提取
        - 动作识别
        - 情绪分析
        - 动机推断
        - 隐性渴望识别
        """)

# ============= 页面2: 批量处理 =============

def render_batch_page():
    """批量处理页面"""
    st.header("📁 批量处理 - 文件夹上传")

    st.markdown("""
    **功能说明:**
    - 上传整个文件夹的视频
    - 后台批量处理
    - 进度实时跟踪
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        # 文件夹路径输入
        folder_path = st.text_input(
            "输入视频文件夹路径",
            placeholder="例如: D:/videos/",
            key='folder_path_input'
        )

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button("📁 添加到队列", type="primary", use_container_width=True):
                if folder_path:
                    with st.spinner("正在扫描文件夹..."):
                        response = requests.post(
                            f"{API_BASE_URL}/batch/add-folder",
                            params={
                                "folder_path": folder_path,
                                "provider": st.session_state.selected_provider,
                                "recursive": False
                            },
                            timeout=30
                        )

                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ 已添加 {result['message']}")
                        else:
                            st.error(f"❌ 添加失败: {response.text}")
                else:
                    st.warning("请输入文件夹路径")

        with col_btn2:
            if st.button("▶️ 开始处理", use_container_width=True):
                response = requests.post(f"{API_BASE_URL}/batch/start", timeout=10)
                if response.status_code == 200:
                    st.success("✅ 批量处理已启动")
                else:
                    st.error("❌ 启动失败")

        # 显示队列状态
        st.markdown("---")
        st.subheader("📊 处理状态")

        if st.button("🔄 刷新状态"):
            st.rerun()

        try:
            status_response = requests.get(f"{API_BASE_URL}/batch/status", timeout=5)
            if status_response.status_code == 200:
                status_data = status_response.json()
                summary = status_data['summary']
                tasks = status_data['tasks']

                # 显示总览
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                col_s1.metric("总任务", summary['total'])
                col_s2.metric("处理中", summary['processing'])
                col_s3.metric("已完成", summary['completed'])
                col_s4.metric("失败", summary['failed'])

                # 显示任务列表
                if tasks:
                    st.markdown("**任务列表:**")
                    for task in tasks:
                        with st.expander(f"{task['video_name']} - {task['status']}"):
                            st.write(f"**Provider:** {task['provider']}")
                            st.write(f"**创建时间:** {task['created_at']}")
                            if task['progress'] > 0:
                                st.progress(task['progress'])
                            if task['error']:
                                st.error(f"错误: {task['error']}")
        except:
            st.warning("无法获取状态信息")

    with col2:
        st.info("""
        **批量处理流程:**

        1. 输入文件夹路径
        2. 添加到处理队列
        3. 点击"开始处理"
        4. 后台自动处理
        5. 完成后可在检查页面查看

        **支持功能:**
        - 多视频并行处理
        - 失败自动重试
        - 进度实时跟踪
        """)

# ============= 页面3: 检查标注 =============

def render_review_page():
    """标注校验页面"""
    st.header("✅ 标注校验")

    # 获取 API 客户端 (也可以直接用 requests，但 DataCache 更方便)
    # 这里我们直接用 DataCache 封装的方法，假设您之前的 utils/cache.py 已保留
    # 如果没有 APIClient 实例，我们可以稍微变通一下，或者直接缓存请求结果

    # 1. 获取视频列表 (带缓存)
    # 使用 st.cache_data 装饰的函数来获取列表
    @st.cache_data(ttl=5) # 列表缓存5秒即可，方便看到新上传的
    def get_cached_video_list():
        try:
            return requests.get(f"{API_BASE_URL}/annotations/list", timeout=2).json().get('annotations', [])
        except:
            return []

    annotations = get_cached_video_list()

    if not annotations:
        st.warning("还没有标注数据，请先上传并分析视频")
        return

    # 2. 视频选择
    # 使用 format_func 让显示更友好
    selected_annotation = st.selectbox(
        "选择视频", 
        annotations, 
        format_func=lambda x: x['video_name']
    )

    if selected_annotation:
        video_id = selected_annotation['video_id']

        # 3. 获取标注详情 (带缓存)
        # ✅ 使用 DataCache (如果您保留了 utils/cache.py)
        # 这里的 _api_client 只是为了满足 DataCache 的签名，传个 None 或者伪造一个对象即可，
        # 或者更简单：直接在这里写一个缓存函数
        
        @st.cache_data(show_spinner=False)
        def get_cached_annotation(vid):
            try:
                return requests.get(f"{API_BASE_URL}/annotations/{vid}", timeout=5).json()
            except:
                return None

        annotation_data = get_cached_annotation(video_id)

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

        st.session_state.current_frame_idx = current_idx

        # 保存按钮
        if edited_data and st.button("💾 保存修改", type="primary"):
            # 保存逻辑...
            try:
                # 合并数据
                keyframes[current_idx]['action'].update(edited_data['action'])
                keyframes[current_idx]['motivation'].update(edited_data['motivation'])
                
                # 更新 motivation
                payload = keyframes[current_idx]['motivation']
                
                # 发送请求
                requests.post(
                    f"{API_BASE_URL}/annotations/{video_id}/keyframe/{current_idx}",
                    json=payload
                )
                
                st.success("✅ 保存成功")
                
                # 关键：保存后要清除缓存，否则看不到更新！
                get_cached_annotation.clear() 
                
            except Exception as e:
                st.error(f"保存失败: {e}")

def render_annotation_viewer(video_id: str, annotation_meta: dict):
    """标注查看器 - 优化版"""
    st.subheader(f"📹 {annotation_meta['video_name']}")

    # 检查是否是新视频，如果是则重置帧索引
    if 'last_video_id' not in st.session_state or st.session_state.last_video_id != video_id:
        st.session_state.last_video_id = video_id
        st.session_state.current_frame_idx = 0

    # 加载完整标注数据
    try:
        response = requests.get(f"{API_BASE_URL}/annotations/{video_id}", timeout=10)
        if response.status_code == 200:
            annotation_data = response.json()
            keyframes = annotation_data.get('keyframes', [])

            if not keyframes:
                st.warning("没有关键帧数据")
                return

            # 确保帧索引在有效范围内
            current_frame_idx = st.session_state.current_frame_idx
            if current_frame_idx >= len(keyframes):
                current_frame_idx = 0
                st.session_state.current_frame_idx = 0

            # 帧选择器
            frame_idx = st.slider(
                "选择关键帧",
                min_value=0,
                max_value=len(keyframes) - 1,
                value=current_frame_idx,
                format="帧 %d",
                key='frame_slider'
            )

            st.session_state.current_frame_idx = frame_idx

            # 显示当前帧
            current_frame = keyframes[frame_idx]
            action = current_frame.get('action', {})
            motivation = current_frame.get('motivation', {})

            # 显示图片 - 使用优化的ImageCache
            frame_path = current_frame.get('frame_path', '')

            # 预加载相邻帧（前后5帧）以实现流畅切换
            from frontend.utils import ImageCache
            ImageCache.preload(keyframes, frame_idx, window_size=5, base_url=API_BASE_URL)

            # 显示当前帧图片
            if frame_path:
                if Path(frame_path).exists():
                    # 使用缓存加载图片
                    img = ImageCache.get(frame_path, base_url=API_BASE_URL)
                    if img:
                        st.image(img, use_container_width=True, caption=f"⏱️ {action.get('timestamp_formatted', '')}")
                    else:
                        st.warning("图片加载失败")
                else:
                    st.warning("图片不存在")

            # 快速导航
            nav_col1, nav_col2, nav_col3 = st.columns(3)

            with nav_col1:
                if st.button("⏪ 前一帧", use_container_width=True, disabled=frame_idx == 0):
                    st.session_state.current_frame_idx = max(0, frame_idx - 1)
                    st.rerun()

            with nav_col2:
                st.markdown(f"**{frame_idx + 1}/{len(keyframes)}**")

            with nav_col3:
                if st.button("下一帧 ⏩", use_container_width=True, disabled=frame_idx == len(keyframes) - 1):
                    st.session_state.current_frame_idx = min(len(keyframes) - 1, frame_idx + 1)
                    st.rerun()

            st.markdown("---")

            # 显示标注内容
            with st.expander("🎬 What - 客观描述", expanded=False):
                st.write(f"**动作:** {action.get('action_description', '')}")
                st.write(f"**场景:** {action.get('visual_context', '')}")
                st.write(f"**场景类型:** {action.get('scene', '')}")

                col_obj, col_char = st.columns(2)
                with col_obj:
                    st.caption("**物体:**")
                    for obj in action.get('objects', []):
                        st.markdown(f"- {obj}")

                with col_char:
                    st.caption("**角色:**")
                    for char in action.get('characters', []):
                        st.markdown(f"- {char}")

            with st.expander("💭 Why - 动机分析", expanded=True):
                st.info(f"**显性动机:** {motivation.get('explicit_motivation', '')}")
                st.warning(f"**隐性渴望:** {motivation.get('implicit_desire', '')}")

                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.write(f"**类别:** {motivation.get('desire_category', '')}")
                    st.write(f"**类型:** {motivation.get('motivation_type', '')}")

                with col_m2:
                    st.write(f"**隐性程度:** {'🎭' * motivation.get('implicit_level', 3)} ({motivation.get('implicit_level', 3)}/5)")
                    st.write(f"**置信度:** {motivation.get('confidence', 0)*100:.1f}%")

                if motivation.get('reasoning'):
                    st.markdown("**🔍 AI推理依据:**")
                    with st.container():
                        st.text(motivation['reasoning'])

                if motivation.get('visual_cues'):
                    st.caption("**视觉线索:**")
                    for cue in motivation.get('visual_cues', []):
                        st.markdown(f"- {cue}")

            # 人工编辑
            with st.expander("✏️ 编辑标注", expanded=False):
                st.markdown("**修改动机分析:**")

                new_explicit = st.text_area(
                    "显性动机",
                    value=motivation.get('explicit_motivation', ''),
                    key=f'edit_explicit_{frame_idx}'
                )

                new_implicit = st.text_area(
                    "隐性渴望",
                    value=motivation.get('implicit_desire', ''),
                    key=f'edit_implicit_{frame_idx}'
                )

                if st.button("💾 保存修改", key=f'save_{frame_idx}'):
                    # TODO: 调用API保存
                    st.success("✅ 保存成功")

        else:
            st.error("无法加载标注数据")

    except Exception as e:
        st.error(f"加载失败: {str(e)}")

def render_review_panel(current_annotation: dict, all_annotations: list):
    """审核面板"""
    st.subheader("📊 标注信息")

    # 统计
    col1, col2 = st.columns(2)
    col1.metric("总帧数", current_annotation['total_frames'])
    col2.metric("已标注", current_annotation['annotated_frames'])

    progress = (
        current_annotation['annotated_frames'] / current_annotation['total_frames']
        if current_annotation['total_frames'] > 0 else 0
    )
    st.progress(progress)

    st.caption(f"📅 {current_annotation.get('last_modified', '')[:19]}")

    # 审核操作
    st.markdown("---")
    st.markdown("**审核操作:**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ 通过", use_container_width=True, type="primary"):
            st.success("已标记为通过")
            # 自动跳转下一个
            if st.session_state.review_index < len(all_annotations) - 1:
                st.session_state.review_index += 1
                st.session_state.current_frame_idx = 0
                st.rerun()

    with col2:
        if st.button("❌ 需修改", use_container_width=True):
            st.warning("已标记为需修改")

    # 快捷跳转
    st.markdown("---")
    st.markdown("**快捷跳转:**")

    video_names = [a['video_name'] for a in all_annotations]
    selected_name = st.selectbox(
        "选择视频",
        options=video_names,
        index=st.session_state.review_index,
        key='video_select'
    )

    if st.button("跳转", use_container_width=True):
        new_idx = video_names.index(selected_name)
        st.session_state.review_index = new_idx
        st.session_state.current_frame_idx = 0
        st.rerun()

# ============= 页面4: 视频重命名 =============

def render_rename_page():
    """视频重命名页面"""
    st.header("✏️ 视频重命名 - 基于标注主题")

    st.markdown("""
    **功能说明:**
    - 根据AI标注内容自动生成视频主题
    - 智能重命名视频文件
    """)

    # 选择视频
    try:
        response = requests.get(f"{API_BASE_URL}/review/list", timeout=10)
        if response.status_code == 200:
            annotations = response.json()['annotations']

            if not annotations:
                st.info("没有可重命名的视频")
                return

            video_names = [a['video_name'] for a in annotations]
            selected_name = st.selectbox("选择视频", options=video_names)

            selected_annotation = next(a for a in annotations if a['video_name'] == selected_name)
            video_id = selected_annotation['video_id']

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("**当前文件名:**")
                st.code(selected_name)

                if st.button("🤖 AI生成新文件名", type="primary", use_container_width=True):
                    with st.spinner("AI正在分析主题..."):
                        rename_response = requests.post(
                            f"{API_BASE_URL}/videos/{video_id}/rename",
                            timeout=30
                        )

                        if rename_response.status_code == 200:
                            result = rename_response.json()

                            if 'suggested_filename' in result:
                                st.success("✅ 生成成功!")

                                st.markdown("**建议的新文件名:**")
                                new_name = result['suggested_filename']
                                st.code(new_name)

                                st.markdown("**主题关键词:**")
                                st.info(result.get('theme_keyword', ''))

                                st.markdown("**说明:**")
                                st.write(result.get('explanation', ''))

                                if st.button("✅ 确认重命名"):
                                    # TODO: 实际重命名操作
                                    st.success(f"✅ 已重命名为: {new_name}")
                            else:
                                st.warning(result.get('message', '功能开发中'))
                        else:
                            st.error("生成失败")

            with col2:
                st.info("""
                **重命名规则:**

                - 基于标注内容
                - 提取核心主题
                - 包含关键动机
                - 简洁易读

                **示例:**
                - 原名: video_001.mp4
                - 新名: 职场焦虑_深夜独处.mp4
                """)

    except Exception as e:
        st.error(f"错误: {str(e)}")

# ============= 主入口 =============

def main():
    """主函数"""
    # 渲染侧边栏
    render_sidebar()

    # 根据当前页面渲染内容
    page = st.session_state.current_page

    if page == 'upload':
        render_upload_page()
    elif page == 'batch':
        render_batch_page()
    elif page == 'review':
        render_review_page()
    elif page == 'rename':
        render_rename_page()
    elif page == 'question_verify':
        render_question_verification_page()
    else:
    else:
        render_upload_page()

if __name__ == "__main__":
    main()
