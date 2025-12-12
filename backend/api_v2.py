# backend/api_v2.py
"""
改进版API - 支持多模型、批量处理、用户管理
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Optional
import uuid
import shutil
from datetime import datetime
from dotenv import load_dotenv
import os
import json

# 加载环境变量
load_dotenv()

from backend.models import *
from backend.ai_providers.base_provider import AIProviderFactory
from backend.ai_providers import GeminiProvider, OpenAIProvider
from backend.batch_processor import batch_processor, TaskStatus
from backend.user_manager import user_manager
from config.config import config
from backend.models_questions import *
from backend.question_generator import QuestionGenerator
from backend.prompt_loader import PromptLoader
from fastapi import Query
from backend.downloader import VideoDownloader
from backend.content_filter import ContentFilter
from fastapi import BackgroundTasks
# 初始化FastAPI
app = FastAPI(
    title="Video Motivation Annotation API v2",
    description="增强版AI辅助视频标注系统",
    version="2.0.0"
)

# CORS
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

for d in [VIDEOS_DIR, KEYFRAMES_DIR, ANNOTATIONS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ============= 依赖注入 =============

async def get_current_user(authorization: Optional[str] = Header(None)):
    """获取当前用户(可选)"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    user = user_manager.validate_token(token)
    
    return user


# ============= 基础端点 =============

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Video Motivation Annotation API v2",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


# ============= 用户管理 =============

