# backend/content_filter.py
"""
内容筛选器 - 使用AI判断视频是否符合心智理论研究要求
专注于识别包含社交互动、心理推理和情感动机的视频内容
"""
from .vlm_analyzer import VLMAnalyzer
from .prompt_loader import PromptLoader
from config.config import config
import json
import time
from pathlib import Path
from typing import Dict, Optional
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold  # <--- 新增这行
logger = logging.getLogger(__name__)
import asyncio

class ContentFilter:
    """AI驱动的视频内容筛选器 - 专注于心智理论研究需求"""

    def __init__(self, model_name: Optional[str] = None):
        """
        初始化内容筛选器

        Args:
            model_name: 可选的模型名称（默认使用配置中的模型）
        """
        api_key = config.get_api_key('gemini')
        self.analyzer = VLMAnalyzer(api_key=api_key, model_name=model_name)
        self.prompt_loader = PromptLoader("backend/prompts/content_filter_prompts.yaml")

    async def check_video_content(self, video_path: str, strict_mode: bool = True, filter_mode: str = "auto") -> Dict:
        """
        Evaluate video content suitability for Theory of Mind research.
        
        Args:
            video_path: Path to the video file.
            strict_mode: Legacy parameter for backward compatibility.
            filter_mode: Selection of filter prompt ('standard', 'strict', 'physiological', 'auto').
                         'physiological' targets physiological needs and second-order desires.
        """
        if not self.analyzer.model:
            logger.warning("AI model not configured, skipping content filter.")
            return {"pass": True, "reason": "AI check skipped (no model)", "confidence": 0.0}

        logger.info(f"🛡️ AI Auditing ({filter_mode}): {Path(video_path).name} ...")

        # 1. Select the appropriate academic prompt
        filter_prompt = self._build_filter_prompt(strict_mode, filter_mode)

        video_file = None
        try:
            import google.generativeai as genai

            # 1. 上传视频 (添加重试机制)
            logger.info("  📤 上传视频到AI服务...")
            max_upload_retries = 3
            upload_success = False

            for retry in range(max_upload_retries):
                try:
                    video_file = genai.upload_file(path=video_path)
                    upload_success = True
                    break
                except Exception as upload_err:
                    if "10055" in str(upload_err) or "buffer space" in str(upload_err):
                        wait_time = (retry + 1) * 5  # 递增等待时间
                        logger.warning(f"  ⚠️ 端口耗尽,等待 {wait_time}s 后重试 ({retry+1}/{max_upload_retries})...")
                        time.sleep(wait_time)
                    else:
                        raise  # 其他错误直接抛出

            if not upload_success:
                raise Exception("视频上传失败: 端口资源耗尽")

            # 2. 等待处理
            max_wait = 120  # 最多等待2分钟
            wait_time = 0
            while video_file.state.name == "PROCESSING":
                await asyncio.sleep(2)
                wait_time += 2
                video_file = genai.get_file(video_file.name)

                if wait_time >= max_wait:
                    logger.error("  ⏱️ 视频处理超时")
                    return {"pass": False, "reason": "视频处理超时", "confidence": 0.0}

            if video_file.state.name != "ACTIVE":
                logger.error(f"  ❌ 视频处理失败: {video_file.state.name}")
                return {"pass": False, "reason": f"视频处理失败: {video_file.state.name}", "confidence": 0.0}

            logger.info("  ✅ 视频已就绪，开始AI审核...")

            # 3. Generate Content Review
            # We relax safety settings to allow for "conflict" or "distress" scenes which are valuable for research
            from google.generativeai.types import HarmCategory, HarmBlockThreshold

            response = self.analyzer.model.generate_content(
                [video_file, filter_prompt],
                generation_config={
                    "max_output_tokens": 2048,
                    "temperature": 0.0, # Zero temperature for deterministic evaluation
                    "response_mime_type": "application/json" # Enforce JSON mode if supported
                },
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )

            # 4. 清理云端文件
            try:
                genai.delete_file(video_file.name)
            except Exception as e:
                logger.warning(f"清理云端文件失败: {e}")

            # 5. 检查响应状态
            logger.info(f"  ✅ AI响应已返回")
            if not response.candidates or response.candidates[0].finish_reason != 1:
                # finish_reason: 1=STOP (正常), 2=SAFETY (安全过滤), 3=MAX_TOKENS
                finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                logger.warning(f"  ⚠️ AI响应异常: finish_reason={finish_reason}")

                if finish_reason == 2:
                    # 安全过滤触发
                    return {
                        "pass": True,
                        "reason": "视频内容触发安全过滤（可能包含冲突场景），但对研究有价值",
                        "confidence": 0.6,
                        "safety_filtered": True
                    }
                else:
                    return {
                        "pass": False,
                        "reason": f"AI响应异常: finish_reason={finish_reason}",
                        "confidence": 0.0
                    }

            # 6. 解析AI响应 (关键调试点)
            logger.info(f"  📝 [DEBUG] AI Response length: {len(response.text)} chars")
            logger.info(f"  📝 [DEBUG] First 200 chars: {repr(response.text[:200])}")

            try:
                result = self._parse_filter_response(response.text)
            except Exception as parse_err:
                # 解析失败时，打印完整的原始响应以便调试
                logger.error(f"  ❌ JSON解析失败!")
                logger.error(f"     异常类型: {type(parse_err).__name__}")
                logger.error(f"     异常消息: {parse_err}")
                logger.error(f"     Response length: {len(response.text)} chars")
                logger.error(f"     === 完整AI响应 ===")
                logger.error(response.text)
                logger.error(f"     === 响应结束 ===")
                # 返回解析错误标记，而不是抛出异常导致整个审核失败
                return {
                    "pass": False,
                    "reason": f"AI响应解析失败: {type(parse_err).__name__}",
                    "confidence": 0.0,
                    "parsing_error": True,
                    "raw_response": response.text[:500]  # 保存前500字符用于调试
                }

            status_icon = "✅" if result['pass'] else "❌"
            logger.info(f"  🎯 Audit Result: {status_icon} [{result.get('category', 'N/A')}] - {result['reason']}")

            return result

        except Exception as e:
            logger.error(f"⚠️ Filter Execution Error: {e}", exc_info=True)
            return {"pass": False, "reason": f"System Error: {str(e)}", "confidence": 0.0}

    def _build_filter_prompt(self, strict_mode: bool, filter_mode: str = "auto") -> str:
        """Selects the prompt template based on the research filter mode."""

        # Priority: explicit filter_mode > strict_mode flag
        if filter_mode in ["physiological", "physiological_desire"]:
            logger.debug(f"🧬 Using physiological_desire prompt mode")
            return self.prompt_loader.get_prompt("content_filter.physiological_desire")

        elif filter_mode == "strict" or (filter_mode == "auto" and strict_mode):
            logger.debug(f"🔒 Using strict prompt mode")
            return self.prompt_loader.get_prompt("content_filter.strict")

        else: # standard or auto+non-strict
            logger.debug(f"📋 Using standard prompt mode")
            return self.prompt_loader.get_prompt("content_filter.standard")
    def _parse_filter_response(self, response_text: str) -> Dict:
        """
        Parses AI response into a strict Academic English Schema.
        Unifies fields from 'Social' and 'Physiological' prompts into a superset.

        Args:
            response_text: The raw text response from the Gemini API.

        Returns:
            A dictionary containing standardized metadata with English keys.
        """
        try:
            # Handle edge case: Empty response
            if not response_text or not response_text.strip():
                raise ValueError("Empty response from AI")

            # 1. Extract JSON from response
            json_str = response_text.strip()

            # 如果响应以 { 或 [ 开头，说明是纯JSON（由于response_mime_type设置）
            if json_str.startswith('{') or json_str.startswith('['):
                logger.info(f"     ✓ Direct JSON detected")
                # 直接使用，不需要提取markdown
                pass
            # 如果有markdown代码块，提取出来
            elif "```json" in json_str:
                logger.info(f"     ✓ Extracting from ```json block")
                parts = json_str.split("```json", 1)
                if len(parts) > 1:
                    json_str = parts[1].split("```", 1)[0].strip()
                else:
                    raise ValueError("Malformed ```json block: missing closing ```")
            elif "```" in json_str:
                logger.info(f"     ✓ Extracting from ``` block")
                parts = json_str.split("```", 2)  # 最多分成3部分: before, content, after
                if len(parts) >= 2:
                    json_str = parts[1].strip()
                else:
                    raise ValueError("Malformed ``` block: unclosed")
            else:
                # 没有代码块标记，假设整个响应是JSON
                logger.info(f"     ✓ No markdown blocks, treating as raw JSON")

            # 确保提取后的内容不为空
            if not json_str:
                raise ValueError("Extracted JSON string is empty")

            logger.info(f"     ✓ Extracted {len(json_str)} chars, first 150: {json_str[:150]}")

            # 2. Advanced String Cleaning
            import re
            # Remove BOM and potential hidden control characters
            json_str = json_str.encode('utf-8', errors='ignore').decode('utf-8')
            # Remove control characters but keep newlines/tabs for readability if present
            json_str = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
            # Remove any trailing commas which are invalid in JSON but common in LLM output
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)

            # 3. Robust JSON Parsing
            try:
                raw_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Standard JSON parse failed: {e}")
                logger.warning(f"   Problematic JSON snippet: {json_str[:200]}")

                # Try json_repair as fallback
                try:
                    import json_repair
                    logger.info("   Attempting json_repair...")
                    raw_data = json_repair.loads(json_str)
                    logger.info("   ✅ json_repair succeeded!")
                except ImportError:
                    logger.error("   ❌ json_repair module not installed. Install with: pip install json-repair")
                    raise e
                except Exception as repair_err:
                    logger.error(f"   ❌ json_repair also failed: {repair_err}")
                    raise e

            # =========================================================
            # 🧬 Unified Research Data Schema (NeurIPS Compatible)
            # =========================================================
            
            # 4. Core Decision Fields (Always present)
            standardized_result = {
                "pass": raw_data.get("pass", False),
                "reason": raw_data.get("reason", "No justification provided"),
                "confidence": float(raw_data.get("confidence", 0.0)),
                "category": raw_data.get("category", "uncategorized"),
            }

            # 5. Behavioral Metrics (Common to both Social & Physiological)
            # We use .get() with defaults to ensure schema consistency across CSV/Pandas
            standardized_result.update({
                "character_count": raw_data.get("character_count", 0),
                "observable_behaviors": raw_data.get("observable_behaviors", "None recorded"),
                "affective_intensity": raw_data.get("affective_intensity", "low"),
                "research_value": raw_data.get("research_value", "low"),
                "key_scene_description": raw_data.get("key_scene_description", "N/A"),
            })

            # 6. Mode-Specific Fields Handling
            # Strategy: Create a Superset Schema (Union of keys)
            # If a field is missing (e.g., 'physiological_type' in a social video), fill with null/safe defaults.
            
            # --- Social Interaction Specifics ---
            if "interaction_type" in raw_data:
                standardized_result["interaction_type"] = raw_data["interaction_type"]
            else:
                # Fallback for Physiological videos where interaction might be 'environmental_reaction' or absent
                standardized_result["interaction_type"] = raw_data.get("interaction_type", "N/A")

            # --- Physiological / Second-Order Desire Specifics ---
            if "physiological_type" in raw_data:
                # Case: Video is explicitly flagged as physiological
                standardized_result["physiological_type"] = raw_data["physiological_type"]
                
                # Handle boolean logic for desire_conflict safely
                dc_val = raw_data.get("desire_conflict", False)
                if isinstance(dc_val, str):
                    dc_val = dc_val.lower() == "true"
                standardized_result["desire_conflict"] = dc_val
            else:
                # Case: Standard social video -> Fill with neutral values
                standardized_result["physiological_type"] = "none"
                standardized_result["desire_conflict"] = False

            return standardized_result

        except Exception as e:
            logger.error(f"❌ JSON Parsing Critical Failure: {type(e).__name__}: {e}")
            logger.error(f"   Raw Response (first 500 chars): {response_text[:500]}")

            # If response is very short, log it entirely for debugging
            if len(response_text) < 500:
                logger.error(f"   Full Response: {response_text}")

            # Return a safe failure object so the pipeline doesn't crash
            return {
                "pass": False,
                "reason": f"System Error: AI response parsing failed ({type(e).__name__})",
                "confidence": 0.0,
                "category": "error",
                "parsing_error": True
            }

    def batch_check(self, video_paths: list, strict_mode: bool = True, max_workers: int = 5,
                    filter_mode: str = "standard") -> Dict[str, Dict]:
        """
        批量检查多个视频 (并行加速版)
        Args:
            max_workers: 同时审核的视频数量 (建议 3-5，取决于你的网速和 API 配额)
            filter_mode: 筛选模式 ("standard" | "strict" | "physiological_desire")
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {}
        total = len(video_paths)
        logger.info(f"🚀 开始批量并发审核 {total} 个视频 (并发数: {max_workers})...")

        # 定义单个任务函数（修复：使用 asyncio 运行协程）
        def process_one(path):
            try:
                logger.info(f"➡️ 开始审核: {Path(path).name}")
                # 在新的事件循环中运行异步函数
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self.check_video_content(path, strict_mode, filter_mode)
                    )
                    return path, result
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"❌ [CRITICAL] 审核异常 {Path(path).name}")
                logger.error(f"   异常类型: {type(e).__name__}")
                logger.error(f"   异常消息: {e}")
                logger.error(f"   完整追踪:")
                import traceback
                traceback.print_exc()
                return path, {
                    "pass": False,
                    "reason": f"系统异常: {type(e).__name__}: {str(e)}",
                    "confidence": 0.0,
                    "parsing_error": True  # 标记为解析错误
                }

        # 使用线程池并发执行
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_video = {executor.submit(process_one, path): path for path in video_paths}

            # 获取结果
            for i, future in enumerate(as_completed(future_to_video), 1):
                path, result = future.result()
                results[path] = result
                status = "✅" if result.get('pass') else "❌"
                logger.info(f"[{i}/{total}] {status} 完成: {Path(path).name}")

        # 统计结果
        passed = sum(1 for r in results.values() if r.get("pass", False))
        logger.info(f"🏁 批量审核完成: {passed}/{total} 个视频通过审核")

        return results