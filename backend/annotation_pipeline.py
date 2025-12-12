"""
Annotation Pipeline with Quality Pre-screening
二阶段标注流程：质量预审 → 完整标注
Author: Desire-VQA Team
Version: 1.0
"""

import json
import cv2
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime
import asyncio
import logging

from .prompt_loader import PromptLoader

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnnotationPipeline:
    """
    两阶段标注管道：
    Stage 1: 质量预审 (Quality Assessment) - 快速评估视频是否适合标注
    Stage 2: 完整标注 (Full Annotation) - 对通过预审的视频进行完整ToM标注
    """

    def __init__(
        self,
        output_dir: str = "data/annotations",
        rejected_log_path: Optional[str] = None,
        borderline_log_path: Optional[str] = None,
        quality_threshold: int = 65,
        auto_reject_threshold: int = 55
    ):
        """
        初始化标注管道

        Args:
            output_dir: 标注输出目录
            rejected_log_path: 被拒绝视频日志路径
            borderline_log_path: 边界情况视频日志路径（需人工复审）
            quality_threshold: 质量分数阈值（≥此值才进行完整标注）
            auto_reject_threshold: 自动拒绝阈值（<此值自动拒绝）
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 日志文件路径
        self.rejected_log_path = Path(rejected_log_path) if rejected_log_path else self.output_dir / "rejected_videos.json"
        self.borderline_log_path = Path(borderline_log_path) if borderline_log_path else self.output_dir / "borderline_videos.json"

        # 阈值配置
        self.quality_threshold = quality_threshold
        self.auto_reject_threshold = auto_reject_threshold

        # 加载Prompt模板
        self.prompt_loader = PromptLoader("backend/prompts/annotation_prompts.yaml")

        # 初始化日志文件
        self._init_log_files()

        logger.info(f"AnnotationPipeline initialized:")
        logger.info(f"  - Output dir: {self.output_dir}")
        logger.info(f"  - Quality threshold: {self.quality_threshold}")
        logger.info(f"  - Auto-reject threshold: {self.auto_reject_threshold}")

    def _init_log_files(self):
        """初始化日志文件结构"""
        for log_path in [self.rejected_log_path, self.borderline_log_path]:
            if not log_path.exists():
                initial_data = {
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "last_updated": datetime.now().isoformat(),
                        "total_count": 0,
                        "log_type": "rejected" if "rejected" in log_path.name else "borderline"
                    },
                    "statistics": {},
                    "videos": []
                }
                with open(log_path, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)

    def assess_video_quality(
        self,
        video_path: str,
        ai_provider,  # AI提供者实例（Gemini/OpenAI等）
        save_result: bool = True
    ) -> Dict[str, Any]:
        """
        阶段1：质量预审

        Args:
            video_path: 视频文件路径
            ai_provider: AI提供者实例，需要有analyze_video方法
            save_result: 是否保存评估结果

        Returns:
            质量评估结果字典，包含:
            - is_suitable: bool
            - overall_score: int
            - criteria_scores: dict
            - recommended_action: str
            - 等
        """
        logger.info(f"Stage 1: Quality Assessment for {video_path}")

        # 获取视频元数据
        video_metadata = self._get_video_metadata(video_path)

        # 加载质量评估prompt
        quality_prompt = self.prompt_loader.get_prompt("quality_assessment")

        # 调用AI进行质量评估
        try:
            assessment_result = ai_provider.analyze_video(
                video_path=video_path,
                prompt=quality_prompt
            )

            # 解析JSON结果
            if isinstance(assessment_result, str):
                assessment_result = self._extract_json(assessment_result)

            # 添加元数据
            assessment_result['video_path'] = str(video_path)
            assessment_result['video_metadata'] = video_metadata
            assessment_result['assessed_at'] = datetime.now().isoformat()

            # 保存结果
            if save_result:
                self._save_quality_assessment(video_path, assessment_result)

            logger.info(f"  ✓ Overall Score: {assessment_result.get('overall_score', 'N/A')}/100")
            logger.info(f"  ✓ Recommended Action: {assessment_result.get('recommended_action', 'N/A')}")

            return assessment_result

        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            raise

    def annotate_with_quality_check(
        self,
        video_path: str,
        ai_provider,
        force_annotate: bool = False
    ) -> Dict[str, Any]:
        """
        完整的两阶段标注流程

        Args:
            video_path: 视频文件路径
            ai_provider: AI提供者实例
            force_annotate: 是否强制标注（跳过质量检查）

        Returns:
            标注结果字典，包含:
            - status: 'completed' | 'rejected' | 'borderline'
            - quality_assessment: 质量评估结果（如果执行了）
            - annotation: 完整标注结果（如果status='completed'）
            - rejection_info: 拒绝信息（如果被拒绝）
        """
        result = {
            'video_path': str(video_path),
            'pipeline_version': '1.0',
            'timestamp': datetime.now().isoformat()
        }

        # 阶段1: 质量预审
        if not force_annotate:
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting 2-Stage Annotation Pipeline")
            logger.info(f"Video: {Path(video_path).name}")
            logger.info(f"{'='*60}")

            quality_result = self.assess_video_quality(
                video_path=video_path,
                ai_provider=ai_provider,
                save_result=True
            )

            result['quality_assessment'] = quality_result

            # 决策逻辑
            action = quality_result.get('recommended_action', 'REJECT_LOW_QUALITY')
            overall_score = quality_result.get('overall_score', 0)
            is_suitable = quality_result.get('is_suitable', False)

            # 情况1: 明确拒绝
            if action in ['REJECT_LOW_QUALITY', 'REJECT_INAPPROPRIATE'] or overall_score < self.auto_reject_threshold:
                logger.warning(f"  ✗ Video REJECTED (score: {overall_score})")
                self._log_rejection(video_path, quality_result, log_type='rejected')
                result['status'] = 'rejected'
                result['rejection_info'] = {
                    'reasons': quality_result.get('rejection_reasons', []),
                    'overall_score': overall_score,
                    'action': action
                }
                return result

            # 情况2: 边界情况（需人工复审）
            elif action == 'BORDERLINE_MANUAL_REVIEW':
                logger.info(f"  ⚠ Video marked for MANUAL REVIEW (score: {overall_score})")
                self._log_rejection(video_path, quality_result, log_type='borderline')
                result['status'] = 'borderline'
                result['review_notes'] = quality_result.get('reviewer_notes', '')
                return result

            # 情况3: 通过预审，进入完整标注
            elif action == 'PROCEED_FULL_ANNOTATION' and is_suitable:
                logger.info(f"  ✓ Quality check PASSED (score: {overall_score})")
                logger.info(f"\nStage 2: Proceeding to Full Annotation...")
            else:
                logger.warning(f"  ? Unexpected assessment result, rejecting by default")
                self._log_rejection(video_path, quality_result, log_type='rejected')
                result['status'] = 'rejected'
                return result
        else:
            logger.info(f"Skipping quality check (force_annotate=True)")

        # 阶段2: 完整标注
        try:
            annotation = self._perform_full_annotation(
                video_path=video_path,
                ai_provider=ai_provider
            )

            result['status'] = 'completed'
            result['annotation'] = annotation

            # 保存标注结果
            self._save_annotation(video_path, annotation)

            logger.info(f"  ✓ Full annotation COMPLETED")
            logger.info(f"{'='*60}\n")

            return result

        except Exception as e:
            logger.error(f"Full annotation failed: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
            return result

    def _perform_full_annotation(
        self,
        video_path: str,
        ai_provider
    ) -> Dict[str, Any]:
        """
        执行完整的ToM标注（阶段2）

        Args:
            video_path: 视频路径
            ai_provider: AI提供者实例

        Returns:
            完整标注结果
        """
        # 加载完整标注prompt
        annotation_prompt = self.prompt_loader.get_prompt("annotation_v5")

        # 调用AI进行完整标注
        annotation_result = ai_provider.analyze_video(
            video_path=video_path,
            prompt=annotation_prompt
        )

        # 解析JSON结果
        if isinstance(annotation_result, str):
            annotation_result = self._extract_json(annotation_result)

        return annotation_result

    def _log_rejection(
        self,
        video_path: str,
        quality_result: Dict[str, Any],
        log_type: str = 'rejected'
    ):
        """
        记录被拒绝或需复审的视频

        Args:
            video_path: 视频路径
            quality_result: 质量评估结果
            log_type: 'rejected' 或 'borderline'
        """
        log_path = self.rejected_log_path if log_type == 'rejected' else self.borderline_log_path

        # 读取现有日志
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        # 添加新记录
        video_entry = {
            'video_id': Path(video_path).stem,
            'video_path': str(video_path),
            'logged_at': datetime.now().isoformat(),
            'quality_assessment': quality_result
        }

        log_data['videos'].append(video_entry)
        log_data['metadata']['total_count'] = len(log_data['videos'])
        log_data['metadata']['last_updated'] = datetime.now().isoformat()

        # 更新统计信息
        rejection_reasons = quality_result.get('rejection_reasons', [])
        if rejection_reasons:
            primary_reason = rejection_reasons[0]
            log_data['statistics'][primary_reason] = log_data['statistics'].get(primary_reason, 0) + 1
        else:
            # 边界情况
            log_data['statistics']['borderline_case'] = log_data['statistics'].get('borderline_case', 0) + 1

        # 保存更新后的日志
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

        logger.info(f"  ✓ Logged to {log_path.name}")

    def _get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """提取视频元数据"""
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            return {
                'error': 'Failed to open video',
                'path': str(video_path)
            }

        metadata = {
            'filename': Path(video_path).name,
            'file_size_mb': round(Path(video_path).stat().st_size / (1024 * 1024), 2),
            'duration_seconds': round(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS), 2) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0,
            'fps': round(cap.get(cv2.CAP_PROP_FPS), 2),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        }

        cap.release()
        return metadata

    def _save_quality_assessment(self, video_path: str, assessment: Dict[str, Any]):
        """保存质量评估结果"""
        assessment_dir = self.output_dir / "quality_assessments"
        assessment_dir.mkdir(exist_ok=True)

        video_name = Path(video_path).stem
        output_path = assessment_dir / f"{video_name}_quality.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(assessment, f, ensure_ascii=False, indent=2)

        logger.debug(f"Quality assessment saved to {output_path}")

    def _save_annotation(self, video_path: str, annotation: Dict[str, Any]):
        """保存完整标注结果"""
        annotations_dir = self.output_dir / "full_annotations"
        annotations_dir.mkdir(exist_ok=True)

        video_name = Path(video_path).stem
        output_path = annotations_dir / f"{video_name}_annotation.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(annotation, f, ensure_ascii=False, indent=2)

        logger.info(f"Full annotation saved to {output_path}")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取JSON（处理markdown代码块）"""
        import re

        # 尝试移除markdown代码块标记
        json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = text

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.debug(f"Raw text: {text[:500]}...")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """获取管道统计信息"""
        stats = {
            'rejected': {},
            'borderline': {},
            'total_processed': 0,
            'rejection_rate': 0.0
        }

        # 读取拒绝日志
        if self.rejected_log_path.exists():
            with open(self.rejected_log_path, 'r', encoding='utf-8') as f:
                rejected_data = json.load(f)
                stats['rejected'] = rejected_data.get('statistics', {})
                stats['rejected_count'] = rejected_data['metadata']['total_count']

        # 读取边界日志
        if self.borderline_log_path.exists():
            with open(self.borderline_log_path, 'r', encoding='utf-8') as f:
                borderline_data = json.load(f)
                stats['borderline'] = borderline_data.get('statistics', {})
                stats['borderline_count'] = borderline_data['metadata']['total_count']

        # 计算总数和拒绝率
        stats['total_processed'] = stats.get('rejected_count', 0) + stats.get('borderline_count', 0)
        if stats['total_processed'] > 0:
            stats['rejection_rate'] = round(
                stats.get('rejected_count', 0) / stats['total_processed'], 3
            )

        return stats

    def batch_annotate(
        self,
        video_paths: List[str],
        ai_provider,
        max_concurrent: int = 3,
        force_annotate: bool = False
    ) -> List[Dict[str, Any]]:
        """
        批量标注多个视频

        Args:
            video_paths: 视频路径列表
            ai_provider: AI提供者实例
            max_concurrent: 最大并发数
            force_annotate: 是否强制标注（跳过质量检查）

        Returns:
            标注结果列表
        """
        results = []

        logger.info(f"\n{'='*60}")
        logger.info(f"Batch Annotation Started")
        logger.info(f"Total videos: {len(video_paths)}")
        logger.info(f"Max concurrent: {max_concurrent}")
        logger.info(f"{'='*60}\n")

        for i, video_path in enumerate(video_paths, 1):
            logger.info(f"\n[{i}/{len(video_paths)}] Processing: {Path(video_path).name}")

            try:
                result = self.annotate_with_quality_check(
                    video_path=video_path,
                    ai_provider=ai_provider,
                    force_annotate=force_annotate
                )
                results.append(result)

            except Exception as e:
                logger.error(f"Failed to process {video_path}: {e}")
                results.append({
                    'video_path': str(video_path),
                    'status': 'error',
                    'error': str(e)
                })

        # 打印汇总统计
        logger.info(f"\n{'='*60}")
        logger.info(f"Batch Annotation Completed")
        logger.info(f"{'='*60}")

        status_counts = {}
        for result in results:
            status = result.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        for status, count in status_counts.items():
            logger.info(f"  {status.upper()}: {count}")

        return results


# 使用示例
if __name__ == "__main__":
    # 这是示例代码，实际使用需要配置AI提供者

    from backend.ai_providers.gemini_provider import GeminiProvider
    import os

    # 初始化管道
    pipeline = AnnotationPipeline(
        output_dir="data/annotations",
        quality_threshold=65,
        auto_reject_threshold=55
    )

    # 初始化AI提供者
    ai_provider = GeminiProvider(
        api_key=os.getenv("GEMINI_API_KEY"),
        model_name="gemini-2.0-flash-exp"
    )

    # 单个视频标注
    result = pipeline.annotate_with_quality_check(
        video_path="data/videos/example.mp4",
        ai_provider=ai_provider
    )

    print(f"\nResult: {result['status']}")

    # 查看统计
    stats = pipeline.get_statistics()
    print(f"\nPipeline Statistics:")
    print(json.dumps(stats, indent=2))
