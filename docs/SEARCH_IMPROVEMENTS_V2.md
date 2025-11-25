# 搜索系统改进 V2 - 智能去重和历史管理

## 📋 改进概览

本次改进解决了以下核心问题：
1. ✅ 搜索数量不足问题（确保搜索到足够的新视频）
2. ✅ 缺少搜索历史记录（防止重复搜索相同视频）
3. ✅ 搜索结果管理混乱（添加时间戳和归档）
4. ✅ 下载审核流程优化（跳过已处理视频）

---

## 🎯 核心功能

### 1. 搜索历史管理系统

#### 新增文件：`data/searched_history.json`

**用途**：记录所有搜索过的视频URL，防止重复搜索

**数据结构**：
```json
{
  "searched_urls": {
    "https://www.youtube.com/watch?v=xxxxx": {
      "title": "视频标题",
      "channel": "频道名称",
      "duration": 120,
      "first_seen": "2025-11-25T10:30:00",
      "keyword": "emotional reaction"
    }
  },
  "metadata": {
    "total_searched": 1234,
    "last_updated": "2025-11-25T10:30:00"
  }
}
```

**自动管理**：
- 每次搜索时自动记录新视频
- 搜索时自动跳过已记录的URL
- 永久保留，避免重复搜索

---

### 2. 改进的搜索逻辑

#### 旧版本问题：
```python
# 旧版：搜索 limit * 3 个结果，如果很多已存在，最终可能只得到很少的新视频
search_query = f"ytsearch{limit * 3}:{keyword}"
for entry in entries:
    if len(links) >= limit:
        break  # 达到limit就停止，可能实际找到的新视频很少
```

#### 新版本改进：
```python
# 新版：动态扩大搜索范围，直到找到足够的新视频
for search_attempt in range(max_search_attempts):
    if len(links) >= limit:
        break

    # 动态增加搜索数量
    search_count = limit * search_multiplier

    # 跳过已搜索过的视频
    if video_url in searched_urls:
        skipped_searched += 1
        continue

    # 立即添加到搜索历史
    self.add_to_search_history(video_info, keyword)

    # 如果本次没找到足够视频，增加下次搜索范围
    if len(links) < limit:
        search_multiplier += 2
```

**关键改进**：
- ✅ 确保搜索到 `limit` 个**新视频**（未在历史中的）
- ✅ 动态扩大搜索范围（3x → 5x → 7x...）
- ✅ 最多尝试 5 次搜索
- ✅ 实时统计跳过数量

---

### 3. 搜索结果文件改进

#### 新增格式：带元数据的搜索结果

**文件**：`data/search_results.json`

**旧格式**（数组）：
```json
[
  {"url": "...", "title": "..."},
  {"url": "...", "title": "..."}
]
```

**新格式**（带元数据）：
```json
{
  "search_time": "2025-11-25T10:30:00",
  "total_videos": 60,
  "videos": [
    {"url": "...", "title": "...", "pre_score": 0.85},
    {"url": "...", "title": "...", "pre_score": 0.72}
  ],
  "statistics": {
    "total_searched": 100,
    "after_dedup": 80,
    "after_scoring": 60,
    "skipped_by_score": 20
  }
}
```

**优势**：
- 📊 记录搜索时间和统计信息
- 📦 自动保存带时间戳的归档副本
- 🔄 下载脚本兼容新旧格式

---

### 4. 下载审核流程优化

#### 改进的跳过逻辑

**旧版**：只检查 `youtube_links.json`
```python
# 只跳过已下载/审核过的视频
existing_urls = {v["url"] for v in downloader.links_db["videos"]}
```

**新版**：兼容新搜索结果格式
```python
# 自动识别新旧格式
if isinstance(data, list):
    videos = data  # 旧格式
elif isinstance(data, dict) and "videos" in data:
    videos = data["videos"]  # 新格式
    # 显示统计信息
```

---

## 🔄 工作流程

### 完整流程（推荐）

```bash
# 1. 搜索视频（只搜索，不下载）
python scripts/run_search.py --search-only

# 输出：
# ✅ data/search_results.json          # 本轮搜索结果
# ✅ data/searched_history.json        # 累积搜索历史
# ✅ data/search_results_20251125_103000.json  # 归档副本

# 2. 下载和审核（使用搜索结果）
python scripts/run_download_review.py

# 自动跳过：
# - 已在 youtube_links.json 中的视频（已下载/审核）
# - 已存在的视频文件
```

### 分批处理

```bash
# 下载前 20 个高分视频
python scripts/run_download_review.py --limit 20

# 从第 21 个开始继续
python scripts/run_download_review.py --start 20 --limit 20
```

---

## 📊 数据文件说明

