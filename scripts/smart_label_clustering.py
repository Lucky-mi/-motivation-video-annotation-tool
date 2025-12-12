#!/usr/bin/env python3
"""
Intelligent Desire Label Clustering
====================================
Uses word embeddings + hierarchical clustering to automatically group
semantically similar desire labels.

Features:
- No fixed dictionary needed
- Handles new/unseen labels automatically
- Uses sentence transformers for semantic similarity
- Hierarchical clustering with configurable granularity
- Generates cluster representatives automatically

Usage:
    python smart_label_clustering.py --input-dir data/annotations_test --n-clusters 20
    python smart_label_clustering.py --input-dir data/annotations_test --threshold 0.3
    python smart_label_clustering.py --input-dir data/annotations_test --visualize
"""

import json
import argparse
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import numpy as np
# ... (保留原有的 imports)
try:
    import matplotlib.pyplot as plt
    import seaborn as sns  # 新增
    from adjustText import adjust_text # 新增
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import plotly.express as px # 新增
    import pandas as pd # 新增
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
# Check for required packages
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.manifold import TSNE
    from sklearn.metrics import (
        silhouette_score,
        davies_bouldin_score,
        calinski_harabasz_score,
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# 可选：UMAP 降维（若未安装将自动降级到 t-SNE）
try:
    import umap  # type: ignore
    HAS_UMAP = True
except ImportError:
    HAS_UMAP = False

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


@dataclass
class LabelCluster:
    """Represents a cluster of semantically similar labels."""
    cluster_id: int
    canonical_label: str  # Representative label for the cluster
    members: List[str]    # All labels in this cluster
    member_counts: Dict[str, int]  # Count of each label
    centroid: Optional[np.ndarray] = None
    
    @property
    def total_count(self) -> int:
        return sum(self.member_counts.values())
    
    def __repr__(self):
        return f"Cluster({self.canonical_label}, {len(self.members)} members, {self.total_count} occurrences)"


class SmartLabelClusterer:
    """
    Clusters desire labels using semantic embeddings.
    
    Algorithm:
    1. Convert Snake_Case labels to natural language
    2. Embed using sentence transformers
    3. Hierarchical clustering based on cosine similarity
    4. Select cluster representatives (most frequent or most central)
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",  # Fast and good quality
        n_clusters: Optional[int] = None,
        distance_threshold: Optional[float] = None,
        use_umap: bool = False,
    ):
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError(
                "sentence-transformers not installed. Run:\n"
                "pip install sentence-transformers --break-system-packages"
            )
        if not HAS_SKLEARN:
            raise ImportError(
                "scikit-learn not installed. Run:\n"
                "pip install scikit-learn --break-system-packages"
            )
        
        print(f"🔄 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.n_clusters = n_clusters
        self.distance_threshold = distance_threshold
        self.use_umap = use_umap and HAS_UMAP
        
        # Storage
        self.labels: List[str] = []
        self.label_counts: Dict[str, int] = {}
        self.embeddings: Optional[np.ndarray] = None
        self.clusters: List[LabelCluster] = []
        self.label_to_cluster: Dict[str, str] = {}
    
    def _snake_to_natural(self, label: str) -> str:
        """Convert Snake_Case label to natural language for embedding."""
        # Split by underscore
        parts = label.split('_')
        # Join with spaces and lowercase
        natural = ' '.join(parts).lower()
        # Add context for better embedding
        return f"psychological desire: {natural}"
    
    def _select_representative(self, cluster_labels: List[str], cluster_embeddings: np.ndarray) -> str:
        """
        Select the most representative label for a cluster.
        Strategy: Choose the label closest to cluster centroid AND has high frequency.
        """
        if len(cluster_labels) == 1:
            return cluster_labels[0]
        
        # Calculate centroid
        centroid = np.mean(cluster_embeddings, axis=0)
        
        # Calculate distance to centroid for each label
        distances = []
        for i, emb in enumerate(cluster_embeddings):
            dist = 1 - cosine_similarity([emb], [centroid])[0][0]
            count = self.label_counts.get(cluster_labels[i], 1)
            # Score: lower distance + higher count = better
            # Normalize: distance is [0,2], count can be anything
            score = dist - 0.1 * np.log1p(count)  # Log count to prevent domination
            distances.append((score, cluster_labels[i]))
        
        # Return the label with best score (lowest)
        distances.sort()
        return distances[0][1]
    
    def _simplify_label(self, label: str) -> str:
        """
        Simplify a label to make it more canonical.
        Remove redundant suffixes, standardize format.
        """
        # Common simplifications
        simplifications = [
            ('_Seeking', ''),
            ('_Maintenance', ''),
            ('_Avoidance', ''),
            ('_Display', ''),
            ('_Provision', ''),
            ('_Expression', ''),
            ('_Resolution', ''),
        ]
        
        result = label
        for old, new in simplifications:
            if result.endswith(old) and len(result) > len(old) + 5:
                # Only simplify if there's meaningful content left
                simplified = result.replace(old, new)
                if simplified:
                    result = simplified
                    break
        
        return result
    
    def collect_labels(self, input_dir: str) -> Dict[str, int]:
        """Collect all unique desire labels from annotation files."""
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
    
    def compute_embeddings(self) -> np.ndarray:
        """Compute embeddings for all labels."""
        if not self.labels:
            raise ValueError("No labels collected. Run collect_labels first.")
        
        # Convert to natural language
        natural_labels = [self._snake_to_natural(label) for label in self.labels]
        
        print(f"🧠 Computing embeddings for {len(natural_labels)} labels...")
        self.embeddings = self.model.encode(natural_labels, show_progress_bar=True)
        
        return self.embeddings
    
    def _auto_select_n_clusters(self) -> int:
        """
        基于多指标自动选择簇数（仅在未显式指定 n_clusters/threshold 时启用）。
        返回推荐的 n_clusters。
        """
        n_labels = len(self.labels)
        # 候选范围：5 到 30 之间，且不超过样本数-1
        candidates = sorted(
            set(
                [
                    max(2, n_labels // 6),
                    max(3, n_labels // 5),
                    max(4, n_labels // 4),
                    max(5, n_labels // 3),
                    8,
                    12,
                    16,
                    20,
                    24,
                    min(30, n_labels - 1),
                ]
            )
        )
        scores = []
        for k in candidates:
            if k <= 1 or k >= n_labels:
                continue
            try:
                clustering = AgglomerativeClustering(
                    n_clusters=k, metric="cosine", linkage="average"
                )
                labels_pred = clustering.fit_predict(self.embeddings)
                # 需要至少 2 个簇且每簇 >1 个点，避免 silhouette 失败
                if len(set(labels_pred)) < 2:
                    continue
                sil = silhouette_score(self.embeddings, labels_pred, metric="cosine")
                db = davies_bouldin_score(self.embeddings, labels_pred)
                ch = calinski_harabasz_score(self.embeddings, labels_pred)
                # 综合评分：sil 较大好，db 较小好，ch 较大好
                composite = sil * 0.6 + (1 / (1 + db)) * 0.2 + np.log1p(ch) * 0.2
                scores.append((composite, sil, db, ch, k))
            except Exception:
                continue
        if not scores:
            # 回退策略
            return min(25, max(5, n_labels // 4))
        scores.sort(reverse=True, key=lambda x: x[0])
        best_k = scores[0][4]
        print(
            f"🤖 Auto-tune picked n_clusters={best_k} "
            f"(sil={scores[0][1]:.3f}, db={scores[0][2]:.3f}, ch={scores[0][3]:.1f})"
        )
        return best_k

    def cluster_labels(self, auto_tune: bool = False) -> List[LabelCluster]:
        """Perform hierarchical clustering on label embeddings."""
        if self.embeddings is None:
            self.compute_embeddings()
        
        # Auto-tune n_clusters when user didn't specify
        if (
            auto_tune
            and self.n_clusters is None
            and self.distance_threshold is None
            and len(self.labels) >= 6
        ):
            self.n_clusters = self._auto_select_n_clusters()

        # Determine clustering parameters
        if self.n_clusters is not None:
            clustering = AgglomerativeClustering(
                n_clusters=self.n_clusters,
                metric='cosine',
                linkage='average'
            )
        elif self.distance_threshold is not None:
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=self.distance_threshold,
                metric='cosine',
                linkage='average'
            )
        else:
            # Default: aim for ~20 clusters or use threshold
            n_labels = len(self.labels)
            if n_labels <= 25:
                self.n_clusters = max(5, n_labels // 2)
            else:
                self.n_clusters = min(25, max(10, n_labels // 4))
            
            clustering = AgglomerativeClustering(
                n_clusters=self.n_clusters,
                metric='cosine',
                linkage='average'
            )
        
        print(f"🔗 Clustering with {'n_clusters=' + str(self.n_clusters) if self.n_clusters else 'threshold=' + str(self.distance_threshold)}...")
        cluster_assignments = clustering.fit_predict(self.embeddings)
        
        # Group labels by cluster
        cluster_groups = defaultdict(list)
        for label, cluster_id in zip(self.labels, cluster_assignments):
            cluster_groups[cluster_id].append(label)
        
        # Create LabelCluster objects
        self.clusters = []
        for cluster_id, members in cluster_groups.items():
            # Get embeddings for this cluster
            member_indices = [self.labels.index(m) for m in members]
            cluster_embeddings = self.embeddings[member_indices]
            
            # Select representative
            representative = self._select_representative(members, cluster_embeddings)
            
            # Compute centroid
            centroid = np.mean(cluster_embeddings, axis=0)
            
            # Get counts
            member_counts = {m: self.label_counts.get(m, 0) for m in members}
            
            cluster = LabelCluster(
                cluster_id=cluster_id,
                canonical_label=representative,
                members=sorted(members),
                member_counts=member_counts,
                centroid=centroid
            )
            self.clusters.append(cluster)
        
        # Sort clusters by total count
        self.clusters.sort(key=lambda c: c.total_count, reverse=True)
        
        # Reassign cluster IDs after sorting
        for i, cluster in enumerate(self.clusters):
            cluster.cluster_id = i
        
        # Build mapping
        self.label_to_cluster = {}
        for cluster in self.clusters:
            for member in cluster.members:
                self.label_to_cluster[member] = cluster.canonical_label
        
        print(f"✅ Created {len(self.clusters)} clusters")
        return self.clusters
    
    def print_clusters(self, show_members: bool = True):
        """Print cluster information."""
        print("\n" + "=" * 70)
        print("📊 LABEL CLUSTERS (Semantic Grouping)")
        print("=" * 70)
        
        for cluster in self.clusters:
            print(f"\n🏷️  Cluster {cluster.cluster_id}: {cluster.canonical_label}")
            print(f"    Total occurrences: {cluster.total_count}")
            
            if show_members and len(cluster.members) > 1:
                print(f"    Members ({len(cluster.members)}):")
                for member in cluster.members:
                    count = cluster.member_counts.get(member, 0)
                    marker = "→" if member == cluster.canonical_label else " "
                    print(f"      {marker} {member}: {count}")
        
        print("\n" + "=" * 70)
        print(f"📈 Summary: {len(self.labels)} labels → {len(self.clusters)} clusters")
        print("=" * 70)
    
    def get_mapping(self) -> Dict[str, str]:
        """Get the label to canonical label mapping."""
        return self.label_to_cluster.copy()

    def _reduce_dimensionality(self) -> np.ndarray:
        """
        降维封装：优先用 UMAP（若安装且启用），否则用 t-SNE。
        会根据样本量自动调整 perplexity。
        """
        if self.embeddings is None:
            raise ValueError("Embeddings not computed.")

        n_samples = len(self.labels)
        if self.use_umap and HAS_UMAP and n_samples >= 5:
            reducer = umap.UMAP(
                n_components=2,
                metric="cosine",
                random_state=42,
                min_dist=0.1,
                n_neighbors=min(30, max(5, n_samples // 2)),
            )
            return reducer.fit_transform(self.embeddings)

        # t-SNE 回退
        perplexity = max(5, min(30, n_samples - 1))
        tsne = TSNE(
            n_components=2,
            random_state=42,
            perplexity=perplexity,
            init='pca',
            learning_rate='auto'
        )
        return tsne.fit_transform(self.embeddings)

    def visualize_interactive(self, output_path: str = "data/desire_map.html"):
        """Generate an interactive HTML plot using Plotly."""
        try:
            import plotly.express as px
            import pandas as pd
        except ImportError:
            print("⚠️ Plotly not installed. (pip install plotly pandas)")
            return

        if self.embeddings is None:
            self.compute_embeddings()
            self.cluster_labels()

        # 降维（UMAP 优先，t-SNE 回退）
        projections = self._reduce_dimensionality()

        # 准备数据框
        df = pd.DataFrame({
            'x': projections[:, 0],
            'y': projections[:, 1],
            'label': self.labels,
            'cluster': [self.label_to_cluster[l] for l in self.labels],
            'count': [self.label_counts[l] for l in self.labels],
            'size': [np.log1p(self.label_counts[l])*10 for l in self.labels] # 大小映射
        })

        # 绘图
        fig = px.scatter(
            df, x='x', y='y',
            color='cluster',
            size='size',
            hover_name='label',
            hover_data={'x': False, 'y': False, 'count': True, 'cluster': False},
            text='label', # 默认显示标签
            title='Interactive Desire Semantic Map',
            template='plotly_white',
            width=1200, height=800
        )

        # 优化文字显示 (只显示大点，其他的鼠标放上去才显示)
        fig.update_traces(textposition='top center')
        
        # 隐藏坐标轴
        fig.update_xaxes(showticklabels=False, title='')
        fig.update_yaxes(showticklabels=False, title='')

        # 保存
        fig.write_html(output_path)
        print(f"💾 Saved interactive map to {output_path}")
    def visualize_clusters(self, output_path: Optional[str] = None):
        """Visualize clusters using t-SNE with scientific styling."""
        if not HAS_MATPLOTLIB:
            print("⚠️  matplotlib not installed. Cannot visualize.")
            return
        
        # 尝试导入 adjustText，如果没装就降级处理
        try:
            from adjustText import adjust_text
            HAS_ADJUST_TEXT = True
        except ImportError:
            print("⚠️  adjustText not installed. Labels might overlap. (pip install adjustText)")
            HAS_ADJUST_TEXT = False

        if self.embeddings is None or len(self.clusters) == 0:
            print("⚠️  Run clustering first.")
            return
        
        print("📊 Generating scientific visualization...")
        
        # 1. 降维（UMAP 优先，t-SNE 回退）
        embeddings_2d = self._reduce_dimensionality()
        
        # 2. 准备绘图数据
        cluster_map = {c.canonical_label: c.cluster_id for c in self.clusters}
        cluster_ids = [cluster_map[self.label_to_cluster[l]] for l in self.labels]
        
        # 3. 设置科研风格 (Seaborn style)
        try:
            import seaborn as sns
            sns.set_style("white")  # 纯白背景，去掉了网格，更适合t-SNE
            sns.set_context("paper", font_scale=1.2) # 论文级字体大小
        except ImportError:
            plt.style.use('seaborn-white')

        # 创建画布 (稍微大一点)
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # 4. 绘制散点 (Scatter)
        # 使用 tab20 调色板，如果聚类超过20个，可以用 'nipy_spectral' 或 'turbo'
        cmap = plt.get_cmap('tab20' if len(self.clusters) <= 20 else 'nipy_spectral')
        
        # 根据频率调整点的大小 (Log scale 防止大点遮挡小点)
        sizes = [100 + np.log1p(self.label_counts.get(l, 1)) * 100 for l in self.labels]
        
        scatter = ax.scatter(
            embeddings_2d[:, 0], 
            embeddings_2d[:, 1],
            c=cluster_ids,
            cmap=cmap,
            alpha=0.7,      # 透明度，体现重叠密度
            s=sizes,        # 动态大小
            edgecolors='w', # 白色描边，增加对比度
            linewidth=0.5
        )
        
        # 5. 智能添加标签 (Annotation)
        texts = []
        for i, label in enumerate(self.labels):
            # 只显示出现频率 >= 2 的标签，或者是该 Cluster 的核心代表词
            is_representative = label in [c.canonical_label for c in self.clusters]
            if self.label_counts.get(label, 0) >= 2 or is_representative:
                # 格式化标签：把下划线换成换行符，或者去掉 Desire 前缀让图更清爽
                display_label = label.replace('_', '\n') 
                
                # 如果是代表词，加粗显示
                weight = 'bold' if is_representative else 'normal'
                fontsize = 9 if is_representative else 8
                
                texts.append(ax.text(
                    embeddings_2d[i, 0], 
                    embeddings_2d[i, 1],
                    display_label,
                    fontsize=fontsize,
                    fontweight=weight,
                    alpha=0.9
                ))
        
        # 6. 自动避让 (关键步骤！)
        if HAS_ADJUST_TEXT:
            print("✨ Optimizing label positions (this may take a moment)...")
            adjust_text(
                texts, 
                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.2, lw=0.5),
                expand_points=(1.5, 1.5) # 让文字离点远一点
            )
        
        # 7. 美化图例和坐标轴
        ax.set_title("Semantic Landscape of Desire Labels", fontsize=16, pad=20)
        
        # 移除 t-SNE 的坐标轴刻度 (因为它们没有物理意义)
        ax.set_xticks([])
        ax.set_yticks([])
        
        # 创建优雅的图例
        # 获取每个 cluster 的颜色
        unique_clusters = sorted(list(set(cluster_ids)))
        legend_elements = []
        for cid in unique_clusters:
            # 找到对应的 cluster 对象
            cluster = next(c for c in self.clusters if c.cluster_id == cid)
            color = cmap(cid / (max(unique_clusters) if max(unique_clusters)>0 else 1))
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                            label=f"{cluster.canonical_label} (n={cluster.total_count})",
                                            markerfacecolor=color, markersize=8))

        # 图例放外面
        ax.legend(handles=legend_elements, loc='center left', 
                  bbox_to_anchor=(1.02, 0.5), fontsize=10, frameon=False)
        
        plt.tight_layout()
        
        # 8. 保存高清图 (300 DPI)
        if output_path:
            # 如果是 png，用 300 dpi；如果是 pdf，那是矢量图最好
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"💾 Saved high-res visualization to {output_path}")
        else:
            plt.show()
    
    def apply_to_annotations(
        self, 
        input_dir: str, 
        output_dir: str,
        dry_run: bool = False
    ) -> Dict:
        """Apply clustering to normalize annotations."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not dry_run:
            output_path.mkdir(parents=True, exist_ok=True)
        
        stats = {
            "files_processed": 0,
            "labels_normalized": 0,
            "new_labels_found": []
        }
        
        json_files = list(input_path.glob("*.json"))
        json_files = [f for f in json_files 
                      if not f.name.startswith("stats_") 
                      and f.name != "annotation_errors.json"]
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    anno = json.load(f)
                
                modified = False
                
                # Normalize desire_motivation_analysis
                for desire in anno.get("desire_motivation_analysis", []):
                    original = desire.get("desire_label", "")
                    if original in self.label_to_cluster:
                        canonical = self.label_to_cluster[original]
                        if original != canonical:
                            desire["desire_label"] = canonical
                            desire["original_label"] = original
                            stats["labels_normalized"] += 1
                            modified = True
                    elif original:
                        # New label not in our clusters
                        stats["new_labels_found"].append(original)
                
                # Normalize desire_transitions
                for trans in anno.get("desire_transitions", []):
                    for key in ["desire_before", "desire_after"]:
                        if key in trans and "label" in trans[key]:
                            original = trans[key]["label"]
                            if original in self.label_to_cluster:
                                canonical = self.label_to_cluster[original]
                                if original != canonical:
                                    trans[key]["label"] = canonical
                                    trans[key]["original_label"] = original
                                    modified = True
                
                if modified:
                    anno.setdefault("annotation_metadata", {})
                    anno["annotation_metadata"]["labels_clustered"] = True
                    anno["annotation_metadata"]["clustering_method"] = "semantic_embedding"
                
                stats["files_processed"] += 1
                
                if not dry_run:
                    out_file = output_path / file_path.name
                    with open(out_file, 'w', encoding='utf-8') as f:
                        json.dump(anno, f, ensure_ascii=False, indent=2)
                        
            except Exception as e:
                print(f"⚠️  Error processing {file_path.name}: {e}")
        
        return stats
    
    def save_mapping(self, output_path: str):
        """Save the clustering mapping to a JSON file."""
        mapping_data = {
            "method": "semantic_embedding_clustering",
            "model": "all-MiniLM-L6-v2",
            "n_clusters": len(self.clusters),
            "total_labels": len(self.labels),
            "clusters": [
                {
                    "id": c.cluster_id,
                    "canonical": c.canonical_label,
                    "members": c.members,
                    "total_count": c.total_count
                }
                for c in self.clusters
            ],
            "mapping": self.label_to_cluster
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved mapping to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Smart semantic clustering for desire labels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic clustering (auto-determine number of clusters)
  python smart_label_clustering.py --input-dir data/annotations_test
  
  # Specify number of clusters
  python smart_label_clustering.py --input-dir data/annotations_test --n-clusters 20
  
  # Use distance threshold instead
  python smart_label_clustering.py --input-dir data/annotations_test --threshold 0.4
  
  # Visualize clusters
  python smart_label_clustering.py --input-dir data/annotations_test --visualize
  
  # Apply clustering to annotations
  python smart_label_clustering.py --input-dir data/annotations_test --output-dir data/annotations_clustered
        """
    )
    
    parser.add_argument("--input-dir", "-i", type=str, required=True,
                        help="Directory containing annotation JSON files")
    parser.add_argument("--output-dir", "-o", type=str, default=None,
                        help="Output directory for clustered annotations")
    parser.add_argument("--n-clusters", "-n", type=int, default=None,
                        help="Target number of clusters")
    parser.add_argument("--threshold", "-t", type=float, default=None,
                        help="Distance threshold for clustering (0-2, lower= more clusters)")
    parser.add_argument("--visualize", "-v", action="store_true",
                        help="Generate t-SNE visualization")
    parser.add_argument("--save-mapping", "-m", type=str, default=None,
                        help="Save clustering mapping to JSON file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without modifying files")
    parser.add_argument("--interactive", action="store_true", 
                        help="Generate interactive HTML visualization")
    parser.add_argument("--auto-tune", action="store_true",
                        help="Auto select n_clusters using validation metrics")
    parser.add_argument("--use-umap", action="store_true",
                        help="Use UMAP for visualization (fallback to t-SNE if unavailable)")
    args = parser.parse_args()
    
    # Initialize clusterer
    clusterer = SmartLabelClusterer(
        n_clusters=args.n_clusters,
        distance_threshold=args.threshold,
        use_umap=args.use_umap,
    )
    
    # Collect labels
    clusterer.collect_labels(args.input_dir)
    
    if len(clusterer.labels) == 0:
        print("❌ No labels found!")
        return 1
    
    # Compute embeddings and cluster
    clusterer.compute_embeddings()
    clusterer.cluster_labels(auto_tune=args.auto_tune)
    
    # Print results
    clusterer.print_clusters(show_members=True)

    # 保存 Mapping (JSON)
    if args.save_mapping:
        clusterer.save_mapping(args.save_mapping)
    
    # 生成静态科研图 (PNG/PDF)
    if args.visualize:
        viz_path = args.save_mapping.replace('.json', '.png') if args.save_mapping else "data/desire_clusters_scientific.png"
        clusterer.visualize_clusters(viz_path)

    # 生成交互式网页 (HTML)
    if args.interactive:
        html_path = args.save_mapping.replace('.json', '.html') if args.save_mapping else "data/desire_map.html"
        clusterer.visualize_interactive(html_path)
    
    # Apply to annotations if output dir specified
    if args.output_dir:
        print(f"\n{'🔍 DRY RUN - ' if args.dry_run else ''}Applying clustering to annotations...")
        stats = clusterer.apply_to_annotations(
            args.input_dir, 
            args.output_dir, 
            dry_run=args.dry_run
        )
        print(f"   Files processed: {stats['files_processed']}")
        print(f"   Labels normalized: {stats['labels_normalized']}")
        if stats['new_labels_found']:
            print(f"   ⚠️  New labels not in clusters: {set(stats['new_labels_found'])}")
        
        if not args.dry_run:
            print(f"\n✅ Clustered annotations saved to: {args.output_dir}")
    
    return 0


if __name__ == "__main__":
    exit(main())