# 关键词优化 - 快速开始指南

## 🎯 目标

将审核通过率从 **25%** 提升到 **50-60%**

---

## 🚀 立即使用（已配置完成！）

当前配置已自动切换到优化关键词：

```python
# config/search_config.py (第12行)
KEYWORD_SET = "real_optimized"  # ✅ 已启用优化关键词
```

**现在就可以直接运行搜索！**

```bash
# 搜索视频（使用优化关键词）
python scripts/run_search.py --search-only
```

---

## 📊 可用的关键词集

### 1️⃣ `real_optimized` - 真实场景优化版 ⭐ **推荐**

**特点**：
- 避免 reaction 视频
- 监控摄像头、行车记录仪镜头
- 真实公共场所冲突
- 高质量节目片段

**预期通过率**: **50-60%**

**关键词数量**: 21个

**示例关键词**:
```
- security camera fight
- caught on camera argument
- dash cam road rage
- karen freakout caught
- Kitchen Nightmares Gordon Ramsay
- What Would You Do ABC
```

**适合场景**: 想要真实场景，不在意画质不完美

---

### 2️⃣ `film_focused` - 电影/剧集专注版

**特点**：
- 电影和电视剧片段
- 画质稳定，较少字幕
- 经典剧集场景

**预期通过率**: **55-65%**

**关键词数量**: 16个

**示例关键词**:
```
- movie argument scene
- tv show argument
- drama emotional scene
- Breaking Bad scene
- Game of Thrones scene
```

**适合场景**: 想要高画质，接受表演而非完全真实

---

### 3️⃣ `hybrid_best` - 混合最优策略

**特点**：
- 平衡真实性和质量
- 40% 真实场景 + 40% 电影剧集 + 20% 真人秀

**预期通过率**: **55-60%**

**关键词数量**: 15个

**适合场景**: 想要多样性，平衡真实与质量

---

## 🔄 如何切换关键词集

编辑 `config/search_config.py` 第12行：

```python
# 选项 1: 真实场景优化（当前）
KEYWORD_SET = "real_optimized"

# 选项 2: 电影剧集专注
KEYWORD_SET = "film_focused"

# 选项 3: 混合最优
KEYWORD_SET = "hybrid_best"

# 选项 4: 旧版本（不推荐，通过率低）
KEYWORD_SET = "standard"  # 通过率 ~25%
```

---

## 📈 预期效果对比

| 关键词集 | 通过率 | 关键词数 | 特点 | 推荐度 |
|---------|-------|---------|------|-------|
| **real_optimized** | **50-60%** | 21 | 真实场景，避免reaction | ⭐⭐⭐⭐⭐ |
| **film_focused** | **55-65%** | 16 | 电影剧集，高画质 | ⭐⭐⭐⭐ |
| **hybrid_best** | **55-60%** | 15 | 平衡真实与质量 | ⭐⭐⭐⭐⭐ |
| standard (旧) | 25% | 12 | 容易搜到reaction | ⭐⭐ |
| documentary | 30-40% | 10 | 真实但数量少 | ⭐⭐⭐ |
| tv_drama | 45-55% | 25 | 电视剧，质量稳定 | ⭐⭐⭐⭐ |

---

## 💡 使用建议

### 场景 1: 想要最多的视频数据
```python
KEYWORD_SET = "real_optimized"  # 21个关键词
VIDEOS_PER_KEYWORD = 10         # 每个搜索10个
# 预计: 210个搜索 → 约105-126个通过
```

### 场景 2: 想要最高质量
```python
KEYWORD_SET = "film_focused"    # 电影剧集
STRICT_MODE = True              # 严格审核
# 预计: 最高通过率 + 最佳画质
```

### 场景 3: 快速测试
```python
KEYWORD_SET = "hybrid_best"     # 15个关键词
VIDEOS_PER_KEYWORD = 5          # 每个搜索5个
# 预计: 75个搜索 → 约40-45个通过
```

---

## 🎨 优化关键词的设计理念

### ✅ 包含的元素

1. **"caught on camera"** - 监控/记录镜头，真实性高
2. **"security/dash cam/cctv"** - 无字幕，原始画面
3. **"real/actual"** - 强调真实性
4. **具体节目名** - 已验证的高质量来源
5. **"scene"** - 电影/剧集片段，画质稳定

### ❌ 避免的元素

1. **"reaction"** - 容易搜到观看反应视频
2. **"compilation"** - 剪辑合集
3. **"meme"** - 娱乐性强，不适合研究
4. **泛化词汇** - 如 "emotional moment"（太宽泛）

---

## 📊 实时查看配置

```bash
# 查看当前配置
python config/search_config.py

# 输出示例：
# 📋 当前搜索配置
# ==================
# 关键词集合: real_optimized
# 关键词数量: 21
# 每个关键词搜索: 10 个视频
# 预计搜索总数: 210 个视频
```

---

## 🔧 自定义关键词

如果你想完全自定义：

```python
# config/search_config.py

CUSTOM_KEYWORDS = [
    "your custom keyword 1",
    "your custom keyword 2",
    # ... 添加更多
]

# 当 CUSTOM_KEYWORDS 不为 None 时，会忽略 KEYWORD_SET
```

---

## 📝 关键词效果追踪

运行搜索后，系统会自动记录每个关键词的效果：

```bash
# 查看哪些关键词通过率高
python -c "
import json
data = json.load(open('data/youtube_links.json', 'r', encoding='utf-8'))
from collections import defaultdict
stats = defaultdict(lambda: {'total': 0, 'approved': 0})

for v in data['videos']:
    kw = v.get('keyword', 'Unknown')
    stats[kw]['total'] += 1
    if v.get('approved'):
        stats[kw]['approved'] += 1

for kw, s in sorted(stats.items(), key=lambda x: x[1]['approved']/x[1]['total'] if x[1]['total'] > 0 else 0, reverse=True):
    if s['total'] > 0:
        rate = s['approved'] / s['total'] * 100
        print(f'{kw}: {s[\"approved\"]}/{s[\"total\"]} ({rate:.1f}%)')
"
```

---

## 🎉 开始使用

**当前配置已经是优化后的 `real_optimized`，直接运行即可！**

```bash
# 1. 搜索视频
python scripts/run_search.py --search-only

# 2. 下载和审核
python scripts/run_download_review.py

# 3. 查看通过率（应该在 50-60% 左右）
python -c "
import json
data = json.load(open('data/youtube_links.json', 'r', encoding='utf-8'))
total = len(data['videos'])
approved = sum(1 for v in data['videos'] if v.get('approved'))
print(f'通过率: {approved}/{total} ({approved/total*100:.1f}%)')
"
```

---

## 💬 反馈和调整

如果通过率仍然不理想：

1. **尝试 `film_focused`** - 更稳定的电影剧集
2. **降低严格度** - `STRICT_MODE = False`
3. **联系我** - 提供拒绝原因，进一步优化

祝你搜索顺利！🎬