| 文件 | 用途 | 更新时机 | 持久性 |
|------|------|----------|--------|
| `searched_history.json` | 搜索历史（所有搜索过的URL） | 每次搜索 | 永久保留 |
| `search_results.json` | 最新一轮搜索结果 | 每次搜索 | 每轮覆盖 |
| `search_results_YYYYMMDD_HHMMSS.json` | 搜索结果归档 | 每次搜索 | 永久保留 |
| `youtube_links.json` | 下载和审核记录 | 下载/审核 | 永久保留 |

---

## 🎨 搜索输出示例

### 改进前：
```
🔍 正在搜索: emotional reaction (目标: 10 个)
✅ 搜索完成，筛选出 3 个视频
```
❌ 问题：很多视频已存在，实际只找到 3 个新视频

### 改进后：
```
🔍 正在搜索: emotional reaction (目标: 10 个新视频)
  🔄 搜索尝试 1/5: 请求 30 个结果
✅ 搜索完成: 找到 10 个新视频
   ⏭️  跳过 15 个已搜索过的视频
```
✅ 确保找到 10 个新视频！

---

## 🔧 新增配置参数

### VideoDownloader 初始化

```python
downloader = VideoDownloader(
    output_dir="data/Youtube_videos",
    links_file="data/youtube_links.json",
    search_history_file="data/searched_history.json"  # 新增！
)
```

### search_videos 方法

```python
videos = downloader.search_videos(
    keyword="emotional reaction",
    limit=10,
    min_duration=30,
    max_duration=300,
    skip_searched=True  # 新增！是否跳过搜索历史中的视频
)
```

---

## 🚀 使用建议

### 1️⃣ 首次使用
```bash
# 删除旧的搜索结果（可选）
rm data/search_results.json

# 执行新的搜索
python scripts/run_search.py --search-only
```

### 2️⃣ 持续采集
```bash
# 每天搜索一次，系统会自动跳过已搜索的视频
python scripts/run_search.py --search-only

# 下载新搜索到的视频
python scripts/run_download_review.py
```

### 3️⃣ 清理搜索历史
如果想要重新搜索（例如YouTube更新了排序算法）：
```bash
# 备份旧历史
mv data/searched_history.json data/searched_history_backup.json

# 重新搜索
python scripts/run_search.py --search-only
```

---

## 📈 性能提升

### 搜索效率
- ✅ 避免重复搜索相同视频
- ✅ 确保每次搜索都能找到足够的新视频
- ✅ 动态调整搜索范围，减少API请求

### 存储优化
- ✅ 搜索历史只记录URL和基本信息（轻量级）
- ✅ 归档文件按日期保存，便于追溯
- ✅ 自动去重，避免重复下载

### 成本节省
- 💰 减少重复搜索API调用
- 💰 避免重复下载相同视频
- 💰 智能评分预筛选，节省AI审核成本

---

## ⚠️ 注意事项

1. **搜索历史持久性**
   - `searched_history.json` 会永久保留
   - 如需重置，手动删除该文件

2. **归档文件管理**
   - 每次搜索都会生成归档文件
   - 定期清理旧归档以节省空间

3. **兼容性**
   - 下载脚本兼容新旧搜索结果格式
   - 可以无缝升级，无需修改现有数据

4. **搜索数量保证**
   - 系统尽力搜索到 `limit` 个新视频
   - 如果关键词相关视频太少，可能达不到目标
   - 会有警告提示

---

## 🐛 故障排除

### 问题：搜索不到新视频
**原因**：所有相关视频都已在搜索历史中
**解决**：
1. 更换关键词
2. 或清空搜索历史重新搜索

### 问题：搜索结果格式错误
**原因**：使用了旧版本脚本
**解决**：下载脚本已自动兼容新旧格式

### 问题：搜索速度慢
**原因**：动态扩大搜索范围需要多次请求
**解决**：这是为了确保找到足够新视频的代价，可以通过增加关键词多样性来缓解

---

## 📝 更新日志

### V2.0 (2025-11-25)
- ✅ 添加搜索历史管理系统
- ✅ 改进搜索逻辑，确保找到足够新视频
- ✅ 搜索结果添加元数据和时间戳
- ✅ 自动保存归档副本
- ✅ 下载脚本兼容新旧格式

### V1.0 (之前)
- 基础搜索和下载功能
- AI智能评分预筛选
- 批量下载和审核

---

## 🎉 总结

通过本次改进，搜索系统现在能够：

1. **确保搜索质量**：每次搜索都能找到足够数量的新视频
2. **避免重复工作**：自动记录和跳过已搜索的视频
3. **追溯性更强**：保留完整的搜索历史和归档
4. **成本更低**：减少重复搜索和下载

**推荐使用模式**：
```bash
# 每天运行一次搜索
python scripts/run_search.py --search-only

# 然后下载和审核新视频
python scripts/run_download_review.py
```

这样可以持续积累高质量的视频数据集，同时避免重复和浪费！
