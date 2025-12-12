"""
轻量级 VQA 处理器 - 只保存时间段信息，不保存实际视频片段
运行时动态加载视频片段

功能：
1. 批量处理文件夹中的视频
2. 自动跳过已处理的视频（断点续传）
3. 支持前端审核时修改时间点
"""
import json
import cv2
from pathlib import Path
from typing import List, Dict, Optional
import google.generativeai as genai
import time
from datetime import datetime


class LightweightVQAProcessor:
    """轻量级 VQA 处理器 - 不存储视频片段，只存储时间戳"""

    def __init__(self, output_dir: Path = Path("data/vqa_light")):
        self.output_dir = output_dir
        self.questions_dir = output_dir / "questions"
        self.questions_dir.mkdir(parents=True, exist_ok=True)

    def extract_time_spans_from_annotation(
        self,
        annotation_path: str
    ) -> List[Dict]:
        """
        从标注数据中提取时间区间（与完整版相同）
        """
        with open(annotation_path, 'r', encoding='utf-8') as f:
            annotation = json.load(f)

        time_spans = []

        # 从 open_inferences 提取
        if 'open_inferences' in annotation:
            for idx, inference in enumerate(annotation['open_inferences']):
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
                            'start': max(0, start - 2.0),
                            'end': end + 1.0,
                            'key_moment': key_moment,
                            'conclusion': inference.get('conclusion', ''),
                            'evidence': inference.get('supporting_evidence', []),
                            'confidence': inference.get('confidence', 'medium')
                        })

        # 从 attribute_changes 提取
        if 'characters' in annotation:
            for char_idx, character in enumerate(annotation['characters']):
                for attr_idx, attr_change in enumerate(character.get('attribute_changes', [])):
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

    def generate_questions(
        self,
        time_spans: List[Dict],
        video_id: str,
        video_path: str  # ⭐ 只记录原视频路径，不截取
    ) -> List[Dict]:
        """
        生成问题（不截取视频片段，只记录时间段）
        """
        questions = []

        for span in time_spans:
            aspect = span['aspect']
            start = span['start']
            end = span['end']
            conclusion = span['conclusion']

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
                }
            ]

            for template in question_templates:
                questions.append({
                    'id': f"{span['id']}_{template['type']}",
                    'video_id': video_id,
                    'video_path': video_path,  # ⭐ 记录原视频路径
                    'question': template['question'],
                    'question_type': template['type'],
                    'time_span': {
                        'start': start,
                        'end': end,
                        'key_moment': span['key_moment'],
                        'duration': end - start
                    },
                    'answer_hint': template['answer_hint'],
                    'confidence': span['confidence']
                })

        return questions

    def is_processed(self, video_id: str) -> bool:
        """检查视频是否已处理"""
        vqa_file = self.questions_dir / f"{video_id}_vqa.json"
        return vqa_file.exists()

    def update_time_span(
        self,
        video_id: str,
        question_id: str,
        new_start: float,
        new_end: float
    ) -> bool:
        """
        更新问题的时间段（前端审核时修改）

        Args:
            video_id: 视频 ID
            question_id: 问题 ID
            new_start: 新的开始时间
            new_end: 新的结束时间

        Returns:
            是否成功
        """
        vqa_file = self.questions_dir / f"{video_id}_vqa.json"
        if not vqa_file.exists():
            return False

        with open(vqa_file, 'r', encoding='utf-8') as f:
            vqa_data = json.load(f)

        # 更新问题的时间段
        updated = False
        for question in vqa_data['questions']:
            if question['id'] == question_id:
                question['time_span']['start'] = new_start
                question['time_span']['end'] = new_end
                question['time_span']['duration'] = new_end - new_start
                question['time_span']['key_moment'] = (new_start + new_end) / 2
                question['manually_adjusted'] = True
                question['adjusted_at'] = datetime.now().isoformat()
                updated = True
                break

        if updated:
            # 保存修改
            with open(vqa_file, 'w', encoding='utf-8') as f:
                json.dump(vqa_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已更新问题 {question_id} 的时间段: {new_start:.1f}s - {new_end:.1f}s")

        return updated

    def process_annotation_to_vqa(
        self,
        video_path: str,
        annotation_path: str,
        skip_if_exists: bool = True
    ) -> Optional[Dict]:
        """
        完整流程：从标注生成 VQA 数据（轻量级，不存储视频片段）

        Args:
            skip_if_exists: 如果已处理则跳过
        """
        video_id = Path(video_path).stem

        # 断点续传：跳过已处理的
        if skip_if_exists and self.is_processed(video_id):
            print(f"⏩ 跳过（已处理）: {video_id}")
            vqa_file = self.questions_dir / f"{video_id}_vqa.json"
            with open(vqa_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        print(f"\n{'='*60}")
        print(f"处理视频: {video_id}")
        print(f"{'='*60}\n")

        # 1. 提取时间区间
        print("1. 从标注提取时间区间...")
        time_spans = self.extract_time_spans_from_annotation(annotation_path)
        print(f"   找到 {len(time_spans)} 个时间区间")

        # 2. 生成问题（不截取片段，只记录时间戳）
        print("2. 生成问题（轻量级，不存储片段）...")
        questions = self.generate_questions(time_spans, video_id, video_path)
        print(f"   生成 {len(questions)} 个问题")

        # 3. 保存 VQA 数据
        vqa_data = {
            'video_id': video_id,
            'video_path': video_path,  # ⭐ 原视频路径
            'annotation_path': annotation_path,
            'time_spans': time_spans,
            'questions': questions,
            'total_questions': len(questions),
            'storage_mode': 'lightweight',  # ⭐ 标记为轻量模式
            'note': '不存储视频片段，运行时动态加载',
            'created_at': datetime.now().isoformat(),
            'version': '1.0'
        }

        output_path = self.questions_dir / f"{video_id}_vqa.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(vqa_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ VQA 数据已保存（轻量级）: {output_path}")
        print(f"💾 磁盘占用：~{output_path.stat().st_size / 1024:.1f} KB（只有 JSON）\n")

        return vqa_data

    # ========== 辅助方法 ==========

    def _find_related_behaviors(self, inference: Dict, behaviors: List[Dict]) -> List[Dict]:
        """找到与推断相关的行为"""
        evidence_text = ' '.join(inference.get('supporting_evidence', [])).lower()
        related = []
        for behavior in behaviors:
            behavior_text = behavior.get('detailed_description', '').lower()
            if any(word in behavior_text for word in evidence_text.split()):
                related.append(behavior)
        return related

    def _find_behaviors_by_character(self, character_id: str, behaviors: List[Dict]) -> List[Dict]:
        """找到某个角色的所有行为"""
        return [b for b in behaviors if b.get('character_id') == character_id]

    def _parse_timestamp(self, timestamp_str: str) -> Optional[float]:
        """解析时间戳"""
        try:
            if '-' in timestamp_str:
                parts = timestamp_str.split('-')
                start = self._time_to_seconds(parts[0].strip())
                end = self._time_to_seconds(parts[1].strip())
                return (start + end) / 2 if start and end else None
            elif ':' in timestamp_str:
                return self._time_to_seconds(timestamp_str)
            elif timestamp_str.replace('.', '').isdigit():
                return float(timestamp_str)
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


class VQARunner:
    """VQA 运行器 - 运行时动态加载视频片段"""

    def __init__(self, model_name: str = 'gemini-2.0-flash'):
        self.model = genai.GenerativeModel(model_name)

    def load_video_segment(
        self,
        video_path: str,
        start: float,
        end: float,
        method: str = 'gemini'  # 'gemini' 或 'frames'
    ):
        """
        运行时加载视频片段

        Args:
            video_path: 原视频路径
            start: 开始时间
            end: 结束时间
            method: 加载方式
                - 'gemini': 上传整个视频，让 Gemini 自己截取（推荐）
                - 'frames': 提取关键帧

        Returns:
            可供 Gemini 使用的对象
        """
        if method == 'gemini':
            # 方式 1：上传完整视频，通过 prompt 指定时间范围
            # Gemini 2.0 支持在 prompt 中指定时间范围
            uploaded_file = genai.upload_file(path=video_path)

            # 等待处理
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)

            return {
                'type': 'video',
                'file': uploaded_file,
                'start': start,
                'end': end
            }

        elif method == 'frames':
            # 方式 2：临时提取关键帧
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)

            frames = []
            current = start
            interval = 2.0  # 每2秒一帧

            while current <= end:
                frame_num = int(current * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()

                if ret:
                    # 临时保存到内存
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        cv2.imwrite(tmp.name, frame)
                        uploaded_frame = genai.upload_file(tmp.name)
                        frames.append(uploaded_frame)

                current += interval

            cap.release()

            return {
                'type': 'frames',
                'files': frames,
                'start': start,
                'end': end
            }

    def answer_question(
        self,
        question: Dict,
        method: str = 'gemini'
    ) -> Dict:
        """
        回答 VQA 问题

        Args:
            question: 问题字典（from VQA JSON）
            method: 加载视频的方式

        Returns:
            答案字典
        """
        video_path = question['video_path']
        time_span = question['time_span']

        print(f"\n问题: {question['question']}")
        print(f"时间: {time_span['start']:.1f}s - {time_span['end']:.1f}s")
        print(f"加载方式: {method}")

        # 1. 加载视频片段
        segment = self.load_video_segment(
            video_path,
            time_span['start'],
            time_span['end'],
            method
        )

        # 2. 构造 Prompt
        if segment['type'] == 'video':
            prompt = f"""
请观看视频的 {time_span['start']:.1f}秒 到 {time_span['end']:.1f}秒 这一段。

问题：{question['question']}

请基于这段视频内容详细回答，包括：
1. 你观察到的具体行为
2. 推理过程
3. 结论
"""
            content = [segment['file'], prompt]

        else:  # frames
            prompt = f"""
这是视频的连续关键帧序列（{len(segment['files'])} 帧）
时间范围：{time_span['start']:.1f}s - {time_span['end']:.1f}s

问题：{question['question']}

请基于这些帧回答。
"""
            content = segment['files'] + [prompt]

        # 3. 获取回答
        print("AI 分析中...")
        response = self.model.generate_content(content)

        result = {
            'question_id': question['id'],
            'question': question['question'],
            'answer': response.text,
            'time_span': time_span,
            'method': method,
            'confidence': question.get('confidence', 'unknown')
        }

        print(f"回答: {response.text[:100]}...")
        return result


# ============ 使用示例 ============

def batch_process(
    videos_dir: str = "data/videos",
    annotations_dir: str = "data/annotations_v3",
    skip_existing: bool = True
):
    """
    批量处理文件夹中的视频

    Args:
        videos_dir: 视频目录
        annotations_dir: 标注目录
        skip_existing: 跳过已处理的视频（断点续传）
    """
    videos_path = Path(videos_dir)
    annotations_path = Path(annotations_dir)

    # 扫描视频文件
    video_files = list(videos_path.glob("*.mp4")) + \
                  list(videos_path.glob("*.avi")) + \
                  list(videos_path.glob("*.mov"))

    print(f"\n{'='*60}")
    print(f"批量处理 VQA 数据生成")
    print(f"{'='*60}")
    print(f"视频目录: {videos_dir}")
    print(f"标注目录: {annotations_dir}")
    print(f"找到视频: {len(video_files)} 个")
    print(f"断点续传: {'开启' if skip_existing else '关闭'}")
    print(f"{'='*60}\n")

    processor = LightweightVQAProcessor()

    processed_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, video_file in enumerate(video_files, 1):
        video_id = video_file.stem
        annotation_file = annotations_path / f"{video_id}.json"

        print(f"\n[{idx}/{len(video_files)}] {video_id}")

        # 检查标注文件是否存在
        if not annotation_file.exists():
            print(f"  ⚠️  标注文件不存在，跳过")
            skipped_count += 1
            continue

        try:
            result = processor.process_annotation_to_vqa(
                str(video_file),
                str(annotation_file),
                skip_if_exists=skip_existing
            )

            if result:
                if processor.is_processed(video_id) and skip_existing:
                    skipped_count += 1
                else:
                    processed_count += 1
            else:
                failed_count += 1

        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            failed_count += 1

    # 统计
    print(f"\n{'='*60}")
    print("批量处理完成")
    print(f"{'='*60}")
    print(f"总视频数: {len(video_files)}")
    print(f"已处理: {processed_count}")
    print(f"跳过: {skipped_count}")
    print(f"失败: {failed_count}")
    print(f"{'='*60}\n")


def main():
    """示例：轻量级 VQA 流程"""
    import argparse

    parser = argparse.ArgumentParser(description="轻量级 VQA 处理")
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # 子命令 1: 生成 VQA 数据（单个）
    gen_parser = subparsers.add_parser('generate', help='生成 VQA 数据（单个）')
    gen_parser.add_argument("video_path", help="视频文件路径")
    gen_parser.add_argument("annotation_path", help="V3 标注文件路径")
    gen_parser.add_argument("--force", action="store_true", help="强制重新处理")

    # 子命令 1.5: 批量生成
    batch_parser = subparsers.add_parser('batch', help='批量生成 VQA 数据')
    batch_parser.add_argument("--videos-dir", default="data/videos", help="视频目录")
    batch_parser.add_argument("--annotations-dir", default="data/annotations_v3", help="标注目录")
    batch_parser.add_argument("--no-skip", action="store_true", help="不跳过已处理的（重新处理全部）")

    # 子命令 2: 更新时间段
    update_parser = subparsers.add_parser('update', help='更新问题时间段（前端审核用）')
    update_parser.add_argument("video_id", help="视频 ID")
    update_parser.add_argument("question_id", help="问题 ID")
    update_parser.add_argument("start", type=float, help="新的开始时间（秒）")
    update_parser.add_argument("end", type=float, help="新的结束时间（秒）")

    # 子命令 3: 回答问题
    ans_parser = subparsers.add_parser('answer', help='回答 VQA 问题')
    ans_parser.add_argument("vqa_data_path", help="VQA 数据 JSON 路径")
    ans_parser.add_argument("--question-id", help="指定问题 ID")
    ans_parser.add_argument("--method", default="gemini", choices=['gemini', 'frames'])

    args = parser.parse_args()

    if args.command == 'generate':
        # 生成 VQA 数据
        processor = LightweightVQAProcessor()
        vqa_data = processor.process_annotation_to_vqa(
            args.video_path,
            args.annotation_path,
            skip_if_exists=not args.force
        )

        print("\n" + "=" * 60)
        print("生成的 VQA 数据（轻量级）")
        print("=" * 60)
        print(f"问题数量: {len(vqa_data['questions'])}")
        print(f"存储模式: {vqa_data['storage_mode']}")
        print(f"视频路径: {vqa_data['video_path']}")
        print("\n前 3 个问题:")
        for i, q in enumerate(vqa_data['questions'][:3], 1):
            print(f"\n{i}. {q['question']}")
            print(f"   时间: {q['time_span']['start']:.1f}s - {q['time_span']['end']:.1f}s")

    elif args.command == 'batch':
        # 批量处理
        batch_process(
            videos_dir=args.videos_dir,
            annotations_dir=args.annotations_dir,
            skip_existing=not args.no_skip
        )

    elif args.command == 'update':
        # 更新时间段
        processor = LightweightVQAProcessor()
        success = processor.update_time_span(
            args.video_id,
            args.question_id,
            args.start,
            args.end
        )

        if success:
            print(f"✅ 时间段已更新")
        else:
            print(f"❌ 更新失败：找不到视频或问题")

    elif args.command == 'answer':
        # 回答问题
        with open(args.vqa_data_path) as f:
            vqa_data = json.load(f)

        runner = VQARunner()

        if args.question_id:
            # 回答指定问题
            question = next(
                (q for q in vqa_data['questions'] if q['id'] == args.question_id),
                None
            )
            if question:
                result = runner.answer_question(question, args.method)
                print("\n" + "=" * 60)
                print(f"Q: {result['question']}")
                print(f"A: {result['answer']}")
                print("=" * 60)
        else:
            # 回答所有问题
            results = []
            for question in vqa_data['questions']:
                result = runner.answer_question(question, args.method)
                results.append(result)

                # 保存结果
                output_path = Path(args.vqa_data_path).parent / f"{vqa_data['video_id']}_answers.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"\n✅ 答案已保存: {output_path}")


if __name__ == "__main__":
    main()
