"""
文件路径: web_app/views_processing.py
功能: 处理中页面的加载动画与逻辑调用。
【修改】引入 SecurityManager 进行 IP 溯源和文件留存。
"""

import streamlit as st
import os
import time
import tempfile
from .logic import process_core_logic
# 引入我们刚写的安全模块
from core.security import SecurityManager


def view_processing():
    """视图：处理中"""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div class="loader-container fade-in-up">
            <div class="quantum-spinner"></div>
            <div class="loader-text">AI 引擎正在重构文档，请稍候...</div>
        </div>
    """, unsafe_allow_html=True)
    status_container = st.container()
    uploaded_file = st.session_state['uploaded_file']
    config = st.session_state['config']

    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_input:
        tmp_input.write(uploaded_file.getvalue())
        tmp_input_path = tmp_input.name
    tmp_output_path = os.path.join(tempfile.gettempdir(), f"Ref_Pro_{int(time.time())}.docx")

    # 执行核心逻辑
    success, stats, logs = process_core_logic(tmp_input_path, tmp_output_path, config, status_container)

    # === 🛡️ 安全审计介入 (Security Audit) ===
    # 无论成功失败，最好都记录一下 IP，防止有人上传恶意文件攻击解析器
    try:
        security = SecurityManager(audit_dir="audit_logs")  # 目录会自动创建在项目根目录下

        if success:
            # 只有成功了才有 Output 文件
            security.log_transaction(uploaded_file, tmp_output_path, status="success")
        else:
            # 失败了只记录 Input 文件
            security.log_transaction(uploaded_file, None, status="failed")

    except Exception as e:
        print(f"Audit Error: {e}")
    # ========================================

    try:
        os.remove(tmp_input_path)
    except:
        pass

    if success:
        end_time = time.time()
        start_time = st.session_state.get('start_time', end_time)
        stats['duration'] = end_time - start_time
        st.session_state['process_stats'] = stats
        st.session_state['process_logs'] = logs
        st.session_state['output_file'] = tmp_output_path
        st.session_state['page_state'] = 'result'
        st.session_state['trigger_balloons'] = True
        st.rerun()
    else:
        error_msg = stats.get('error', '未知错误')
        st.error(f"❌ 处理过程中断: {error_msg}")
        if stats.get('error_trace'):
            with st.expander("查看详细错误信息", expanded=False): st.code(stats.get('error_trace'), language="python")
        if logs:
            with st.expander("查看处理日志", expanded=True):
                for log in logs: st.text(log)
        if st.button("返回工作台", type="primary"):
            st.session_state['page_state'] = 'upload'
            st.rerun()