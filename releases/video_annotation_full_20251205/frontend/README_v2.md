# Frontend V2 - 解耦架构说明

## 📁 项目结构

```
frontend/
├── app_v2.py                    # 主应用入口（解耦版）
├── app_complete.py              # 旧版完整应用（保留）
├── app_fast.py                  # 高性能版（保留）
│
├── components/                  # UI组件模块
│   ├── __init__.py
│   ├── video_player.py         # 视频播放器组件
│   ├── keyframe_viewer.py      # 关键帧查看器组件
│   └── annotation_editor.py    # 标注编辑器组件
│
├── pages/                       # 页面模块
│   ├── __init__.py
│   ├── upload_page.py          # 上传页面
│   ├── review_page.py          # 审核页面
│   ├── batch_page.py           # 批量处理页面
│   └── rename_page.py          # 重命名页面
│
└── utils/                       # 工具模块
    ├── __init__.py
    ├── api_client.py           # API客户端封装
    ├── cache.py                # 缓存管理
    └── helpers.py              # 辅助函数
```

## 🎯 设计理念

### 1. 模块化设计
- **组件层** (`components/`): 可复用的UI组件
- **页面层** (`pages/`): 完整的页面视图
- **工具层** (`utils/`): 业务逻辑和数据处理

### 2. 职责分离
- 每个模块负责单一职责
- 降低耦合度，提高可维护性
- 便于单元测试和功能扩展

### 3. 统一接口
- 所有页面类提供 `render(api_client)` 方法
- 所有组件类提供静态渲染方法
- 统一的数据缓存策略

## 📦 核心模块说明

### Components 组件

#### KeyframeViewer (关键帧查看器)
```python
from frontend.components import KeyframeViewer

# 渲染完整查看器（导航+图片+标注）
idx, edited_data = KeyframeViewer.render_complete_viewer(
    keyframes=keyframes,
    current_idx=0,
    editable=False,
    base_url="http://localhost:8000"
)
```

**功能**:
- 关键帧导航控件
- 图片显示和预加载
- 标注内容展示
- 支持编辑模式

#### AnnotationEditor (标注编辑器)
```python
from frontend.components import AnnotationEditor

# 元数据编辑
metadata = AnnotationEditor.render_metadata_editor(annotation)

# 转变编辑
transitions = AnnotationEditor.render_transitions_editor(transitions_list)

# 保存控件
AnnotationEditor.render_save_controls(
    on_save_callback=save_function,
    on_cancel_callback=cancel_function
)
```

**功能**:
- 视频元信息编辑
- 动机转变编辑
- 统一的保存/取消控件

### Pages 页面

#### UploadPage (上传页面)
```python
from frontend.pages import UploadPage

UploadPage.render(api_client)
```

**功能**:
- 视频文件上传
- AI模型选择
- 实时分析进度
- 结果摘要展示

#### ReviewPage (审核页面)
```python
from frontend.pages import ReviewPage

ReviewPage.render(api_client)
```

**功能**:
- 视频列表选择
- 关键帧浏览
- 标注内容审核
- 编辑模式切换

#### BatchPage (批量处理页面)
```python
from frontend.pages import BatchPage

BatchPage.render(api_client)
```

**功能**:
- 文件夹扫描
- 批量视频分析
- 进度跟踪
- 结果统计

#### RenamePage (重命名页面)
```python
from frontend.pages import RenamePage

RenamePage.render(api_client)
```

**功能**:
- AI主题提取
- 自动命名建议
- 批量重命名

### Utils 工具

#### APIClient (API客户端)
```python
from frontend.utils import get_api_client

api_client = get_api_client()  # 单例模式

# 上传视频
result = api_client.upload_video(file, provider="gemini")

# 获取标注
annotation = api_client.get_annotation(video_id)

# 更新标注
api_client.update_annotation(video_id, annotation_data)
```

**功能**:
- 统一的HTTP请求封装
- 错误处理
- 超时管理
- 健康检查

#### DataCache (数据缓存)
```python
from frontend.utils import DataCache

# 缓存视频列表
videos = DataCache.get_videos(api_client)

# 缓存标注数据
annotation = DataCache.get_annotation(api_client, video_id)

# 清除缓存
DataCache.clear_annotation_cache(video_id)
```

**功能**:
- Streamlit缓存装饰器
- TTL管理（5-10分钟）
- 选择性缓存清除

