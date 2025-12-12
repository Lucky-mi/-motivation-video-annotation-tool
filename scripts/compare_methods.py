#!/usr/bin/env python3
"""
Clustering Methods Comparison Tool
===================================
对比三种聚类方法的结果，帮助选择最佳方案

Usage:
    python compare_methods.py --input-dir data/annotations_test
"""

import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import sys

# Try to import clustering modules
try:
    from label_normalizer import LabelNormalizer
    HAS_NORMALIZER = True
except ImportError:
    HAS_NORMALIZER = False

try:
    from smart_label_clustering import SmartLabelClusterer
    HAS_SMART = True
except ImportError:
    HAS_SMART = False

try:
    from hybrid_label_clustering import HybridClusterer
    HAS_HYBRID = True
except ImportError:
    HAS_HYBRID = False


class MethodComparator:
    """比较不同聚类方法的效果"""

    def __init__(self, input_dir: str):
        self.input_dir = input_dir
        self.label_counts = {}
        self.results = {}

    def collect_labels(self):
        """收集所有标签"""
        input_path = Path(self.input_dir)
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
        print(f"📊 Collected {len(self.label_counts)} unique labels")
        print(f"   Total occurrences: {sum(self.label_counts.values())}")

    def run_manual_method(self):
        """运行手动字典方法"""
        if not HAS_NORMALIZER:
            print("⚠️  LabelNormalizer not available")
            return None

        print("\n" + "=" * 60)
        print("🔧 Method 1: Manual Dictionary (label_normalizer.py)")
        print("=" * 60)

        normalizer = LabelNormalizer()

        # Count mapped vs unmapped
        mapped = 0
        unmapped = 0
        canonical_set = set()

        for label in self.label_counts.keys():
            if label in normalizer.DESIRE_LABEL_MAP:
                mapped += 1
                canonical = normalizer.DESIRE_LABEL_MAP[label]
                canonical_set.add(canonical)
            else:
                unmapped += 1

        coverage = mapped / len(self.label_counts) * 100 if self.label_counts else 0
        reduction = (1 - len(canonical_set) / len(self.label_counts)) * 100 if self.label_counts else 0

        print(f"   Dictionary size: {len(normalizer.DESIRE_LABEL_MAP)}")
        print(f"   Labels in dataset: {len(self.label_counts)}")
        print(f"   Covered: {mapped} ({coverage:.1f}%)")
        print(f"   Uncovered: {unmapped}")
        print(f"   Canonical labels: {len(canonical_set)}")
        print(f"   Reduction rate: {reduction:.1f}%")

        self.results["manual"] = {
            "method": "Manual Dictionary",
            "total_labels": len(self.label_counts),
            "canonical_labels": len(canonical_set),
            "coverage": coverage,
            "reduction": reduction,
            "uncovered": unmapped
        }

        return self.results["manual"]

    def run_smart_clustering(self, n_clusters=None):
        """运行全自动语义聚类"""
        if not HAS_SMART:
            print("⚠️  SmartLabelClusterer not available")
            return None

        print("\n" + "=" * 60)
        print("🤖 Method 2: Semantic Clustering (smart_label_clustering.py)")
        print("=" * 60)

        clusterer = SmartLabelClusterer(n_clusters=n_clusters)
        clusterer.label_counts = self.label_counts
        clusterer.labels = list(self.label_counts.keys())

        clusterer.compute_embeddings()
        clusterer.cluster_labels()

        n_canonical = len(set(clusterer.label_to_cluster.values()))
        reduction = (1 - n_canonical / len(self.label_counts)) * 100 if self.label_counts else 0

        print(f"   Total labels: {len(self.label_counts)}")
        print(f"   Clusters created: {n_canonical}")
        print(f"   Reduction rate: {reduction:.1f}%")
        print(f"   Coverage: 100.0% (all labels clustered)")

        # Check for potential issues
        domain_mixing = self._check_domain_mixing(clusterer.clusters)
        if domain_mixing:
            print(f"\n   ⚠️  Warning: {len(domain_mixing)} clusters mix multiple domains")
            for cluster_id, domains in domain_mixing[:3]:  # Show first 3
                cluster = clusterer.clusters[cluster_id]
                print(f"      Cluster '{cluster.canonical_label}': {domains}")

        self.results["smart"] = {
            "method": "Semantic Clustering",
            "total_labels": len(self.label_counts),
            "canonical_labels": n_canonical,
            "coverage": 100.0,
            "reduction": reduction,
            "domain_mixing_issues": len(domain_mixing)
        }

        return self.results["smart"]

    def run_hybrid_clustering(self, threshold=0.25):
        """运行混合聚类"""
        if not HAS_HYBRID:
            print("⚠️  HybridClusterer not available")
            return None

        print("\n" + "=" * 60)
        print("🌟 Method 3: Hybrid Clustering (hybrid_label_clustering.py)")
        print("=" * 60)

        clusterer = HybridClusterer(intra_domain_threshold=threshold)
        clusterer.label_counts = self.label_counts
        clusterer.labels = list(self.label_counts.keys())

        clusterer.group_by_domain()
        clusterer.build_hierarchical_mapping()

        n_canonical = len(set(clusterer.flat_mapping.values()))
        reduction = (1 - n_canonical / len(self.label_counts)) * 100 if self.label_counts else 0

        # Domain statistics
        n_domains = len(clusterer.domain_groups)
        unknown_count = len(clusterer.domain_groups.get("Unknown", []))
        unknown_pct = unknown_count / len(self.label_counts) * 100 if self.label_counts else 0

        print(f"   Total labels: {len(self.label_counts)}")
        print(f"   Psychological domains: {n_domains}")
        print(f"   Canonical labels: {n_canonical}")
        print(f"   Reduction rate: {reduction:.1f}%")
        print(f"   Unknown domain: {unknown_count} labels ({unknown_pct:.1f}%)")
        print(f"   Coverage: 100.0% (all labels processed)")

        self.results["hybrid"] = {
            "method": "Hybrid Clustering",
            "total_labels": len(self.label_counts),
            "canonical_labels": n_canonical,
            "coverage": 100.0,
            "reduction": reduction,
            "n_domains": n_domains,
            "unknown_labels": unknown_count
        }

        return self.results["hybrid"]

    def _check_domain_mixing(self, clusters):
        """检查是否有聚类混合了多个心理学维度"""
        mixing_issues = []

        for cluster in clusters:
            domains = set()
            for member in cluster.members:
                domain = self._extract_domain(member)
                domains.add(domain)

            if len(domains) > 1 and "Unknown" not in domains:
                mixing_issues.append((cluster.cluster_id, sorted(list(domains))))

        return mixing_issues

    def _extract_domain(self, label: str) -> str:
        """提取心理学维度"""
        for domain in ["Social", "Safety", "Esteem", "Epistemic",
                      "Cognitive", "Physiological", "Emotional", "Resource", "Belonging"]:
            if label.startswith(domain + "_"):
                return domain
        return "Unknown"

    def print_comparison_table(self):
        """打印对比表格"""
        print("\n" + "=" * 80)
        print("📊 COMPARISON SUMMARY")
        print("=" * 80)

        if not self.results:
            print("❌ No results to compare")
            return

        # Header
        print(f"\n{'Metric':<30} {'Manual':<20} {'Semantic':<20} {'Hybrid':<20}")
        print("-" * 90)

        # Total labels
        print(f"{'Total Labels':<30}", end="")
        for method in ["manual", "smart", "hybrid"]:
            if method in self.results:
                print(f"{self.results[method]['total_labels']:<20}", end="")
            else:
                print(f"{'N/A':<20}", end="")
        print()

        # Canonical labels
        print(f"{'Canonical Labels':<30}", end="")
        for method in ["manual", "smart", "hybrid"]:
            if method in self.results:
                print(f"{self.results[method]['canonical_labels']:<20}", end="")
            else:
                print(f"{'N/A':<20}", end="")
        print()

        # Reduction rate
        print(f"{'Reduction Rate':<30}", end="")
        for method in ["manual", "smart", "hybrid"]:
            if method in self.results:
                print(f"{self.results[method]['reduction']:.1f}%{' ':<15}", end="")
            else:
                print(f"{'N/A':<20}", end="")
        print()

        # Coverage
        print(f"{'Coverage':<30}", end="")
        for method in ["manual", "smart", "hybrid"]:
            if method in self.results:
                print(f"{self.results[method]['coverage']:.1f}%{' ':<15}", end="")
            else:
                print(f"{'N/A':<20}", end="")
        print()

        # Method-specific metrics
        print(f"\n{'Method-Specific Issues':<30}")
        print("-" * 90)

        if "manual" in self.results:
            print(f"  Manual: {self.results['manual'].get('uncovered', 0)} uncovered labels")

        if "smart" in self.results:
            print(f"  Semantic: {self.results['smart'].get('domain_mixing_issues', 0)} domain-mixing clusters")

        if "hybrid" in self.results:
            print(f"  Hybrid: {self.results['hybrid'].get('unknown_labels', 0)} unknown domain labels")

        print("\n" + "=" * 80)

    def print_recommendation(self):
        """打印推荐建议"""
        print("\n💡 RECOMMENDATION")
        print("=" * 80)

        if "manual" in self.results:
            manual_coverage = self.results["manual"]["coverage"]
            if manual_coverage >= 95:
                print("✅ Manual dictionary has excellent coverage (>95%)")
                print("   → Recommended if you want maximum control and accuracy")
                print("   → Consider using it as-is, or supplement with AI for new labels")
            elif manual_coverage >= 80:
                print("⚠️  Manual dictionary has good but incomplete coverage (80-95%)")
                print("   → Use smart_cluster.py to handle uncovered labels")
            else:
                print("❌ Manual dictionary has low coverage (<80%)")
                print("   → Not recommended as primary method")

        if "smart" in self.results and "hybrid" in self.results:
            smart_mixing = self.results["smart"].get("domain_mixing_issues", 0)
            hybrid_unknown = self.results["hybrid"].get("unknown_labels", 0)

            print(f"\n🌟 Hybrid Clustering Analysis:")
            print(f"   - Reduction: {self.results['hybrid']['reduction']:.1f}%")
            print(f"   - Unknown labels: {hybrid_unknown}")
            print(f"   - Preserves psychological domains ✓")

            if smart_mixing > 5:
                print(f"\n⚠️  Semantic clustering has {smart_mixing} domain-mixing issues")
                print("   → Hybrid method is strongly recommended")
            elif hybrid_unknown < len(self.label_counts) * 0.1:
                print("\n✅ Hybrid method handles most labels well")
                print("   → Recommended for balance of automation and theory")
            else:
                print(f"\n⚠️  Hybrid method has {hybrid_unknown} unknown domain labels")
                print("   → Review these labels and add domain prefixes if needed")

        print("\n📝 General Recommendation:")
        print("   1. Start with HYBRID clustering (best balance)")
        print("   2. Review Unknown domain labels, manually categorize if needed")
        print("   3. Use smart_cluster.py for ongoing incremental updates")
        print("   4. Keep manual dictionary as gold standard for critical cases")

        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Compare clustering methods",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--input-dir", "-i", required=True,
                       help="Directory with annotation files")
    parser.add_argument("--skip-manual", action="store_true",
                       help="Skip manual dictionary method")
    parser.add_argument("--skip-semantic", action="store_true",
                       help="Skip semantic clustering method")
    parser.add_argument("--skip-hybrid", action="store_true",
                       help="Skip hybrid clustering method")
    parser.add_argument("--n-clusters", type=int, default=None,
                       help="Number of clusters for semantic method (default: auto)")
    parser.add_argument("--threshold", type=float, default=0.25,
                       help="Threshold for hybrid method (default: 0.25)")

    args = parser.parse_args()

    print("🔍 Clustering Methods Comparison")
    print("=" * 80)

    comparator = MethodComparator(args.input_dir)
    comparator.collect_labels()

    # Run methods
    if not args.skip_manual:
        comparator.run_manual_method()

    if not args.skip_semantic:
        comparator.run_smart_clustering(n_clusters=args.n_clusters)

    if not args.skip_hybrid:
        comparator.run_hybrid_clustering(threshold=args.threshold)

    # Print results
    comparator.print_comparison_table()
    comparator.print_recommendation()

    return 0


if __name__ == "__main__":
    exit(main())
