# frontend/app_annotation_checker.py
"""
视频标注可视化检查平台
功能：
1. 加载 annotations_test 目录中的 JSON 标注文件
2. 显示所有带时间戳的标注段
3. 视频播放器支持跳转到指定时间点
4. 标记标注段的合理性（合理/需要修改）
5. 可视化编辑 JSON 内容
"""
import streamlit as st
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
import sys

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 配置
st.set_page_config(
    page_title="视频标注检查平台",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API配置
API_BASE_URL = "http://localhost:8000"

# ============= 工具函数 =============

def check_api_connection():
    """检查API连接"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def load_annotation_list():
    """加载标注文件列表"""
    try:
        response = requests.get(f"{API_BASE_URL}/annotations_test/list", timeout=5)
        if response.status_code == 200:
            return response.json().get("annotations", [])
    except Exception as e:
        st.error(f"加载列表失败: {e}")
    return []

def load_annotation_data(video_id: str):
    """加载标注数据"""
    try:
        response = requests.get(f"{API_BASE_URL}/annotations_test/{video_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"加载标注数据失败: {e}")
    return None

def load_segments(video_id: str):
    """加载标注段列表"""
    try:
        response = requests.get(f"{API_BASE_URL}/annotations_test/{video_id}/segments", timeout=10)
        if response.status_code == 200:
            return response.json().get("segments", [])
    except Exception as e:
        st.error(f"加载标注段失败: {e}")
    return []

def update_segment_review(video_id: str, segment_id: str, review_status: str, notes: str = ""):
    """更新标注段审核状态"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/annotations_test/{video_id}/segments/{segment_id}/review",
            json={"review_status": review_status, "notes": notes},
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"更新审核状态失败: {e}")
        return False

def save_annotation_data(video_id: str, data: Dict):
    """保存标注数据"""
    try:
        response = requests.put(
            f"{API_BASE_URL}/annotations_test/{video_id}",
            json=data,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"保存失败: {e}")
        return False

