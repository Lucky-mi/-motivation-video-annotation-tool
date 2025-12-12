# frontend/annotation_reviewer.py
"""
AI标注质量检查平台
支持视频片段播放、标注验证、人工修改JSON
"""
import streamlit as st
from pathlib import Path
import sys
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

# 页面配置
st.set_page_config(
    page_title="标注质量检查平台",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 配置路径
ANNOTATIONS_DIR = Path("data/annotations_test")
VIDEOS_DIR = Path("data/Youtube_videos")
REVIEW_STATUS_FILE = Path("data/review_status.json")


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
    # 备份原文件
    backup_dir = Path("data/annotations_backup")
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original)

    # 保存新文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_video_path(annotation: Dict) -> Optional[Path]:
    """获取视频路径"""
    video_path_str = annotation.get('video_path', '')
    if video_path_str:
        # 尝试多种路径格式
        paths_to_try = [
            Path(video_path_str),
            Path(video_path_str.replace('\\', '/')),
            VIDEOS_DIR / f"{annotation.get('video_id', '')}.mp4",
            VIDEOS_DIR / annotation.get('video_id', ''),
        ]
        for p in paths_to_try:
            if p.exists():
                return p
    return None


def format_timestamp(seconds: float) -> str:
    """格式化时间戳"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def get_all_segments(annotation: Dict) -> List[Dict]:
    """提取所有可播放的片段"""
    segments = []

    # 1. 从 desire_motivation_analysis 提取
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
                'confidence': item.get('confidence', ''),
                'reasoning': item.get('reasoning_chain', ''),
                'evidence': item.get('supporting_evidence', []),
                'raw_data': item
            })

    # 2. 从 desire_transitions 提取
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
                'trigger': item.get('trigger_event', {}),
                'interpretation': item.get('psychological_interpretation', ''),
                'markers': item.get('behavioral_markers', []),
                'raw_data': item
            })

    # 3. 从 behavioral_sequence 提取
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
                'mental_state': item.get('inferred_mental_state', ''),
                'raw_data': item
            })

    # 4. 从 key_segments_for_qa 提取
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
                'raw_data': item
            })

    # 按开始时间排序
    segments.sort(key=lambda x: x['start'])
    return segments


def render_video_player(video_path: Path, start_time: float = 0, end_time: float = None):
    """渲染视频播放器（支持时间段）"""
    if not video_path or not video_path.exists():
        st.warning("视频文件不存在")
        return

    with open(video_path, 'rb') as f:
        video_bytes = f.read()

    st.video(video_bytes, start_time=int(start_time))

    if end_time:
        st.caption(f"片段: {format_timestamp(start_time)} - {format_timestamp(end_time)} (时长: {end_time - start_time:.1f}秒)")


def render_segment_detail(segment: Dict, annotation: Dict, file_path: Path):
    """渲染片段详情和编辑界面"""
    seg_type = segment['type']

    # 类型标签颜色
    type_colors = {
        'desire_motivation': '🟢',
        'desire_transition': '🔵',
        'behavioral_sequence': '🟡',
        'key_segment_qa': '🟣'
    }
    type_names = {
        'desire_motivation': '动机分析',
        'desire_transition': '欲望转变',
        'behavioral_sequence': '行为序列',
        'key_segment_qa': 'QA关键片段'
    }

    st.markdown(f"### {type_colors.get(seg_type, '⚪')} {type_names.get(seg_type, seg_type)}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**ID:** `{segment['id']}`")
        st.markdown(f"**角色:** {segment['character']}")
    with col2:
        st.markdown(f"**时间:** {format_timestamp(segment['start'])} - {format_timestamp(segment['end'])}")
        st.markdown(f"**标签:** {segment['label']}")

    st.markdown("---")

    # 根据类型显示不同内容
    if seg_type == 'desire_motivation':
        render_desire_motivation_detail(segment)
    elif seg_type == 'desire_transition':
        render_desire_transition_detail(segment)
    elif seg_type == 'behavioral_sequence':
        render_behavioral_sequence_detail(segment)
    elif seg_type == 'key_segment_qa':
        render_key_segment_detail(segment)

    st.markdown("---")

    # 审核操作
    render_review_actions(segment, annotation, file_path)


def render_desire_motivation_detail(segment: Dict):
    """渲染动机分析详情"""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**强度:** {segment.get('intensity', 'N/A')}")
    with col2:
        st.markdown(f"**马斯洛层级:** {segment.get('maslow_level', 'N/A')}")
    with col3:
        st.markdown(f"**置信度:** {segment.get('confidence', 'N/A')}")

    with st.expander("推理链条", expanded=True):
        st.info(segment.get('reasoning', '无'))

    with st.expander("支撑证据"):
        evidence = segment.get('evidence', [])
        for e in evidence:
            st.markdown(f"- **{format_timestamp(e.get('timestamp_seconds', 0))}** [{e.get('behavior_type', '')}]: {e.get('description', '')}")


def render_desire_transition_detail(segment: Dict):
    """渲染欲望转变详情"""
    st.markdown(f"**转变类型:** {segment.get('transition_type', 'N/A')}")

    trigger = segment.get('trigger', {})
    if trigger:
        st.markdown(f"**触发事件:** [{format_timestamp(trigger.get('timestamp_seconds', 0))}] {trigger.get('description', '')}")

    with st.expander("心理解释", expanded=True):
        st.info(segment.get('interpretation', '无'))

    with st.expander("行为标记"):
        markers = segment.get('markers', [])
        for m in markers:
            st.markdown(f"- **{format_timestamp(m.get('timestamp_seconds', 0))}** [{m.get('marker_type', '')}]: {m.get('description', '')}")


def render_behavioral_sequence_detail(segment: Dict):
    """渲染行为序列详情"""
    st.markdown(f"**强度:** {segment.get('intensity', 'N/A')}")

    with st.expander("行为描述", expanded=True):
        st.info(segment.get('description', '无'))

    st.markdown(f"**推断心理状态:** {segment.get('mental_state', 'N/A')}")


def render_key_segment_detail(segment: Dict):
    """渲染QA关键片段详情"""
    st.markdown(f"**难度:** {segment.get('difficulty', 'N/A')}")
    st.markdown(f"**QA类型:** {', '.join(segment.get('qa_types', []))}")

    with st.expander("描述", expanded=True):
        st.info(segment.get('description', '无'))

    with st.expander("心理意义"):
        st.info(segment.get('significance', '无'))


def render_review_actions(segment: Dict, annotation: Dict, file_path: Path):
    """渲染审核操作"""
    review_status = load_review_status()
    video_id = annotation.get('video_id', '')
    segment_key = f"{video_id}_{segment['id']}"

    current_status = review_status.get(segment_key, {})

    st.markdown("### 审核操作")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ 标记为合理", key=f"approve_{segment['id']}", use_container_width=True, type="primary"):
            review_status[segment_key] = {
                'status': 'approved',
                'timestamp': datetime.now().isoformat(),
                'segment_type': segment['type']
            }
            save_review_status(review_status)
            st.success("已标记为合理")
            st.rerun()

    with col2:
        if st.button("❌ 标记需修改", key=f"reject_{segment['id']}", use_container_width=True):
            review_status[segment_key] = {
                'status': 'needs_modification',
                'timestamp': datetime.now().isoformat(),
                'segment_type': segment['type']
            }
            save_review_status(review_status)
            st.warning("已标记需修改")
            st.rerun()

    with col3:
        if st.button("🗑️ 标记删除", key=f"delete_{segment['id']}", use_container_width=True):
            review_status[segment_key] = {
                'status': 'to_delete',
                'timestamp': datetime.now().isoformat(),
                'segment_type': segment['type']
            }
            save_review_status(review_status)
            st.error("已标记为删除")
            st.rerun()

    # 显示当前状态
    if current_status:
        status_map = {
            'approved': ('✅ 已批准', 'success'),
            'needs_modification': ('⚠️ 需修改', 'warning'),
            'to_delete': ('🗑️ 待删除', 'error')
        }
        status_text, status_type = status_map.get(current_status.get('status'), ('❓ 未知', 'info'))
        st.markdown(f"**当前状态:** {status_text}")

    # 备注
    note_key = f"note_{segment['id']}"
    note = st.text_area("审核备注", value=current_status.get('note', ''), key=note_key, height=80)
    if st.button("保存备注", key=f"save_note_{segment['id']}"):
        if segment_key not in review_status:
            review_status[segment_key] = {}
        review_status[segment_key]['note'] = note
        save_review_status(review_status)
        st.success("备注已保存")


def render_json_editor(segment: Dict, annotation: Dict, file_path: Path):
    """渲染JSON编辑器"""
    st.markdown("### JSON编辑器")

    raw_data = segment.get('raw_data', {})

    # 显示当前JSON
    edited_json = st.text_area(
        "编辑JSON内容",
        value=json.dumps(raw_data, ensure_ascii=False, indent=2),
        height=400,
        key=f"json_editor_{segment['id']}"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 保存修改", key=f"save_json_{segment['id']}", type="primary", use_container_width=True):
            try:
                new_data = json.loads(edited_json)

                # 根据类型更新对应的数组
                seg_type = segment['type']
                type_to_key = {
                    'desire_motivation': 'desire_motivation_analysis',
                    'desire_transition': 'desire_transitions',
                    'behavioral_sequence': 'behavioral_sequence',
                    'key_segment_qa': 'key_segments_for_qa'
                }

                array_key = type_to_key.get(seg_type)
                if array_key and array_key in annotation:
                    # 找到并更新对应项
                    id_field = {
                        'desire_motivation': 'analysis_id',
                        'desire_transition': 'transition_id',
                        'behavioral_sequence': 'sequence_id',
                        'key_segment_qa': 'segment_id'
                    }.get(seg_type, 'id')

                    for idx, item in enumerate(annotation[array_key]):
                        if item.get(id_field) == segment['id']:
                            annotation[array_key][idx] = new_data
                            break

                    # 保存文件
                    save_annotation(file_path, annotation)
                    st.success("JSON已保存!")
                    st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"JSON格式错误: {e}")

    with col2:
        if st.button("↩️ 重置", key=f"reset_json_{segment['id']}", use_container_width=True):
            st.rerun()


def render_sidebar():
    """渲染侧边栏"""
    st.sidebar.header("📁 标注文件")

    # 获取所有标注文件
    annotation_files = sorted(ANNOTATIONS_DIR.glob("*.json"))

    # 过滤选项
    filter_option = st.sidebar.selectbox(
        "过滤",
        options=['全部', '已审核', '未审核', '需修改'],
        key='file_filter'
    )

    # 搜索
    search_term = st.sidebar.text_input("搜索文件", key='file_search')

    # 过滤文件列表
    review_status = load_review_status()
    filtered_files = []

    for f in annotation_files:
        if f.name == 'annotation_errors.json':
            continue
        if search_term and search_term.lower() not in f.stem.lower():
            continue
        filtered_files.append(f)

    # 显示文件列表
    st.sidebar.markdown(f"共 {len(filtered_files)} 个文件")

    selected_file = None
    for f in filtered_files:
        # 计算该文件的审核进度
        video_id = f.stem
        file_segments = [k for k in review_status.keys() if k.startswith(f"{video_id}_")]
        approved = sum(1 for k in file_segments if review_status[k].get('status') == 'approved')

        # 显示文件按钮
        label = f.stem[:20] + ("..." if len(f.stem) > 20 else "")
        if file_segments:
            label = f"{label} [{approved}/{len(file_segments)}]"

        if st.sidebar.button(label, key=f"file_{f.stem}", use_container_width=True):
            st.session_state.selected_file = str(f)
            st.session_state.selected_segment_idx = 0

    return st.session_state.get('selected_file')


def main():
    st.title("🔍 AI标注质量检查平台")
    st.markdown("检查标注片段、播放对应视频、标记审核状态、编辑JSON")

    # 初始化session state
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
    if 'selected_segment_idx' not in st.session_state:
        st.session_state.selected_segment_idx = 0
    if 'show_json_editor' not in st.session_state:
        st.session_state.show_json_editor = False

    # 侧边栏
    selected_file_path = render_sidebar()

    if st.session_state.selected_file:
        file_path = Path(st.session_state.selected_file)
        annotation = load_annotation(file_path)

        if annotation:
            # 获取视频路径
            video_path = get_video_path(annotation)

            # 获取所有片段
            segments = get_all_segments(annotation)

            if not segments:
                st.warning("该标注文件中没有可检查的片段")
                return

            # 顶部信息栏
            st.markdown("---")
            info_cols = st.columns(4)
            with info_cols[0]:
                st.metric("视频ID", annotation.get('video_id', 'N/A'))
            with info_cols[1]:
                st.metric("总时长", f"{annotation.get('duration_seconds', 0)}秒")
            with info_cols[2]:
                st.metric("片段数", len(segments))
            with info_cols[3]:
                st.metric("角色数", len(annotation.get('characters', [])))

            st.markdown("---")

            # 片段选择器
            col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 3, 1, 1])

            with col_nav1:
                if st.button("⬅️ 上一段", use_container_width=True):
                    if st.session_state.selected_segment_idx > 0:
                        st.session_state.selected_segment_idx -= 1
                        st.rerun()

            with col_nav2:
                # 片段下拉选择
                segment_options = [
                    f"[{s['type'][:8]}] {s['id']} ({format_timestamp(s['start'])}-{format_timestamp(s['end'])})"
                    for s in segments
                ]
                selected_idx = st.selectbox(
                    "选择片段",
                    options=range(len(segments)),
                    format_func=lambda x: segment_options[x],
                    index=st.session_state.selected_segment_idx,
                    key='segment_selector'
                )
                if selected_idx != st.session_state.selected_segment_idx:
                    st.session_state.selected_segment_idx = selected_idx
                    st.rerun()

            with col_nav3:
                if st.button("➡️ 下一段", use_container_width=True):
                    if st.session_state.selected_segment_idx < len(segments) - 1:
                        st.session_state.selected_segment_idx += 1
                        st.rerun()

            with col_nav4:
                st.session_state.show_json_editor = st.checkbox("显示JSON编辑器", value=st.session_state.show_json_editor)

            st.markdown("---")

            # 当前片段
            current_segment = segments[st.session_state.selected_segment_idx]

            # 主内容区
            if st.session_state.show_json_editor:
                col_video, col_detail, col_json = st.columns([1.2, 1, 1])
            else:
                col_video, col_detail = st.columns([1.2, 1])

            with col_video:
                st.markdown("### 视频播放")
                render_video_player(video_path, current_segment['start'], current_segment['end'])

                # 显示角色信息
                if current_segment['character']:
                    char_info = None
                    for char in annotation.get('characters', []):
                        if char.get('character_id') == current_segment['character']:
                            char_info = char
                            break

                    if char_info:
                        with st.expander("角色信息"):
                            st.markdown(f"**描述:** {char_info.get('physical_description', '')}")
                            st.markdown(f"**年龄组:** {char_info.get('estimated_age_group', '')}")
                            st.markdown(f"**场景角色:** {char_info.get('role_in_scene', '')}")

            with col_detail:
                render_segment_detail(current_segment, annotation, file_path)

            if st.session_state.show_json_editor:
                with col_json:
                    render_json_editor(current_segment, annotation, file_path)

            # 底部统计
            st.markdown("---")
            render_review_summary(annotation, segments)

    else:
        # 欢迎页面
        st.markdown("## 欢迎使用标注质量检查平台")
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 1️⃣ 选择文件")
            st.markdown("从左侧选择要检查的标注文件")

        with col2:
            st.markdown("### 2️⃣ 播放片段")
            st.markdown("每个标注片段对应视频播放，便于核对")

        with col3:
            st.markdown("### 3️⃣ 审核/编辑")
            st.markdown("标记是否合理，或直接编辑JSON")

        # 显示总体统计
        st.markdown("---")
        render_overall_stats()


def render_review_summary(annotation: Dict, segments: List[Dict]):
    """渲染审核汇总"""
    review_status = load_review_status()
    video_id = annotation.get('video_id', '')

    approved = 0
    needs_mod = 0
    to_delete = 0
    pending = 0

    for seg in segments:
        key = f"{video_id}_{seg['id']}"
        status = review_status.get(key, {}).get('status')
        if status == 'approved':
            approved += 1
        elif status == 'needs_modification':
            needs_mod += 1
        elif status == 'to_delete':
            to_delete += 1
        else:
            pending += 1

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("✅ 已批准", approved)
    with col2:
        st.metric("⚠️ 需修改", needs_mod)
    with col3:
        st.metric("🗑️ 待删除", to_delete)
    with col4:
        st.metric("⏳ 待审核", pending)


def render_overall_stats():
    """渲染总体统计"""
    st.markdown("### 总体统计")

    annotation_files = list(ANNOTATIONS_DIR.glob("*.json"))
    review_status = load_review_status()

    total_segments = 0
    reviewed = len(review_status)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("标注文件数", len(annotation_files))
    with col2:
        st.metric("已审核片段", reviewed)
    with col3:
        approved = sum(1 for v in review_status.values() if v.get('status') == 'approved')
        st.metric("已批准片段", approved)


if __name__ == "__main__":
    main()
