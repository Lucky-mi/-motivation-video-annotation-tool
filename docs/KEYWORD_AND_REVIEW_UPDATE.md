# 🔄 关键词和审核系统重大更新

## 📅 更新时间
2025-11-24

## 🎯 更新原因

根据实际测试发现两个核心问题：

1. **搜索词过于理论性** → 搜索到的大多是科普讲解视频，缺乏真实人类行为展现
2. **AI审核过于宽松** → 过度依赖对话和字幕，忽视了行为和动作中体现的心智理论

## ✅ 核心改进

### 改进1: 关键词从"理论型"改为"行为展现型"

#### 之前的问题关键词（已废弃）：
```python
"social interaction psychology"        # 搜到：心理学讲座
"theory of mind"                       # 搜到：理论讲解视频
"understanding human motivation"        # 搜到：教育科普
"emotional intelligence social"        # 搜到：技能培训
```

#### 现在的行为展现型关键词：
```python
"people arguing"           # 搜到：真实争吵场景
"emotional reaction"       # 搜到：情感爆发瞬间
"couple fight"            # 搜到：情侣冲突
"crying moment"           # 搜到：真实哭泣场景
"awkward moment"          # 搜到：尴尬社交情境
```

### 改进2: AI审核强制要求"行为观察"

#### 之前的审核标准（过于宽松）：
- ✅ 有人类出现
- ✅ 有社交互动或心理活动
- ✅ 对话展现意图也可以

**结果**：大量访谈、讲解、对话类视频通过，缺乏可观察的行为

#### 现在的审核标准（行为优先）：
- ⚠️ **核心**：心智理论必须通过【动作和交互】体现
- ❌ **明确拒绝**：仅通过对话展现意图的视频
- ❌ **明确拒绝**：主要依靠字幕/旁白讲解的视频
- ❌ **明确拒绝**：访谈、演讲、讲课等静态场景
- ❌ **明确拒绝**：科普讲解（即使主题是心理学）

**必须有的可观察行为**：
- 面部表情变化（惊讶、愤怒、悲伤、恐惧等）
- 肢体语言（手势、姿态、身体距离、触碰、回避）
- 眼神交流（对视、回避、凝视、眼神互动）
- 行为反应（对他人行为的即时反应）
- 情境互动（争吵、拥抱、推开、靠近、转身离开）

---

## 📊 完整关键词更新

### 1. 标准关键词集（12个）- 默认使用

**之前**（理论性）：
```python
"social interaction psychology"
"people understanding emotions"
"theory of mind"
"emotional intelligence social"
...
```

**现在**（行为展现）：
```python
# 冲突争执（真实情感爆发）
"people arguing"
"couple fight"
"family argument"

# 强烈情感表达
"emotional reaction"
"crying moment"
"surprise reaction"

# 日常对话互动
"friends talking"
"deep conversation"
"awkward moment"

# 复杂情感关系
"jealousy moment"
"betrayal reaction"
"heartbreak moment"
```

### 2. 扩展关键词集（24个）

```python
# 冲突争执（6个）
"people arguing"
"couple fight"
"family argument"
"friends conflict"
"heated debate"
"confrontation moment"

# 情感爆发（6个）
"emotional reaction"
"crying moment"
"surprise reaction"
"angry outburst"
"emotional breakdown"
"frustration moment"

# 日常互动（6个）
"friends talking"
"deep conversation"
"awkward moment"
"embarrassing situation"
"uncomfortable silence"
"tension moment"

# 复杂关系（6个）
"jealousy moment"
"betrayal reaction"
"heartbreak moment"
"breakup scene"
"apology moment"
"reconciliation scene"
```

### 3. 完整关键词集（36个）

新增：
- `workplace conflict` - 职场冲突
- `panic attack` - 恐慌发作
- `laughter moment` - 欢笑瞬间
- `scared reaction` - 惊恐反应
- `gossip moment` - 八卦时刻
- `secret revealed` - 秘密揭露
- `confession moment` - 坦白时刻
- `romantic proposal` - 浪漫求婚
- `first date awkward` - 初次约会尴尬
- `relationship drama` - 关系戏剧

### 4. 电视剧关键词（25个）

**之前**（过于正式）：
```python
"tv series emotional scene"
"drama series relationship conflict"
"tv show character development"
```

