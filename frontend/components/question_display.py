import streamlit as st
from typing import List, Dict, Any, Callable
import sys
from pathlib import Path

# Add backend to path to import models
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.append(str(backend_path))

# Try importing models, handle if backend not found (e.g. during dev)
try:
    from backend.models_questions import Question, QuestionOption
except ImportError:
    # Fallback or mock if needed
    pass

class QuestionDisplay:
    """问题展示组件"""

    @staticmethod
    def render_question_card(
        question: Dict, 
        index: int, 
        total: int,
        editable: bool = False,
        on_verify: Callable = None
    ):
        """渲染单个问题卡片"""
        
        # 标题栏
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### 问题 {index + 1}/{total}")
        with col2:
            if question.get('verified'):
                st.success("✅ 已校验")
            else:
                st.warning("⏳ 待校验")

        # 问题文本
        if editable:
            q_text = st.text_area(
                "问题内容",
                value=question.get('question_text', ''),
                key=f"q_text_{question.get('question_id')}"
            )
        else:
            st.markdown(f"**Q: {question.get('question_text', '')}**")
            q_text = question.get('question_text', '')

        st.divider()

        # 选项列表
        options = question.get('options', [])
        correct_id = question.get('correct_option_id', '')
        
        # 提取选项ID列表
        option_ids = [opt.get('option_id') for opt in options]
        
        if editable:
            # 1. 使用单选按钮选择正确答案
            col_sel, col_tip = st.columns([1, 3])
            with col_sel:
                new_correct_id = st.radio(
                    "选择正确选项",
                    options=option_ids,
                    index=option_ids.index(correct_id) if correct_id in option_ids else 0,
                    horizontal=True,
                    key=f"correct_radio_{question.get('question_id')}"
                )
            with col_tip:
                st.info(f"当前正确答案: {new_correct_id}")
            
            # 更新 correct_id 供后续使用
            correct_id = new_correct_id
        
        # 渲染选项文本编辑
        QuestionDisplay.render_option_list(
            options, 
            correct_id, 
            editable, 
            key_prefix=question.get('question_id')
        )

        st.divider()

        # 推理过程
        with st.expander("🧠 AI推理过程", expanded=True):
            if editable:
                reasoning = st.text_area(
                    "推理逻辑",
                    value=question.get('reasoning_process', ''),
                    key=f"reasoning_{question.get('question_id')}"
                )
            else:
                st.info(question.get('reasoning_process', ''))
                reasoning = question.get('reasoning_process', '')

        # 校验控制区
        if on_verify:
            st.divider()
            QuestionDisplay.render_verification_controls(
                question, 
                on_verify,
                current_data = {
                'question_text': question.get('question_text', ''), # 注意：这里应该获取 editable textarea 的值
                'reasoning_process': question.get('reasoning_process', ''), # 同上
                'correct_option_id': correct_id, # <--- 传入新的正确答案 ID
                'options': options # 选项文本在 render_option_list 里是直接绑定的，可能需要特殊处理
            }
            )

    @staticmethod
    def render_option_list(
        options: List[Dict], 
        correct_id: str, 
        editable: bool = False,
        key_prefix: str = ""
    ):
        for i, opt in enumerate(options):
            opt_id = opt.get('option_id')
            is_correct = (opt_id == correct_id)
            
            container = st.container()
            
            if editable:
                col1, col2 = container.columns([1, 10]) # 去掉 checkbox 列
                with col1:
                    # 高亮显示正确选项的 ID
                    if is_correct:
                        st.markdown(f"### ✅ {opt_id}")
                    else:
                        st.markdown(f"### {opt_id}")
                with col2:
                    # 选项文本输入
                    new_text = st.text_input(
                        "选项文本",
                        value=opt.get('text', ''),
                        key=f"opt_text_{key_prefix}_{opt_id}",
                        label_visibility="collapsed"
                    )
                    # 直接修改原字典（Streamlit reruns时会重置，如果需要保存，这里其实需要配合 session_state 或回调）
                    # 简单做法：在 on_verify 时重新从 state 中读取
                    opt['text'] = new_text 
                    
                    st.text_input(
                        "解释",
                        value=opt.get('explanation', ''),
                        key=f"opt_exp_{key_prefix}_{opt_id}",
                        placeholder="选项解释..."
                    )
            else:
                # 只读模式
                bg_color = "rgba(0, 255, 0, 0.1)" if is_correct else "transparent"
                border_color = "green" if is_correct else "gray"
                icon = "✅" if is_correct else "❌"
                
                container.markdown(
                    f"""
                    <div style="
                        padding: 10px; 
                        border: 1px solid {border_color}; 
                        border-radius: 5px; 
                        background-color: {bg_color};
                        margin-bottom: 10px;
                    ">
                        <div style="font-weight: bold;">
                            {opt_id}. {opt.get('text', '')} {icon}
                        </div>
                        <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                            {opt.get('explanation', '')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    @staticmethod
    def render_test_mode(question: Dict, index: int, total: int, on_submit: Callable):
        """渲染测试模式（盲测答题）"""
        st.markdown(f"### 📝 问题 {index + 1} / {total}")
        
        # 显示问题文本
        st.markdown(f"**Q: {question.get('question_text', '')}**")
        
        st.divider()
        
        # 获取选项
        options = question.get('options', [])
        # 提取选项文本用于显示
        option_labels = [f"{opt['option_id']}. {opt['text']}" for opt in options]
        
        # 使用 Radio 进行单选
        # 注意：key 需要包含 'test_mode' 以免与编辑模式冲突
        selected_label = st.radio(
            "请选择最合适的答案：",
            options=option_labels,
            index=None, # 默认不选中
            key=f"test_radio_{question.get('question_id')}"
        )
        
        st.markdown("---")
        
        # 提交按钮
        if st.button("提交答案", type="primary", disabled=(selected_label is None), use_container_width=True):
            # 提取选中的 ID (例如 "A")
            selected_id = selected_label.split(".")[0]
            # 回调
            on_submit(question.get('question_id'), selected_id)
    @staticmethod
    def render_verification_controls(
        question: Dict, 
        on_verify: Callable,
        current_data: Dict
    ):
        """渲染校验控制按钮"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ 通过", key=f"btn_approve_{question.get('question_id')}", width="stretch"):
                on_verify(question.get('question_id'), "approved", current_data)
                
        with col2:
            if st.button("💾 保存修改", key=f"btn_save_{question.get('question_id')}", width="stretch"):
                on_verify(question.get('question_id'), "modified", current_data)
                
        with col3:
            if st.button("🗑️ 废弃", key=f"btn_reject_{question.get('question_id')}", width="stretch"):
                on_verify(question.get('question_id'), "rejected", None)
