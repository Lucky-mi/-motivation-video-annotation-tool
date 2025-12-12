from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class QuestionOption(BaseModel):
    """单选题选项"""
    option_id: str = Field(..., description="选项ID (A/B/C/D)")
    text: str = Field(..., description="选项文本")
    is_correct: bool = Field(default=False, description="是否为正确答案")
    explanation: str = Field(default="", description="选项解释（为什么对/错）")


class Question(BaseModel):
    """单个问题（单选题）"""
    question_id: str = Field(..., description="问题ID")
    question_text: str = Field(..., description="问题文本")
    options: List[QuestionOption] = Field(..., description="选项列表（4个）")
    correct_option_id: str = Field(..., description="正确答案ID (A/B/C/D)")
    related_frame_ids: List[int] = Field(default_factory=list, description="关联的关键帧ID")
    reasoning_process: str = Field(default="", description="AI推理过程")
    
    # 灵活的元数据字段 - 便于后续扩展
    question_meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="问题元数据（可包含：question_type, difficulty, desire_labels等）"
    )
    
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    verified: bool = Field(default=False, description="是否已校验")
    verification_notes: str = Field(default="", description="校验备注")


class QuestionSet(BaseModel):
    """问题集"""
    question_set_id: str = Field(..., description="问题集ID")
    video_id: str = Field(..., description="关联的视频ID")
    video_name: str = Field(..., description="视频名称")
    questions: List[Question] = Field(default_factory=list, description="问题列表")
    total_questions: int = Field(default=0, description="总问题数")
    verified_questions: int = Field(default=0, description="已校验问题数")
    
    # 灵活的元数据 - 便于后续添加字段
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="问题集元数据"
    )
    
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    last_modified: str = Field(default_factory=lambda: datetime.now().isoformat(), description="最后修改时间")
    ai_provider: str = Field(default="gemini", description="使用的AI Provider")


class VerificationRecord(BaseModel):
    """校验记录"""
    record_id: str = Field(..., description="记录ID")
    question_id: str = Field(..., description="问题ID")
    verifier: str = Field(default="", description="校验者")
    action: str = Field(..., description="操作类型：approved/modified/rejected")
    modifications: Dict[str, Any] = Field(default_factory=dict, description="修改内容")
    notes: str = Field(default="", description="校验备注")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="校验时间")


class QuestionGenerationRequest(BaseModel):
    """问题生成请求"""
    video_id: str = Field(..., description="视频ID")
    num_questions: int = Field(default=10, ge=1, le=50, description="生成问题数量")
    provider: str = Field(default="gemini", description="AI Provider")
