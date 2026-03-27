# frontend/annotation_reviewer_v6.py
"""
AI标注质量检查平台 V6
适配 v6 JSON 标注格式，修复 v3 已知问题：
- 数据目录指向 annotations_v6
- intensity 整数映射修复
- 新增 scene_context / inter_character_dynamics / annotation_metadata 面板
- 移除 base64 视频编码方案，统一使用原生播放器
- 备份路径使用绝对路径
- 增强角色卡片显示 attribute_dynamics
"""
import streamlit as st
from pathlib import Path
import sys
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
# 时间轴使用纯 HTML/CSS 多轨道实现 (无需 pandas/altair/pyarrow)
sys.path.append(str(Path(__file__).parent.parent))

# 页面配置
st.set_page_config(
    page_title="标注质量检查平台 V6",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .main { padding: 0.5rem 1rem; background: #f5f7fa; }

    .segment-card {
        border: 1px solid #e1e8ed; border-radius: 16px; padding: 20px;
        margin: 16px 0; background: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .segment-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        transform: translateY(-3px);
    }
    .segment-card.approved { border-left: 5px solid #10b981; background: linear-gradient(135deg, #fff 0%, #f0fdf4 100%); }
    .segment-card.needs-mod { border-left: 5px solid #f59e0b; background: linear-gradient(135deg, #fff 0%, #fffbeb 100%); }
    .segment-card.to-delete { border-left: 5px solid #ef4444; background: linear-gradient(135deg, #fff 0%, #fef2f2 100%); }

    .type-badge {
        display: inline-block; padding: 6px 14px; border-radius: 20px;
        font-size: 12px; font-weight: 700; margin: 4px;
        letter-spacing: 0.3px; box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    .type-desire-motivation { background: #10b981; color: white; }
    .type-desire-transition { background: #3b82f6; color: white; }
    .type-behavioral-sequence { background: #f59e0b; color: white; }
    .type-key-segment-qa { background: #8b5cf6; color: white; }

    .scene-card {
        background: linear-gradient(135deg, #667eea15, #764ba215);
        border: 1px solid #667eea30; border-radius: 12px;
        padding: 16px; margin: 8px 0;
    }
    .meta-card {
        background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
        color: #e0e0e0; border-radius: 12px;
        padding: 16px; margin: 8px 0;
    }
    .dynamics-card {
        background: linear-gradient(135deg, #f093fb15, #f5576c15);
        border: 1px solid #f093fb30; border-radius: 12px;
        padding: 16px; margin: 8px 0;
    }
    .character-card {
        background: linear-gradient(to bottom right, #f8f9fa, #e9ecef);
        border-radius: 10px; padding: 18px; margin: 12px 0;
        border-left: 4px solid #007bff;
    }
    .evidence-item {
        background: white; padding: 12px 16px; border-radius: 8px;
        margin: 6px 0; font-size: 14px; border-left: 3px solid #17a2b8;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .info-panel {
        background: white; border-radius: 10px; padding: 20px;
        margin: 12px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stButton > button {
        border-radius: 8px; font-weight: 600; transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# ============= 配置 =============
BASE_DIR = Path(__file__).parent.parent
ANNOTATIONS_DIR = BASE_DIR / "data" / "annotations_v6"
REVIEW_STATUS_FILE = BASE_DIR / "data" / "review_status_v6.json"
BACKUP_DIR = BASE_DIR / "data" / "annotations_backup"

VIDEOS_DIRS = [
    BASE_DIR / "data" / "Youtube_videos",
    BASE_DIR / "data" / "videos",
    Path("D:/Desire-VQA/video_anno/data/Youtube_videos"),
]

SEGMENT_TYPES = {
    'desire_motivation': {'name': '动机分析', 'icon': '🎯', 'color': '#28a745'},
    'desire_transition': {'name': '欲望转变', 'icon': '🔄', 'color': '#007bff'},
    'behavioral_sequence': {'name': '行为序列', 'icon': '📊', 'color': '#ffc107'},
    'key_segment_qa': {'name': 'QA片段', 'icon': '❓', 'color': '#6f42c1'}
}

# ============= 工具函数 =============

def load_review_status() -> Dict:
    if REVIEW_STATUS_FILE.exists():
        with open(REVIEW_STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_review_status(status: Dict):
    REVIEW_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

def load_annotation(file_path: Path) -> Optional[Dict]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"加载标注失败: {e}")
        return None

def save_annotation(file_path: Path, data: Dict):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return backup_path

def get_video_path(annotation: Dict) -> Optional[Path]:
    video_id = annotation.get('video_id', '')
    video_path_str = annotation.get('video_path', '')
    paths_to_try = []
    if video_path_str:
        normalized = video_path_str.replace('\\', '/')
        paths_to_try.append(Path(normalized))
        paths_to_try.append(BASE_DIR / normalized)
        paths_to_try.append(Path("D:/Desire-VQA/video_anno") / normalized)
    for videos_dir in VIDEOS_DIRS:
        for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            paths_to_try.append(videos_dir / f"{video_id}{ext}")
    for p in paths_to_try:
        if p and p.exists():
            return p
    return None

def format_time(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def get_all_segments(annotation: Dict) -> List[Dict]:
    segments = []

    for item in annotation.get('desire_motivation_analysis', []):
        temporal = item.get('temporal_scope', {})
        start = temporal.get('start_seconds', 0)
        end = temporal.get('end_seconds', 0)
        if end > start:
            segments.append({
                'type': 'desire_motivation', 'id': item.get('analysis_id', ''),
                'character': item.get('character_id', ''),
                'label': item.get('desire_label', ''),
                'start': start, 'end': end,
                'intensity': item.get('intensity', 0),
                'maslow_level': item.get('maslow_level', ''),
                'bdi_component': item.get('bdi_component', ''),
                'desire_type': item.get('desire_type', ''),
                'confidence': item.get('confidence', ''),
                'dimension': item.get('dimension', ''),
                'explicitness': item.get('explicitness', ''),
                'temporal_type': item.get('temporal_type', ''),
                'reasoning': item.get('reasoning_chain', ''),
                'evidence': item.get('supporting_evidence', []),
                'supporting_sequence_ids': item.get('supporting_sequence_ids', []),
                'alternatives': item.get('alternative_interpretations', []),
                'raw_data': item
            })

    for item in annotation.get('desire_transitions', []):
        temporal = item.get('temporal_boundaries', {})
        start = temporal.get('onset_timestamp_seconds', 0)
        end = temporal.get('offset_timestamp_seconds', 0)
        if end > start:
            segments.append({
                'type': 'desire_transition', 'id': item.get('transition_id', ''),
                'character': item.get('character_id', ''),
                'label': f"{item.get('desire_before', {}).get('label', '')} → {item.get('desire_after', {}).get('label', '')}",
                'start': start, 'end': end,
                'transition_type': item.get('transition_type', ''),
                'desire_before': item.get('desire_before', {}),
                'desire_after': item.get('desire_after', {}),
                'trigger': item.get('trigger_event', {}),
                'markers': item.get('behavioral_markers', []),
                'visual_marker': item.get('visual_marker_of_change', ''),
                'interpretation': item.get('psychological_interpretation', ''),
                'raw_data': item
            })

    for item in annotation.get('behavioral_sequence', []):
        start = item.get('timestamp_start_seconds', 0)
        end = item.get('timestamp_end_seconds', 0)
        if end > start:
            segments.append({
                'type': 'behavioral_sequence', 'id': item.get('sequence_id', ''),
                'character': item.get('character_id', ''),
                'label': item.get('behavior_category', ''),
                'start': start, 'end': end,
                'description': item.get('behavior_description', ''),
                'intensity': item.get('intensity', ''),
                'target': item.get('target', ''),
                'mental_state': item.get('inferred_mental_state', ''),
                'relevance': item.get('relevance_to_desire', ''),
                'raw_data': item
            })

    for item in annotation.get('key_segments_for_qa', []):
        start = item.get('start_timestamp_seconds', 0)
        end = item.get('end_timestamp_seconds', 0)
        if end > start:
            segments.append({
                'type': 'key_segment_qa', 'id': item.get('segment_id', ''),
                'character': '', 'label': item.get('segment_description', '')[:50],
                'start': start, 'end': end,
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
    for char in annotation.get('characters', []):
        if char.get('character_id') == character_id:
            return char
    return None


# ============= 视频播放器 =============

FFMPEG_PATH = "D:/GoogleData/ffmpeg-2025-03-31-git-35c091f4b7-essentials_build/ffmpeg-2025-03-31-git-35c091f4b7-essentials_build/bin/ffmpeg.exe"
WEB_VIDEOS_DIR = BASE_DIR / "data" / "videos_web"


def _get_web_ready_video(video_path: Path) -> Path:
    """获取浏览器兼容的视频副本（faststart 优化），有缓存"""
    WEB_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    web_path = WEB_VIDEOS_DIR / video_path.name

    # 缓存命中
    if web_path.exists() and web_path.stat().st_size > 0:
        return web_path

    # 使用 ffmpeg 重封装 (不重新编码，仅调整 moov atom 位置)
    ffmpeg = FFMPEG_PATH if Path(FFMPEG_PATH).exists() else "ffmpeg"
    try:
        import subprocess
        result = subprocess.run(
            [ffmpeg, "-y", "-i", str(video_path), "-c", "copy",
             "-movflags", "+faststart", str(web_path)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and web_path.exists():
            return web_path
    except Exception:
        pass

    return video_path  # 失败则回退到原始文件


def render_video_player(video_path: Path, segment: Dict):
    """统一使用原生播放器，自动 faststart 优化确保浏览器兼容"""
    if not video_path or not video_path.exists():
        st.error(f"❌ 视频文件不存在: {video_path.name if video_path else '未找到'}")
        if video_path:
            st.caption(f"搜索路径: {video_path}")
        return

    st.markdown("### 🎬 视频片段播放")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⏱️ 开始", format_time(segment['start']))
    with col2:
        st.metric("⏱️ 结束", format_time(segment['end']))
    with col3:
        st.metric("⏳ 时长", f"{segment['end'] - segment['start']:.1f}秒")

    # 优先使用 faststart 优化过的版本
    playable_path = _get_web_ready_video(video_path)

    try:
        video_bytes = playable_path.read_bytes()
        st.video(video_bytes, start_time=int(segment['start']))
        if playable_path != video_path:
            st.caption("💡 已使用 faststart 优化版本")
    except Exception as e:
        st.error(f"播放器加载失败: {e}")
        st.caption(f"文件: {video_path.resolve()} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)")
        st.warning("提示: 视频编码可能不被浏览器支持 (仅支持 H.264/MP4)")


# ============= 新增 V6 面板 =============

def render_scene_context_panel(annotation: Dict):
    """渲染场景上下文面板 (v6 新增)"""
    scene = annotation.get('scene_context', {})
    if not scene:
        return

    video_id = annotation.get('video_id', 'unknown')
    with st.expander(f"🌍 场景概览 — {video_id[:12]}", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**🏠 物理环境:** {scene.get('physical_setting', 'N/A')}")
            st.markdown(f"**👥 社交语境:** {scene.get('social_context', 'N/A')}")
            st.markdown(f"**🎭 活动类型:** {scene.get('activity_type', 'N/A')}")
        with col2:
            st.markdown(f"**⏰ 时间语境:** {scene.get('temporal_context', 'N/A')}")
            st.markdown(f"**💫 情感氛围:** {scene.get('emotional_atmosphere', 'N/A')}")
            objects = scene.get('salient_objects', [])
            if objects:
                st.markdown(f"**📦 显著物品:** {', '.join(objects)}")


def render_inter_character_dynamics_panel(annotation: Dict):
    """渲染角色间互动面板 (v6 新增)"""
    dynamics = annotation.get('inter_character_dynamics', [])
    if not dynamics:
        return

    video_id = annotation.get('video_id', 'unknown')
    with st.expander(f"🤝 角色间互动关系 — {video_id[:12]}", expanded=False):
        for dyad in dynamics:
            st.markdown(f"#### {dyad.get('character_1_id', '')} ↔ {dyad.get('character_2_id', '')}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**关系类型:** {dyad.get('relationship_type', 'N/A')}")
            with col2:
                quality_map = {'cooperative': '🤝 合作', 'competitive': '⚔️ 竞争',
                               'neutral': '😐 中性', 'hostile': '👊 敌对'}
                quality = dyad.get('interaction_quality', '')
                st.markdown(f"**互动质量:** {quality_map.get(quality, quality)}")
            with col3:
                st.markdown(f"**相互影响:** {dyad.get('mutual_influence', 'N/A')}")

            moments = dyad.get('key_interaction_moments', [])
            if moments:
                st.markdown("**关键互动时刻:**")
                for m in moments:
                    st.markdown(f"- ⏱️ {format_time(m.get('timestamp_seconds', 0))}: {m.get('description', '')}")
            st.markdown("---")


def render_annotation_metadata_panel(annotation: Dict):
    """渲染标注元数据面板 (v6 新增)"""
    meta = annotation.get('annotation_metadata', {})
    if not meta:
        return

    video_id = annotation.get('video_id', 'unknown')
    with st.expander(f"📋 标注元数据 — {video_id[:12]}", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**🤖 模型:** `{meta.get('model_used', 'N/A')}`")
            st.markdown(f"**📌 标注版本:** `{meta.get('annotation_version', 'N/A')}`")
            st.markdown(f"**📐 分类版本:** `{meta.get('taxonomy_version', 'N/A')}`")
        with col2:
            st.markdown(f"**👥 角色数:** {meta.get('total_characters_annotated', 0)}")
            st.markdown(f"**🎯 欲望标注数:** {meta.get('total_desire_annotations', 0)}")
            st.markdown(f"**🔄 转变数:** {meta.get('total_transitions_detected', 0)}")
        with col3:
            st.markdown(f"**🎯 整体置信度:** {meta.get('overall_annotation_confidence', 'N/A')}")
            st.markdown(f"**📝 Prompt版本:** `{meta.get('prompt_version', 'N/A')}`")

        # 框架
        frameworks = meta.get('frameworks_applied', [])
        if frameworks:
            st.markdown(f"**🧠 应用框架:** {' · '.join(frameworks)}")

        # 维度分布
        dim_dist = meta.get('dimension_distribution', {})
        if dim_dist:
            st.markdown("**📊 维度分布:**")
            dim_cols = st.columns(len(dim_dist))
            for i, (dim, count) in enumerate(dim_dist.items()):
                with dim_cols[i]:
                    st.metric(dim, count)

        # 质量标志
        flags = meta.get('quality_flags', {})
        if flags:
            flag_items = []
            flag_map = {
                'video_quality_issues': '🎥 视频质量问题',
                'occlusion_present': '🚧 遮挡',
                'multiple_simultaneous_events': '🔀 多事件并发',
                'ambiguous_behaviors': '❓ 模糊行为'
            }
            for k, v in flags.items():
                label = flag_map.get(k, k)
                flag_items.append(f"{'🔴' if v else '🟢'} {label}")
            st.markdown("**🚩 质量标志:** " + " | ".join(flag_items))

        # 注释
        notes = meta.get('annotation_notes', '')
        if notes:
            st.info(f"📝 {notes}")


# ============= 详情面板 =============

def render_desire_motivation_panel(segment: Dict, annotation: Dict):
    """渲染动机分析面板 - 修复 intensity 整数映射"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**💪 强度**")
        intensity = segment.get('intensity', 0)
        if isinstance(intensity, int):
            emoji = ['', '🟢', '🟢', '🟡', '🟠', '🔴']
            st.markdown(f"{emoji[min(intensity, 5)]} {intensity}/5")
            st.progress(intensity / 5)
        else:
            intensity_map = {'strong': '🔴 强', 'moderate': '🟡 中', 'weak': '🟢 弱'}
            st.markdown(intensity_map.get(str(intensity), str(intensity)))

    with col2:
        st.markdown("**🎯 马斯洛层级**")
        maslow_map = {
            'physiological': '🍽️ 生理', 'safety': '🛡️ 安全',
            'belonging': '👥 归属', 'esteem': '🏆 尊重',
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
        conf_map = {'high': '🟢 高', 'moderate': '🟡 中', 'low': '🔴 低'}
        st.markdown(conf_map.get(conf, str(conf)))

    # v6 新增字段
    v6_cols = st.columns(4)
    with v6_cols[0]:
        st.markdown(f"**📐 维度:** `{segment.get('dimension', 'N/A')}`")
    with v6_cols[1]:
        expl_map = {
            'explicit_verbal': '🗣️ 显式言语', 'explicit_behavioral': '👋 显式行为',
            'implicit_behavioral': '🔍 隐式行为', 'implicit_contextual': '🌐 隐式语境'
        }
        expl = segment.get('explicitness', '')
        st.markdown(f"**👁️ 显隐性:** {expl_map.get(expl, expl or 'N/A')}")
    with v6_cols[2]:
        temp_map = {'sustained': '⏳ 持续', 'momentary': '⚡ 瞬时', 'recurring': '🔁 反复'}
        temp = segment.get('temporal_type', '')
        st.markdown(f"**⏱️ 时间类型:** {temp_map.get(temp, temp or 'N/A')}")
    with v6_cols[3]:
        dtype_map = {'intrinsic': '💎 内在', 'extrinsic': '🏅 外在', 'mixed': '🔀 混合'}
        dtype = segment.get('desire_type', '')
        st.markdown(f"**🔖 欲望类型:** {dtype_map.get(dtype, dtype or 'N/A')}")

    # 关联行为序列
    seq_ids = segment.get('supporting_sequence_ids', [])
    if seq_ids:
        st.markdown(f"**🔗 关联行为序列:** `{'`, `'.join(seq_ids)}`")

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
                st.markdown(f"**⏱️ {format_time(e.get('timestamp_seconds', 0))}** [{e.get('behavior_type', '')}]: {e.get('description', '')}")
        else:
            st.caption("无证据")

    with st.expander("🔄 替代解释"):
        alternatives = segment.get('alternatives', [])
        if alternatives:
            if isinstance(alternatives, str):
                st.markdown(alternatives)
            else:
                for idx, alt_item in enumerate(alternatives, 1):
                    if isinstance(alt_item, dict):
                        st.markdown(f"**{idx}. {alt_item.get('alternative_label', '')}**")
                        st.markdown(f"📝 推理: {alt_item.get('reasoning', '')}")
                        st.markdown(f"⚠️ _为何非主要: {alt_item.get('why_not_primary', '')}_")
                    else:
                        st.markdown(f"**{idx}.** {alt_item}")
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
        intensity_b = before.get('intensity', 'N/A')
        st.markdown(f"- 强度: {intensity_b}/5" if isinstance(intensity_b, int) else f"- 强度: {intensity_b}")
        st.markdown(f"- 马斯洛: {before.get('maslow_level', 'N/A')}")
    with col2:
        st.markdown("**📈 转变后**")
        after = segment.get('desire_after', {})
        st.markdown(f"- 标签: {after.get('label', 'N/A')}")
        intensity_a = after.get('intensity', 'N/A')
        st.markdown(f"- 强度: {intensity_a}/5" if isinstance(intensity_a, int) else f"- 强度: {intensity_a}")
        st.markdown(f"- 马斯洛: {after.get('maslow_level', 'N/A')}")

    with st.expander("⚡ 触发事件", expanded=True):
        trigger = segment.get('trigger', {})
        if trigger:
            st.markdown(f"**⏱️ 时间:** {format_time(trigger.get('timestamp_seconds', 0))}")
            st.markdown(f"**📌 类型:** {trigger.get('trigger_type', 'N/A')}")
            st.info(trigger.get('description', ''))
        else:
            st.caption("无触发事件")

    with st.expander("🔖 行为标记"):
        markers = segment.get('markers', [])
        if markers:
            for m in markers:
                st.markdown(f"**⏱️ {format_time(m.get('timestamp_seconds', 0))}** [{m.get('marker_type', '')}]: {m.get('description', '')}")
        else:
            st.caption("无标记")

    st.markdown(f"**👁️ 视觉标记:** {segment.get('visual_marker', '无')}")
    with st.expander("🧠 心理解释"):
        st.info(segment.get('interpretation', '无解释'))


def render_behavioral_sequence_panel(segment: Dict, annotation: Dict):
    """渲染行为序列面板"""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**📊 行为类别:** {segment.get('label', 'N/A')}")
        intensity = segment.get('intensity', '')
        intensity_map = {'strong': '🔴 强', 'moderate': '🟡 中', 'weak': '🟢 弱'}
        st.markdown(f"**💪 强度:** {intensity_map.get(str(intensity), str(intensity) or 'N/A')}")
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
    st.markdown(f"**❓ QA类型:** {', '.join(qa_types) if qa_types else 'N/A'}")
    with st.expander("📝 片段描述", expanded=True):
        st.info(segment.get('description', '无描述'))
    with st.expander("🧠 心理意义"):
        st.info(segment.get('significance', '无'))


# ============= 角色卡片（增强版）=============

def render_character_card(char: Dict):
    """渲染角色卡片 - 增强版，支持 attribute_dynamics"""
    st.markdown(f"**👤 {char.get('character_id', '')}**")
    st.markdown(f"📝 描述: {char.get('physical_description', '')}")
    st.markdown(f"👶 年龄组: {char.get('estimated_age_group', '')}")
    st.markdown(f"🎭 场景角色: {char.get('role_in_scene', '')}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🎬 初始状态**")
        initial = char.get('initial_state', {})
        emotion = initial.get('emotional_state', {})
        st.markdown(f"- ⏱️ 时间: {format_time(initial.get('timestamp_seconds', 0))}")
        st.markdown(f"- 😊 情绪: {emotion.get('primary_emotion', 'N/A')}")
        st.markdown(f"- 💗 效价: {emotion.get('valence', 'N/A')} | ⚡ 唤醒度: {emotion.get('arousal', 'N/A')}")
        st.markdown(f"- 🧍 体态: {initial.get('body_language_summary', 'N/A')}")
        st.markdown(f"- 🎯 目标: {initial.get('apparent_goal', 'N/A')}")
        evidence = initial.get('behavioral_evidence', [])
        if evidence:
            st.markdown(f"- 📋 证据: {', '.join(evidence)}")

    with col2:
        st.markdown("**🎬 最终状态**")
        final = char.get('final_state', {})
        emotion = final.get('emotional_state', {})
        st.markdown(f"- ⏱️ 时间: {format_time(final.get('timestamp_seconds', 0))}")
        st.markdown(f"- 😊 情绪: {emotion.get('primary_emotion', 'N/A')}")
        st.markdown(f"- 💗 效价: {emotion.get('valence', 'N/A')} | ⚡ 唤醒度: {emotion.get('arousal', 'N/A')}")
        st.markdown(f"- 🧍 体态: {final.get('body_language_summary', 'N/A')}")
        st.markdown(f"- 🎯 目标: {final.get('apparent_goal', 'N/A')}")
        evidence = final.get('behavioral_evidence', [])
        if evidence:
            st.markdown(f"- 📋 证据: {', '.join(evidence)}")

    # attribute_dynamics (v6 新增)
    dynamics = char.get('attribute_dynamics', [])
    if dynamics:
        st.markdown("**📈 属性动态变化:**")
        traj_map = {'INCREASING': '📈 上升', 'DECREASING': '📉 下降',
                     'STABLE': '➡️ 稳定', 'FLUCTUATING': '📊 波动'}
        for d in dynamics:
            traj = d.get('trajectory', '')
            st.markdown(
                f"- **{d.get('attribute_name', '')}**: "
                f"{traj_map.get(traj, traj)} "
                f"({d.get('initial_level', '')} → {d.get('final_level', '')}) "
                f"[置信度: {d.get('confidence', '')}]"
            )
            ev = d.get('behavioral_evidence', [])
            if ev:
                st.caption(f"  证据: {', '.join(ev)}")


# ============= 详情面板路由 =============

def render_segment_detail_panel(segment: Dict, annotation: Dict):
    seg_type = segment['type']
    type_info = SEGMENT_TYPES.get(seg_type, {})
    st.markdown(f"### {type_info.get('icon', '📌')} {type_info.get('name', seg_type)}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**ID:** `{segment['id']}`")
        st.markdown(f"**👤 角色:** {segment['character'] if segment['character'] else 'N/A'}")
    with col2:
        st.markdown(f"**🏷️ 标签:** {segment['label']}")

    st.markdown("---")

    if seg_type == 'desire_motivation':
        render_desire_motivation_panel(segment, annotation)
    elif seg_type == 'desire_transition':
        render_desire_transition_panel(segment, annotation)
    elif seg_type == 'behavioral_sequence':
        render_behavioral_sequence_panel(segment, annotation)
    elif seg_type == 'key_segment_qa':
        render_key_segment_panel(segment, annotation)

    with st.expander("👤 角色详细信息"):
        if segment['character']:
            char_info = get_character_info(annotation, segment['character'])
            if char_info:
                render_character_card(char_info)
            else:
                st.caption("无角色详细信息")
        else:
            st.caption("无角色信息")


# ============= 审核操作 =============

def render_review_actions(segment: Dict, annotation: Dict, file_path: Path, video_id: str):
    review_status = load_review_status()
    segment_key = f"{video_id}_{segment['id']}"
    current_status = review_status.get(segment_key, {})

    st.markdown("### 📋 审核操作")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ 合理", key=f"approve_{segment['id']}", use_container_width=True, type="primary"):
            review_status[segment_key] = {'status': 'approved', 'timestamp': datetime.now().isoformat(), 'segment_type': segment['type']}
            save_review_status(review_status)
            st.rerun()
    with col2:
        if st.button("⚠️ 需修改", key=f"modify_{segment['id']}", use_container_width=True):
            review_status[segment_key] = {'status': 'needs_modification', 'timestamp': datetime.now().isoformat(), 'segment_type': segment['type']}
            save_review_status(review_status)
            st.rerun()
    with col3:
        if st.button("🗑️ 删除", key=f"delete_{segment['id']}", use_container_width=True):
            review_status[segment_key] = {'status': 'to_delete', 'timestamp': datetime.now().isoformat(), 'segment_type': segment['type']}
            save_review_status(review_status)
            st.rerun()
    with col4:
        if st.button("↩️ 重置", key=f"reset_{segment['id']}", use_container_width=True):
            if segment_key in review_status:
                del review_status[segment_key]
                save_review_status(review_status)
                st.rerun()

    status_map = {'approved': '✅ 已批准', 'needs_modification': '⚠️ 需修改', 'to_delete': '🗑️ 待删除', 'pending': '⏳ 待审核'}
    current_text = status_map.get(current_status.get('status'), '⏳ 待审核') if current_status else '⏳ 待审核'
    st.info(f"**当前状态:** {current_text}")

    note = st.text_area("📝 审核备注", value=current_status.get('note', ''), key=f"note_{segment['id']}", height=80)
    if st.button("💾 保存备注", key=f"save_note_{segment['id']}"):
        if segment_key not in review_status:
            review_status[segment_key] = {'status': 'pending'}
        review_status[segment_key]['note'] = note
        save_review_status(review_status)
        st.success("💾 备注已保存")


# ============= JSON编辑器 =============

def render_json_editor(segment: Dict, annotation: Dict, file_path: Path):
    st.markdown("### 📝 JSON编辑")
    raw_data = segment.get('raw_data', {})
    edited_json = st.text_area("编辑JSON", value=json.dumps(raw_data, ensure_ascii=False, indent=2), height=400, key=f"json_{segment['id']}")

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


# ============= 时间轴 =============

def render_interactive_timeline(segments: List[Dict], duration: float, current_idx: int):
    """多轨道 HTML/CSS 时间轴 — 按类型分行，带悬浮提示和时间刻度"""
    st.markdown("### 📊 时间轴")

    if not segments or duration <= 0:
        st.warning("无数据")
        return None

    # 按类型分组
    type_order = ['desire_motivation', 'desire_transition', 'behavioral_sequence', 'key_segment_qa']
    grouped = {}
    for seg_type in type_order:
        grouped[seg_type] = [(i, seg) for i, seg in enumerate(segments) if seg['type'] == seg_type]

    # 有数据的轨道
    active_types = [t for t in type_order if grouped.get(t)]
    if not active_types:
        st.warning("无数据")
        return None

    track_height = 28
    track_gap = 4
    label_width = 80
    total_tracks = len(active_types)
    chart_height = total_tracks * (track_height + track_gap) + 30  # 30px for ticks

    # 构建轨道 HTML
    tracks_html = ""
    for track_idx, seg_type in enumerate(active_types):
        type_info = SEGMENT_TYPES.get(seg_type, {})
        top = track_idx * (track_height + track_gap)
        color = type_info.get('color', '#808080')
        name = type_info.get('name', seg_type)
        icon = type_info.get('icon', '📌')

        # 轨道标签
        tracks_html += (
            f'<div style="position:absolute; left:0; top:{top}px; width:{label_width}px; '
            f'height:{track_height}px; display:flex; align-items:center; font-size:12px; '
            f'color:#555; font-weight:500; white-space:nowrap;">'
            f'{icon} {name}</div>'
        )

        # 轨道背景
        tracks_html += (
            f'<div style="position:absolute; left:{label_width}px; right:0; top:{top}px; '
            f'height:{track_height}px; background:#f5f5f5; border-radius:4px; '
            f'border:1px solid #e0e0e0;"></div>'
        )

        # 片段条
        for i, seg in grouped[seg_type]:
            left_pct = (seg['start'] / duration) * 100
            width_pct = max(((seg['end'] - seg['start']) / duration) * 100, 0.8)
            is_active = i == current_idx
            bar_opacity = "1.0" if is_active else "0.6"
            bar_border = "2.5px solid #1a1a1a" if is_active else "1px solid rgba(0,0,0,0.15)"
            bar_shadow = "0 2px 6px rgba(0,0,0,0.35)" if is_active else "none"
            bar_z = "10" if is_active else "1"
            bar_transform = "scaleY(1.15)" if is_active else "scaleY(1)"
            label_text = seg['label'][:20] + ('…' if len(seg['label']) > 20 else '')
            tooltip = f"{name}: {seg['label']}&#10;{format_time(seg['start'])} → {format_time(seg['end'])}&#10;时长: {seg['end']-seg['start']:.1f}秒"

            tracks_html += (
                f'<div title="{tooltip}" style="position:absolute; '
                f'left:calc({label_width}px + (100% - {label_width}px) * {left_pct / 100}); '
                f'width:calc((100% - {label_width}px) * {width_pct / 100}); '
                f'top:{top + 2}px; height:{track_height - 4}px; '
                f'background:{color}; opacity:{bar_opacity}; border-radius:4px; '
                f'border:{bar_border}; box-shadow:{bar_shadow}; z-index:{bar_z}; '
                f'transform:{bar_transform}; cursor:pointer; transition:all 0.15s ease; '
                f'display:flex; align-items:center; justify-content:center; '
                f'overflow:hidden; padding:0 4px;'
                f'">'
                f'<span style="font-size:10px; color:white; text-shadow:0 1px 2px rgba(0,0,0,0.5); '
                f'white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">'
                f'{"▶ " if is_active else ""}{label_text}</span>'
                f'</div>'
            )

    # 时间刻度
    ticks_area_top = total_tracks * (track_height + track_gap) + 2
    ticks_html = ""
    num_ticks = min(10, max(4, int(duration / 5)))
    tick_interval = duration / num_ticks
    for idx in range(num_ticks + 1):
        t = idx * tick_interval
        left_pct = (t / duration) * 100
        # 刻度线
        ticks_html += (
            f'<div style="position:absolute; '
            f'left:calc({label_width}px + (100% - {label_width}px) * {left_pct / 100}); '
            f'top:0; height:{ticks_area_top - 2}px; width:1px; background:rgba(0,0,0,0.08);"></div>'
        )
        # 刻度数字
        ticks_html += (
            f'<div style="position:absolute; '
            f'left:calc({label_width}px + (100% - {label_width}px) * {left_pct / 100}); '
            f'top:{ticks_area_top}px; font-size:11px; color:#888; '
            f'transform:translateX(-50%); white-space:nowrap;">'
            f'{format_time(t)}</div>'
        )

    # 当前片段指示器
    current_seg = segments[current_idx]
    current_left_pct = (current_seg['start'] / duration) * 100
    indicator_html = (
        f'<div style="position:absolute; '
        f'left:calc({label_width}px + (100% - {label_width}px) * {current_left_pct / 100}); '
        f'top:0; height:{ticks_area_top}px; width:2px; background:#ff4444; z-index:15; '
        f'opacity:0.7;"></div>'
    )

    # 组合
    timeline_html = f"""
    <div style="background:white; padding:16px 20px 12px; border-radius:12px;
                margin:8px 0 16px; box-shadow:0 2px 12px rgba(0,0,0,0.06);
                border:1px solid #eee;">
        <div style="position:relative; height:{chart_height}px; user-select:none;">
            {ticks_html}
            {tracks_html}
            {indicator_html}
        </div>
    </div>
    """
    st.markdown(timeline_html, unsafe_allow_html=True)

    # 当前片段信息
    type_info = SEGMENT_TYPES.get(current_seg['type'], {})
    st.caption(
        f"▶ 当前: **{type_info.get('icon','')} {type_info.get('name','')}** | "
        f"`{current_seg['label']}` | "
        f"{format_time(current_seg['start'])} → {format_time(current_seg['end'])} "
        f"({current_seg['end']-current_seg['start']:.1f}秒) | "
        f"片段 {current_idx + 1}/{len(segments)}"
    )

    return None


# ============= 侧边栏 =============

def render_sidebar() -> Tuple[Optional[str], Dict]:
    st.sidebar.title("📁 V6 标注文件列表")

    if not ANNOTATIONS_DIR.exists():
        st.sidebar.error(f"目录不存在: {ANNOTATIONS_DIR}")
        return None, {}

    annotation_files = sorted([f for f in ANNOTATIONS_DIR.glob("*.json") if f.name != 'annotation_errors.json'])
    review_status = load_review_status()

    st.sidebar.markdown(f"**📊 共 {len(annotation_files)} 个文件**")
    approved_total = sum(1 for v in review_status.values() if v.get('status') == 'approved')
    st.sidebar.markdown(f"✅ 已批准片段: {approved_total}")
    st.sidebar.markdown("---")

    search = st.sidebar.text_input("🔍 搜索文件", key='search')
    st.sidebar.markdown("---")

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
            st.rerun()

    return st.session_state.get('selected_file'), {}


# ============= 主函数 =============

def main():
    st.title("🔬 AI标注质量检查平台 V6")
    st.caption("适配 V6 标注格式 | 支持场景概览·角色动态·欲望维度·互动关系·元数据")

    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
    if 'selected_segment_idx' not in st.session_state:
        st.session_state.selected_segment_idx = 0
    if 'show_json' not in st.session_state:
        st.session_state.show_json = False
    if 'show_timeline' not in st.session_state:
        st.session_state.show_timeline = True

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

            if st.session_state.selected_segment_idx >= len(segments):
                st.session_state.selected_segment_idx = 0

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
                st.metric("✅ 已批准", f"{approved}/{len(segments)}")

            # 场景概览 (v6 新增)
            render_scene_context_panel(annotation)

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
                    "选择片段", options=range(len(segments)),
                    format_func=lambda x: segment_options[x],
                    index=st.session_state.selected_segment_idx,
                    key='segment_select', label_visibility='collapsed'
                )
                if selected_idx != st.session_state.selected_segment_idx:
                    st.session_state.selected_segment_idx = selected_idx
                    st.rerun()

            # 时间轴
            if st.session_state.show_timeline:
                timeline_selection = render_interactive_timeline(
                    segments, annotation.get('duration_seconds', 60),
                    st.session_state.selected_segment_idx
                )
                if timeline_selection and 'selection' in timeline_selection:
                    selected_points = timeline_selection['selection'].get('point_indices', [])
                    if selected_points:
                        new_idx = selected_points[0]
                        if new_idx != st.session_state.selected_segment_idx:
                            st.session_state.selected_segment_idx = new_idx
                            st.rerun()

            st.markdown("---")
            current_segment = segments[st.session_state.selected_segment_idx]

            # 主内容区
            if st.session_state.show_json:
                col_video, col_detail, col_json = st.columns([1.2, 1.2, 1])
            else:
                col_video, col_detail = st.columns([1.2, 1.3])

            with col_video:
                render_video_player(video_path, current_segment)

            with col_detail:
                render_segment_detail_panel(current_segment, annotation)
                st.markdown("---")
                render_review_actions(current_segment, annotation, file_path, video_id)

            if st.session_state.show_json:
                with col_json:
                    render_json_editor(current_segment, annotation, file_path)

            # 底部面板 (v6 新增)
            st.markdown("---")
            render_inter_character_dynamics_panel(annotation)
            render_annotation_metadata_panel(annotation)

            # 统计
            st.markdown("---")
            render_stats_summary(annotation, segments, video_id)

    else:
        render_welcome_page()


def render_stats_summary(annotation: Dict, segments: List[Dict], video_id: str):
    review_status = load_review_status()
    stats = {'approved': 0, 'needs_modification': 0, 'to_delete': 0, 'pending': 0}
    for seg in segments:
        key = f"{video_id}_{seg['id']}"
        status = review_status.get(key, {}).get('status', 'pending')
        stats[status] = stats.get(status, 0) + 1

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
    st.markdown("## 👋 欢迎使用标注质量检查平台 V6")
    st.markdown("---")
    st.markdown("""
    ### 🆕 V6 相比 V3 的改进
    - 📍 **场景概览面板** — 显示物理环境、社交语境、情感氛围
    - 📐 **欲望维度信息** — 显示 dimension、explicitness、temporal_type
    - 📈 **角色属性动态** — 显示 attribute_dynamics 变化轨迹
    - 🤝 **角色互动关系** — 显示 inter_character_dynamics
    - 📋 **标注元数据** — 显示模型版本、质量标志、维度分布
    - 🔧 **强度修复** — 正确显示 1-5 整数强度（进度条显示）
    - 🎬 **视频播放优化** — 移除 base64 编码方案
    """)

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

    if not ANNOTATIONS_DIR.exists():
        st.warning(f"标注目录不存在: {ANNOTATIONS_DIR}")
        return

    annotation_files = [f for f in ANNOTATIONS_DIR.glob("*.json") if f.name != 'annotation_errors.json']
    review_status = load_review_status()

    total_segments = 0
    for f in annotation_files:
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
