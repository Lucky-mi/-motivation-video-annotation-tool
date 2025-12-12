# frontend/components/video_player.py
"""视频播放器组件"""
import streamlit as st
from pathlib import Path


class VideoPlayer:
    """视频播放器组件"""

    @staticmethod
    def render(video_path: str, width: int = 700):
        """渲染视频播放器"""
        if Path(video_path).exists():
            with open(video_path, 'rb') as f:
                video_bytes = f.read()
            st.video(video_bytes)
        else:
            st.warning("视频文件不存在")

    @staticmethod
    def render_with_info(video_path: str, video_info: dict = None):
        """渲染带信息的视频播放器"""
        col1, col2 = st.columns([2, 1])

        with col1:
            VideoPlayer.render(video_path)

        with col2:
            if video_info:
                st.markdown("**📊 视频信息**")
                st.write(f"时长: {video_info.get('duration', 0):.1f}秒")
                st.write(f"分辨率: {video_info.get('width')}x{video_info.get('height')}")
                st.write(f"帧率: {video_info.get('fps', 0):.1f} FPS")
                st.write(f"总帧数: {video_info.get('frame_count', 0)}")
