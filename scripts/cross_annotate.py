# scripts/cross_annotate.py
"""
AI交叉标注工具 - 使用Gemini和Moonshot(Kimi)同时标注同一视频
适配 V6 JSON 结构，输出完全兼容 V6 审核平台的数据。
"""
import os
import sys
import json
import time
import cv2
import base64
try:
    import json_repair
    JSON_REPAIR_AVAILABLE = True
except ImportError:
    JSON_REPAIR_AVAILABLE = False
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.vlm_analyzer import VLMAnalyzer
from backend.prompt_loader import PromptLoader
from config.config import config

# 加载环境变量
load_dotenv()

# 配置路径
VIDEOS_DIR = Path("data/Youtube_videos")
ANNOTATIONS_DIR = Path("data/annotations_v6_cross") # 交叉标注结果单独存放
ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)

def prefix_ids(data_json: dict, prefix: str):
    """
    遍历V6的JSON，为每个主键和外键添加前缀，确保多个模型的标注不冲突。
    """
    # characters
    if "characters" in data_json:
        for char in data_json["characters"]:
            old_id = char.get("character_id")
            if old_id:
                char["character_id"] = f"{prefix}{old_id}"
                
    # behavioral_sequence
    if "behavioral_sequence" in data_json:
        for seq in data_json["behavioral_sequence"]:
            if "sequence_id" in seq:
                seq["sequence_id"] = f"{prefix}{seq['sequence_id']}"
            if "character_id" in seq and seq["character_id"]:
                seq["character_id"] = f"{prefix}{seq['character_id']}"
                
    # desire_motivation_analysis
    if "desire_motivation_analysis" in data_json:
        for dma in data_json["desire_motivation_analysis"]:
            if "analysis_id" in dma:
                dma["analysis_id"] = f"{prefix}{dma['analysis_id']}"
            if "character_id" in dma and dma["character_id"]:
                dma["character_id"] = f"{prefix}{dma['character_id']}"
            if "supporting_sequence_ids" in dma:
                dma["supporting_sequence_ids"] = [f"{prefix}{sid}" for sid in dma.get("supporting_sequence_ids", [])]
                
    # desire_transitions
    if "desire_transitions" in data_json:
        for dt in data_json["desire_transitions"]:
            if "transition_id" in dt:
                dt["transition_id"] = f"{prefix}{dt['transition_id']}"
            if "character_id" in dt and dt["character_id"]:
                dt["character_id"] = f"{prefix}{dt['character_id']}"
                
    # inter_character_dynamics
    if "inter_character_dynamics" in data_json:
        for icd in data_json["inter_character_dynamics"]:
            if "dyad_id" in icd:
                icd["dyad_id"] = f"{prefix}{icd['dyad_id']}"
            if "character_1_id" in icd and icd["character_1_id"]:
                icd["character_1_id"] = f"{prefix}{icd['character_1_id']}"
            if "character_2_id" in icd and icd["character_2_id"]:
                icd["character_2_id"] = f"{prefix}{icd['character_2_id']}"
                
    # key_segments_for_qa
    if "key_segments_for_qa" in data_json:
        for ksqa in data_json["key_segments_for_qa"]:
            if "segment_id" in ksqa:
                ksqa["segment_id"] = f"{prefix}{ksqa['segment_id']}"
                
    # metadata
    if "annotation_metadata" in data_json:
        if "neutral_segments" in data_json["annotation_metadata"]:
            for ns in data_json["annotation_metadata"]["neutral_segments"]:
                if "character_id" in ns and ns["character_id"]:
                    ns["character_id"] = f"{prefix}{ns['character_id']}"
    
    return data_json

