"""
Video Question Answering (VQA) 处理器
基于标注数据生成问题，并截取对应视频片段用于回答
"""
import json
import cv2
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import subprocess


class VQAProcessor:
    """VQA 处理器 - 从标注到问答"""

    def __init__(self, output_dir: Path = Path("data/vqa")):
        self.output_dir = output_dir
        self.clips_dir = output_dir / "video_clips"
        self.frames_dir = output_dir / "frame_sequences"
        self.questions_dir = output_dir / "questions"

        # 创建目录
        for d in [self.clips_dir, self.frames_dir, self.questions_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def extract_time_spans_from_annotation(
        self,
        annotation_path: str
    ) -> List[Dict]:
        """
        从标注数据中提取时间区间

        Args:
            annotation_path: V3 标注文件路径

        Returns:
            时间区间列表，每个包含：
            - aspect: 推断方面
            - start: 开始时间
            - end: 结束时间
            - key_moment: 关键时刻
            - context: 推断内容
        """
        with open(annotation_path, 'r', encoding='utf-8') as f:
            annotation = json.load(f)

        time_spans = []

        # 1. 从 open_inferences 提取（V3 格式）
        if 'open_inferences' in annotation:
            for idx, inference in enumerate(annotation['open_inferences']):
                # 尝试从 supporting_evidence 推断时间范围
                # 如果标注中记录了具体时间，直接使用
                # 否则，根据行为序列推断

                # 简单策略：寻找相关的 observable_behaviors
                related_behaviors = self._find_related_behaviors(
                    inference, annotation.get('observable_behaviors', [])
                )

                if related_behaviors:
                    timestamps = [self._parse_timestamp(b['timestamp'])
                                  for b in related_behaviors]
                    timestamps = [t for t in timestamps if t is not None]

                    if timestamps:
                        start = min(timestamps)
                        end = max(timestamps)
                        key_moment = (start + end) / 2

                        time_spans.append({
                            'id': f"inference_{idx}",
                            'aspect': inference.get('inference_aspect', ''),
                            'start': max(0, start - 2.0),  # 前2秒上下文
                            'end': end + 1.0,  # 后1秒上下文
                            'key_moment': key_moment,
                            'conclusion': inference.get('conclusion', ''),
                            'evidence': inference.get('supporting_evidence', []),
                            'confidence': inference.get('confidence', 'medium')
                        })

        # 2. 从 characters.attribute_changes 提取（V3 格式）
        if 'characters' in annotation:
            for char_idx, character in enumerate(annotation['characters']):
                for attr_idx, attr_change in enumerate(character.get('attribute_changes', [])):
                    # 属性变化通常发生在整个视频过程中
                    # 需要从 observable_behaviors 中找到相关时间

                    related_behaviors = self._find_behaviors_by_character(
                        character['character_id'],
                        annotation.get('observable_behaviors', [])
                    )

                    if related_behaviors:
                        timestamps = [self._parse_timestamp(b['timestamp'])
                                      for b in related_behaviors]
                        timestamps = [t for t in timestamps if t is not None]

                        if timestamps:
                            start = min(timestamps)
                            end = max(timestamps)

                            time_spans.append({
                                'id': f"attr_change_{char_idx}_{attr_idx}",
                                'aspect': f"{character['character_id']}: {attr_change['attribute_name']}的{attr_change['direction']}",
                                'start': max(0, start - 2.0),
                                'end': end + 1.0,
                                'key_moment': (start + end) / 2,
                                'conclusion': f"从{attr_change.get('start_level', '?')}变为{attr_change.get('end_level', '?')}",
                                'evidence': attr_change.get('evidence', []),
                                'confidence': attr_change['confidence']
                            })

        return time_spans

    def _find_related_behaviors(
        self,
        inference: Dict,
        behaviors: List[Dict]
    ) -> List[Dict]:
        """找到与推断相关的行为"""
        # 简单策略：如果推断的证据中提到了某些行为关键词
        evidence_text = ' '.join(inference.get('supporting_evidence', [])).lower()

        related = []
        for behavior in behaviors:
            behavior_text = behavior.get('detailed_description', '').lower()
            # 简单的文本匹配
            if any(word in behavior_text for word in evidence_text.split()):
                related.append(behavior)

        return related

    def _find_behaviors_by_character(
        self,
        character_id: str,
        behaviors: List[Dict]
    ) -> List[Dict]:
        """找到某个角色的所有行为"""
        return [b for b in behaviors if b.get('character_id') == character_id]

    def _parse_timestamp(self, timestamp_str: str) -> Optional[float]:
        """
        解析时间戳字符串

        支持格式：
        - "0:05-0:10" → 返回中点 7.5
        - "15秒" → 返回 15.0
        - "开始阶段" → 返回 None（无法解析）
        """
        try:
            if '-' in timestamp_str:
                # 区间格式 "0:05-0:10"
                parts = timestamp_str.split('-')
                start = self._time_to_seconds(parts[0].strip())
                end = self._time_to_seconds(parts[1].strip())
                return (start + end) / 2 if start and end else None
            elif ':' in timestamp_str:
                # 时间格式 "0:05"
                return self._time_to_seconds(timestamp_str)
            elif timestamp_str.replace('.', '').isdigit():
                # 纯数字 "15" 或 "15.5"
                return float(timestamp_str)
            else:
                return None
        except:
            return None

    def _time_to_seconds(self, time_str: str) -> Optional[float]:
        """将 "0:05" 转换为秒数"""
        try:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes, seconds = parts
                return int(minutes) * 60 + float(seconds)
            return None
        except:
            return None

    def extract_video_clip(
        self,
        video_path: str,
        start: float,
        end: float,
        output_name: str
    ) -> str:
        """
        截取视频片段（使用 ffmpeg）

        Args:
            video_path: 原始视频路径
            start: 开始时间（秒）
            end: 结束时间（秒）
            output_name: 输出文件名（不含扩展名）

        Returns:
            输出视频路径
        """
        output_path = self.clips_dir / f"{output_name}.mp4"
        duration = end - start

        # 使用 ffmpeg 截取
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(start),
            '-t', str(duration),
            '-c', 'copy',  # 快速复制，不重新编码
            '-y',  # 覆盖已存在文件
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return str(output_path)
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️ ffmpeg 截取失败: {e}")
            # 降级方案：使用 opencv（会重新编码，较慢）
            return self._extract_clip_opencv(video_path, start, end, output_path)

    def _extract_clip_opencv(
        self,
        video_path: str,
        start: float,
        end: float,
        output_path: Path
    ) -> str:
        """使用 OpenCV 截取视频片段（降级方案）"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

        start_frame = int(start * fps)
        end_frame = int(end * fps)

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        for frame_num in range(start_frame, end_frame):
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        cap.release()
        out.release()

        return str(output_path)

    def extract_frame_sequence(
        self,
        video_path: str,
        start: float,
        end: float,
        output_name: str,
        interval: float = 2.0
    ) -> List[str]:
        """
        提取连续关键帧序列

        Args:
            video_path: 原始视频路径
            start: 开始时间
            end: 结束时间
            output_name: 输出名称前缀
            interval: 帧间隔（秒）

        Returns:
            帧图片路径列表
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)

        frames_output_dir = self.frames_dir / output_name
        frames_output_dir.mkdir(exist_ok=True)

        frame_paths = []
        current = start

        idx = 0
        while current <= end:
            frame_num = int(current * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()

            if ret:
                filename = f"frame_{idx:03d}_t{current:.2f}s.jpg"
                output_path = frames_output_dir / filename

                # 支持中文路径
                is_success, im_buf = cv2.imencode(".jpg", frame)
                if is_success:
                    im_buf.tofile(str(output_path))
                    frame_paths.append(str(output_path))

            idx += 1
            current += interval

        cap.release()
        return frame_paths

    def generate_questions(
        self,
        time_spans: List[Dict],
        video_id: str
    ) -> List[Dict]:
        """
        根据时间区间生成问题

        Args:
            time_spans: 时间区间列表
            video_id: 视频 ID

        Returns:
            问题列表，每个包含：
            - question: 问题文本
            - time_span: 对应的时间区间
            - answer_hint: 答案提示（从标注中提取）
        """
        questions = []

        for span in time_spans:
            aspect = span['aspect']
            start = span['start']
            end = span['end']
            conclusion = span['conclusion']

            # 生成多种类型的问题
            question_templates = [
                {
                    'type': 'what',
                    'question': f"在 {start:.1f}s 到 {end:.1f}s 之间发生了什么？",
                    'answer_hint': conclusion
                },
                {
                    'type': 'why',
                    'question': f"为什么{aspect}？",
                    'answer_hint': f"{conclusion}。证据：{', '.join(span['evidence'][:3])}"
                },
                {
                    'type': 'how',
                    'question': f"{aspect}是如何表现出来的？",
                    'answer_hint': f"通过以下行为：{', '.join(span['evidence'])}"
                },
                {
                    'type': 'when',
                    'question': f"{aspect}的关键时刻在什么时候？",
                    'answer_hint': f"大约在 {span['key_moment']:.1f} 秒"
                }
            ]

            for template in question_templates:
                questions.append({
                    'id': f"{span['id']}_{template['type']}",
                    'video_id': video_id,
                    'question': template['question'],
                    'question_type': template['type'],
                    'time_span': {
                        'start': start,
                        'end': end,
                        'key_moment': span['key_moment']
                    },
                    'answer_hint': template['answer_hint'],
                    'confidence': span['confidence'],
                    'video_clip_path': None,  # 待填充
                    'frame_sequence_dir': None  # 待填充
                })

        return questions

    def process_annotation_to_vqa(
        self,
        video_path: str,
        annotation_path: str,
        extract_clips: bool = True,
        extract_frames: bool = True
    ) -> Dict:
        """
        完整流程：从标注生成 VQA 数据

        Args:
            video_path: 视频文件路径
            annotation_path: V3 标注文件路径
            extract_clips: 是否截取视频片段
            extract_frames: 是否提取关键帧序列

        Returns:
            VQA 数据包，包含问题和对应的视频片段/帧序列
        """
        video_id = Path(video_path).stem

        print(f"\n{'='*60}")
        print(f"处理视频: {video_id}")
        print(f"{'='*60}\n")

        # 1. 提取时间区间
        print("1. 从标注提取时间区间...")
        time_spans = self.extract_time_spans_from_annotation(annotation_path)
        print(f"   找到 {len(time_spans)} 个时间区间")

        # 2. 生成问题
        print("2. 生成问题...")
        questions = self.generate_questions(time_spans, video_id)
        print(f"   生成 {len(questions)} 个问题")

        # 3. 截取视频片段或提取帧序列
        if extract_clips or extract_frames:
            print(f"3. 提取视频片段...")

            for question in questions:
                span = question['time_span']
                clip_name = f"{video_id}_{question['id']}"

                try:
                    if extract_clips:
                        clip_path = self.extract_video_clip(
                            video_path,
                            span['start'],
                            span['end'],
                            clip_name
                        )
                        question['video_clip_path'] = clip_path
                        print(f"   ✅ 片段: {clip_name} ({span['start']:.1f}s - {span['end']:.1f}s)")

                    if extract_frames:
                        frame_paths = self.extract_frame_sequence(
                            video_path,
                            span['start'],
                            span['end'],
                            clip_name,
                            interval=2.0
                        )
                        question['frame_sequence_dir'] = str(self.frames_dir / clip_name)
                        question['frame_count'] = len(frame_paths)

                except Exception as e:
                    print(f"   ⚠️ 提取失败: {e}")

        # 4. 保存 VQA 数据
        vqa_data = {
            'video_id': video_id,
            'video_path': video_path,
            'annotation_path': annotation_path,
            'time_spans': time_spans,
            'questions': questions,
            'total_questions': len(questions)
        }

        output_path = self.questions_dir / f"{video_id}_vqa.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(vqa_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ VQA 数据已保存: {output_path}\n")

        return vqa_data


