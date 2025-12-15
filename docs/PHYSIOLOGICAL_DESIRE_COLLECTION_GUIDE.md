# 生理需求与二阶Desire数据收集指南

> **创建日期**: 2025-12-14
> **目标**: 收集生理需求（饥饿、睡眠、体温、疼痛）和二阶desire（欲望冲突）的高质量视频数据

---

## 📋 目录

1. [背景与动机](#背景与动机)
2. [关键词策略](#关键词策略)
3. [快速开始](#快速开始)
4. [关键词集合详解](#关键词集合详解)
5. [收集策略建议](#收集策略建议)
6. [预期效果](#预期效果)

---

## 🎯 背景与动机

### 当前问题
- 现有数据集中**生理需求**方面的视频偏少（冷、饿、困等）
- 缺乏**二阶desire**推理数据（欲望冲突、意志力斗争）
- 现有关键词多聚焦于社会互动，生理层面覆盖不足

### 解决方案
采用**情境化关键词策略**（Context of Deprivation）：
- ❌ 不搜索欲望本身（如"hunger", "tired"）
- ✅ 搜索导致该欲望的外部情境（如"fasting vlog", "night shift"）

---

## 🔑 关键词策略

### 策略一：情境化关键词
搜索**导致欲望的情境**而非欲望本身，提高推理难度和数据价值。

**示例对比**：
| ❌ 传统关键词 | ✅ 情境化关键词 | 推理价值 |
|-------------|----------------|---------|
| "hungry" | "fasting vlog 24h" | 高：需要从视觉线索推断饥饿状态 |
| "tired" | "fighting sleep" | 高：捕捉对抗睡意的挣扎过程 |
| "cold" | "ice bath challenge" | 高：生理反应 vs 社交动机冲突 |

### 策略二：长视频切片分析
通过长视频（如"Study with me 12 hours"）捕捉**渐变状态**：
- **第10分钟**: 精力充沛、姿态端正
- **第110分钟**: 坐姿瘫软、频繁看表、打哈欠

→ **价值**: 提供Desire逐渐增强的时间序列证据

### 策略三：无意图动作与失败集锦
"Fail Army"、"Scare Cam"等视频捕捉**社会面具脱落**的瞬间：
- 惊恐、疼痛、逃避等原始生理反应
- 突破预先策划的社会行为
- 展现最真实的"求生/安全"欲望

### 策略四：二阶Desire（欲望冲突）
捕捉**意志力斗争**场景：
- **犹豫**: 手伸向食物又缩回（try not to eat challenge）
- **自我约束**: 闹钟放远处强迫起床
- **事后后悔**: 吃完高热量食物的懊恼表情

**示例**: "Ice Bucket Challenge"
- **社交Desire**: 获得认可、支持公益
- **生理Desire**: 逃避冰水刺激
- **冲突**: 被浇水时的尖叫、瑟缩、逃跑

---

## 🚀 快速开始

### 方法1：使用完整关键词集（推荐）

编辑 [config/search_config.py](../config/search_config.py):

```python
# 修改 KEYWORD_SET 为：
KEYWORD_SET = "desire_extended"  # 包含生理需求 + 二阶desire（77个关键词）
```

然后运行搜索：

```bash
# 仅搜索（推荐先做，避免大量下载）
python scripts/run_search.py --search-only

# 查看搜索结果
cat data/search_results.json | head -n 100

# 下载和审核（限制前50个高分视频）
python scripts/run_download_review.py --limit 50
```

### 方法2：仅收集生理需求

```python
KEYWORD_SET = "physiological"  # 仅生理需求（41个关键词）
```

### 方法3：仅收集二阶Desire

```python
KEYWORD_SET = "second_order"  # 仅欲望冲突（36个关键词）
```

### 方法4：自定义组合

```python
from search_config import KEYWORDS_PHYSIOLOGICAL, KEYWORDS_SECOND_ORDER

# 只要饥饿和睡眠相关
CUSTOM_KEYWORDS = [
    "fasting vlog 24h",
    "survival challenge alone",
    "fighting sleep",
    "trying to stay awake",
    "night shift vlog"
]
```

---

## 📊 关键词集合详解

### 1. KEYWORDS_PHYSIOLOGICAL（41个关键词）

#### 1.1 饥饿/进食（7个）
**视觉特征**: 眼神呆滞、吞咽口水、进食速度极快、对食物凝视

```
- fasting vlog 24h
- survival challenge alone
- military ration taste test
- ramadan daily routine
- post workout cheat meal
- mukbang extreme hunger
- food challenge starving
```

**推荐场景**:
- ⭐ **Fasting vlog**: 断食过程中的饥饿感渐变
- ⭐ **Survival challenge**: 野外生存的食物匮乏
- ⭐ **Military ration**: 长期不佳饮食后的进食反应

#### 1.2 睡眠/休息（8个）
**视觉特征**: 头部下垂、频繁眨眼、打哈欠、揉眼睛

```
- fighting sleep
- trying to stay awake
- night shift vlog
- nodding off in class
- marathon exhaustion
- study with me 12 hours
- falling asleep at work
- sleep deprivation challenge
```

**推荐场景**:
- ⭐ **Study with me 12 hours**: 长时间学习的疲惫渐变
- ⭐ **Night shift vlog**: 夜班工作对抗睡意
- ⭐ **Sleep deprivation challenge**: 主动挑战不睡觉

#### 1.3 体温调节/舒适（8个）
**视觉特征**: 颤抖、大量出汗、皮肤发红、蜷缩身体

```
- ice bath challenge
- sauna endurance
- polar plunge
- walking in blizzard
- heatwave no AC
- spicy noodle challenge
- cold water challenge
- extreme heat survival
```

**推荐场景**:
- ⭐ **Ice bath challenge**: 社交动机 vs 身体舒适的冲突
- ⭐ **Polar plunge**: 极寒环境的生理反应
- ⭐ **Spicy noodle challenge**: 辣味带来的生理痛感

#### 1.4 疼痛规避（7个）
**视觉特征**: 畏缩、流泪、尖叫、屏住呼吸、肌肉紧绷

```
- tattoo pain level
- waxing reaction
- removing bandaid
- piercing reaction
- spicy food reaction
- hot sauce challenge
- painful massage
```

**推荐场景**:
- ⭐ **Tattoo pain level**: 长时间忍受疼痛
- ⭐ **Waxing reaction**: 瞬间疼痛的真实反应
- ⭐ **Hot sauce challenge**: 社交挑战 vs 生理痛感

#### 1.5 身体活动/氧气（6个）
**视觉特征**: 大口喘气、面色潮红、无法说话、身体瘫软

```
- holding breath challenge
- altitude sickness
- crossfit fail
- marathon finish line collapse
- breathing exercise extreme
- underwater challenge
```

---

### 2. KEYWORDS_SECOND_ORDER（36个关键词）

#### 2.1 欲望冲突场景（5个）
**特点**: 多重desire冲突，生理本能 vs 社会动机

```
- ice bucket challenge          # 社交认可 vs 身体舒适
- trying not to laugh challenge # 自我控制 vs 本能反应
- try not to eat challenge      # 意志力 vs 食欲
- diet cheat day vlog           # 自律 vs 欲望
- resisting temptation          # 克制 vs 诱惑
```

**深度洞察**:
- **Ice bucket challenge**: 完美的冲突性数据源
  - **社会desire**: 获得认可、支持公益
  - **生理desire**: 逃避冰水刺激
  - **表现**: 尖叫、瑟缩、逃跑（生理本能突破社会面具）

#### 2.2 无意图动作与失败集锦（7个）
**特点**: 社会面具脱落，真实本能反应

```
- reflexes compilation
- scare cam reactions
- clumsy moments
- instant karma
- fail army
- people falling
- unexpected reactions
```

**价值**:
- 捕捉人类失去控制瞬间的真实反应
- 最原始的"求生/安全"欲望（Reiss的Tranquility）
- 平衡数据集中过多的"有预谋社会行为"

#### 2.3 意志力斗争（6个）
**特点**: 犹豫、自我约束、事后后悔

```
- trying to quit smoking
- struggling to wake up
- procrastination vlog
- breaking bad habits
- new year resolution fail
- giving up challenge
```

**推理场景**:
- **犹豫**: 手伸向香烟又缩回
- **自我约束**: 把闹钟放远处强迫起床
- **后悔**: 放弃挑战后的懊恼表情

#### 2.4 长视频切片（4个）
**特点**: 从专注到疲惫的渐变过程

```
- study with me tired
- all nighter vlog
- 24 hour challenge exhausted
- working overtime tired
```

**分析策略**:
利用Gemini进行**滑动窗口分析**（Sliding Window Analysis）：
- 比较第10分钟 vs 第110分钟的状态差异
- 捕捉desire逐渐增强的时间序列

#### 2.5 社交压力 vs 生理需求（4个）

```
- holding pee challenge
- not sleeping challenge
- endurance challenge
- strength test fail
```

---

## 💡 收集策略建议

### 阶段1：先搜索，后下载

```bash
# 1. 仅搜索（快速预览）
python scripts/run_search.py --search-only

# 2. 查看搜索结果（按评分排序）
cat data/search_results.json | head -n 100

# 3. 选择性下载（避免浪费时间和存储）
python scripts/run_download_review.py --limit 50
```

**优点**:
- 避免大量下载不合格视频
- 预先评估搜索质量
- 节省时间和API配额

### 阶段2：分批审核

```bash
# 第一批：前50个
python scripts/run_download_review.py --limit 50

# 第二批：50-100
python scripts/run_download_review.py --start 50 --limit 50

# 第三批：100-150
python scripts/run_download_review.py --start 100 --limit 50
```

**优点**:
- 支持断点续传
- 避免网络中断丢失进度
- 灵活控制批次大小

### 阶段3：人工审核和标注

```bash
# 启动审核平台
python run_reviewer.py

# 选择"完整系统"启动后端API + 前端
```

在审核平台中：
- ✅ **Approve**: 符合生理需求/二阶desire特征
- ⚠️ **Modify**: 标注需要调整
- ❌ **Delete**: 不符合目标

### 阶段4：批量重命名

```bash
# 使用AI生成描述性文件名
python batch_rename_annotations.py
```

**示例**:
```
01133e42-8b19.json → ice_bath_challenge_shivering.json
02d961a4-8c7f.json → fasting_vlog_extreme_hunger.json
03154389-46cb.json → fighting_sleep_nodding_off.json
```

---

## 📈 预期效果

### 数据集平衡改善

**改善前**:
```
社会需求（Social）: 60%
尊重需求（Esteem）: 25%
生理需求（Physiological）: 10%  ← 偏少
其他: 5%
```

**改善后**（预期）:
```
社会需求（Social）: 45%
尊重需求（Esteem）: 20%
生理需求（Physiological）: 30%  ← 显著提升
其他: 5%
```

### 二阶Desire覆盖

**新增场景**:
- ✅ 意志力斗争（戒烟、减肥、起床）
- ✅ 欲望冲突（社交认可 vs 生理舒适）
- ✅ 渐变状态（从专注到疲惫）
- ✅ 本能反应（惊吓、疼痛、失败）

### 推理难度提升

**一阶Desire（直接）**:
```
视频: 一个人在吃饭
问题: 这个人想做什么？
答案: 吃饭（显而易见）
推理层级: 1层
```

**二阶Desire（深度）**:
```
视频: "Try not to eat challenge"，手伸向食物又缩回
问题: 这个人为什么犹豫？
答案:
  - 一阶: 想吃食物（生理饥饿）
  - 二阶: 想要完成挑战（社交认可、自我控制）
  - 冲突: 饥饿 vs 意志力
推理层级: 3层
```

---

## 🔍 质量控制

### AI审核重点

内容筛选器（`content_filter.py`）会重点检查：

1. **生理反应可见性**
   - 颤抖、出汗、瞳孔变化
   - 面部表情（痛苦、疲惫、渴望）
   - 肢体语言（蜷缩、逃避、急切）

2. **情境真实性**
   - 非表演、非科普讲解
   - 真实的生理压力场景
   - 可观察的欲望表达

3. **推理价值**
   - 欲望非直接表达（需要推理）
   - 包含冲突或渐变过程
   - 视觉线索丰富

### 人工审核标准

在 `annotation_reviewer_v3.py` 中审核时，重点关注：

✅ **批准标准**:
- 清晰的生理需求表现
- 可观察的欲望冲突
- 视觉特征符合预期（颤抖、出汗、打哈欠等）
- 无字幕遮挡关键区域

❌ **拒绝标准**:
- 纯表演性质（无真实生理压力）
- 科普讲解视频（非行为展示）
- 硬字幕/动画/reaction视频
- 无法推断欲望（视觉线索不足）

---

## 📊 预估数据量

### 关键词数量

| 关键词集 | 数量 | 预估视频数（@5视频/关键词） |
|---------|------|---------------------------|
| **physiological** | 41个 | 205个 |
| **second_order** | 36个 | 180个 |
| **desire_extended** | 77个 | 385个 |

### 审核通过率预估

根据历史数据：
- **严格模式**: 30-40% 通过率
- **标准模式**: 50-60% 通过率

**预期最终数据**（严格模式）:
```
搜索: 385个
下载: ~350个（去重、评分筛选）
审核通过: ~120-140个（35%通过率）
人工审核通过: ~100-120个（人工再筛选）
```

---

## 🛠 故障排除

### 问题1: 搜索到的视频与预期不符

**解决**:
- 调整关键词措辞（如"ice bath challenge"改为"ice bath reaction"）
- 增加过滤条件（时长、观看量）
- 使用自定义关键词组合

### 问题2: AI审核通过率太低

**解决**:
```python
# 在 search_config.py 中调整
STRICT_MODE = False  # 改为标准模式
MIN_DURATION = 20    # 降低时长要求
MAX_DURATION = 600   # 提高时长上限（长视频更有价值）
```

### 问题3: 生理特征不明显

**解决**:
- 优先选择"challenge"类视频（如ice bath, holding breath）
- 避免vlog类（生理特征可能不明显）
- 使用"extreme"、"fail"等强化词

---

## 📝 更新日志

### 2025-12-14
- ✅ 新增 `KEYWORDS_PHYSIOLOGICAL`（41个关键词）
- ✅ 新增 `KEYWORDS_SECOND_ORDER`（36个关键词）
- ✅ 新增 `KEYWORDS_DESIRE_EXTENDED`（组合版，77个）
- ✅ 更新 `search_config.py` 支持新关键词集
- ✅ 创建使用指南文档

---

## 🔗 相关资源

- **配置文件**: [config/search_config.py](../config/search_config.py)
- **搜索脚本**: [scripts/run_search.py](../scripts/run_search.py)
- **下载审核**: [scripts/run_download_review.py](../scripts/run_download_review.py)
- **审核平台**: [frontend/annotation_reviewer_v3.py](../frontend/annotation_reviewer_v3.py)
- **项目架构**: [PROJECT_ARCHITECTURE.md](../PROJECT_ARCHITECTURE.md)

---

## 💬 反馈与改进

如果在使用过程中发现：
- 某些关键词效果特别好/差
- 新的情境化关键词思路
- AI审核误判案例

请记录并反馈，我们会持续优化关键词策略。

---

**祝数据收集顺利！🎉**
