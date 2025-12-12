# backend/annotation_schema.py
"""
标注数据结构定义
"""
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import json

class AnnotationSchema:
    """标注数据结构"""
    
    @staticmethod
    def create_empty_annotation(video_path: str, keyframes: List[Dict]) -> Dict:
        """创建空白标注"""
        return {
            "video_info": {
                "video_path": video_path,
                "video_name": Path(video_path).name,
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "annotator": "",
                "status": "in_progress"  # in_progress, completed
            },
            "keyframes": [
                {
                    "frame_id": kf["frame_id"],
                    "timestamp": kf["timestamp"],
                    "timestamp_formatted": kf["timestamp_formatted"],
                    "frame_path": kf["frame_path"],
                    
                    # 核心标注字段
                    "explicit_motivation": "",  # 显性动机
                    "implicit_desire": "",      # 隐性渴望
                    "implicit_level": 3,        # 1-5，隐性程度
                    "visual_cues": [],          # 视觉线索列表
                    "notes": "",                # 备注
                    
                    # 是否为转变点
                    "is_transition": False,
                    "transition_info": None     # 如果是转变点，记录详细信息
                }
                for kf in keyframes
            ],
            "transitions": [],  # 所有转变点汇总
            "overall_trajectory": ""  # 整体motivation演变描述
        }
    
    @staticmethod
    def create_transition_info(
        trigger_event: str,
        motivation_before: str,
        motivation_after: str,
        desire_before: str,
        desire_after: str
    ) -> Dict:
        """创建转变点信息"""
        return {
            "trigger_event": trigger_event,
            "motivation_before": motivation_before,
            "motivation_after": motivation_after,
            "desire_before": desire_before,
            "desire_after": desire_after
        }
    
    @staticmethod
    def save_annotation(annotation: Dict, output_path: str):
        """保存标注到JSON"""
        annotation["video_info"]["last_modified"] = datetime.now().isoformat()
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(annotation, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_annotation(annotation_path: str) -> Optional[Dict]:
        """加载已有标注"""
        path = Path(annotation_path)
        if not path.exists():
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)