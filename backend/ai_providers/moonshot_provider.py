# backend/ai_providers/moonshot_provider.py
"""
Moonshot (Kimi) Provider实现
支持 Kimi K2.5 视觉模型，兼容 OpenAI SDK。
"""
import json
import base64
import time
from pathlib import Path
from typing import Dict, Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

from .base_provider import BaseAIProvider, AIProviderFactory
from backend.prompt_loader import PromptLoader

# 交叉审核时发给 Moonshot 的最大帧数（控制 token 成本）
_MAX_REVIEW_FRAMES = 10

# 交叉审核 prompt（直接定义在代码中，避免 YAML 大括号转义问题）
_REVIEW_PROMPT = """你是一位专业的视频动机分析专家，正在审核另一个 AI 对视频的标注结果。

上方已提供：
1. 主标注 JSON（含所有关键时刻的显性动机、隐性渴望、推理等字段）
2. 对应的视频关键帧图像

## 审核任务

请对主标注中的每一条 key_moment（moment_index 从 0 开始）逐一评估以下字段：
- explicit_motivation（显性动机）：是否准确描述了人物表面行为动机？
- implicit_desire（隐性渴望）：深层心理解读是否合理？是否有更好的解读？
- desire_category：physiological/safety/belonging/esteem/self_actualization/other，分类是否正确？
- implicit_level（1-5）：隐性程度打分是否恰当？
- reasoning：推理依据是否有视觉证据支持？

同时注意：视频中是否存在主标注遗漏的重要时刻？

## 输出格式

严格只输出以下 JSON，不要包含任何其他文字或代码块标记：

{
  "review_summary": "整体评价（1-2句话）",
  "reviewed_moments": [
    {
      "moment_index": 0,
      "timestamp_seconds": 15,
      "agreement_score": 0.85,
      "field_reviews": {
        "explicit_motivation": {"agree": true, "correction": null},
        "implicit_desire": {"agree": false, "correction": "修正后的隐性渴望描述"},
        "desire_category": {"agree": true, "correction": null},
        "implicit_level": {"agree": false, "correction": 3},
        "reasoning": {"agree": true, "correction": null}
      },
      "overall_flag": "minor_correction",
      "reviewer_comment": "简短说明不同意的理由"
    }
  ],
  "missing_moments": [
    {
      "timestamp_seconds": 45,
      "action_description": "遗漏的动作描述",
      "explicit_motivation": "显性动机",
      "implicit_desire": "隐性渴望",
      "desire_category": "belonging",
      "implicit_level": 3,
      "reasoning": "推理依据",
      "visual_cues": ["视觉线索1", "视觉线索2"]
    }
  ]
}

overall_flag 取值规则：
- "confirmed"：agreement_score >= 0.8，基本同意
- "minor_correction"：0.5 <= agreement_score < 0.8，有小问题
- "major_disagreement"：agreement_score < 0.5，严重分歧

开始审核："""


