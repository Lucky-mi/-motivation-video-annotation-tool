# backend/batch_processor.py
"""
批量视频处理系统 - 支持文件夹导入和队列处理
"""
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Callable
from datetime import datetime
import json
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"  # 等待中
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class BatchTask:
    """批量处理任务"""
    
    def __init__(
        self,
        task_id: str,
        video_path: str,
        video_name: str,
        provider: str = "gemini",
        **kwargs
    ):
        self.task_id = task_id
        self.video_path = video_path
        self.video_name = video_name
        self.provider = provider
        self.status = TaskStatus.PENDING
        self.progress = 0.0
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.kwargs = kwargs
    
    def to_dict(self) -> Dict:
        """转为字典"""
        return {
            "task_id": self.task_id,
            "video_path": self.video_path,
            "video_name": self.video_name,
            "provider": self.provider,
            "status": self.status.value,
            "progress": self.progress,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, max_concurrent: int = 2):
        self.max_concurrent = max_concurrent
        self.tasks: Dict[str, BatchTask] = {}
        self.queue: List[str] = []  # task_id队列
        self.processing: set = set()  # 正在处理的task_id
        self._processing_lock = asyncio.Lock()
    
    def add_task(
        self,
        video_path: str,
        provider: str = "gemini",
        **kwargs
    ) -> str:
        """添加任务到队列"""
        import uuid
        
        task_id = str(uuid.uuid4())
        video_name = Path(video_path).name
        
        task = BatchTask(
            task_id=task_id,
            video_path=video_path,
            video_name=video_name,
            provider=provider,
            **kwargs
        )
        
        self.tasks[task_id] = task
        self.queue.append(task_id)
        
        print(f"📝 添加任务: {video_name} (ID: {task_id})")
        return task_id
    
    def add_folder(
        self,
        folder_path: str,
        provider: str = "gemini",
        recursive: bool = False,
        **kwargs
    ) -> List[str]:
        """批量添加文件夹中的所有视频"""
        folder = Path(folder_path)
        
        if not folder.exists():
            raise ValueError(f"文件夹不存在: {folder_path}")
        
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
        
        # 扫描视频文件
        if recursive:
            video_files = [
                f for f in folder.rglob('*')
                if f.suffix.lower() in video_extensions
            ]
        else:
            video_files = [
                f for f in folder.glob('*')
                if f.suffix.lower() in video_extensions
            ]
        
        print(f"📂 扫描文件夹: {folder_path}")
        print(f"   找到 {len(video_files)} 个视频文件")
        
        task_ids = []
        for video_file in video_files:
            task_id = self.add_task(str(video_file), provider, **kwargs)
            task_ids.append(task_id)
        
        return task_ids
    
    async def process_queue(
        self,
        processor_func: Callable,
        progress_callback: Optional[Callable] = None
    ):
        """处理队列"""
        
        while self.queue or self.processing:
            async with self._processing_lock:
                # 启动新任务(不超过并发限制)
                while len(self.processing) < self.max_concurrent and self.queue:
                    task_id = self.queue.pop(0)
                    task = self.tasks[task_id]
                    
                    self.processing.add(task_id)
                    task.status = TaskStatus.PROCESSING
                    task.started_at = datetime.now()
                    
                    # 异步处理
                    asyncio.create_task(
                        self._process_task(task, processor_func, progress_callback)
                    )
            
            await asyncio.sleep(0.5)
    
    async def _process_task(
        self,
        task: BatchTask,
        processor_func: Callable,
        progress_callback: Optional[Callable]
    ):
        """处理单个任务"""
        try:
            print(f"\n🚀 开始处理: {task.video_name}")
            
            # 调用处理函数
            result = await asyncio.to_thread(
                processor_func,
                task.video_path,
                task.provider,
                **task.kwargs
            )
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.progress = 1.0
            task.completed_at = datetime.now()
            
            print(f"✅ 完成: {task.video_name}")
            
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            print(f"❌ 失败: {task.video_name} - {e}")
        
        finally:
            self.processing.remove(task.task_id)
            
            if progress_callback:
                progress_callback(task)
    
    def get_task(self, task_id: str) -> Optional[BatchTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务"""
        return [task.to_dict() for task in self.tasks.values()]
    
    def get_status_summary(self) -> Dict:
        """获取状态摘要"""
        status_count = {status: 0 for status in TaskStatus}
        
        for task in self.tasks.values():
            status_count[task.status] += 1
        
        return {
            "total": len(self.tasks),
            "pending": status_count[TaskStatus.PENDING],
            "processing": status_count[TaskStatus.PROCESSING],
            "completed": status_count[TaskStatus.COMPLETED],
            "failed": status_count[TaskStatus.FAILED],
            "cancelled": status_count[TaskStatus.CANCELLED]
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        
        if not task:
            return False
        
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            if task_id in self.queue:
                self.queue.remove(task_id)
            return True
        
        return False
    
    def clear_completed(self):
        """清除已完成的任务"""
        completed_ids = [
            task_id for task_id, task in self.tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        
        for task_id in completed_ids:
            del self.tasks[task_id]
        
        print(f"🗑️ 清除了 {len(completed_ids)} 个已完成任务")


# 全局批量处理器实例
batch_processor = BatchProcessor(max_concurrent=2)