**现在**（直接场景）：
```python
# 冲突争吵
"tv show fight scene"
"drama argument scene"
"drama characters arguing"

# 情感爆发
"tv series crying scene"
"drama emotional breakdown"
"tv show angry scene"
"drama shocked reaction"
"tv series betrayal scene"

# 对话互动
"tv show conversation scene"
"drama dialogue scene"
"tv series confession scene"
"drama secret revealed"

# 关系场景
"tv series breakup scene"
"drama romantic scene"
"tv show jealousy scene"
"drama apology scene"
```

### 5. 电影关键词（15个）

```python
# 情感场景
"movie fight scene"
"film crying scene"
"movie argument scene"
"film emotional scene"
"movie angry scene"

# 对话互动
"movie conversation scene"
"film dialogue scene"
"movie confession scene"
"film confrontation scene"

# 关系场景
"movie breakup scene"
"film romantic scene"
"movie betrayal scene"
"film reunion scene"
"movie proposal scene"
```

### 6. 纪录片/真实场景（10个）

```python
"real people arguing"
"real life conflict"
"real emotional moment"
"candid reaction"
"real couple fight"
"real family moment"
"street interview emotional"
"real life drama"
"caught on camera emotional"
"real confrontation moment"
```

---

## 🤖 AI审核Prompt更新

### 严格模式的新标准

#### 1. 真实人类的可观察行为 ⭐⭐⭐
- 画面中必须有真人（非动画、游戏、照片）
- 人物面部清晰，能观察到表情变化
- 人物占据画面主体，能清楚看到肢体语言
- ❌ 拒绝：仅有配音、字幕、静态图片、远景人物

#### 2. 行为中体现的心智理论 ⭐⭐⭐ (核心!)
必须通过以下可观察的行为展现：
- **面部表情变化**：惊讶、愤怒、悲伤、恐惧、厌恶、喜悦
- **肢体语言**：手势、姿态、身体距离、触碰、回避
- **眼神交流**：对视、回避、凝视、眼神互动
- **行为反应**：对他人行为的即时反应
- **情境互动**：争吵、拥抱、推开、靠近、转身离开

❌ **明确拒绝**：
- 仅通过对话展现意图的视频（看不到行为）
- 主要依靠字幕/旁白讲解的视频
- 访谈类视频（纯坐着说话，无行为展现）
- 新闻播报、演讲、讲课等静态场景
- 科普讲解视频（即使内容是心理学）

#### 3. 真实的社交互动场景 ⭐⭐
- 有明确的社交情境（冲突、和解、欺骗、安慰、谈判等）
- 能观察到意图、欲望、信念在行为中的体现
- 有情感的真实流露（非表演式的夸张）
- ✅ 好例子：争吵时的推搡、安慰时的拥抱、说谎时的回避眼神
- ❌ 坏例子：坐着平静地讨论情感、讲述故事、理论讲解

### 明确排除的类型

1. **科普讲解类**：心理学讲座、理论讲解、教育视频（即使主题相关）
2. **访谈对话类**：坐着聊天、播客、新闻采访（无行为展现）
3. **技能展示类**：烹饪、化妆、手工（无情感互动）
4. **游戏/动画**：游戏录屏、动画片、虚拟角色
5. **静态内容**：幻灯片、文字、静态图片集
6. **纯风景/动物**：无人类或人类仅为背景
7. **纯搞笑/恶作剧**：无真实情感，纯为娱乐

### 输出格式更新

新增字段 `"可观察行为"` - 强制AI描述看到的表情、动作、肢体语言：

```json
{
  "pass": true/false,
  "reason": "重点描述【观察到的行为】而非对话内容",
  "可观察行为": "描述看到的表情、动作、肢体语言等（非对话内容）",
  "互动类型": "眼神交流/肢体接触/推拉动作/表情反应/姿态变化/无明显互动",
  "关键场景描述": "描述最有价值的行为场景（非对话场景）"
}
```

---

## 📈 预期效果对比

### 使用旧关键词和旧审核标准

**搜索结果**：
- 心理学讲座：30%
- 教育科普视频：25%
- 访谈对话：20%
- 真实行为展现：25%

**AI审核通过率**：70%
**实际可用率**：约25%（只有真实行为展现的部分）

