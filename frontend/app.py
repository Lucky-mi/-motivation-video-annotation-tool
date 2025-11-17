# frontend/app.py
"""
标注平台主界面
"""
import streamlit as st
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from config.config import config
from backend.video_processor_v2 import SmartVideoProcessor

# 页面配置
st.set_page_config(
    page_title="Motivation标注平台",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化session_state
if 'current_video' not in st.session_state:
    st.session_state.current_video = None
if 'keyframes' not in st.session_state:
    st.session_state.keyframes = []
if 'video_list' not in st.session_state:
    st.session_state.video_list = []

def main():
    st.title("🎬 VLM Motivation 标注平台")
    st.markdown("---")
    
    # 侧边栏：配置和视频列表
    with st.sidebar:
        st.header("⚙️ 配置")
        
        # 提取模式选择
        extraction_mode = st.selectbox(
            "关键帧提取模式",
            options=['uniform', 'gemini'],
            format_func=lambda x: "均匀采样" if x == 'uniform' else "Gemini智能提取",
            index=0 if config.get('extraction.mode') == 'uniform' else 1
        )
        
        if extraction_mode != config.get('extraction.mode'):
            config.set('extraction.mode', extraction_mode)
            st.success(f"✅ 已切换到：{'均匀采样' if extraction_mode == 'uniform' else 'Gemini智能提取'}")
        
        # 根据模式显示不同配置
        if extraction_mode == 'uniform':
            st.subheader("均匀采样配置")
            interval = st.slider(
                "采样间隔（秒）",
                min_value=1.0,
                max_value=30.0,
                value=float(config.get('extraction.interval_seconds', 5.0)),
                step=0.5
            )
            config.set('extraction.interval_seconds', interval)
            
            max_frames = st.number_input(
                "最大帧数",
                min_value=10,
                max_value=200,
                value=int(config.get('extraction.max_frames', 50))
            )
            config.set('extraction.max_frames', max_frames)
        
        else:  # gemini模式
            st.subheader("Gemini配置")
            gemini_key = st.text_input(
                "Gemini API Key",
                value=config.get_api_key('gemini') or "",
                type="password"
            )
            if gemini_key:
                config.set_api_key('gemini', gemini_key)
                st.success("✅ API Key已保存")
            else:
                st.warning("⚠️ 请输入Gemini API Key")
        
        st.markdown("---")
        
        # 视频上传区域
        st.header("📁 视频管理")
        
        # 方式1：多文件上传
        with st.expander("📤 上传视频文件", expanded=True):
            uploaded_files = st.file_uploader(
                "选择视频文件（可多选）",
                type=['mp4', 'avi', 'mov', 'mkv'],
                accept_multiple_files=True,
                key='file_uploader'
            )
            
            if uploaded_files:
                if st.button("💾 保存上传的视频"):
                    video_dir = Path(config.get('paths.videos'))
                    video_dir.mkdir(parents=True, exist_ok=True)
                    
                    saved_count = 0
                    for uploaded_file in uploaded_files:
                        video_path = video_dir / uploaded_file.name
                        with open(video_path, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        saved_count += 1
                    
                    st.success(f"✅ 已保存 {saved_count} 个视频文件")
                    st.rerun()
        
        # 方式2：本地文件夹
        with st.expander("📂 从本地文件夹加载"):
            local_folder = st.text_input(
                "输入文件夹路径",
                value=config.get('paths.videos'),
                key='local_folder'
            )
            
            if st.button("🔄 刷新视频列表"):
                load_videos_from_folder(local_folder)
        
        st.markdown("---")
        
        # 显示视频列表
        st.header("📋 视频列表")
        if st.session_state.video_list:
            selected_video = st.selectbox(
                f"共 {len(st.session_state.video_list)} 个视频",
                options=st.session_state.video_list,
                format_func=lambda x: Path(x).name
            )
            
            if st.button("▶️ 加载选中视频"):
                st.session_state.current_video = selected_video
                st.session_state.keyframes = []
                st.rerun()
        else:
            st.info("暂无视频，请上传或从文件夹加载")
    
    # 主区域：视频处理或标注
    if st.session_state.get('show_annotation_editor', False):
        # 显示标注编辑器
        from frontend.annotation_editor import editor

        # 返回按钮
        if st.button("⬅️ 返回视频列表"):
            st.session_state.show_annotation_editor = False
            st.rerun()

        st.markdown("---")
        editor.render()

    elif st.session_state.current_video:
        show_video_processing_area()

    else:
        st.info("👈 请从侧边栏选择或上传视频")


def load_videos_from_folder(folder_path: str):
    """从文件夹加载视频列表"""
    folder = Path(folder_path)
    if not folder.exists():
        st.error(f"❌ 文件夹不存在: {folder_path}")
        return
    
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    videos = [
        str(f) for f in folder.rglob('*') 
        if f.suffix.lower() in video_extensions
    ]
    
    st.session_state.video_list = sorted(videos)
    st.success(f"✅ 找到 {len(videos)} 个视频文件")


def show_video_processing_area():
    """显示视频处理区域"""
    video_path = st.session_state.current_video
    video_name = Path(video_path).name
    
    st.header(f"🎬 当前视频: {video_name}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 显示视频
        st.video(video_path)
    
    with col2:
        st.subheader("视频信息")
        try:
            processor = SmartVideoProcessor(
                output_dir=config.get('paths.keyframes'),
                gemini_api_key=config.get_api_key('gemini')
            )
            
            # 获取视频信息
            video_info = processor.get_video_info(video_path)
            st.metric("时长", video_info['duration_formatted'])
            st.metric("分辨率", f"{video_info['width']}x{video_info['height']}")
            st.metric("帧率", f"{video_info['fps']:.2f} fps")
            
        except Exception as e:
            st.error(f"❌ 读取视频失败: {str(e)}")
    
    st.markdown("---")
    
    # 提取关键帧按钮
    mode = config.get('extraction.mode')
    
    if st.button(f"🔍 提取关键帧 ({'智能模式' if mode == 'gemini' else '均匀采样'})", type="primary"):
        extract_keyframes(video_path, mode)
    
    # 显示已提取的关键帧
    if st.session_state.keyframes:
        show_keyframes()

        # 添加标注按钮
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📝 开始标注", type="primary", use_container_width=True):
                # 加载或创建标注
                from frontend.annotation_editor import editor
                annotation = editor.load_or_create_annotation(
                    st.session_state.current_video,
                    st.session_state.keyframes
                )
                st.session_state.current_annotation = annotation
                st.session_state.show_annotation_editor = True
                st.rerun()



def extract_keyframes(video_path: str, mode: str):
    """提取关键帧"""
    processor = SmartVideoProcessor(
        output_dir=config.get('paths.keyframes'),
        gemini_api_key=config.get_api_key('gemini')
    )
    
    with st.spinner(f"⏳ 正在提取关键帧..."):
        try:
            if mode == 'uniform':
                # 均匀采样
                keyframes = processor.extract_uniform_frames(
                    video_path,
                    interval_seconds=config.get('extraction.interval_seconds'),
                    max_frames=config.get('extraction.max_frames')
                )
                st.session_state.keyframes = keyframes
                st.success(f"✅ 提取完成！共 {len(keyframes)} 帧")
            
            elif mode == 'gemini':
                # Gemini智能分析
                if not config.get_api_key('gemini'):
                    st.error("❌ 请先配置Gemini API Key")
                    return
                
                # 分析视频
                analysis = processor.analyze_video_with_gemini(video_path)
                
                if 'error' in analysis:
                    st.error(f"❌ Gemini分析失败: {analysis['error']}")
                    with st.expander("查看原始返回"):
                        st.text(analysis.get('raw_response', ''))
                    return
                
                # 提取关键帧
                timestamps = analysis.get('suggested_keyframe_timestamps', [])
                keyframes = processor.extract_suggested_frames(video_path, timestamps)
                
                st.session_state.keyframes = keyframes
                st.session_state.gemini_analysis = analysis
                
                st.success(f"✅ Gemini分析完成！提取了 {len(keyframes)} 个关键帧")
                
                # 显示分析结果
                with st.expander("📊 查看Gemini分析结果", expanded=True):
                    st.json(analysis)
        
        except Exception as e:
            st.error(f"❌ 提取失败: {str(e)}")
            import traceback
            st.code(traceback.format_exc())


def show_keyframes():
    """显示提取的关键帧"""
    st.subheader(f"📸 关键帧预览 (共 {len(st.session_state.keyframes)} 帧)")
    
    # 网格显示
    cols_per_row = 4
    keyframes = st.session_state.keyframes
    
    for i in range(0, len(keyframes), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(keyframes):
                frame = keyframes[i + j]
                with col:
                    st.image(
                        frame['frame_path'],
                        caption=f"T={frame['timestamp']:.1f}s",
                        use_container_width=True
                    )


if __name__ == "__main__":
    # 自动加载视频列表
    if not st.session_state.video_list:
        video_dir = Path(config.get('paths.videos'))
        if video_dir.exists():
            load_videos_from_folder(str(video_dir))
    
    main()