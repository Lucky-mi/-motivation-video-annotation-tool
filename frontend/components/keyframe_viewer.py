# frontend/components/keyframe_viewer.py
"""关键帧查看器组件 - 修复Key冲突与路径问题"""
import streamlit as st
from typing import List, Dict, Optional
from pathlib import Path
from ..utils import ImageCache, format_timestamp, get_desire_emoji
import time

class KeyframeViewer:
    """关键帧查看器组件"""

    @staticmethod
    def render_frame_navigation(
        keyframes: List[Dict],
        current_idx: int,
        on_change_callback=None
    ) -> int:
        """渲染帧导航控件"""
        if not keyframes:
            st.warning("没有可用的关键帧")
            return 0

        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            if st.button("⬅️ 上一帧", disabled=(current_idx <= 0), key="prev_frame_btn"):
                current_idx = max(0, current_idx - 1)
                if on_change_callback: on_change_callback(current_idx)

        with col2:
            new_idx = st.slider(
                "关键帧位置",
                0,
                len(keyframes) - 1,
                current_idx,
                key=f"frame_slider_{id(keyframes)}"
            )
            if new_idx != current_idx:
                current_idx = new_idx
                if on_change_callback: on_change_callback(current_idx)

        with col3:
            if st.button("下一帧 ➡️", disabled=(current_idx >= len(keyframes) - 1), key="next_frame_btn"):
                current_idx = min(len(keyframes) - 1, current_idx + 1)
                if on_change_callback: on_change_callback(current_idx)

        # 显示当前帧信息
        frame = keyframes[current_idx]
        timestamp = 0.0
        # 兼容多种时间戳字段名
        if frame.get('timestamp_seconds') is not None:
            timestamp = float(frame['timestamp_seconds'])
        elif isinstance(frame.get('action'), dict):
            timestamp = frame['action'].get('timestamp', 0.0)
            
        st.caption(f"帧 {current_idx + 1}/{len(keyframes)} | 时间: {format_timestamp(timestamp)}")

        return current_idx

    @staticmethod
    def render_frame_image(frame: Dict, base_url: str = "http://localhost:8000"):
        """渲染关键帧图片"""
        frame_path = frame.get('frame_path', '')
        
        # === 尝试自动修复缺失的路径 ===
        if not frame_path and 'frame_id' in frame:
            # 尝试根据ID推断可能的路径（仅作为备用）
            # 注意：这需要知道video_id，但在组件里可能拿不到，所以这里主要做展示优化
            pass 
            
        if frame_path:
            img = ImageCache.get(frame_path, base_url)
            if img:
                st.image(img, use_container_width=True)
            else:
                # 显示更详细的错误信息以便调试
                st.warning(f"🖼️ 图片加载失败: {Path(frame_path).name}")
                st.caption(f"路径: {frame_path}")
        else:
            st.error("⚠️ 此帧缺少图片路径数据")
            st.code(str(frame)[:200], language="json") # 显示部分数据帮助调试

    @staticmethod
    def render_frame_annotation(frame: Dict, index: int, editable: bool = False) -> Optional[Dict]:
        """渲染关键帧标注信息
        Args:
            index: 使用列表索引作为Key，确保唯一性，解决文字不刷新问题
        """
        action = frame.get('action', {}) or {}
        motivation = frame.get('motivation', {}) or {}

        # What部分
        with st.expander("🎬 What - 客观描述", expanded=True):
            if editable:
                # === 修复：使用 index 作为 key，确保切换帧时输入框刷新 ===
                action_desc = st.text_area(
                    "动作描述",
                    value=action.get('action_description', ''),
                    key=f"action_desc_idx_{index}" 
                )
                scene = st.text_input(
                    "场景",
                    value=action.get('scene', action.get('scene_description', '')),
                    key=f"scene_idx_{index}"
                )
            else:
                st.markdown(f"**动作**: {action.get('action_description', 'N/A')}")
                st.markdown(f"**场景**: {action.get('scene', action.get('scene_description', 'N/A'))}")
                
                objects = action.get('objects', [])
                if objects:
                    st.markdown(f"**物体**: {', '.join(objects)}")

        # Why部分
        with st.expander("💭 Why - 动机分析", expanded=True):
            if editable:
                # === 修复：使用 index 作为 key ===
                explicit = st.text_area(
                    "显性动机",
                    value=motivation.get('explicit_motivation', ''),
                    key=f"explicit_idx_{index}"
                )
                implicit = st.text_area(
                    "隐性渴望",
                    value=motivation.get('implicit_desire', ''),
                    key=f"implicit_idx_{index}"
                )
            else:
                st.markdown(f"**显性动机**: {motivation.get('explicit_motivation', 'N/A')}")
                st.markdown(f"**隐性渴望**: {motivation.get('implicit_desire', 'N/A')}")

                desire_type = motivation.get('desire_category', motivation.get('desire_type', ''))
                if desire_type:
                    emoji = get_desire_emoji(desire_type)
                    st.markdown(f"**渴望类型**: {emoji} {desire_type}")

                reasoning = motivation.get('reasoning', '')
                if reasoning:
                    st.markdown("**🔍 AI推理依据**")
                    st.caption(reasoning)

        if editable:
            return {
                'action': {'action_description': action_desc, 'scene_description': scene},
                'motivation': {'explicit_motivation': explicit, 'implicit_desire': implicit}
            }
        return None

    @staticmethod
    def render_complete_viewer(
            keyframes: List[Dict],
            current_idx: int = 0,
            editable: bool = False,
            base_url: str = "http://localhost:8000"
        ) -> tuple[int, Optional[Dict]]:
            """渲染完整的关键帧查看器"""
            if not keyframes:
                st.warning("没有可用的关键帧")
                return 0, None

            current_idx = max(0, min(current_idx, len(keyframes) - 1))

            # 1. 渲染导航
            current_idx = KeyframeViewer.render_frame_navigation(keyframes, current_idx)

            # 2. 异步预加载 (静默执行)
            # 增加到 2 帧，因为图片变小了，多预加载一点可以保证连续点击不卡
            ImageCache.preload(keyframes, current_idx, window_size=2, base_url=base_url)

            # 3. 显示内容
            current_frame = keyframes[current_idx]
            col1, col2 = st.columns([1.2, 1]) # 调整比例，让图片稍微大一点点

            with col1:
                # 性能计时（调试用，如果你觉得还慢，可以看到具体慢在哪里）
                # t0 = time.time()
                KeyframeViewer.render_frame_image(current_frame, base_url)
                # st.caption(f"加载耗时: {(time.time()-t0)*1000:.1f}ms") 

            with col2:
                edited_data = KeyframeViewer.render_frame_annotation(current_frame, current_idx, editable)

            return current_idx, edited_data