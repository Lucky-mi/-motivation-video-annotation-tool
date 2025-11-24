import yaml
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import VideoAnnotation, KeyframeAnnotation
from .models_questions import Question, QuestionSet, QuestionOption
from .ai_providers.base_provider import BaseAIProvider

class PromptLoader:
    """Prompt模板加载器 - 支持热加载"""
    def __init__(self, config_path: str = "backend/prompts/question_prompts.yaml"):
        self.config_path = config_path
        self.prompts = {}
        self.load_prompts()

    def load_prompts(self):
        """加载prompt配置"""
        path = Path(self.config_path)
        if not path.exists():
            # Try relative path if absolute fails
            path = Path.cwd() / self.config_path
            
        if not path.exists():
            print(f"Warning: Prompt file not found at {path}")
            return

        with open(path, 'r', encoding='utf-8') as f:
            self.prompts = yaml.safe_load(f)

    def reload(self):
        """热加载 - 无需重启服务"""
        self.load_prompts()

    def get_prompt(self, prompt_key: str, **kwargs) -> str:
        """获取并格式化prompt"""
        prompt_config = self.prompts.get(prompt_key, {})
        if isinstance(prompt_config, dict):
            template = prompt_config.get("template", "")
        else:
            template = str(prompt_config)
            
        return template.format(**kwargs)

class QuestionGenerator:
    """问题生成器 - 完全解耦"""
    def __init__(self, ai_provider: BaseAIProvider, prompt_loader: PromptLoader = None):
        self.ai_provider = ai_provider
        self.prompt_loader = prompt_loader or PromptLoader()

    def generate_questions_for_video(
        self,
        video_id: str,
        annotation_data: VideoAnnotation,
        num_questions: int = 10
    ) -> QuestionSet:
        """为视频生成问题集"""
        questions = []
        
        # 从标注数据中选择关键帧
        selected_frames = self._select_frames_for_questions(
            annotation_data.keyframes,
            num_questions
        )
        
        for frame in selected_frames:
            try:
                # 生成"desire是什么"类型的问题
                question = self._generate_desire_inference_question(frame)
                if question:
                    questions.append(question)
            except Exception as e:
                print(f"Error generating question for frame {frame.frame_id}: {e}")
                continue

        return QuestionSet(
            question_set_id=str(uuid.uuid4()),
            video_id=video_id,
            video_name=annotation_data.video_name,
            questions=questions,
            total_questions=len(questions),
            verified_questions=0,
            created_at=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            ai_provider=self.ai_provider.model_name
        )

    def _generate_desire_inference_question(
        self,
        keyframe: KeyframeAnnotation
    ) -> Optional[Question]:
        """生成desire推理问题"""
        # 从prompt配置加载模板
        prompt = self.prompt_loader.get_prompt(
            "desire_inference",
            action_description=keyframe.action.action_description,
            visual_context=keyframe.action.visual_context,
            timestamp=keyframe.action.timestamp_formatted
        )
        
        # 调用AI生成问题和选项
        response_text = self.ai_provider.generate_question(prompt)
        
        # 解析响应
        try:
            # Handle potential markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text
                
            question_data = json.loads(json_str)
            
            return Question(
                question_id=str(uuid.uuid4()),
                question_text=question_data['question_text'],
                options=[
                    QuestionOption(**opt) for opt in question_data['options']
                ],
                correct_option_id=question_data['correct_option_id'],
                related_frame_ids=[keyframe.frame_id],
                reasoning_process=question_data.get('reasoning', ''),
                created_at=datetime.now().isoformat()
            )
        except Exception as e:
            print(f"Failed to parse AI response: {e}")
            print(f"Response was: {response_text}")
            return None

    def _select_frames_for_questions(
        self,
        keyframes: List[KeyframeAnnotation],
        num_questions: int
    ) -> List[KeyframeAnnotation]:
        """选择用于生成问题的关键帧"""
        # 简单策略：均匀采样，但优先选择有丰富标注的帧
        if not keyframes:
            return []
            
        # 过滤掉没有动作描述或视觉上下文的帧
        valid_frames = [
            k for k in keyframes 
            if k.action.action_description and k.action.visual_context
        ]
        
        if not valid_frames:
            valid_frames = keyframes

        if len(valid_frames) <= num_questions:
            return valid_frames
            
        # 均匀采样
        step = len(valid_frames) / num_questions
        selected = []
        for i in range(num_questions):
            idx = int(i * step)
            selected.append(valid_frames[idx])
            
        return selected
