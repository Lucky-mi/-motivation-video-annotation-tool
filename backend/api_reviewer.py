# backend/api_reviewer.py
"""
标注审核API服务
支持标注文件的CRUD操作、审核状态管理
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import json
import shutil

# 初始化FastAPI
app = FastAPI(
    title="Annotation Review API",
    description="标注质量审核系统API",
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
BASE_DIR = Path(__file__).parent.parent
ANNOTATIONS_DIR = BASE_DIR / "data" / "annotations_test"
VIDEOS_DIR = BASE_DIR / "data" / "Youtube_videos"
BACKUP_DIR = BASE_DIR / "data" / "annotations_backup"
REVIEW_STATUS_FILE = BASE_DIR / "data" / "review_status.json"

# 确保目录存在
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


# ============= 数据模型 =============

class ReviewStatus(BaseModel):
    status: str  # approved, needs_modification, to_delete
    note: Optional[str] = ""
    timestamp: Optional[str] = None


class SegmentUpdate(BaseModel):
    segment_type: str  # desire_motivation, desire_transition, behavioral_sequence, key_segment_qa
    segment_id: str
    data: Dict[str, Any]


class BatchReviewRequest(BaseModel):
    video_id: str
    segment_ids: List[str]
    status: str
    note: Optional[str] = ""


# ============= 工具函数 =============

def load_review_status() -> Dict:
    """加载审核状态"""
    if REVIEW_STATUS_FILE.exists():
        with open(REVIEW_STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_review_status(status: Dict):
    """保存审核状态"""
    with open(REVIEW_STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def get_video_path(video_id: str, annotation: Dict = None) -> Optional[Path]:
    """获取视频路径"""
    # 尝试多种命名格式
    patterns = [
        f"{video_id}.mp4",
        f"{video_id}.avi",
        f"{video_id}.mov",
        f"{video_id}.mkv"
    ]

    for pattern in patterns:
        video_path = VIDEOS_DIR / pattern
        if video_path.exists():
            return video_path

    # 从annotation中获取路径
    if annotation:
        video_path_str = annotation.get('video_path', '')
        if video_path_str:
            video_path = Path(video_path_str.replace('\\', '/'))
            if video_path.exists():
                return video_path

    return None


def extract_segments(annotation: Dict) -> List[Dict]:
    """从标注中提取所有片段"""
    segments = []

    # desire_motivation_analysis
    for item in annotation.get('desire_motivation_analysis', []):
        temporal = item.get('temporal_scope', {})
        segments.append({
            'type': 'desire_motivation',
            'id': item.get('analysis_id', ''),
            'character_id': item.get('character_id', ''),
            'label': item.get('desire_label', ''),
            'start_seconds': temporal.get('start_seconds', 0),
            'end_seconds': temporal.get('end_seconds', 0),
            'data': item
        })

    # desire_transitions
    for item in annotation.get('desire_transitions', []):
        temporal = item.get('temporal_boundaries', {})
        segments.append({
            'type': 'desire_transition',
            'id': item.get('transition_id', ''),
            'character_id': item.get('character_id', ''),
            'label': f"{item.get('desire_before', {}).get('label', '')} -> {item.get('desire_after', {}).get('label', '')}",
            'start_seconds': temporal.get('onset_timestamp_seconds', 0),
            'end_seconds': temporal.get('offset_timestamp_seconds', 0),
            'data': item
        })

    # behavioral_sequence
    for item in annotation.get('behavioral_sequence', []):
        segments.append({
            'type': 'behavioral_sequence',
            'id': item.get('sequence_id', ''),
            'character_id': item.get('character_id', ''),
            'label': item.get('behavior_category', ''),
            'start_seconds': item.get('timestamp_start_seconds', 0),
            'end_seconds': item.get('timestamp_end_seconds', 0),
            'data': item
        })

    # key_segments_for_qa
    for item in annotation.get('key_segments_for_qa', []):
        segments.append({
            'type': 'key_segment_qa',
            'id': item.get('segment_id', ''),
            'character_id': '',
            'label': item.get('segment_description', '')[:50],
            'start_seconds': item.get('start_timestamp_seconds', 0),
            'end_seconds': item.get('end_timestamp_seconds', 0),
            'data': item
        })

    segments.sort(key=lambda x: x['start_seconds'])
    return segments


# ============= API端点 =============

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Annotation Review API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "annotations_dir": str(ANNOTATIONS_DIR),
        "total_files": len(list(ANNOTATIONS_DIR.glob("*.json")))
    }


# ============= 标注文件管理 =============

@app.get("/annotations")
async def list_annotations(
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0
):
    """列出所有标注文件"""
    annotation_files = sorted(ANNOTATIONS_DIR.glob("*.json"))

    # 过滤
    if search:
        annotation_files = [f for f in annotation_files if search.lower() in f.stem.lower()]

    # 加载审核状态
    review_status = load_review_status()

    results = []
    for f in annotation_files[offset:offset + limit]:
        if f.name == 'annotation_errors.json':
            continue

        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)

            video_id = f.stem
            segments = extract_segments(data)

            # 计算审核进度
            reviewed = sum(1 for s in segments if f"{video_id}_{s['id']}" in review_status)
            approved = sum(1 for s in segments
                          if review_status.get(f"{video_id}_{s['id']}", {}).get('status') == 'approved')

            results.append({
                "file_name": f.name,
                "video_id": video_id,
                "duration_seconds": data.get('duration_seconds', 0),
                "characters_count": len(data.get('characters', [])),
                "segments_count": len(segments),
                "reviewed_count": reviewed,
                "approved_count": approved,
                "annotation_timestamp": data.get('annotation_timestamp', ''),
                "annotator": data.get('annotator', '')
            })
        except Exception as e:
            results.append({
                "file_name": f.name,
                "video_id": f.stem,
                "error": str(e)
            })

    return {
        "total": len(annotation_files),
        "offset": offset,
        "limit": limit,
        "annotations": results
    }


@app.get("/annotations/{video_id}")
async def get_annotation(video_id: str):
    """获取单个标注详情"""
    file_path = ANNOTATIONS_DIR / f"{video_id}.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="标注文件不存在")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 添加片段信息
    segments = extract_segments(data)

    # 添加审核状态
    review_status = load_review_status()
    for seg in segments:
        key = f"{video_id}_{seg['id']}"
        seg['review_status'] = review_status.get(key, None)

    return {
        "annotation": data,
        "segments": segments,
        "video_path": str(get_video_path(video_id, data)) if get_video_path(video_id, data) else None
    }


@app.get("/annotations/{video_id}/segments")
async def get_segments(video_id: str, segment_type: Optional[str] = None):
    """获取标注的所有片段"""
    file_path = ANNOTATIONS_DIR / f"{video_id}.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="标注文件不存在")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    segments = extract_segments(data)

    if segment_type:
        segments = [s for s in segments if s['type'] == segment_type]

    # 添加审核状态
    review_status = load_review_status()
    for seg in segments:
        key = f"{video_id}_{seg['id']}"
        seg['review_status'] = review_status.get(key, None)

    return {"segments": segments}


@app.put("/annotations/{video_id}/segments/{segment_id}")
async def update_segment(video_id: str, segment_id: str, update: SegmentUpdate):
    """更新单个片段"""
    file_path = ANNOTATIONS_DIR / f"{video_id}.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="标注文件不存在")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 备份
    backup_path = BACKUP_DIR / f"{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy(file_path, backup_path)

    # 根据类型更新
    type_to_key = {
        'desire_motivation': ('desire_motivation_analysis', 'analysis_id'),
        'desire_transition': ('desire_transitions', 'transition_id'),
        'behavioral_sequence': ('behavioral_sequence', 'sequence_id'),
        'key_segment_qa': ('key_segments_for_qa', 'segment_id')
    }

    if update.segment_type not in type_to_key:
        raise HTTPException(status_code=400, detail="无效的片段类型")

    array_key, id_field = type_to_key[update.segment_type]

    found = False
    for idx, item in enumerate(data.get(array_key, [])):
        if item.get(id_field) == segment_id:
            data[array_key][idx] = update.data
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="片段不存在")

    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"message": "更新成功", "backup": str(backup_path)}


@app.delete("/annotations/{video_id}/segments/{segment_id}")
async def delete_segment(video_id: str, segment_id: str, segment_type: str):
    """删除单个片段"""
    file_path = ANNOTATIONS_DIR / f"{video_id}.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="标注文件不存在")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 备份
    backup_path = BACKUP_DIR / f"{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy(file_path, backup_path)

    type_to_key = {
        'desire_motivation': ('desire_motivation_analysis', 'analysis_id'),
        'desire_transition': ('desire_transitions', 'transition_id'),
        'behavioral_sequence': ('behavioral_sequence', 'sequence_id'),
        'key_segment_qa': ('key_segments_for_qa', 'segment_id')
    }

    if segment_type not in type_to_key:
        raise HTTPException(status_code=400, detail="无效的片段类型")

    array_key, id_field = type_to_key[segment_type]

    original_len = len(data.get(array_key, []))
    data[array_key] = [item for item in data.get(array_key, []) if item.get(id_field) != segment_id]

    if len(data.get(array_key, [])) == original_len:
        raise HTTPException(status_code=404, detail="片段不存在")

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 删除审核状态
    review_status = load_review_status()
    key = f"{video_id}_{segment_id}"
    if key in review_status:
        del review_status[key]
        save_review_status(review_status)

    return {"message": "删除成功", "backup": str(backup_path)}


# ============= 审核状态管理 =============

@app.get("/review-status")
async def get_all_review_status():
    """获取所有审核状态"""
    return load_review_status()


@app.get("/review-status/{video_id}")
async def get_video_review_status(video_id: str):
    """获取单个视频的审核状态"""
    review_status = load_review_status()
    return {k: v for k, v in review_status.items() if k.startswith(f"{video_id}_")}


@app.put("/review-status/{video_id}/{segment_id}")
async def update_review_status(video_id: str, segment_id: str, status: ReviewStatus):
    """更新审核状态"""
    review_status = load_review_status()
    key = f"{video_id}_{segment_id}"

    review_status[key] = {
        "status": status.status,
        "note": status.note,
        "timestamp": status.timestamp or datetime.now().isoformat()
    }

    save_review_status(review_status)
    return {"message": "更新成功", "key": key}


@app.post("/review-status/batch")
async def batch_update_review_status(request: BatchReviewRequest):
    """批量更新审核状态"""
    review_status = load_review_status()

    for segment_id in request.segment_ids:
        key = f"{request.video_id}_{segment_id}"
        review_status[key] = {
            "status": request.status,
            "note": request.note,
            "timestamp": datetime.now().isoformat()
        }

    save_review_status(review_status)
    return {"message": f"已更新 {len(request.segment_ids)} 个片段"}


@app.delete("/review-status/{video_id}/{segment_id}")
async def delete_review_status(video_id: str, segment_id: str):
    """删除审核状态"""
    review_status = load_review_status()
    key = f"{video_id}_{segment_id}"

    if key in review_status:
        del review_status[key]
        save_review_status(review_status)
        return {"message": "删除成功"}

    raise HTTPException(status_code=404, detail="审核状态不存在")


# ============= 视频访问 =============

@app.get("/videos/{video_id}")
async def get_video(video_id: str):
    """获取视频文件"""
    # 尝试从annotations获取路径
    file_path = ANNOTATIONS_DIR / f"{video_id}.json"
    annotation = None
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            annotation = json.load(f)

    video_path = get_video_path(video_id, annotation)

    if not video_path or not video_path.exists():
        raise HTTPException(status_code=404, detail="视频不存在")

    return FileResponse(video_path, media_type="video/mp4")


# ============= 统计信息 =============

@app.get("/stats")
async def get_stats():
    """获取统计信息"""
    annotation_files = list(ANNOTATIONS_DIR.glob("*.json"))
    review_status = load_review_status()

    total_segments = 0
    total_characters = 0

    for f in annotation_files:
        if f.name == 'annotation_errors.json':
            continue
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
            total_segments += len(extract_segments(data))
            total_characters += len(data.get('characters', []))
        except:
            pass

    approved = sum(1 for v in review_status.values() if v.get('status') == 'approved')
    needs_mod = sum(1 for v in review_status.values() if v.get('status') == 'needs_modification')
    to_delete = sum(1 for v in review_status.values() if v.get('status') == 'to_delete')

    return {
        "total_files": len(annotation_files),
        "total_segments": total_segments,
        "total_characters": total_characters,
        "review_stats": {
            "reviewed": len(review_status),
            "approved": approved,
            "needs_modification": needs_mod,
            "to_delete": to_delete
        }
    }


@app.get("/stats/by-type")
async def get_stats_by_type():
    """按类型获取统计"""
    annotation_files = list(ANNOTATIONS_DIR.glob("*.json"))

    type_stats = {
        'desire_motivation': 0,
        'desire_transition': 0,
        'behavioral_sequence': 0,
        'key_segment_qa': 0
    }

    for f in annotation_files:
        if f.name == 'annotation_errors.json':
            continue
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)

            type_stats['desire_motivation'] += len(data.get('desire_motivation_analysis', []))
            type_stats['desire_transition'] += len(data.get('desire_transitions', []))
            type_stats['behavioral_sequence'] += len(data.get('behavioral_sequence', []))
            type_stats['key_segment_qa'] += len(data.get('key_segments_for_qa', []))
        except:
            pass

    return type_stats


# ============= 导出功能 =============

@app.get("/export/approved")
async def export_approved_annotations():
    """导出所有已批准的片段"""
    review_status = load_review_status()
    approved_keys = [k for k, v in review_status.items() if v.get('status') == 'approved']

    # 按video_id分组
    by_video = {}
    for key in approved_keys:
        parts = key.split('_', 1)
        if len(parts) == 2:
            video_id, segment_id = parts
            if video_id not in by_video:
                by_video[video_id] = []
            by_video[video_id].append(segment_id)

    results = []
    for video_id, segment_ids in by_video.items():
        file_path = ANNOTATIONS_DIR / f"{video_id}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            segments = extract_segments(data)
            approved_segments = [s for s in segments if s['id'] in segment_ids]

            results.append({
                "video_id": video_id,
                "segments": approved_segments
            })

    return {"approved_annotations": results}


# ============= 启动配置 =============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