def format_time(seconds: float) -> str:
    """格式化时间显示"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def get_segment_type_label(segment_type: str) -> str:
    """获取标注段类型标签"""
    labels = {
        "character_initial_state": "角色初始状态",
        "character_final_state": "角色最终状态",
        "desire_motivation": "欲望动机分析",
        "desire_transition": "欲望转换",
        "behavioral_sequence": "行为序列",
        "key_segment_qa": "QA关键段"
    }
    return labels.get(segment_type, segment_type)

def get_review_status_color(status: str) -> str:
    """获取审核状态颜色"""
    colors = {
        "pending": "⚪",
        "approved": "✅",
        "needs_revision": "⚠️"
    }
    return colors.get(status, "⚪")

# ============= 主界面 =============

def main():
    st.title("🎬 视频标注可视化检查平台")
    st.markdown("**功能**: 检查 annotations_test 目录中的标注文件，支持视频播放对照、标记合理性和编辑JSON")
    
    # 检查API连接
    if not check_api_connection():
        st.error("❌ 无法连接到后端API服务")
        st.info("请先启动后端服务: `python -m uvicorn backend.api:app --reload`")
        st.stop()
    
    st.markdown("---")
    
    # 侧边栏：文件选择
    with st.sidebar:
        st.header("📁 标注文件")
        
        # 加载文件列表
        annotations = load_annotation_list()
        
        if not annotations:
            st.warning("没有找到标注文件")
            st.stop()
        
        # 文件选择器
        selected_file = st.selectbox(
            "选择标注文件",
            options=annotations,
            format_func=lambda x: f"{x['file_name']} ({x['video_id']})",
            key="file_selector"
        )
        
        if selected_file:
            video_id = selected_file["video_id"]
            st.info(f"""
            **视频ID**: {video_id}
            
            **时长**: {selected_file.get('duration_seconds', 0):.1f}秒
            
            **角色数**: {selected_file.get('total_characters', 0)}
            
            **欲望分析**: {selected_file.get('total_desires', 0)}
            
            **转换数**: {selected_file.get('total_transitions', 0)}
            
            **行为序列**: {selected_file.get('total_sequences', 0)}
            """)
    
    # 主内容区
    if selected_file:
        video_id = selected_file["video_id"]
        video_path = selected_file.get("video_path", "")
        
        # 加载标注数据和段列表
        if "annotation_data" not in st.session_state or st.session_state.get("current_video_id") != video_id:
            with st.spinner("加载标注数据..."):
                st.session_state.annotation_data = load_annotation_data(video_id)
                st.session_state.segments = load_segments(video_id)
                st.session_state.current_video_id = video_id
        
        annotation_data = st.session_state.annotation_data
        segments = st.session_state.segments
        
        if not annotation_data:
            st.error("无法加载标注数据")
            st.stop()
        
        # 创建标签页
        tab1, tab2, tab3 = st.tabs(["📹 视频播放对照", "📋 标注段列表", "✏️ JSON编辑器"])
        
        # 标签页1: 视频播放对照
        with tab1:
            render_video_player_tab(video_path, segments, video_id)
        
        # 标签页2: 标注段列表
        with tab2:
            render_segments_list_tab(segments, video_id, annotation_data)
        
        # 标签页3: JSON编辑器
        with tab3:
            render_json_editor_tab(annotation_data, video_id)

def render_video_player_tab(video_path: str, segments: List, video_id: str):
    """视频播放对照标签页"""
    st.header("📹 视频播放对照")
    
    if not video_path or not Path(video_path).exists():
        st.warning(f"视频文件不存在: {video_path}")
        st.info("请检查 video_path 字段是否正确")
        return
    
    # 视频播放器
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("视频播放器")
        try:
            # 尝试直接读取文件
            video_file = Path(video_path)
            if video_file.exists():
                with open(video_file, 'rb') as f:
                    video_bytes = f.read()
                st.video(video_bytes)
            else:
                # 尝试通过API获取
                try:
                    response = requests.get(
                        f"{API_BASE_URL}/videos/file",
                        params={"video_path": video_path},
                        timeout=30
                    )
                    if response.status_code == 200:
                        st.video(response.content)
                    else:
                        st.error(f"无法通过API加载视频: {response.status_code}")
                except Exception as api_e:
                    st.error(f"无法加载视频: {api_e}")
                    st.info(f"视频路径: {video_path}")
                    st.info("请检查视频文件是否存在，或路径是否正确")
        except Exception as e:
            st.error(f"无法加载视频: {e}")
            st.info(f"视频路径: {video_path}")
    
    with col2:
        st.subheader("快速跳转")
        st.markdown("点击下面的时间点跳转到对应标注段")
        
        # 按时间排序的段列表
        for seg in segments:
            start_time = seg.get("start_seconds", 0)
            end_time = seg.get("end_seconds", 0)
            seg_type = get_segment_type_label(seg.get("type", ""))
            review_status = get_review_status_color(seg.get("review_status", "pending"))
            
            if st.button(
                f"{review_status} {format_time(start_time)} - {format_time(end_time)} | {seg_type}",
                key=f"jump_{seg.get('segment_id')}",
                use_container_width=True
            ):
                st.info(f"跳转到 {format_time(start_time)} - {seg.get('description', '')}")
                # 注意：Streamlit 的 video 组件不支持直接跳转，需要手动操作
    
    # 当前选中段详情
    st.markdown("---")
    st.subheader("标注段详情")
    
    if segments:
        selected_seg_idx = st.selectbox(
            "选择标注段查看详情",
            range(len(segments)),
            format_func=lambda i: f"{format_time(segments[i]['start_seconds'])} - {segments[i]['description']}",
            key="segment_detail_selector"
        )
        
        if selected_seg_idx is not None:
            selected_seg = segments[selected_seg_idx]
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**基本信息**")
                st.write(f"**类型**: {get_segment_type_label(selected_seg.get('type', ''))}")
                st.write(f"**时间**: {format_time(selected_seg['start_seconds'])} - {format_time(selected_seg['end_seconds'])}")
                st.write(f"**角色**: {selected_seg.get('character_id', 'N/A')}")
                st.write(f"**描述**: {selected_seg.get('description', '')}")
                st.write(f"**审核状态**: {get_review_status_color(selected_seg.get('review_status', 'pending'))} {selected_seg.get('review_status', 'pending')}")
            
            with col2:
                st.markdown("**审核操作**")
                review_status = st.radio(
                    "标记合理性",
                    ["pending", "approved", "needs_revision"],
                    index=["pending", "approved", "needs_revision"].index(selected_seg.get("review_status", "pending")),
                    format_func=lambda x: {"pending": "⚪ 待审核", "approved": "✅ 合理", "needs_revision": "⚠️ 需要修改"}[x],
                    key=f"review_{selected_seg.get('segment_id')}"
                )
                
                review_notes = st.text_area(
                    "审核备注",
                    value=selected_seg.get("review_notes", ""),
                    key=f"notes_{selected_seg.get('segment_id')}"
                )
                
                if st.button("保存审核状态", key=f"save_review_{selected_seg.get('segment_id')}"):
                    if update_segment_review(video_id, selected_seg.get("segment_id"), review_status, review_notes):
                        st.success("审核状态已保存")
                        st.rerun()
                    else:
                        st.error("保存失败")
            
            # 显示详细数据
            st.markdown("---")
            st.markdown("**详细数据**")
            st.json(selected_seg.get("data", {}))

def render_segments_list_tab(segments: List, video_id: str, annotation_data: Dict):
    """标注段列表标签页"""
    st.header("📋 标注段列表")
    
    if not segments:
        st.warning("没有找到标注段")
        return
    
    # 统计信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总段数", len(segments))
    with col2:
        pending = sum(1 for s in segments if s.get("review_status") == "pending")
        st.metric("待审核", pending)
    with col3:
        approved = sum(1 for s in segments if s.get("review_status") == "approved")
        st.metric("已通过", approved)
    with col4:
        needs_revision = sum(1 for s in segments if s.get("review_status") == "needs_revision")
        st.metric("需修改", needs_revision)
    
    st.markdown("---")
    
    # 筛选选项
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox(
            "按类型筛选",
            ["全部"] + list(set(s.get("type", "") for s in segments)),
            key="filter_type"
        )
    with col2:
        filter_status = st.selectbox(
            "按审核状态筛选",
            ["全部", "pending", "approved", "needs_revision"],
            format_func=lambda x: {"全部": "全部", "pending": "⚪ 待审核", "approved": "✅ 合理", "needs_revision": "⚠️ 需要修改"}.get(x, x),
            key="filter_status"
        )
    with col3:
        filter_character = st.selectbox(
            "按角色筛选",
            ["全部"] + list(set(s.get("character_id", "") for s in segments if s.get("character_id"))),
            key="filter_character"
        )
    
    # 应用筛选
    filtered_segments = segments
    if filter_type != "全部":
        filtered_segments = [s for s in filtered_segments if s.get("type") == filter_type]
    if filter_status != "全部":
        filtered_segments = [s for s in filtered_segments if s.get("review_status") == filter_status]
    if filter_character != "全部":
        filtered_segments = [s for s in filtered_segments if s.get("character_id") == filter_character]
    
    st.markdown(f"**显示 {len(filtered_segments)} 个标注段**")
    
    # 显示段列表
    for idx, seg in enumerate(filtered_segments):
        with st.expander(
            f"{get_review_status_color(seg.get('review_status', 'pending'))} "
            f"[{format_time(seg['start_seconds'])} - {format_time(seg['end_seconds'])}] "
            f"{get_segment_type_label(seg.get('type', ''))} - {seg.get('description', '')}",
            expanded=False
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**段ID**: {seg.get('segment_id')}")
                st.markdown(f"**类型**: {get_segment_type_label(seg.get('type', ''))}")
                st.markdown(f"**时间范围**: {format_time(seg['start_seconds'])} - {format_time(seg['end_seconds'])}")
                st.markdown(f"**角色**: {seg.get('character_id', 'N/A')}")
                st.markdown(f"**描述**: {seg.get('description', '')}")
                st.markdown(f"**审核状态**: {seg.get('review_status', 'pending')}")
                
                if seg.get("review_notes"):
                    st.markdown(f"**审核备注**: {seg.get('review_notes')}")
            
            with col2:
                # 快速审核
                new_status = st.radio(
                    "审核状态",
                    ["pending", "approved", "needs_revision"],
                    index=["pending", "approved", "needs_revision"].index(seg.get("review_status", "pending")),
                    key=f"quick_review_{seg.get('segment_id')}"
                )
                
                notes = st.text_input(
                    "备注",
                    value=seg.get("review_notes", ""),
                    key=f"quick_notes_{seg.get('segment_id')}"
                )
                
                if st.button("保存", key=f"save_{seg.get('segment_id')}"):
                    if update_segment_review(video_id, seg.get("segment_id"), new_status, notes):
                        st.success("已保存")
                        st.rerun()
            
            # 显示数据
            st.markdown("**数据内容**")
            st.json(seg.get("data", {}))

def render_json_editor_tab(annotation_data: Dict, video_id: str):
    """JSON编辑器标签页"""
    st.header("✏️ JSON编辑器")
    st.markdown("**注意**: 直接编辑JSON内容，修改后点击保存")
    
    # JSON编辑器
    json_str = st.text_area(
        "JSON内容",
        value=json.dumps(annotation_data, ensure_ascii=False, indent=2),
        height=600,
        key="json_editor"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 保存JSON", type="primary"):
            try:
                # 验证JSON格式
                edited_data = json.loads(json_str)
                
                # 保存
                if save_annotation_data(video_id, edited_data):
                    st.success("JSON已保存")
                    # 清除缓存，重新加载
                    if "annotation_data" in st.session_state:
                        del st.session_state.annotation_data
                    if "segments" in st.session_state:
                        del st.session_state.segments
                    st.rerun()
                else:
                    st.error("保存失败")
            except json.JSONDecodeError as e:
                st.error(f"JSON格式错误: {e}")
    
    with col2:
        if st.button("🔄 重置为原始内容"):
            if "annotation_data" in st.session_state:
                del st.session_state.annotation_data
            if "segments" in st.session_state:
                del st.session_state.segments
            st.rerun()
    
    # JSON验证信息
    st.markdown("---")
    st.markdown("**JSON结构信息**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**视频ID**: {annotation_data.get('video_id', 'N/A')}")
        st.write(f"**时长**: {annotation_data.get('duration_seconds', 0):.1f}秒")
    with col2:
        st.write(f"**角色数**: {len(annotation_data.get('characters', []))}")
        st.write(f"**欲望分析数**: {len(annotation_data.get('desire_motivation_analysis', []))}")
    with col3:
        st.write(f"**转换数**: {len(annotation_data.get('desire_transitions', []))}")
        st.write(f"**行为序列数**: {len(annotation_data.get('behavioral_sequence', []))}")

if __name__ == "__main__":
    main()

