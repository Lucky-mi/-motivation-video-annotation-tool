# 聚类标签改进说明

本次调整聚焦于更科学的簇数选择、可视化降维增强，以及 CLI 体验改进。主要改动如下：

## 新增能力
- **自动簇数选择 (`--auto-tune`)**：在未指定 `n_clusters` / `threshold` 时，扫描多个候选簇数，综合 Silhouette / Davies-Bouldin / Calinski-Harabasz 评分自动给出推荐值，并输出日志说明。
- **可选 UMAP 降维 (`--use-umap`)**：若已安装 `umap-learn`，可启用更平滑的局部/全局结构展示；未安装时自动回退 t-SNE。
- **降维封装**：统一 `_reduce_dimensionality`，自动调整 t-SNE perplexity，避免小样本报错。

## CLI 用法
```bash
# 自动调簇 + UMAP 可视化
python scripts/smart_label_clustering.py -i data/annotations_test --auto-tune --visualize --use-umap

# 指定簇数 + 生成交互图
python scripts/smart_label_clustering.py -i data/annotations_test -n 20 --interactive
```

主要参数：
- `--auto-tune`：自动选择簇数（仅在未显式指定簇数/阈值时生效）。
- `--use-umap`：启用 UMAP 降维（需安装 `umap-learn`）。
- `--visualize` / `--interactive`：分别生成静态科研风格图 / 交互式 HTML。

## 依赖提示
- 如需 UMAP：`pip install umap-learn`
- 已使用的 sklearn 指标均为内置模块，无需额外依赖。

## 行为变更
- 当使用 `--auto-tune` 且未指定簇数/阈值时，将在聚类前自动打印选择的簇数及评价指标。
- 可视化默认尝试 UMAP（开启 `--use-umap` 且已安装），否则回退 t-SNE。小样本场景会自动降低 perplexity。

## 下一步建议
- 与 `scripts/smart_cluster.py` 的锚点映射组合使用：先用锚点高置信度归一，再对剩余未知做无监督聚类，减少误并/漏并。
- 为每簇生成“代表 Top-K + 相似度”与摘要标题，便于审阅（可结合 LLM）。