@app.post("/auth/register")
async def register(username: str, email: str, password: str):
    """用户注册"""
    try:
        user = user_manager.register(username, email, password)
        return {"message": "注册成功", "user": user.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login")
async def login(username: str, password: str):
    """用户登录"""
    try:
        token = user_manager.login(username, password)
        return {"message": "登录成功", "token": token}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/auth/logout")
async def logout(authorization: str = Header(...)):
    """用户登出"""
    token = authorization.replace("Bearer ", "")
    user_manager.logout(token)
    return {"message": "登出成功"}


@app.get("/auth/me")
async def get_current_user_info(user = Depends(get_current_user)):
    """获取当前用户信息"""
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    return user.to_dict()


@app.put("/auth/settings")
async def update_settings(settings: dict, user = Depends(get_current_user)):
    """更新用户设置"""
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    
    user_manager.update_settings(user.user_id, settings)
    return {"message": "设置已更新"}


# ============= AI Provider管理 =============

@app.get("/providers/list")
async def list_providers():
    """列出所有可用的AI Provider"""
    providers = AIProviderFactory.list_providers()
    
    result = []
    for provider_name in providers:
        try:
            # 检查API key是否配置
            api_key = config.get_api_key(provider_name)
            configured = bool(api_key)
            
            result.append({
                "name": provider_name,
                "display_name": provider_name.title(),
                "configured": configured,
                "available": configured
            })
        except:
            result.append({
                "name": provider_name,
                "display_name": provider_name.title(),
                "configured": False,
                "available": False
            })
    
    return {"providers": result}


@app.post("/providers/{provider_name}/test")
async def test_provider(provider_name: str):
    """测试Provider连接"""
    try:
        api_key = config.get_api_key(provider_name)
        if not api_key:
            raise HTTPException(status_code=400, detail=f"{provider_name} API Key未配置")
        
        provider = AIProviderFactory.create_provider(provider_name, api_key=api_key)
        success = provider.test_connection()
        
        if success:
            return {"message": f"{provider_name}连接成功", "available": True}
        else:
            return {"message": f"{provider_name}连接失败", "available": False}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= 视频管理(支持批量) =============

@app.get("/videos/list")
async def list_videos():
    """列出所有视频"""
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


@app.post("/videos/upload")
async def upload_video(file: UploadFile = File(...), user = Depends(get_current_user)):
    """上传单个视频"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    video_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    video_filename = f"{video_id}{file_extension}"
    video_path = VIDEOS_DIR / video_filename

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "video_id": video_id,
        "video_name": file.filename,
        "video_path": str(video_path),
        "size": video_path.stat().st_size
    }

@app.post("/videos/import-link")
async def import_video_from_link(
    url: str, 
    auto_filter: bool = True,
    user = Depends(get_current_user)
):
    """从链接导入视频"""
    downloader = VideoDownloader()
    content_filter = ContentFilter()
    
    try:
        # 1. 下载
        print(f"📥 接到下载任务: {url}")
        video_info = downloader.download_from_url(url)
        video_path = video_info['video_path']
        
        # 2. AI 筛选 (可选)
        if auto_filter:
            filter_result = content_filter.check_video_content(video_path)
            if not filter_result.get('pass', False):
                Path(video_path).unlink(missing_ok=True) # 删掉不合格的
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"未通过筛选: {filter_result.get('reason')}"}
                )
        
        return {"success": True, "message": "导入成功", "video": video_info}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
async def _background_mining_task(keyword: str, limit: int, auto_filter: bool):
    """后台执行的挖掘任务逻辑"""
    print(f"🚀 [后台任务] 开始挖掘关键词: {keyword}")
    
    downloader = VideoDownloader()
    content_filter = ContentFilter() # 你的AI看门人
    
    # 1. 搜索
    candidates = downloader.search_videos(keyword, limit)
    print(f"🔎 [后台任务] 找到 {len(candidates)} 个潜在视频")
    
    success_count = 0
    
    # 2. 循环下载并筛选
    for i, item in enumerate(candidates):
        url = item['url']
        title = item['title']
        print(f"  👉 [{i+1}/{len(candidates)}] 处理: {title}")
        
        try:
            # 下载
            video_info = downloader.download_from_url(url)
            video_path = video_info['video_path']
            
            # AI 筛选
            if auto_filter:
                filter_result = content_filter.check_video_content(video_path)
                
                if not filter_result.get('pass', False):
                    print(f"  🗑️ [AI拒绝] {filter_result.get('reason')}")
                    # 既然不合格，就删掉文件省空间
                    Path(video_path).unlink(missing_ok=True)
                    continue # 跳过，处理下一个
                
                print(f"  ✅ [AI通过] {filter_result.get('category')}")
            
            # 如果到了这一步，说明是好视频（或者没开筛选）
            success_count += 1
            # 这里其实已经入库了（文件在 data/videos 里），
            # 如果你做了数据库，这里应该写入数据库。
            
        except Exception as e:
            print(f"  ❌ 处理出错: {e}")
            continue

    print(f"🏁 [后台任务] 挖掘结束! 成功入库: {success_count}/{len(candidates)}")


@app.post("/videos/auto-mine")
async def auto_mine_videos(
    keyword: str, 
    limit: int = 5, 
    auto_filter: bool = True,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    全自动挖掘机接口
    输入关键词 -> 后台搜索 -> 下载 -> AI筛选 -> 入库
    """
    # 将耗时任务放入后台运行，立即返回响应
    background_tasks.add_task(_background_mining_task, keyword, limit, auto_filter)
    
    return {
        "message": f"挖掘任务已启动! 关键词: {keyword}",
        "note": "请关注后端控制台日志查看进度"
    }
@app.post("/videos/upload-folder")
async def upload_folder(
    folder_path: str,
    user = Depends(get_current_user)
):
    """
    添加文件夹中的所有视频到处理队列
    注意: 需要本地文件系统访问权限
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise HTTPException(status_code=404, detail="文件夹不存在")
    
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
    video_files = [
        f for f in folder.glob('*')
        if f.suffix.lower() in video_extensions
    ]
    
    if not video_files:
        raise HTTPException(status_code=404, detail="文件夹中没有视频文件")
    
    uploaded = []
    for video_file in video_files:
        video_id = str(uuid.uuid4())
        new_path = VIDEOS_DIR / f"{video_id}{video_file.suffix}"
        shutil.copy(video_file, new_path)
        
        uploaded.append({
            "video_id": video_id,
            "video_name": video_file.name,
            "video_path": str(new_path),
            "size": new_path.stat().st_size
        })
    
    return {
        "message": f"批量上传成功",
        "count": len(uploaded),
        "videos": uploaded
    }


# ============= 批量处理 =============

@app.post("/batch/add-task")
async def add_batch_task(
    video_path: str,
    provider: str = "gemini",
    user = Depends(get_current_user)
):
    """添加单个任务到批量处理队列"""
    task_id = batch_processor.add_task(video_path, provider)
    return {"task_id": task_id}


@app.post("/batch/add-folder")
async def add_batch_folder(
    folder_path: str,
    provider: str = "gemini",
    recursive: bool = False,
    user = Depends(get_current_user)
):
    """添加文件夹到批量处理队列"""
    try:
        task_ids = batch_processor.add_folder(folder_path, provider, recursive)
        return {
            "message": f"已添加 {len(task_ids)} 个任务",
            "task_ids": task_ids
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/batch/start")
async def start_batch_processing():
    """开始批量处理"""
    import asyncio
    
    # 定义处理函数
    def process_video(video_path: str, provider_name: str, **kwargs):
        api_key = config.get_api_key(provider_name)
        provider = AIProviderFactory.create_provider(provider_name, api_key=api_key)
        
        result = provider.analyze_video_comprehensive(
            video_path,
            analyze_actions=True,
            analyze_motivations=True
        )
        
        return result
    
    # 启动异步处理
    asyncio.create_task(
        batch_processor.process_queue(process_video)
    )
    
    return {"message": "批量处理已启动"}


@app.get("/batch/status")
async def get_batch_status():
    """获取批量处理状态"""
    summary = batch_processor.get_status_summary()
    tasks = batch_processor.get_all_tasks()
    
    return {
        "summary": summary,
        "tasks": tasks
    }


@app.get("/batch/task/{task_id}")
async def get_batch_task(task_id: str):
    """获取单个任务状态"""
    task = batch_processor.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task.to_dict()


@app.delete("/batch/task/{task_id}")
async def cancel_batch_task(task_id: str):
    """取消任务"""
    success = batch_processor.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="无法取消任务")
    
    return {"message": "任务已取消"}


# ============= AI分析(改进版) =============

@app.post("/analyze/video", response_model=AIAnalysisResponse)
async def analyze_video(
    request: AIAnalysisRequest,
    user = Depends(get_current_user)
):
    """AI分析视频 - 支持多Provider"""
    
    video_path = Path(request.video_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    # 获取Provider
    provider_name = request.provider if hasattr(request, 'provider') else 'gemini'
    api_key = config.get_api_key(provider_name)
    
    if not api_key:
        raise HTTPException(status_code=400, detail=f"{provider_name} API Key未配置")
    
    try:
        provider = AIProviderFactory.create_provider(provider_name, api_key=api_key)
        
        # 分析视频
        analysis = provider.analyze_video_comprehensive(
            str(video_path),
            analyze_actions=request.analyze_actions,
            analyze_motivations=request.suggest_motivations
        )
        
        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])
        
        # 提取关键帧
        timestamps = analysis.get("suggested_keyframe_timestamps", [])
        extracted_frames = provider.extract_keyframes(
            str(video_path),
            timestamps,
            KEYFRAMES_DIR
        )

        # 构建响应数据
        video_id = video_path.stem
        key_moments = analysis.get("key_moments", [])

        # 转换为KeyframeAnnotation格式
        keyframes = []
        for idx, moment in enumerate(key_moments):
            # 找到对应的帧图片
            frame_path = ""
            timestamp = moment.get("timestamp_seconds", 0)
            for ts, fp in extracted_frames:
                if abs(ts - timestamp) < 0.1:  # 允许0.1秒误差
                    frame_path = fp
                    break

            # 构建action和motivation - 使用更宽松的类型转换
            try:
                # 安全获取timestamp
                ts = moment.get("timestamp_seconds", timestamp)
                if isinstance(ts, str):
                    try:
                        ts = float(ts)
                    except:
                        ts = timestamp

                # 安全获取confidence
                conf = moment.get("confidence", 0.5)
                if isinstance(conf, str):
                    try:
                        conf = float(conf)
                    except:
                        conf = 0.5
                conf = max(0.0, min(1.0, conf))  # 限制在0-1范围

                # 安全获取列表字段
                objects = moment.get("objects", [])
                if isinstance(objects, str):
                    objects = [objects]
                elif not isinstance(objects, list):
                    objects = []

                characters = moment.get("characters", [])
                if isinstance(characters, str):
                    characters = [characters]
                elif not isinstance(characters, list):
                    characters = []

                action = KeyframeAction(
                    timestamp=ts,
                    timestamp_formatted=moment.get("timestamp", "00:00"),
                    action_description=str(moment.get("action_description", "")),
                    visual_context=str(moment.get("visual_context", "")),
                    objects=objects,
                    characters=characters,
                    scene=str(moment.get("scene", moment.get("scene_description", ""))),
                    confidence=conf
                )

                # 安全获取desire_category
                desire_cat = moment.get("desire_category", moment.get("desire_type", "other"))
                valid_desires = ["physiological", "safety", "belonging", "esteem", "self_actualization", "other"]
                if desire_cat not in valid_desires:
                    desire_cat = "other"

                # 安全获取motivation_type
                mot_type = moment.get("motivation_type", "mixed")
                valid_mot_types = ["intrinsic", "extrinsic", "mixed"]
                if mot_type not in valid_mot_types:
                    mot_type = "mixed"

                # 安全获取implicit_level
                impl_level = moment.get("implicit_level", 3)
                if isinstance(impl_level, str):
                    try:
                        impl_level = int(impl_level)
                    except:
                        impl_level = 3
                impl_level = max(1, min(5, impl_level))  # 限制在1-5范围

                # 安全获取visual_cues
                visual_cues = moment.get("visual_cues", [])
                if isinstance(visual_cues, str):
                    visual_cues = [visual_cues]
                elif not isinstance(visual_cues, list):
                    visual_cues = []

                motivation = MotivationAnnotation(
                    explicit_motivation=str(moment.get("explicit_motivation", "")),
                    implicit_desire=str(moment.get("implicit_desire", "")),
                    desire_category=desire_cat,
                    motivation_type=mot_type,
                    implicit_level=impl_level,
                    reasoning=str(moment.get("reasoning", "")),
                    visual_cues=visual_cues,
                    confidence=conf
                )
            except Exception as e:
                # 如果构建失败，使用最小化默认值
                print(f"⚠️ 解析关键帧数据时出错: {e}，使用默认值")
                action = KeyframeAction(
                    timestamp=timestamp,
                    timestamp_formatted="00:00",
                    action_description="",
                    confidence=0.5
                )
                motivation = MotivationAnnotation(
                    explicit_motivation="",
                    implicit_desire="",
                    confidence=0.5
                )

            keyframe = KeyframeAnnotation(
                frame_id=idx,
                frame_path=frame_path,
                action=action,
                motivation=motivation
            )
            keyframes.append(keyframe)

        # 转换transitions
        transitions = []
        for t in analysis.get("transitions", []):
            transition = MotivationTransition(
                from_timestamp=t.get("from_timestamp", 0),
                to_timestamp=t.get("to_timestamp", 0),
                trigger_event=t.get("trigger_event", ""),
                motivation_before=t.get("motivation_before", ""),
                motivation_after=t.get("motivation_after", ""),
                desire_before=t.get("desire_before", ""),
                desire_after=t.get("desire_after", ""),
                transition_type=t.get("transition_type", ""),
                intensity=t.get("intensity", 3)
            )
            transitions.append(transition)

        # 构建响应
        response = AIAnalysisResponse(
            video_id=video_id,
            keyframes=keyframes,
            suggested_transitions=transitions,
            overall_summary=analysis.get("overall_narrative", ""),
            processing_time=analysis.get("processing_time", 0.0),
            model_used=analysis.get("model_used", provider_name)
        )

        # 保存标注到文件
        annotation_data = VideoAnnotation(
            video_id=video_id,
            video_name=video_path.name,
            video_path=str(video_path),
            keyframes=keyframes,
            transitions=transitions,
            overall_trajectory=analysis.get("overall_narrative", ""),
            total_frames=len(keyframes),
            annotated_frames=len(keyframes),
            ai_generated_frames=len(keyframes)
        )

        annotation_file = ANNOTATIONS_DIR / f"{video_id}.json"
        with open(annotation_file, 'w', encoding='utf-8') as f:
            json.dump(annotation_data.dict(), f, ensure_ascii=False, indent=2)

        # 添加到用户历史
        if user:
            user_manager.add_annotation_to_history(
                user.user_id,
                video_id,
                video_path.name,
                str(annotation_file)
            )

        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= 标注管理 =============

@app.get("/annotations/list")
async def list_annotations():
    """列出所有标注文件"""
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


@app.post("/annotations/{video_id}/keyframe/{frame_id}")
async def update_keyframe_annotation(
    video_id: str,
    frame_id: int,
    annotation_data: Dict = None
):
    """更新单个关键帧的标注"""
    annotation_file = ANNOTATIONS_DIR / f"{video_id}.json"

    if not annotation_file.exists():
        raise HTTPException(status_code=404, detail=f"标注文件不存在: {video_id}")

    # 读取现有标注
    with open(annotation_file, 'r', encoding='utf-8') as f:
        video_annotation = json.load(f)

    # 查找并更新指定的关键帧
    keyframes = video_annotation.get('keyframes', [])

    updated = False
    for i, kf in enumerate(keyframes):
        if kf.get('frame_id') == frame_id:
            # 更新标注数据
            if annotation_data:
                # 更新 action 数据
                if 'action' in annotation_data:
                    kf['action'].update(annotation_data['action'])

                # 更新 motivation 数据
                if 'motivation' in annotation_data:
                    kf['motivation'].update(annotation_data['motivation'])

                # 更新状态为已修改
                kf['motivation']['status'] = 'human_modified'

            keyframes[i] = kf
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail=f"找不到帧ID: {frame_id}")

    # 更新时间戳
    from datetime import datetime
    video_annotation['last_modified'] = datetime.now().isoformat()
    video_annotation['keyframes'] = keyframes

    # 保存
    with open(annotation_file, 'w', encoding='utf-8') as f:
        json.dump(video_annotation, f, ensure_ascii=False, indent=2)

    return {"success": True, "message": f"关键帧 {frame_id} 已更新"}


# ============= 标注检查界面(支持连续查看) =============

@app.get("/review/list")
async def list_annotations_for_review(user = Depends(get_current_user)):
    """列出所有待检查的标注"""
    annotations = []

    for ann_file in ANNOTATIONS_DIR.glob("*.json"):
        import json
        with open(ann_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

            annotations.append({
                "video_id": ann_file.stem,
                "video_name": data.get("video_name", ""),
                "annotation_path": str(ann_file),
                "status": data.get("status", ""),
                "annotated_frames": data.get("annotated_frames", 0),
                "total_frames": data.get("total_frames", 0),
                "last_modified": data.get("last_modified", "")
            })

    # 按时间排序
    annotations.sort(key=lambda x: x['last_modified'], reverse=True)

    return {"annotations": annotations, "total": len(annotations)}


@app.get("/review/{video_id}/next")
async def get_next_annotation(video_id: str):
    """获取下一个待检查的标注"""
    all_files = sorted(ANNOTATIONS_DIR.glob("*.json"))
    
    current_idx = None
    for idx, f in enumerate(all_files):
        if f.stem == video_id:
            current_idx = idx
            break
    
    if current_idx is None or current_idx >= len(all_files) - 1:
        return {"next_video_id": None, "message": "已是最后一个"}
    
    next_file = all_files[current_idx + 1]
    return {"next_video_id": next_file.stem}


@app.get("/review/{video_id}/previous")
async def get_previous_annotation(video_id: str):
    """获取上一个待检查的标注"""
    all_files = sorted(ANNOTATIONS_DIR.glob("*.json"))
    
    current_idx = None
    for idx, f in enumerate(all_files):
        if f.stem == video_id:
            current_idx = idx
            break
    
    if current_idx is None or current_idx == 0:
        return {"previous_video_id": None, "message": "已是第一个"}
    
    previous_file = all_files[current_idx - 1]
    return {"previous_video_id": previous_file.stem}


# ============= 视频重命名 =============

@app.post("/videos/{video_id}/rename")
async def rename_video_by_theme(video_id: str, user = Depends(get_current_user)):
    """根据标注主题重命名视频"""
    from backend.ai_providers.prompt_templates import PromptTemplates
    
    # 加载标注
    annotation_path = ANNOTATIONS_DIR / f"{video_id}.json"
    if not annotation_path.exists():
        raise HTTPException(status_code=404, detail="标注不存在")
    
    import json
    with open(annotation_path, 'r', encoding='utf-8') as f:
        annotation_data = json.load(f)
    
    # 使用AI提取主题
    provider_name = 'gemini'  # 默认使用gemini
    api_key = config.get_api_key(provider_name)
    
    if not api_key:
        raise HTTPException(status_code=400, detail="AI Provider未配置")
    
    provider = AIProviderFactory.create_provider(provider_name, api_key=api_key)

    # 生成prompt
    prompt = PromptTemplates.get_theme_extraction_prompt(annotation_data)

    try:
        # 调用AI生成主题
        if hasattr(provider, 'model'):
            response = provider.model.generate_content(prompt)
            result_text = response.text

            # 解析JSON
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                json_str = result_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = result_text

            theme_data = json.loads(json_str)

            # 可选：实际重命名文件
            # suggested_filename = theme_data.get('suggested_filename', '')
            # if suggested_filename:
            #     old_video_path = Path(annotation_data.get('video_path', ''))
            #     if old_video_path.exists():
            #         new_video_path = old_video_path.parent / (suggested_filename + old_video_path.suffix)
            #         old_video_path.rename(new_video_path)

            return {
                "theme_keyword": theme_data.get('theme_keyword', ''),
                "suggested_filename": theme_data.get('suggested_filename', ''),
                "explanation": theme_data.get('explanation', ''),
                "original_name": annotation_data.get('video_name', '')
            }
        else:
            raise HTTPException(status_code=500, detail="Provider不支持主题提取")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"主题提取失败: {str(e)}")


# ============= 获取标注数据 =============

@app.get("/annotations/{video_id}")
async def get_annotation(video_id: str):
    """获取视频标注数据"""
    annotation_path = ANNOTATIONS_DIR / f"{video_id}.json"

    if not annotation_path.exists():
        raise HTTPException(status_code=404, detail="标注不存在")

    try:
        with open(annotation_path, 'r', encoding='utf-8') as f:
            annotation_data = json.load(f)
        return annotation_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取失败: {str(e)}")


@app.get("/keyframes/{video_id}/{filename}")
async def get_keyframe_image(video_id: str, filename: str):
    """获取关键帧图片"""
    image_path = KEYFRAMES_DIR / video_id / filename

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")

    return FileResponse(image_path)



# ============= 问题生成 =============

# 全局prompt加载器
prompt_loader = PromptLoader()

@app.post("/questions/generate/{video_id}")
async def generate_questions(
    video_id: str,
    num_questions: int = Query(default=10, ge=1, le=50),
    provider: str = Query(default="gemini")
):
    """为视频生成问题集"""
    try:
        # 加载标注数据
        annotation_path = ANNOTATIONS_DIR / f"{video_id}.json"
        if not annotation_path.exists():
            raise HTTPException(status_code=404, detail="标注数据不存在")
            
        with open(annotation_path, 'r', encoding='utf-8') as f:
            annotation_data = VideoAnnotation(**json.load(f))

        # 获取AI provider
        api_key = config.get_api_key(provider)
        if not api_key:
            raise HTTPException(status_code=400, detail=f"{provider} API Key未配置")
            
        ai_provider = AIProviderFactory.create_provider(provider, api_key=api_key)

        # 生成问题
        generator = QuestionGenerator(ai_provider, prompt_loader)
        question_set = generator.generate_questions_for_video(
            video_id,
            annotation_data,
            num_questions
        )

        # 保存问题集
        questions_dir = Path("data/questions")
        questions_dir.mkdir(exist_ok=True, parents=True)
        output_path = questions_dir / f"{video_id}_questions.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(question_set.dict(), f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "question_set_id": question_set.question_set_id,
            "total_questions": question_set.total_questions,
            "message": f"成功生成{question_set.total_questions}个问题"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/questions/{video_id}")
async def get_question_set(video_id: str):
    """获取视频的问题集"""
    questions_path = Path("data/questions") / f"{video_id}_questions.json"
    
    if not questions_path.exists():
        raise HTTPException(status_code=404, detail="问题集不存在")
        
    with open(questions_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.put("/questions/{question_id}/verify")
async def verify_question(
    question_id: str,
    action: str,  # "approved", "modified", "rejected"
    modifications: dict = None,
    notes: str = ""
):
    """提交问题校验 (TODO: 实现具体逻辑)"""
    # 这里需要遍历所有问题集找到对应的问题，或者建立索引
    # 暂时只返回成功
    return {"success": True, "message": "校验已提交(Mock)"}

@app.post("/prompts/reload")
async def reload_prompts():
    """重新加载prompt配置(热加载)"""
    try:
        prompt_loader.reload()
        return {"success": True, "message": "Prompt配置已重新加载"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prompts/list")
async def list_prompts():
    """列出所有可用的prompt模板"""
    return {
        "prompts": list(prompt_loader.prompts.keys()),
        "config_path": str(prompt_loader.config_path)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)