#### ImageCache (图片缓存)
```python
from frontend.utils import ImageCache

# 获取图片（自动缓存）
img = ImageCache.get(image_path, base_url)

# 预加载相邻帧
ImageCache.preload(keyframes, current_idx, num_ahead=2)

# 清空缓存
ImageCache.clear()
```

**功能**:
- LRU缓存算法
- 本地文件优先
- API回退机制
- 相邻帧预加载

#### Helpers (辅助函数)
```python
from frontend.utils import format_timestamp, get_desire_emoji

# 格式化时间戳
time_str = format_timestamp(125.5)  # "02:05"

# 获取emoji
emoji = get_desire_emoji("belonging")  # "❤️"
```

**功能**:
- 时间格式化
- Emoji映射
- 文本截断
- 安全字典访问

## 🚀 使用指南

### 启动应用
```bash
# 启动解耦版
streamlit run frontend/app_v2.py

# 或使用快捷脚本
python main.py  # 选择 app_v2
```

### 添加新页面
1. 在 `pages/` 创建新文件
2. 实现 `render(api_client)` 静态方法
3. 在 `pages/__init__.py` 导出
4. 在 `app_v2.py` 添加路由

示例:
```python
# pages/export_page.py
import streamlit as st

class ExportPage:
    @staticmethod
    def render(api_client):
        st.title("导出数据")
        # 实现导出逻辑
```

```python
# pages/__init__.py
from .export_page import ExportPage
__all__ = [..., 'ExportPage']
```

```python
# app_v2.py
from frontend.pages import ..., ExportPage

# 在render_main_content()添加
elif current_page == "export":
    ExportPage.render(api_client)
```

### 添加新组件
1. 在 `components/` 创建新文件
2. 使用静态方法实现组件
3. 在 `components/__init__.py` 导出

示例:
```python
# components/timeline.py
import streamlit as st

class Timeline:
    @staticmethod
    def render(keyframes):
        # 渲染时间轴
        pass
```

## 🎨 设计模式

### 1. 单例模式
- `get_api_client()` 返回全局唯一的API客户端
- 使用 `@st.cache_resource` 装饰器

### 2. 静态工厂模式
- 所有组件和页面使用静态方法
- 无需实例化，直接调用

### 3. 策略模式
- 不同AI提供商的策略
- 缓存策略（LRU）

### 4. 观察者模式
- Session State作为状态管理
- 页面间通过状态通信

## 📊 性能优化

### 1. 多级缓存
- **数据缓存**: Streamlit `@cache_data`（5-10分钟TTL）
- **图片缓存**: LRU缓存（最多30张）
- **API客户端**: `@cache_resource` 单例

### 2. 预加载策略
- 相邻关键帧预加载
- 后台异步加载

### 3. 懒加载
- 按需加载标注数据
- 视频切换时才重新加载

## 🔧 扩展建议

### 短期优化
- [ ] 添加导出功能页面
- [ ] 支持视频剪辑预览
- [ ] 添加标注质量检查
- [ ] 支持多用户协作

### 长期规划
- [ ] 迁移到React前端
- [ ] WebSocket实时通信
- [ ] 用户权限管理
- [ ] 数据库持久化

## 📝 版本对比

| 特性 | app.py (原版) | app_v2.py (解耦版) |
|------|--------------|-------------------|
| 代码行数 | ~800 | ~260 (主文件) |
| 可维护性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 可扩展性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 可测试性 | ⭐⭐ | ⭐⭐⭐⭐ |
| 性能 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 模块复用 | ❌ | ✅ |

## 🐛 常见问题

### Q: 为什么要解耦？
A: 提高代码可维护性、可测试性和可扩展性，方便团队协作。

### Q: 旧版本还能用吗？
A: 可以，`app.py` 和 `app_complete.py` 都保留了。

### Q: 如何选择合适的版本？
- **快速开发**: 使用 `app_v2.py`（解耦，易维护）
- **高性能**: 使用 `app_fast.py`（优化版）
- **完整功能**: 使用 `app_complete.py`（功能最全）

### Q: 缓存什么时候清除？
- 图片缓存: 手动清除或重启应用
- 数据缓存: TTL过期自动清除
- 强制清除: 使用侧边栏的清除按钮

## 📄 许可证

MIT License

---

**作者**: Claude Code
**版本**: v2.0.0
**更新日期**: 2025-01-18
