# frontend/app_verification_only.py
"""
视频标注校验平台 - 精简版 (修复导航Bug + 性能优化)
功能：
1. 帧标注校验（查看+修改AI生成的标注）
2. 问题校验（查看+修改AI生成的问题）
3. 问卷收集（让测试者观看视频并回答问题）
"""
import streamlit as st
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

# 添加项目根目录到路径，以便导入 utils
sys.path.append(str(Path(__file__).parent.parent))
# 引入我们之前优化的缓存工具
from frontend.utils.cache import ImageCache

# 配置
st.set_page_config(
    page_title="视频标注校验平台",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API配置 (如果后端启动在8000端口，请改为8000，您之前是8001?)
# 请根据实际情况修改端口，通常是 8000
API_BASE_URL = "http://localhost:8000" 

# 数据路径
DATA_ROOT = Path("data")
ANNOTATIONS_DIR = DATA_ROOT / "annotations"
QUESTIONS_DIR = DATA_ROOT / "questions"
KEYFRAMES_DIR = DATA_ROOT / "keyframes"
QUESTIONNAIRE_DIR = DATA_ROOT / "questionnaire_responses"

# ============= 工具函数 =============

def load_annotation(video_id: str) -> Optional[Dict]:
    """加载标注数据"""
    try:
        # 尝试从API加载
        response = requests.get(f"{API_BASE_URL}/annotations/{video_id}", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # 降级到本地读取
    anno_path = ANNOTATIONS_DIR / f"{video_id}.json"
    if anno_path.exists():
        with open(anno_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_annotation(video_id: str, data: Dict) -> bool:
    """保存标注数据"""
    try:
        # 1. 尝试调用API保存
        # 注意：这里假设后端有 keyframe 更新接口，如果没有则只存本地
        # requests.post(f"{API_BASE_URL}...", json=...) 
        
        # 2. 本地保存
        anno_path = ANNOTATIONS_DIR / f"{video_id}.json"
        data['last_modified'] = datetime.now().isoformat()
        with open(anno_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"保存失败: {e}")
        return False

def load_questions(video_id: str) -> Optional[Dict]:
    """加载问题集"""
    try:
        response = requests.get(f"{API_BASE_URL}/questions/{video_id}", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
        
    q_path = QUESTIONS_DIR / f"{video_id}_questions.json"
    if q_path.exists():
        with open(q_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_questions(video_id: str, data: Dict) -> bool:
    """保存问题集"""
    try:
        q_path = QUESTIONS_DIR / f"{video_id}_questions.json"
        with open(q_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"保存失败: {e}")
        return False

def list_videos(only_with_images: bool = True) -> List[Dict]:
    """列出所有视频

    Args:
        only_with_images: 如果为True，只返回有实际关键帧图片的视频
    """
    videos = []
    for anno_file in ANNOTATIONS_DIR.glob("*.json"):
        try:
            with open(anno_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                video_id = anno_file.stem
                video_name = data.get("video_name", anno_file.stem)
                keyframes = data.get("keyframes", [])

                # 如果需要检查图片是否存在
                has_images = False
                if keyframes:
                    # 检查第一帧图片是否存在
                    first_frame_path = keyframes[0].get('frame_path', '')
                    if first_frame_path:
                        # 尝试多种可能的路径
                        possible_paths = [
                            Path(first_frame_path),
                            KEYFRAMES_DIR / video_id / Path(first_frame_path).name,
                            KEYFRAMES_DIR / Path(video_name).stem / Path(first_frame_path).name
                        ]
                        has_images = any(p.exists() for p in possible_paths)

                # 如果要求只显示有图片的，且当前视频没有图片，跳过
                if only_with_images and not has_images:
                    continue

                videos.append({
                    "video_id": video_id,
                    "video_name": video_name,
                    "total_frames": len(keyframes),
                    "status": data.get("status", "unknown"),
                    "has_images": has_images
                })
        except:
            continue
    return videos

# ============= 页面1: 帧标注校验 =============

def page_frame_verification():
    """帧标注校验页面"""
    st.title("🖼️ 关键帧标注校验")
    st.markdown("校验和修改AI生成的帧标注（动作描述 + 动机分析）")

    # 选择视频
    videos = list_videos()
    if not videos:
        st.warning("没有找到标注数据，请先运行 annotation.py 进行批处理")
        return

    video_options = {v['video_name']: v['video_id'] for v in videos}
    selected_name = st.selectbox("选择视频", list(video_options.keys()))

    if not selected_name:
        return

    video_id = video_options[selected_name]

    # === 关键修复：检测视频切换，重置帧索引 ===
    if 'last_video_id' not in st.session_state:
        st.session_state.last_video_id = None

    # 如果切换了视频，重置帧索引
    if st.session_state.last_video_id != video_id:
        st.session_state.current_frame_idx = 0
        st.session_state.last_video_id = video_id

    # 加载标注
    annotation = load_annotation(video_id)
    if not annotation:
        st.error("加载标注失败")
        return

    keyframes = annotation.get('keyframes', [])
    if not keyframes:
        st.warning("该视频没有关键帧")
        return

    st.markdown("---")

    # === 核心修复：导航逻辑 ===
    # 初始化状态
    if 'current_frame_idx' not in st.session_state:
        st.session_state.current_frame_idx = 0

    # 确保索引不越界
    if st.session_state.current_frame_idx >= len(keyframes):
        st.session_state.current_frame_idx = len(keyframes) - 1
    if st.session_state.current_frame_idx < 0:
        st.session_state.current_frame_idx = 0

    st.subheader(f"共 {len(keyframes)} 个关键帧")

    # 1. 数字输入框回调：当用户手动输入数字时触发
    def on_frame_input_change():
        st.session_state.current_frame_idx = st.session_state.frame_selector

    # 2. 按钮回调：点击按钮时触发
    def go_prev():
        new_idx = max(0, st.session_state.current_frame_idx - 1)
        st.session_state.current_frame_idx = new_idx
        st.session_state.frame_selector = new_idx  # 强制同步输入框

    def go_next():
        new_idx = min(len(keyframes)-1, st.session_state.current_frame_idx + 1)
        st.session_state.current_frame_idx = new_idx
        st.session_state.frame_selector = new_idx  # 强制同步输入框

    # 渲染控件
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    
    with col_nav2:
        st.number_input(
            "跳转到帧",
            min_value=0,
            max_value=len(keyframes)-1,
            value=st.session_state.current_frame_idx,
            key="frame_selector",
            on_change=on_frame_input_change,
            label_visibility="collapsed"
        )

    with col_nav1:
        st.button("⬅️ 上一帧", disabled=(st.session_state.current_frame_idx == 0), on_click=go_prev)
    with col_nav3:
        st.button("下一帧 ➡️", disabled=(st.session_state.current_frame_idx >= len(keyframes)-1), on_click=go_next)

    # 当前索引
    frame_idx = st.session_state.current_frame_idx
    
    # 预加载图片 (解决卡顿)
    ImageCache.preload(keyframes, frame_idx, window_size=1, base_url=API_BASE_URL)

    st.markdown("---")

    # 显示当前帧
    frame = keyframes[frame_idx]

    col_img, col_edit = st.columns([1.2, 1]) # 调整比例让图片大一点

    with col_img:
        st.subheader(f"关键帧 #{frame_idx}")

        # === 优化：使用 ImageCache 加载图片 ===
        frame_path_str = frame.get('frame_path', '')
        if frame_path_str:
            # 尝试从缓存加载（支持本地和URL）
            img = ImageCache.get(frame_path_str, API_BASE_URL)
            if img:
                st.image(img, width='stretch')
            else:
                # 降级提示
                st.warning(f"图片加载失败: {frame_path_str}")
                # 尝试直接显示本地路径（作为最后手段）
                if Path(frame_path_str).exists():
                    st.image(str(frame_path_str), width='stretch')
        else:
            st.error("路径为空")

        # 时间戳
        ts = frame.get('timestamp_seconds', 0)
        st.info(f"⏱️ 时间戳: {int(ts//60):02d}:{int(ts%60):02d}")

    with col_edit:
        st.subheader("标注编辑")

        # Action (What)
        with st.expander("📝 动作描述 (What)", expanded=True):
            action = frame.get('action', {})

            # 使用唯一的 Key 避免文字不刷新
            action_desc = st.text_area(
                "动作描述",
                value=action.get('action_description', ''),
                height=100,
                key=f"action_desc_{frame_idx}_{video_id}"
            )

            visual_context = st.text_area(
                "视觉环境",
                value=action.get('visual_context', ''),
                height=80,
                key=f"visual_{frame_idx}_{video_id}"
            )

            col_obj, col_char = st.columns(2)
            with col_obj:
                objects = st.text_input(
                    "物体",
                    value=", ".join(action.get('objects', [])),
                    key=f"objects_{frame_idx}_{video_id}"
                )
            with col_char:
                characters = st.text_input(
                    "角色",
                    value=", ".join(action.get('characters', [])),
                    key=f"chars_{frame_idx}_{video_id}"
                )

        # Motivation (Why)
        with st.expander("🧠 动机分析 (Why)", expanded=True):
            motivation = frame.get('motivation', {})

            explicit_mot = st.text_area(
                "显性动机",
                value=motivation.get('explicit_motivation', ''),
                height=80,
                key=f"explicit_{frame_idx}_{video_id}"
            )

            implicit_desire = st.text_area(
                "隐性渴望",
                value=motivation.get('implicit_desire', ''),
                height=80,
                key=f"implicit_{frame_idx}_{video_id}"
            )

            col_cat, col_type = st.columns(2)
            with col_cat:
                # 安全获取索引
                cat_opts = ["safety", "belonging", "esteem", "self_actualization", "other"]
                curr_cat = motivation.get('desire_category', 'other')
                cat_idx = cat_opts.index(curr_cat) if curr_cat in cat_opts else 4
                
                desire_category = st.selectbox(
                    "渴望类别",
                    options=cat_opts,
                    index=cat_idx,
                    key=f"category_{frame_idx}_{video_id}"
                )
            with col_type:
                type_opts = ["intrinsic", "extrinsic", "mixed"]
                curr_type = motivation.get('motivation_type', 'mixed')
                type_idx = type_opts.index(curr_type) if curr_type in type_opts else 2
                
                mot_type = st.selectbox(
                    "动机类型",
                    options=type_opts,
                    index=type_idx,
                    key=f"mottype_{frame_idx}_{video_id}"
                )

            reasoning = st.text_area(
                "推理依据",
                value=motivation.get('reasoning', ''),
                height=80,
                key=f"reasoning_{frame_idx}_{video_id}"
            )

        # 保存按钮
        if st.button("💾 保存修改", type="primary"):
            # 更新数据
            keyframes[frame_idx]['action'] = {
                **action,
                'action_description': action_desc,
                'visual_context': visual_context,
                'objects': [o.strip() for o in objects.split(',') if o.strip()],
                'characters': [c.strip() for c in characters.split(',') if c.strip()]
            }

            keyframes[frame_idx]['motivation'] = {
                **motivation,
                'explicit_motivation': explicit_mot,
                'implicit_desire': implicit_desire,
                'desire_category': desire_category,
                'motivation_type': mot_type,
                'reasoning': reasoning,
                'status': 'human_modified'
            }

            annotation['keyframes'] = keyframes

            if save_annotation(video_id, annotation):
                st.toast("✅ 保存成功！")
            else:
                st.error("❌ 保存失败")

# ============= 页面2: 问题校验 =============

def page_question_verification():
    """问题校验页面"""
    st.title("❓ 问题校验")
    st.markdown("校验和修改AI生成的问题")

    # 选择视频
    videos = list_videos()
    if not videos:
        st.warning("没有找到标注数据")
        return

    video_options = {v['video_name']: v['video_id'] for v in videos}
    selected_name = st.selectbox("选择视频", list(video_options.keys()), key="q_video_select")

    if not selected_name:
        return

    video_id = video_options[selected_name]

    # 加载问题
    questions_data = load_questions(video_id)
    if not questions_data:
        st.warning("该视频还没有生成问题集，请运行问题生成脚本")
        return

    questions = questions_data.get('questions', [])
    if not questions:
        st.warning("问题集为空")
        return

    st.markdown("---")
    st.subheader(f"共 {len(questions)} 个问题")

    # 逐个显示问题
    for idx, q in enumerate(questions):
        # 使用 unique key 确保展开状态正常
        with st.expander(f"问题 {idx+1}: {q.get('question_text', '')[:50]}...", expanded=(idx==0)):
            col_q, col_a = st.columns([2, 1])

            with col_q:
                question_text = st.text_area(
                    "问题",
                    value=q.get('question_text', ''),
                    height=100,
                    key=f"q_text_{idx}_{video_id}"
                )
                
                # 选项列表
                options = q.get('options', [])
                for opt_idx, opt in enumerate(options):
                    col_o1, col_o2 = st.columns([1, 4])
                    with col_o1:
                        st.markdown(f"**{opt.get('option_id')}**")
                    with col_o2:
                        opt['text'] = st.text_input(
                            "选项内容",
                            value=opt.get('text', ''),
                            key=f"opt_{idx}_{opt_idx}_{video_id}",
                            label_visibility="collapsed"
                        )

            with col_a:
                # 正确答案选择
                option_ids = [opt.get('option_id') for opt in options]
                correct_id = q.get('correct_option_id')
                
                # 确保索引有效
                try:
                    correct_idx = option_ids.index(correct_id)
                except ValueError:
                    correct_idx = 0
                
                new_correct_id = st.radio(
                    "正确答案",
                    options=option_ids,
                    index=correct_idx,
                    key=f"correct_{idx}_{video_id}",
                    horizontal=True
                )
                
                # 校验状态
                verified = st.checkbox(
                    "✅ 已校验",
                    value=q.get('verified', False),
                    key=f"q_verified_{idx}_{video_id}"
                )

            if st.button(f"💾 保存问题 {idx+1}", key=f"save_q_{idx}_{video_id}"):
                # 更新对象
                q['question_text'] = question_text
                q['correct_option_id'] = new_correct_id
                q['verified'] = verified
                # options 是引用，已经更新了
                
                questions[idx] = q
                questions_data['questions'] = questions

                if save_questions(video_id, questions_data):
                    st.toast(f"✅ 问题 {idx+1} 保存成功！")

# ============= 页面3: 问卷收集 =============

def page_questionnaire():
    """问卷收集页面"""
    st.title("📋 问卷测试")
    st.markdown("让测试者观看视频并回答问题")

    # 测试者信息
    st.subheader("测试者信息")
    col1, col2 = st.columns(2)
    with col1:
        tester_id = st.text_input("测试者ID（必填）", key="tester_id")
    with col2:
        tester_name = st.text_input("测试者姓名（可选）", key="tester_name")

    if not tester_id:
        st.warning("请输入测试者ID")
        return

    st.markdown("---")

    # 选择视频 (使用匿名映射防止作弊)
    videos = list_videos()
    if not videos:
        st.warning("没有可用的视频")
        return

    # 匿名映射：测试视频 A, 测试视频 B...
    video_map = {f"测试视频 {i+1}": v['video_id'] for i, v in enumerate(videos)}
    display_names = list(video_map.keys())
    
    selected_display = st.selectbox("选择测试视频", display_names, key="test_video_select")
    video_id = video_map[selected_display]

    # 加载问题
    questions_data = load_questions(video_id)
    if not questions_data:
        st.warning("该视频还没有问题集")
        return

    questions = questions_data.get('questions', [])
    if not questions:
        st.warning("问题集为空")
        return

    # 加载关键帧图片（用于答题参考）
    annotation = load_annotation(video_id)
    keyframes = annotation.get('keyframes', []) if annotation else []

    st.markdown("---")
    st.subheader("问题回答")

    # 收集答案
    answers = {}
    for idx, q in enumerate(questions):
        st.markdown(f"#### 问题 {idx+1}")
        
        # 1. 显示关联图片
        related_ids = q.get('related_frame_ids', [])
        if related_ids and keyframes:
            target_frame = next((k for k in keyframes if k.get('frame_id') == related_ids[0]), None)
            if target_frame:
                path = target_frame.get('frame_path')
                if path:
                    img = ImageCache.get(path, API_BASE_URL)
                    if img:
                        st.image(img, caption="参考场景", width=500) # 限制宽度
        
        # 2. 显示题目
        st.markdown(f"**{q.get('question_text', '')}**")
        
        # 3. 显示选项 (Radio)
        opts = q.get('options', [])
        opt_labels = [f"{o['option_id']}. {o['text']}" for o in opts]
        
        user_choice = st.radio(
            "请选择:",
            options=opt_labels,
            index=None,
            key=f"user_ans_{idx}_{video_id}"
        )
        
        if user_choice:
            choice_id = user_choice.split(".")[0]
            answers[q.get('question_id')] = choice_id
            
        st.markdown("---")

    # 提交
    if st.button("📤 提交问卷", type="primary"):
        if len(answers) < len(questions):
            st.warning(f"请回答所有问题 (已答 {len(answers)}/{len(questions)})")
        else:
            # 保存问卷
            submission_data = {
                "tester_id": tester_id,
                "tester_name": tester_name,
                "video_id": video_id,
                "answers": answers,
                "submitted_at": datetime.now().isoformat()
            }

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{video_id}_{tester_id}_{timestamp}.json"

            QUESTIONNAIRE_DIR.mkdir(parents=True, exist_ok=True)
            output_path = QUESTIONNAIRE_DIR / filename

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(submission_data, f, ensure_ascii=False, indent=2)

            st.success("✅ 提交成功！感谢你的参与！")
            st.balloons()
            
            # 可选：显示得分
            score = 0
            for q in questions:
                qid = q.get('question_id')
                if answers.get(qid) == q.get('correct_option_id'):
                    score += 1
            st.info(f"本次得分: {score} / {len(questions)}")

# ============= 主应用 =============

def main():
    st.sidebar.title("🎯 功能选择")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "选择功能",
        ["🖼️ 帧标注校验", "❓ 问题校验", "📋 问卷测试"],
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📌 使用说明")
    st.sidebar.info("""
    **帧标注校验**: 查看和修改AI生成的关键帧标注
    
    **问题校验**: 审核和修改AI生成的问题
    
    **问卷测试**: 让测试者观看视频并回答问题
    
    ---
    
    **AI批处理**: 请运行 `python annotation.py`
    """)

    # 路由
    if page == "🖼️ 帧标注校验":
        page_frame_verification()
    elif page == "❓ 问题校验":
        page_question_verification()
    elif page == "📋 问卷测试":
        page_questionnaire()

if __name__ == "__main__":
    main()