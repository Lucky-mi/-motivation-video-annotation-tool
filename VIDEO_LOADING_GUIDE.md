# 视频加载问题诊断指南

## 🎯 问题已修复 (V3版本)

V3版本已经修复了视频加载问题：

### ✅ 修复内容

1. **使用Base64编码**：不再使用 `file://` 协议，改用base64编码嵌入视频
2. **多路径查找**：自动在多个可能的目录中查找视频文件
3. **详细错误提示**：显示具体的错误信息和调试信息

## 🚀 如何使用

### 启动系统

```bash
cd d:\Desire-VQA\video_anno
python run_reviewer.py
```

选择 **选项1 - 完整系统** 或 **选项2 - 仅前端**

### 访问界面

浏览器访问：http://localhost:8502

## 📂 视频文件位置

系统会自动在以下目录查找视频：

1. `d:\Desire-VQA\video_anno\data\Youtube_videos\`
2. `d:\Desire-VQA\video_anno\data\videos\`
3. `D:\Desire-VQA\video_anno\data\Youtube_videos\`
4. `D:\Desire-VQA\video_anno\data\videos\`

### 支持的视频格式

- ✅ `.mp4` (推荐)
- ✅ `.avi`
- ✅ `.mov`
- ✅ `.mkv`
- ✅ `.webm`

## 🔍 如何检查视频是否存在

### 方法1：在系统中查看

1. 选择一个标注文件
2. 如果视频不存在，会显示错误信息
3. 点击 **"🔍 查看所有尝试的路径"** 查看详细信息

### 方法2：手动检查

```bash
# 检查视频目录
dir d:\Desire-VQA\video_anno\data\Youtube_videos\

# 或使用PowerShell
Get-ChildItem "d:\Desire-VQA\video_anno\data\Youtube_videos\" -Filter *.mp4
```

## ⚠️ 常见问题解决

### 问题1：视频文件不存在

**症状**：显示 "❌ 视频文件不存在"

**解决方案**：
1. 检查JSON文件中的 `video_path` 字段
2. 确认视频文件在正确的目录中
3. 确认文件名与 `video_id` 匹配

**示例**：
```json
{
  "video_id": "1.1",
  "video_path": "data\\Youtube_videos\\1.1.mp4"
}
```

视频文件应该在：`d:\Desire-VQA\video_anno\data\Youtube_videos\1.1.mp4`

### 问题2：视频加载很慢

**症状**：视频加载时间很长

**原因**：使用base64编码会增加文件大小约33%

**解决方案**：
1. 等待加载完成（大文件可能需要几秒到几十秒）
2. 考虑压缩视频文件
3. 使用 `.mp4` 格式（最优化）

**视频大小建议**：
- ✅ 优秀：< 20 MB
- ⚠️ 可接受：20-100 MB
- ❌ 较慢：> 100 MB

### 问题3：视频显示空白

**症状**：视频播放器显示，但是空白

**可能原因**：
1. 视频编码格式不支持
2. 浏览器不支持该视频格式
3. 视频文件损坏

**解决方案**：
1. 使用Chrome或Firefox浏览器
2. 检查视频文件是否可以在本地播放器中打开
3. 转换视频为标准MP4格式：
   ```bash
   ffmpeg -i input.mov -c:v libx264 -c:a aac output.mp4
   ```

### 问题4：时间片段不准确

**症状**：视频没有在正确的时间开始/结束

**可能原因**：JSON中的时间戳不准确

**解决方案**：
1. 使用JSON编辑功能修正时间戳
2. 确保 `start_seconds < end_seconds`
3. 时间戳应该在视频总时长范围内

## 🔧 转换视频格式

如果视频格式不兼容，使用ffmpeg转换：

```bash
# 安装ffmpeg（如果未安装）
# 下载：https://ffmpeg.org/download.html

# 转换为标准MP4
ffmpeg -i "input_video.avi" -c:v libx264 -c:a aac -strict experimental "output_video.mp4"

# 批量转换
for %f in (*.avi) do ffmpeg -i "%f" -c:v libx264 -c:a aac "%~nf.mp4"
```

## 📊 视频加载流程

```
1. 读取标注JSON文件
   ↓
2. 获取 video_id 和 video_path
   ↓
3. 在多个目录中查找视频文件
   ↓
4. 读取视频文件为二进制
   ↓
5. 转换为Base64编码
   ↓
6. 嵌入HTML5 video标签
   ↓
7. JavaScript控制播放时间段
   ↓
8. 渲染到浏览器
```

## ✅ 验证清单

在使用前，请确认：

- [ ] 视频文件存在于正确的目录
- [ ] 视频文件可以在本地播放器中播放
- [ ] 视频格式为支持的格式（推荐MP4）
- [ ] JSON文件中的路径正确
- [ ] 使用Chrome或Firefox浏览器
- [ ] Streamlit版本 >= 1.20.0

## 🆘 仍然无法加载？

1. **检查控制台错误**：
   - 打开浏览器开发者工具 (F12)
   - 查看Console标签页
   - 截图错误信息

2. **检查文件权限**：
   ```bash
   # 确保有读取权限
   icacls "d:\Desire-VQA\video_anno\data\Youtube_videos\1.1.mp4"
   ```

3. **尝试简单测试**：
   ```python
   from pathlib import Path
   video_path = Path("d:/Desire-VQA/video_anno/data/Youtube_videos/1.1.mp4")
   print(f"文件存在: {video_path.exists()}")
   print(f"文件大小: {video_path.stat().st_size / (1024*1024):.2f} MB")
   ```

4. **重启服务**：
   - 按 Ctrl+C 停止服务
   - 重新运行 `python run_reviewer.py`

## 📝 反馈

如果问题仍然存在，请提供：
1. 错误截图
2. 浏览器控制台日志
3. 视频文件信息（大小、格式、位置）
4. JSON文件内容片段

---

**祝使用愉快！** 🎉

如有问题，请查看 [REVIEWER_USAGE.md](REVIEWER_USAGE.md) 获取更多帮助。
