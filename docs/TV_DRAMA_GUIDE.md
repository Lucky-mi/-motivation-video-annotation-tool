# 📺 电视剧与电影片段采集指南

## 🎯 为什么要采集电视剧/电影片段？

电视剧和电影片段是**极佳**的心智理论研究素材，因为：

✅ **丰富的人物互动**：对话、冲突、情感表达
✅ **复杂的心理动机**：角色目标、隐藏意图、情感变化
✅ **多样的社交情境**：家庭、职场、友情、爱情
✅ **专业的剧本编排**：精心设计的情节和人物弧线
✅ **高质量的视听效果**：清晰的画面和音频

---

## 🆕 新增功能

### 1. 专用关键词集合

现在有**75个新增关键词**，专门针对影视内容：

| 类别 | 关键词数 | 说明 |
|------|----------|------|
| **TV Drama** (电视剧) | 25个 | 情感场景、人物互动、心理戏份 |
| **Movie Clips** (电影片段) | 15个 | 经典场景、心理分析 |
| **Documentary** (纪录片) | 10个 | 真实人类行为 |
| **Mega** (超大集合) | 111个 | 包含所有类型 |

### 2. 智能去重系统 ⭐

**问题：** 电视剧片段容易重复（同一剧集的多个场景）

**解决方案：** 智能识别同一剧集，自动去重

**特性：**
- ✅ 自动识别剧集名称（即使标题不同）
- ✅ 基于相似度匹配（85%以上认为是同一剧集）
- ✅ 可配置：完全去重 或 保留少量同剧片段

**示例：**
```python
# 这些会被识别为同一剧集
"Breaking Bad - Best Scene"
"Breaking Bad S01E05 - Intense Moment"
"Breaking Bad (2008) - Final Scene"

# 结果：只保留第一个，其他自动过滤
```

---

## 🚀 快速使用

### 方式1: 仅搜索电视剧片段

编辑 `config/search_config.py`:

```python
# 使用电视剧关键词集
KEYWORD_SET = "tv_drama"  # 25个电视剧相关关键词

# 每个关键词搜索10个
VIDEOS_PER_KEYWORD = 10

# 总共 = 25 × 10 = 250个候选视频
```

### 方式2: 搜索电影片段

```python
KEYWORD_SET = "movie_clips"  # 15个电影相关关键词
VIDEOS_PER_KEYWORD = 10
# 总共 = 15 × 10 = 150个候选视频
```

### 方式3: 综合搜索（推荐）

```python
KEYWORD_SET = "mega"  # 111个关键词（包含所有类型）
VIDEOS_PER_KEYWORD = 5
# 总共 = 111 × 5 = 555个候选视频
```

---

## 🎛️ 去重配置

在搜索时可以控制去重行为：

### 配置1: 严格去重（推荐）

```python
# 在 run_search.py 或直接调用时
downloader.batch_search(
    keywords=keywords,
    videos_per_keyword=10,
    enable_smart_dedup=True,     # 启用智能去重
    allow_same_series=False,     # 不允许同剧集的多个片段
    max_per_series=1             # 每个剧集最多1个片段
)
```

**效果：** 每部剧/电影只保留1个片段，最大化多样性

### 配置2: 允许少量重复

```python
downloader.batch_search(
    keywords=keywords,
    videos_per_keyword=10,
    enable_smart_dedup=True,
    allow_same_series=True,      # 允许同剧集的多个片段
    max_per_series=3             # 每个剧集最多3个片段
)
```

**效果：** 如果某剧有多个优秀片段，最多保留3个

### 配置3: 基础去重

```python
downloader.batch_search(
    keywords=keywords,
    videos_per_keyword=10,
    enable_smart_dedup=False     # 仅去除完全相同的URL
)
```

**效果：** 只要URL不同就保留，可能有较多同剧片段

---

## 📊 预期效果

### 搜索阶段
```
🚀 开始批量搜索，共 25 个关键词
⚙️ 智能去重: 启用 | 同剧集片段: 不允许

[1/25] 搜索关键词: tv series emotional scene
✅ 搜索完成，筛选出 10 个视频

[2/25] 搜索关键词: drama series relationship conflict
✅ 搜索完成，筛选出 10 个视频
...
```

