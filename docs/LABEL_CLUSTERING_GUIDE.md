# 🎯 Desire标签聚类与可视化完整指南

## 📋 目录
1. [问题分析](#问题分析)
2. [三种聚类方法对比](#三种聚类方法对比)
3. [推荐方案：混合聚类](#推荐方案混合聚类)
4. [高级可视化](#高级可视化)
5. [完整工作流程](#完整工作流程)
6. [科学性评估](#科学性评估)

---

## 问题分析

### 当前挑战
AI生成的desire标签存在以下问题：
- **变体过多**：同一概念有多个表达（如 `Social_Affiliation_Seeking` vs `Social_Connection_Initiation`）
- **粒度不一**：有些标签非常具体，有些较为宽泛
- **新标签不断出现**：AI生成新视频标注时会产生未见过的标签

### 目标
1. ✅ 将相似标签归并到规范形式（Canonical Labels）
2. ✅ 保持心理学理论框架的完整性
3. ✅ 自动化处理，减少人工维护成本
4. ✅ 提供直观的可视化展示

---

## 三种聚类方法对比

### 方法1：手动字典映射 (`label_normalizer.py`)

```python
DESIRE_LABEL_MAP = {
    "Social_Affiliation_Seeking": "Social_Affiliation_Seeking",
    "Social_Connection_Initiation": "Social_Affiliation_Seeking",
    ...
}
```

**优点：**
- ✅ 精确控制，符合心理学理论
- ✅ 完全透明，易于理解

**缺点：**
- ❌ 需要手动维护128个映射
- ❌ 新标签出现时需要人工添加
- ❌ 扩展性差

**适用场景：** 标签集稳定，追求最高准确性

---

### 方法2：AI辅助交互式映射 (`smart_cluster.py`)

```bash
python scripts/smart_cluster.py --input-dir data/annotations_test
```

**工作流程：**
1. 扫描所有新标签（不在字典中的）
2. 使用Sentence-BERT计算与现有标准标签的相似度
3. 推荐Top 3最相似的映射
4. 人工确认或手动输入

**优点：**
- ✅ 结合AI推荐和人工判断
- ✅ 适合增量添加新标签
- ✅ 保持理论一致性

**缺点：**
- ❌ 需要逐个处理，耗时
- ❌ 仍需人工介入

**适用场景：** 定期更新字典，追求准确性+效率平衡

---

### 方法3：全自动语义聚类 (`smart_label_clustering.py`)

```bash
python scripts/smart_label_clustering.py \
    --input-dir data/annotations_test \
    --n-clusters 25 \
    --visualize
```

**工作流程：**
1. 使用Sentence-BERT将所有标签转换为向量
2. 基于余弦相似度进行层次聚类
3. 自动选择每个聚类的代表标签

**优点：**
- ✅ 完全自动化
- ✅ 基于语义相似度，合理
- ✅ 可视化效果好

**缺点：**
- ⚠️ **关键问题**：可能将**语义相似但心理学意义不同**的标签聚在一起
- ⚠️ 例如：
  - `Social_Conflict_Avoidance` (社交动机)
  - `Safety_Conflict_Avoidance` (安全动机)
  - 语义相似，但属于不同心理学维度！

**适用场景：** 探索性分析，快速原型

---

## 推荐方案：混合聚类

### 🌟 为什么选择混合方法？

**核心思想：**
> 第一层按心理学理论分类，第二层用数据驱动聚类

```
心理学维度 (理论驱动)
    ├── Social
    │   ├── 语义聚类1: Social_Affiliation_Seeking
    │   │   ├── Social_Connection_Initiation
    │   │   └── Social_Shared_Experience_Seeking
    │   └── 语义聚类2: Social_Support_Exchange
    │       ├── Social_Support_Seeking
    │       └── Social_Caregiving_Provision
    ├── Safety
    │   ├── Safety_Threat_Avoidance
    │   └── Safety_Psychological_Protection
    └── ...
```

### 使用方法

```bash
# 基础用法
python scripts/hybrid_label_clustering.py \
    --input-dir data/annotations_test \
    --save-mapping data/hybrid_mapping.json \
    --export-python data/hybrid_dict.py \
    --visualize

# 调整聚类粒度（阈值越低，聚类越多）
python scripts/hybrid_label_clustering.py \
    --input-dir data/annotations_test \
    --threshold 0.2 \
    --save-mapping data/hybrid_mapping.json
```

### 输出文件

1. **`hybrid_mapping.json`**: 完整的层次化映射
   ```json
   {
     "method": "hybrid_clustering",
     "domains": {
       "Social": {
         "n_labels": 45,
         "n_clusters": 12,
         "mapping": {...}
       }
     }
   }
   ```

2. **`hybrid_dict.py`**: Python字典格式（可直接用于代码）
   ```python
   HYBRID_DESIRE_LABEL_MAP = {
       "Social_Affiliation_Seeking": "Social_Affiliation_Seeking",
       "Social_Connection_Initiation": "Social_Affiliation_Seeking",
       ...
   }
   ```

3. **`hybrid_clusters.png`**: 可视化（按维度着色的t-SNE图）

---

## 高级可视化

### 为什么需要更好的可视化？

当前可视化的问题：
- ❌ 标签重叠严重（虽然用了adjustText，但还不够）
- ❌ 缺少交互性，无法drill-down查看细节
- ❌ 没有展示层次结构
- ❌ 不够美观，难以用于论文

### 解决方案：高级可视化套件

```bash
# 生成所有可视化
python scripts/advanced_visualization.py \
    --input-dir data/annotations_test \
    --mapping data/hybrid_mapping.json \
    --all

# 或者单独生成
python scripts/advanced_visualization.py \
    --input-dir data/annotations_test \
    --mapping data/hybrid_mapping.json \
    --dashboard          # 交互式仪表板
    --sunburst          # 层次化旭日图
    --publication       # 出版级组合图
    --umap              # UMAP降维可视化
```

### 可视化类型说明

#### 1. 交互式仪表板 (`label_dashboard.html`)
- **用途**: 探索性数据分析
- **特点**:
  - 4个子图：维度分布、Top标签、聚类效率、频率分布
  - 可交互缩放、悬停查看详情
  - 适合在浏览器中探索数据

#### 2. 层次化旭日图 (`label_sunburst.html`)
- **用途**: 展示层次结构
- **特点**:
  - 内圈：心理学维度
  - 外圈：规范标签
  - 大小：出现频率
  - 可点击展开/收起

#### 3. 出版级组合图 (`publication_figure.png`)
- **用途**: 论文、报告
- **特点**:
  - 300 DPI高清
  - 5个子图：饼图、柱状图、频率分布、统计信息
  - 符合学术出版规范

#### 4. UMAP可视化 (`umap_visualization.html`)
- **用途**: 比t-SNE更好的降维
- **特点**:
  - UMAP保留更多全局结构
  - 按维度着色
  - 标注规范标签
  - 交互式，可缩放

---

## 完整工作流程

### 第一次使用：建立基准

```bash
# Step 1: 运行混合聚类（推荐！）
python scripts/hybrid_label_clustering.py \
    --input-dir data/annotations_test \
    --save-mapping data/label_normalization/hybrid_mapping_v1.json \
    --export-python data/label_normalization/hybrid_dict_v1.py \
    --visualize

# Step 2: 生成高级可视化
python scripts/advanced_visualization.py \
    --input-dir data/annotations_test \
    --mapping data/label_normalization/hybrid_mapping_v1.json \
    --all

# Step 3: 人工审核
# - 查看 hybrid_clusters.png，检查聚类是否合理
# - 查看 label_sunburst.html，理解层次结构
# - 查看 label_dashboard.html，了解统计分布

# Step 4: 如果发现问题，调整threshold重新聚类
python scripts/hybrid_label_clustering.py \
    --input-dir data/annotations_test \
    --threshold 0.2 \  # 调小->更多聚类，调大->更少聚类
    --save-mapping data/label_normalization/hybrid_mapping_v2.json
```

### 后续：增量更新

当出现新标签时：

**方案A：使用AI辅助（推荐新手）**
```bash
# 发现新标签并获得AI建议
python scripts/smart_cluster.py \
    --input-dir data/annotations_new

# 根据建议更新 hybrid_dict.py
```

**方案B：自动重聚类（推荐熟练用户）**
```bash
# 直接重新运行混合聚类
python scripts/hybrid_label_clustering.py \
    --input-dir data/annotations_all \
    --threshold 0.25 \
    --save-mapping data/label_normalization/hybrid_mapping_v3.json
```

### 应用到标注文件

```bash
# 使用label_normalizer应用映射
python scripts/label_normalizer.py \
    --input-dir data/annotations_test \
    --output-dir data/annotations_normalized \
    --dry-run  # 先预览

# 确认无误后正式运行
python scripts/label_normalizer.py \
    --input-dir data/annotations_test \
    --output-dir data/annotations_normalized
```

---

## 科学性评估

### ✅ 混合方法的科学优势

1. **理论驱动 + 数据驱动结合**
   - 第一层分类基于心理学理论（Social, Safety, Esteem...）
   - 第二层聚类基于实际语义相似度
   - 避免了纯数据驱动方法的"理论失真"

2. **可解释性强**
   - 每个聚类都有明确的心理学维度归属
   - 规范标签选择基于频率+中心性，有理可依

3. **适应性好**
   - 自动处理新标签（只要前缀匹配已知维度）
   - 阈值可调，适应不同粒度需求

4. **可重复性**
   - 完全基于算法，无人为主观因素
   - 相同输入必定产生相同输出

### ⚠️ 潜在问题与解决方案

| 问题 | 影响 | 解决方案 |
|------|------|---------|
| 前缀不规范的标签 | 被归入"Unknown" | 人工审核Unknown组，手动分类 |
| 同一维度内差异过大 | 过度聚类 | 降低threshold（如0.15） |
| 聚类过于细碎 | 失去归并意义 | 提高threshold（如0.35） |
| 代表标签选择不理想 | 可读性差 | 后处理：人工指定代表标签 |

### 📊 质量指标

建议追踪以下指标：

1. **压缩率** = 1 - (规范标签数 / 原始标签数)
   - 理想值：40%-60%
   - 过低：聚类不够
   - 过高：可能过度聚类

2. **维度内聚度**
   - 计算每个聚类的平均相似度
   - 应 > 0.7（余弦相似度）

3. **维度间分离度**
   - 不同维度的聚类应该分离
   - 可视化检查：t-SNE/UMAP图中不同颜色区域应分开

---

## 更好的可视化思路

### 1. 网络图可视化
适合展示标签间的相似关系：
```python
# 可以基于相似度阈值构建网络
# 节点：标签
# 边：相似度 > 0.7
# 颜色：心理学维度
# 大小：出现频率
```

### 2. 时间演化可视化
如果你有多批标注数据：
```python
# 展示标签分布如何随时间变化
# 哪些新标签出现了？
# 哪些标签频率上升/下降？
```

### 3. 标签共现矩阵
```python
# 热力图：哪些标签经常在同一视频中出现
# 有助于发现标签间的关联模式
```

---

## 总结与建议

### 🎯 最终推荐

**对于你的项目，建议采用：**

1. **主要方法**: 混合聚类 (`hybrid_label_clustering.py`)
   - 既保留理论框架，又自动化处理
   - 是科学性和实用性的最佳平衡

2. **辅助方法**: AI交互式映射 (`smart_cluster.py`)
   - 用于处理"Unknown"维度的标签
   - 用于验证混合聚类的结果

3. **可视化**: 高级可视化套件 (`advanced_visualization.py`)
   - 用UMAP代替t-SNE（更好的全局结构）
   - 提供交互式探索和出版级静态图

### 📝 论文中如何描述

```markdown
我们采用混合聚类方法对AI生成的desire标签进行规范化：

1. **第一层分类**：基于心理学理论框架（Maslow's Hierarchy,
   Self-Determination Theory等），将标签按前缀分为Social、
   Safety、Esteem等维度。

2. **第二层聚类**：在每个维度内，使用Sentence-BERT (all-MiniLM-L6-v2)
   计算语义向量，通过层次聚类（Average Linkage, Cosine Distance）
   合并相似标签。

3. **代表标签选择**：综合考虑频率和向量中心性，选择最具代表性的
   标签作为规范形式。

最终将X个原始标签归并为Y个规范标签（压缩率Z%），在保持理论框架
完整性的同时，显著提高了标注一致性。
```

### 🚀 下一步行动

1. ✅ 运行混合聚类
2. ✅ 生成所有可视化
3. ✅ 人工审核结果，调整参数
4. ✅ 导出Python字典，集成到标注系统
5. ✅ 定期（如每月）重新聚类，纳入新标签

---

## 附录：依赖安装

```bash
# 基础依赖
pip install sentence-transformers scikit-learn numpy

# 可视化依赖
pip install matplotlib seaborn plotly pandas

# 高级功能
pip install adjustText umap-learn

# 如果遇到权限问题
pip install --user [package_name]
# 或
pip install --break-system-packages [package_name]  # Linux系统
```

---

**有问题？**
- 查看各脚本的 `--help`
- 参考示例输出文件
- 调整参数多次实验
