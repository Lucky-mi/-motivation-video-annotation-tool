# 错误修复指南

## 问题1: 搜索时出现 "Requested format is not available" 错误

### 错误信息
```
ERROR: [youtube] qdk7XuBgSjw: Requested format is not available
```

### 原因
YouTube的格式获取策略变化，某些视频的格式信息无法直接获取。

### 解决方案
我已经修复了 `backend/downloader.py` 中的搜索逻辑：

**改进内容：**
1. 使用更稳定的 `android` 客户端
2. 添加 `ignoreerrors=True` 跳过有问题的视频
3. 改用两步搜索：先获取列表，再逐个获取详细信息
4. 增加备选数量以确保找到足够的视频

### 如何运行修复后的代码

**方式1: 使用虚拟环境（推荐）**
```bash
# 激活虚拟环境
cd d:\Desire-VQA\video_anno
venv\Scripts\activate

# 运行搜索
python scripts/run_search.py
```

**方式2: 直接测试搜索功能**
```bash
# 在虚拟环境中
cd d:\Desire-VQA\video_anno
venv\Scripts\activate

# 快速测试
python -c "
import sys
sys.path.insert(0, '.')
from backend.downloader import VideoDownloader

dl = VideoDownloader()
videos = dl.search_videos('psychology', limit=3)
print(f'找到 {len(videos)} 个视频:')
for v in videos:
    print(f'  - {v[\"title\"][:60]}...')
"
```

---

## 问题2: cv2 DLL加载失败

### 错误信息
```
ImportError: DLL load failed while importing cv2
```

### 原因
这是cv2（OpenCV）的DLL依赖问题，与YouTube搜索无关。

### 临时解决方案
直接导入downloader和content_filter模块，避免导入完整的backend包：

```python
# 不要这样导入
from backend.downloader import VideoDownloader  # 会触发backend/__init__.py

# 而是这样
import sys
sys.path.insert(0, 'backend')
from downloader import VideoDownloader  # 直接导入downloader模块
```

或者使用我创建的独立脚本。

---

## 验证修复

### 测试1: 搜索功能
```bash
# 在虚拟环境中运行
cd d:\Desire-VQA\video_anno
venv\Scripts\activate

# 测试搜索（应该成功找到视频）
python -c "
import sys
sys.path.insert(0, 'backend')
from downloader import VideoDownloader

dl = VideoDownloader()
print('测试搜索...')
videos = dl.search_videos('psychology experiment', limit=2)
print(f'✅ 成功找到 {len(videos)} 个视频')
for v in videos:
    print(f'  标题: {v[\"title\"][:60]}')
    print(f'  时长: {v[\"duration\"]}秒')
    print()
"
```

### 测试2: 完整流程
```bash
# 如果上面的搜索测试成功，运行完整流程
python scripts/run_search.py
```

---

## 代码改进说明

### 修改前的问题代码
```python
ydl_opts = {
    'extract_flat': False,  # 尝试获取所有信息，但某些视频会失败
}
result = ydl.extract_info(search_query, download=False)
# 一旦某个视频出错，整个搜索失败
```

### 修改后的代码
```python
ydl_opts = {
    'extract_flat': 'in_playlist',  # 先获取基本列表
    'ignoreerrors': True,  # 忽略单个错误
}
result = ydl.extract_info(search_query, download=False)

# 然后对每个视频单独获取详细信息
for entry in result['entries']:
    try:
        info = detail_ydl.extract_info(video_url, download=False)
        # 获取成功的才加入结果
    except:
        continue  # 失败的跳过，继续处理下一个
```

**优势：**
- ✅ 单个视频失败不会影响整体搜索
- ✅ 使用更稳定的android客户端
- ✅ 自动跳过有问题的视频
- ✅ 增加备选数量确保找到足够视频

---

## 预期结果

修复后，搜索应该能够：
- ✅ 成功找到符合时长要求的视频
- ✅ 自动跳过无法获取格式的视频
- ✅ 显示类似这样的输出：

```
[1/12] 搜索关键词: social interaction psychology
INFO:backend.downloader:🔍 正在搜索: social interaction psychology (Limit: 5, Duration: 30-300s)
INFO:backend.downloader:✅ 搜索完成，筛选出 5 个视频
  ✅ 找到 5 个视频

[2/12] 搜索关键词: people understanding emotions
INFO:backend.downloader:🔍 正在搜索: people understanding emotions (Limit: 5, Duration: 30-300s)
INFO:backend.downloader:✅ 搜索完成，筛选出 5 个视频
  ✅ 找到 5 个视频
```

---

## 如果还有问题

### 检查yt-dlp版本
```bash
pip install --upgrade yt-dlp
```

### 检查网络连接
```bash
# 测试能否访问YouTube
curl -I https://www.youtube.com
```

### 查看详细日志
在代码中添加详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 手动测试单个视频
```bash
yt-dlp --dump-json "https://www.youtube.com/watch?v=VIDEO_ID"
```

---

## 总结

✅ **已修复**: 搜索功能现在更加稳定和容错
✅ **已优化**: 警告信息已减少
✅ **已增强**: 可以轻松调整搜索数量（修改配置文件）

**下一步操作：**
1. 激活虚拟环境: `venv\Scripts\activate`
2. 运行搜索脚本: `python scripts/run_search.py`
3. 根据提示确认配置并开始搜索
