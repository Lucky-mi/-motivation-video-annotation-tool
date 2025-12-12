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

    async def check_video_content(self, video_path: str, strict_mode: bool = True) -> Dict:
        """
        检查视频内容是否符合心智理论研究要求

        Args:
            video_path: 视频文件路径
            strict_mode: 严格模式（更高的筛选标准）

        Returns:
            包含审核结果的字典
        """
        if not self.analyzer.model:
            logger.warning("AI未配置，跳过筛选")
            return {"pass": True, "reason": "AI未配置，跳过筛选", "confidence": 0.0}

        logger.info(f"🛡️ AI正在审核视频内容: {Path(video_path).name} ...")

        # 构建专业的筛选 Prompt
        filter_prompt = self._build_filter_prompt(strict_mode)

        video_file = None  # 初始化用于 finally 块
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

            # 3. 生成审核结果（降低安全限制以处理争吵等场景）
            from google.generativeai.types import HarmCategory, HarmBlockThreshold

            response = self.analyzer.model.generate_content(
                [video_file, filter_prompt],
                generation_config={
                    "max_output_tokens": 2048,
                    "temperature": 0.1
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
            if not response.candidates or response.candidates[0].finish_reason != 1:
                # finish_reason: 1=STOP (正常), 2=SAFETY (安全过滤), 3=MAX_TOKENS
                finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                logger.warning(f"  ⚠️ AI响应异常: finish_reason={finish_reason}")

                if finish_reason == 2:
                    # 安全过滤触发，但这些视频（争吵等）对研究有价值
                    return {
                        "pass": True,  # 仍然通过，因为争吵场景对ToM研究重要
                        "reason": "视频内容触发安全过滤（可能包含冲突场景），但对心智理论研究有价值",
                        "confidence": 0.6,
                        "safety_filtered": True
                    }
                else:
                    return {
                        "pass": False,
                        "reason": f"AI响应异常: finish_reason={finish_reason}",
                        "confidence": 0.0
                    }

            # 6. 解析结果
            result = self._parse_filter_response(response.text)
            logger.info(f"  🎯 审核完成: {'✅ 通过' if result['pass'] else '❌ 不通过'} - {result['reason']}")

            return result

        except Exception as e:
            logger.error(f"⚠️ 筛选过程出错: {e}", exc_info=True)
            # 出错时默认不通过，避免低质量视频进入数据集
            return {
                "pass": False,
                "reason": f"筛选出错: {str(e)}",
                "confidence": 0.0,
                "error": str(e)
            }

    def _build_filter_prompt(self, strict_mode: bool) -> str:
        """
        构建专业的筛选提示词
        
        Args:
            strict_mode: 是否使用严格模式
        """
        if strict_mode:
            return self.prompt_loader.get_prompt("content_filter.strict")
        else:
            return self.prompt_loader.get_prompt("content_filter.standard")

    def _parse_filter_response(self, response_text: str) -> Dict:
        """
        解析AI返回的审核结果

        Args:
            response_text: AI响应文本

        Returns:
            标准化的审核结果字典
        """
        try:
            # 提取 JSON 块
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            # 清理可能的问题字符
            import re

            # 1. 移除 BOM 和其他隐藏字符
            json_str = json_str.encode('utf-8', errors='ignore').decode('utf-8')

            # 2. 移除可能的控制字符（保留换行和制表符）
            json_str = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)

            # 3. 尝试修复常见的 Markdown 格式问题
            # 移除可能残留的 markdown 标记
            json_str = re.sub(r'^```(json)?\s*', '', json_str)
            json_str = re.sub(r'\s*```$', '', json_str)

            # 尝试直接解析
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as json_err:
                # 如果失败，尝试使用 json_repair（如果可用）
                logger.warning(f"标准JSON解析失败，尝试修复: {json_err}")
                try:
                    import json_repair
                    result = json_repair.loads(json_str)
                    logger.info("✅ 使用 json_repair 成功修复JSON")
                except (ImportError, Exception) as repair_err:
                    logger.error(f"json_repair 也失败: {repair_err}")
                    # 打印详细的调试信息
                    logger.debug(f"JSON字符串前100字符: {repr(json_str[:100])}")
                    raise json_err  # 重新抛出原始错误

            # 确保必需字段存在
            standardized_result = {
                "pass": result.get("pass", False),
                "reason": result.get("reason", "未提供理由"),
                "category": result.get("category", "other"),
                "confidence": float(result.get("confidence", 0.5)),
                "人物数量": result.get("人物数量", "未知"),
                "互动类型": result.get("互动类型", "未知"),
                "情感强度": result.get("情感强度", "未知"),
                "分析价值": result.get("分析价值", "未知"),
                "关键场景描述": result.get("关键场景描述", "无")
            }

            return standardized_result

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"错误位置: line {e.lineno} column {e.colno}")
            logger.error(f"原始响应:\n{response_text}")

            # 显示问题区域
            if "```json" in response_text or "```" in response_text:
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                else:
                    json_str = response_text.split("```")[1].split("```")[0].strip()

                lines = json_str.split('\n')
                if e.lineno <= len(lines):
                    problem_line = lines[e.lineno - 1]
                    logger.error(f"问题行 ({e.lineno}): {problem_line}")
                    logger.error(f"问题位置: {' ' * (e.colno - 1)}^")

            return {
                "pass": False,
                "reason": "AI响应格式错误",
                "confidence": 0.0,
                "raw_response": response_text[:500],
                "error_detail": f"JSON解析失败: {e}"
            }
        except Exception as e:
            logger.error(f"解析响应时出错: {e}")
            return {
                "pass": False,
                "reason": f"解析错误: {str(e)}",
                "confidence": 0.0
            }

    def batch_check(self, video_paths: list, strict_mode: bool = True, max_workers: int = 5) -> Dict[str, Dict]:
        """
        批量检查多个视频 (并行加速版)
        Args:
            max_workers: 同时审核的视频数量 (建议 3-5，取决于你的网速和 API 配额)
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
                    result = loop.run_until_complete(self.check_video_content(path, strict_mode))
                    return path, result
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"❌ 审核异常 {Path(path).name}: {e}")
                return path, {"pass": False, "reason": f"异常: {str(e)}", "confidence": 0.0}

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