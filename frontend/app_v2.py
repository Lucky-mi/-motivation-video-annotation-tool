# frontend/app_v2.py
"""
AI协同标注平台 v2 - 解耦架构版
采用模块化设计，提升代码可维护性和可扩展性
"""
import streamlit as st
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入解耦模块
from frontend.utils import get_api_client, DataCache, ImageCache
from frontend.pages import UploadPage, ReviewPage, BatchPage, RenamePage

# ============= 页面配置 =============
st.set_page_config(
    page_title="AI协同标注平台 v2",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============= 全局样式 =============
st.markdown("""
<style>
    /* 优化整体样式 */
    .main {
        padding: 1rem;
    }

    /* 优化按钮样式 */
    .stButton button {
        border-radius: 8px;
        transition: all 0.3s;
    }

    /* 优化expander样式 */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1.1rem;
    }

    /* 优化metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }

    /* 优化侧边栏 */
    .css-1d391kg {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============= Session State初始化 =============
def init_session_state():
    """初始化session state"""
    defaults = {
        'current_page': 'upload',
        'last_review_video': None,
        'review_frame_idx': 0,
        'image_cache': {},
        'image_order': []
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============= 侧边栏导航 =============
def render_sidebar():
    """渲染侧边栏导航"""
    with st.sidebar:
        st.title("🎬 AI标注平台")
        st.markdown("---")

        # 页面导航
        st.markdown("### 📋 功能导航")

        pages = {
            "📤 上传视频": "upload",
            "🔍 审核标注": "review",
            "📦 批量处理": "batch",
            "✏️ 视频重命名": "rename"
        }

        for page_name, page_key in pages.items():
            if st.button(
                page_name,
                use_container_width=True,
                type="primary" if st.session_state.current_page == page_key else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()

        st.markdown("---")

        # 系统状态
        st.markdown("### 📊 系统状态")

        # API健康检查
        api_client = get_api_client()
        is_healthy = api_client.health_check()

        if is_healthy:
            st.success("✅ API服务正常")
        else:
            st.error("❌ API服务离线")
            st.caption("请检查后端服务是否启动")

        # 缓存状态
        cache_size = len(st.session_state.get('image_cache', {}))
        st.info(f"🖼️ 图片缓存: {cache_size} 张")

        if cache_size > 0:
            if st.button("🗑️ 清空图片缓存", use_container_width=True):
                ImageCache.clear()
                st.success("缓存已清空")
                st.rerun()

        st.markdown("---")

        # 帮助信息
        with st.expander("❓ 使用帮助"):
            st.markdown("""
            **快速开始**:
            1. 📤 上传视频进行AI分析
            2. 🔍 审核AI生成的标注
            3. ✏️ 编辑和修改标注
            4. 💾 导出标注数据

            **快捷键**:
            - `←` `→`: 切换关键帧
            - `Ctrl+S`: 保存修改

            **提示**:
            - 使用Gemini模型更快
            - 支持批量处理
            - 数据自动缓存
            """)

        # 版本信息
        st.caption("v2.0.0 | 解耦架构版")
        st.caption("Powered by Claude Code")

# ============= 主页面路由 =============
def render_main_content():
    """根据当前页面渲染主内容"""
    api_client = get_api_client()

    current_page = st.session_state.current_page

    # 页面路由
    if current_page == "upload":
        UploadPage.render(api_client)

    elif current_page == "review":
        ReviewPage.render(api_client)

    elif current_page == "batch":
        BatchPage.render(api_client)

    elif current_page == "rename":
        RenamePage.render(api_client)

    else:
        # 默认欢迎页
        render_welcome_page()

# ============= 欢迎页 =============
def render_welcome_page():
    """渲染欢迎页"""
    st.title("🎬 欢迎使用AI协同标注平台")

    st.markdown("""
    ### ✨ 功能特性

    这是一个基于AI的视频标注平台，帮助您快速理解视频内容的深层含义。

    **核心功能**:
    - 🤖 **智能分析**: 使用Gemini/GPT-4V分析视频内容
    - 🎯 **双层标注**: What(客观描述) + Why(动机分析)
    - 🔍 **可视化审核**: 直观的关键帧查看和标注编辑
    - 📦 **批量处理**: 一次性处理整个文件夹
    - ⚡ **高性能缓存**: 图片预加载，快速切换

    ### 🚀 快速开始

    1. **上传视频** - 点击左侧"📤 上传视频"开始分析
    2. **审核标注** - 查看AI生成的标注结果
    3. **编辑优化** - 根据需要调整标注内容
    4. **导出数据** - 保存为JSON格式

    ### 📋 标注框架

    本系统采用双层标注框架:

    - **What层**: 客观描述可见元素
      - 动作描述
      - 场景信息
      - 物体和角色

    - **Why层**: 分析隐性动机
      - 显性动机 (表面意图)
      - 隐性渴望 (深层需求)
      - 推理依据 (AI分析)

    ### 🎯 适用场景

    - 📺 影视剧情分析
    - 📊 用户行为研究
    - 🎓 教学视频标注
    - 🔬 心理学研究
    - 📈 营销广告分析
    """)

    # 统计信息
    st.markdown("---")
    st.markdown("### 📊 系统概览")

    try:
        api_client = get_api_client()
        videos = DataCache.get_videos(api_client)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("已分析视频", len(videos))

        with col2:
            total_keyframes = sum(
                len(DataCache.get_annotation(api_client, v['video_id']).get('keyframes', []))
                for v in videos
                if DataCache.get_annotation(api_client, v['video_id'])
            )
            st.metric("总关键帧数", total_keyframes)

        with col3:
            cache_size = len(st.session_state.get('image_cache', {}))
            st.metric("缓存图片", cache_size)

    except:
        st.info("💡 上传第一个视频开始使用平台")

# ============= 主入口 =============
def main():
    """主函数"""
    # 渲染侧边栏
    render_sidebar()

    # 渲染主内容
    render_main_content()

if __name__ == "__main__":
    main()
