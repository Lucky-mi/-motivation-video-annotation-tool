import os
import json
import time
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# 复用现有逻辑，但修改路径配置
from backend.vlm_analyzer import VLMAnalyzer
from backend.annotation_schema import AnnotationSchema
from config.config import config

# 加载环境变量
load_dotenv(override=True)

# ==========================================
# 🧪 实验配置 (沙盒模式)
# ==========================================
# 1. 定义实验模型 (例如: gemini-3.0)
EXPERIMENTAL_MODEL = "gemini-3-pro-preview" 

# 2. 定义独立的实验目录 (不干扰原数据)
TEST_VIDEOS_DIR = Path("data/videos_test_set")       # 把要测试的10个视频复制到这里
EXP_OUTPUT_DIR = Path(f"data/annotations_{EXPERIMENTAL_MODEL}") # 结果会自动存到这里
EXP_KEYFRAMES_DIR = Path(f"data/keyframes_{EXPERIMENTAL_MODEL}")

# 确保目录存在
for d in [TEST_VIDEOS_DIR, EXP_OUTPUT_DIR, EXP_KEYFRAMES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def process_video_experiment(video_path: Path, analyzer: VLMAnalyzer):
    print(f"🧪 [实验] 正在分析: {video_path.name}")
    
    # 1. AI 分析
    analysis = analyzer.analyze_video_comprehensive(
        str(video_path),
        analyze_actions=True,
        analyze_motivations=True
    )
    
    if "error" in analysis:
        print(f"  ❌ 分析失败: {analysis['error']}")
        return

    # 2. 提取关键帧 (存到实验目录)
    timestamps = analysis.get("suggested_keyframe_timestamps", [])
    extracted = analyzer.extract_keyframes_from_video(
        str(video_path),
        timestamps,
        EXP_KEYFRAMES_DIR 
    )
    
    # 3. 组装数据 (简化版逻辑)
    keyframes_data = []
    key_moments = analysis.get('key_moments', [])
    moment_map = {int(m.get('timestamp_seconds', -1)): m for m in key_moments}

    for idx, (ts, path) in enumerate(extracted):
        moment = moment_map.get(int(ts), {})
        if not moment:
            closest = min(moment_map.keys(), key=lambda k: abs(k-ts)) if moment_map else None
            if closest and abs(closest - ts) < 1.5:
                moment = moment_map[closest]

        # 构造 Action & Motivation (使用 AI 的原始输出)
        action = {
            "timestamp": ts,
            "timestamp_formatted": f"{int(ts//60):02d}:{int(ts%60):02d}",
            "action_description": moment.get("action_description", ""),
            "visual_context": moment.get("visual_context", ""),
            "scene": moment.get("scene", "")
        }
        motivation = {
            "explicit_motivation": moment.get("explicit_motivation", ""),
            "implicit_desire": moment.get("implicit_desire", ""),
            "reasoning": moment.get("reasoning", ""),
            "model_version": EXPERIMENTAL_MODEL # 标记模型版本
        }
        
        keyframes_data.append({
            "frame_id": idx,
            "frame_path": str(path).replace('\\', '/'),
            "timestamp_seconds": ts,
            "action": action,
            "motivation": motivation
        })

    # 4. 保存 JSON 到实验目录
    annotation_data = {
        "video_id": video_path.stem,
        "video_name": video_path.name,
        "model_used": EXPERIMENTAL_MODEL,
        "keyframes": keyframes_data,
        "overall_trajectory": analysis.get('overall_narrative', '')
    }

    out_path = EXP_OUTPUT_DIR / f"{video_path.stem}.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(annotation_data, f, ensure_ascii=False, indent=2)
    
    print(f"  ✅ 实验数据已保存: {out_path}")

def main():
    print(f"🚀 启动对比实验: {EXPERIMENTAL_MODEL}")
    print(f"📂 视频源: {TEST_VIDEOS_DIR}")
    print(f"📂 结果存至: {EXP_OUTPUT_DIR}")
    
    api_key = config.get_api_key('gemini')
    if not api_key:
        print("❌ 未配置 API Key")
        return

    # 初始化分析器 (传入实验模型)
    analyzer = VLMAnalyzer(api_key=api_key, model_name=EXPERIMENTAL_MODEL)
    
    videos = list(TEST_VIDEOS_DIR.glob("*.*"))
    if not videos:
        print("⚠️ 测试目录为空，请先复制几个视频到 data/videos_test_set/")
        return

    for video in tqdm(videos):
        process_video_experiment(video, analyzer)
        time.sleep(5) # 防止限流

if __name__ == "__main__":
    main()