class MoonshotProvider(BaseAIProvider):
    """Moonshot (Kimi) Provider，支持图像/视频输入"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)

        if not OPENAI_AVAILABLE:
            raise ImportError("openai 包未安装，Moonshot API 依赖 openai 包")

        if not api_key:
            raise ValueError("Moonshot API Key 未提供")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1",
        )
        # 优先使用 kwargs 传入的 model_name，其次读取环境变量 MOONSHOT_MODEL，最后使用默认值
        import os
        default_model = os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k-vision-preview")
        self.model_name = kwargs.get("model_name", default_model)
        self.prompt_loader = PromptLoader("backend/prompts/video_analysis_prompts.yaml")

    # ------------------------------------------------------------------ #
    #  主标注：综合视频分析（帧采样方式）                                    #
    # ------------------------------------------------------------------ #

    def analyze_video_comprehensive(
        self,
        video_path: str,
        analyze_actions: bool = True,
        analyze_motivations: bool = True,
        **kwargs,
    ) -> Dict:
        """综合分析视频（帧采样方式，每5秒取1帧，最多15帧）"""
        import cv2

        print(f"ℹ️ {self.model_name} 使用帧采样方式分析视频")

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        num_samples = max(1, min(15, int(duration / 5)))
        sample_interval = max(1, frame_count // num_samples)

        sampled_frames = []
        for i in range(num_samples):
            frame_idx = i * sample_interval
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                timestamp = frame_idx / fps
                sampled_frames.append((timestamp, frame))

        cap.release()

        print(f"📊 分析 {len(sampled_frames)} 个采样帧...")
        start_time = time.time()

        key_moments = []
        for timestamp, frame in sampled_frames:
            _, buffer = cv2.imencode(".jpg", frame)
            b64 = base64.b64encode(buffer).decode("utf-8")
            analysis = self._analyze_frame_base64(b64, timestamp)
            if not analysis.get("error"):
                key_moments.append(analysis)
            time.sleep(2)  # 避免触发速率限制

        processing_time = time.time() - start_time
        suggested_timestamps = [m["timestamp_seconds"] for m in key_moments]

        return {
            "key_moments": key_moments,
            "overall_narrative": self._synthesize_narrative(key_moments),
            "suggested_keyframe_timestamps": suggested_timestamps,
            "processing_time": processing_time,
            "model_used": self.model_name,
        }

    def analyze_single_frame(
        self,
        frame_path: str,
        timestamp: float,
        context: str = "",
    ) -> Dict:
        """分析单个关键帧"""
        with open(frame_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return self._analyze_frame_base64(b64, timestamp, context)

    def _analyze_frame_base64(
        self,
        base64_image: str,
        timestamp: float,
        context: str = "",
    ) -> Dict:
        """分析 base64 编码的图片"""
        prompt = self.prompt_loader.get_prompt(
            "single_frame.template", timestamp=timestamp, context=context
        )

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=1000,
                )

                result_text = response.choices[0].message.content
                json_str = self._extract_json(result_text)
                data = json.loads(json_str)
                data["timestamp_seconds"] = timestamp
                return data

            except Exception as e:
                print(f"⚠️ Kimi 分析帧失败 (尝试 {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(5)
                else:
                    return {"error": str(e), "timestamp_seconds": timestamp}

    def _synthesize_narrative(self, key_moments: list) -> str:
        """综合多个时刻生成整体叙述"""
        if not key_moments:
            return ""

        summary_prompt = (
            "基于以下关键时刻的分析，总结整个视频的动机演变：\n\n"
            f"{json.dumps(key_moments, ensure_ascii=False, indent=2)}\n\n"
            "请用一段话（50-100字）描述整体的 motivation 演变轨迹。"
        )

        try:
            response = self.client.chat.completions.create(
                model="moonshot-v1-8k",
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ 整体演变轨迹分析失败: {e}")
            return "整体演变轨迹分析失败"

    # ------------------------------------------------------------------ #
    #  交叉审核：review_annotation                                         #
    # ------------------------------------------------------------------ #

    def review_annotation(self, annotation: Dict) -> Dict:
        """
        作为审核方，对 Gemini 的主标注进行逐条审核。

        策略：
        1. 读取已提取的关键帧图片（最多 _MAX_REVIEW_FRAMES 帧）
        2. 将标注 JSON + 关键帧图片一起发给 Kimi
        3. 解析结构化审核结果
        """
        keyframes = annotation.get("keyframes", [])
        if not keyframes:
            return {
                "review_summary": "标注为空，无需审核",
                "reviewed_moments": [],
                "missing_moments": [],
            }

        # 选帧：均匀抽取，不超过上限
        if len(keyframes) > _MAX_REVIEW_FRAMES:
            step = len(keyframes) / _MAX_REVIEW_FRAMES
            selected = [keyframes[int(i * step)] for i in range(_MAX_REVIEW_FRAMES)]
        else:
            selected = keyframes

        # 构建消息内容
        content = []

        # 1. 先把完整的主标注 JSON 告知审核方
        annotation_summary = {
            "key_moments": [
                {
                    "moment_index": i,
                    "timestamp_seconds": kf.get("action", {}).get("timestamp", 0),
                    "action_description": kf.get("action", {}).get("action_description", ""),
                    "explicit_motivation": kf.get("motivation", {}).get("explicit_motivation", ""),
                    "implicit_desire": kf.get("motivation", {}).get("implicit_desire", ""),
                    "desire_category": kf.get("motivation", {}).get("desire_category", ""),
                    "implicit_level": kf.get("motivation", {}).get("implicit_level", 3),
                    "reasoning": kf.get("motivation", {}).get("reasoning", ""),
                }
                for i, kf in enumerate(keyframes)
            ]
        }

        content.append({
            "type": "text",
            "text": (
                f"## 主标注结果（共 {len(keyframes)} 个关键时刻）\n\n"
                f"{json.dumps(annotation_summary, ensure_ascii=False, indent=2)}\n\n"
                f"## 视频关键帧（共 {len(selected)} 帧，均匀采样）"
            ),
        })

        # 2. 插入关键帧图片
        frames_added = 0
        for kf in selected:
            frame_path = kf.get("frame_path", "")
            ts = kf.get("action", {}).get("timestamp", 0)

            if frame_path and Path(frame_path).exists():
                with open(frame_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")

                content.append({
                    "type": "text",
                    "text": f"[时间戳: {ts}s]",
                })
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                })
                frames_added += 1

        if frames_added == 0:
            print("⚠️ 未找到任何关键帧图片，审核将仅基于文本标注")

        # 3. 附加审核指令
        content.append({"type": "text", "text": _REVIEW_PROMPT})

        # 调用 API（带重试）
        for attempt in range(3):
            try:
                print(f"🤖 Moonshot 审核中（使用 {frames_added} 帧图片）...")
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": content}],
                    max_tokens=4000,
                )

                result_text = response.choices[0].message.content
                json_str = self._extract_json(result_text)
                result = json.loads(json_str)

                # 确保返回结构完整
                result.setdefault("review_summary", "")
                result.setdefault("reviewed_moments", [])
                result.setdefault("missing_moments", [])
                return result

            except json.JSONDecodeError as e:
                print(f"⚠️ JSON 解析失败 (尝试 {attempt + 1}/3): {e}")
                print(f"   原始响应: {result_text[:200]}...")
                if attempt < 2:
                    time.sleep(5)
                else:
                    return {
                        "review_summary": f"审核结果解析失败: {e}",
                        "reviewed_moments": [],
                        "missing_moments": [],
                    }
            except Exception as e:
                print(f"⚠️ Moonshot 审核调用失败 (尝试 {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(5)
                else:
                    raise

    # ------------------------------------------------------------------ #
    #  工具方法                                                            #
    # ------------------------------------------------------------------ #

    def generate_question(self, prompt: str) -> str:
        """根据 Prompt 生成问题"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ 生成问题失败: {e}")
            raise

    def test_connection(self) -> bool:
        """测试 API 连接"""
        try:
            response = self.client.chat.completions.create(
                model="moonshot-v1-8k",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ Moonshot 连接测试失败: {e}")
            return False

    @staticmethod
    def _extract_json(text: str) -> str:
        """从响应文本中提取 JSON 字符串"""
        if "```json" in text:
            return text.split("```json")[1].split("```")[0].strip()
        if "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()


# 注册 Provider
AIProviderFactory.register_provider("moonshot", MoonshotProvider)