def merge_v6_annotations(gemini_json: dict, kimi_json: dict) -> dict:
    """合并两个 V6 标注"""
    gemini_clean = prefix_ids(gemini_json.copy(), "G_")
    kimi_clean = prefix_ids(kimi_json.copy(), "K_")
    
    combined = {
        "video_id": gemini_clean.get("video_id", kimi_clean.get("video_id")),
        "video_path": gemini_clean.get("video_path", kimi_clean.get("video_path")),
        "duration_seconds": gemini_clean.get("duration_seconds", kimi_clean.get("duration_seconds")),
        "annotation_timestamp": gemini_clean.get("annotation_timestamp", kimi_clean.get("annotation_timestamp")),
        "annotator": "CrossModel_Gemini_Kimi",
        
        # 场景以上下文丰富的为准，或者合并
        "scene_context": gemini_clean.get("scene_context", kimi_clean.get("scene_context", {})),
        
        # 将各数组拼接到一起
        "characters": gemini_clean.get("characters", []) + kimi_clean.get("characters", []),
        "behavioral_sequence": gemini_clean.get("behavioral_sequence", []) + kimi_clean.get("behavioral_sequence", []),
        "desire_motivation_analysis": gemini_clean.get("desire_motivation_analysis", []) + kimi_clean.get("desire_motivation_analysis", []),
        "desire_transitions": gemini_clean.get("desire_transitions", []) + kimi_clean.get("desire_transitions", []),
        "key_segments_for_qa": gemini_clean.get("key_segments_for_qa", []) + kimi_clean.get("key_segments_for_qa", []),
        "inter_character_dynamics": gemini_clean.get("inter_character_dynamics", []) + kimi_clean.get("inter_character_dynamics", []),
        
        "annotation_metadata": {
            "model_used": "Gemini + Moonshot(Kimi)",
            "annotation_version": "6.1_cross",
            "taxonomy_version": "DDF_v1.0",
            "frameworks_applied": ["BDI", "Maslow", "ToM", "Circumplex", "Desire_Dynamics", "DDF_v1.0"],
            "total_characters_annotated": len(gemini_clean.get("characters", [])) + len(kimi_clean.get("characters", [])),
            "total_desire_annotations": len(gemini_clean.get("desire_motivation_analysis", [])) + len(kimi_clean.get("desire_motivation_analysis", [])),
            "total_transitions_detected": len(gemini_clean.get("desire_transitions", [])) + len(kimi_clean.get("desire_transitions", [])),
            "gemini_processing_time": gemini_clean.get("processing_time"),
            "kimi_processing_time": kimi_clean.get("processing_time")
        }
    }
    
    # 将质量问题合集
    g_flags = gemini_clean.get("annotation_metadata", {}).get("quality_flags", {})
    k_flags = kimi_clean.get("annotation_metadata", {}).get("quality_flags", {})
    combined_flags = {}
    for k in set(g_flags.keys()).union(k_flags.keys()):
        combined_flags[k] = g_flags.get(k, False) or k_flags.get(k, False)
    
    combined["annotation_metadata"]["quality_flags"] = combined_flags
    return combined

def kimi_analyze_v6(video_path: str, kimi_api_key: str) -> dict:
    """
    使用 Kimi 模型进行 V6 完整框架分析。
    Kimi K2.5 支持视频输入，但需要公网 URL；本地视频文件采用均匀帧采样
    + 多图 Prompt 的方式传入，实际效果与直接上传视频相近。
    """
    kimi_model = os.getenv("MOONSHOT_MODEL", "moonshot-v1-32k-vision-preview")
    print(f"  🌙 准备 Kimi ({kimi_model}) 帧采样...")

    # 屏蔽 FFmpeg/OpenCV 底层解码警告（co located POCs 等噪音）
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    old_stderr_fd = os.dup(2)
    os.dup2(devnull_fd, 2)
    os.close(devnull_fd)
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps else 0

        num_samples = min(20, int(duration / 3))
        num_samples = max(num_samples, 5)
        sample_interval = max(frame_count // num_samples, 1)

        sampled_base64 = []
        for i in range(num_samples):
            frame_idx = i * sample_interval
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                height, width = frame.shape[:2]
                max_dim = 1024
                if max(height, width) > max_dim:
                    scale = max_dim / max(height, width)
                    frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
                _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                b64 = base64.b64encode(buffer).decode('utf-8')
                sampled_base64.append((frame_idx / fps, b64))
        cap.release()
    finally:
        os.dup2(old_stderr_fd, 2)
        os.close(old_stderr_fd)

    print(f"  📸 Kimi 已采帧 {len(sampled_base64)} 张")
    
    loader = PromptLoader("backend/prompts/annotation_prompts_v6.yaml")
    prompt_text = loader.get_prompt("annotation_v6", duration=duration)
    
    content_list = [{"type": "text", "text": prompt_text}]
    for ts, b64 in sampled_base64:
        content_list.append({
            "type": "text", "text": f"Timestamp: {ts:.2f}s"
        })
        content_list.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })
        
    client = OpenAI(
        api_key=kimi_api_key,
        base_url="https://api.moonshot.cn/v1",
    )
    
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=kimi_model,
            messages=[{"role": "user", "content": content_list}],
            max_tokens=32768,
            temperature=1
        )
        t = time.time() - start_time
        res_text = response.choices[0].message.content
        
        if "```json" in res_text:
            json_str = res_text.split("```json")[1].split("```")[0].strip()
        elif "```" in res_text:
            json_str = res_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = res_text
            
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            if JSON_REPAIR_AVAILABLE:
                print("  ⚠️ Kimi JSON格式异常，尝试自动修复...")
                data = json_repair.loads(json_str)
            else:
                raise
        data['processing_time'] = t
        return data
        
    except Exception as e:
        print(f"  ❌ Kimi 分析出错: {e}")
        return {"error": str(e)}

