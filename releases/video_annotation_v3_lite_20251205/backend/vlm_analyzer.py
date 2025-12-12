# backend/vlm_analyzer.py
"""
增强的VLM分析器 - 支持自动修复 JSON 和准确计时
"""
import json
import time
import cv2
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 尝试导入 json_repair，如果没有则降级处理
try:
    import json_repair
    JSON_REPAIR_AVAILABLE = True
except ImportError:
    JSON_REPAIR_AVAILABLE = False
    print("⚠️ 未安装 json_repair，建议运行: pip install json_repair")

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from backend.models import (
    KeyframeAction,
    MotivationAnnotation,
    KeyframeAnnotation,
    AnnotationStatus,
    DesireCategory,
    MotivationType
)


class VLMAnalyzer:
    """VLM视频分析器 - 专注于What和Why的智能分析"""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        # 如果没有传入 api_key，尝试从环境变量读取
        if not api_key:
            api_key = os.getenv('GEMINI_API_KEY')

        # 如果没有传入 model_name，从环境变量读取，默认为 gemini-2.0-flash
        if not model_name:
            model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

        if api_key and genai is not None:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            print(f"🤖 使用模型: {model_name}")
        else:
            self.model = None
    
    def analyze_video_comprehensive(
        self,
        video_path: str,
        analyze_actions: bool = True,
        analyze_motivations: bool = True
    ) -> Dict:
        """综合分析视频"""
        if not self.model or genai is None:
            return {"error": "未配置Gemini API"}
        
        # 1. 上传视频
        print(f"📤 上传视频: {Path(video_path).name} ...")
        try:
            uploaded_file = genai.upload_file(path=str(video_path))
            print(f"  ⏳ 文件已上传，等待处理... (初始状态: {uploaded_file.state.name})")

            # 等待处理 (增加超时和详细日志)
            max_wait_time = 300  # 5分钟超时
            wait_count = 0

            while uploaded_file.state.name == "PROCESSING":
                time.sleep(5)
                wait_count += 1
                uploaded_file = genai.get_file(uploaded_file.name)

                if wait_count % 6 == 0:  # 每30秒显示一次
                    print(f"  ⏳ 仍在处理中... ({wait_count * 5}秒)")

                if wait_count * 5 >= max_wait_time:
                    return {"error": f"处理超时（超过{max_wait_time}秒）"}

            if uploaded_file.state.name != "ACTIVE":
                error_msg = f"文件处理失败: {uploaded_file.state.name}"
                # 尝试获取详细错误信息
                if hasattr(uploaded_file, 'error'):
                    error_msg += f" - {uploaded_file.error}"
                print(f"  ❌ {error_msg}")
                return {"error": error_msg}

            print(f"  ✅ 文件处理完成！")

        except Exception as e:
            error_detail = f"上传失败: {str(e)}"
            print(f"  ❌ {error_detail}")
            import traceback
            traceback.print_exc()
            return {"error": error_detail}

        # 2. 构建 Prompt
        prompt = self._build_comprehensive_prompt(analyze_actions, analyze_motivations)

        # 3. 生成内容 (计时修复)
        print("🤖 AI分析中...")
        start_time = time.time()  # <--- 修复：计时器放在请求前
        
        try:
            # 设置较大的 token 上限以防截断
            response = self.model.generate_content(
                [uploaded_file, prompt],
                generation_config={"max_output_tokens": 8192} 
            )
            
            processing_time = time.time() - start_time
            print(f"✅ 分析完成 (耗时: {processing_time:.2f}s)")
            
            # 4. 解析与修复 JSON
            result_text = response.text
            
            # 提取 JSON 块
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                json_str = result_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = result_text
            
            try:
                # 优先使用标准库解析
                analysis = json.loads(json_str)
            except json.JSONDecodeError:
                # 如果失败，尝试使用 json_repair 抢救
                if JSON_REPAIR_AVAILABLE:
                    print("  ⚠️ JSON格式错误，正在尝试自动修复...")
                    analysis = json_repair.loads(json_str)
                else:
                    raise  # 没装库就抛出异常

            # 补充字段
            analysis['processing_time'] = processing_time
            
            # 清理云端文件
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass
                
            return analysis
        
        except Exception as e:
            print(f"  ⚠️ 解析失败: {e}")
            return {
                "error": str(e),
                "raw_response": response.text if 'response' in locals() else "",
                "processing_time": time.time() - start_time
            }
    
    def _build_comprehensive_prompt(self, analyze_actions: bool, analyze_motivations: bool) -> str:
        """构建 Prompt - 强调简洁性以防截断"""
        return """
你是一位专业的心理学视频分析专家。请分析这个视频的关键时刻。

请按以下 JSON 格式输出（保持简洁，不要过度啰嗦，确保 JSON 格式完整）：

```json
{
  "key_moments": [
    {
      "timestamp_seconds": 15,
      "action_description": "客观描述动作",
      "visual_context": "环境描述",
      "objects": ["物体1"],
      "characters": ["角色A"],
      "scene": "场景名",
      
      "explicit_motivation": "显性动机",
      "implicit_desire": "隐性渴望 (基于马斯洛需求)",
      "desire_category": "safety",
      "motivation_type": "intrinsic",
      "implicit_level": 4,
      "reasoning": "简短的推理依据",
      "visual_cues": ["线索1"],
      "confidence": 0.9
    }
  ],
  "transitions": [],
  "overall_narrative": "一句话总结",
  "suggested_keyframe_timestamps": [15, 30]
}
要求：

只输出 JSON，不要其他废话。

提取 5-10 个最具代表性的关键帧即可，不用太多。

确保 JSON 语法正确，尤其是结尾的闭合括号。 """

    def extract_keyframes_from_video(
        self, 
        video_path: str, 
        timestamps: List[float], 
        output_dir: Path
    ) -> List[Tuple[float, str]]:
        """
        提取关键帧 (修复中文路径支持)
        """
        import numpy as np # 确保引入numpy
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return []
        
        video_name = Path(video_path).stem
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        kf_dir = output_dir / video_name
        kf_dir.mkdir(parents=True, exist_ok=True)
        
        extracted = []
        unique_timestamps = sorted(list(set(timestamps)))
        
        for idx, ts in enumerate(unique_timestamps):
            try:
                frame_num = int(ts * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if ret:
                    filename = f"frame_{idx:04d}_t{ts:.2f}s.jpg"
                    path = kf_dir / filename
                    
                    # 🔥【核心修复】🔥
                    # Windows下 cv2.imwrite 不支持中文路径
                    # 改用 cv2.imencode + tofile 的方式，完美支持中文
                    is_success, im_buf = cv2.imencode(".jpg", frame)
                    if is_success:
                        im_buf.tofile(str(path))
                        extracted.append((ts, str(path)))
                    
            except Exception as e:
                # print(f"  ⚠️ 提取帧失败: {e}")
                continue
        
        cap.release()
        return extracted