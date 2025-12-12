#!/usr/bin/env python3
"""
Smart Label Clusterer (AI-Assisted)
===================================
Uses Sentence-BERT embeddings to automatically suggest mappings for unknown labels.
"""

import json
import sys
import numpy as np
from pathlib import Path
from collections import defaultdict
from colorama import Fore, Style, init

# 导入你之前的普通版 Normalizer，为了获取现有的字典作为“基准”
# 假设你的普通脚本叫 label_normalizer.py
try:
    from label_normalizer import LabelNormalizer
except ImportError:
    print("❌ 找不到 label_normalizer.py，请确保它在同一目录下")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("❌ 需要安装 AI 库: pip install sentence-transformers scikit-learn numpy colorama")
    sys.exit(1)

init(autoreset=True)

class SmartClusterer:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        print(f"⏳ Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.normalizer = LabelNormalizer()
        
        # 1. 提取所有已经确立的“标准类别” (Canonical Labels)
        # 我们只从 values 里提取，因为这些是我们的目标归宿
        self.canonical_labels = sorted(list(set(self.normalizer.DESIRE_LABEL_MAP.values())))
        print(f"✅ Loaded {len(self.canonical_labels)} canonical categories as anchors.")
        
        # 2. 预计算标准类别的向量 (Anchors)
        self.anchor_embeddings = self.model.encode(self.canonical_labels)
        
    def find_unknown_labels(self, input_dir):
        """扫描文件夹，找出所有不在字典里的新标签"""
        unknowns = set()
        path = Path(input_dir)
        files = list(path.glob("*.json"))
        
        print(f"📂 Scanning {len(files)} files for new labels...")
        
        for p in files:
            if "stats" in p.name or "rejected" in p.name: continue
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Check Desire Analysis
                for item in data.get("desire_motivation_analysis", []):
                    label = item.get("desire_label")
                    if label and label not in self.normalizer.DESIRE_LABEL_MAP:
                        unknowns.add(label)
                        
                # Check Transitions
                for trans in data.get("desire_transitions", []):
                    for key in ["desire_before", "desire_after"]:
                        if key in trans:
                            label = trans[key].get("label")
                            if label and label not in self.normalizer.DESIRE_LABEL_MAP:
                                unknowns.add(label)
            except:
                pass
                
        return sorted(list(unknowns))

    def suggest_mapping(self, new_label):
        """核心算法：计算新标签与标准类别的相似度"""
        # 1. 把新词变成向量
        new_vec = self.model.encode([new_label])
        
        # 2. 计算与所有锚点的余弦相似度
        scores = cosine_similarity(new_vec, self.anchor_embeddings)[0]
        
        # 3. 找到分数最高的 Top 3
        top_indices = np.argsort(scores)[::-1][:3]
        
        suggestions = []
        for idx in top_indices:
            suggestions.append({
                "label": self.canonical_labels[idx],
                "score": float(scores[idx])
            })
            
        return suggestions

    def interactive_mode(self, input_dir):
        unknowns = self.find_unknown_labels(input_dir)
        
        if not unknowns:
            print(Fore.GREEN + "\n🎉 No unknown labels found! Your dictionary is up to date.")
            return

        print(Fore.YELLOW + f"\n⚠️  Found {len(unknowns)} unknown labels. Entering AI Assistant Mode...\n")
        
        new_mappings = {}
        
        for i, unknown in enumerate(unknowns):
            print("-" * 60)
            print(f"[{i+1}/{len(unknowns)}] New Label: {Fore.CYAN}{Style.BRIGHT}{unknown}{Style.RESET_ALL}")
            
            # AI 计算推荐
            suggestions = self.suggest_mapping(unknown)
            top_pick = suggestions[0]
            
            # 打印推荐
            print(f"🤖 AI Suggestion: {Fore.GREEN}{top_pick['label']}{Style.RESET_ALL} (Confidence: {top_pick['score']:.2f})")
            
            # 如果置信度很高 (>0.85)，标记为推荐
            if top_pick['score'] > 0.85:
                print(f"   (Also close: {suggestions[1]['label']} - {suggestions[1]['score']:.2f})")
            
            # 交互输入
            print("\nOptions:")
            print(f"  [Enter] Accept AI suggestion: '{top_pick['label']}'")
            print(f"  [2] Accept 2nd choice: '{suggestions[1]['label']}'")
            print(f"  [s] Skip / Ignore")
            print(f"  [type] Type a different mapping manually")
            
            choice = input("👉 Your choice: ").strip()
            
            final_map = ""
            if choice == "":
                final_map = top_pick['label']
            elif choice == "2":
                final_map = suggestions[1]['label']
            elif choice.lower() == "s":
                print("Skipped.")
                continue
            else:
                final_map = choice # 用户手动输入
                
            if final_map:
                new_mappings[unknown] = final_map
                print(f"✅ Mapped: {unknown} -> {final_map}")

        # 最终输出 Python 代码供复制
        if new_mappings:
            print("\n" + "="*60)
            print("💾 COPY THIS INTO YOUR label_normalizer.py DESIRE_LABEL_MAP:")
            print("="*60)
            for k, v in new_mappings.items():
                print(f'        "{k}": "{v}",')
            print("="*60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI-Assisted Label Clustering")
    parser.add_argument("--input-dir", required=True, help="Path to annotations")
    args = parser.parse_args()
    
    clusterer = SmartClusterer()
    clusterer.interactive_mode(args.input_dir)