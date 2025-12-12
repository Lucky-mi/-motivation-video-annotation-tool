"""
关键帧提取策略 - 智能混合提取
确保连续性和可理解性
"""
from typing import List, Tuple
import cv2
from pathlib import Path


class KeyframeStrategy:
    """关键帧提取策略"""

    @staticmethod
    def generate_continuous_timestamps(
        video_duration: float,
        ai_suggested_timestamps: List[float],
        strategy: str = "hybrid",
        base_interval: float = 8.0,
        context_window: float = 3.0,
        max_frames: int = 15
    ) -> List[float]:
        """
        生成连续的关键帧时间戳

        Args:
            video_duration: 视频总时长（秒）
            ai_suggested_timestamps: AI建议的关键时刻
            strategy: 提取策略
                - "hybrid": 混合策略（固定间隔 + AI关键帧）⭐ 推荐
                - "context_aware": 上下文感知（AI帧前后补充）
                - "dense": 密集采样（高连续性）
            base_interval: 基础采样间隔（秒）
            context_window: 上下文窗口（秒）
            max_frames: 最大帧数

        Returns:
            排序后的时间戳列表
        """
        timestamps = set()

        # 1. 起始帧（必须）
        timestamps.add(0.0)
        timestamps.add(min(2.0, video_duration * 0.05))  # 0秒和2秒（或5%位置）

        # 2. 结束帧（可选，用于闭合叙事）
        if video_duration > 10:
            timestamps.add(max(0, video_duration - 2.0))

        # 3. 根据策略添加帧
        if strategy == "hybrid":
            timestamps.update(
                KeyframeStrategy._hybrid_strategy(
                    video_duration, ai_suggested_timestamps, base_interval
                )
            )

        elif strategy == "context_aware":
            timestamps.update(
                KeyframeStrategy._context_aware_strategy(
                    video_duration, ai_suggested_timestamps, context_window
                )
            )

        elif strategy == "dense":
            timestamps.update(
                KeyframeStrategy._dense_strategy(
                    video_duration, base_interval / 2
                )
            )

        # 4. 清理和限制
        timestamps = KeyframeStrategy._clean_timestamps(
            timestamps, video_duration, max_frames
        )

        return sorted(list(timestamps))

    @staticmethod
    def _hybrid_strategy(
        duration: float,
        ai_timestamps: List[float],
        base_interval: float
    ) -> List[float]:
        """混合策略：固定间隔 + AI关键帧"""
        timestamps = set()

        # 固定间隔基础帧
        current = 0.0
        while current <= duration:
            timestamps.add(current)
            current += base_interval

        # AI建议的关键帧
        timestamps.update(ai_timestamps)

        return timestamps

    @staticmethod
    def _context_aware_strategy(
        duration: float,
        ai_timestamps: List[float],
        context_window: float
    ) -> List[float]:
        """上下文感知策略：每个关键时刻前后补充帧"""
        timestamps = set()

        for ts in ai_timestamps:
            # 关键帧本身
            timestamps.add(ts)

            # 前置上下文帧（看到"之前发生了什么"）
            before = max(0, ts - context_window)
            timestamps.add(before)

            # 后置上下文帧（看到"结果如何"）
            after = min(duration, ts + context_window / 2)
            timestamps.add(after)

        return timestamps

    @staticmethod
    def _dense_strategy(
        duration: float,
        interval: float
    ) -> List[float]:
        """密集策略：均匀采样"""
        timestamps = set()
        current = 0.0

        while current <= duration:
            timestamps.add(current)
            current += interval

        return timestamps

    @staticmethod
    def _clean_timestamps(
        timestamps: set,
        video_duration: float,
        max_frames: int
    ) -> List[float]:
        """清理时间戳：去重、排序、限制数量"""
        # 去除超出范围的
        valid_ts = [ts for ts in timestamps if 0 <= ts <= video_duration]

        # 去除过于接近的（最小间隔1秒）
        valid_ts.sort()
        deduplicated = [valid_ts[0]] if valid_ts else []

        for ts in valid_ts[1:]:
            if ts - deduplicated[-1] >= 1.0:  # 最小间隔1秒
                deduplicated.append(ts)

        # 限制最大数量（如果超了，均匀筛选）
        if len(deduplicated) > max_frames:
            step = len(deduplicated) / max_frames
            deduplicated = [
                deduplicated[int(i * step)]
                for i in range(max_frames)
            ]

        return deduplicated


