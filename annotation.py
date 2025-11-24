import os
import json
import cv2
import re
import time
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# 导入现有模块
from backend.vlm_analyzer import VLMAnalyzer
from backend.annotation_schema import AnnotationSchema
from backend.ai_providers.prompt_templates import PromptTemplates  # 新增导入
from config.config import config

# 加载环境变量
load_dotenv()

# 配置路径
VIDEOS_DIR = Path("data/videos")
KEYFRAMES_DIR = Path("data/keyframes")
ANNOTATIONS_DIR = Path("data/annotations")

# 确保目录存在
for d in [VIDEOS_DIR, KEYFRAMES_DIR, ANNOTATIONS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def auto_rename_video(video_path: Path, annotation_path: Path, analyzer: VLMAnalyzer):
    """
    [修复版V2] 智能重命名：增加防重复机制
    """
    # 1. 读取标注数据
    try:
        with open(annotation_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return

    # === 防重复检查 1: 检查 JSON 标记 ===
    # 如果已经标记为 "已重命名"，直接跳过
    if data.get('is_renamed', False):
        # print(f"  ⏩ 跳过: 已标记为重命名 ({video_path.name})") # 嫌啰嗦可以注释掉
        return

    # === 防重复检查 2: 检查文件名特征 (针对中文重命名) ===
    # 如果文件名包含中文字符，假设已经重命名过，跳过
    # (如果您是想翻成英文，请注释掉这段逻辑；如果是为了生成中文名，这段很有效)
    has_chinese = any('\u4e00' <= char <= '\u9fa5' for char in video_path.name)
    if has_chinese:
        # 补打标记并退出
        data['is_renamed'] = True
        with open(annotation_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return

    print(f"🏷️  正在分析主题并重命名: {video_path.name}")

    try:
        # 2. 生成 Prompt 并调用 AI
        prompt = PromptTemplates.get_theme_extraction_prompt(data)
        response = analyzer.model.generate_content(prompt)
        
        # 3. 解析 AI 返回的 JSON
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        result = json.loads(text)
        new_stem = result.get('suggested_filename')
        
        if not new_stem:
            return

        # 4. 清理文件名
        new_stem = re.sub(r'[\\/*?:"<>|]', "", new_stem)
        new_stem = new_stem.replace(" ", "_")
        new_video_name = f"{new_stem}{video_path.suffix}"
        
        # 如果名字极其相似（比如只是大小写或下划线区别），也视为一样
        if new_stem.lower() == video_path.stem.lower():
            data['is_renamed'] = True # 标记为已完成
            with open(annotation_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return

        # 5. 构造路径
        new_video_path = VIDEOS_DIR / new_video_name
        new_anno_path = ANNOTATIONS_DIR / f"{new_stem}.json"
        old_kf_dir = KEYFRAMES_DIR / video_path.stem
        new_kf_dir = KEYFRAMES_DIR / new_stem

        if new_video_path.exists():
            print(f"  ⚠️ 目标已存在，跳过: {new_video_name}")
            return

        print(f"  ✨ 执行重命名: {new_video_name}")

        # --- 执行重命名 ---
        video_path.rename(new_video_path)
        
        if old_kf_dir.exists() and not new_kf_dir.exists():
            old_kf_dir.rename(new_kf_dir)
            
        # --- 更新 JSON 内容 ---
        # 兼容 V1/V2 结构
        video_name_str = new_video_path.name
        video_path_str = str(new_video_path).replace('\\', '/')

        if 'video_info' in data:
            data['video_info']['video_name'] = video_name_str
            data['video_info']['video_path'] = video_path_str
        else:
            data['video_name'] = video_name_str
            data['video_path'] = video_path_str
        
        # 更新关键帧路径
        for kf in data.get('keyframes', []):
            old_path = kf.get('frame_path', '')
            if old_path:
                kf['frame_path'] = old_path.replace(f"/{video_path.stem}/", f"/{new_stem}/") \
                                           .replace(f"\\{video_path.stem}\\", f"\\{new_stem}\\")

        # 🔥 核心修改：写入“已重命名”标记
        data['is_renamed'] = True

        # 保存新 JSON
        with open(new_anno_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        if annotation_path != new_anno_path:
            annotation_path.unlink()

        print(f"  ✅ 重命名完成")
        
    except Exception as e:
        print(f"  ❌ 重命名失败: {e}")


def repair_missing_frames(video_path: Path, annotation_path: Path):
    """修复模式：有JSON但没图片的情况"""
    # ... (保持原代码不变) ...
    # 为了节省篇幅，这里逻辑与上一个版本一致，仅需确保 keyframes 路径逻辑正确
    # 可以在这里直接复制上一版的 repair_missing_frames 函数内容
    print(f"🔧 正在检查: {video_path.name}")
    
    try:
        with open(annotation_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return

    keyframes = data.get('keyframes', [])
    if not keyframes:
        return

    video_name = video_path.stem
    save_dir = KEYFRAMES_DIR / video_name
    
    # 如果还没创建目录，说明之前可能没切图
    if not save_dir.exists():
        save_dir.mkdir(exist_ok=True)

    # 简单检查第一帧图片是否存在
    first_frame_path = keyframes[0].get('frame_path')
    if first_frame_path and Path(first_frame_path).exists():
        # 大概通过了，跳过详细检查以节省时间
        return

    # 如果第一帧都没有，开始修复
    print(f"  ⚠️ 发现图片缺失，开始补切...")
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    updated = False

    for kf in keyframes:
        ts = kf.get('timestamp_seconds')
        if ts is None and 'action' in kf:
            ts = kf['action'].get('timestamp')
        
        if ts is None: continue
        ts = float(ts)
        
        # 生成标准路径
        filename = f"frame_{int(ts*100):05d}_t{ts:.2f}s.jpg"
        target_path = save_dir / filename
        
        if not target_path.exists():
            frame_num = int(ts * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame_img = cap.read()
            if ret:
                cv2.imwrite(str(target_path), frame_img)
                kf['frame_path'] = str(target_path).replace('\\', '/')
                updated = True
                print(f"    + 补回: {filename}")
    
    cap.release()
    if updated:
        with open(annotation_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("  💾 修复保存完成")


def process_new_video(video_path: Path, analyzer: VLMAnalyzer):
    """处理新视频：调用AI + 提取关键帧 + 手动构建V2数据"""
    import uuid
    from datetime import datetime
    
    print(f"🚀 开始处理新视频: {video_path.name}")
    max_retries = 3  # 最多重试3次
    analysis = {}
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f"  🔄 第 {attempt + 1} 次尝试重新分析...")
            
            # 1. AI 分析
            analysis = analyzer.analyze_video_comprehensive(
                str(video_path),
                analyze_actions=True,
                analyze_motivations=True
            )
            
            # 如果没有 error 字段，说明成功，跳出循环
            if "error" not in analysis:
                break
            
            # 如果有错，打印错误并等待
            print(f"  ⚠️ AI返回格式错误: {analysis['error']}")
            time.sleep(3) # 稍微冷静一下再重试
            
        except Exception as e:
            print(f"  ⚠️ 请求异常: {e}")
            time.sleep(3)

    # 如果重试了3次还是失败，才彻底放弃
    if "error" in analysis:
        print(f"  ❌ 重试 {max_retries} 次后依然失败，跳过此视频。")
        return
    # ====================

    try:
        # 2. 提取关键帧 (后续代码保持不变...)
        timestamps = analysis.get("suggested_keyframe_timestamps", [])
        # 1. AI 分析
        analysis = analyzer.analyze_video_comprehensive(
            str(video_path),
            analyze_actions=True,
            analyze_motivations=True
        )
        
        if "error" in analysis:
            print(f"  ❌ AI分析失败: {analysis['error']}")
            return

        # 2. 提取关键帧
        timestamps = analysis.get("suggested_keyframe_timestamps", [])
        print(f"  📸 提取 {len(timestamps)} 个关键帧...")
        
        extracted = analyzer.extract_keyframes_from_video(
            str(video_path),
            timestamps,
            KEYFRAMES_DIR 
        )
        
        # 3. 组装 V2 格式数据
        keyframes_data = []
        key_moments = analysis.get('key_moments', [])
        
        # 建立时间戳映射 (允许 1秒 误差)
        moment_map = {}
        for m in key_moments:
            ts = m.get('timestamp_seconds')
            if ts is not None:
                moment_map[int(ts)] = m

        for idx, (ts, path) in enumerate(extracted):
            # 查找 AI 结果
            moment = moment_map.get(int(ts), {})
            if not moment:
                # 模糊匹配
                closest = min(moment_map.keys(), key=lambda k: abs(k-ts)) if moment_map else None
                if closest and abs(closest - ts) < 1.5:
                    moment = moment_map[closest]

            # 构造 Action (What)
            action = {
                "timestamp": ts,
                "timestamp_formatted": f"{int(ts//60):02d}:{int(ts%60):02d}",
                "action_description": moment.get("action_description", ""),
                "visual_context": moment.get("visual_context", ""),
                "objects": moment.get("objects", []),
                "characters": moment.get("characters", []),
                "scene": moment.get("scene", ""),
                "confidence": moment.get("confidence", 0.8)
            }
            
            # 构造 Motivation (Why)
            motivation = {
                "explicit_motivation": moment.get("explicit_motivation", ""),
                "implicit_desire": moment.get("implicit_desire", ""),
                "desire_category": moment.get("desire_category", "other"),
                "motivation_type": moment.get("motivation_type", "mixed"),
                "implicit_level": moment.get("implicit_level", 3),
                "reasoning": moment.get("reasoning", ""),
                "visual_cues": moment.get("visual_cues", []),
                "status": "ai_generated",
                "confidence": moment.get("confidence", 0.8)
            }
            
            # 关键帧条目
            kf_data = {
                "frame_id": idx,
                "frame_path": str(path).replace('\\', '/'),
                "timestamp_seconds": ts,
                "action": action,           # V2 核心嵌套结构
                "motivation": motivation,   # V2 核心嵌套结构
                "is_transition": False
            }
            keyframes_data.append(kf_data)

        # 4. 构建完整的视频标注对象 (符合 V2 API 标准)
        # 不再使用 AnnotationSchema.create_empty_annotation，而是直接构建字典
        annotation_data = {
            "video_id": video_path.stem,
            "video_name": video_path.name,
            "video_path": str(video_path).replace('\\', '/'),
            "duration": 0.0, # 可选
            "keyframes": keyframes_data,
            "transitions": analysis.get('transitions', []),
            "overall_trajectory": analysis.get('overall_narrative', ''),
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "annotator": "AI_Batch",
            "status": "ai_generated",
            "total_frames": len(keyframes_data),
            "annotated_frames": 0,
            "ai_generated_frames": len(keyframes_data)
        }

        # 5. 保存文件
        out_path = ANNOTATIONS_DIR / f"{video_path.stem}.json"
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(annotation_data, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ 基础标注完成: {len(keyframes_data)} 帧")

        # 6. 自动重命名 (如果需要)
        auto_rename_video(video_path, out_path, analyzer)

        # 速率限制保护
        time.sleep(2) 

    except Exception as e:
        print(f"  ❌ 处理异常: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("========================================")
    print("   🎥 AI视频批处理 & 自动重命名工具")
    print("========================================")
    
    api_key = config.get_api_key('gemini')
    if not api_key:
        print("❌ 未配置 API Key")
        return
        
    analyzer = VLMAnalyzer(api_key=api_key)
    
    # 获取视频列表
    video_exts = {'.mp4', '.avi', '.mov', '.mkv'}
    videos = [f for f in VIDEOS_DIR.iterdir() if f.suffix.lower() in video_exts]
    
    print(f"📂 扫描到 {len(videos)} 个视频")
    
    # 选项：是否对已有标注的视频进行重命名？
    # rename_existing = input("是否对已有标注的视频进行AI重命名? (y/n): ").lower() == 'y'
    rename_existing = True # 默认开启，您可以手动改为 False

    for video in tqdm(videos):
        anno_path = ANNOTATIONS_DIR / f"{video.stem}.json"
        
        if anno_path.exists():
            # 已有标注：修复图片
            repair_missing_frames(video, anno_path)
            
            # [新增] 如果开启，则对旧视频也执行重命名
            if rename_existing:
                # 检查是否已经是中文名（简单判断：包含非ASCII字符）
                # 或者直接让AI判断，这里简单起见，只要存在就跑一次
                try:
                    # 为了避免重复调用，可以检查文件名长度或特征
                    # 这里直接调用，内部有判断 new_name == old_name 则跳过
                    auto_rename_video(video, anno_path, analyzer)
                    time.sleep(2) # 避免速率限制
                except Exception as e:
                    print(f"重命名出错: {e}")
        else:
            # 无标注：全流程处理 (分析 -> 切图 -> 保存 -> 重命名)
            process_new_video(video, analyzer)

    print("\n🎉 全部完成！")

if __name__ == "__main__":
    main()