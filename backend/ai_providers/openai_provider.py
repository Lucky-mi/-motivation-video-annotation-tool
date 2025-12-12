# backend/ai_providers/openai_provider.py
"""
OpenAI GPT-4V Provider实现
"""
import json
import base64
import time
from typing import Dict, Optional
from pathlib import Path

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

from .base_provider import BaseAIProvider, AIProviderFactory
from .prompt_loader import PromptLoader


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT-4V Provider"""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("openai包未安装")
        
        if not api_key:
            raise ValueError("OpenAI API Key未提供")
        
        self.client = OpenAI(api_key=api_key)
        self.model_name = kwargs.get('model_name', 'gpt-4-vision-preview')
        self.prompt_loader = PromptLoader("backend/prompts/video_analysis_prompts.yaml")
    
    def analyze_video_comprehensive(
        self,
        video_path: str,
        analyze_actions: bool = True,
        analyze_motivations: bool = True,
        **kwargs
    ) -> Dict:
        """
        综合分析视频
        注意: GPT-4V不直接支持视频,需要先提取关键帧
        """
        print("ℹ️ GPT-4V不支持直接视频分析,将使用帧采样方法")
        
        # 1. 先提取均匀采样的帧
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        # 采样10-15帧
        num_samples = min(15, int(duration / 5))
        sample_interval = frame_count // num_samples
        
        sampled_frames = []
        for i in range(num_samples):
            frame_idx = i * sample_interval
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                timestamp = frame_idx / fps
                sampled_frames.append((timestamp, frame))
        
        cap.release()
        
        # 2. 分析每一帧
        print(f"📊 分析 {len(sampled_frames)} 个采样帧...")
        start_time = time.time()
        
        key_moments = []
        for timestamp, frame in sampled_frames:
            # 将frame转为base64
            _, buffer = cv2.imencode('.jpg', frame)
            base64_image = base64.b64encode(buffer).decode('utf-8')
            
            # 分析这一帧
            analysis = self._analyze_frame_base64(base64_image, timestamp)
            if not analysis.get('error'):
                key_moments.append(analysis)
        
        processing_time = time.time() - start_time
        
        # 3. 综合所有帧的分析
        suggested_timestamps = [m['timestamp_seconds'] for m in key_moments]
        
        return {
            "key_moments": key_moments,
            "overall_narrative": self._synthesize_narrative(key_moments),
            "suggested_keyframe_timestamps": suggested_timestamps,
            "processing_time": processing_time,
            "model_used": self.model_name
        }
    
    def analyze_single_frame(
        self,
        frame_path: str,
        timestamp: float,
        context: str = ""
    ) -> Dict:
        """分析单个关键帧"""
        
        # 读取图片并转为base64
        with open(frame_path, 'rb') as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        
        return self._analyze_frame_base64(base64_image, timestamp, context)
    
    def _analyze_frame_base64(
        self,
        base64_image: str,
        timestamp: float,
        context: str = ""
    ) -> Dict:
        """分析base64编码的图片"""
        
        prompt = self.prompt_loader.get_prompt("single_frame.template", timestamp=timestamp, context=context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content
            
            # 解析JSON
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                json_str = result_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = result_text
            
            data = json.loads(json_str)
            data['timestamp_seconds'] = timestamp
            return data
        
        except Exception as e:
            return {
                "error": str(e),
                "timestamp_seconds": timestamp
            }
    
    def _synthesize_narrative(self, key_moments: list) -> str:
        """综合多个时刻生成整体叙述"""
        if not key_moments:
            return ""
        
        summary_prompt = f"""
基于以下关键时刻的分析,总结整个视频的动机演变:

{json.dumps(key_moments, ensure_ascii=False, indent=2)}

请用一段话(50-100字)描述整体的motivation演变轨迹。
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # 使用文本模型即可
                messages=[
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        except:
            return "整体演变轨迹分析失败"
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ OpenAI连接测试失败: {e}")
            return False


# 注册Provider
AIProviderFactory.register_provider('openai', OpenAIProvider)