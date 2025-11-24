# frontend/components/annotation_editor.py
"""标注编辑器组件"""
import streamlit as st
from typing import Dict, List


class AnnotationEditor:
    """标注编辑器组件"""

    @staticmethod
    def render_metadata_editor(metadata: Dict) -> Dict:
        """渲染元数据编辑器"""
        st.markdown("### 📝 视频元信息")

        col1, col2 = st.columns(2)

        with col1:
            video_title = st.text_input(
                "视频标题",
                value=metadata.get('video_title', ''),
                key="edit_title"
            )
            overall_theme = st.text_input(
                "整体主题",
                value=metadata.get('overall_theme', ''),
                key="edit_theme"
            )

        with col2:
            provider = st.selectbox(
                "AI模型",
                options=["gemini", "openai"],
                index=0 if metadata.get('model_used', '').startswith('gemini') else 1,
                key="edit_provider"
            )

        overall_narrative = st.text_area(
            "整体叙事",
            value=metadata.get('overall_narrative', ''),
            height=100,
            key="edit_narrative"
        )

        return {
            'video_title': video_title,
            'overall_theme': overall_theme,
            'overall_narrative': overall_narrative,
            'model_used': metadata.get('model_used', '')
        }

    @staticmethod
    def render_transitions_editor(transitions: List[Dict]) -> List[Dict]:
        """渲染转变编辑器"""
        st.markdown("### 🔄 动机转变")

        if not transitions:
            st.info("暂无动机转变记录")
            if st.button("➕ 添加转变"):
                return [{
                    'from_frame': 0,
                    'to_frame': 1,
                    'transition_description': '',
                    'trigger': ''
                }]
            return []

        edited_transitions = []

        for idx, trans in enumerate(transitions):
            with st.expander(f"转变 {idx + 1}: 帧 {trans.get('from_frame', 0)} → {trans.get('to_frame', 0)}", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    from_frame = st.number_input(
                        "起始帧",
                        value=trans.get('from_frame', 0),
                        min_value=0,
                        key=f"trans_from_{idx}"
                    )

                with col2:
                    to_frame = st.number_input(
                        "结束帧",
                        value=trans.get('to_frame', 0),
                        min_value=0,
                        key=f"trans_to_{idx}"
                    )

                description = st.text_area(
                    "转变描述",
                    value=trans.get('transition_description', ''),
                    key=f"trans_desc_{idx}"
                )

                trigger = st.text_input(
                    "触发因素",
                    value=trans.get('trigger', ''),
                    key=f"trans_trigger_{idx}"
                )

                edited_transitions.append({
                    'from_frame': from_frame,
                    'to_frame': to_frame,
                    'transition_description': description,
                    'trigger': trigger
                })

        # 添加新转变按钮
        if st.button("➕ 添加转变"):
            edited_transitions.append({
                'from_frame': len(transitions),
                'to_frame': len(transitions) + 1,
                'transition_description': '',
                'trigger': ''
            })

        return edited_transitions

    @staticmethod
    def render_save_controls(on_save_callback, on_cancel_callback=None):
        """渲染保存控件"""
        col1, col2, col3 = st.columns([1, 1, 3])

        with col1:
            if st.button("💾 保存修改", type="primary", width="stretch"):
                if on_save_callback:
                    on_save_callback()

        with col2:
            if on_cancel_callback and st.button("❌ 取消", width="stretch"):
                on_cancel_callback()
