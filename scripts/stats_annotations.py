"""
标注 JSON 文件统计脚本
输出:
  1. 控制台统计报告
  2. data/stats_report.json  — 结构化 JSON
  3. data/stats_dashboard.html — Plotly 交互式仪表板
"""
import json
from pathlib import Path
from collections import Counter
from datetime import datetime

ANNOTATIONS_DIR = Path(__file__).resolve().parent.parent / "data" / "annotations_v6"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"


# ============= 数据加载 =============

def load_annotations():
    files = sorted(ANNOTATIONS_DIR.glob("*.json"))
    annotations = []
    for f in files:
        if f.name == "annotation_errors.json":
            continue
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            data["_filename"] = f.name
            annotations.append(data)
        except Exception as e:
            print(f"[WARN] 跳过 {f.name}: {e}")
    return annotations


# ============= 统计逻辑 =============

def run_stats(annotations):
    dimension_counter = Counter()
    desire_label_counter = Counter()
    maslow_counter = Counter()
    activity_type_counter = Counter()
    behavior_cat_counter = Counter()
    explicitness_counter = Counter()
    desire_type_counter = Counter()
    temporal_type_counter = Counter()
    model_counter = Counter()
    version_counter = Counter()
    confidence_counter = Counter()
    transition_type_counter = Counter()

    total_characters = 0
    total_behaviors = 0
    total_desires = 0
    total_transitions = 0
    total_qa_segments = 0
    total_dynamics = 0
    durations = []

    for ann in annotations:
        sc = ann.get("scene_context", {})
        activity_type_counter[sc.get("activity_type", "unknown")] += 1
        dur = ann.get("duration_seconds", 0)
        if dur:
            durations.append(dur)

        total_characters += len(ann.get("characters", []))

        bseq = ann.get("behavioral_sequence", [])
        total_behaviors += len(bseq)
        for b in bseq:
            behavior_cat_counter[b.get("behavior_category", "unknown")] += 1

        dma = ann.get("desire_motivation_analysis", [])
        total_desires += len(dma)
        for d in dma:
            desire_label_counter[d.get("desire_label", "unknown")] += 1
            dimension_counter[d.get("dimension", "unknown")] += 1
            maslow_counter[d.get("maslow_level", "unknown")] += 1
            explicitness_counter[d.get("explicitness", "unknown")] += 1
            desire_type_counter[d.get("desire_type", "unknown")] += 1
            temporal_type_counter[d.get("temporal_type", "unknown")] += 1
            confidence_counter[d.get("confidence", "unknown")] += 1

        dt = ann.get("desire_transitions", [])
        total_transitions += len(dt)
        for t in dt:
            transition_type_counter[t.get("transition_type", "unknown")] += 1

        total_qa_segments += len(ann.get("key_segments_for_qa", []))
        total_dynamics += len(ann.get("inter_character_dynamics", []))

        meta = ann.get("annotation_metadata", {})
        model_counter[meta.get("model_used", "unknown")] += 1
        version_counter[meta.get("annotation_version", "unknown")] += 1

    n = len(annotations)
    return {
        "file_count": n,
        "total_characters": total_characters,
        "total_behaviors": total_behaviors,
        "total_desires": total_desires,
        "total_transitions": total_transitions,
        "total_qa_segments": total_qa_segments,
        "total_dynamics": total_dynamics,
        "avg_duration": sum(durations) / len(durations) if durations else 0,
        "avg_characters": total_characters / n if n else 0,
        "avg_desires": total_desires / n if n else 0,
        "avg_transitions": total_transitions / n if n else 0,
        "dimension": dict(dimension_counter.most_common()),
        "desire_label": dict(desire_label_counter.most_common()),
        "maslow_level": dict(maslow_counter.most_common()),
        "activity_type": dict(activity_type_counter.most_common()),
        "behavior_category": dict(behavior_cat_counter.most_common()),
        "explicitness": dict(explicitness_counter.most_common()),
        "desire_type": dict(desire_type_counter.most_common()),
        "temporal_type": dict(temporal_type_counter.most_common()),
        "confidence": dict(confidence_counter.most_common()),
        "transition_type": dict(transition_type_counter.most_common()),
        "model_used": dict(model_counter.most_common()),
        "annotation_version": dict(version_counter.most_common()),
        "generated_at": datetime.now().isoformat(),
    }


