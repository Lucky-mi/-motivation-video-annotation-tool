# backend/models.py
"""
数据模型定义 - 使用Pydantic进行数据验证
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class AnnotationStatus(str, Enum):
    """标注状态"""
    AI_GENERATED = "ai_generated"  # AI生成
    HUMAN_CONFIRMED = "human_confirmed"  # 人工确认
    HUMAN_MODIFIED = "human_modified"  # 人工修改
    HUMAN_CREATED = "human_created"  # 人工创建


class DesireCategory(str, Enum):
    """渴望类型（基于马斯洛需求层次）"""
    PHYSIOLOGICAL = "physiological"  # 生理需求
    SAFETY = "safety"  # 安全需求
    BELONGING = "belonging"  # 归属需求
    ESTEEM = "esteem"  # 尊重需求
    SELF_ACTUALIZATION = "self_actualization"  # 自我实现
    OTHER = "other"  # 其他


class MotivationType(str, Enum):
    """动机类型"""
    INTRINSIC = "intrinsic"  # 内在动机
    EXTRINSIC = "extrinsic"  # 外在动机
    MIXED = "mixed"  # 混合动机


class KeyframeAction(BaseModel):
    """关键帧动作（What - 客观描述）"""
    timestamp: float = Field(default=0.0, description="时间戳（秒）")
    timestamp_formatted: str = Field(default="00:00", description="格式化时间（HH:MM:SS）")
    action_description: str = Field(default="", description="动作描述")
    visual_context: str = Field(default="", description="视觉上下文")
    objects: List[str] = Field(default_factory=list, description="画面中的物体")
    characters: List[str] = Field(default_factory=list, description="画面中的角色")
    scene: str = Field(default="", description="场景描述")
    scene_description: Optional[str] = Field(default=None, description="场景描述（别名）")  # 兼容字段
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="AI置信度")

    class Config:
        # 允许额外字段，不会报错
        extra = "allow"


class MotivationAnnotation(BaseModel):
    """动机标注（Why - 深度分析）"""
    explicit_motivation: str = Field(default="", description="显性动机")
    implicit_desire: str = Field(default="", description="隐性渴望")
    desire_category: Optional[str] = Field(default="other", description="渴望类型")  # 改为字符串，更宽松
    desire_type: Optional[str] = Field(default=None, description="渴望类型（别名）")  # 兼容字段
    motivation_type: Optional[str] = Field(default="mixed", description="动机类型")  # 改为字符串
    implicit_level: int = Field(default=3, ge=1, le=5, description="隐性程度（1-5）")
    reasoning: str = Field(default="", description="AI推理依据")
    visual_cues: List[str] = Field(default_factory=list, description="视觉线索")
    status: AnnotationStatus = Field(default=AnnotationStatus.AI_GENERATED, description="标注状态")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="AI置信度")
    notes: str = Field(default="", description="备注")

    class Config:
        # 允许额外字段，不会报错
        extra = "allow"


class MotivationTransition(BaseModel):
    """动机转变"""
    from_timestamp: float = Field(default=0.0, description="转变起始时间")
    to_timestamp: float = Field(default=0.0, description="转变结束时间")
    trigger_event: str = Field(default="", description="触发事件")
    motivation_before: str = Field(default="", description="转变前动机")
    motivation_after: str = Field(default="", description="转变后动机")
    desire_before: str = Field(default="", description="转变前渴望")
    desire_after: str = Field(default="", description="转变后渴望")
    transition_type: str = Field(default="", description="转变类型")
    intensity: int = Field(default=3, ge=1, le=5, description="转变强度")

    class Config:
        extra = "allow"


class KeyframeAnnotation(BaseModel):
    """关键帧完整标注（What + Why）"""
    frame_id: int = Field(default=0, description="帧ID")
    frame_path: str = Field(default="", description="帧图片路径")
    action: Optional[KeyframeAction] = Field(default=None, description="动作信息（What）")
    motivation: Optional[MotivationAnnotation] = Field(default=None, description="动机信息（Why）")
    is_transition: bool = Field(default=False, description="是否为转变点")
    transition_info: Optional[MotivationTransition] = Field(default=None, description="转变详情")

    # 兼容字段 - 直接包含timestamp等
    timestamp_seconds: Optional[float] = Field(default=None, description="时间戳（兼容）")

    class Config:
        extra = "allow"

    def __init__(self, **data):
        # 如果没有action但有其他字段，自动创建action
        if 'action' not in data or data['action'] is None:
            action_data = {}
            for key in ['timestamp', 'timestamp_formatted', 'action_description', 'scene', 'scene_description']:
                if key in data:
                    action_data[key] = data[key]
            if action_data:
                data['action'] = KeyframeAction(**action_data)
            else:
                data['action'] = KeyframeAction()

        # 如果没有motivation但有其他字段，自动创建motivation
        if 'motivation' not in data or data['motivation'] is None:
            motivation_data = {}
            for key in ['explicit_motivation', 'implicit_desire', 'desire_category', 'desire_type']:
                if key in data:
                    motivation_data[key] = data[key]
            if motivation_data:
                data['motivation'] = MotivationAnnotation(**motivation_data)
            else:
                data['motivation'] = MotivationAnnotation()

        super().__init__(**data)


class VideoAnnotation(BaseModel):
    """视频完整标注"""
    video_id: str = Field(..., description="视频ID")
    video_name: str = Field(..., description="视频名称")
    video_path: str = Field(..., description="视频路径")
    duration: float = Field(default=0.0, description="视频时长（秒）")
    keyframes: List[KeyframeAnnotation] = Field(default_factory=list, description="关键帧列表")
    transitions: List[MotivationTransition] = Field(default_factory=list, description="转变点列表")
    overall_trajectory: str = Field(default="", description="整体动机演变轨迹")
    summary: str = Field(default="", description="总结")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    last_modified: str = Field(default_factory=lambda: datetime.now().isoformat(), description="最后修改时间")
    annotator: str = Field(default="", description="标注者")
    status: str = Field(default="in_progress", description="标注状态")
    total_frames: int = Field(default=0, description="总帧数")
    annotated_frames: int = Field(default=0, description="已标注帧数")
    ai_generated_frames: int = Field(default=0, description="AI生成帧数")
    human_confirmed_frames: int = Field(default=0, description="人工确认帧数")


# ============= API请求/响应模型 =============

class AIAnalysisRequest(BaseModel):
    """AI分析请求"""
    video_path: str = Field(..., description="视频路径")
    extraction_mode: str = Field(default="uniform", description="提取模式：uniform/smart")
    interval_seconds: float = Field(default=5.0, description="均匀采样间隔（秒）")
    max_frames: int = Field(default=50, description="最大帧数")
    analyze_actions: bool = Field(default=True, description="是否分析动作")
    analyze_emotions: bool = Field(default=True, description="是否分析情绪")
    analyze_objects: bool = Field(default=True, description="是否识别物体")
    suggest_motivations: bool = Field(default=True, description="是否推断动机")


class AIAnalysisResponse(BaseModel):
    """AI分析响应"""
    video_id: str = Field(..., description="视频ID")
    keyframes: List[KeyframeAnnotation] = Field(..., description="关键帧标注")
    suggested_transitions: List[MotivationTransition] = Field(default_factory=list, description="建议的转变点")
    overall_summary: str = Field(default="", description="整体总结")
    processing_time: float = Field(default=0.0, description="处理时间（秒）")
    model_used: str = Field(default="gemini-2.5-flash", description="使用的模型")


class AnnotationUpdateRequest(BaseModel):
    """标注更新请求"""
    frame_id: int = Field(..., description="帧ID")
    motivation: MotivationAnnotation = Field(..., description="更新的动机标注")