### 去重阶段
```
📊 搜索完成: 共找到 247 个候选视频

🎯 智能去重完成:
   - 总视频: 247 个
   - 去重后: 168 个
   - 移除重复: 79 个
   - 唯一剧集/电影: 142 部  ← 识别出142部不同的剧/电影
```

### 典型去重案例
```
移除的重复（示例）:
  ✗ Breaking Bad S01E01 - Pilot Scene
  ✗ Breaking Bad Best Moments Compilation
  ✗ Breaking Bad Season 5 Finale
  ✓ Breaking Bad - Jesse's Breakdown (保留的)

  ✗ Friends - Ross and Rachel Scene
  ✗ Friends Season 2 Episode 5
  ✓ Friends - Chandler's Best Line (保留的)
```

---

## 🎬 关键词详解

### 电视剧关键词分类

#### 1. 情感剧情 (5个) - 最核心
```python
"tv series emotional scene"          # 情感场景
"drama series relationship conflict"  # 关系冲突
"tv show character development"       # 角色发展
"series emotional moments"            # 情感时刻
"drama series psychological scene"    # 心理场景
```

#### 2. 人物互动 (5个)
```python
"tv series dialogue scene"     # 对话场景
"drama confrontation scene"    # 对抗场景
"tv show argument scene"       # 争吵场景
"series character interaction" # 角色互动
"drama emotional conversation" # 情感对话
```

#### 3. 心理戏份 (5个) - 深度挖掘
```python
"tv series psychological drama"  # 心理剧
"drama series betrayal scene"    # 背叛场景
"tv show moral dilemma"          # 道德困境
"series character motivation"    # 角色动机
"drama decision making scene"    # 决策场景
```

#### 4. 关系动力学 (5个)
```python
"tv series family dynamics"   # 家庭动力
"drama friendship conflict"   # 友情冲突
"tv show romantic tension"    # 浪漫张力
"series trust issues"         # 信任问题
"drama power dynamics"        # 权力动态
```

#### 5. 特定类型 (5个) - 特定题材
```python
"psychological thriller series scene"  # 心理惊悚
"crime drama interrogation"            # 犯罪剧审讯
"legal drama courtroom scene"          # 法律剧法庭
"medical drama ethical dilemma"        # 医疗剧伦理
"political drama negotiation"          # 政治剧谈判
```

### 电影关键词分类

#### 1. 经典场景 (5个)
```python
"movie scene emotional breakthrough"  # 情感突破
"film clip character revelation"      # 角色揭示
"movie dialogue psychology"           # 对话心理学
"film scene moral choice"             # 道德选择
"movie clip relationship moment"      # 关系时刻
```

#### 2. 心理分析 (5个)
```python
"movie analysis psychology"        # 电影心理学分析
"film scene breakdown psychology"  # 场景分解
"movie character psychology"       # 角色心理学
"film psychology explained"        # 心理学解读
"cinema therapy scene analysis"    # 电影疗法分析
```

#### 3. 特定类型 (5个)
```python
"indie film emotional scene"     # 独立电影
"drama film intense scene"       # 剧情片
"psychological film analysis"    # 心理分析
"character study film clip"      # 角色研究
"movie scene theory of mind"     # 心智理论
```

---

## 💡 使用建议

### 建议1: 分阶段采集

```python
# 第一阶段：测试电视剧关键词
KEYWORD_SET = "tv_drama"
VIDEOS_PER_KEYWORD = 3
# = 25 × 3 = 75个视频（测试）

# 第二阶段：扩大规模
KEYWORD_SET = "tv_drama"
VIDEOS_PER_KEYWORD = 10
# = 25 × 10 = 250个视频

# 第三阶段：综合采集
KEYWORD_SET = "mega"
VIDEOS_PER_KEYWORD = 5
# = 111 × 5 = 555个视频
```

### 建议2: 根据研究需求选择

| 研究重点 | 推荐关键词集 | 原因 |
|---------|-------------|------|
| 日常互动 | `tv_drama` | 电视剧更贴近日常 |
| 极端情境 | `movie_clips` | 电影情节更戏剧化 |
| 真实行为 | `documentary` | 纪录片最真实 |
| 全面数据 | `mega` | 涵盖所有类型 |

### 建议3: 调整去重策略

```python
# 如果通过率很高(>70%)，可以更宽松
allow_same_series = True
max_per_series = 3

# 如果重复太多，更严格
allow_same_series = False
max_per_series = 1
```