# ============= 控制台输出 =============

def print_counter(title, counter_dict, top_n=None):
    items = list(counter_dict.items())[:top_n] if top_n else list(counter_dict.items())
    total = sum(counter_dict.values())
    print(f"\n{'='*50}")
    print(f"  {title}  (共 {total} 项)")
    print(f"{'='*50}")
    if not items:
        print("  (无数据)")
        return
    max_label = max(len(str(k)) for k, _ in items)
    max_val = max(v for _, v in items)
    for k, v in items:
        bar = "█" * int(v / max(1, max_val) * 30)
        print(f"  {str(k):<{max_label}}  {v:>4}  {bar}")


def print_report(stats):
    print("\n" + "=" * 50)
    print("  📊 标注数据统计报告")
    print("=" * 50)
    print(f"\n  标注文件总数:        {stats['file_count']}")
    print(f"  角色总数:            {stats['total_characters']}")
    print(f"  行为序列总数:        {stats['total_behaviors']}")
    print(f"  欲望/动机分析总数:   {stats['total_desires']}")
    print(f"  欲望转变总数:        {stats['total_transitions']}")
    print(f"  QA 关键片段总数:     {stats['total_qa_segments']}")
    print(f"  角色互动关系总数:    {stats['total_dynamics']}")
    print(f"  平均视频时长:        {stats['avg_duration']:.1f}s")
    print(f"  平均每视频角色数:    {stats['avg_characters']:.1f}")
    print(f"  平均每视频 Desire 数: {stats['avg_desires']:.1f}")

    print_counter("维度分布 (D1-D5)", stats["dimension"])
    print_counter("Maslow 层级分布", stats["maslow_level"])
    print_counter("Desire 标签 Top 20", stats["desire_label"], top_n=20)
    print_counter("场景类型 (activity_type)", stats["activity_type"])
    print_counter("行为类别 (behavior_category)", stats["behavior_category"])
    print_counter("显隐性 (explicitness)", stats["explicitness"])
    print_counter("欲望类型 (desire_type)", stats["desire_type"])
    print_counter("时间类型 (temporal_type)", stats["temporal_type"])
    print_counter("转变类型 (transition_type)", stats["transition_type"])
    print_counter("置信度 (confidence)", stats["confidence"])
    print_counter("使用模型", stats["model_used"])
    print_counter("标注版本", stats["annotation_version"])


# ============= JSON 报告 =============

def save_json_report(stats, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"\n💾 JSON 报告已保存: {path}")


# ============= Plotly 可视化 =============

