# backend/content_filter.py
"""
内容筛选器 - 使用AI判断视频是否符合心智理论研究要求
专注于识别包含社交互动、心理推理和情感动机的视频内容
"""
from .vlm_analyzer import VLMAnalyzer
from config.config import config
import json
import time
from pathlib import Path
from typing import Dict, Optional
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold  # <--- 新增这行
logger = logging.getLogger(__name__)


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

    def check_video_content(self, video_path: str, strict_mode: bool = True) -> Dict:
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

        try:
            import google.generativeai as genai

            # 1. 上传视频
            logger.info("  📤 上传视频到AI服务...")
            video_file = genai.upload_file(path=video_path)

            # 2. 等待处理
            max_wait = 120  # 最多等待2分钟
            wait_time = 0
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
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
            criteria_section = """
    ### 🛡️ 视觉纯净度要求 (关键):
    我们只需要**原始的、电影感**的画面。
    - ❌ **拒绝** 带有大量后期花字、特效字幕、表情包贴纸的视频（如综艺节目风格）。
    - ❌ **拒绝** 带有硬字幕（Hardcoded Subtitles）的视频，特别是字幕直接解释了人物心理或对话内容的。
    - ✅ **保留** 仅有少量必要水印或不影响画面主体的视频。
    
    如果视频画面看起来像是一个经过大量后期加工的解说视频或综艺，请直接【拒绝】。
### 核心筛选标准（严格模式）：

⚠️ **关键要求：心智理论必须通过【动作和交互】体现，而非仅通过对话或字幕！**

必须同时满足以下条件才能通过：

1. **真实人类的可观察行为** ⭐⭐⭐
   - 画面中必须有真人（非动画、游戏角色、AI生成人物、照片）
   - 人物面部清晰可见，能观察到表情变化
   - 人物占据画面主体，能清楚看到肢体语言和动作
   - ❌ 拒绝：仅有配音、字幕、静态图片、远景人物

2. **行为中体现的心智理论** ⭐⭐⭐ (核心!)
   必须通过以下可观察的行为展现：
   - **面部表情变化**：惊讶、愤怒、悲伤、恐惧、厌恶、喜悦等真实情绪
   - **肢体语言**：手势、姿态、身体距离、触碰、回避等
   - **眼神交流**：对视、回避、凝视、眼神互动
   - **行为反应**：对他人行为的即时反应（非预先编排）
   - **情境互动**：争吵、拥抱、推开、靠近、转身离开等

   ❌ **明确拒绝**：
   - 仅通过对话展现意图的视频（看不到行为）
   - 主要依靠字幕/旁白讲解的视频
   - 访谈类视频（纯坐着说话，无行为展现）
   - 新闻播报、演讲、讲课等静态场景
   - 科普讲解视频（即使内容是心理学）

3. **真实的社交互动场景** ⭐⭐
   - 有明确的社交情境（冲突、和解、欺骗、安慰、谈判等）
   - 能观察到意图、欲望、信念在行为中的体现
   - 有情感的真实流露（非表演式的夸张）
   - ✅ 好例子：争吵时的推搡、安慰时的拥抱、说谎时的回避眼神
   - ❌ 坏例子：坐着平静地讨论情感、讲述故事、理论讲解

4. **画面质量与完整性** ⭐
   - 画面清晰稳定，能看清人物表情和动作
   - 情节相对完整（有开始、发展，非碎片拼接）
   - 无大量无关内容（长广告、转场动画）

### 明确排除类型：
- **科普讲解类**：心理学讲座、理论讲解、教育视频（即使主题相关）
- **访谈对话类**：坐着聊天、播客、新闻采访（无行为展现）
- **技能展示类**：烹饪、化妆、手工（无情感互动）
- **游戏/动画**：游戏录屏、动画片、虚拟角色
- **静态内容**：幻灯片、文字、静态图片集
- **纯风景/动物**：无人类或人类仅为背景
- **纯搞笑/恶作剧**：无真实情感，纯为娱乐
"""
        else:
            criteria_section = """
### 核心筛选标准（标准模式）：

⚠️ **关键要求：优先通过【动作和行为】判断，对话/字幕为辅助**

满足以下大部分条件即可通过：

1. **真实人类的可观察行为** ⭐⭐
   - 有真实人类，面部或身体清晰可见
   - 能观察到一定的表情或肢体语言
   - ❌ 拒绝：纯静态图片、远景人物、动画角色

2. **行为或情感展现** ⭐⭐
   - 有明显的情感表达（表情、动作、语气）
   - 有人际互动行为（即使简单）
   - 单人场景需有明确的情绪变化或反应
   - ⚠️ 注意：坐着聊天的访谈需有情感波动，否则拒绝

3. **基本可分析性** ⭐
   - 有一定的情境背景
   - 画面质量可接受

### 明确排除类型：
- 科普讲解、教程、演讲（即使主题相关）
- 游戏录屏、动画、虚拟角色
- 纯风景、动物、静物（无人类）
- 纯技能展示（无情感交流）
- 幻灯片、文字内容
"""

        return f"""你是一位专业的心理学研究助理，负责为Theory of Mind（心智理论）研究筛选高质量视频数据。

{criteria_section}

### 输出格式（必须严格遵守JSON格式）：

```json
{{
  "pass": true/false,
  "reason": "简洁说明通过/不通过的核心理由，重点描述【观察到的行为】而非对话内容（50字内）",
  "category": "选择一个：conflict/emotional_reaction/social_interaction/relationship/conversation/drama/other",
  "confidence": 0.85,
  "人物数量": 2,
  "可观察行为": "描述看到的表情、动作、肢体语言等（非对话内容）",
  "互动类型": "眼神交流/肢体接触/推拉动作/表情反应/姿态变化/无明显互动",
  "情感强度": "高/中/低",
  "分析价值": "高/中/低",
  "关键场景描述": "用一句话描述最有价值的行为场景（非对话场景）"
}}
```

### 重要提示：
- 只输出JSON，不要任何其他文字
- ⚠️ **核心**：必须基于【可观察的行为】判断，而非对话或字幕
- 如果视频主要是对话/讲解，缺乏行为展现，应该【拒绝】
- 对于边缘案例，偏向保守（不通过）
- confidence表示你的判断信心（0.0-1.0）
- 优先考虑研究价值（能否观察到心智状态的行为表现）

现在请审核这个视频："""

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

            # 尝试直接解析
            result = json.loads(json_str)

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
            logger.error(f"JSON解析失败: {e}\n原始响应: {response_text}")
            return {
                "pass": False,
                "reason": "AI响应格式错误",
                "confidence": 0.0,
                "raw_response": response_text[:500]
            }
        except Exception as e:
            logger.error(f"解析响应时出错: {e}")
            return {
                "pass": False,
                "reason": f"解析错误: {str(e)}",
                "confidence": 0.0
            }

    def batch_check(self, video_paths: list, strict_mode: bool = True) -> Dict[str, Dict]:
        """
        批量检查多个视频

        Args:
            video_paths: 视频路径列表
            strict_mode: 是否使用严格模式

        Returns:
            {video_path: result} 的字典
        """
        results = {}
        total = len(video_paths)

        logger.info(f"🚀 开始批量审核 {total} 个视频...")

        for idx, video_path in enumerate(video_paths, 1):
            logger.info(f"[{idx}/{total}] 审核: {Path(video_path).name}")
            try:
                result = self.check_video_content(video_path, strict_mode)
                results[video_path] = result
            except Exception as e:
                logger.error(f"审核失败: {e}")
                results[video_path] = {
                    "pass": False,
                    "reason": f"审核异常: {str(e)}",
                    "confidence": 0.0
                }

        # 统计结果
        passed = sum(1 for r in results.values() if r.get("pass", False))
        logger.info(f"✅ 批量审核完成: {passed}/{total} 个视频通过审核")

        return results