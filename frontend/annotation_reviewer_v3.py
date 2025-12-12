# frontend/annotation_reviewer_v3.py
"""
AI标注质量检查平台 V3 - 修复版
修复：
1. HTML渲染问题
2. 视频片段播放（只播放指定时间段）
3. DOM错误
4. 美观的UI
"""
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import sys
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import base64

sys.path.append(str(Path(__file__).parent.parent))

# 页面配置
st.set_page_config(
    page_title="标注质量检查平台 V3",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 主容器样式 */
    .main {
        padding: 1rem;
    }

    /* 卡片样式 */
    .segment-card {
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        background: linear-gradient(to bottom, #ffffff, #f8f9fa);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    .segment-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }

    .segment-card.approved {
        border-left: 6px solid #28a745;
        background: linear-gradient(to bottom, #f0fff4, #e6f9ef);
    }

    .segment-card.needs-mod {
        border-left: 6px solid #ffc107;
        background: linear-gradient(to bottom, #fffbf0, #fff8e1);
    }

    .segment-card.to-delete {
        border-left: 6px solid #dc3545;
        background: linear-gradient(to bottom, #fff5f5, #ffebee);
    }

    /* 徽章样式 */
    .type-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 13px;
        font-weight: 600;
        margin: 2px;
    }

    .type-desire-motivation {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        border: 1px solid #b1dfbb;
    }

    .type-desire-transition {
        background: linear-gradient(135deg, #cce5ff 0%, #b8daff 100%);
        color: #004085;
        border: 1px solid #9fcdff;
    }

    .type-behavioral-sequence {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        color: #856404;
        border: 1px solid #ffe69c;
    }

    .type-key-segment-qa {
        background: linear-gradient(135deg, #e2d5f1 0%, #d6c8e6 100%);
        color: #6f42c1;
        border: 1px solid #c9b8df;
    }

    /* 统计卡片 */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 8px 0;
    }

    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }

    /* 角色卡片 */
    .character-card {
        background: linear-gradient(to bottom right, #f8f9fa, #e9ecef);
        border-radius: 10px;
        padding: 18px;
        margin: 12px 0;
        border-left: 4px solid #007bff;
    }

    /* 证据项 */
    .evidence-item {
        background: white;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 6px 0;
        font-size: 14px;
        border-left: 3px solid #17a2b8;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* 时间轴样式 */
    .timeline-container {
        background: white;
        padding: 20px;
        border-radius: 10px;
        margin: 16px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .timeline-bar {
        height: 40px;
        background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
        border-radius: 8px;
        position: relative;
        margin: 16px 0;
        border: 1px solid #dee2e6;
        overflow: hidden;
    }

    .timeline-segment {
        position: absolute;
        height: 100%;
        border-radius: 4px;
        opacity: 0.85;
        transition: all 0.2s ease;
        cursor: pointer;
    }

    .timeline-segment:hover {
        opacity: 1;
        transform: scaleY(1.1);
        z-index: 10;
    }

    .timeline-segment.active {
        opacity: 1;
        border: 2px solid #000;
        z-index: 20;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }

    /* 视频容器 */
    .video-container {
        background: #000;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        margin: 16px 0;
    }

    /* 信息面板 */
    .info-panel {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 12px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .info-panel h3 {
        color: #495057;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid #e9ecef;
    }

    /* 按钮组 */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# 配置路径
BASE_DIR = Path(__file__).parent.parent
ANNOTATIONS_DIR = BASE_DIR / "data" / "annotations_test"
REVIEW_STATUS_FILE = BASE_DIR / "data" / "review_status.json"

# 视频目录 - 尝试多个可能的位置
VIDEOS_DIRS = [
    BASE_DIR / "data" / "Youtube_videos",
    BASE_DIR / "data" / "videos",
    Path("D:/Desire-VQA/video_anno/data/Youtube_videos"),
    Path("D:/Desire-VQA/video_anno/data/videos"),
]

# 类型配置
SEGMENT_TYPES = {
    'desire_motivation': {'name': '动机分析', 'icon': '🎯', 'color': '#28a745'},
    'desire_transition': {'name': '欲望转变', 'icon': '🔄', 'color': '#007bff'},
    'behavioral_sequence': {'name': '行为序列', 'icon': '📊', 'color': '#ffc107'},
    'key_segment_qa': {'name': 'QA片段', 'icon': '❓', 'color': '#6f42c1'}
}


# ============= 工具函数 =============

def load_review_status() -> Dict:
    """加载审核状态"""
    if REVIEW_STATUS_FILE.exists():
        with open(REVIEW_STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_review_status(status: Dict):
    """保存审核状态"""
    REVIEW_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def load_annotation(file_path: Path) -> Optional[Dict]:
    """加载标注文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"加载标注失败: {e}")
        return None


def save_annotation(file_path: Path, data: Dict):
    """保存标注文件"""
    backup_dir = Path("data/annotations_backup")
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return backup_path


def get_video_path(annotation: Dict) -> Optional[Path]:
    """获取视频路径 - 增强版，支持多种路径查找"""
    video_id = annotation.get('video_id', '')
    video_path_str = annotation.get('video_path', '')

    paths_to_try = []

    # 1. 首先尝试JSON中指定的路径
    if video_path_str:
        # 处理Windows路径
        normalized = video_path_str.replace('\\', '/')
        paths_to_try.append(Path(normalized))
        paths_to_try.append(BASE_DIR / normalized)
        # 也尝试主仓库路径
        paths_to_try.append(Path("D:/Desire-VQA/video_anno") / normalized)

    # 2. 在所有可能的视频目录中查找
    for videos_dir in VIDEOS_DIRS:
        for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            paths_to_try.append(videos_dir / f"{video_id}{ext}")

    # 3. 尝试所有路径
    for p in paths_to_try:
        if p and p.exists():
            return p

    return None


def format_time(seconds: float) -> str:
    """格式化时间"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def get_all_segments(annotation: Dict) -> List[Dict]:
    """提取所有片段"""
    segments = []

    # desire_motivation_analysis
    for item in annotation.get('desire_motivation_analysis', []):
        temporal = item.get('temporal_scope', {})
        start = temporal.get('start_seconds', 0)
        end = temporal.get('end_seconds', 0)
        if end > start:
            segments.append({
                'type': 'desire_motivation',
                'id': item.get('analysis_id', ''),
                'character': item.get('character_id', ''),
                'label': item.get('desire_label', ''),
                'start': start,
                'end': end,
                'intensity': item.get('intensity', ''),
                'maslow_level': item.get('maslow_level', ''),
                'bdi_component': item.get('bdi_component', ''),
                'desire_type': item.get('desire_type', ''),
                'confidence': item.get('confidence', ''),
                'reasoning': item.get('reasoning_chain', ''),
                'evidence': item.get('supporting_evidence', []),
                'alternatives': item.get('alternative_interpretations', []),
                'raw_data': item
            })

    # desire_transitions
    for item in annotation.get('desire_transitions', []):
        temporal = item.get('temporal_boundaries', {})
        start = temporal.get('onset_timestamp_seconds', 0)
        end = temporal.get('offset_timestamp_seconds', 0)
        if end > start:
            segments.append({
                'type': 'desire_transition',
                'id': item.get('transition_id', ''),
                'character': item.get('character_id', ''),
                'label': f"{item.get('desire_before', {}).get('label', '')} -> {item.get('desire_after', {}).get('label', '')}",
                'start': start,
                'end': end,
                'transition_type': item.get('transition_type', ''),
                'desire_before': item.get('desire_before', {}),
                'desire_after': item.get('desire_after', {}),
                'trigger': item.get('trigger_event', {}),
                'markers': item.get('behavioral_markers', []),
                'visual_marker': item.get('visual_marker_of_change', ''),
                'interpretation': item.get('psychological_interpretation', ''),
                'raw_data': item
            })

    # behavioral_sequence
    for item in annotation.get('behavioral_sequence', []):
        start = item.get('timestamp_start_seconds', 0)
        end = item.get('timestamp_end_seconds', 0)
        if end > start:
            segments.append({
                'type': 'behavioral_sequence',
                'id': item.get('sequence_id', ''),
                'character': item.get('character_id', ''),
                'label': item.get('behavior_category', ''),
                'start': start,
                'end': end,
                'description': item.get('behavior_description', ''),
                'intensity': item.get('intensity', ''),
                'target': item.get('target', ''),
                'mental_state': item.get('inferred_mental_state', ''),
                'relevance': item.get('relevance_to_desire', ''),
                'raw_data': item
            })

    # key_segments_for_qa
    for item in annotation.get('key_segments_for_qa', []):
        start = item.get('start_timestamp_seconds', 0)
        end = item.get('end_timestamp_seconds', 0)
        if end > start:
            segments.append({
                'type': 'key_segment_qa',
                'id': item.get('segment_id', ''),
                'character': '',
                'label': item.get('segment_description', '')[:50],
                'start': start,
                'end': end,
                'description': item.get('segment_description', ''),
                'significance': item.get('psychological_significance', ''),
                'qa_types': item.get('potential_qa_types', []),
                'difficulty': item.get('difficulty_level', ''),
                'recommended': item.get('recommended_for_qa', False),
                'raw_data': item
            })

    segments.sort(key=lambda x: x['start'])
    return segments


def get_character_info(annotation: Dict, character_id: str) -> Optional[Dict]:
    """获取角色信息"""
    for char in annotation.get('characters', []):
        if char.get('character_id') == character_id:
            return char
    return None


# ============= 视频播放器组件 =============

def create_video_player(video_path: Path, start_time: float, end_time: float, segment_id: str) -> str:
    """创建自定义视频播放器HTML（只播放指定片段）"""

    # 读取视频文件并转换为base64编码（解决浏览器安全限制）
    try:
        with open(video_path, 'rb') as f:
            video_bytes = f.read()
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
    except Exception as e:
        return f'<p style="color: red;">视频加载失败: {e}</p>'

    # 根据文件扩展名确定MIME类型
    suffix = video_path.suffix.lower()
    mime_types = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.mkv': 'video/x-matroska'
    }
    mime_type = mime_types.get(suffix, 'video/mp4')

    # 创建HTML5视频播放器
    html = f"""
    <div class="video-container" style="margin: 16px 0;">
        <video id="video-{segment_id}"
               width="100%"
               style="max-height: 500px; display: block; background: #000;"
               controls
               preload="auto">
            <source src="data:{mime_type};base64,{video_base64}" type="{mime_type}">
            您的浏览器不支持视频播放。
        </video>

        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); color: white; padding: 16px; text-align: center; border-radius: 0 0 12px 12px;">
            <div style="margin-bottom: 8px;">
                <strong style="font-size: 16px;">⏱️ 片段播放范围</strong>
            </div>
            <div style="font-size: 18px; font-weight: bold;">
                <span style="color: #4CAF50; background: rgba(76, 175, 80, 0.2); padding: 4px 12px; border-radius: 4px;">
                    {format_time(start_time)}
                </span>
                <span style="margin: 0 12px; color: #fff;">→</span>
                <span style="color: #f44336; background: rgba(244, 67, 54, 0.2); padding: 4px 12px; border-radius: 4px;">
                    {format_time(end_time)}
                </span>
            </div>
            <div style="margin-top: 8px; color: #aaa; font-size: 14px;">
                📏 时长: <strong>{end_time - start_time:.1f}秒</strong>
            </div>
        </div>
    </div>

    <script>
        (function() {{
            const video = document.getElementById('video-{segment_id}');
            const startTime = {start_time};
            const endTime = {end_time};
            let hasSetInitialTime = false;

            // 设置初始播放位置
            video.addEventListener('loadedmetadata', function() {{
                if (!hasSetInitialTime) {{
                    video.currentTime = startTime;
                    hasSetInitialTime = true;
                }}
            }});

            // 如果元数据已加载
            if (video.readyState >= 1) {{
                video.currentTime = startTime;
                hasSetInitialTime = true;
            }}

            // 监听时间更新，确保只播放片段
            video.addEventListener('timeupdate', function() {{
                if (video.currentTime < startTime - 0.1) {{
                    video.currentTime = startTime;
                }}
                if (video.currentTime >= endTime) {{
                    video.pause();
                    video.currentTime = startTime;
                }}
            }});

            // 当用户拖动进度条时，限制在片段范围内
            video.addEventListener('seeking', function() {{
                if (video.currentTime < startTime) {{
                    video.currentTime = startTime;
                }}
                if (video.currentTime > endTime) {{
                    video.currentTime = endTime;
                }}
            }});

            // 播放结束后回到开始
            video.addEventListener('ended', function() {{
                video.currentTime = startTime;
            }});

            // 添加循环播放按钮功能
            video.addEventListener('pause', function() {{
                // 如果暂停在结束位置，回到开始
                if (Math.abs(video.currentTime - endTime) < 0.5) {{
                    video.currentTime = startTime;
                }}
            }});
        }})();
    </script>
    """

    return html


def render_video_player_with_segment(video_path: Path, segment: Dict):
    """渲染视频播放器（片段播放）"""
    if not video_path or not video_path.exists():
        st.error("❌ 视频文件不存在")
        st.info(f"尝试路径: {video_path}")

        # 显示调试信息
        with st.expander("🔍 查看所有尝试的路径"):
            st.markdown("**已检查的视频目录：**")
            for vdir in VIDEOS_DIRS:
                exists = "✅" if vdir.exists() else "❌"
                st.text(f"{exists} {vdir}")
        return

    st.markdown(f"### 🎬 视频片段播放")

    # 显示视频信息
    file_size_mb = video_path.stat().st_size / (1024 * 1024)
    st.caption(f"📁 {video_path.name} ({file_size_mb:.2f} MB)")

    if file_size_mb > 100:
        st.warning(f"⚠️ 视频文件较大 ({file_size_mb:.0f} MB)，加载可能需要一些时间...")

    # 创建自定义视频播放器
    with st.spinner("🔄 正在加载视频..."):
        video_html = create_video_player(
            video_path,
            segment['start'],
            segment['end'],
            segment['id']
        )

    # 渲染HTML
    components.html(video_html, height=600, scrolling=False)

    # 显示时间信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⏱️ 开始时间", format_time(segment['start']))
    with col2:
        st.metric("⏱️ 结束时间", format_time(segment['end']))
    with col3:
        st.metric("⏳ 片段时长", f"{segment['end'] - segment['start']:.1f}秒")


# ============= UI组件 =============

def render_timeline_visualization(segments: List[Dict], duration: float, current_idx: int):
    """渲染时间轴可视化 - 使用 Streamlit components 确保正确渲染"""
    if duration <= 0:
        duration = max(seg['end'] for seg in segments) if segments else 60

    st.markdown("### 📊 时间轴可视化")
    st.caption(f"视频总时长: {format_time(duration)} | 当前片段: {current_idx + 1}/{len(segments)}")

    # 构建完整的HTML（包含CSS和交互）
    segments_data = []
    for idx, seg in enumerate(segments):
        left = (seg['start'] / duration) * 100
        width = ((seg['end'] - seg['start']) / duration) * 100
        color = SEGMENT_TYPES.get(seg['type'], {}).get('color', '#999')
        is_active = (idx == current_idx)

        segments_data.append({
            'left': left,
            'width': max(width, 0.5),
            'color': color,
            'is_active': is_active,
            'label': seg['label'][:30],
            'start': format_time(seg['start']),
            'end': format_time(seg['end']),
            'type_name': SEGMENT_TYPES.get(seg['type'], {}).get('name', seg['type'])
        })

    # 创建时间刻度
    time_marks = []
    for i in range(11):
        time_point = (duration / 10) * i
        time_marks.append({
            'position': (i / 10) * 100,
            'time': format_time(time_point)
        })

    # 构建HTML
    timeline_html = f'''
    <div style="background: white; padding: 20px; border-radius: 10px; margin: 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <!-- 时间轴容器 -->
        <div style="
            height: 40px;
            background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
            border-radius: 8px;
            position: relative;
            margin: 16px 0;
            border: 1px solid #dee2e6;
            overflow: hidden;
        ">
    '''

    # 添加所有片段
    for seg in segments_data:
        opacity = '1' if seg['is_active'] else '0.75'
        border = '3px solid #000' if seg['is_active'] else '1px solid rgba(0,0,0,0.2)'
        z_index = '100' if seg['is_active'] else '10'
        transform = 'scaleY(1.15)' if seg['is_active'] else 'scaleY(1)'
        box_shadow = '0 4px 12px rgba(0,0,0,0.4)' if seg['is_active'] else 'none'

        timeline_html += f'''
        <div style="
            position: absolute;
            left: {seg['left']}%;
            width: {seg['width']}%;
            height: 100%;
            background-color: {seg['color']};
            opacity: {opacity};
            border: {border};
            z-index: {z_index};
            border-radius: 4px;
            transform: {transform};
            transition: all 0.3s ease;
            box-shadow: {box_shadow};
            cursor: pointer;
        " title="{seg['type_name']}: {seg['label']} ({seg['start']}-{seg['end']})">
        </div>
        '''

    timeline_html += '</div>'

    # 添加时间刻度
    timeline_html += '<div style="display: flex; justify-content: space-between; margin-top: 8px;">'
    for mark in time_marks:
        timeline_html += f'''
        <div style="
            flex: 1;
            text-align: center;
            font-size: 12px;
            color: #6c757d;
        ">{mark['time']}</div>
        '''
    timeline_html += '</div>'

    # 添加图例
    timeline_html += '''
    <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #dee2e6;">
        <div style="display: flex; gap: 16px; flex-wrap: wrap; justify-content: center;">
    '''

    for seg_type, info in SEGMENT_TYPES.items():
        timeline_html += f'''
        <div style="display: flex; align-items: center; gap: 6px;">
            <div style="
                width: 16px;
                height: 16px;
                background-color: {info['color']};
                border-radius: 3px;
                border: 1px solid rgba(0,0,0,0.2);
            "></div>
            <span style="font-size: 13px; color: #495057;">{info['icon']} {info['name']}</span>
        </div>
        '''

    timeline_html += '</div></div></div>'

    # 使用 components.html 渲染
    components.html(timeline_html, height=200, scrolling=False)


def render_segment_detail_panel(segment: Dict, annotation: Dict):
    """渲染片段详情面板"""
    seg_type = segment['type']
    type_info = SEGMENT_TYPES.get(seg_type, {})

    st.markdown('<div class="info-panel">', unsafe_allow_html=True)
    st.markdown(f"### {type_info.get('icon', '📌')} {type_info.get('name', seg_type)}")

    # 基本信息
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**ID:** `{segment['id']}`")
        if segment['character']:
            st.markdown(f"**👤 角色:** {segment['character']}")
    with col2:
        st.markdown(f"**🏷️ 标签:** {segment['label']}")

    st.markdown("---")

    # 根据类型渲染详情
    if seg_type == 'desire_motivation':
        render_desire_motivation_panel(segment, annotation)
    elif seg_type == 'desire_transition':
        render_desire_transition_panel(segment, annotation)
    elif seg_type == 'behavioral_sequence':
        render_behavioral_sequence_panel(segment, annotation)
    elif seg_type == 'key_segment_qa':
        render_key_segment_panel(segment, annotation)

    # 角色信息
    if segment['character']:
        char_info = get_character_info(annotation, segment['character'])
        if char_info:
            with st.expander("👤 角色详细信息"):
                render_character_card(char_info)

    st.markdown('</div>', unsafe_allow_html=True)


def render_desire_motivation_panel(segment: Dict, annotation: Dict):
    """渲染动机分析面板"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**💪 强度**")
        intensity_map = {'strong': '🔴 强', 'moderate': '🟡 中', 'weak': '🟢 弱'}
        st.markdown(intensity_map.get(segment.get('intensity', ''), segment.get('intensity', 'N/A')))

    with col2:
        st.markdown("**🎯 马斯洛层级**")
        maslow_map = {
            'physiological': '🍽️ 生理',
            'safety': '🛡️ 安全',
            'belonging': '👥 归属',
            'esteem': '🏆 尊重',
            'self_actualization': '🌟 自我实现'
        }
        st.markdown(maslow_map.get(segment.get('maslow_level', ''), segment.get('maslow_level', 'N/A')))

    with col3:
        st.markdown("**🧠 BDI组件**")
        bdi_map = {'belief': '💭 信念', 'desire': '❤️ 欲望', 'intention': '🎯 意图'}
        st.markdown(bdi_map.get(segment.get('bdi_component', ''), segment.get('bdi_component', 'N/A')))

    with col4:
        st.markdown("**📊 置信度**")
        conf = segment.get('confidence', 'N/A')
        if conf in ['high', 'moderate', 'low']:
            conf_map = {'high': '🟢 高', 'moderate': '🟡 中', 'low': '🔴 低'}
            st.markdown(conf_map.get(conf, conf))
        else:
            st.markdown(str(conf))

    with st.expander("🔗 推理链条", expanded=True):
        reasoning = segment.get('reasoning', '无推理链条')
        if isinstance(reasoning, list):
            for idx, step in enumerate(reasoning, 1):
                st.markdown(f"{idx}. {step}")
        else:
            st.info(reasoning)

    with st.expander("📋 支撑证据"):
        evidence = segment.get('evidence', [])
        if evidence:
            for e in evidence:
                st.markdown(f"""
                <div class="evidence-item">
                    <strong>⏱️ {format_time(e.get('timestamp_seconds', 0))}</strong>
                    <span style="color: #007bff;">[{e.get('behavior_type', '')}]</span>: {e.get('description', '')}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("无证据")

    with st.expander("🔄 替代解释"):
        alternatives = segment.get('alternatives', [])
        if alternatives:
            for idx, alt in enumerate(alternatives, 1):
                st.markdown(f"**{idx}. {alt.get('alternative_label', '')}**")
                st.markdown(f"📝 推理: {alt.get('reasoning', '')}")
                st.markdown(f"⚠️ _为何非主要: {alt.get('why_not_primary', '')}_")
                st.markdown("---")
        else:
            st.caption("无替代解释")


def render_desire_transition_panel(segment: Dict, annotation: Dict):
    """渲染欲望转变面板"""
    st.markdown(f"**🔄 转变类型:** {segment.get('transition_type', 'N/A')}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📉 转变前**")
        before = segment.get('desire_before', {})
        st.markdown(f"- 标签: {before.get('label', 'N/A')}")
        st.markdown(f"- 强度: {before.get('intensity', 'N/A')}")
        st.markdown(f"- 马斯洛: {before.get('maslow_level', 'N/A')}")

    with col2:
        st.markdown("**📈 转变后**")
        after = segment.get('desire_after', {})
        st.markdown(f"- 标签: {after.get('label', 'N/A')}")
        st.markdown(f"- 强度: {after.get('intensity', 'N/A')}")
        st.markdown(f"- 马斯洛: {after.get('maslow_level', 'N/A')}")

    trigger = segment.get('trigger', {})
    if trigger:
        with st.expander("⚡ 触发事件", expanded=True):
            st.markdown(f"**⏱️ 时间:** {format_time(trigger.get('timestamp_seconds', 0))}")
            st.markdown(f"**📌 类型:** {trigger.get('trigger_type', 'N/A')}")
            st.info(trigger.get('description', ''))

    with st.expander("🔖 行为标记"):
        markers = segment.get('markers', [])
        if markers:
            for m in markers:
                st.markdown(f"""
                <div class="evidence-item">
                    <strong>⏱️ {format_time(m.get('timestamp_seconds', 0))}</strong>
                    <span style="color: #007bff;">[{m.get('marker_type', '')}]</span>: {m.get('description', '')}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("无标记")

    if segment.get('visual_marker'):
        st.markdown(f"**👁️ 视觉标记:** {segment.get('visual_marker')}")

    with st.expander("🧠 心理解释"):
        st.info(segment.get('interpretation', '无解释'))


def render_behavioral_sequence_panel(segment: Dict, annotation: Dict):
    """渲染行为序列面板"""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**📊 行为类别:** {segment.get('label', 'N/A')}")
        intensity_map = {'strong': '🔴 强', 'moderate': '🟡 中', 'weak': '🟢 弱'}
        st.markdown(f"**💪 强度:** {intensity_map.get(segment.get('intensity', ''), segment.get('intensity', 'N/A'))}")

    with col2:
        st.markdown(f"**🎯 目标:** {segment.get('target', 'N/A')}")

    with st.expander("📝 行为描述", expanded=True):
        st.info(segment.get('description', '无描述'))

    st.markdown(f"**🧠 推断心理状态:** {segment.get('mental_state', 'N/A')}")

    with st.expander("🔗 与欲望的关联"):
        st.info(segment.get('relevance', '无关联说明'))


def render_key_segment_panel(segment: Dict, annotation: Dict):
    """渲染QA片段面板"""
    col1, col2 = st.columns(2)

    with col1:
        difficulty_map = {'easy': '🟢 简单', 'medium': '🟡 中等', 'hard': '🔴 困难'}
        st.markdown(f"**📊 难度:** {difficulty_map.get(segment.get('difficulty', ''), segment.get('difficulty', 'N/A'))}")

    with col2:
        st.markdown(f"**✅ 推荐QA:** {'✅ 是' if segment.get('recommended') else '❌ 否'}")

    qa_types = segment.get('qa_types', [])
    if qa_types:
        st.markdown(f"**❓ QA类型:** {', '.join(qa_types)}")

    with st.expander("📝 片段描述", expanded=True):
        st.info(segment.get('description', '无描述'))

    with st.expander("🧠 心理意义"):
        st.info(segment.get('significance', '无'))


def render_character_card(char: Dict):
    """渲染角色卡片"""
    st.markdown(f"**👤 {char.get('character_id', '')}**")
    st.markdown(f"📝 描述: {char.get('physical_description', '')}")
    st.markdown(f"👶 年龄组: {char.get('estimated_age_group', '')}")
    st.markdown(f"🎭 场景角色: {char.get('role_in_scene', '')}")

    # 初始/最终状态
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🎬 初始状态**")
        initial = char.get('initial_state', {})
        emotion = initial.get('emotional_state', {})
        st.markdown(f"- 😊 情绪: {emotion.get('primary_emotion', 'N/A')}")
        st.markdown(f"- 💗 效价: {emotion.get('valence', 'N/A')}")
        st.markdown(f"- ⚡ 唤醒度: {emotion.get('arousal', 'N/A')}")

    with col2:
        st.markdown("**🎬 最终状态**")
        final = char.get('final_state', {})
        emotion = final.get('emotional_state', {})
        st.markdown(f"- 😊 情绪: {emotion.get('primary_emotion', 'N/A')}")
        st.markdown(f"- 💗 效价: {emotion.get('valence', 'N/A')}")
        st.markdown(f"- ⚡ 唤醒度: {emotion.get('arousal', 'N/A')}")


def render_review_actions(segment: Dict, annotation: Dict, file_path: Path, video_id: str):
    """渲染审核操作"""
    review_status = load_review_status()
    segment_key = f"{video_id}_{segment['id']}"
    current_status = review_status.get(segment_key, {})

    st.markdown("### 📋 审核操作")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ 合理", key=f"approve_{segment['id']}", use_container_width=True, type="primary"):
            review_status[segment_key] = {
                'status': 'approved',
                'timestamp': datetime.now().isoformat(),
                'segment_type': segment['type']
            }
            save_review_status(review_status)
            st.success("✅ 已批准")
            st.rerun()

    with col2:
        if st.button("⚠️ 需修改", key=f"modify_{segment['id']}", use_container_width=True):
            review_status[segment_key] = {
                'status': 'needs_modification',
                'timestamp': datetime.now().isoformat(),
                'segment_type': segment['type']
            }
            save_review_status(review_status)
            st.warning("⚠️ 已标记")
            st.rerun()

    with col3:
        if st.button("🗑️ 删除", key=f"delete_{segment['id']}", use_container_width=True):
            review_status[segment_key] = {
                'status': 'to_delete',
                'timestamp': datetime.now().isoformat(),
                'segment_type': segment['type']
            }
            save_review_status(review_status)
            st.error("🗑️ 已标记删除")
            st.rerun()

    with col4:
        if st.button("↩️ 重置", key=f"reset_{segment['id']}", use_container_width=True):
            if segment_key in review_status:
                del review_status[segment_key]
                save_review_status(review_status)
                st.info("↩️ 已重置")
                st.rerun()

    # 当前状态
    if current_status:
        status_map = {
            'approved': '✅ 已批准',
            'needs_modification': '⚠️ 需修改',
            'to_delete': '🗑️ 待删除'
        }
        st.info(f"**当前状态:** {status_map.get(current_status.get('status'), '未知')}")

    # 备注
    note = st.text_area(
        "📝 审核备注",
        value=current_status.get('note', ''),
        key=f"note_{segment['id']}",
        height=80
    )

    if st.button("💾 保存备注", key=f"save_note_{segment['id']}"):
        if segment_key not in review_status:
            review_status[segment_key] = {'status': 'pending'}
        review_status[segment_key]['note'] = note
        save_review_status(review_status)
        st.success("💾 备注已保存")


def render_json_editor(segment: Dict, annotation: Dict, file_path: Path):
    """渲染JSON编辑器"""
    st.markdown("### 📝 JSON编辑")

    raw_data = segment.get('raw_data', {})

    edited_json = st.text_area(
        "编辑JSON",
        value=json.dumps(raw_data, ensure_ascii=False, indent=2),
        height=400,
        key=f"json_{segment['id']}"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 保存JSON", key=f"save_json_{segment['id']}", type="primary", use_container_width=True):
            try:
                new_data = json.loads(edited_json)

                type_to_key = {
                    'desire_motivation': ('desire_motivation_analysis', 'analysis_id'),
                    'desire_transition': ('desire_transitions', 'transition_id'),
                    'behavioral_sequence': ('behavioral_sequence', 'sequence_id'),
                    'key_segment_qa': ('key_segments_for_qa', 'segment_id')
                }

                array_key, id_field = type_to_key.get(segment['type'], (None, None))

                if array_key and array_key in annotation:
                    for idx, item in enumerate(annotation[array_key]):
                        if item.get(id_field) == segment['id']:
                            annotation[array_key][idx] = new_data
                            break

                    backup_path = save_annotation(file_path, annotation)
                    st.success(f"✅ 已保存！备份: {backup_path.name}")
                    st.rerun()

            except json.JSONDecodeError as e:
                st.error(f"❌ JSON格式错误: {e}")

    with col2:
        if st.button("↩️ 重置", key=f"reset_json_{segment['id']}", use_container_width=True):
            st.rerun()


def render_sidebar() -> Tuple[Optional[str], Dict]:
    """渲染侧边栏"""
    st.sidebar.title("📁 标注文件列表")

    # 统计信息
    annotation_files = sorted([f for f in ANNOTATIONS_DIR.glob("*.json") if f.name != 'annotation_errors.json'])
    review_status = load_review_status()

    st.sidebar.markdown(f"**📊 共 {len(annotation_files)} 个文件**")

    approved_total = sum(1 for v in review_status.values() if v.get('status') == 'approved')
    st.sidebar.markdown(f"✅ 已批准片段: {approved_total}")

    st.sidebar.markdown("---")

    # 搜索
    search = st.sidebar.text_input("🔍 搜索文件", key='search')

    st.sidebar.markdown("---")

    # 文件列表
    for f in annotation_files:
        if search and search.lower() not in f.stem.lower():
            continue

        video_id = f.stem
        file_segments = [k for k in review_status.keys() if k.startswith(f"{video_id}_")]
        approved = sum(1 for k in file_segments if review_status[k].get('status') == 'approved')

        label = f.stem[:20] + ("..." if len(f.stem) > 20 else "")
        if file_segments:
            label = f"{label} [{approved}/{len(file_segments)}]"

        if st.sidebar.button(label, key=f"file_{f.stem}", use_container_width=True):
            st.session_state.selected_file = str(f)
            st.session_state.selected_segment_idx = 0

    return st.session_state.get('selected_file'), {}


# ============= 主函数 =============

def main():
    st.title("🔍 AI标注质量检查平台 V3")
    st.caption("支持视频片段播放、美观的UI、完整的标注信息展示")

    # 初始化session state
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
    if 'selected_segment_idx' not in st.session_state:
        st.session_state.selected_segment_idx = 0
    if 'show_json' not in st.session_state:
        st.session_state.show_json = False
    if 'show_timeline' not in st.session_state:
        st.session_state.show_timeline = True

    # 侧边栏
    selected_file, filters = render_sidebar()

    if st.session_state.selected_file:
        file_path = Path(st.session_state.selected_file)
        annotation = load_annotation(file_path)

        if annotation:
            video_id = annotation.get('video_id', file_path.stem)
            video_path = get_video_path(annotation)
            segments = get_all_segments(annotation)

            if not segments:
                st.warning("⚠️ 该文件中没有可检查的片段")
                return

            # 顶部信息栏
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("🎬 视频ID", video_id[:12] + "..." if len(video_id) > 12 else video_id)
            with col2:
                st.metric("⏱️ 时长", f"{annotation.get('duration_seconds', 0)}秒")
            with col3:
                st.metric("📊 片段数", len(segments))
            with col4:
                st.metric("👥 角色数", len(annotation.get('characters', [])))
            with col5:
                review_status = load_review_status()
                approved = sum(1 for s in segments if review_status.get(f"{video_id}_{s['id']}", {}).get('status') == 'approved')
                progress = f"{approved}/{len(segments)}"
                st.metric("✅ 已批准", progress)

            # 工具栏
            st.markdown("---")
            tool_cols = st.columns([1, 1, 1, 1, 2])

            with tool_cols[0]:
                if st.button("⬅️ 上一段", use_container_width=True):
                    if st.session_state.selected_segment_idx > 0:
                        st.session_state.selected_segment_idx -= 1
                        st.rerun()

            with tool_cols[1]:
                if st.button("➡️ 下一段", use_container_width=True):
                    if st.session_state.selected_segment_idx < len(segments) - 1:
                        st.session_state.selected_segment_idx += 1
                        st.rerun()

            with tool_cols[2]:
                st.session_state.show_timeline = st.checkbox("📊 时间轴", value=st.session_state.show_timeline)

            with tool_cols[3]:
                st.session_state.show_json = st.checkbox("📝 JSON编辑", value=st.session_state.show_json)

            with tool_cols[4]:
                segment_options = [
                    f"{SEGMENT_TYPES.get(s['type'], {}).get('icon', '📌')} {s['id'][:15]}... ({format_time(s['start'])})"
                    for s in segments
                ]
                selected_idx = st.selectbox(
                    "选择片段",
                    options=range(len(segments)),
                    format_func=lambda x: segment_options[x],
                    index=st.session_state.selected_segment_idx,
                    key='segment_select',
                    label_visibility='collapsed'
                )
                if selected_idx != st.session_state.selected_segment_idx:
                    st.session_state.selected_segment_idx = selected_idx
                    st.rerun()

            # 时间轴
            if st.session_state.show_timeline:
                render_timeline_visualization(segments, annotation.get('duration_seconds', 60), st.session_state.selected_segment_idx)

            st.markdown("---")

            # 当前片段
            current_segment = segments[st.session_state.selected_segment_idx]

            # 主内容区
            if st.session_state.show_json:
                col_video, col_detail, col_json = st.columns([1.2, 1.2, 1])
            else:
                col_video, col_detail = st.columns([1.2, 1.3])

            with col_video:
                render_video_player_with_segment(video_path, current_segment)

            with col_detail:
                render_segment_detail_panel(current_segment, annotation)
                st.markdown("---")
                render_review_actions(current_segment, annotation, file_path, video_id)

            if st.session_state.show_json:
                with col_json:
                    render_json_editor(current_segment, annotation, file_path)

            # 底部统计
            st.markdown("---")
            render_stats_summary(annotation, segments, video_id)

    else:
        render_welcome_page()


def render_stats_summary(annotation: Dict, segments: List[Dict], video_id: str):
    """渲染统计汇总"""
    review_status = load_review_status()

    stats = {'approved': 0, 'needs_modification': 0, 'to_delete': 0, 'pending': 0}

    for seg in segments:
        key = f"{video_id}_{seg['id']}"
        status = review_status.get(key, {}).get('status', 'pending')
        if status in stats:
            stats[status] += 1
        else:
            stats['pending'] += 1

    st.markdown("### 📊 审核统计")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("✅ 已批准", stats['approved'])
    with col2:
        st.metric("⚠️ 需修改", stats['needs_modification'])
    with col3:
        st.metric("🗑️ 待删除", stats['to_delete'])
    with col4:
        st.metric("⏳ 待审核", stats['pending'])


def render_welcome_page():
    """渲染欢迎页面"""
    st.markdown("## 👋 欢迎使用标注质量检查平台 V3")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 1️⃣ 选择文件")
        st.markdown("从左侧选择标注JSON文件")

    with col2:
        st.markdown("### 2️⃣ 播放片段")
        st.markdown("**只播放标注的时间段**")

    with col3:
        st.markdown("### 3️⃣ 审核标注")
        st.markdown("标记合理/需修改/删除")

    with col4:
        st.markdown("### 4️⃣ 编辑JSON")
        st.markdown("直接修改并保存")

    st.markdown("---")
    st.markdown("### 📊 总体统计")

    annotation_files = list(ANNOTATIONS_DIR.glob("*.json"))
    review_status = load_review_status()

    total_segments = 0
    for f in annotation_files:
        if f.name == 'annotation_errors.json':
            continue
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
            total_segments += len(get_all_segments(data))
        except:
            pass

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📁 标注文件数", len(annotation_files))
    with col2:
        st.metric("📊 总片段数", total_segments)
    with col3:
        st.metric("✅ 已审核", len(review_status))
    with col4:
        approved = sum(1 for v in review_status.values() if v.get('status') == 'approved')
        st.metric("✅ 已批准", approved)


if __name__ == "__main__":
    main()
