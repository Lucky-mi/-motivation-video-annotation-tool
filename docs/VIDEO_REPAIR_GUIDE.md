# 视频修复指南

## 📋 问题说明

由于之前的bug，部分审核通过的视频没有正确记录文件路径，导致：
- 数据库中有记录
- 但找不到视频文件路径
- 或者路径指向的文件不存在

## 🔧 修复方案

### 方案 1: 自动修复脚本（推荐）

运行修复脚本自动处理：

```bash
python scripts/repair_missing_videos.py
```

**脚本会自动：**
1. 识别所有缺失文件的视频
2. 从数据库中删除这些记录
3. 重新下载这些视频
4. 重新进行AI审核
5. 更新数据库记录（正确记录路径）

**注意**：
- ✅ 自动处理，无需手动操作
- ✅ 会重新审核，可能结果不同
- ⚠️ 需要重新消耗API配额

---

### 方案 2: 手动清理（简单但会丢失记录）

如果只想清理数据库：

```python
import json
from pathlib import Path

# 1. 加载数据库
with open('data/youtube_links.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 2. 过滤掉缺失文件的记录
valid_videos = []
removed_count = 0

for video in data['videos']:
    video_path = video.get('video_path')

    # 保留条件：路径不为空且文件存在
    if video_path and Path(video_path).exists():
        valid_videos.append(video)
    else:
        removed_count += 1
        print(f"删除: {video['title'][:50]}")

# 3. 更新数据库
data['videos'] = valid_videos
data['metadata']['total_count'] = len(valid_videos)

# 4. 保存
with open('data/youtube_links.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n删除了 {removed_count} 条缺失文件的记录")
```

**结果**：
- ✅ 数据库干净了
- ❌ 但丢失了这些视频的URL信息
- ❌ 无法重新下载

---

### 方案 3: 导出URL列表后重新搜索

如果想保留URL但不重新下载：

```python
import json

# 1. 导出缺失视频的URL
with open('data/youtube_links.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

missing_urls = []
for video in data['videos']:
    if video.get('approved') == True:
        video_path = video.get('video_path')
        if not video_path or not Path(video_path).exists():
            missing_urls.append({
                'url': video['url'],
                'title': video['title']
            })

# 2. 保存URL列表
with open('data/missing_videos_urls.json', 'w', encoding='utf-8') as f:
    json.dump(missing_urls, f, ensure_ascii=False, indent=2)

print(f"导出了 {len(missing_urls)} 个缺失视频的URL")
print("保存到: data/missing_videos_urls.json")
```

然后可以：
- 手动浏览这些URL
- 或者添加到自定义关键词重新搜索

---

## 📊 检查当前状态

### 快速检查

```bash
python -c "
import json
from pathlib import Path

data = json.load(open('data/youtube_links.json', 'r', encoding='utf-8'))
approved = [v for v in data['videos'] if v.get('approved') == True]

missing = 0
for v in approved:
    video_path = v.get('video_path')
    if not video_path or not Path(video_path).exists():
        missing += 1

print(f'审核通过的视频: {len(approved)}')
print(f'文件缺失: {missing}')
print(f'文件完整: {len(approved) - missing}')
"
```

### 详细检查

```bash
python -c "
import json
from pathlib import Path

data = json.load(open('data/youtube_links.json', 'r', encoding='utf-8'))

print('审核通过但文件缺失的视频:\n')
for v in data['videos']:
    if v.get('approved') == True:
        video_path = v.get('video_path')
        if not video_path:
            print(f'[路径为空] {v[\"title\"][:60]}')
        elif not Path(video_path).exists():
            print(f'[文件不存在] {v[\"title\"][:60]}')
"
```

---

## ⚠️ 预防措施

### 确保修复生效

修复后，测试新下载的视频：

```bash
# 1. 下载少量新视频测试
python scripts/run_download_review.py --limit 3

# 2. 验证路径是否正确记录
python -c "
import json
from pathlib import Path

data = json.load(open('data/youtube_links.json', 'r', encoding='utf-8'))

# 检查最近3个审核通过的视频
approved = [v for v in data['videos'] if v.get('approved') == True]
recent = approved[-3:]

for v in recent:
    title = v['title'][:50]
    has_path = v.get('video_path') is not None
    file_exists = Path(v.get('video_path', '')).exists() if has_path else False

    status = '✅' if (has_path and file_exists) else '❌'
    print(f'{status} {title}')
    if has_path:
        print(f'   Path: {v[\"video_path\"]}')
        print(f'   Exists: {file_exists}')
"
```

### 定期检查

建议定期运行检查脚本：

```bash
# 创建检查脚本
cat > scripts/check_integrity.sh << 'EOF'
#!/bin/bash
python -c "
import json
from pathlib import Path

data = json.load(open('data/youtube_links.json', 'r', encoding='utf-8'))
approved = [v for v in data['videos'] if v.get('approved') == True]

issues = 0
for v in approved:
    video_path = v.get('video_path')
    if not video_path or not Path(video_path).exists():
        issues += 1

if issues > 0:
    print(f'⚠️ Warning: {issues} approved videos have missing files!')
    exit(1)
else:
    print('✅ All approved videos have valid files')
    exit(0)
"
EOF

chmod +x scripts/check_integrity.sh
```

---

## 🎯 推荐做法

**最简单的方案**：

1. **运行修复脚本**（一次性解决）
   ```bash
   python scripts/repair_missing_videos.py
   ```

2. **验证修复**
   ```bash
   # 检查是否还有缺失
   python -c "import json; from pathlib import Path; data = json.load(open('data/youtube_links.json')); approved = [v for v in data['videos'] if v.get('approved') == True]; missing = sum(1 for v in approved if not v.get('video_path') or not Path(v.get('video_path', '')).exists()); print(f'Still missing: {missing}')"
   ```

3. **继续正常使用**
   ```bash
   python scripts/run_search.py --search-only
   python scripts/run_download_review.py
   ```

之后新下载的视频都会正确记录路径！✅

---

## 💡 常见问题

### Q: 修复脚本会删除我的数据吗？

A: 会临时删除数据库中的缺失记录，但会立即重新下载和添加。最终数据不会丢失（除非重新审核不通过）。

### Q: 我不想重新审核，只想重新下载可以吗？

A: 可以！修改 `config/search_config.py`:
```python
ENABLE_AI_REVIEW = False
```
然后运行修复脚本。

### Q: 修复需要多长时间？

A: 取决于缺失视频的数量：
- 6个视频约需 5-10 分钟（包括下载和审核）
- 每个视频平均 1-2 分钟

### Q: 修复后还会再次出现这个问题吗？

A: 不会！我们已经修复了代码，现在会正确记录 `video_path`。

---

## 📝 总结

| 方案 | 优点 | 缺点 | 推荐度 |
|-----|------|------|-------|
| 修复脚本 | 自动化，数据完整 | 需要时间，消耗API | ⭐⭐⭐⭐⭐ |
| 手动清理 | 快速简单 | 丢失URL信息 | ⭐⭐ |
| 导出URL | 保留信息 | 需要手动操作 | ⭐⭐⭐ |

**推荐使用修复脚本！**一次运行，永久解决。
