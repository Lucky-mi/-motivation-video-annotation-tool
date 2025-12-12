import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import json

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from question_generator import QuestionGenerator, PromptLoader
from models import KeyframeAnnotation, KeyframeAction, VideoAnnotation
from models_questions import QuestionSet
from ai_providers.base_provider import BaseAIProvider

class MockAIProvider(BaseAIProvider):
    def analyze_video_comprehensive(self, *args, **kwargs):
        return {}
    
    def analyze_single_frame(self, *args, **kwargs):
        return {}
    
    def test_connection(self):
        return True
        
    def generate_question(self, prompt: str) -> str:
        # Return a mock JSON response
        return json.dumps({
            "question_text": "Test Question?",
            "options": [
                {"option_id": "A", "text": "Option A", "is_correct": True, "explanation": "Exp A"},
                {"option_id": "B", "text": "Option B", "is_correct": False, "explanation": "Exp B"},
                {"option_id": "C", "text": "Option C", "is_correct": False, "explanation": "Exp C"},
                {"option_id": "D", "text": "Option D", "is_correct": False, "explanation": "Exp D"}
            ],
            "correct_option_id": "A",
            "reasoning": "Test Reasoning"
        })

@pytest.fixture
def mock_annotation():
    action = KeyframeAction(
        timestamp=1.0,
        timestamp_formatted="00:00:01",
        action_description="Test Action",
        visual_context="Test Context"
    )
    keyframe = KeyframeAnnotation(
        frame_id=1,
        frame_path="test.jpg",
        action=action,
        motivation=MagicMock()
    )
    return VideoAnnotation(
        video_id="test_video",
        video_name="test.mp4",
        video_path="test.mp4",
        keyframes=[keyframe]
    )

def test_prompt_loader():
    loader = PromptLoader()
    assert loader.prompts is not None
    # Check if default prompts are loaded (assuming the yaml exists)
    # If running in isolation, we might need to mock the file or ensure it exists
    
def test_question_generator(mock_annotation):
    provider = MockAIProvider()
    generator = QuestionGenerator(provider)
    
    question_set = generator.generate_questions_for_video(
        "test_video",
        mock_annotation,
        num_questions=1
    )
    
    assert isinstance(question_set, QuestionSet)
    assert len(question_set.questions) == 1
    q = question_set.questions[0]
    assert q.question_text == "Test Question?"
    assert len(q.options) == 4
    assert q.correct_option_id == "A"
