# frontend/utils/helpers.py
"""辅助函数"""
from typing import Dict, Optional
from pathlib import Path


def format_timestamp(seconds: float) -> str:
    """格式化时间戳"""
    if seconds is None:
        return "00:00"
    try:
        seconds = float(seconds)
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    except (TypeError, ValueError):
        return "00:00"


def get_video_info(video_path: str) -> Optional[Dict]:
    """获取视频信息"""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0

        cap.release()

        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": duration
        }
    except Exception as e:
        return None


def get_desire_emoji(desire_type: str) -> str:
    """获取渴望类型对应的emoji"""
    emoji_map = {
        "physiological": "🍔",
        "safety": "🛡️",
        "belonging": "❤️",
        "esteem": "🏆",
        "self-actualization": "✨",
        "cognitive": "🧠",
        "aesthetic": "🎨"
    }
    return emoji_map.get(desire_type.lower(), "💭")


def truncate_text(text: str, max_length: int = 100) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def safe_get(data: Dict, *keys, default=None):
    """安全获取嵌套字典值"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, {})
        else:
            return default
    return data if data != {} else default
