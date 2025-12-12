# backend package
"""
后端处理模块：视频处理和标注数据管理
"""

from .video_processor_v2 import SmartVideoProcessor
from .annotation_schema import AnnotationSchema

__all__ = ['SmartVideoProcessor', 'AnnotationSchema']