def process_cross_annotation(video_path: Path):
    """执行单个视频的双模型交叉标注"""
    print(f"\n🚀 开始交叉标注处理: {video_path.name}")
    
    gemini_key = os.getenv('GEMINI_API_KEY') or config.get_api_key('gemini')
    kimi_key = os.getenv('MOONSHOT_API_KEY') or config.get_api_key('moonshot')
    
    if not gemini_key or not kimi_key:
        print("❌ 缺少 API Key！请确保配置了 GEMINI_API_KEY 和 MOONSHOT_API_KEY。")
        return False
        
    gemini_model = os.getenv('GEMINI_MODEL', 'gemini-3.1-pro-preview')
    analyzer = VLMAnalyzer(api_key=gemini_key, model_name=gemini_model)

    out_path = ANNOTATIONS_DIR / f"{video_path.stem}_cross.json"
    if out_path.exists():
        print(f"⏩ 已存在标注文件，跳过: {out_path.name}")
        return True

    # ---------- 第 1 步：Gemini 分析 ----------
    print("  ⭐ [1/3] Gemini V6 正在分析...")
    # 修改 analyze_video_comprehensive 为正确调用，如果 VLMAnalyzer 有包装 V6 最好，否则自己拼接 prompt
    # 这里 VLMAnalyzer.analyze_video_comprehensive 已经配置好了 V6 提示词
    gemini_result = analyzer.analyze_video_comprehensive(str(video_path))
    
    if "error" in gemini_result:
        print(f"  ⚠️ Gemini分析报错: {gemini_result['error']}")
        return False
        
    # 填充必要数据
    gemini_result["video_id"] = video_path.stem
    gemini_result["video_path"] = str(video_path).replace('\\', '/')
        
    # ---------- 第 2 步：Kimi 分析 ----------
    print("  🌙 [2/3] Kimi (Moonshot) V6 正在分析...")
    if not OpenAI:
        print("  ⚠️ OpenAI 库未安装，跳过 Kimi 分析。")
        return False
        
    kimi_result = kimi_analyze_v6(str(video_path), kimi_key)
    
    if "error" in kimi_result:
         # Kimi 可能会挂，但我们可以保存单 Gemini 数据
         print(f"  ⚠️ Kimi分析失败，本次仅包含 Gemini 数据。")
         with open(out_path, 'w', encoding='utf-8') as f:
             json.dump(gemini_result, f, ensure_ascii=False, indent=2)
         return True
    
    # ---------- 第 3 步：融合并保存 ----------
    print("  💾 [3/3] 合并交叉标注结果...")
    
    kimi_result["video_id"] = video_path.stem
    kimi_result["video_path"] = str(video_path).replace('\\', '/')
    
    final_data = merge_v6_annotations(gemini_result, kimi_result)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    print(f"  ✅ 交叉标注完成: {video_path.name} -> {out_path.name}")
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI视频交叉标注工具 (Gemini + Kimi)")
    parser.add_argument("--videos", type=str, default=None, help="视频目录路径，默认使用 data/Youtube_videos")
    args = parser.parse_args()

    videos_dir = Path(args.videos) if args.videos else VIDEOS_DIR

    print("========================================")
    print("   ⚔️ AI视频交叉标注工具 (Gemini + Kimi) [V6版]")
    print("========================================")
    print(f"📁 视频目录: {videos_dir.resolve()}")
    print(f"💾 输出目录: {ANNOTATIONS_DIR.resolve()}")

    video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    videos = [f for f in videos_dir.iterdir() if f.suffix.lower() in video_exts]
    print(f"📂 扫描到 {len(videos)} 个视频")

    if not videos:
        print(f"💡 未找到视频，请检查目录: {videos_dir}")
        return

    for video in tqdm(videos):
        process_cross_annotation(video)

if __name__ == "__main__":
    main()
