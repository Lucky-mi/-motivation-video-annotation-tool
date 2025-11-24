# 📹 视频审核指南

## 🎯 概述

本指南说明如何使用独立审核脚本 `review_videos.py` 对已下载的视频进行AI审核。

---

## 🚀 快速使用

### 基础命令

```bash
# 激活虚拟环境
cd d:\Desire-VQA\video_anno
.\venv\Scripts\activate

# 使用标准模式审核所有已下载视频（推荐）
python scripts/review_videos.py --mode standard
```

---

## 📖 命令详解

### 完整命令格式

```bash
python scripts/review_videos.py [选项]
```

### 可用选项

| 选项 | 说明 | 默认值 | 示例 |
|-----|------|--------|------|
| `--mode` | 审核模式 | `standard` | `--mode strict` |
| `--delete-rejected` | 自动删除未通过的视频 | 否 | `--delete-rejected` |
| `--video-dir` | 视频目录路径 | `data/Youtube_videos` | `--video-dir data/test_videos` |

---

## 💡 常用场景

### 场景1: 标准审核（推荐）

```bash
# 使用标准模式审核，不删除未通过的视频
python scripts/review_videos.py --mode standard
```

**适用于：**
- 首次审核，想要保留所有视频
- 需要较高通过率（50-70%）
- 后续可能手动检查未通过的视频

### 场景2: 严格审核

```bash
# 使用严格模式审核
python scripts/review_videos.py --mode strict
```

**适用于：**
- 需要高质量样本
- 对视频质量要求严格
- 预期通过率30-50%

### 场景3: 审核并自动清理

```bash
# 标准模式审核，自动删除未通过的视频
python scripts/review_videos.py --mode standard --delete-rejected
```

**适用于：**
- 磁盘空间有限
- 只需要通过审核的视频
- 不需要手动检查未通过的视频

### 场景4: 严格审核并清理

```bash
# 严格模式审核，自动删除未通过的视频
python scripts/review_videos.py --mode strict --delete-rejected
```

**适用于：**
- 需要最高质量样本
- 愿意牺牲数量换取质量
- 不需要保留未通过的视频

### 场景5: 指定目录审核

```bash
# 审核特定目录下的视频
python scripts/review_videos.py --mode standard --video-dir data/test_videos
```

**适用于：**
- 有多个视频目录
- 测试新下载的视频
- 分批审核

---

## 📊 输出示例

### 运行开始

```
================================================================================
📹 视频审核脚本
================================================================================
审核模式: 标准
视频目录: data/Youtube_videos
自动删除未通过: 否
================================================================================

找到 68 个视频文件

📦 初始化AI审核器...

================================================================================
🤖 开始AI审核
================================================================================
```

### 审核过程

```
[1/68] abc123.mp4
  ✅ 通过 | 包含两人对话，情感表达明确，适合心智理论研究
     置信度: 0.85
     分析价值: 高

[2/68] def456.mp4
  ❌ 拒绝 | 视频主要是游戏画面，不包含真实人类互动

[3/68] ghi789.mp4
  ✅ 通过 | 展示了一家人的日常互动，有清晰的情感交流
     置信度: 0.78
     分析价值: 中等
```

### 最终统计

```
================================================================================
💾 保存审核报告
================================================================================
✅ 报告已保存: reports/review_report_20251124_143022.json

================================================================================
📊 审核统计
================================================================================
总视频数: 68
通过: 42 (61.8%)
拒绝: 24 (35.3%)
失败: 2

📈 通过视频的分类统计:
  社交互动: 25个
  情感表达: 12个
  对话场景: 5个

================================================================================
🎉 审核完成!
================================================================================
```

---

## 📁 输出文件

### 审核报告

**位置：** `reports/review_report_YYYYMMDD_HHMMSS.json`

**格式：**

```json
{
  "reviewed_time": "2025-11-24T14:30:22",
  "mode": "standard",
  "total_videos": 68,
  "approved": 42,
  "rejected": 24,
  "failed": 2,
  "results": [
    {
      "video_path": "data/Youtube_videos/abc123.mp4",
      "video_name": "abc123.mp4",
      "approved": true,
      "review_result": {
        "pass": true,
        "reason": "包含两人对话，情感表达明确",
        "confidence": 0.85,
        "类别": "社交互动",
        "互动类型": "对话",
        "分析价值": "高",
        "情感强度": "中等"
      },
      "reviewed_time": "2025-11-24T14:30:25"
    }
  ]
}
```

---

## 🔍 审核模式对比

### 标准模式 vs 严格模式

