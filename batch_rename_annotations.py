import json
import os
import time
import shutil
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
import google.generativeai as genai

# 加载配置
from config.config import config
load_dotenv(override=True)

# 路径配置
ANNOTATIONS_DIR = Path("data/annotations_test")
BACKUP_DIR = Path("data/annotations_test_backup")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class AnnotationRenamer:
    def __init__(self):
        api_key = config.get_api_key('gemini')
        if not api_key:
            raise ValueError("❌ 未找到 Gemini API Key")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-3-pro-preview')
        print(f"🤖 使用模型: gemini-3-pro-preview")

    def generate_filename_from_content(self, json_data: dict) -> str:
        """调用大模型根据 JSON 内容生成文件名"""

        # 提取关键信息用于生成文件名
        summary = {
            "video_id": json_data.get("video_id", ""),
            "scene_context": json_data.get("scene_context", {}),
            "characters": json_data.get("characters", []),
            "duration": json_data.get("duration_seconds", 0)
        }

        # 简化字符信息，只保留关键内容
        if summary["characters"]:
            summary["characters"] = [
                {
                    "character_id": c.get("character_id", ""),
                    "role": c.get("role_in_scene", ""),
                    "initial_emotion": c.get("initial_state", {}).get("emotional_state", {}).get("primary_emotion", "")
                }
                for c in summary["characters"][:3]  # 只取前3个角色
            ]

        prompt = f"""
Based on the following video annotation data, generate a SHORT, DESCRIPTIVE filename.

Video Annotation Summary:
{json.dumps(summary, indent=2, ensure_ascii=False)}

Requirements:
1. The filename should be 3-5 words maximum
2. Use snake_case format (lowercase with underscores)
3. Include the most distinctive elements: setting, main action, or emotion
4. Be specific but concise
5. Only output the filename WITHOUT .json extension
6. Avoid generic words like "video" or "scene"

Examples:
- "romantic_breakup_apartment"
- "office_conflict_presentation"
- "family_dinner_argument"
- "beach_proposal_sunset"

Output ONLY the filename:
"""

        try:
            response = self.model.generate_content(prompt)
            filename = response.text.strip().lower()

            # 清理文件名：移除特殊字符，确保是 snake_case
            filename = filename.replace('"', '').replace("'", "").replace('.json', '')
            filename = ''.join(c if c.isalnum() or c == '_' else '_' for c in filename)

            # 移除连续的下划线
            while '__' in filename:
                filename = filename.replace('__', '_')

            filename = filename.strip('_')

            # 确保文件名不为空且不超过50字符
            if not filename or len(filename) < 3:
                filename = "unnamed_video"
            elif len(filename) > 50:
                filename = filename[:50].rstrip('_')

            return filename

        except Exception as e:
            print(f"    ⚠️ 生成文件名失败: {e}")
            return None

    def process_file(self, file_path: Path) -> str:
        """处理单个标注文件"""

        # 读取 JSON 内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ 读取文件失败 {file_path.name}: {e}")
            return "ERROR"

        # 检查是否已经重命名过
        if data.get('is_renamed', False):
            return "SKIP"

        # 检查是否跳过 annotation_errors.json
        if file_path.name == "annotation_errors.json":
            return "SKIP"

        video_id = data.get("video_id", "")
        print(f"\n🔍 分析文件: {file_path.name}")
        print(f"   Video ID: {video_id}")

        # 生成新文件名
        new_filename = self.generate_filename_from_content(data)

        if not new_filename:
            return "ERROR"

        # 添加 .json 扩展名
        new_filename = f"{new_filename}.json"
        new_path = file_path.parent / new_filename

        # 检查文件名是否已存在
        counter = 1
        while new_path.exists() and new_path != file_path:
            new_filename = f"{new_filename[:-5]}_{counter}.json"
            new_path = file_path.parent / new_filename
            counter += 1

        # 如果新文件名和旧文件名相同，跳过
        if new_path == file_path:
            print(f"   ✓ 文件名已是最优: {file_path.name}")
            # 标记为已重命名
            data['is_renamed'] = True
            data['original_filename'] = file_path.name
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return "ALREADY_GOOD"

        print(f"   ✨ 新文件名: {new_filename}")

        # 备份原文件
        backup_path = BACKUP_DIR / file_path.name
        shutil.copy2(file_path, backup_path)
        print(f"   💾 已备份到: {backup_path}")

        # 更新 JSON 数据：添加重命名标记和原始文件名
        data['is_renamed'] = True
        data['original_filename'] = file_path.name
        data['generated_filename'] = new_filename

        # 写入新文件
        with open(new_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 删除旧文件（如果不同）
        if file_path != new_path:
            file_path.unlink()

        print(f"   ✅ 重命名完成: {file_path.name} -> {new_filename}")

        return "SUCCESS"


def main():
    print("=" * 60)
    print("   📝 视频标注文件智能重命名工具")
    print("   基于内容生成有意义的文件名")
    print("=" * 60)

    renamer = AnnotationRenamer()

    # 获取所有 JSON 文件
    files = list(ANNOTATIONS_DIR.glob("*.json"))

    # 过滤掉 annotation_errors.json
    files = [f for f in files if f.name != "annotation_errors.json"]

    # 找出待处理的文件（未重命名的）
    todo_files = []
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as j:
                data = json.load(j)
                if not data.get('is_renamed', False):
                    todo_files.append(f)
        except:
            # 如果读取失败，也加入待处理列表
            todo_files.append(f)

    print(f"\n📂 总文件数: {len(files)}")
    print(f"📂 待处理文件: {len(todo_files)}")

    if not todo_files:
        print("\n✨ 所有文件都已处理完毕！")
        return

    # 显示前5个待处理文件的示例
    print("\n📋 待处理文件示例（前5个）:")
    for i, f in enumerate(todo_files[:5], 1):
        print(f"   {i}. {f.name}")

    # 询问用户是否继续
    print(f"\n⚠️  即将处理 {len(todo_files)} 个文件")
    response = input("是否继续？(y/n): ").strip().lower()

    if response != 'y':
        print("❌ 操作已取消")
        return

    # 处理文件
    results = {
        "SUCCESS": 0,
        "SKIP": 0,
        "ALREADY_GOOD": 0,
        "ERROR": 0
    }

    print("\n开始处理...\n")

    for file_path in tqdm(todo_files, desc="处理进度"):
        try:
            result = renamer.process_file(file_path)
            results[result] = results.get(result, 0) + 1
            time.sleep(1)  # 避免API限流
        except Exception as e:
            print(f"\n❌ 处理出错 {file_path.name}: {e}")
            results["ERROR"] += 1

    # 显示统计结果
    print("\n" + "=" * 60)
    print("📊 处理结果统计:")
    print(f"   ✅ 成功重命名: {results['SUCCESS']}")
    print(f"   ✓ 文件名已优: {results['ALREADY_GOOD']}")
    print(f"   ⏭️  跳过: {results['SKIP']}")
    print(f"   ❌ 错误: {results['ERROR']}")
    print("=" * 60)
    print(f"\n💾 备份文件保存在: {BACKUP_DIR}")


if __name__ == "__main__":
    main()
