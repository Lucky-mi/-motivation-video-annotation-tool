# API Key 统一配置说明

## 🎯 快速开始

**只需要修改一个文件：`.env`**

```bash
# 打开项目根目录下的 .env 文件
# 修改这一行：
GEMINI_API_KEY=你的API密钥
```

就这么简单！所有脚本都会自动读取这个配置。

---

## 📁 配置文件位置

### 主配置文件：`.env`
```
video_anno/
├── .env  ← 在这里修改API Key！
├── annotation.py
├── main.py
└── ...
```

### .env 文件示例
```env
# ============= AI API配置 =============
# Gemini API (Google AI) - 主要使用
GEMINI_API_KEY=AIzaSyDB_ShZ8Ga-bz3VBcSEGMaIIrUqmMfuUc0

# OpenAI API (可选)
# OPENAI_API_KEY=sk-xxxxxxxxxxxxx

# Claude API (可选)
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# ============= 服务端口配置 =============
BACKEND_PORT=8000
FRONTEND_PORT=8502
```

---

## 🔍 配置读取优先级

系统会按以下顺序查找API Key：

1. **环境变量** (`.env` 文件) ← **推荐！**
2. `config/config.yaml` 文件
3. 命令行参数（部分脚本支持）

**结论**：只需要在 `.env` 文件中配置即可！

---

## 📝 使用API Key的文件

所有这些文件都会自动从 `.env` 读取配置，**无需手动修改**：

| 文件 | 用途 | 自动读取 |
|------|------|---------|
| `annotation.py` | AI批量标注 | ✅ |
| `main.py` | 主入口 | ✅ |
| `backend/vlm_analyzer.py` | VLM分析器 | ✅ |
| `backend/api.py` | 后端API | ✅ |
| `config/config.py` | 配置管理 | ✅ |

---

## 🛠️ 验证配置

### 方法1：运行测试脚本
```bash
python -c "from config.config import config; print('Gemini API:', config.get_api_key('gemini')[:20] + '...')"
```

### 方法2：在Python中测试
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key: {api_key[:20]}...")  # 只显示前20个字符
```

### 方法3：检查配置
```bash
python check_config.py
```

---

## 🔐 安全提示

### ✅ 推荐做法
1. **不要**把 `.env` 提交到Git
2. 使用 `.gitignore` 忽略 `.env` 文件
3. 创建 `.env.example` 模板文件

### .gitignore 示例
```gitignore
# API密钥配置
.env
*.env.local

# 排除示例文件
!.env.example
```

### .env.example 模板
```env
# 复制此文件为 .env 并填入你的API Key

GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

---

## 🚀 切换AI模型

### 使用Gemini（默认）
```env
GEMINI_API_KEY=AIzaSy...
```

### 使用OpenAI
1. 在 `.env` 中添加：
```env
OPENAI_API_KEY=sk-...
```

2. 修改脚本中的模型选择：
```python
# annotation.py
analyzer = VLMAnalyzer(
    api_key=config.get_api_key('openai'),  # 改为 'openai'
    provider='openai'  # 指定provider
)
```

### 使用Claude
1. 在 `.env` 中添加：
```env
ANTHROPIC_API_KEY=sk-ant-...
```

2. 类似上面修改provider

---

## 📚 相关文件说明

### `config/config.py`
统一的配置管理类，提供：
- `config.get_api_key(service)` - 获取API Key
- `config.set_api_key(service, key)` - 设置API Key
- 自动从环境变量和配置文件读取

### `config/config.yaml`
备用配置文件（可选），结构：
```yaml
api_keys:
  gemini: null
  openai: null

paths:
  videos: data/videos
  annotations: data/annotations
  keyframes: data/keyframes
```

---

## ❓ 常见问题

### Q: 修改了 .env 但没生效？
**A:** 重启应用/脚本。Python需要重新加载环境变量。

### Q: 找不到 .env 文件？
**A:**
```bash
# 创建 .env 文件
cd video_anno
touch .env  # Linux/Mac
# 或
echo. > .env  # Windows

# 然后编辑
notepad .env  # Windows
nano .env     # Linux/Mac
```

### Q: 想用多个API Key？
**A:** 可以！在 `.env` 中配置多个：
```env
GEMINI_API_KEY=key1
OPENAI_API_KEY=key2
ANTHROPIC_API_KEY=key3
```

### Q: 如何获取Gemini API Key？
**A:** 访问 https://aistudio.google.com/app/apikey

---

## 📞 技术支持

如果遇到问题：
1. 检查 `.env` 文件是否存在
2. 确认API Key格式正确
3. 运行 `python check_config.py` 验证配置
4. 查看错误日志

---

**最后提醒**：修改API Key后记得重启应用！🔄