def create_dashboard(stats, output_path):
    """生成交互式 HTML 仪表板（复用 advanced_visualization 的风格）"""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        print("⚠️  需要 plotly: pip install plotly")
        return

    # 颜色方案
    colors = {
        "D1": "#FF6B6B", "D2": "#FFA726", "D3": "#66BB6A",
        "D4": "#42A5F5", "D5": "#AB47BC",
    }
    maslow_colors = {
        "physiological": "#FF6B6B", "safety": "#FFA726",
        "belonging": "#66BB6A", "esteem": "#42A5F5",
        "self_actualization": "#AB47BC",
    }

    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            "维度分布 (D1-D5)", "Maslow 层级分布",
            "Desire 标签 Top 15", "行为类别分布",
            "显隐性 & 欲望类型", "时间类型 & 转变类型",
        ),
        specs=[
            [{"type": "pie"}, {"type": "pie"}],
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "bar"}],
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.12,
    )

    # 1. 维度饼图
    dim = stats["dimension"]
    fig.add_trace(go.Pie(
        labels=list(dim.keys()), values=list(dim.values()),
        marker=dict(colors=[colors.get(k, "#999") for k in dim.keys()]),
        textinfo="label+percent+value", hole=0.35,
    ), row=1, col=1)

    # 2. Maslow 饼图
    mas = stats["maslow_level"]
    fig.add_trace(go.Pie(
        labels=list(mas.keys()), values=list(mas.values()),
        marker=dict(colors=[maslow_colors.get(k, "#999") for k in mas.keys()]),
        textinfo="label+percent+value", hole=0.35,
    ), row=1, col=2)

    # 3. Desire 标签 Top 15 (水平条形图)
    dl = dict(list(stats["desire_label"].items())[:15])
    labels_sorted = list(reversed(dl.keys()))
    values_sorted = list(reversed(dl.values()))
    bar_colors = [colors.get(l.split("_")[0].split(".")[0], "#42A5F5") for l in labels_sorted]
    fig.add_trace(go.Bar(
        y=labels_sorted, x=values_sorted, orientation="h",
        marker_color=bar_colors,
        text=values_sorted, textposition="outside",
    ), row=2, col=1)

    # 4. 行为类别
    bc = stats["behavior_category"]
    fig.add_trace(go.Bar(
        x=list(bc.keys()), y=list(bc.values()),
        marker_color="#66BB6A",
        text=list(bc.values()), textposition="outside",
    ), row=2, col=2)

    # 5. 显隐性 + 欲望类型
    exp = stats["explicitness"]
    dt = stats["desire_type"]
    fig.add_trace(go.Bar(
        x=list(exp.keys()), y=list(exp.values()),
        name="显隐性", marker_color="#FFA726",
        text=list(exp.values()), textposition="outside",
    ), row=3, col=1)
    fig.add_trace(go.Bar(
        x=list(dt.keys()), y=list(dt.values()),
        name="欲望类型", marker_color="#AB47BC",
        text=list(dt.values()), textposition="outside",
    ), row=3, col=1)

    # 6. 时间类型 + 转变类型
    tt = stats["temporal_type"]
    trt = stats["transition_type"]
    fig.add_trace(go.Bar(
        x=list(tt.keys()), y=list(tt.values()),
        name="时间类型", marker_color="#42A5F5",
        text=list(tt.values()), textposition="outside",
    ), row=3, col=2)
    fig.add_trace(go.Bar(
        x=list(trt.keys()), y=list(trt.values()),
        name="转变类型", marker_color="#FF6B6B",
        text=list(trt.values()), textposition="outside",
    ), row=3, col=2)

    # 总览标题
    n = stats["file_count"]
    fig.update_layout(
        title=dict(
            text=(
                f"📊 Desire-VQA 标注统计仪表板<br>"
                f"<sub>{n} 视频 | {stats['total_desires']} 欲望分析 | "
                f"{stats['total_behaviors']} 行为序列 | "
                f"{stats['total_transitions']} 欲望转变 | "
                f"生成时间: {stats['generated_at'][:16]}</sub>"
            ),
            font_size=18,
        ),
        height=1200,
        template="plotly_white",
        showlegend=True,
        legend=dict(orientation="h", y=-0.02),
    )

    fig.write_html(str(output_path), include_plotlyjs=True)
    print(f"📊 交互式仪表板已保存: {output_path}")


# ============= 主函数 =============

def main():
    annotations = load_annotations()
    if not annotations:
        print("未找到标注文件!")
        return

    stats = run_stats(annotations)

    # 1. 控制台输出
    print_report(stats)

    # 2. JSON 报告
    json_path = OUTPUT_DIR / "stats_report.json"
    save_json_report(stats, json_path)

    # 3. Plotly 仪表板
    html_path = OUTPUT_DIR / "stats_dashboard.html"
    create_dashboard(stats, html_path)


if __name__ == "__main__":
    main()
