#!/usr/bin/env python3
"""
Hybrid Label Clustering - 混合聚类方法
=====================================
结合心理学理论分类 + 语义相似度聚类的混合方法

核心思路：
1. 第一层：按心理学维度分组（Social, Safety, Esteem, Epistemic...）
2. 第二层：在每个维度内进行语义聚类
3. 优点：既保留理论框架，又能自动处理细粒度相似标签

Features:
- Two-tier clustering (theory-driven + data-driven)
- Better interpretability for psychology research
- Automatic handling of new labels within known domains
- Enhanced visualization with hierarchical structure
"""

import json
import argparse
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional, Set
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.manifold import TSNE
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False
    print("⚠️  Missing libraries. Install with:")
    print("pip install sentence-transformers scikit-learn matplotlib seaborn")

try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False


class HybridClusterer:
    """
    混合聚类器 - 结合理论分类和数据驱动聚类

    Algorithm:
    1. Extract domain prefix (Social_, Safety_, Esteem_, etc.)
    2. Group labels by domain (theory-driven)
    3. Within each domain, cluster by semantic similarity
    4. Generate hierarchical mapping
    """

    # 定义心理学理论维度（一级分类）
    PSYCHOLOGICAL_DOMAINS = {
        "Social": ["Social"],
        "Safety": ["Safety"],
        "Esteem": ["Esteem"],
        "Epistemic": ["Epistemic"],
        "Cognitive": ["Cognitive"],
        "Physiological": ["Physiological"],
        "Emotional": ["Emotional"],
        "Resource": ["Resource"],
        "Belonging": ["Belonging"],  # Sometimes appears separately
    }

    def __init__(self,
                 model_name: str = "all-MiniLM-L6-v2",
                 intra_domain_threshold: float = 0.25):
        """
        Args:
            model_name: Sentence transformer model
            intra_domain_threshold: Distance threshold for clustering within domain
        """
        if not HAS_LIBS:
            raise ImportError("Required libraries not installed")

        print(f"🔄 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.intra_domain_threshold = intra_domain_threshold

        # Storage
        self.labels: List[str] = []
        self.label_counts: Dict[str, int] = {}
        self.domain_groups: Dict[str, List[str]] = defaultdict(list)
        self.hierarchical_mapping: Dict[str, Dict[str, str]] = {}  # {domain: {label: canonical}}
        self.flat_mapping: Dict[str, str] = {}  # Final flat mapping

    def _extract_domain(self, label: str) -> str:
        """提取标签的心理学维度（前缀）"""
        for domain in self.PSYCHOLOGICAL_DOMAINS:
            if label.startswith(domain + "_"):
                return domain
        return "Unknown"

    def _snake_to_natural(self, label: str) -> str:
        """Convert Snake_Case to natural language"""
        parts = label.split('_')
        natural = ' '.join(parts).lower()
        return f"desire: {natural}"

    def collect_labels(self, input_dir: str) -> Dict[str, int]:
        """收集所有标签"""
        input_path = Path(input_dir)
        label_counts = Counter()

        json_files = list(input_path.glob("*.json"))
        json_files = [f for f in json_files
                      if not f.name.startswith("stats_")
                      and f.name != "annotation_errors.json"]

        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    anno = json.load(f)

                # Collect from desire_motivation_analysis
                for desire in anno.get("desire_motivation_analysis", []):
                    label = desire.get("desire_label", "")
                    if label:
                        label_counts[label] += 1

                # Collect from desire_transitions
                for trans in anno.get("desire_transitions", []):
                    for key in ["desire_before", "desire_after"]:
                        if key in trans and "label" in trans[key]:
                            label = trans[key]["label"]
                            if label:
                                label_counts[label] += 1

            except Exception as e:
                print(f"⚠️  Error reading {file_path.name}: {e}")

        self.label_counts = dict(label_counts)
        self.labels = list(label_counts.keys())

        print(f"📊 Found {len(self.labels)} unique labels")
        return self.label_counts

    def group_by_domain(self):
        """第一步：按心理学维度分组"""
        for label in self.labels:
            domain = self._extract_domain(label)
            self.domain_groups[domain].append(label)

        print(f"\n📂 Grouped into {len(self.domain_groups)} psychological domains:")
        for domain, labels in sorted(self.domain_groups.items()):
            print(f"   {domain}: {len(labels)} labels")

    def cluster_within_domain(self, domain: str, labels: List[str]) -> Dict[str, str]:
        """第二步：在每个维度内进行语义聚类"""
        if len(labels) <= 1:
            return {labels[0]: labels[0]} if labels else {}

        # Compute embeddings
        natural_labels = [self._snake_to_natural(label) for label in labels]
        embeddings = self.model.encode(natural_labels)

        # Determine number of clusters (adaptive)
        if len(labels) <= 3:
            n_clusters = len(labels)  # No clustering needed
        else:
            # Use distance threshold for hierarchical clustering
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=self.intra_domain_threshold,
                metric='cosine',
                linkage='average'
            )
            cluster_assignments = clustering.fit_predict(embeddings)

            # Group by cluster
            cluster_groups = defaultdict(list)
            for label, cluster_id in zip(labels, cluster_assignments):
                cluster_groups[cluster_id].append(label)

            # Select representative for each cluster
            mapping = {}
            for cluster_id, cluster_members in cluster_groups.items():
                # Get embeddings for this cluster
                member_indices = [labels.index(m) for m in cluster_members]
                cluster_embeddings = embeddings[member_indices]

                # Select representative (most frequent + most central)
                representative = self._select_representative(
                    cluster_members, cluster_embeddings
                )

                for member in cluster_members:
                    mapping[member] = representative

            return mapping

        # Fallback: no clustering
        return {label: label for label in labels}

    def _select_representative(self, labels: List[str], embeddings: np.ndarray) -> str:
        """选择聚类代表（最频繁 + 最中心）"""
        if len(labels) == 1:
            return labels[0]

        centroid = np.mean(embeddings, axis=0)

        scores = []
        for i, (label, emb) in enumerate(zip(labels, embeddings)):
            # Distance to centroid
            dist = 1 - cosine_similarity([emb], [centroid])[0][0]
            # Frequency
            count = self.label_counts.get(label, 1)
            # Combined score (lower is better)
            score = dist - 0.15 * np.log1p(count)
            scores.append((score, label))

        scores.sort()
        return scores[0][1]

    def build_hierarchical_mapping(self):
        """构建层次化映射"""
        print(f"\n🔗 Clustering within each domain...")

        for domain, labels in self.domain_groups.items():
            if domain == "Unknown":
                # Handle unknown domain separately
                self.hierarchical_mapping[domain] = {label: label for label in labels}
                print(f"   ⚠️  {domain}: {len(labels)} labels (kept as-is)")
            else:
                mapping = self.cluster_within_domain(domain, labels)
                self.hierarchical_mapping[domain] = mapping

                # Count clusters
                n_clusters = len(set(mapping.values()))
                print(f"   ✅ {domain}: {len(labels)} labels → {n_clusters} clusters")

        # Build flat mapping
        for domain, mapping in self.hierarchical_mapping.items():
            self.flat_mapping.update(mapping)

    def print_results(self, show_members: bool = True):
        """打印聚类结果"""
        print("\n" + "=" * 80)
        print("📊 HYBRID CLUSTERING RESULTS (Theory-Driven + Data-Driven)")
        print("=" * 80)

        for domain in sorted(self.hierarchical_mapping.keys()):
            mapping = self.hierarchical_mapping[domain]
            labels = self.domain_groups[domain]

            # Group by canonical label
            canonical_groups = defaultdict(list)
            for label, canonical in mapping.items():
                canonical_groups[canonical].append(label)

            print(f"\n📁 {domain} Domain ({len(labels)} labels → {len(canonical_groups)} clusters)")
            print("-" * 80)

            # Sort by total count
            canonical_with_counts = []
            for canonical, members in canonical_groups.items():
                total_count = sum(self.label_counts.get(m, 0) for m in members)
                canonical_with_counts.append((total_count, canonical, members))

            canonical_with_counts.sort(reverse=True)

            for total_count, canonical, members in canonical_with_counts:
                print(f"   🏷️  {canonical} (n={total_count})")

                if show_members and len(members) > 1:
                    for member in sorted(members):
                        if member != canonical:
                            count = self.label_counts.get(member, 0)
                            print(f"       ↳ {member} (n={count})")

        print("\n" + "=" * 80)
        total_labels = len(self.labels)
        total_clusters = len(set(self.flat_mapping.values()))
        print(f"📈 Summary: {total_labels} labels → {total_clusters} canonical labels")
        print("=" * 80)

    def visualize_hierarchical(self, output_path: str = "data/hybrid_clusters.png"):
        """可视化：按维度着色的层次化t-SNE图"""
        if not HAS_LIBS:
            print("⚠️  Visualization libraries not available")
            return

        # Compute embeddings for all labels
        natural_labels = [self._snake_to_natural(label) for label in self.labels]
        embeddings = self.model.encode(natural_labels, show_progress_bar=True)

        # t-SNE projection
        print("📊 Generating t-SNE projection...")
        tsne = TSNE(n_components=2, random_state=42,
                   perplexity=min(30, len(self.labels)-1),
                   init='pca', learning_rate='auto')
        projections = tsne.fit_transform(embeddings)

        # Setup plot
        sns.set_style("white")
        sns.set_context("paper", font_scale=1.2)

        fig, ax = plt.subplots(figsize=(18, 14))

        # Color by domain
        domain_list = [self._extract_domain(label) for label in self.labels]
        unique_domains = sorted(list(set(domain_list)))

        # Use distinct colors for each domain
        domain_colors = sns.color_palette("husl", len(unique_domains))
        domain_to_color = {d: domain_colors[i] for i, d in enumerate(unique_domains)}

        colors = [domain_to_color[d] for d in domain_list]

        # Size by frequency
        sizes = [100 + np.log1p(self.label_counts.get(l, 1)) * 100 for l in self.labels]

        # Scatter plot
        for domain in unique_domains:
            mask = [d == domain for d in domain_list]
            domain_x = projections[mask, 0]
            domain_y = projections[mask, 1]
            domain_sizes = [s for s, m in zip(sizes, mask) if m]

            ax.scatter(domain_x, domain_y,
                      c=[domain_to_color[domain]],
                      s=domain_sizes,
                      alpha=0.7,
                      edgecolors='w',
                      linewidth=0.5,
                      label=f"{domain} ({sum(mask)})")

        # Add labels for canonical representatives
        texts = []
        canonical_labels = set(self.flat_mapping.values())

        for i, label in enumerate(self.labels):
            # Only show canonical labels or high-frequency labels
            is_canonical = label in canonical_labels and label == self.flat_mapping[label]
            is_frequent = self.label_counts.get(label, 0) >= 3

            if is_canonical or is_frequent:
                display_label = label.replace('_', '\n')
                weight = 'bold' if is_canonical else 'normal'
                fontsize = 9 if is_canonical else 7

                texts.append(ax.text(
                    projections[i, 0],
                    projections[i, 1],
                    display_label,
                    fontsize=fontsize,
                    fontweight=weight,
                    alpha=0.9
                ))

        # Adjust text positions
        if HAS_ADJUST_TEXT and len(texts) > 0:
            print("✨ Optimizing label positions...")
            adjust_text(
                texts,
                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.3, lw=0.5),
                expand_points=(1.5, 1.5)
            )

        # Styling
        ax.set_title("Hybrid Clustering: Psychological Domains + Semantic Similarity",
                    fontsize=16, pad=20, fontweight='bold')
        ax.set_xticks([])
        ax.set_yticks([])

        # Legend
        ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5),
                 fontsize=10, frameon=True, title="Psychological Domains")

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"💾 Saved visualization to {output_path}")

    def save_mapping(self, output_path: str):
        """保存映射结果"""
        mapping_data = {
            "method": "hybrid_clustering",
            "description": "Theory-driven (domain) + Data-driven (semantic)",
            "model": "all-MiniLM-L6-v2",
            "intra_domain_threshold": self.intra_domain_threshold,
            "total_labels": len(self.labels),
            "total_canonical": len(set(self.flat_mapping.values())),
            "domains": {},
            "flat_mapping": self.flat_mapping
        }

        # Add domain-wise info
        for domain, mapping in self.hierarchical_mapping.items():
            canonical_set = set(mapping.values())
            mapping_data["domains"][domain] = {
                "n_labels": len(self.domain_groups[domain]),
                "n_clusters": len(canonical_set),
                "canonical_labels": sorted(list(canonical_set)),
                "mapping": mapping
            }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)

        print(f"💾 Saved mapping to {output_path}")

    def export_python_dict(self, output_path: str):
        """导出为Python字典格式（可直接用于代码）"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Auto-generated by hybrid_label_clustering.py\n")
            f.write("# Hybrid method: Theory-driven domains + Data-driven clustering\n\n")
            f.write("HYBRID_DESIRE_LABEL_MAP = {\n")

            for domain in sorted(self.hierarchical_mapping.keys()):
                f.write(f"\n    # ----- {domain} Domain -----\n")
                mapping = self.hierarchical_mapping[domain]

                for original, canonical in sorted(mapping.items()):
                    f.write(f'    "{original}": "{canonical}",\n')

            f.write("}\n")

        print(f"💾 Exported Python dict to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Hybrid Label Clustering (Theory + Data)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python hybrid_label_clustering.py --input-dir data/annotations_test

  # Adjust clustering threshold (lower = more clusters)
  python hybrid_label_clustering.py --input-dir data/annotations_test --threshold 0.2

  # Generate visualization
  python hybrid_label_clustering.py --input-dir data/annotations_test --visualize

  # Save mapping
  python hybrid_label_clustering.py --input-dir data/annotations_test --save-mapping data/hybrid_mapping.json
        """
    )

    parser.add_argument("--input-dir", "-i", required=True,
                       help="Directory with annotation files")
    parser.add_argument("--threshold", "-t", type=float, default=0.25,
                       help="Distance threshold for intra-domain clustering (default: 0.25)")
    parser.add_argument("--visualize", "-v", action="store_true",
                       help="Generate visualization")
    parser.add_argument("--save-mapping", "-m", type=str, default=None,
                       help="Save mapping to JSON file")
    parser.add_argument("--export-python", "-p", type=str, default=None,
                       help="Export as Python dict")

    args = parser.parse_args()

    # Initialize
    clusterer = HybridClusterer(intra_domain_threshold=args.threshold)

    # Process
    clusterer.collect_labels(args.input_dir)
    clusterer.group_by_domain()
    clusterer.build_hierarchical_mapping()

    # Print results
    clusterer.print_results(show_members=True)

    # Save outputs
    if args.save_mapping:
        clusterer.save_mapping(args.save_mapping)

    if args.export_python:
        clusterer.export_python_dict(args.export_python)

    if args.visualize:
        viz_path = args.save_mapping.replace('.json', '.png') if args.save_mapping else "data/hybrid_clusters.png"
        clusterer.visualize_hierarchical(viz_path)

    return 0


if __name__ == "__main__":
    exit(main())
