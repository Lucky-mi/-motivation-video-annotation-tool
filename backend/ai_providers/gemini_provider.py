# backend/ai_providers/gemini_provider.py
"""
Google Gemini Provider实现
"""
import json
import time
from typing import Dict, Optional
from pathlib import Path

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

from .base_provider import BaseAIProvider, AIProviderFactory
from .prompt_loader import PromptLoader


class GeminiProvider(BaseAIProvider):
    """Google Gemini Provider"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)

        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai包未安装")

        if not api_key:
            raise ValueError("Gemini API Key未提供")

        genai.configure(api_key=api_key)
        self.model_name = kwargs.get('model_name', 'gemini-2.0-flash-exp')
        self.model = genai.GenerativeModel(self.model_name)
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
        Gemini支持直接视频分析
        """
        print(f"📹 使用Gemini {self.model_name}分析视频...")

        # 1. 上传视频文件
        video_file = genai.upload_file(path=video_path)
        print(f"✅ 视频已上传: {video_file.name}")

        # 等待处理完成
        import time
        while video_file.state.name == "PROCESSING":
            print("⏳ 等待视频处理...")
            time.sleep(2)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise ValueError(f"视频处理失败: {video_file.state.name}")

        # 2. 生成分析提示词
        # 2. 生成分析提示词
        prompt = self.prompt_loader.get_prompt("comprehensive_video")

        # 3. 调用Gemini API
        start_time = time.time()

        try:
            response = self.model.generate_content(
                [video_file, prompt],
                request_options={"timeout": 600}
            )

            processing_time = time.time() - start_time

            # 4. 解析结果
            result_text = response.text

            # 尝试提取JSON
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                json_str = result_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = result_text

            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                # 如果解析失败，返回原始文本
                data = {
                    "raw_response": result_text,
                    "key_moments": [],
                    "overall_narrative": result_text[:500]
                }

            # 确保包含必要字段
            if "key_moments" not in data:
                data["key_moments"] = []

            if "suggested_keyframe_timestamps" not in data:
                # 从key_moments提取时间戳
                data["suggested_keyframe_timestamps"] = [
                    m.get("timestamp_seconds", 0)
                    for m in data["key_moments"]
                ]

            data["processing_time"] = processing_time
            data["model_used"] = self.model_name

            return data

        except Exception as e:
            return {
                "error": str(e),
                "key_moments": [],
                "suggested_keyframe_timestamps": [],
                "processing_time": time.time() - start_time
            }

        finally:
            # 清理上传的文件
            try:
                genai.delete_file(video_file.name)
                print(f"🗑️ 已删除临时文件: {video_file.name}")
            except:
                pass

    def analyze_single_frame(
        self,
        frame_path: str,
        timestamp: float,
        context: str = ""
    ) -> Dict:
        """分析单个关键帧"""

        # 上传图片
        image_file = genai.upload_file(path=frame_path)

        # 生成提示词
        # 生成提示词
        prompt = self.prompt_loader.get_prompt("single_frame.template", timestamp=timestamp, context=context)

        try:
            response = self.model.generate_content([image_file, prompt])
            result_text = response.text

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

        finally:
            # 清理上传的文件
            try:
                genai.delete_file(image_file.name)
            except:
                pass

    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content("Hello")
            return bool(response.text)
        except Exception as e:
            print(f"❌ Gemini连接测试失败: {e}")
            return False

    def generate_question(self, prompt: str) -> str:
        """根据Prompt生成问题"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ 生成问题失败: {e}")
            raise e


# 注册Provider
AIProviderFactory.register_provider('gemini', GeminiProvider)