---

## 🔍 去重算法说明

### 工作原理

1. **提取剧名**
```python
"Breaking Bad - Best Scene"
    → 移除 "- Best Scene"
    → 移除括号、剧集编号等
    → 得到 "breaking bad"
```

2. **相似度匹配**
```python
"breaking bad" vs "breaking bad" = 1.00 (100% 相同)
"breaking bad" vs "braking bad" = 0.92 (92% 相似)
"breaking bad" vs "friends" = 0.20 (20% 相似)

# 设定阈值：85%以上认为是同一剧集
```

3. **多重检查**
- 检查1: 视频ID（完全相同的视频）
- 检查2: 频道+标题（完全相同的上传）
- 检查3: 剧集名称（相似度匹配）

---

## 📈 效果对比

### 不使用去重
```
搜索: 250个视频
其中:
- Breaking Bad片段: 15个
- Friends片段: 12个
- The Office片段: 10个
- ...
总计：大量重复
```

### 使用严格去重
```
搜索: 250个视频
去重后: 165个视频

其中:
- Breaking Bad片段: 1个 ✓
- Friends片段: 1个 ✓
- The Office片段: 1个 ✓
- ...
总计：165部不同的剧/电影 ✓
```

### 使用宽松去重
```
搜索: 250个视频
去重后: 210个视频

其中:
- Breaking Bad片段: 3个（不同场景）
- Friends片段: 3个（不同场景）
- The Office片段: 3个（不同场景）
- ...
总计：保留多样性的同时允许优质剧集多个片段
```

---

## 🎯 完整示例

### 代码示例
```python
from backend.downloader import VideoDownloader

# 初始化
dl = VideoDownloader()

# 使用电视剧关键词 + 智能去重
keywords = [
    "tv series emotional scene",
    "drama series psychological scene",
    "tv show character development"
]

videos = dl.batch_search(
    keywords=keywords,
    videos_per_keyword=10,
    enable_smart_dedup=True,     # 启用智能去重
    allow_same_series=False,     # 每部剧只要1个
    max_per_series=1
)

print(f"找到 {len(videos)} 个独特的视频片段")

# 查看剧集分布
from collections import Counter
from backend.deduplicator import VideoDeduplicator

dedup = VideoDeduplicator()
series_names = [dedup.extract_series_name(v['title']) for v in videos]
distribution = Counter(series_names)

print("\n剧集分布（Top 10）:")
for series, count in distribution.most_common(10):
    print(f"  {series}: {count}个片段")
```

### 运行示例
```bash
# 激活虚拟环境
cd d:\Desire-VQA\video_anno
.\venv\Scripts\activate

# 编辑配置文件
# 修改 config/search_config.py:
#   KEYWORD_SET = "tv_drama"
#   VIDEOS_PER_KEYWORD = 10

# 运行搜索
python scripts/run_search.py
```

---

## 🆘 常见问题

### Q: 为什么有些剧集没被识别为重复？

**A:** 如果标题差异太大，可能无法识别。例如：
```python
"The Office" vs "办公室的故事"  # 语言不同，无法匹配
```

**解决方案：** 调整 `max_per_series` 适当增加，允许2-3个同剧片段。

### Q: 如何完全禁用去重？

**A:**
```python
enable_smart_dedup = False
```

### Q: 电视剧片段通过率低怎么办？

**A:**
1. 切换到标准审核模式：`STRICT_MODE = False`
2. 电视剧片段通常质量很高，如果通过率低可能是关键词问题
3. 尝试更具体的关键词，如 "drama series emotional"

---

## 📚 总结

现在你有：

✅ **75个新增关键词**，专门针对影视内容
✅ **智能去重系统**，自动识别同剧集片段
✅ **灵活的配置**，可调节去重策略
✅ **111个关键词**的超大集合（mega模式）

**推荐工作流：**

```bash
# 1. 小规模测试（75个视频）
KEYWORD_SET = "tv_drama"
VIDEOS_PER_KEYWORD = 3

# 2. 标准采集（250个视频）
KEYWORD_SET = "tv_drama"
VIDEOS_PER_KEYWORD = 10

# 3. 大规模采集（555个视频）
KEYWORD_SET = "mega"
VIDEOS_PER_KEYWORD = 5
```

开始采集你的电视剧和电影素材吧！ 🎬
