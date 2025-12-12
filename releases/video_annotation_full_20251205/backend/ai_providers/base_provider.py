# backend/ai_providers/base_provider.py
"""
AI Provider抽象基类 - 支持多种VLM模型
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import timedelta


class BaseAIProvider(ABC):
    """AI Provider抽象基类"""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.model_name = kwargs.get('model_name', 'default')
        self.config = kwargs
    
    @abstractmethod
    def analyze_video_comprehensive(
        self,
        video_path: str,
        analyze_actions: bool = True,
        analyze_motivations: bool = True,
        **kwargs
    ) -> Dict:
        """
        综合分析视频
        
        Returns:
            {
                "key_moments": [...],
                "overall_narrative": "...",
                "suggested_keyframe_timestamps": [...],
                "processing_time": 0.0
            }
        """
        pass
    
    @abstractmethod
    def analyze_single_frame(
        self,
        frame_path: str,
        timestamp: float,
        context: str = ""
    ) -> Dict:
        """
        分析单个关键帧
        
        Returns:
            {
                "action_description": "...",
                "explicit_motivation": "...",
                "implicit_desire": "...",
                "desire_type": "..."
            }
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """测试API连接"""
        pass

    @abstractmethod
    def generate_question(self, prompt: str) -> str:
        """根据Prompt生成问题"""
        pass

    def extract_keyframes(
        self,
        video_path: str,
        timestamps: List[float],
        output_dir: Path
    ) -> List[Tuple[float, str]]:
        """
        从视频中提取指定时间戳的关键帧
        (通用方法,所有provider共享)
        """
        import cv2
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        video_name = Path(video_path).stem
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        keyframes_dir = output_dir / video_name
        keyframes_dir.mkdir(parents=True, exist_ok=True)
        
        extracted = []
        
        for idx, timestamp in enumerate(sorted(timestamps)):
            frame_number = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if not ret:
                print(f"⚠️ 无法读取 {timestamp}s 处的帧")
                continue
            
            frame_filename = f"frame_{idx:04d}_t{timestamp:.2f}s.jpg"
            frame_path = keyframes_dir / frame_filename
            cv2.imwrite(str(frame_path), frame)
            
            extracted.append((timestamp, str(frame_path)))
        
        cap.release()
        return extracted
    
    def get_provider_info(self) -> Dict:
        """获取Provider信息"""
        return {
            "provider": self.__class__.__name__,
            "model": self.model_name,
            "api_configured": bool(self.api_key)
        }


class AIProviderFactory:
    """AI Provider工厂类"""
    
    _providers = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class):
        """注册Provider"""
        cls._providers[name] = provider_class
    
    @classmethod
    def create_provider(cls, name: str, **kwargs) -> BaseAIProvider:
        """创建Provider实例"""
        if name not in cls._providers:
            raise ValueError(f"未知的Provider: {name}")
        
        provider_class = cls._providers[name]
        return provider_class(**kwargs)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """列出所有可用的Provider"""
        return list(cls._providers.keys())