# ============ 使用示例 ============

def main():
    """示例使用"""
    import argparse

    parser = argparse.ArgumentParser(description="从标注生成 VQA 数据")
    parser.add_argument("video_path", help="视频文件路径")
    parser.add_argument("annotation_path", help="V3 标注文件路径")
    parser.add_argument("--no-clips", action="store_true", help="不提取视频片段")
    parser.add_argument("--no-frames", action="store_true", help="不提取关键帧序列")

    args = parser.parse_args()

    processor = VQAProcessor()
    vqa_data = processor.process_annotation_to_vqa(
        args.video_path,
        args.annotation_path,
        extract_clips=not args.no_clips,
        extract_frames=not args.no_frames
    )

    print("=" * 60)
    print("📊 VQA 数据摘要")
    print("=" * 60)
    print(f"视频 ID: {vqa_data['video_id']}")
    print(f"时间区间: {len(vqa_data['time_spans'])} 个")
    print(f"问题总数: {vqa_data['total_questions']} 个")
    print()

    # 显示前3个问题
    print("示例问题（前3个）:")
    for i, q in enumerate(vqa_data['questions'][:3], 1):
        print(f"\n{i}. {q['question']}")
        print(f"   类型: {q['question_type']}")
        print(f"   时间: {q['time_span']['start']:.1f}s - {q['time_span']['end']:.1f}s")
        if q['video_clip_path']:
            print(f"   视频片段: {Path(q['video_clip_path']).name}")


if __name__ == "__main__":
    main()
