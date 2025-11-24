"""
修复缺失的关键帧图片
用于修复标注文件存在但关键帧图片缺失的情况
"""
import json
import cv2
from pathlib import Path
from tqdm import tqdm

# 配置路径
VIDEOS_DIR = Path("data/videos")
KEYFRAMES_DIR = Path("data/keyframes")
ANNOTATIONS_DIR = Path("data/annotations")

def repair_missing_frames(video_path: Path, annotation_path: Path):
    """修复单个视频的缺失关键帧"""
    print(f"🔧 检查: {video_path.name}")

    try:
        with open(annotation_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ❌ 无法读取标注: {e}")
        return

    keyframes = data.get('keyframes', [])
    if not keyframes:
        print(f"  ⏭️ 跳过: 没有关键帧定义")
        return

    video_name = video_path.stem
    save_dir = KEYFRAMES_DIR / video_name
    save_dir.mkdir(parents=True, exist_ok=True)

    # 检查是否需要修复
    missing_count = 0
    for kf in keyframes:
        frame_path = kf.get('frame_path', '')
        if frame_path and not Path(frame_path).exists():
            missing_count += 1

    if missing_count == 0:
        print(f"  ✅ 完好: 所有关键帧都存在")
        return

    print(f"  ⚠️ 发现 {missing_count} 个缺失关键帧，开始修复...")

    # 打开视频
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"  ❌ 无法打开视频文件")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    updated = False

    for idx, kf in enumerate(keyframes):
        # 获取时间戳
        ts = kf.get('timestamp_seconds')
        if ts is None and 'action' in kf:
            ts = kf['action'].get('timestamp')

        if ts is None:
            continue

        ts = float(ts)

        # 生成标准路径
        filename = f"frame_{idx:04d}_t{ts:.2f}s.jpg"
        target_path = save_dir / filename

        # 检查文件是否存在
        if not target_path.exists():
            # 提取帧
            frame_num = int(ts * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame_img = cap.read()

            if ret:
                cv2.imwrite(str(target_path), frame_img)
                # 更新JSON中的路径
                kf['frame_path'] = str(target_path).replace('\\', '/')
                updated = True
                print(f"    ✅ 补回: {filename}")
            else:
                print(f"    ❌ 无法提取帧 @{ts}s")

    cap.release()

    # 保存更新后的标注
    if updated:
        with open(annotation_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 标注已更新")

def main():
    print("=" * 60)
    print("  关键帧修复工具")
    print("=" * 60)
    print()

    # 获取所有标注文件
    annotations = list(ANNOTATIONS_DIR.glob("*.json"))
    print(f"📂 找到 {len(annotations)} 个标注文件")
    print()

    # 遍历处理
    repaired_count = 0

    for anno_file in tqdm(annotations, desc="处理中"):
        video_id = anno_file.stem

        # 查找对应的视频文件
        video_exts = ['.mp4', '.avi', '.mov', '.mkv']
        video_file = None

        # 先尝试根据video_id查找
        for ext in video_exts:
            candidate = VIDEOS_DIR / f"{video_id}{ext}"
            if candidate.exists():
                video_file = candidate
                break

        # 如果没找到，尝试从JSON中读取video_name
        if not video_file:
            try:
                with open(anno_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    video_name = data.get('video_name', '')
                    if video_name:
                        candidate = VIDEOS_DIR / video_name
                        if candidate.exists():
                            video_file = candidate
            except:
                pass

        if video_file:
            repair_missing_frames(video_file, anno_file)
            repaired_count += 1
        else:
            print(f"⚠️ 找不到视频文件: {video_id}")

    print()
    print("=" * 60)
    print(f"🎉 完成！处理了 {repaired_count} 个视频")
    print("=" * 60)

if __name__ == "__main__":
    main()
