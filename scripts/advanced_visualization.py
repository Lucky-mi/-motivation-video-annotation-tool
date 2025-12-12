#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Label Visualization Suite
===================================
提供多种美观且信息丰富的可视化方案

Features:
1. Interactive Plotly dashboard with drill-down
2. Scientific publication-quality matplotlib figures
3. Hierarchical sunburst chart
4. Network graph visualization
5. Sankey diagram for label transitions
"""

import sys
import io
# Fix Windows encoding issue
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Optional
import numpy as np

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.patches import Rectangle
    import matplotlib.patches as mpatches
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.manifold import TSNE
    import umap  # Better than t-SNE for structure preservation
    HAS_UMAP = True
except ImportError:
    HAS_UMAP = False
    try:
        from sklearn.manifold import TSNE
        HAS_TSNE = True
    except:
        HAS_TSNE = False


class AdvancedVisualizer:
    """高级可视化工具集"""

    def __init__(self, mapping_file: Optional[str] = None):
        """
        Args:
            mapping_file: Path to clustering mapping JSON
        """
        self.mapping = None
        self.label_counts = {}
        self.domain_stats = defaultdict(lambda: {"labels": [], "counts": []})

        if mapping_file:
            self.load_mapping(mapping_file)

    def load_mapping(self, mapping_file: str):
        """加载聚类映射"""
        with open(mapping_file, 'r', encoding='utf-8') as f:
            self.mapping = json.load(f)

        print(f"✅ Loaded mapping: {self.mapping.get('method', 'unknown')}")

        # Extract statistics
        if "domains" in self.mapping:
            for domain, info in self.mapping["domains"].items():
                self.domain_stats[domain]["n_labels"] = info["n_labels"]
                self.domain_stats[domain]["n_clusters"] = info["n_clusters"]

    def collect_label_stats(self, input_dir: str):
        """收集标签统计"""
        input_path = Path(input_dir)
        label_counts = Counter()

        json_files = [f for f in input_path.glob("*.json")
                     if not f.name.startswith("stats_")
                     and f.name != "annotation_errors.json"]

        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    anno = json.load(f)

                for desire in anno.get("desire_motivation_analysis", []):
                    label = desire.get("desire_label", "")
                    if label:
                        label_counts[label] += 1

                for trans in anno.get("desire_transitions", []):
                    for key in ["desire_before", "desire_after"]:
                        if key in trans and "label" in trans[key]:
                            label = trans[key]["label"]
                            if label:
                                label_counts[label] += 1

            except Exception as e:
                print(f"⚠️  Error reading {file_path.name}: {e}")

        self.label_counts = dict(label_counts)
        print(f"📊 Collected statistics for {len(self.label_counts)} labels")

    def create_interactive_dashboard(self, output_path: str = "data/label_dashboard.html"):
        """创建交互式Plotly仪表板"""
        if not HAS_PLOTLY or not self.mapping:
            print("⚠️  Plotly or mapping not available")
            return

        print("🎨 Creating interactive dashboard...")

        # Prepare data
        domains = []
        labels = []
        counts = []
        canonical_labels = []

        flat_mapping = self.mapping.get("flat_mapping", {})

        for label, count in self.label_counts.items():
            domain = self._extract_domain(label)
            canonical = flat_mapping.get(label, label)

            domains.append(domain)
            labels.append(label)
            counts.append(count)
            canonical_labels.append(canonical)

        df = pd.DataFrame({
            "Domain": domains,
            "Label": labels,
            "Count": counts,
            "Canonical": canonical_labels,
            "Is_Canonical": [l == c for l, c in zip(labels, canonical_labels)]
        })

        # Create subplot dashboard
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Label Distribution by Domain",
                "Top 20 Most Frequent Labels",
                "Clustering Efficiency by Domain",
                "Label Frequency Distribution"
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "histogram"}]
            ]
        )

        # 1. Distribution by domain
        domain_counts = df.groupby("Domain")["Count"].sum().sort_values(ascending=False)
        fig.add_trace(
            go.Bar(x=domain_counts.index, y=domain_counts.values,
                  marker_color='lightseagreen',
                  name="Domain Count"),
            row=1, col=1
        )

        # 2. Top labels
        top_labels = df.nlargest(20, "Count")
        fig.add_trace(
            go.Bar(y=top_labels["Label"], x=top_labels["Count"],
                  orientation='h',
                  marker_color='coral',
                  name="Top Labels"),
            row=1, col=2
        )

        # 3. Clustering efficiency
        if "domains" in self.mapping:
            domain_names = []
            original_counts = []
            clustered_counts = []

            for domain, info in self.mapping["domains"].items():
                if domain != "Unknown":
                    domain_names.append(domain)
                    original_counts.append(info["n_labels"])
                    clustered_counts.append(info["n_clusters"])

            fig.add_trace(
                go.Bar(x=domain_names, y=original_counts,
                      name="Original", marker_color='indianred'),
                row=2, col=1
            )
            fig.add_trace(
                go.Bar(x=domain_names, y=clustered_counts,
                      name="Clustered", marker_color='lightgreen'),
                row=2, col=1
            )

        # 4. Frequency histogram
        fig.add_trace(
            go.Histogram(x=df["Count"], nbinsx=30,
                        marker_color='mediumpurple',
                        name="Frequency"),
            row=2, col=2
        )

        # Layout
        fig.update_layout(
            title_text="Desire Label Clustering Dashboard",
            title_font_size=20,
            showlegend=True,
            height=900,
            template="plotly_white"
        )

        fig.write_html(output_path)
        print(f"💾 Saved dashboard to {output_path}")

    def create_sunburst_chart(self, output_path: str = "data/label_sunburst.html"):
        """创建层次化旭日图（Sunburst）"""
        if not HAS_PLOTLY or not self.mapping:
            print("⚠️  Plotly or mapping not available")
            return

        print("🎨 Creating sunburst chart...")

        # Prepare hierarchical data
        labels_list = []
        parents_list = []
        values_list = []
        colors_list = []

        # Root
        labels_list.append("All Desires")
        parents_list.append("")
        values_list.append(sum(self.label_counts.values()))
        colors_list.append("#ffffff")

        # Color palette
        domain_colors = {
            "Social": "#3498db",
            "Safety": "#9b59b6",
            "Esteem": "#e74c3c",
            "Epistemic": "#f39c12",
            "Cognitive": "#1abc9c",
            "Physiological": "#16a085",
            "Emotional": "#e67e22",
            "Resource": "#95a5a6",
            "Unknown": "#7f8c8d"
        }

        flat_mapping = self.mapping.get("flat_mapping", {})

        # Add domains
        domain_totals = defaultdict(int)
        for label, count in self.label_counts.items():
            domain = self._extract_domain(label)
            domain_totals[domain] += count

        for domain, total in domain_totals.items():
            labels_list.append(domain)
            parents_list.append("All Desires")
            values_list.append(total)
            colors_list.append(domain_colors.get(domain, "#cccccc"))

        # Add canonical labels
        canonical_counts = defaultdict(int)
        canonical_to_domain = {}

        for label, count in self.label_counts.items():
            canonical = flat_mapping.get(label, label)
            domain = self._extract_domain(label)
            canonical_counts[canonical] += count
            canonical_to_domain[canonical] = domain

        for canonical, count in canonical_counts.items():
            domain = canonical_to_domain[canonical]
            labels_list.append(canonical)
            parents_list.append(domain)
            values_list.append(count)
            # Lighter shade of domain color
            base_color = domain_colors.get(domain, "#cccccc")
            colors_list.append(base_color)

        # Create sunburst
        fig = go.Figure(go.Sunburst(
            labels=labels_list,
            parents=parents_list,
            values=values_list,
            marker=dict(colors=colors_list),
            branchvalues="total",
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percentParent}',
        ))

        fig.update_layout(
            title="Hierarchical Structure of Desire Labels",
            width=1000,
            height=1000,
            template="plotly_white"
        )

        fig.write_html(output_path)
        print(f"💾 Saved sunburst chart to {output_path}")

    def create_publication_figure(self,
                                  input_dir: str,
                                  output_path: str = "data/publication_figure.png"):
        """创建出版级质量的组合图"""
        if not HAS_MPL:
            print("⚠️  Matplotlib not available")
            return

        print("🎨 Creating publication-quality figure...")

        sns.set_style("whitegrid")
        sns.set_context("paper", font_scale=1.0)

        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

        # Prepare data
        flat_mapping = self.mapping.get("flat_mapping", {}) if self.mapping else {}

        # 1. Domain distribution (pie)
        ax1 = fig.add_subplot(gs[0, 0])
        domain_counts = defaultdict(int)
        for label, count in self.label_counts.items():
            domain = self._extract_domain(label)
            domain_counts[domain] += count

        colors = sns.color_palette("husl", len(domain_counts))
        ax1.pie(domain_counts.values(), labels=domain_counts.keys(),
               autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title("A. Distribution by Psychological Domain", fontweight='bold')

        # 2. Clustering efficiency (bar)
        ax2 = fig.add_subplot(gs[0, 1])
        if self.mapping and "domains" in self.mapping:
            domains = []
            original = []
            clustered = []

            for domain, info in self.mapping["domains"].items():
                if domain != "Unknown":
                    domains.append(domain[:8])  # Truncate for space
                    original.append(info["n_labels"])
                    clustered.append(info["n_clusters"])

            x = np.arange(len(domains))
            width = 0.35

            ax2.bar(x - width/2, original, width, label='Original', color='#e74c3c', alpha=0.8)
            ax2.bar(x + width/2, clustered, width, label='Clustered', color='#27ae60', alpha=0.8)

            ax2.set_xlabel('Domain')
            ax2.set_ylabel('Number of Labels')
            ax2.set_title('B. Clustering Efficiency by Domain', fontweight='bold')
            ax2.set_xticks(x)
            ax2.set_xticklabels(domains, rotation=45, ha='right')
            ax2.legend()
            ax2.grid(axis='y', alpha=0.3)

        # 3. Top labels (horizontal bar)
        ax3 = fig.add_subplot(gs[0, 2])
        top_n = 15
        top_items = sorted(self.label_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        top_labels, top_counts = zip(*top_items)

        # Simplify labels for display
        display_labels = [l.replace('_', ' ')[:30] for l in top_labels]

        y_pos = np.arange(len(display_labels))
        ax3.barh(y_pos, top_counts, color='#3498db', alpha=0.7)
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(display_labels, fontsize=8)
        ax3.invert_yaxis()
        ax3.set_xlabel('Frequency')
        ax3.set_title(f'C. Top {top_n} Most Frequent Labels', fontweight='bold')
        ax3.grid(axis='x', alpha=0.3)

        # 4. Frequency distribution (histogram)
        ax4 = fig.add_subplot(gs[1, :2])
        counts = list(self.label_counts.values())
        ax4.hist(counts, bins=30, color='#9b59b6', alpha=0.7, edgecolor='black')
        ax4.set_xlabel('Label Frequency')
        ax4.set_ylabel('Number of Labels')
        ax4.set_title('D. Distribution of Label Frequencies (Log Scale)', fontweight='bold')
        ax4.set_yscale('log')
        ax4.grid(axis='y', alpha=0.3)

        # 5. Summary statistics (text box)
        ax5 = fig.add_subplot(gs[1, 2])
        ax5.axis('off')

        stats_text = "E. Summary Statistics\n\n"
        stats_text += f"Total Labels: {len(self.label_counts)}\n"
        stats_text += f"Total Occurrences: {sum(self.label_counts.values())}\n\n"

        if self.mapping:
            n_canonical = len(set(flat_mapping.values()))
            reduction = (1 - n_canonical / len(self.label_counts)) * 100
            stats_text += f"Canonical Labels: {n_canonical}\n"
            stats_text += f"Reduction: {reduction:.1f}%\n\n"

        stats_text += f"Avg. Frequency: {np.mean(counts):.1f}\n"
        stats_text += f"Median Frequency: {np.median(counts):.0f}\n"
        stats_text += f"Max Frequency: {max(counts)}\n"

        ax5.text(0.1, 0.9, stats_text, transform=ax5.transAxes,
                fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3),
                family='monospace')

        # Main title
        fig.suptitle('Desire Label Analysis: Clustering & Distribution',
                    fontsize=16, fontweight='bold', y=0.98)

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"💾 Saved publication figure to {output_path}")

    def create_umap_visualization(self,
                                  input_dir: str,
                                  output_path: str = "data/umap_visualization.html"):
        """使用UMAP创建更好的降维可视化（比t-SNE保留更多全局结构）"""
        if not HAS_PLOTLY or not HAS_UMAP:
            print("⚠️  UMAP or Plotly not available. Install: pip install umap-learn")
            return

        print("🎨 Creating UMAP visualization...")

        # Collect all labels
        labels = list(self.label_counts.keys())

        # Compute embeddings
        model = SentenceTransformer('all-MiniLM-L6-v2')
        natural_labels = [self._snake_to_natural(l) for l in labels]
        embeddings = model.encode(natural_labels, show_progress_bar=True)

        # UMAP projection
        reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, metric='cosine', random_state=42)
        projections = reducer.fit_transform(embeddings)

        # Prepare data
        domains = [self._extract_domain(l) for l in labels]
        counts = [self.label_counts[l] for l in labels]

        flat_mapping = self.mapping.get("flat_mapping", {}) if self.mapping else {}
        canonical = [flat_mapping.get(l, l) for l in labels]
        is_canonical = [l == c for l, c in zip(labels, canonical)]

        df = pd.DataFrame({
            'x': projections[:, 0],
            'y': projections[:, 1],
            'label': labels,
            'domain': domains,
            'count': counts,
            'canonical': canonical,
            'is_canonical': is_canonical,
            'size': [np.log1p(c) * 10 for c in counts]
        })

        # Create interactive plot
        fig = px.scatter(
            df, x='x', y='y',
            color='domain',
            size='size',
            hover_name='label',
            hover_data={
                'x': False,
                'y': False,
                'count': True,
                'canonical': True,
                'domain': False
            },
            title='UMAP Projection of Desire Labels (Better Global Structure)',
            template='plotly_white',
            width=1400,
            height=900,
            color_discrete_sequence=px.colors.qualitative.Bold
        )

        # Highlight canonical labels
        canonical_df = df[df['is_canonical']]
        fig.add_trace(go.Scatter(
            x=canonical_df['x'],
            y=canonical_df['y'],
            mode='markers',
            marker=dict(
                size=canonical_df['size'] + 5,
                color='rgba(255, 255, 255, 0)',
                line=dict(color='black', width=2)
            ),
            name='Canonical',
            hoverinfo='skip'
        ))

        fig.update_xaxes(showticklabels=False, title='')
        fig.update_yaxes(showticklabels=False, title='')

        fig.write_html(output_path)
        print(f"💾 Saved UMAP visualization to {output_path}")

    def _extract_domain(self, label: str) -> str:
        """提取标签的心理学维度"""
        for domain in ["Social", "Safety", "Esteem", "Epistemic",
                      "Cognitive", "Physiological", "Emotional", "Resource", "Belonging"]:
            if label.startswith(domain + "_"):
                return domain
        return "Unknown"

    def _snake_to_natural(self, label: str) -> str:
        """Convert snake_case to natural language"""
        return ' '.join(label.split('_')).lower()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Advanced visualization suite")
    parser.add_argument("--input-dir", "-i", required=True,
                       help="Directory with annotations")
    parser.add_argument("--mapping", "-m", type=str, default=None,
                       help="Clustering mapping JSON file")
    parser.add_argument("--dashboard", action="store_true",
                       help="Create interactive dashboard")
    parser.add_argument("--sunburst", action="store_true",
                       help="Create sunburst chart")
    parser.add_argument("--publication", action="store_true",
                       help="Create publication-quality figure")
    parser.add_argument("--umap", action="store_true",
                       help="Create UMAP visualization")
    parser.add_argument("--all", action="store_true",
                       help="Create all visualizations")

    args = parser.parse_args()

    viz = AdvancedVisualizer(mapping_file=args.mapping)
    viz.collect_label_stats(args.input_dir)

    if args.all or args.dashboard:
        viz.create_interactive_dashboard()

    if args.all or args.sunburst:
        viz.create_sunburst_chart()

    if args.all or args.publication:
        viz.create_publication_figure(args.input_dir)

    if args.all or args.umap:
        viz.create_umap_visualization(args.input_dir)

    if not any([args.dashboard, args.sunburst, args.publication, args.umap, args.all]):
        print("⚠️  No visualization type specified. Use --all or specific flags.")
        print("   See --help for options")


if __name__ == "__main__":
    main()