### 使用新关键词和新审核标准

**搜索结果**：
- 真实冲突场景：35%
- 情感展现片段：30%
- 剧情片段：25%
- 其他：10%

**AI审核通过率**：40-50%（更严格）
**实际可用率**：40-50%（大幅提升！）

---

## 🚀 如何使用

### 1. 配置文件已自动更新

`config/search_config.py` 中的关键词已全部替换为行为展现型

### 2. 无需修改代码

AI审核的prompt已在 `backend/content_filter.py` 中更新

### 3. 直接运行即可

```bash
# 激活虚拟环境
cd d:\Desire-VQA\video_anno
.\venv\Scripts\activate

# 运行搜索（自动使用新关键词和新审核标准）
python scripts\run_search.py
```

### 4. 推荐配置

```python
# config/search_config.py
KEYWORD_SET = "standard"      # 12个行为展现型关键词
VIDEOS_PER_KEYWORD = 10       # 每个关键词10个
ENABLE_AI_REVIEW = True       # 启用AI审核
STRICT_MODE = True            # 使用严格模式（强制行为展现）
```

预期：搜索120个 → 通过50-60个高质量行为展现视频

---

## 💡 使用建议

### 建议1: 先用标准模式测试

```python
KEYWORD_SET = "standard"      # 12个关键词
VIDEOS_PER_KEYWORD = 5        # 先测试5个
STRICT_MODE = False           # 先用标准模式
```

运行后查看：
- 搜索到的视频类型是否符合预期（行为展现型）
- AI拒绝的原因（检查 `data/youtube_links.json`）

### 建议2: 根据通过率调整

如果通过率：
- **< 30%**：可能标准太严格 → 使用 `STRICT_MODE = False`
- **30-50%**：理想范围 ✅
- **> 70%**：可能标准太宽松，检查视频质量

### 建议3: 分类测试不同关键词集

```bash
# 测试1: 冲突类场景
KEYWORD_SET = "minimal"  # 包含 arguing, fight, conflict
VIDEOS_PER_KEYWORD = 5

# 测试2: 电视剧片段
KEYWORD_SET = "tv_drama"
VIDEOS_PER_KEYWORD = 5

# 测试3: 综合采集
KEYWORD_SET = "standard"
VIDEOS_PER_KEYWORD = 10
```

---

## 🔍 验证改进效果

### 验证步骤

1. **运行搜索**
```bash
python scripts\run_search.py
```

2. **检查搜索结果**
```bash
# 查看搜索到的视频标题
cat data/search_results.json | grep "title"
```

3. **检查审核结果**
```bash
# 查看AI审核的拒绝原因
cat data/youtube_links.json | grep "review_reason"
```

4. **手动抽查视频**
```bash
# 随机查看几个通过的视频
# 检查是否真的是行为展现型（而非讲解型）
```

### 预期观察

**好的结果**（目标）：
- ✅ 搜索到的标题包含：fight, crying, arguing, reaction 等动作词
- ✅ AI拒绝理由包含："无明显行为展现"、"主要是对话讲解"
- ✅ 通过的视频能清楚看到表情、动作、肢体语言

**不好的结果**（需要调整）：
- ❌ 搜索到的标题包含：psychology, explained, tutorial, guide
- ❌ AI通过的视频主要是人坐着聊天
- ❌ 通过率接近100%（说明审核不够严格）

---

## 📞 相关文档

- [完整系统指南](COMPLETE_SYSTEM_GUIDE.md) - 系统全功能
- [电视剧采集指南](TV_DRAMA_GUIDE.md) - 影视片段专用
- [审核指南](REVIEW_GUIDE.md) - 独立审核已下载视频
- [快速开始](QUICK_START.md) - 三步快速上手

---

## 🎉 总结

### 核心改变

1. **关键词**：从"理论性"改为"行为展现性" ✅
2. **审核**：强制要求"动作和交互"，拒绝"仅对话/讲解" ✅

### 预期效果

- 搜索质量：⬆️ 大幅提升（更多真实行为场景）
- 审核通过率：⬇️ 从70%降至40-50%（更严格）
- 实际可用率：⬆️ 从25%提升至40-50%（翻倍！）

### 立即开始

```bash
python scripts\run_search.py
```

祝采集顺利！ 🚀
