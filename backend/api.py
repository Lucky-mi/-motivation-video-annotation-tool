# backend/api.py
"""
FastAPI 后端服务
提供视频分析和标注的API接口
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Optional
import uuid
import shutil
import json
from datetime import datetime

from backend.models import (
    VideoAnnotation,
    KeyframeAnnotation,
    AIAnalysisRequest,
    AIAnalysisResponse,
    AnnotationStatus,
    MotivationAnnotation,
    DesireCategory,  # <--- 添加这个
    MotivationType
)
# ... 导入之后
VALID_DESIRE_CATEGORIES = [e.value for e in DesireCategory]
VALID_MOTIVATION_TYPES = [e.value for e in MotivationType]
from backend.vlm_analyzer import VLMAnalyzer
from config.config import config

# 初始化FastAPI
app = FastAPI(
    title="Video Motivation Annotation API",
    description="AI辅助的视频动机标注系统",
    version="2.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路径配置
VIDEOS_DIR = Path(config.get_str('paths.videos', 'data/videos'))
KEYFRAMES_DIR = Path(config.get_str('paths.keyframes', 'data/keyframes'))
ANNOTATIONS_DIR = Path(config.get_str('paths.annotations', 'data/annotations'))

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
KEYFRAMES_DIR.mkdir(parents=True, exist_ok=True)
ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)

# 初始化VLM分析器
vlm_analyzer = VLMAnalyzer(api_key=config.get_api_key('gemini'))


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Video Motivation Annotation API",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "gemini_available": vlm_analyzer.model is not None
    }


# ============= 视频管理 =============

@app.post("/videos/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    上传视频文件
    
    Returns:
        {
            "video_id": "...",
            "video_name": "...",
            "video_path": "...",
            "size": 12345
        }
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    # 生成唯一ID
    video_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    video_filename = f"{video_id}{file_extension}"
    video_path = VIDEOS_DIR / video_filename
    
    # 保存文件
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {
        "video_id": video_id,
        "video_name": file.filename,
        "video_path": str(video_path),
        "size": video_path.stat().st_size
    }


@app.get("/videos/list")
async def list_videos():
    """
    列出所有视频
    
    Returns:
        {
            "videos": [
                {
                    "video_id": "...",
                    "video_name": "...",
                    "video_path": "...",
                    "size": 12345
                }
            ]
        }
    """
    videos = []
    for video_file in VIDEOS_DIR.glob("*"):
        if video_file.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
            video_id = video_file.stem
            videos.append({
                "video_id": video_id,
                "video_name": video_file.name,
                "video_path": str(video_file),
                "size": video_file.stat().st_size
            })
    
    return {"videos": videos}


@app.get("/videos/{video_id}")
async def get_video(video_id: str):
    """
    获取视频文件
    """
    video_files = list(VIDEOS_DIR.glob(f"{video_id}.*"))
    if not video_files:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    return FileResponse(video_files[0])


# ============= AI分析 =============

@app.post("/analyze/video", response_model=AIAnalysisResponse)
async def analyze_video(request: AIAnalysisRequest):
    """
    AI分析视频 - 生成What和Why的预标注
    
    Workflow:
    1. 提取关键帧 (uniform/smart)
    2. AI分析每一帧的What (action/objects/scene)
    3. AI推断Why (motivation/desire)
    4. 返回完整标注供人工审核
    """
    video_path = Path(request.video_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    video_id = video_path.stem
    
    try:
        # Step 1: 提取关键帧
        print(f"📹 开始分析视频: {video_path.name}")
        
        if request.extraction_mode == "smart":
            # 智能提取 - 基于AI分析
            analysis = vlm_analyzer.analyze_video_comprehensive(
                str(video_path),
                analyze_actions=request.analyze_actions,
                analyze_motivations=request.suggest_motivations
            )
            
            if "error" in analysis:
                raise HTTPException(status_code=500, detail=analysis["error"])
            
            # 提取建议的关键帧
            timestamps = analysis.get("suggested_keyframe_timestamps", [])
            extracted_frames = vlm_analyzer.extract_keyframes_from_video(
                str(video_path),
                timestamps,
                KEYFRAMES_DIR
            )
            
            # 构建KeyframeAnnotation列表
            keyframes = []
            key_moments = {m['timestamp_seconds']: m for m in analysis.get('key_moments', [])}
            
            for idx, (timestamp, frame_path) in enumerate(extracted_frames):
                moment_data = key_moments.get(int(timestamp), {})
                
                # 构建action
                action_data = {
                    "timestamp": timestamp,
                    "timestamp_formatted": f"{int(timestamp//60):02d}:{int(timestamp%60):02d}",
                    "action_description": moment_data.get("action_description", ""),
                    "visual_context": moment_data.get("visual_context", ""),
                    "objects": moment_data.get("objects", []),
                    "characters": moment_data.get("characters", []),
                    "scene": moment_data.get("scene", ""),
                    "confidence": moment_data.get("confidence", 0.8)
                }
                # --- 开始修复：清洗AI返回的数据 ---
                ai_desire_category = moment_data.get("desire_category")
                if ai_desire_category not in VALID_DESIRE_CATEGORIES:
                    print(f"⚠️ AI返回了无效的 desire_category: '{ai_desire_category}'，已自动修正为 'other'")
                    ai_desire_category = "other"

                ai_motivation_type = moment_data.get("motivation_type")
                if ai_motivation_type not in VALID_MOTIVATION_TYPES:
                    print(f"⚠️ AI返回了无效的 motivation_type: '{ai_motivation_type}'，已自动修正为 'mixed'")
                    ai_motivation_type = "mixed" # 假设 'mixed' 是默认值
                # --- 结束修复 ---
                # 构建motivation
                motivation_data = {
                    "explicit_motivation": moment_data.get("explicit_motivation", ""),
                    "implicit_desire": moment_data.get("implicit_desire", ""),
                    "desire_category": moment_data.get("desire_category"),
                    "motivation_type": moment_data.get("motivation_type"),
                    "implicit_level": moment_data.get("implicit_level", 3),
                    "reasoning": moment_data.get("reasoning", ""),
                    "visual_cues": moment_data.get("visual_cues", []),
                    "status": AnnotationStatus.AI_GENERATED,
                    "confidence": moment_data.get("confidence", 0.8)
                }
                
                keyframe = KeyframeAnnotation(
                    frame_id=idx,
                    frame_path=frame_path,
                    action=action_data,
                    motivation=motivation_data
                )
                keyframes.append(keyframe)
            
            suggested_transitions = analysis.get("transitions", [])
            overall_summary = analysis.get("overall_narrative", "")
            processing_time = analysis.get("processing_time", 0.0)
        
        else:
            # 均匀采样
            extracted_frames = vlm_analyzer.extract_uniform_frames(
                str(video_path),
                KEYFRAMES_DIR,
                interval_seconds=request.interval_seconds,
                max_frames=request.max_frames
            )
            
            # 对每一帧进行AI分析
            keyframes = []
            for idx, (timestamp, frame_path) in enumerate(extracted_frames):
                annotation = vlm_analyzer.analyze_single_frame(
                    frame_path,
                    timestamp
                )
                annotation.frame_id = idx
                keyframes.append(annotation)
            
            suggested_transitions = []
            overall_summary = ""
            processing_time = 0.0
        
        # 返回响应
        response = AIAnalysisResponse(
            video_id=video_id,
            keyframes=keyframes,
            suggested_transitions=suggested_transitions,
            overall_summary=overall_summary,
            processing_time=processing_time,
            model_used="gemini-2.5-flash"
        )
        
        # 自动保存初始标注
        save_annotation_to_file(video_id, response)
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= 标注管理 =============

@app.get("/annotations/list")
async def list_annotations():
    """
    列出所有标注文件
    """
    annotations = []
    for ann_file in ANNOTATIONS_DIR.glob("*.json"):
        with open(ann_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            annotations.append({
                "video_id": ann_file.stem,
                "video_name": data.get("video_name", ""),
                "status": data.get("status", ""),
                "last_modified": data.get("last_modified", ""),
                "annotated_frames": data.get("annotated_frames", 0),
                "total_frames": data.get("total_frames", 0)
            })
    
    return {"annotations": annotations}


@app.get("/annotations/{video_id}")
async def get_annotation(video_id: str):
    """
    获取视频标注
    """
    annotation_path = ANNOTATIONS_DIR / f"{video_id}.json"
    if not annotation_path.exists():
        raise HTTPException(status_code=404, detail="标注不存在")
    
    with open(annotation_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@app.post("/annotations/{video_id}/keyframe/{frame_id}")
async def update_keyframe_annotation(
    video_id: str,
    frame_id: int,
    motivation: MotivationAnnotation
):
    """
    更新单个关键帧的标注 (人工修改Why部分)
    """
    annotation_path = ANNOTATIONS_DIR / f"{video_id}.json"
    if not annotation_path.exists():
        raise HTTPException(status_code=404, detail="标注不存在")
    
    with open(annotation_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 更新指定帧的motivation
    if frame_id < len(data.get('keyframes', [])):
        data['keyframes'][frame_id]['motivation'] = motivation.dict()
        data['last_modified'] = datetime.now().isoformat()
        
        # 更新统计
        annotated_count = sum(
            1 for kf in data['keyframes']
            if kf['motivation'].get('status') in ['human_confirmed', 'human_modified', 'human_created']
        )
        data['annotated_frames'] = annotated_count
    
    # 保存
    with open(annotation_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {"message": "更新成功", "frame_id": frame_id}


@app.post("/annotations/{video_id}/confirm-all")
async def confirm_all_ai_annotations(video_id: str):
    """
    批量确认所有AI标注
    """
    annotation_path = ANNOTATIONS_DIR / f"{video_id}.json"
    if not annotation_path.exists():
        raise HTTPException(status_code=404, detail="标注不存在")
    
    with open(annotation_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 更新所有AI标注状态
    for keyframe in data.get('keyframes', []):
        if keyframe['motivation'].get('status') == 'ai_generated':
            keyframe['motivation']['status'] = 'human_confirmed'
    
    data['last_modified'] = datetime.now().isoformat()
    data['human_confirmed_frames'] = len(data.get('keyframes', []))
    
    with open(annotation_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {"message": "批量确认成功"}


@app.get("/keyframes/{video_id}/{frame_filename}")
async def get_keyframe_image(video_id: str, frame_filename: str):
    """
    获取关键帧图片
    """
    frame_path = KEYFRAMES_DIR / video_id / frame_filename
    if not frame_path.exists():
        raise HTTPException(status_code=404, detail="关键帧不存在")
    
    return FileResponse(frame_path)


# ============= 工具函数 =============

def save_annotation_to_file(video_id: str, analysis: AIAnalysisResponse):
    """保存标注到文件"""
    annotation_data = {
        "video_id": video_id,
        "video_name": video_id,
        "video_path": str(VIDEOS_DIR / video_id),
        "duration": 0.0,
        "keyframes": [kf.dict() for kf in analysis.keyframes],
        "transitions": [t.dict() for t in analysis.suggested_transitions],
        "overall_trajectory": analysis.overall_summary,
        "summary": "",
        "created_at": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
        "annotator": "AI",
        "status": "ai_generated",
        "total_frames": len(analysis.keyframes),
        "annotated_frames": 0,
        "ai_generated_frames": len(analysis.keyframes),
        "human_confirmed_frames": 0
    }
    
    annotation_path = ANNOTATIONS_DIR / f"{video_id}.json"
    with open(annotation_path, 'w', encoding='utf-8') as f:
        json.dump(annotation_data, f, ensure_ascii=False, indent=2)


# ============= 启动配置 =============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)