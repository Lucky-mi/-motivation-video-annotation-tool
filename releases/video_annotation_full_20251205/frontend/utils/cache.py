# frontend/utils/cache.py
"""缓存管理模块 - 包含数据缓存和优化的图片缓存"""
import streamlit as st
from typing import Optional, Dict, List
from PIL import Image
import requests
from io import BytesIO
from pathlib import Path

# ==========================================
# 1. DataCache (补回丢失的类)
# ==========================================
class DataCache:
    """数据缓存管理"""

    @staticmethod
    @st.cache_data(ttl=300, show_spinner=False)
    def get_videos(_api_client) -> List[Dict]:
        """缓存视频列表"""
        # 注意：如果_api_client无法被hash，这里可能会报错
        # 建议在调用处直接传入 list 结果，或者确保 client 可 hash
        # 暂时保持原逻辑
        return _api_client.list_videos()

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def get_annotation(_api_client, video_id: str) -> Optional[Dict]:
        """缓存标注数据"""
        return _api_client.get_annotation(video_id)

    @staticmethod
    def clear_annotation_cache(video_id: str = None):
        """清除标注缓存"""
        if video_id:
            DataCache.get_annotation.clear()
        else:
            st.cache_data.clear()


# ==========================================
# 2. ImageCache (极速优化版)
# ==========================================
class ImageCache:
    """图片缓存 - 极速优化版 (自动压缩)"""

    @staticmethod
    @st.cache_resource(max_entries=500, show_spinner=False)
    def _load_and_resize_image(image_path: str, base_url: str, target_width: int = 800) -> Optional[Image.Image]:
        """加载并压缩图片"""
        img = None
        try:
            # 1. 优先尝试本地绝对路径/相对路径读取 (速度最快)
            candidates = [
                Path(image_path),
                Path(image_path).absolute(),
                Path("data") / Path(image_path).name, # 应对只传文件名的情况
                Path(".") / image_path
            ]
            
            for p in candidates:
                if p.exists() and p.is_file():
                    img = Image.open(p)
                    break
            
            # 2. 如果本地没找到，尝试 API 读取 (作为备选)
            if img is None:
                # 构建 URL
                if image_path.startswith("http"):
                    url = image_path
                else:
                    # 假设 image_path 类似 "data/keyframes/video1/frame_0.jpg"
                    parts = Path(image_path).parts
                    if len(parts) >= 2:
                        url_path = f"{parts[-2]}/{parts[-1]}"
                    else:
                        url_path = Path(image_path).name
                    url = f"{base_url}/keyframes/{url_path}"
                
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))

            # 3. 核心优化：调整图片尺寸 (Resize)
            if img:
                if img.width > target_width:
                    ratio = target_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((target_width, new_height), Image.Resampling.BILINEAR)
                return img
                
            return None

        except Exception:
            return None

    @staticmethod
    def get(image_path: str, base_url: str = "http://localhost:8000") -> Optional[Image.Image]:
        """获取图片接口"""
        if not image_path:
            return None
        return ImageCache._load_and_resize_image(image_path, base_url, target_width=800)

    @staticmethod
    def preload(
        keyframes: list, 
        current_idx: int, 
        window_size: int = 2,
        base_url: str = "http://localhost:8000"
    ):
        """预加载相邻帧"""
        start = max(0, current_idx - window_size)
        end = min(len(keyframes), current_idx + window_size + 1)
        
        for i in range(start, end):
            if i == current_idx: continue
            
            frame_path = keyframes[i].get('frame_path', '')
            if frame_path:
                ImageCache._load_and_resize_image(frame_path, base_url, target_width=800)

    @staticmethod
    def clear():
        ImageCache._load_and_resize_image.clear()