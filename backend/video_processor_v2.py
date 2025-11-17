# backend/video_processor_v2.py
"""
增强版视频处理器：支持Gemini原生视频理解
"""
import cv2
from pathlib import Path
from typing import List, Dict, Optional
from datetime import timedelta
import json
import re

# Google Generative AI 导入（类型检查忽略）
try:
    import google.generativeai as genai  # type: ignore
except ImportError:
    genai = None  # 如果未安装，设为 None

class SmartVideoProcessor:
    """智能视频处理器：结合传统方法和VLM"""
    
    def __init__(self, output_dir: str = "data/keyframes", gemini_api_key: Optional[str] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 配置Gemini
        if gemini_api_key and genai is not None:
            genai.configure(api_key=gemini_api_key)  # type: ignore
            self.model = genai.GenerativeModel('gemini-1.5-flash')  # type: ignore
        else:
            self.model = None
    
    def get_video_info(self, video_path: str) -> dict:
        """获取视频基本信息"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        cap.release()
        
        return {
            "fps": fps,
            "frame_count": frame_count,
            "duration": duration,
            "duration_formatted": str(timedelta(seconds=int(duration))),
            "width": width,
            "height": height
        }
    
    def extract_uniform_frames(
        self, 
        video_path: str, 
        interval_seconds: float = 5.0,
        max_frames: int = 50
    ) -> List[Dict]:
        """均匀采样提取关键帧"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        video_name = Path(video_path).stem
        video_info = self.get_video_info(video_path)
        fps = video_info["fps"]
        duration = video_info["duration"]
        
        # 计算采样间隔
        interval_frames = int(fps * interval_seconds)
        
        # 调整间隔以不超过max_frames
        total_possible_frames = int(duration / interval_seconds)
        if total_possible_frames > max_frames:
            interval_seconds = duration / max_frames
            interval_frames = int(fps * interval_seconds)
        
        keyframes = []
        frame_id = 0
        saved_count = 0
        
        video_keyframes_dir = self.output_dir / video_name
        video_keyframes_dir.mkdir(exist_ok=True)
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            if frame_id % interval_frames == 0:
                timestamp = frame_id / fps
                
                frame_filename = f"frame_{saved_count:04d}_t{timestamp:.2f}s.jpg"
                frame_path = video_keyframes_dir / frame_filename
                cv2.imwrite(str(frame_path), frame)
                
                keyframes.append({
                    "frame_id": saved_count,
                    "timestamp": timestamp,
                    "timestamp_formatted": str(timedelta(seconds=int(timestamp))),
                    "frame_path": str(frame_path),
                    "auto_extracted": True
                })
                
                saved_count += 1
                
                if saved_count >= max_frames:
                    break
            
            frame_id += 1
        
        cap.release()
        
        print(f"✅ 提取完成：从 {video_name} 中提取了 {len(keyframes)} 帧")
        return keyframes
    
    def analyze_video_with_gemini(self, video_path: str) -> Dict:
        """使用Gemini分析视频"""
        if not self.model or genai is None:
            raise ValueError("未配置Gemini API key或未安装google-generativeai")

        print(f"📤 正在上传视频到Gemini: {Path(video_path).name}")
        video_file = genai.upload_file(path=video_path)  # type: ignore
        print(f"✅ 上传完成，URI: {video_file.uri}")
        
        prompt = """
        请仔细观看这个视频，分析人物的motivation/desire变化。
        
        请按以下JSON格式输出：
        {
            "key_moments": [
                {
                    "timestamp": "00:15",
                    "timestamp_seconds": 15,
                    "description": "人物表情从专注变为焦虑",
                    "motivation_before": "想要完成工作",
                    "motivation_after": "担心无法按时完成",
                    "trigger_event": "接到催促电话",
                    "implicit_level": 4
                }
            ],
            "overall_motivation_trajectory": "从自信完成任务 → 焦虑逃避 → 重新振作",
            "suggested_keyframe_timestamps": [5, 15, 30, 45]
        }
        
        注意：
        1. 重点关注**隐性motivation**，不只是表面行为
        2. 标注motivation转变的**触发事件**
        3. 建议5-10个关键时刻即可
        """
        
        response = self.model.generate_content([video_file, prompt])
        
        try:
            response_text = response.text
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text
            
            analysis = json.loads(json_str)
            return analysis
        
        except Exception as e:
            print(f"⚠️ 解析Gemini返回失败: {e}")
            return {"error": str(e), "raw_response": response.text}
    
    def extract_suggested_frames(
        self, 
        video_path: str, 
        timestamps: List[float]
    ) -> List[Dict]:
        """根据指定timestamp提取关键帧"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        video_name = Path(video_path).stem
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        video_keyframes_dir = self.output_dir / video_name
        video_keyframes_dir.mkdir(exist_ok=True)
        
        keyframes = []
        
        for idx, timestamp in enumerate(sorted(timestamps)):
            frame_number = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if not ret:
                print(f"⚠️ 无法读取 {timestamp}s 处的帧")
                continue
            
            frame_filename = f"frame_{idx:04d}_t{timestamp:.2f}s.jpg"
            frame_path = video_keyframes_dir / frame_filename
            cv2.imwrite(str(frame_path), frame)
            
            keyframes.append({
                "frame_id": idx,
                "timestamp": timestamp,
                "timestamp_formatted": str(timedelta(seconds=int(timestamp))),
                "frame_path": str(frame_path),
                "auto_extracted": True,
                "vlm_suggested": True
            })
        
        cap.release()
        print(f"✅ 提取了 {len(keyframes)} 个VLM建议的关键帧")
        return keyframes