# 快速开始指南

## 重要提示 ⚠️

**并发脚本现在会使用 `config/search_config.py` 中的配置！**

默认使用 `KEYWORD_SET = "minimal"`（6个实际场景关键词），而不是旧的理论性关键词。

## 1. 查看当前配置

```bash
# 查看当前将使用哪些关键词
python scripts/youtube_collector_concurrent.py --show-config
```

## 2. 修改配置（如果需要）

编辑 [config/search_config.py](config/search_config.py)：

```python
# 选择关键词集合
KEYWORD_SET = "minimal"  # 选项: minimal, standard, extensive, full, tv_drama, mega

# 每个关键词搜索的视频数量
VIDEOS_PER_KEYWORD = 5

# AI并发数
AI_REVIEW_WORKERS = 3
```

### 可用的关键词集合

- **minimal** (6个): 快速测试，最常见场景
  - `people arguing`, `emotional reaction`, `surprise moment` 等

- **standard** (12个): 平衡速度和覆盖
  - 包含冲突、情感、对话、关系等场景

- **extensive** (24个): 更全面的场景覆盖

- **full** (36个): 完整覆盖各类场景

- **tv_drama** (25个): 电视剧片段专用

- **mega** (全部): 所有关键词组合（100+个）

## 3. 运行并发采集（推荐）

```bash
# 使用默认配置（会读取search_config.py）
python scripts/youtube_collector_concurrent.py

# 使用4个并发线程（更快）
python scripts/youtube_collector_concurrent.py --max-workers 4

# 自定义关键词（覆盖配置文件）
python scripts/youtube_collector_concurrent.py --keywords "people crying" "angry moment"

# 每个关键词搜索10个视频
python scripts/youtube_collector_concurrent.py --videos-per-keyword 10
```

## 4. 常见场景

### 快速测试（minimal集合，3个并发）
```bash
# 使用默认配置即可（minimal + 5个/关键词）
python scripts/youtube_collector_concurrent.py
```

### 大规模采集（mega集合，4个并发）
```bash
# 1. 先修改配置文件
# config/search_config.py: KEYWORD_SET = "mega"

# 2. 运行
python scripts/youtube_collector_concurrent.py --max-workers 4 --max-total 500
```

### 只采集电视剧片段
```bash
# 1. 修改配置文件
# config/search_config.py: KEYWORD_SET = "tv_drama"

# 2. 运行
python scripts/youtube_collector_concurrent.py
```

### 自定义关键词快速测试
```bash
python scripts/youtube_collector_concurrent.py \
    --keywords "couple fight" "family argument" \
    --videos-per-keyword 3 \
    --max-workers 2
```

## 5. 性能对比

| 配置 | 关键词数 | 并发数 | 每个关键词 | 预计时间 |
|------|---------|--------|-----------|---------|
| minimal | 6 | 3 | 5 | ~3-5分钟 |
| standard | 12 | 3 | 5 | ~5-10分钟 |
| extensive | 24 | 4 | 5 | ~15-25分钟 |
| mega | 100+ | 4 | 5 | ~1-2小时 |

## 6. 监控和调试

```bash
# 实时查看日志
python scripts/youtube_collector_concurrent.py 2>&1 | tee collection.log

# 查看统计
cat data/collection_stats_concurrent.json

# 查看数据库
python -c "import json; print(json.dumps(json.load(open('data/youtube_links.json')), indent=2))"
```

## 7. 故障排查

### 问题：仍在使用旧的理论性关键词
**解决**：检查 `config/search_config.py` 中的 `KEYWORD_SET` 是否设置为 `"minimal"`

### 问题：速度很慢
**解决**：
1. 增加并发数：`--max-workers 4`
2. 检查网络连接
3. 确认没有触发YouTube限制

### 问题：大量视频下载失败
**解决**：
1. 更新yt-dlp：`pip install --upgrade yt-dlp`
2. 添加cookies.txt文件
3. 减少并发数到2

## 8. 配置文件位置

- **关键词配置**: [config/search_config.py](config/search_config.py)
- **API配置**: [config/config.py](config/config.py)
- **视频数据库**: `data/youtube_links.json`
- **下载目录**: `data/Youtube_videos/`
- **统计信息**: `data/collection_stats_concurrent.json`
