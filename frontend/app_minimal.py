# backend/api_minimal.py
"""
极简API服务 - 只提供读写功能
不包含AI分析功能（由本地批处理脚本完成）
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Dict, Optional
import json
from datetime import datetime

# 初始化FastAPI
app = FastAPI(
    title="Video Annotation API - Minimal",
    description="极简版API - 只提供数据读写功能",
    version="1.0.0"
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
ANNOTATIONS_DIR = Path("data/annotations")
QUESTIONS_DIR = Path("data/questions")
KEYFRAMES_DIR = Path("data/keyframes")
QUESTIONNAIRE_DIR = Path("data/questionnaire_responses")

# 确保目录存在
for d in [ANNOTATIONS_DIR, QUESTIONS_DIR, KEYFRAMES_DIR, QUESTIONNAIRE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ============= 基础端点 =============

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Video Annotation API - Minimal",
        "version": "1.0.0",
        "status": "running",
        "note": "Use local batch processor for AI analysis"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# ============= 标注管理 =============

@app.get("/annotations/list")
async def list_annotations():
    """列出所有标注"""
    annotations = []
    
    for ann_file in ANNOTATIONS_DIR.glob("*.json"):
        try:
            with open(ann_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                annotations.append({
                    "video_id": ann_file.stem,
                    "video_name": data.get("video_name", ann_file.stem),
                    "status": data.get("status", ""),
                    "last_modified": data.get("last_modified", ""),
                    "annotated_frames": data.get("annotated_frames", 0),
                    "total_frames": data.get("total_frames", 0)
                })
        except Exception as e:
            print(f"Error loading {ann_file}: {e}")
            continue
    
    # 按修改时间排序
    annotations.sort(key=lambda x: x.get('last_modified', ''), reverse=True)
    
    return {"annotations": annotations}


@app.get("/annotations/{video_id}")
async def get_annotation(video_id: str):
    """获取视频标注"""
    annotation_path = ANNOTATIONS_DIR / f"{video_id}.json"
    
    if not annotation_path.exists():
        raise HTTPException(status_code=404, detail="标注不存在")
    
    try:
        with open(annotation_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取失败: {str(e)}")


@app.post("/annotations/{video_id}/keyframe/{frame_id}")
async def update_keyframe_annotation(
    video_id: str,
    frame_id: int,
    data: Dict
):
    """更新单个关键帧的标注"""
    annotation_path = ANNOTATIONS_DIR / f"{video_id}.json"
    
    if not annotation_path.exists():
        raise HTTPException(status_code=404, detail="标注不存在")
    
    try:
        # 读取现有数据
        with open(annotation_path, 'r', encoding='utf-8') as f:
            annotation = json.load(f)
        
        # 更新指定帧
        keyframes = annotation.get('keyframes', [])
        
        if frame_id < len(keyframes):
            # 更新action和motivation
            if 'action' in data:
                keyframes[frame_id]['action'].update(data['action'])
            
            if 'motivation' in data:
                keyframes[frame_id]['motivation'].update(data['motivation'])
            
            # 更新时间戳
            annotation['last_modified'] = datetime.now().isoformat()
            
            # 更新统计
            annotated_count = sum(
                1 for kf in keyframes
                if kf.get('motivation', {}).get('status') in ['human_confirmed', 'human_modified']
            )
            annotation['annotated_frames'] = annotated_count
        
        # 保存
        with open(annotation_path, 'w', encoding='utf-8') as f:
            json.dump(annotation, f, ensure_ascii=False, indent=2)
        
        return {"message": "更新成功", "frame_id": frame_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


# ============= 问题管理 =============

@app.get("/questions/{video_id}")
async def get_question_set(video_id: str):
    """获取视频的问题集"""
    questions_path = QUESTIONS_DIR / f"{video_id}_questions.json"
    
    if not questions_path.exists():
        raise HTTPException(status_code=404, detail="问题集不存在")
    
    try:
        with open(questions_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取失败: {str(e)}")


@app.put("/questions/{question_id}/verify")
async def verify_question(
    question_id: str,
    action: str,
    modifications: Optional[Dict] = None,
    notes: str = ""
):
    """校验问题
    
    action: "approved", "modified", "rejected"
    """
    # 查找包含该问题的问题集
    question_file = None
    question_set = None
    
    for qf in QUESTIONS_DIR.glob("*_questions.json"):
        try:
            with open(qf, 'r', encoding='utf-8') as f:
                qs = json.load(f)
                
                # 检查是否包含该问题
                for q in qs.get('questions', []):
                    if q.get('question_id') == question_id:
                        question_file = qf
                        question_set = qs
                        break
                
                if question_file:
                    break
        except:
            continue
    
    if not question_file:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    try:
        # 更新问题
        for q in question_set.get('questions', []):
            if q.get('question_id') == question_id:
                q['verified'] = (action == "approved" or action == "modified")
                q['verification_notes'] = notes
                
                if action == "modified" and modifications:
                    q.update(modifications)
                
                break
        
        # 保存
        with open(question_file, 'w', encoding='utf-8') as f:
            json.dump(question_set, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "message": f"问题已{action}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


# ============= 问卷管理 =============

@app.post("/questionnaire/submit")
async def submit_questionnaire(data: Dict):
    """提交问卷答案"""
    try:
        tester_id = data.get('tester_id')
        video_id = data.get('video_id')
        
        if not tester_id or not video_id:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{video_id}_{tester_id}_{timestamp}.json"
        
        # 添加提交时间
        data['submitted_at'] = datetime.now().isoformat()
        
        # 保存
        output_path = QUESTIONNAIRE_DIR / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": "提交成功",
            "submission_id": filename
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交失败: {str(e)}")


@app.get("/questionnaire/list")
async def list_questionnaire_responses():
    """列出所有问卷回复"""
    responses = []
    
    for resp_file in QUESTIONNAIRE_DIR.glob("*.json"):
        try:
            with open(resp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                responses.append({
                    "filename": resp_file.name,
                    "video_id": data.get("video_id"),
                    "tester_id": data.get("tester_id"),
                    "tester_name": data.get("tester_name"),
                    "submitted_at": data.get("submitted_at"),
                    "num_answers": len(data.get("answers", {}))
                })
        except:
            continue
    
    # 按提交时间排序
    responses.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
    
    return {"responses": responses}


# ============= 关键帧图片 =============

@app.get("/keyframes/{video_id}/{filename}")
async def get_keyframe_image(video_id: str, filename: str):
    """获取关键帧图片"""
    image_path = KEYFRAMES_DIR / video_id / filename
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    
    return FileResponse(image_path)


# ============= 统计信息 =============

@app.get("/stats")
async def get_stats():
    """获取统计信息"""
    # 统计标注
    num_annotations = len(list(ANNOTATIONS_DIR.glob("*.json")))
    
    # 统计问题
    num_questions = 0
    for qf in QUESTIONS_DIR.glob("*_questions.json"):
        try:
            with open(qf, 'r', encoding='utf-8') as f:
                qs = json.load(f)
                num_questions += len(qs.get('questions', []))
        except:
            continue
    
    # 统计问卷回复
    num_responses = len(list(QUESTIONNAIRE_DIR.glob("*.json")))
    
    return {
        "annotations": num_annotations,
        "questions": num_questions,
        "questionnaire_responses": num_responses
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)