# backend/tests/test_models.py
"""
数据模型单元测试
测试所有Pydantic模型的验证逻辑
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from backend.models import (
    KeyframeAction, MotivationAnnotation, KeyframeAnnotation,
    VideoAnnotation, MotivationTransition, AnnotationStatus,
    DesireCategory, MotivationType
)
from backend.models_questions import (
    QuestionOption, Question, QuestionSet, VerificationRecord
)


class TestKeyframeAction:
    """测试关键帧动作模型"""

    def test_create_valid_action(self, sample_keyframe_action):
        """测试创建有效的动作"""
        assert sample_keyframe_action.timestamp == 10.5
        assert sample_keyframe_action.action_description == "角色打开冰箱"
        assert "冰箱" in sample_keyframe_action.objects
        assert sample_keyframe_action.confidence == 0.85

    def test_timestamp_required(self):
        """测试timestamp是必填字段"""
        with pytest.raises(ValidationError):
            KeyframeAction(timestamp_formatted="00:10")

    def test_confidence_range(self):
        """测试置信度范围验证"""
        # 有效范围
        action = KeyframeAction(timestamp=10.0, timestamp_formatted="00:10", confidence=0.5)
        assert action.confidence == 0.5

        # 超出范围应该失败
        with pytest.raises(ValidationError):
            KeyframeAction(timestamp=10.0, timestamp_formatted="00:10", confidence=1.5)

        with pytest.raises(ValidationError):
            KeyframeAction(timestamp=10.0, timestamp_formatted="00:10", confidence=-0.1)


class TestMotivationAnnotation:
    """测试动机标注模型"""

    def test_create_valid_motivation(self, sample_motivation_annotation):
        """测试创建有效的动机标注"""
        assert sample_motivation_annotation.explicit_motivation == "寻找食物"
        assert sample_motivation_annotation.implicit_desire == "逃避焦虑和孤独"
        assert sample_motivation_annotation.desire_category == DesireCategory.SAFETY
        assert sample_motivation_annotation.implicit_level == 4

    def test_desire_category_enum(self):
        """测试desire类别枚举"""
        # 有效的枚举值
        motivation = MotivationAnnotation(desire_category="safety")
        assert motivation.desire_category == DesireCategory.SAFETY

        # 无效的枚举值应该失败
        with pytest.raises(ValidationError):
            MotivationAnnotation(desire_category="invalid_category")

    def test_implicit_level_range(self):
        """测试隐性程度范围"""
        # 有效范围 1-5
        motivation = MotivationAnnotation(implicit_level=3)
        assert motivation.implicit_level == 3

        # 超出范围
        with pytest.raises(ValidationError):
            MotivationAnnotation(implicit_level=6)

        with pytest.raises(ValidationError):
            MotivationAnnotation(implicit_level=0)

    def test_default_status(self):
        """测试默认状态"""
        motivation = MotivationAnnotation()
        assert motivation.status == AnnotationStatus.AI_GENERATED


class TestKeyframeAnnotation:
    """测试关键帧完整标注模型"""

    def test_create_valid_keyframe(self, sample_keyframe):
        """测试创建有效的关键帧"""
        assert sample_keyframe.frame_id == 0
        assert sample_keyframe.action.timestamp == 10.5
        assert sample_keyframe.motivation.implicit_desire == "逃避焦虑和孤独"

    def test_nested_models(self, sample_keyframe_action, sample_motivation_annotation):
        """测试嵌套模型"""
        keyframe = KeyframeAnnotation(
            frame_id=1,
            frame_path="test.jpg",
            action=sample_keyframe_action,
            motivation=sample_motivation_annotation
        )

        assert isinstance(keyframe.action, KeyframeAction)
        assert isinstance(keyframe.motivation, MotivationAnnotation)

    def test_transition_optional(self):
        """测试转变信息是可选的"""
        keyframe = KeyframeAnnotation(
            frame_id=0,
            frame_path="test.jpg",
            action=KeyframeAction(timestamp=10.0, timestamp_formatted="00:10"),
            motivation=MotivationAnnotation()
        )

        assert keyframe.is_transition == False
        assert keyframe.transition_info is None


class TestVideoAnnotation:
    """测试视频标注模型"""

    def test_create_valid_annotation(self, sample_video_annotation):
        """测试创建有效的视频标注"""
        assert sample_video_annotation.video_id == "test_video_001"
        assert sample_video_annotation.duration == 180.0
        assert len(sample_video_annotation.keyframes) == 1
        assert sample_video_annotation.total_frames == 1

    def test_timestamp_auto_generation(self):
        """测试时间戳自动生成"""
        annotation = VideoAnnotation(
            video_id="test",
            video_name="test.mp4",
            video_path="test.mp4"
        )

        # 应该自动生成created_at和last_modified
        assert annotation.created_at is not None
        assert annotation.last_modified is not None

        # 验证时间戳格式
        datetime.fromisoformat(annotation.created_at)
        datetime.fromisoformat(annotation.last_modified)

    def test_default_values(self):
        """测试默认值"""
        annotation = VideoAnnotation(
            video_id="test",
            video_name="test.mp4",
            video_path="test.mp4"
        )

        assert annotation.keyframes == []
        assert annotation.transitions == []
        assert annotation.total_frames == 0
        assert annotation.status == "in_progress"


class TestQuestionModels:
    """测试问题相关模型"""

    def test_question_option(self, sample_question_options):
        """测试问题选项"""
        option = sample_question_options[0]

        assert option.option_id == "A"
        assert option.is_correct == True
        assert option.explanation != ""

    def test_question_creation(self, sample_question):
        """测试问题创建"""
        assert sample_question.question_id == "q_001"
        assert len(sample_question.options) == 4
        assert sample_question.correct_option_id == "A"
        assert sample_question.verified == False

    def test_question_meta_flexibility(self):
        """测试问题元数据的灵活性"""
        question = Question(
            question_id="q_test",
            question_text="Test?",
            options=[
                QuestionOption(option_id="A", text="A", is_correct=True),
                QuestionOption(option_id="B", text="B")
            ],
            correct_option_id="A",
            question_meta={
                "custom_field": "custom_value",
                "difficulty": 5,
                "tags": ["emotion", "desire"]
            }
        )

        assert question.question_meta["custom_field"] == "custom_value"
        assert "tags" in question.question_meta

    def test_question_set(self, sample_question_set):
        """测试问题集"""
        assert sample_question_set.video_id == "test_video_001"
        assert sample_question_set.total_questions == 1
        assert len(sample_question_set.questions) == 1
        assert sample_question_set.verified_questions == 0

    def test_verification_record(self):
        """测试校验记录"""
        record = VerificationRecord(
            record_id="r_001",
            question_id="q_001",
            verifier="test_user",
            action="approved",
            modifications={},
            notes="Looks good"
        )

        assert record.action == "approved"
        assert record.verifier == "test_user"

        # 验证timestamp自动生成
        assert record.timestamp is not None
        datetime.fromisoformat(record.timestamp)


class TestMotivationTransition:
    """测试动机转变模型"""

    def test_create_transition(self):
        """测试创建转变"""
        transition = MotivationTransition(
            from_timestamp=10.0,
            to_timestamp=20.0,
            trigger_event="角色接到电话",
            motivation_before="逃避焦虑",
            motivation_after="寻求帮助",
            desire_before="安全需求",
            desire_after="归属需求",
            intensity=4
        )

        assert transition.from_timestamp == 10.0
        assert transition.to_timestamp == 20.0
        assert transition.intensity == 4

    def test_intensity_range(self):
        """测试强度范围"""
        # 有效范围
        transition = MotivationTransition(
            from_timestamp=0,
            to_timestamp=10,
            trigger_event="test",
            motivation_before="A",
            motivation_after="B",
            intensity=3
        )
        assert transition.intensity == 3

        # 超出范围
        with pytest.raises(ValidationError):
            MotivationTransition(
                from_timestamp=0,
                to_timestamp=10,
                trigger_event="test",
                motivation_before="A",
                motivation_after="B",
                intensity=6
            )


class TestEnums:
    """测试枚举类型"""

    def test_annotation_status_enum(self):
        """测试标注状态枚举"""
        assert AnnotationStatus.AI_GENERATED == "ai_generated"
        assert AnnotationStatus.HUMAN_CONFIRMED == "human_confirmed"
        assert AnnotationStatus.HUMAN_MODIFIED == "human_modified"
        assert AnnotationStatus.HUMAN_CREATED == "human_created"

    def test_desire_category_enum(self):
        """测试渴望类别枚举"""
        assert DesireCategory.PHYSIOLOGICAL == "physiological"
        assert DesireCategory.SAFETY == "safety"
        assert DesireCategory.BELONGING == "belonging"
        assert DesireCategory.ESTEEM == "esteem"
        assert DesireCategory.SELF_ACTUALIZATION == "self_actualization"

    def test_motivation_type_enum(self):
        """测试动机类型枚举"""
        assert MotivationType.INTRINSIC == "intrinsic"
        assert MotivationType.EXTRINSIC == "extrinsic"
        assert MotivationType.MIXED == "mixed"