class ContinuousFrameExtractor:
    """连续关键帧提取器"""

    @staticmethod
    def extract_with_strategy(
        video_path: str,
        ai_timestamps: List[float],
        output_dir: Path,
        strategy: str = "hybrid",
        **kwargs
    ) -> List[Tuple[float, str]]:
        """
        使用指定策略提取关键帧

        Args:
            video_path: 视频路径
            ai_timestamps: AI建议的时间戳
            output_dir: 输出目录
            strategy: 提取策略
            **kwargs: 传递给 KeyframeStrategy 的其他参数

        Returns:
            [(timestamp, image_path), ...]
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        # 生成连续时间戳
        timestamps = KeyframeStrategy.generate_continuous_timestamps(
            duration, ai_timestamps, strategy, **kwargs
        )

        print(f"  📸 提取策略: {strategy}")
        print(f"  📊 时间戳数量: {len(timestamps)} 帧")
        print(f"  ⏱️  覆盖范围: 0s - {duration:.1f}s")

        # 提取帧
        video_name = Path(video_path).stem
        kf_dir = output_dir / video_name
        kf_dir.mkdir(parents=True, exist_ok=True)

        extracted = []

        for idx, ts in enumerate(timestamps):
            try:
                frame_num = int(ts * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()

                if ret:
                    filename = f"frame_{idx:04d}_t{ts:.2f}s.jpg"
                    path = kf_dir / filename

                    # 支持中文路径
                    is_success, im_buf = cv2.imencode(".jpg", frame)
                    if is_success:
                        im_buf.tofile(str(path))
                        extracted.append((ts, str(path)))

            except Exception as e:
                print(f"  ⚠️ 提取帧失败 (t={ts:.2f}s): {e}")
                continue

        cap.release()

        print(f"  ✅ 成功提取 {len(extracted)}/{len(timestamps)} 帧")
        return extracted


# ============ 使用示例 ============

def demo_comparison():
    """演示不同策略的对比"""

    # 假设视频30秒，AI建议了3个关键时刻
    video_duration = 30.0
    ai_timestamps = [8.5, 15.2, 24.7]

    print("=" * 60)
    print("关键帧提取策略对比")
    print("=" * 60)
    print(f"\n视频时长: {video_duration}s")
    print(f"AI建议: {ai_timestamps}")
    print()

    strategies = {
        "传统方式（仅AI）": ai_timestamps,
        "混合策略（推荐）": KeyframeStrategy.generate_continuous_timestamps(
            video_duration, ai_timestamps, strategy="hybrid", base_interval=8.0
        ),
        "上下文感知": KeyframeStrategy.generate_continuous_timestamps(
            video_duration, ai_timestamps, strategy="context_aware", context_window=3.0
        ),
        "密集采样": KeyframeStrategy.generate_continuous_timestamps(
            video_duration, ai_timestamps, strategy="dense", base_interval=5.0
        ),
    }

    for name, timestamps in strategies.items():
        print(f"\n【{name}】")
        print(f"  帧数: {len(timestamps)}")
        print(f"  时间戳: {[f'{t:.1f}s' for t in timestamps]}")

        # 计算平均间隔
        if len(timestamps) > 1:
            intervals = [
                timestamps[i+1] - timestamps[i]
                for i in range(len(timestamps)-1)
            ]
            avg_interval = sum(intervals) / len(intervals)
            max_gap = max(intervals)
            print(f"  平均间隔: {avg_interval:.1f}s")
            print(f"  最大间隔: {max_gap:.1f}s")


if __name__ == "__main__":
    demo_comparison()
