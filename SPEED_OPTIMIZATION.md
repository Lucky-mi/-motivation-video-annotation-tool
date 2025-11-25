# 速度优化指南

## 优化总结

### 1. 延迟优化 ⚡
- **完全移除**搜索时的视频详情延迟（原0.05-0.15秒）
- **大幅减少**请求间延迟：每50个请求才延迟0.5秒（原每5个请求延迟3-6秒）
- **移除**关键词间的延迟

### 2. 跳过已存在视频 🚀
- 下载前检查数据库和文件系统
- 搜索时自动跳过已有URL
- 避免重复下载和重复API调用

### 3. 并发处理 🔥
- 新增并发版本采集脚本：`youtube_collector_concurrent.py`
- 使用线程池并发处理下载和AI审核
- 默认3个并发线程，可调整

### 4. 格式兼容性修复 ✅
- 简化为最宽松的格式选择：`'format': 'best'`
- 移除限制性的编解码器和分辨率要求
- 添加备用下载方法

## 性能对比

### 原版（串行）
```
搜索5个视频：约25-60秒/关键词
下载+审核：约2-3分钟/视频
总耗时（10个视频）：约30-40分钟
```

### 优化后（串行）
```
搜索5个视频：约2-5秒/关键词
下载+审核：约1-2分钟/视频
总耗时（10个视频）：约10-20分钟
速度提升：约2-3倍
```

### 并发版本（推荐）
```
搜索5个视频：约2-5秒/关键词
下载+审核：约30-60秒/视频（3个并发）
总耗时（10个视频）：约3-7分钟
速度提升：约5-10倍
```

## 使用方法

### 方式1: 使用并发版本（最快）
```bash
# 默认配置（3个并发线程）
python scripts/youtube_collector_concurrent.py

# 自定义并发数（建议2-4）
python scripts/youtube_collector_concurrent.py --max-workers 4

# 自定义关键词
python scripts/youtube_collector_concurrent.py --keywords "people crying" "emotional reaction"

# 完整配置
python scripts/youtube_collector_concurrent.py \
    --videos-per-keyword 5 \
    --max-total 50 \
    --max-workers 3 \
    --no-strict
```

### 方式2: 使用原版脚本（已优化）
```bash
# 原版脚本也已经过延迟优化，但仍是串行处理
python scripts/youtube_collector.py --mode full
```

## 并发数建议

- **2个线程**：稳定但较慢，适合网络不稳定的情况
- **3个线程**：推荐配置，速度和稳定性平衡
- **4个线程**：最快速度，可能触发API限制
- **5+个线程**：不推荐，容易被YouTube限制

## 注意事项

1. **API限制**：如果出现大量429错误或被限制，减少并发数
2. **网络稳定性**：并发数过高可能导致网络超时
3. **磁盘IO**：同时写入多个视频文件，确保磁盘性能足够
4. **内存占用**：每个并发线程会占用额外内存

## 监控和调试

查看实时日志：
```bash
# 并发版本会显示每个线程的进度
python scripts/youtube_collector_concurrent.py 2>&1 | tee collection.log
```

检查统计信息：
```bash
# 统计信息保存在
cat data/collection_stats_concurrent.json
```

## 故障排查

### 问题1: 速度仍然很慢
- 检查网络连接
- 减少并发数到2
- 确认没有VPN或代理干扰

### 问题2: 大量下载失败
- 检查cookies.txt是否有效
- 升级yt-dlp：`pip install --upgrade yt-dlp`
- 尝试使用备用格式

### 问题3: AI审核很慢
- 检查Gemini API配额
- 减少并发数避免API限制
- 考虑使用更快的模型

## 进一步优化建议

1. **使用SSD**：加快视频读写速度
2. **配置cookies**：避免年龄限制和登录验证
3. **批量处理**：一次处理多个关键词
4. **定时任务**：在非高峰时段运行