| 维度 | 标准模式 | 严格模式 |
|-----|---------|---------|
| **通过标准** | 大部分要求达标 | 所有要求必须达标 |
| **预期通过率** | 50-70% | 30-50% |
| **适用场景** | 需要数量和多样性 | 需要高质量样本 |
| **真实人类** | 必须 | 必须 |
| **社交互动** | 建议有 | 必须有 |
| **可分析情境** | 建议清晰 | 必须清晰 |
| **视频质量** | 中等即可 | 必须高质量 |

### 审核标准详解

**标准模式要求：**
- ⭐⭐⭐ 真实人类出现（必须）
- ⭐⭐⭐ 社交互动或心理活动（建议）
- ⭐⭐ 可分析的情境（建议）
- ⭐ 视频质量（中等即可）

**严格模式要求：**
- ⭐⭐⭐ 真实人类出现（必须）
- ⭐⭐⭐ 社交互动或心理活动（必须）
- ⭐⭐ 可分析的情境（必须）
- ⭐ 视频质量（必须高质量）

---

## 💡 使用建议

### 建议1: 先标准后严格

```bash
# 第一步：标准模式审核，保留所有视频
python scripts/review_videos.py --mode standard

# 查看通过率和质量
# 检查 reports/review_report_*.json

# 第二步：如果需要更高质量，再用严格模式
python scripts/review_videos.py --mode strict --delete-rejected
```

### 建议2: 分批审核

```bash
# 如果视频很多（>100个），建议分批审核以避免API配额限制

# 方法1: 手动移动视频到不同目录
# 审核第一批
python scripts/review_videos.py --mode standard --video-dir data/batch1

# 审核第二批
python scripts/review_videos.py --mode standard --video-dir data/batch2
```

### 建议3: 查看拒绝原因

```bash
# 运行审核后，查看报告文件
cat reports/review_report_*.json | grep -A 5 '"approved": false'
```

或者在Python中：

```python
import json

# 读取最新报告
with open("reports/review_report_20251124_143022.json") as f:
    report = json.load(f)

# 统计拒绝原因
rejection_reasons = {}
for result in report['results']:
    if not result.get('approved'):
        reason = result['review_result'].get('reason', '未知')
        rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

# 显示
for reason, count in sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True):
    print(f"{reason}: {count}个")
```

---

## 🆘 常见问题

### Q1: 审核失败，提示API错误

**A:** 检查Gemini API密钥和配额

```bash
# 检查.env文件
cat .env | grep GEMINI_API_KEY

# 查看API配额
# 访问：https://aistudio.google.com/
```

### Q2: 所有视频都被拒绝

**A:** 可能是严格模式太严格

```bash
# 切换到标准模式
python scripts/review_videos.py --mode standard
```

### Q3: 审核速度很慢

**A:** 这是正常的，AI审核需要时间

- 单个视频：10-30秒
- 100个视频：约30-60分钟
- 建议：分批审核，避免一次性审核太多

### Q4: 想恢复被删除的视频

**A:** 如果使用了 `--delete-rejected`，被删除的视频无法恢复

**建议：**
1. 首次审核不使用 `--delete-rejected`
2. 检查审核报告确认质量
3. 确认无误后再运行带 `--delete-rejected` 的审核

### Q5: 如何只审核新下载的视频？

**A:** 将新视频放到单独目录

```bash
# 审核新视频
python scripts/review_videos.py --mode standard --video-dir data/new_videos

# 通过的视频手动移动到主目录
# 或使用脚本自动移动通过的视频
```

---

## 🔧 高级用法

### 自动移动通过的视频

```python
# scripts/move_approved_videos.py
import json
import shutil
from pathlib import Path

# 读取审核报告
report_file = "reports/review_report_20251124_143022.json"
with open(report_file) as f:
    report = json.load(f)

# 创建目标目录
approved_dir = Path("data/approved_videos")
rejected_dir = Path("data/rejected_videos")
approved_dir.mkdir(exist_ok=True)
rejected_dir.mkdir(exist_ok=True)

# 移动视频
for result in report['results']:
    video_path = Path(result['video_path'])
    if video_path.exists():
        if result.get('approved'):
            shutil.move(str(video_path), str(approved_dir / video_path.name))
        else:
            shutil.move(str(video_path), str(rejected_dir / video_path.name))

print(f"✅ 视频已分类移动")
```

### 重新审核未通过的视频

```bash
# 如果第一次用严格模式，很多被拒绝
python scripts/review_videos.py --mode strict

# 将未通过的视频移到单独目录，用标准模式重新审核
python scripts/review_videos.py --mode standard --video-dir data/rejected_videos
```

---

## 📞 相关文档

- [完整系统指南](COMPLETE_SYSTEM_GUIDE.md) - 系统全功能说明
- [快速开始](QUICK_START.md) - 搭建和使用
- [电视剧采集指南](TV_DRAMA_GUIDE.md) - 电视剧/电影采集

---

**🎉 开始审核你的视频吧！**

```bash
python scripts/review_videos.py --mode standard
```
