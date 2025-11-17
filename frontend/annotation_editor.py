# frontend/annotation_editor.py
"""
标注编辑器组件
"""
import streamlit as st
from pathlib import Path
from typing import Dict, List
import sys

sys.path.append(str(Path(__file__).parent.parent))
from backend.annotation_schema import AnnotationSchema
from config.config import config

class AnnotationEditor:
    """标注编辑器"""
    
    def __init__(self):
        self.schema = AnnotationSchema()
        
        # 初始化session_state
        if 'current_annotation' not in st.session_state:
            st.session_state.current_annotation = None
        if 'current_frame_idx' not in st.session_state:
            st.session_state.current_frame_idx = 0
        if 'annotation_changed' not in st.session_state:
            st.session_state.annotation_changed = False
    
    def load_or_create_annotation(self, video_path: str, keyframes: List[Dict]) -> Dict:
        """加载或创建标注"""
        video_name = Path(video_path).stem
        annotation_path = Path(config.get('paths.annotations')) / f"{video_name}.json"
        
        # 尝试加载已有标注
        annotation = self.schema.load_annotation(str(annotation_path))
        
        if annotation is None:
            # 创建新标注
            annotation = self.schema.create_empty_annotation(video_path, keyframes)
            st.info("📝 创建新标注")
        else:
            st.success("✅ 加载已有标注")
        
        return annotation
    
    def save_current_annotation(self):
        """保存当前标注"""
        if st.session_state.current_annotation is None:
            return
        
        annotation = st.session_state.current_annotation
        video_name = Path(annotation['video_info']['video_path']).stem
        annotation_path = Path(config.get('paths.annotations')) / f"{video_name}.json"
        
        self.schema.save_annotation(annotation, str(annotation_path))
        st.session_state.annotation_changed = False
        return str(annotation_path)
    
    def render(self):
        """渲染标注界面"""
        if st.session_state.current_annotation is None:
            st.warning("⚠️ 请先提取关键帧")
            return
        
        annotation = st.session_state.current_annotation
        keyframes = annotation['keyframes']
        
        if not keyframes:
            st.error("❌ 没有可标注的关键帧")
            return
        
        # 顶部工具栏
        self._render_toolbar(keyframes)
        
        st.markdown("---")
        
        # 主编辑区域
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self._render_frame_viewer(keyframes)
        
        with col2:
            self._render_annotation_panel(keyframes)
        
        st.markdown("---")
        
        # 底部时间轴
        self._render_timeline(keyframes)
    
    def _render_toolbar(self, keyframes: List[Dict]):
        """渲染工具栏"""
        cols = st.columns([2, 1, 1, 1, 1, 2])
        
        with cols[0]:
            st.markdown(f"### 📍 帧 {st.session_state.current_frame_idx + 1} / {len(keyframes)}")
        
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
            if st.button("💾 保存", type="primary", use_container_width=True):
                path = self.save_current_annotation()
                st.success(f"✅ 已保存到: {Path(path).name}")
        
        with cols[4]:
            if st.button("📊 预览", use_container_width=True):
                st.session_state.show_preview = True
        
        with cols[5]:
            # 进度显示
            annotated = sum(1 for kf in keyframes if kf['explicit_motivation'])
            progress = annotated / len(keyframes) if keyframes else 0
            st.progress(progress, text=f"进度: {annotated}/{len(keyframes)}")
    
    def _render_frame_viewer(self, keyframes: List[Dict]):
        """渲染关键帧查看器"""
        idx = st.session_state.current_frame_idx
        current_frame = keyframes[idx]
        
        st.subheader("🖼️ 当前关键帧")
        
        # 显示图片
        st.image(
            current_frame['frame_path'],
            caption=f"时间点: {current_frame['timestamp_formatted']} ({current_frame['timestamp']:.2f}s)",
            use_container_width=True
        )
        
        # 帧导航滑块
        new_idx = st.slider(
            "快速跳转到帧",
            min_value=0,
            max_value=len(keyframes) - 1,
            value=idx,
            key='frame_slider'
        )
        
        if new_idx != idx:
            st.session_state.current_frame_idx = new_idx
            st.rerun()
    
    def _render_annotation_panel(self, keyframes: List[Dict]):
        """渲染标注面板"""
        idx = st.session_state.current_frame_idx
        current_frame = keyframes[idx]
        
        st.subheader("✏️ 标注面板")
        
        # 显性Motivation
        explicit_motivation = st.text_area(
            "显性Motivation（表面动机）",
            value=current_frame['explicit_motivation'],
            height=80,
            placeholder="例如：想要完成工作任务",
            help="人物表面上表现出来的动机",
            key=f'explicit_{idx}'
        )
        
        # 隐性Desire
        implicit_desire = st.text_area(
            "隐性Desire（深层渴望）",
            value=current_frame['implicit_desire'],
            height=80,
            placeholder="例如：渴望被认可和肯定",
            help="人物内心真正的渴望和需求",
            key=f'implicit_{idx}'
        )
        
        # 隐性程度
        implicit_level = st.select_slider(
            "隐性程度",
            options=[1, 2, 3, 4, 5],
            value=current_frame['implicit_level'],
            format_func=lambda x: {
                1: "😊 非常显性",
                2: "🙂 较显性",
                3: "😐 中等",
                4: "🤔 较隐性",
                5: "🎭 非常隐性"
            }[x],
            help="1=很容易从画面看出，5=需要深度推理才能理解",
            key=f'level_{idx}'
        )
        
        st.markdown("---")
        
        # 视觉线索
        st.markdown("**🔍 视觉线索**")
        visual_cues_text = st.text_input(
            "视觉线索（用逗号分隔）",
            value=", ".join(current_frame['visual_cues']),
            placeholder="例如：皱眉, 紧握拳头, 避免眼神接触",
            help="帮助你推断motivation的画面细节",
            key=f'cues_{idx}'
        )
        visual_cues = [c.strip() for c in visual_cues_text.split(",") if c.strip()]
        
        # 备注
        notes = st.text_area(
            "备注",
            value=current_frame['notes'],
            height=60,
            placeholder="其他想记录的信息...",
            key=f'notes_{idx}'
        )
        
        st.markdown("---")
        
        # 转变点标注
        st.markdown("**🔄 Motivation转变点**")
        is_transition = st.checkbox(
            "标记为转变点",
            value=current_frame['is_transition'],
            key=f'is_transition_{idx}'
        )
        
        transition_info = None
        if is_transition:
            with st.expander("📝 转变点详情", expanded=True):
                trigger_event = st.text_input(
                    "触发事件",
                    value=current_frame['transition_info']['trigger_event'] if current_frame['transition_info'] else "",
                    placeholder="例如：接到批评电话",
                    key=f'trigger_{idx}'
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    motivation_before = st.text_input(
                        "转变前Motivation",
                        value=current_frame['transition_info']['motivation_before'] if current_frame['transition_info'] else "",
                        key=f'mot_before_{idx}'
                    )
                    desire_before = st.text_input(
                        "转变前Desire",
                        value=current_frame['transition_info']['desire_before'] if current_frame['transition_info'] else "",
                        key=f'des_before_{idx}'
                    )
                
                with col2:
                    motivation_after = st.text_input(
                        "转变后Motivation",
                        value=current_frame['transition_info']['motivation_after'] if current_frame['transition_info'] else "",
                        key=f'mot_after_{idx}'
                    )
                    desire_after = st.text_input(
                        "转变后Desire",
                        value=current_frame['transition_info']['desire_after'] if current_frame['transition_info'] else "",
                        key=f'des_after_{idx}'
                    )
                
                transition_info = self.schema.create_transition_info(
                    trigger_event,
                    motivation_before,
                    motivation_after,
                    desire_before,
                    desire_after
                )
        
        # 保存按钮
        if st.button("✅ 保存当前帧", type="primary", use_container_width=True):
            # 更新数据
            current_frame['explicit_motivation'] = explicit_motivation
            current_frame['implicit_desire'] = implicit_desire
            current_frame['implicit_level'] = implicit_level
            current_frame['visual_cues'] = visual_cues
            current_frame['notes'] = notes
            current_frame['is_transition'] = is_transition
            current_frame['transition_info'] = transition_info
            
            st.session_state.annotation_changed = True
            st.success("✅ 当前帧已更新")
            
            # 自动保存
            self.save_current_annotation()
    
    def _render_timeline(self, keyframes: List[Dict]):
        """渲染时间轴"""
        st.subheader("📊 Motivation演变时间轴")
        
        # 创建时间轴可视化
        timeline_data = []
        for idx, kf in enumerate(keyframes):
            status = "✅" if kf['explicit_motivation'] else "⬜"
            transition_marker = "🔄" if kf['is_transition'] else ""
            
            timeline_data.append({
                "帧": idx + 1,
                "时间": kf['timestamp_formatted'],
                "状态": status,
                "转变": transition_marker,
                "显性Motivation": kf['explicit_motivation'][:30] + "..." if len(kf['explicit_motivation']) > 30 else kf['explicit_motivation'],
                "隐性Desire": kf['implicit_desire'][:30] + "..." if len(kf['implicit_desire']) > 30 else kf['implicit_desire']
            })
        
        # 显示表格
        st.dataframe(
            timeline_data,
            use_container_width=True,
            height=300
        )
        
        # 整体描述
        st.markdown("---")
        overall_trajectory = st.text_area(
            "🎯 整体Motivation演变描述",
            value=st.session_state.current_annotation['overall_trajectory'],
            height=100,
            placeholder="总结整个视频中人物的motivation/desire如何演变...",
            key='overall_trajectory'
        )
        
        if overall_trajectory != st.session_state.current_annotation['overall_trajectory']:
            st.session_state.current_annotation['overall_trajectory'] = overall_trajectory
            st.session_state.annotation_changed = True


# 全局编辑器实例
editor = AnnotationEditor()