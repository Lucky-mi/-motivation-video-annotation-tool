# AI标注质量检查平台使用指南

## 概述

这是一个专为视频标注数据设计的质量检查和审核平台，支持：

- 视频片段播放与标注内容对照
- 标注审核（合理/需修改/删除）
- JSON内容可视化编辑
- 批量操作和导出功能

## 快速启动

### 方式一：使用启动脚本

```bash
python run_reviewer.py
```

选择启动模式：
- `1` - 完整系统（后端API + 前端）
- `2` - 仅前端（Streamlit）
- `3` - 仅后端API

### 方式二：手动启动

```bash
# 启动前端
streamlit run frontend/annotation_reviewer_v2.py --server.port 8502

# 启动后端API（可选）
python -m uvicorn backend.api_reviewer:app --host 0.0.0.0 --port 8001
```

访问地址：
- 前端界面：http://localhost:8502
- 后端API文档：http://localhost:8001/docs

## 数据格式说明

### JSON标注文件结构

```json
{
  "video_id": "视频标识",
  "video_path": "视频路径",
  "duration_seconds": 60,
  "characters": [...],
  "desire_motivation_analysis": [...],
  "desire_transitions": [...],
  "behavioral_sequence": [...],
  "key_segments_for_qa": [...]
}
```

### 片段类型

| 类型 | 说明 | 关键字段 |
|------|------|----------|
| `desire_motivation` | 动机分析 | `temporal_scope.start_seconds/end_seconds` |
| `desire_transition` | 欲望转变 | `temporal_boundaries.onset_timestamp_seconds/offset_timestamp_seconds` |
| `behavioral_sequence` | 行为序列 | `timestamp_start_seconds/timestamp_end_seconds` |
| `key_segment_qa` | QA关键片段 | `start_timestamp_seconds/end_timestamp_seconds` |

## 功能说明

### 1. 文件浏览

左侧边栏显示所有标注文件：
- 显示文件名和审核进度 `[已批准/总数]`
- 支持搜索过滤
- 点击文件加载标注

### 2. 片段导航

- **上一段/下一段** 按钮：快速切换片段
- **片段选择器**：下拉选择特定片段
- **时间轴可视化**：显示所有片段在视频中的位置

### 3. 视频播放

- 自动从片段开始时间播放
- 显示片段时间范围和时长

### 4. 片段详情

根据片段类型显示不同内容：

#### 动机分析 (desire_motivation)
- 强度、马斯洛层级、BDI组件、置信度
- 推理链条
- 支撑证据（带时间戳）
- 替代解释

#### 欲望转变 (desire_transition)
- 转变类型
- 转变前后状态对比
- 触发事件
- 行为标记
- 心理解释

#### 行为序列 (behavioral_sequence)
- 行为类别、强度
- 行为描述
- 推断心理状态
- 与欲望的关联

#### QA关键片段 (key_segment_qa)
- 难度级别
- QA类型
- 片段描述
- 心理意义

### 5. 审核操作

每个片段可标记为：
- ✅ **合理**：标注正确，无需修改
- ⚠️ **需修改**：标注有问题，需要修正
- 🗑️ **删除**：标注错误或不需要
- ↩️ **重置**：清除审核状态

可添加审核备注说明问题。

### 6. JSON编辑

勾选"JSON编辑"选项显示编辑面板：
- 查看原始JSON内容
- 直接编辑并保存
- 自动备份原文件到 `data/annotations_backup/`

### 7. 批量操作

点击"批量操作"按钮：
- **全部批准**：批量标记当前文件所有片段为已批准
- **全部重置**：清除当前文件所有审核状态
- **导出审核结果**：导出为JSON文件

## 数据存储

### 审核状态
存储在 `data/review_status.json`：
```json
{
  "video_id_segment_id": {
    "status": "approved|needs_modification|to_delete",
    "timestamp": "2025-12-12T10:00:00",
    "note": "审核备注"
  }
}
```

### 备份文件
编辑JSON时自动备份到 `data/annotations_backup/`，命名格式：
`{video_id}_{yyyymmdd_HHMMSS}.json`

## API接口

### 标注管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/annotations` | 列出所有标注文件 |
| GET | `/annotations/{video_id}` | 获取单个标注详情 |
| GET | `/annotations/{video_id}/segments` | 获取所有片段 |
| PUT | `/annotations/{video_id}/segments/{segment_id}` | 更新片段 |
| DELETE | `/annotations/{video_id}/segments/{segment_id}` | 删除片段 |

### 审核状态

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/review-status` | 获取所有审核状态 |
| GET | `/review-status/{video_id}` | 获取单个视频审核状态 |
| PUT | `/review-status/{video_id}/{segment_id}` | 更新审核状态 |
| POST | `/review-status/batch` | 批量更新审核状态 |

### 统计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/stats` | 获取总体统计 |
| GET | `/stats/by-type` | 按类型统计 |
| GET | `/export/approved` | 导出已批准片段 |

## 常见问题

### Q: 视频无法播放？
检查：
1. 视频文件路径是否正确（`data/Youtube_videos/`）
2. 视频文件是否存在
3. 视频格式是否支持（mp4/avi/mov/mkv）

### Q: JSON编辑后未生效？
1. 检查JSON格式是否正确
2. 确认点击了"保存JSON"按钮
3. 刷新页面重新加载

### Q: 如何恢复误删的标注？
从 `data/annotations_backup/` 目录找到对应备份文件，复制回 `data/annotations_test/`

## 文件结构

```
project/
├── frontend/
│   ├── annotation_reviewer.py       # 基础版前端
│   └── annotation_reviewer_v2.py    # 增强版前端
├── backend/
│   └── api_reviewer.py              # 审核API服务
├── data/
│   ├── annotations_test/            # 标注JSON文件
│   ├── annotations_backup/          # 备份文件
│   ├── Youtube_videos/              # 视频文件
│   └── review_status.json           # 审核状态
├── run_reviewer.py                  # 启动脚本
└── docs/
    └── ANNOTATION_REVIEWER_GUIDE.md # 本文档
```
