# YouTube 防封禁完整指南

## 🚨 问题症状

```
ERROR: [youtube] Sign in to confirm you're not a bot.
Use --cookies-from-browser or --cookies for the authentication.
```

## ✅ 解决方案（按优先级）

### 方案 1: 更新 Cookies（最有效）⭐

YouTube 的 cookies 会过期，需要定期更新。

#### 步骤：

1. **安装浏览器扩展**
   - **Chrome/Edge**: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - **Firefox**: [cookies.txt](https://addons.mozilla.org/firefox/addon/cookies-txt/)

2. **导出 Cookies**
   ```
   1. 在浏览器中访问 https://youtube.com
   2. 确保已登录你的 Google 账号
   3. 点击扩展图标
   4. 选择 "Export" 或 "导出"
   5. 保存为 cookies.txt
   ```

3. **替换文件**
   ```bash
   # 将下载的 cookies.txt 复制到项目根目录
   cp ~/Downloads/cookies.txt ./cookies.txt
   ```

4. **验证 Cookies**
   ```bash
   python scripts/fix_youtube_ban.py
   ```

### 方案 2: 降低请求频率

修改 `config/search_config.py`:

```python
# 保守配置（推荐）
VIDEOS_PER_KEYWORD = 3  # 每个关键词只搜索3个
AI_REVIEW_WORKERS = 1   # 串行下载，避免并发

# 中等配置
VIDEOS_PER_KEYWORD = 5
AI_REVIEW_WORKERS = 1

# 激进配置（容易被限制）
VIDEOS_PER_KEYWORD = 10
AI_REVIEW_WORKERS = 3
```

### 方案 3: 使用代理

如果有代理/VPN，可以分散请求：

```python
# 在脚本中使用代理
from backend.downloader import VideoDownloader

# HTTP 代理
dl = VideoDownloader(proxy='http://127.0.0.1:7890')

# SOCKS5 代理
dl = VideoDownloader(proxy='socks5://127.0.0.1:1080')
```

或者使用命令行：

```bash
python scripts/safe_download.py --proxy http://127.0.0.1:7890
```

### 方案 4: 使用安全下载脚本

我们提供了带速率限制的安全下载脚本：

```bash
# 保守模式（3个关键词，每个3个视频，间隔10秒）
python scripts/safe_download.py --keywords 3 --per-keyword 3 --delay 10

# 标准模式
python scripts/safe_download.py --keywords 5 --per-keyword 5 --delay 5

# 带代理
python scripts/safe_download.py --keywords 5 --per-keyword 5 --proxy http://127.0.0.1:7890
```

### 方案 5: 等待冷却期

如果已经被限制：

1. **短期限制**（1-2小时）
   - 等待 30 分钟 - 2 小时
   - 期间不要访问 YouTube

2. **中期限制**（几小时）
   - 更换 IP（重启路由器）
   - 使用移动热点
   - 使用 VPN

3. **长期限制**（24小时+）
   - 更换 Google 账号
   - 使用不同的 cookies
   - 联系 YouTube 支持

## 🔍 诊断工具

运行诊断脚本检查状态：

```bash
python scripts/fix_youtube_ban.py
```

输出示例：

```
============================================================
📊 诊断结果
============================================================
Cookies 状态: ✅ 正常
网络状态: ✅ 正常
YouTube 访问: ✅ 正常
```

## 💡 最佳实践

### 1. 定期更新 Cookies

```bash
# 建议每周更新一次
# 添加到定时任务或手动执行
```

### 2. 合理设置请求间隔

```python
# 推荐配置
request_delay = (2, 5)  # 每个请求间隔 2-5 秒（随机）
```

### 3. 避免高峰期

```
避免的时间段（UTC）:
- 12:00-14:00（亚洲高峰）
- 18:00-22:00（欧美高峰）

推荐时间段：
- 02:00-08:00（亚洲深夜）
- 14:00-18:00（欧美上午）
```

### 4. 分批次下载

```bash
# 不要一次性下载大量视频
# 建议：每批 10-20 个，间隔 1 小时

# 第一批
python scripts/safe_download.py --keywords 3 --per-keyword 3

# 等待 1 小时

# 第二批
python scripts/safe_download.py --keywords 3 --per-keyword 3
```

## 🔧 代码改进

### 已添加的防封禁措施

1. **真实浏览器 User-Agent**
   ```python
   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...'
   ```

2. **代理支持**
   ```python
   VideoDownloader(proxy='http://127.0.0.1:7890')
   ```

3. **自适应速率限制**
   - 检测到限制后自动减速
   - 指数退避策略

4. **Cookies 状态检查**
   - 自动检测 cookies 是否存在
   - 提示更新过期 cookies

## 📋 常见问题

### Q: Cookies 多久需要更新一次？

**A**: 建议每 7-14 天更新一次。如果频繁下载，建议每 3-5 天更新。

### Q: 已经被限制了怎么办？

**A**:
1. 立即停止所有请求
2. 等待 30 分钟
3. 更新 cookies
4. 更换 IP（如果可能）
5. 降低并发数和搜索频率

### Q: 使用代理会不会更容易被检测？

**A**: 不会。优质的住宅代理反而能降低被检测的风险。避免使用：
- 数据中心 IP
- 免费代理
- 已被滥用的代理池

### Q: 可以用多个账号吗？

**A**: 可以。准备 2-3 个 Google 账号轮换使用：
```bash
# 使用不同的 cookies 文件
cp cookies_account1.txt cookies.txt  # 账号1
python scripts/safe_download.py

cp cookies_account2.txt cookies.txt  # 账号2
python scripts/safe_download.py
```

## 🚀 高级技巧

### 1. 使用 Cookie 池

```python
import random
from pathlib import Path

cookie_files = list(Path('cookies_pool/').glob('*.txt'))
cookie_file = random.choice(cookie_files)

dl = VideoDownloader()
dl.cookies_path = cookie_file
```

### 2. IP 轮换

```python
proxy_pool = [
    'http://proxy1:8080',
    'http://proxy2:8080',
    'http://proxy3:8080',
]

proxy = random.choice(proxy_pool)
dl = VideoDownloader(proxy=proxy)
```

### 3. 监控限流状态

```bash
# 查看日志中的限流信息
grep -i "rate" logs/download.log
grep -i "限制" logs/download.log
```

## 📞 需要帮助？

如果以上方法都无效：

1. 运行诊断工具并保存输出
   ```bash
   python scripts/fix_youtube_ban.py > diagnosis.txt
   ```

2. 检查日志文件
   ```bash
   tail -n 100 logs/download.log
   ```

3. 提供以下信息：
   - 诊断输出
   - 错误日志
   - Cookies 最后更新时间
   - 使用的关键词数量和频率

## 🎯 总结

**最有效的防封禁策略：**

1. ✅ **定期更新 Cookies**（每周一次）
2. ✅ **降低请求频率**（3-5个视频/关键词）
3. ✅ **使用代理轮换**（如果可能）
4. ✅ **分批次下载**（每批10-20个）
5. ✅ **避开高峰期**（深夜或清晨）

**记住：慢即是快。耐心下载总比被长期封禁好！**
