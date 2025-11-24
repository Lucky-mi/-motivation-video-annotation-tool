#!/usr/bin/env python3
# scripts/annotate_with_v3.py
"""
使用V3标注Schema对视频进行标注
特点：
1. 保留完整视频（带音频）
2. 筛选纯净视频（无字幕、特效）
3. 记录属性上升/下降
4. 开放式推断，不用固定标签
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from datetime import datetime
from backend.annotation_schema_v3 import (
    VideoAnnotationV3,
    CharacterDescription,
    SceneDescription,
    ObservableBehavior,
    AttributeChange,
    OpenInference,
    PsychologyReference,
    ANNOTATION_PROMPT_V3,
    PSYCHOLOGY_KNOWLEDGE_BASE
)
from backend.vlm_analyzer import VLMAnalyzer
from config.config import config
import google.generativeai as genai


def annotate_video_v3(video_path: str, video_id: str = None) -> VideoAnnotationV3:
    """
    使用V3格式标注视频

    Args:
        video_path: 视频文件路径
        video_id: 视频ID（可选）

    Returns:
        VideoAnnotationV3对象
    """
    if video_id is None:
        video_id = Path(video_path).stem

    print(f"\n{'='*80}")
    print(f"开始标注视频: {video_id}")
    print(f"{'='*80}\n")

    # 初始化VLM
    api_key = config.get_api_key('gemini')
    analyzer = VLMAnalyzer(api_key=api_key)

    # 上传视频
    print("1. 上传视频到AI服务...")
    video_file = genai.upload_file(path=video_path)

    # 等待处理
    print("2. 等待视频处理...")
    import time
    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name != "ACTIVE":
        raise Exception(f"视频处理失败: {video_file.state.name}")

    print("3. 视频已就绪，开始AI标注...\n")

    # 构建提示
    prompt = f"""{ANNOTATION_PROMPT_V3}

---

## 当前任务

请对这个视频进行完整的Theory of Mind标注。

记住：
- 详细记录人物属性的变化（上升/下降）
- 使用开放式描述，不要用固定的情感标签
- 提供充分的证据支持你的推断
- 考虑多种可能的解释

请以JSON格式输出，严格遵循VideoAnnotationV3的Schema。
"""

    # 调用AI
    response = analyzer.model.generate_content(
        [video_file, prompt],
        generation_config={
            "max_output_tokens": 8192,
            "temperature": 0.3
        }
    )

    # 清理云端文件
    try:
        genai.delete_file(video_file.name)
    except:
        pass

    # 解析JSON
    response_text = response.text.strip()

    # 移除可能的markdown代码块标记
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]

    response_text = response_text.strip()

    # 解析为Pydantic模型
    annotation_data = json.loads(response_text)
    annotation = VideoAnnotationV3(**annotation_data)

    print("✅ 标注完成！\n")
    return annotation


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="使用V3格式标注视频")
    parser.add_argument("video_path", help="视频文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径（默认：data/annotations_v3/）")
    parser.add_argument("--video-id", help="视频ID（默认使用文件名）")

    args = parser.parse_args()

    video_path = Path(args.video_path)
    if not video_path.exists():
        print(f"❌ 视频文件不存在: {video_path}")
        return

    # 标注视频
    try:
        annotation = annotate_video_v3(str(video_path), args.video_id)

        # 保存结果
        if args.output:
            output_path = Path(args.output)
        else:
            output_dir = Path("data/annotations_v3")
            output_dir.mkdir(exist_ok=True, parents=True)
            output_path = output_dir / f"{annotation.video_id}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(annotation.model_dump(), f, ensure_ascii=False, indent=2)

        print(f"💾 标注已保存: {output_path}")

        # 打印摘要
        print(f"\n{'='*80}")
        print("📊 标注摘要")
        print(f"{'='*80}")
        print(f"视频ID: {annotation.video_id}")
        print(f"时长: {annotation.duration:.1f}秒")
        print(f"纯净视频: {'是' if annotation.is_clean_video else '否'}")
        print(f"人物数量: {len(annotation.characters)}")
        print(f"行为记录: {len(annotation.observable_behaviors)}个")
        print(f"开放式推断: {len(annotation.open_inferences)}个")

        # 打印属性变化
        print(f"\n📈 属性变化统计:")
        for char in annotation.characters:
            if char.attribute_changes:
                print(f"\n  {char.character_id}:")
                for attr in char.attribute_changes:
                    print(f"    - {attr.attribute_name}: {attr.direction}")

        # 打印部分推断
        print(f"\n🧠 推断示例（前2个）:")
        for i, inference in enumerate(annotation.open_inferences[:2], 1):
            print(f"\n  {i}. {inference.inference_aspect}")
            print(f"     结论: {inference.conclusion[:100]}...")
            print(f"     确定性: {inference.confidence}")

    except Exception as e:
        print(f"❌ 标注失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
