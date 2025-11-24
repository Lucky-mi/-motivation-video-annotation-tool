import json
import os
import time
import shutil
import re
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
import google.generativeai as genai

# 加载配置
from config.config import config
load_dotenv(override=True)

# 路径配置
VIDEOS_DIR = Path("data/videos")
KEYFRAMES_DIR = Path("data/keyframes")
ANNOTATIONS_DIR = Path("data/annotations")
BACKUP_DIR = Path("data/annotations_backup")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)

class VisualRewriter:
    def __init__(self):
        api_key = config.get_api_key('gemini')
        if not api_key:
            raise ValueError("❌ 未找到 API Key")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def try_find_image(self, original_path):
        """智能寻图：如果原路径找不到，尝试搜索同名文件"""
        path_obj = Path(original_path)
        
        # 1. 直接检查原路径
        if path_obj.exists():
            return path_obj
            
        # 2. 尝试在 KEYFRAMES_DIR 下递归搜索同名文件
        # (应对文件夹被重命名但文件名没变的情况)
        filename = path_obj.name
        found = list(KEYFRAMES_DIR.rglob(filename))
        
        if found:
            # 如果找到多个，优先选路径最短的（通常是最匹配的）
            return found[0]
            
        return None

    def get_character_visual_description(self, name, frame_path):
        """看图说话：生成人物的视觉描述"""
        
        # === 增强：智能查找图片 ===
        real_img_path = self.try_find_image(frame_path)
        
        if not real_img_path:
            print(f"    ❌ 图片丢失: {Path(frame_path).name}")
            return f"Person ({name})" # 降级

        img_file = genai.upload_file(path=str(real_img_path))
        
        # 等待文件就绪
        while img_file.state.name == "PROCESSING":
            time.sleep(1)
            img_file = genai.get_file(img_file.name)

        prompt = f"""
        Look at this image. The person named "{name}" is in this scene.
        Please provide a **very short, distinctive visual description** for this person to anonymize them.
        
        Rules:
        1. Use format: "the [gender] in [distinctive clothing/feature]"
        2. Example: "the man in the red suit", "the woman with blonde hair", "the girl in the pink shirt".
        3. Max 6 words.
        4. Strictly NO proper names in the output.
        5. Output ONLY the description.
        """
        
        try:
            response = self.model.generate_content([img_file, prompt])
            description = response.text.strip().replace('"', '').replace("'", "").lower()
            
            # 简单清洗：如果AI还是输出了名字，强制修正
            if name.lower() in description:
                description = f"the person in the scene"

            genai.delete_file(img_file.name)
            return description
        except Exception as e:
            print(f"    ⚠️ 视觉分析失败: {e}")
            return f"Person ({name})"

    def process_video(self, file_path: Path):
        """处理单个视频标注文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data.get('is_anonymized_visual', False):
            return "SKIP"

        keyframes = data.get('keyframes', [])
        if not keyframes: return "EMPTY"

        print(f"🔍 分析人物: {file_path.name}")

        # 1. 提取名字 (文本模式)
        # 简单粗暴策略：直接让模型列出名字
        text_prompt = f"""
        Extract all character names from this JSON data.
        Return a JSON list of strings, e.g., ["Jason", "Regina"].
        Ignore generic terms like "Man", "Woman".
        JSON Data: {json.dumps(keyframes)[:3000]}...
        """
        try:
            resp = self.model.generate_content(text_prompt)
            names_text = resp.text
            if "```json" in names_text:
                names_text = names_text.split("```json")[1].split("```")[0]
            names = json.loads(names_text)
        except:
            print("    ⚠️ 无法提取名字")
            return "ERROR"

        if not names:
            # 如果没名字，标记为已处理并跳过
            data['is_anonymized_visual'] = True
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return "NO_NAMES"

        # 2. 为每个名字生成视觉描述
        name_map = {}
        for name in names:
            # 排除已经是描述性的名字
            if len(name.split()) > 3 or name.lower().startswith("the "):
                continue

            target_frame = None
            for kf in keyframes:
                # 拼接所有文本字段来查找名字
                content = json.dumps(kf)
                if name in content:
                    target_frame = kf.get('frame_path')
                    break
            
            if target_frame:
                print(f"  📸 正在观察: {name} ...")
                desc = self.get_character_visual_description(name, target_frame)
                name_map[name] = desc
                print(f"     -> 映射为: {desc}")
                time.sleep(1) 
            else:
                name_map[name] = f"Person ({name})"

        # 3. 全局替换
        json_str = json.dumps(data)
        for name, desc in name_map.items():
            # 使用正则全词匹配，防止替换部分单词
            # e.g. 避免把 "Jason" 替换后影响 "Jason's car"
            pattern = re.compile(r'\b' + re.escape(name) + r'\b')
            json_str = pattern.sub(desc, json_str)

        new_data = json.loads(json_str)
        new_data['is_anonymized_visual'] = True
        new_data['character_map'] = name_map 

        # 备份
        backup_path = BACKUP_DIR / file_path.name
        shutil.copy2(file_path, backup_path)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
            
        return "SUCCESS"

def main():
    print("========================================")
    print("   👁️ 视觉增强版：人物匿名化工具 (V2)")
    print("   包含智能寻图功能")
    print("========================================")
    
    rewriter = VisualRewriter()
    files = list(ANNOTATIONS_DIR.glob("*.json"))
    
    todo_files = []
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as j:
                if not json.load(j).get('is_anonymized_visual'):
                    todo_files.append(f)
        except: pass

    print(f"📂 待处理文件: {len(todo_files)}")
    
    if not todo_files:
        print("✨ 所有文件都已处理完毕！")
        return

    for file_path in tqdm(todo_files):
        try:
            rewriter.process_video(file_path)
            time.sleep(1)
        except Exception as e:
            print(f"❌ 处理出错 {file_path.name}: {e}")

if __name__ == "__main__":
    main()