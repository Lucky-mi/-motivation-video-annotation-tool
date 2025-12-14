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
            placeholder = st.empty()
            
            # 2. 强制清空容器（这步至关重要，它会把旧的播放器彻底删掉！）
            # 这样浏览器就不会记住“5:30”这个进度了
            placeholder.empty()
            
            # 3. 在干净的容器里放入新视频
            # 注意：这里不要加 key 参数，因为 st.video 不支持
            placeholder.video(video_bytes)
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
