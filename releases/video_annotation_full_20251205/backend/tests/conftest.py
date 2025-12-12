# backend/tests/conftest.py
"""
Pytest配置文件 - 定义共享的fixtures
"""
import pytest
import os
import sys
from pathlib import Path
import tempfile
import shutil
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.models import (
    VideoAnnotation, KeyframeAnnotation, KeyframeAction,
    MotivationAnnotation, AnnotationStatus
)
from backend.models_questions import Question, QuestionOption, QuestionSet


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # 清理
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_keyframe_action() -> KeyframeAction:
    """示例关键帧动作数据"""
    return KeyframeAction(
        timestamp=10.5,
        timestamp_formatted="00:10",
        action_description="角色打开冰箱",
        visual_context="深夜厨房，昏暗灯光",
        objects=["冰箱", "厨房", "灯"],
        characters=["主角"],
        scene="厨房",
        confidence=0.85
    )


@pytest.fixture
def sample_motivation_annotation() -> MotivationAnnotation:
    """示例动机标注数据"""
    return MotivationAnnotation(
        explicit_motivation="寻找食物",
        implicit_desire="逃避焦虑和孤独",
        desire_category="safety",
        motivation_type="intrinsic",
        implicit_level=4,
        reasoning="深夜独自在厨房，表情焦虑，这是典型的情绪化进食行为",
        visual_cues=["焦虑的表情", "深夜时间", "孤独的场景"],
        status=AnnotationStatus.AI_GENERATED,
        confidence=0.8
    )


@pytest.fixture
def sample_keyframe(sample_keyframe_action, sample_motivation_annotation) -> KeyframeAnnotation:
    """示例关键帧完整标注"""
    return KeyframeAnnotation(
        frame_id=0,
        frame_path="data/keyframes/test_video/frame_0000_t10.50s.jpg",
        action=sample_keyframe_action,
        motivation=sample_motivation_annotation
    )


@pytest.fixture
def sample_video_annotation(sample_keyframe) -> VideoAnnotation:
    """示例视频标注"""
    return VideoAnnotation(
        video_id="test_video_001",
        video_name="test_video.mp4",
        video_path="data/videos/test_video.mp4",
        duration=180.0,
        keyframes=[sample_keyframe],
        overall_trajectory="从焦虑到平静的情绪转变",
        summary="深夜情绪化进食行为研究",
        total_frames=1,
        annotated_frames=1,
        ai_generated_frames=1
    )


@pytest.fixture
def sample_question_options() -> list:
    """示例问题选项"""
    return [
        QuestionOption(
            option_id="A",
            text="逃避内心焦虑（安全需求）",
            is_correct=True,
            explanation="深夜独自在厨房，表情焦虑，这是典型的逃避行为"
        ),
        QuestionOption(
            option_id="B",
            text="口渴想喝水（生理需求）",
            is_correct=False,
            explanation="虽然打开冰箱可能是为了喝水，但从情绪线索看更像是逃避行为"
        ),
        QuestionOption(
            option_id="C",
            text="寻找宵夜（生理需求）",
            is_correct=False,
            explanation="表面看是寻找食物，但深层动机是情绪调节"
        ),
        QuestionOption(
            option_id="D",
            text="检查冰箱库存（认知需求）",
            is_correct=False,
            explanation="不符合深夜焦虑的情境"
        )
    ]


@pytest.fixture
def sample_question(sample_question_options) -> Question:
    """示例问题"""
    return Question(
        question_id="q_001",
        question_text="在时间戳00:10，人物打开冰箱的深层desire是什么？",
        options=sample_question_options,
        correct_option_id="A",
        related_frame_ids=[0],
        reasoning_process="基于深夜时间、焦虑表情和孤独场景的综合分析",
        question_meta={
            "difficulty": 4,
            "question_type": "desire_inference"
        }
    )


@pytest.fixture
def sample_question_set(sample_question) -> QuestionSet:
    """示例问题集"""
    return QuestionSet(
        question_set_id="qs_001",
        video_id="test_video_001",
        video_name="test_video.mp4",
        questions=[sample_question],
        total_questions=1,
        verified_questions=0,
        ai_provider="gemini"
    )


@pytest.fixture
def mock_gemini_response() -> Dict[str, Any]:
    """Mock Gemini API响应"""
    return {
        "key_moments": [
            {
                "timestamp_seconds": 10,
                "timestamp": "00:10",
                "action_description": "角色打开冰箱",
                "visual_context": "深夜厨房",
                "objects": ["冰箱"],
                "characters": ["主角"],
                "scene": "厨房",
                "explicit_motivation": "寻找食物",
                "implicit_desire": "逃避焦虑",
                "desire_category": "safety",
                "motivation_type": "intrinsic",
                "implicit_level": 4,
                "reasoning": "情绪化进食",
                "visual_cues": ["焦虑表情"],
                "confidence": 0.8
            }
        ],
        "suggested_keyframe_timestamps": [10],
        "overall_narrative": "情绪转变",
        "processing_time": 2.5
    }


@pytest.fixture
def mock_ai_provider():
    """Mock AI Provider"""
    class MockAIProvider:
        def __init__(self):
            self.model_name = "mock-model"

        def analyze_video_comprehensive(self, video_path, **kwargs):
            return {
                "key_moments": [],
                "suggested_keyframe_timestamps": [],
                "overall_narrative": "Mock analysis",
                "processing_time": 1.0
            }

        def generate_question(self, prompt: str) -> str:
            return '''```json
{
  "question_text": "Mock question?",
  "options": [
    {"option_id": "A", "text": "Option A", "is_correct": true, "explanation": "Correct"},
    {"option_id": "B", "text": "Option B", "is_correct": false, "explanation": "Wrong"},
    {"option_id": "C", "text": "Option C", "is_correct": false, "explanation": "Wrong"},
    {"option_id": "D", "text": "Option D", "is_correct": false, "explanation": "Wrong"}
  ],
  "correct_option_id": "A",
  "reasoning": "Mock reasoning"
}
```'''

        def test_connection(self) -> bool:
            return True

    return MockAIProvider()


@pytest.fixture
def api_key():
    """测试用的API Key"""
    return os.getenv('GEMINI_API_KEY', 'test_api_key')
