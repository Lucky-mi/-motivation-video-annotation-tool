# 视频审核错误处理指南

## 🔍 问题诊断

当AI审核出现 `'\n  "pass"'` 错误时，说明JSON解析失败。我已经添加了详细的调试日志。

## 📋 修复内容

### 1. 增强错误日志 (`backend/content_filter.py`)

现在会显示：
- AI响应长度
- JSON提取方式（直接JSON、```json代码块、```代码块）
- 提取后的前150字符
- **完整的AI响应内容**（如果解析失败）

### 2. 创建重新审核工具 (`scripts/retry_review.py`)

专门用于重新审核 `ai_check_errors` 目录中的视频。

### 3. 改进 `run_download_review.py`

- 自动跳过数据库中已有的视频（包括在ai_check_errors中的）
- 提示ai_check_errors中有多少待审核视频

## 🚀 使用方法

### 第一步：诊断AI审核问题

再次运行下载审核，**这次会输出完整的AI响应**：

```bash
python scripts/run_download_review.py
```

**新的日志会显示**：
```
🛡️ AI Auditing (physiological_desire): xxx.mp4 ...
📝 AI Response length: 450 chars
   ✓ Direct JSON detected
   ✓ Extracted 420 chars, first 150: {"pass":true,...

如果解析失败：
❌ JSON解析失败!
   异常类型: JSONDecodeError
   异常消息: Expecting value: line 1 column 1 (char 0)
   === 完整AI响应 ===
   [这里会显示AI返回的完整内容]
   === 响应结束 ===
```

**请把这个完整的AI响应发给我**，这样我就能看到问题所在。

### 第二步：重新审核失败的视频

当AI配置修复后（或想重试），使用重新审核工具：

```bash
# 重新审核所有ai_check_errors中的视频
python scripts/retry_review.py

# 只审核前10个
python scripts/retry_review.py --max-count 10
```

**工作流程**：
1. 从 `data/ai_check_errors/` 读取所有 .mp4 文件
2. 重新进行AI审核
3. **通过的视频** → 移动到 `data/Youtube_videos/`
4. **拒绝的视频** → 删除（如果 AUTO_DELETE_REJECTED=True）或保留
5. **仍然出错的** → 继续保留在 `ai_check_errors/`

### 第三步：继续下载新视频

`run_download_review.py` 会自动跳过已下载的视频：

```bash
# 会跳过数据库中已有的URL（包括在ai_check_errors中的）
python scripts/run_download_review.py --input data/search_results.json
```

## 📁 目录结构

```
data/
├── Youtube_videos/          # ✅ 审核通过的视频
├── ai_check_errors/         # ⚠️ AI审核出错的视频（待重新审核）
├── youtube_links.json       # 📊 所有视频的元数据库
└── search_results.json      # 🔍 搜索结果
```

## 🔧 可能的AI审核错误原因

1. **Gemini API配置问题**
   - API密钥过期
   - 配额不足
   - 网络问题

2. **JSON格式问题**
   - prompt没有正确要求JSON格式
   - AI返回了markdown解释而非纯JSON
   - response_mime_type设置有问题

3. **视频处理问题**
   - 视频格式不支持
   - 视频太大或太长
   - 视频上传失败

## 💡 下一步

1. **运行 `run_download_review.py`**，查看新的详细日志
2. **把完整的AI响应发给我**（从"=== 完整AI响应 ===" 到 "=== 响应结束 ==="）
3. 我根据实际响应内容修复JSON解析逻辑
4. 修复后，使用 `retry_review.py` 重新审核失败的视频

## ⚙️ 配置

确保 `config/search_config.py` 中设置了：

```python
FILTER_MODE = "physiological_desire"  # 使用生理需求审核模式
STRICT_MODE = False                    # 推荐使用False
AUTO_DELETE_REJECTED = True            # 是否自动删除拒绝的视频
AI_REVIEW_WORKERS = 5                  # 并发审核数量
```

## 🎯 预期结果

修复后，AI审核应该显示：

```
🛡️ AI Auditing (physiological_desire): xxx.mp4 ...
📝 AI Response length: 450 chars
   ✓ Direct JSON detected
   ✓ Extracted 420 chars, first 150: {"pass":true,"category":"physiological_hunger",...
🎯 Audit Result: ✅ [physiological_hunger] - Observable eating behavior after fasting
```
