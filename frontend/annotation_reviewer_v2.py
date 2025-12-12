# frontend/annotation_reviewer_v2.py
"""
AI标注质量检查平台 V2
增强版：更好的UI、时间轴可视化、批量操作
"""
import streamlit as st
from pathlib import Path
import sys
import json
import base64
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

# 页面配置
st.set_page_config(
    page_title="标注质量检查平台 V2",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS - 只保留简单样式
st.markdown("""
<style>
    .stVideo > div { border-radius: 8px; }
    .segment-info {
        background: #f0f2f6;
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# 配置路径 - 使用绝对路径
BASE_DIR = Path(__file__).parent.parent
ANNOTATIONS_DIR = BASE_DIR / "data" / "annotations_test"
REVIEW_STATUS_FILE = BASE_DIR / "data" / "review_status.json"

# 视频目录 - 尝试多个位置
VIDEOS_DIRS = [
    BASE_DIR / "data" / "Youtube_videos",
    BASE_DIR / "data" / "videos",
    Path("D:/Desire-VQA/video_anno/data/Youtube_videos"),  # 主仓库
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
    backup_dir = BASE_DIR / "data" / "annotations_backup"
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
    """获取视频路径"""
    video_id = annotation.get('video_id', '')
    video_path_str = annotation.get('video_path', '')

    # 尝试多种路径
    paths_to_try = []

    # 从annotation中的路径
    if video_path_str:
        # 处理Windows路径
        normalized = video_path_str.replace('\\', '/')
        paths_to_try.append(Path(normalized))
        paths_to_try.append(BASE_DIR / normalized)
        # 也尝试主仓库路径
        paths_to_try.append(Path("D:/Desire-VQA/video_anno") / normalized)

    # 尝试所有视频目录下的各种格式
    for videos_dir in VIDEOS_DIRS:
        for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            paths_to_try.append(videos_dir / f"{video_id}{ext}")

    for p in paths_to_try:
        if p and p.exists():
            return p

    return None


def format_time(seconds: float) -> str:
    """格式化时间"""
    if seconds is None:
        return "00:00"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def get_all_segments(annotation: Dict) -> List[Dict]:
    """提取所有片段"""
    segments = []

    # desire_motivation_analysis
    for item in annotation.get('desire_motivation_analysis', []):
        temporal = item.get('temporal_scope', {})
        start = temporal.get('start_seconds', 0) or 0
        end = temporal.get('end_seconds', 0) or 0
        if end > start:
            segments.append({
                'type': 'desire_motivation',
                'id': item.get('analysis_id', f"dm_{len(segments)}"),
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
        start = temporal.get('onset_timestamp_seconds', 0) or 0
        end = temporal.get('offset_timestamp_seconds', 0) or 0
        if end > start:
            before_label = item.get('desire_before', {}).get('label', '')
            after_label = item.get('desire_after', {}).get('label', '')
            segments.append({
                'type': 'desire_transition',
                'id': item.get('transition_id', f"dt_{len(segments)}"),
                'character': item.get('character_id', ''),
                'label': f"{before_label} -> {after_label}",
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
        start = item.get('timestamp_start_seconds', 0) or 0
        end = item.get('timestamp_end_seconds', 0) or 0
        if end > start:
            segments.append({
                'type': 'behavioral_sequence',
                'id': item.get('sequence_id', f"bs_{len(segments)}"),
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
        start = item.get('start_timestamp_seconds', 0) or 0
        end = item.get('end_timestamp_seconds', 0) or 0
        if end > start:
            desc = item.get('segment_description', '')
            segments.append({
                'type': 'key_segment_qa',
                'id': item.get('segment_id', f"qa_{len(segments)}"),
                'character': '',
                'label': desc[:50] if desc else 'QA片段',
                'start': start,
                'end': end,
                'description': desc,
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


# ============= 视频播放器（支持时间段） =============

def render_video_segment_player(video_path: Path, start_time: float, end_time: float):
    """
    渲染支持精确时间段播放的视频播放器
    使用HTML5 video标签实现开始/结束时间控制
    """
    if not video_path or not video_path.exists():
        st.error(f"视频文件不存在: {video_path}")
        return

    # 读取视频并转为base64
    with open(video_path, 'rb') as f:
        video_bytes = f.read()

    video_base64 = base64.b64encode(video_bytes).decode('utf-8')

    # 获取视频格式
    suffix = video_path.suffix.lower()
    mime_types = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.mkv': 'video/x-matroska'
    }
    mime_type = mime_types.get(suffix, 'video/mp4')

    # 生成唯一ID
    player_id = f"video_{int(start_time)}_{int(end_time)}"

    # HTML5视频播放器，支持时间段限制
    video_html = f'''
    <div style="background: #000; border-radius: 8px; overflow: hidden; margin-bottom: 10px;">
        <video id="{player_id}"
               style="width: 100%; max-height: 400px;"
               controls>
            <source src="data:{mime_type};base64,{video_base64}" type="{mime_type}">
            您的浏览器不支持视频播放
        </video>
    </div>
    <script>
        (function() {{
            var video = document.getElementById("{player_id}");
            var startTime = {start_time};
            var endTime = {end_time};

            // 设置开始时间
            video.currentTime = startTime;

            // 监听时间更新，到达结束时间时暂停
            video.addEventListener('timeupdate', function() {{
                if (video.currentTime >= endTime) {{
                    video.pause();
                    video.currentTime = startTime;
                }}
            }});

            // 防止拖动到结束时间之后
            video.addEventListener('seeking', function() {{
                if (video.currentTime > endTime) {{
                    video.currentTime = endTime - 0.1;
                }}
                if (video.currentTime < startTime) {{
                    video.currentTime = startTime;
                }}
            }});

            // 播放时如果超出范围则重置
            video.addEventListener('play', function() {{
                if (video.currentTime >= endTime || video.currentTime < startTime) {{
                    video.currentTime = startTime;
                }}
            }});
        }})();
    </script>
    '''

    st.components.v1.html(video_html, height=450)


def render_video_player_simple(video_path: Path, segment: Dict):
    """简单视频播放器（备用方案）"""
    if not video_path or not video_path.exists():
        st.error(f"视频文件不存在")
        st.info(f"尝试路径: {video_path}")
        return

    st.info(f"播放片段: {format_time(segment['start'])} - {format_time(segment['end'])} (时长: {segment['end'] - segment['start']:.1f}秒)")

    with open(video_path, 'rb') as f:
        video_bytes = f.read()

    st.video(video_bytes, start_time=int(segment['start']))
    st.caption(f"注意：请手动在 {format_time(segment['end'])} 处停止播放")


# ============= UI组件 =============

def render_timeline_simple(segments: List[Dict], duration: float, current_idx: int):
    """简化的时间轴显示"""
    if duration <= 0:
        duration = max(seg['end'] for seg in segments) if segments else 60

    st.markdown("#### 时间轴概览")

    # 使用progress bar显示当前片段位置
    current_seg = segments[current_idx] if segments else None
    if current_seg:
        progress = current_seg['start'] / duration
        st.progress(min(progress, 1.0))

        # 显示片段列表摘要
        cols = st.columns(len(segments[:10]))  # 最多显示10个
        for i, col in enumerate(cols):
            if i < len(segments):
                seg = segments[i]
                type_info = SEGMENT_TYPES.get(seg['type'], {})
                icon = type_info.get('icon', '📌')

                if i == current_idx:
                    col.markdown(f"**{icon}**")
                else:
                    col.caption(icon)


def render_segment_detail_panel(segment: Dict, annotation: Dict):
    """渲染片段详情面板"""
    seg_type = segment['type']
    type_info = SEGMENT_TYPES.get(seg_type, {})

    st.markdown(f"### {type_info.get('icon', '📌')} {type_info.get('name', seg_type)}")

    # 基本信息
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**ID:** `{segment['id']}`")
        if segment['character']:
            st.markdown(f"**角色:** {segment['character']}")
    with col2:
        st.markdown(f"**标签:** {segment['label']}")

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
            with st.expander("角色详情"):
                render_character_card(char_info)


def render_desire_motivation_panel(segment: Dict, annotation: Dict):
    """渲染动机分析面板"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**强度**")
        intensity_map = {'strong': '🔴 强', 'moderate': '🟡 中', 'weak': '🟢 弱'}
        st.markdown(intensity_map.get(segment.get('intensity', ''), segment.get('intensity', 'N/A')))

    with col2:
        st.markdown("**马斯洛层级**")
        maslow_map = {
            'physiological': '🍽️ 生理',
            'safety': '🛡️ 安全',
            'belonging': '👥 归属',
            'esteem': '🏆 尊重',
            'self_actualization': '🌟 自我实现'
        }
        st.markdown(maslow_map.get(segment.get('maslow_level', ''), segment.get('maslow_level', 'N/A')))

    with col3:
        st.markdown("**BDI组件**")
        bdi_map = {'belief': '💭 信念', 'desire': '❤️ 欲望', 'intention': '🎯 意图'}
        st.markdown(bdi_map.get(segment.get('bdi_component', ''), segment.get('bdi_component', 'N/A')))

    with col4:
        st.markdown("**置信度**")
        conf = segment.get('confidence', 'N/A')
        if conf in ['high', 'moderate', 'low']:
            conf_map = {'high': '🟢 高', 'moderate': '🟡 中', 'low': '🔴 低'}
            st.markdown(conf_map.get(conf, conf))
        else:
            st.markdown(str(conf))

    with st.expander("推理链条", expanded=True):
        st.info(segment.get('reasoning', '无推理链条'))

    with st.expander("支撑证据"):
        evidence = segment.get('evidence', [])
        if evidence:
            for e in evidence:
                ts = e.get('timestamp_seconds', 0)
                st.markdown(f"- **{format_time(ts)}** [{e.get('behavior_type', '')}]: {e.get('description', '')}")
        else:
            st.caption("无证据")

    with st.expander("替代解释"):
        alternatives = segment.get('alternatives', [])
        if alternatives:
            for alt in alternatives:
                st.markdown(f"**{alt.get('alternative_label', '')}**")
                st.markdown(f"推理: {alt.get('reasoning', '')}")
                st.markdown(f"_为何非主要: {alt.get('why_not_primary', '')}_")
                st.markdown("---")
        else:
            st.caption("无替代解释")


def render_desire_transition_panel(segment: Dict, annotation: Dict):
    """渲染欲望转变面板"""
    st.markdown(f"**转变类型:** {segment.get('transition_type', 'N/A')}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**转变前**")
        before = segment.get('desire_before', {})
        st.markdown(f"- 标签: {before.get('label', 'N/A')}")
        st.markdown(f"- 强度: {before.get('intensity', 'N/A')}")
        st.markdown(f"- 马斯洛: {before.get('maslow_level', 'N/A')}")

    with col2:
        st.markdown("**转变后**")
        after = segment.get('desire_after', {})
        st.markdown(f"- 标签: {after.get('label', 'N/A')}")
        st.markdown(f"- 强度: {after.get('intensity', 'N/A')}")
        st.markdown(f"- 马斯洛: {after.get('maslow_level', 'N/A')}")

    trigger = segment.get('trigger', {})
    if trigger:
        with st.expander("触发事件", expanded=True):
            st.markdown(f"**时间:** {format_time(trigger.get('timestamp_seconds', 0))}")
            st.markdown(f"**类型:** {trigger.get('trigger_type', 'N/A')}")
            st.info(trigger.get('description', ''))

    with st.expander("行为标记"):
        markers = segment.get('markers', [])
        if markers:
            for m in markers:
                ts = m.get('timestamp_seconds', 0)
                st.markdown(f"- **{format_time(ts)}** [{m.get('marker_type', '')}]: {m.get('description', '')}")
        else:
            st.caption("无标记")

    if segment.get('visual_marker'):
        st.markdown(f"**视觉标记:** {segment.get('visual_marker')}")

    with st.expander("心理解释"):
        st.info(segment.get('interpretation', '无解释'))


def render_behavioral_sequence_panel(segment: Dict, annotation: Dict):
    """渲染行为序列面板"""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**行为类别:** {segment.get('label', 'N/A')}")
        intensity_map = {'strong': '🔴 强', 'moderate': '🟡 中', 'weak': '🟢 弱'}
        st.markdown(f"**强度:** {intensity_map.get(segment.get('intensity', ''), segment.get('intensity', 'N/A'))}")

    with col2:
        st.markdown(f"**目标:** {segment.get('target', 'N/A')}")

    with st.expander("行为描述", expanded=True):
        st.info(segment.get('description', '无描述'))

    st.markdown(f"**推断心理状态:** {segment.get('mental_state', 'N/A')}")

    with st.expander("与欲望的关联"):
        st.info(segment.get('relevance', '无关联说明'))


def render_key_segment_panel(segment: Dict, annotation: Dict):
    """渲染QA片段面板"""
    col1, col2 = st.columns(2)

    with col1:
        difficulty_map = {'easy': '🟢 简单', 'medium': '🟡 中等', 'hard': '🔴 困难'}
        st.markdown(f"**难度:** {difficulty_map.get(segment.get('difficulty', ''), segment.get('difficulty', 'N/A'))}")

    with col2:
        st.markdown(f"**推荐QA:** {'✅ 是' if segment.get('recommended') else '❌ 否'}")

    qa_types = segment.get('qa_types', [])
    if qa_types:
        st.markdown(f"**QA类型:** {', '.join(qa_types)}")

    with st.expander("片段描述", expanded=True):
        st.info(segment.get('description', '无描述'))

    with st.expander("心理意义"):
        st.info(segment.get('significance', '无'))


def render_character_card(char: Dict):
    """渲染角色卡片"""
    st.markdown(f"**{char.get('character_id', '')}**")
    st.markdown(f"描述: {char.get('physical_description', '')}")
    st.markdown(f"年龄组: {char.get('estimated_age_group', '')}")
    st.markdown(f"场景角色: {char.get('role_in_scene', '')}")

    # 初始/最终状态
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**初始状态**")
        initial = char.get('initial_state', {})
        emotion = initial.get('emotional_state', {})
        st.markdown(f"- 情绪: {emotion.get('primary_emotion', 'N/A')}")
        st.markdown(f"- 效价: {emotion.get('valence', 'N/A')}")
        st.markdown(f"- 唤醒度: {emotion.get('arousal', 'N/A')}")

    with col2:
        st.markdown("**最终状态**")
        final = char.get('final_state', {})
        emotion = final.get('emotional_state', {})
        st.markdown(f"- 情绪: {emotion.get('primary_emotion', 'N/A')}")
        st.markdown(f"- 效价: {emotion.get('valence', 'N/A')}")
        st.markdown(f"- 唤醒度: {emotion.get('arousal', 'N/A')}")


def render_review_actions(segment: Dict, annotation: Dict, file_path: Path, video_id: str):
    """渲染审核操作"""
    review_status = load_review_status()
    segment_key = f"{video_id}_{segment['id']}"
    current_status = review_status.get(segment_key, {})

    st.markdown("### 审核操作")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ 合理", key=f"approve_{segment['id']}", use_container_width=True, type="primary"):
            review_status[segment_key] = {
                'status': 'approved',
                'timestamp': datetime.now().isoformat(),
                'segment_type': segment['type']
            }
            save_review_status(review_status)
            st.success("已批准")
            st.rerun()

    with col2:
        if st.button("⚠️ 需修改", key=f"modify_{segment['id']}", use_container_width=True):
            review_status[segment_key] = {
                'status': 'needs_modification',
                'timestamp': datetime.now().isoformat(),
                'segment_type': segment['type']
            }
            save_review_status(review_status)
            st.warning("已标记")
            st.rerun()

    with col3:
        if st.button("🗑️ 删除", key=f"delete_{segment['id']}", use_container_width=True):
            review_status[segment_key] = {
                'status': 'to_delete',
                'timestamp': datetime.now().isoformat(),
                'segment_type': segment['type']
            }
            save_review_status(review_status)
            st.error("已标记删除")
            st.rerun()

    with col4:
        if st.button("↩️ 重置", key=f"reset_{segment['id']}", use_container_width=True):
            if segment_key in review_status:
                del review_status[segment_key]
                save_review_status(review_status)
                st.info("已重置")
                st.rerun()

    # 当前状态
    if current_status:
        status_map = {
            'approved': '✅ 已批准',
            'needs_modification': '⚠️ 需修改',
            'to_delete': '🗑️ 待删除'
        }
        st.markdown(f"**当前状态:** {status_map.get(current_status.get('status'), '未知')}")

    # 备注
    note = st.text_area(
        "审核备注",
        value=current_status.get('note', ''),
        key=f"note_{segment['id']}",
        height=80
    )

    if st.button("💾 保存备注", key=f"save_note_{segment['id']}"):
        if segment_key not in review_status:
            review_status[segment_key] = {'status': 'pending'}
        review_status[segment_key]['note'] = note
        save_review_status(review_status)
        st.success("备注已保存")


def render_json_editor(segment: Dict, annotation: Dict, file_path: Path):
    """渲染JSON编辑器"""
    st.markdown("### JSON编辑")

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
                    st.success(f"已保存！备份: {backup_path.name}")
                    st.rerun()

            except json.JSONDecodeError as e:
                st.error(f"JSON格式错误: {e}")

    with col2:
        if st.button("↩️ 重置", key=f"reset_json_{segment['id']}", use_container_width=True):
            st.rerun()


def render_sidebar() -> Tuple[Optional[str], Dict]:
    """渲染侧边栏"""
    st.sidebar.title("📁 标注文件")

    # 统计信息
    if not ANNOTATIONS_DIR.exists():
        st.sidebar.error(f"标注目录不存在: {ANNOTATIONS_DIR}")
        return None, {}

    annotation_files = sorted([f for f in ANNOTATIONS_DIR.glob("*.json") if f.name != 'annotation_errors.json'])
    review_status = load_review_status()

    st.sidebar.markdown(f"**共 {len(annotation_files)} 个文件**")

    approved_total = sum(1 for v in review_status.values() if v.get('status') == 'approved')
    st.sidebar.markdown(f"已批准片段: {approved_total}")

    st.sidebar.markdown("---")

    # 搜索
    search = st.sidebar.text_input("搜索文件", key='search')

    st.sidebar.markdown("---")

    # 文件列表
    for f in annotation_files:
        if search and search.lower() not in f.stem.lower():
            continue

        video_id = f.stem
        file_segments = [k for k in review_status.keys() if k.startswith(f"{video_id}_")]
        approved = sum(1 for k in file_segments if review_status[k].get('status') == 'approved')

        label = f.stem[:18] + ("..." if len(f.stem) > 18 else "")
        if file_segments:
            label = f"{label} [{approved}/{len(file_segments)}]"

        if st.sidebar.button(label, key=f"file_{f.stem}", use_container_width=True):
            st.session_state.selected_file = str(f)
            st.session_state.selected_segment_idx = 0

    filters = {}
    return st.session_state.get('selected_file'), filters


# ============= 主函数 =============

def main():
    st.title("🔍 AI标注质量检查平台 V2")

    # 初始化session state
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
    if 'selected_segment_idx' not in st.session_state:
        st.session_state.selected_segment_idx = 0
    if 'show_json' not in st.session_state:
        st.session_state.show_json = False
    if 'use_simple_player' not in st.session_state:
        st.session_state.use_simple_player = False

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
                st.warning("该文件中没有可检查的片段")
                return

            # 顶部信息栏
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                display_id = video_id[:15] + "..." if len(video_id) > 15 else video_id
                st.metric("视频ID", display_id)
            with col2:
                st.metric("时长", f"{annotation.get('duration_seconds', 0)}秒")
            with col3:
                st.metric("片段数", len(segments))
            with col4:
                st.metric("角色数", len(annotation.get('characters', [])))
            with col5:
                review_status = load_review_status()
                approved = sum(1 for s in segments if review_status.get(f"{video_id}_{s['id']}", {}).get('status') == 'approved')
                st.metric("已批准", f"{approved}/{len(segments)}")

            # 工具栏
            st.markdown("---")
            tool_cols = st.columns([1, 1, 1, 1, 3])

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
                st.session_state.show_json = st.checkbox("JSON编辑", value=st.session_state.show_json)

            with tool_cols[3]:
                st.session_state.use_simple_player = st.checkbox("简单播放器", value=st.session_state.use_simple_player)

            with tool_cols[4]:
                segment_options = [
                    f"{SEGMENT_TYPES.get(s['type'], {}).get('icon', '📌')} {s['id'][:20]} ({format_time(s['start'])}-{format_time(s['end'])})"
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

            st.markdown("---")

            # 当前片段
            current_segment = segments[st.session_state.selected_segment_idx]

            # 显示时间信息
            st.markdown(f"### 当前片段: {format_time(current_segment['start'])} - {format_time(current_segment['end'])} (时长: {current_segment['end'] - current_segment['start']:.1f}秒)")

            # 主内容区
            if st.session_state.show_json:
                col_video, col_detail, col_json = st.columns([1.2, 1.2, 1])
            else:
                col_video, col_detail = st.columns([1.2, 1.3])

            with col_video:
                st.markdown("#### 视频播放")
                if video_path and video_path.exists():
                    if st.session_state.use_simple_player:
                        render_video_player_simple(video_path, current_segment)
                    else:
                        render_video_segment_player(
                            video_path,
                            current_segment['start'],
                            current_segment['end']
                        )
                    st.caption(f"视频: {video_path.name}")
                else:
                    st.error("视频文件未找到")
                    st.info(f"JSON中的路径: {annotation.get('video_path', 'N/A')}")
                    st.info(f"视频ID: {video_id}")
                    with st.expander("查看尝试的路径"):
                        for vdir in VIDEOS_DIRS:
                            exists = "✅" if vdir.exists() else "❌"
                            st.text(f"{exists} {vdir}")

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

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("✅ 已批准", stats['approved'])
    with col2:
        st.metric("⚠️ 需修改", stats['needs_modification'])
    with col3:
        st.metric("🗑️ 待删除", stats['to_delete'])
    with col4:
        st.metric("⏳ 待审核", stats['pending'])
    with col5:
        # 批量操作
        render_batch_actions(segments, video_id, annotation)


def render_batch_actions(segments: List[Dict], video_id: str, annotation: Dict):
    """渲染批量操作"""
    with st.popover("批量操作"):
        st.markdown("**批量审核**")

        if st.button("✅ 全部批准", key="batch_approve", use_container_width=True):
            review_status = load_review_status()
            for seg in segments:
                key = f"{video_id}_{seg['id']}"
                review_status[key] = {
                    'status': 'approved',
                    'timestamp': datetime.now().isoformat(),
                    'segment_type': seg['type']
                }
            save_review_status(review_status)
            st.success(f"已批准 {len(segments)} 个片段")
            st.rerun()

        if st.button("↩️ 全部重置", key="batch_reset", use_container_width=True):
            review_status = load_review_status()
            for seg in segments:
                key = f"{video_id}_{seg['id']}"
                if key in review_status:
                    del review_status[key]
            save_review_status(review_status)
            st.info("已重置所有审核状态")
            st.rerun()

        st.markdown("---")
        st.markdown("**导出**")

        if st.button("📥 导出审核结果", key="export_review", use_container_width=True):
            review_status = load_review_status()
            export_data = {
                'video_id': video_id,
                'export_time': datetime.now().isoformat(),
                'segments': []
            }
            for seg in segments:
                key = f"{video_id}_{seg['id']}"
                status = review_status.get(key, {})
                export_data['segments'].append({
                    'segment_id': seg['id'],
                    'type': seg['type'],
                    'label': seg['label'],
                    'start': seg['start'],
                    'end': seg['end'],
                    'review_status': status.get('status', 'pending'),
                    'note': status.get('note', '')
                })

            st.download_button(
                "下载JSON",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name=f"review_{video_id}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )


def render_welcome_page():
    """渲染欢迎页面"""
    st.markdown("## 欢迎使用标注质量检查平台 V2")

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 1️⃣ 选择文件")
        st.markdown("从左侧选择标注JSON文件")

    with col2:
        st.markdown("### 2️⃣ 播放视频")
        st.markdown("自动播放指定时间段的视频片段")

    with col3:
        st.markdown("### 3️⃣ 审核标注")
        st.markdown("标记是否合理、需修改或删除")

    with col4:
        st.markdown("### 4️⃣ 编辑JSON")
        st.markdown("直接修改JSON内容并保存")

    st.markdown("---")

    # 总体统计
    st.markdown("### 总体统计")

    if ANNOTATIONS_DIR.exists():
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
            st.metric("标注文件数", len(annotation_files))
        with col2:
            st.metric("总片段数", total_segments)
        with col3:
            st.metric("已审核", len(review_status))
        with col4:
            approved = sum(1 for v in review_status.values() if v.get('status') == 'approved')
            st.metric("已批准", approved)
    else:
        st.warning(f"标注目录不存在: {ANNOTATIONS_DIR}")


if __name__ == "__main__":
    main()
