"""
文件路径: web_app/views_result.py
【更新】
- 简化报告逻辑：移除独立的“AI 审慎放弃”卡片。
- 将 AI 放弃的文献统一归入“检索失败”类别。
- 在“文献检索质量”卡片中列出具体失败的序号，方便用户手动定位修改。
"""

import streamlit as st
import os
import time
import base64
import streamlit.components.v1 as components
from .views_components import render_footer


@st.dialog("🔐 获取下载验证码")
def show_verification_modal(qr_img_data):
    st.markdown(
        """<style>div[role="dialog"] {background-color: #1A202C !important;border: 1px solid rgba(255,255,255,0.1) !important;box-shadow: 0 10px 40px rgba(0,0,0,0.5) !important;color: #E2E8F0 !important;}div[role="dialog"] h2 {color: #E2E8F0 !important;}div[role="dialog"] .stTextInput input {background-color: rgba(255,255,255,0.05) !important;color: white !important;border-color: rgba(255,255,255,0.1) !important;}div[role="dialog"] .stTextInput input:focus {border-color: #63B3ED !important;box-shadow: 0 0 0 1px #63B3ED !important;}div[role="dialog"] button[aria-label="Close"] {color: #A0AEC0 !important;}</style>""",
        unsafe_allow_html=True)
    st.markdown(
        """<div style="text-align: center; margin-bottom: 10px;"><p style="color: #E2E8F0; font-size: 0.95rem;">请扫描下方二维码或搜索关注公众号<br><b style="color: #63B3ED; font-size: 1.1em;">【小白元宵】</b></p><p style="color: #A0AEC0; font-size: 0.85rem;">回复 <b style="color: #F6AD55;">“验证码”</b> 获取下载解锁口令</p></div>""",
        unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if qr_img_data:
            st.image(qr_img_data, width=200, use_container_width=False)
        else:
            st.error("⚠️ 二维码加载失败")
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("verify_form", border=False):
        code = st.text_input("请输入验证码", placeholder="请输入4位验证码", help="不区分大小写")
        if st.form_submit_button("立即解锁", type="primary", use_container_width=True):
            if code.strip().lower() == "xbyx":
                st.session_state['download_verified'] = True
                st.session_state['trigger_balloons'] = True
                st.session_state['auto_download_trigger'] = True
                st.success("验证成功！即将开始下载...")
                time.sleep(0.8)
                st.rerun()
            else:
                st.error("❌ 验证码错误")


def view_result():
    """视图：结果展示"""
    st.markdown(
        """<style>div.stButton > button, div.stDownloadButton > button {height: 3.5rem !important; line-height: 1 !important;}</style>""",
        unsafe_allow_html=True)
    stats = st.session_state.get('process_stats', {})
    output_path = st.session_state.get('output_file')
    config = st.session_state.get('config', {})
    qr_code_path = "assets/公众号二维码.jpg"
    qr_data = None
    if os.path.exists(qr_code_path):
        with open(qr_code_path, "rb") as f: qr_data = f.read()

    file_bytes = None
    if output_path and os.path.exists(output_path):
        with open(output_path, "rb") as f:
            file_bytes = f.read()

    if st.session_state.get('auto_download_trigger', False) and file_bytes:
        b64 = base64.b64encode(file_bytes).decode()
        file_name = f"Result_{int(time.time())}.docx"
        download_html = f"""<html><body><a id="auto_download_link" href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="{file_name}" style="display:none;">Download</a><script>document.getElementById('auto_download_link').click();</script></body></html>"""
        components.html(download_html, height=0)
        st.session_state['auto_download_trigger'] = False

    if st.session_state.get('trigger_balloons', False):
        st.balloons();
        st.session_state['trigger_balloons'] = False

    st.markdown(
        """<div class="hero-container" style="background: rgba(47, 133, 90, 0.15); border: 1px solid rgba(72, 187, 120, 0.3); padding: 2.5rem 2rem;"><div style="font-size: 2.5rem; color: #68D391; font-weight: bold; margin-bottom: 0.5rem;">重构完成</div><div style="color: #9AE6B4;">文档已更新。若后续删改了段落，请在 Word 中“全选 -> 右键 -> 更新域”即可自动规整。</div></div>""",
        unsafe_allow_html=True)

    c_cnt, b_cnt = stats.get('citations', 0), stats.get('bibs', 0)
    cl_val = str(stats.get('cleaned', 0)) if config.get('use_gb_format') else "-"
    m_val = str(stats.get('merged', 0)) if config.get('merge_duplicates') else "-"

    st.markdown(f"""
        <div class="glass-card fade-in-up" style="display: flex; padding: 1rem 0; margin: 20px 0;">
            <div style="flex:1; text-align:center; border-right:1px solid rgba(255,255,255,0.1);"><div style="font-size:2rem; color:#63B3ED;">{c_cnt}</div><div style="font-size:0.8rem; color:#A0AEC0;">正文引用</div></div>
            <div style="flex:1; text-align:center; border-right:1px solid rgba(255,255,255,0.1);"><div style="font-size:2rem; color:#F6AD55;">{b_cnt}</div><div style="font-size:0.8rem; color:#A0AEC0;">文末文献</div></div>
            <div style="flex:1; text-align:center; border-right:1px solid rgba(255,255,255,0.1);"><div style="font-size:2rem; color:#68D391;">{cl_val}</div><div style="font-size:0.8rem; color:#A0AEC0;">国标清洗</div></div>
            <div style="flex:1; text-align:center;"><div style="font-size:2rem; color:#F687B3;">{m_val}</div><div style="font-size:0.8rem; color:#A0AEC0;">合并去重</div></div>
        </div>
    """, unsafe_allow_html=True)

    show_health_report = False
    failed_list = stats.get('failed_cleaning_indices', [])
    # 移除 ai_aborted 的单独获取，因为它们已经包含在 failed_list 里了

    if (config.get('use_gb_format') and failed_list) or \
            stats.get('missing_ids') or \
            stats.get('unused_ids') or \
            stats.get('ai_filled', 0) > 0:
        show_health_report = True

    if show_health_report:
        with st.expander("🔍 文档健康度体检报告", expanded=True):
            st.markdown("""
            <style>
            .report-card {background: rgba(49, 130, 206, 0.08); border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; border: 1px solid rgba(255, 255, 255, 0.08); transition: all 0.3s ease; backdrop-filter: blur(5px);}
            .report-card:hover {background: rgba(49, 130, 206, 0.12); border-color: rgba(99, 179, 237, 0.3);}
            .report-header {display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;}
            .report-title {font-weight: 600; font-size: 0.95rem; color: #E2E8F0; display: flex; align-items: center; gap: 8px;}
            .report-summary {font-size: 0.9rem; color: #A0AEC0; line-height: 1.5;}
            .report-details {margin-top: 10px; padding-top: 8px; border-top: 1px dashed rgba(255, 255, 255, 0.1); font-size: 0.85rem; font-family: Consolas, "Liberation Mono", monospace; color: #F6AD55; word-wrap: break-word; white-space: pre-wrap;}
            .status-badge {font-size: 0.75rem; padding: 2px 8px; border-radius: 12px; font-weight: bold; letter-spacing: 0.05em;}
            .status-success { background: rgba(72, 187, 120, 0.15); color: #68D391; border: 1px solid rgba(72, 187, 120, 0.3); }
            .status-warning { background: rgba(237, 137, 54, 0.15); color: #F6AD55; border: 1px solid rgba(237, 137, 54, 0.3); }
            .status-notice  { background: rgba(237, 137, 54, 0.15); color: #F6AD55; border: 1px solid rgba(237, 137, 54, 0.3); }
            </style>
            """, unsafe_allow_html=True)

            def render_card(title, status, summary, details_list=None):
                status_class = f"status-{status}"
                icon = "✅" if status == "success" else "⚠️" if status in ["warning", "notice"] else "❌"

                details_html = ""
                if details_list:
                    # 限制显示数量，防止太长
                    display_items = details_list[:15]
                    items_html = "<br>".join([f"• {item}" for item in display_items])
                    if len(details_list) > 15: items_html += f"<br>... (以及其他 {len(details_list) - 15} 项)"
                    details_html = f'<div class="report-details">{items_html}</div>'

                st.markdown(f"""
                <div class="report-card">
                    <div class="report-header">
                        <div class="report-title">{icon} {title}</div>
                        <div class="status-badge {status_class}">{status.upper()}</div>
                    </div>
                    <div class="report-summary">{summary}</div>
                    {details_html}
                </div>
                """, unsafe_allow_html=True)

            if config.get('use_gb_format'):
                total = stats.get('total_cleaning_targets', 0)
                success = stats.get('cleaned', 0)

                # 1. 总体质量 (合并了 API 失败和 AI 放弃)
                if failed_list:
                    # 排序一下序号
                    sorted_failed = sorted(list(set(failed_list)))
                    ids_str = ", ".join([f"[{i}]" for i in sorted_failed])
                    if len(ids_str) > 500: ids_str = ids_str[:500] + "..."

                    summary = f"共 {total} 条文献，<b style='color:#68D391'>{success}</b> 条清洗成功，<b style='color:#F6AD55'>{len(sorted_failed)}</b> 条检索失败。"
                    details = [
                        f"以下文献未搜索到有效信息，已保持原样，请手动检查（输出文档序号）：<br><span style='color:#E2E8F0; font-size:0.8rem'>{ids_str}</span>"]
                    render_card("文献检索质量", "notice", summary, details)
                else:
                    render_card("文献检索质量", "success", f"完美！共 {total} 条文献全部检索并清洗成功。", None)

            # ... (其他报告逻辑保持不变) ...
            missing = stats.get('missing_ids', [])
            if missing:
                summary = f"发现 <b style='color:#F6AD55'>{len(missing)}</b> 处“幽灵引用”（正文有标号，但文末无对应文献）。"
                ids_str = ", ".join([f"[{i}]" for i in missing])
                if len(ids_str) > 500: ids_str = ids_str[:500] + "..."
                details = [
                    f"以下序号正文中出现，但文献列表缺失：<br><span style='color:#E2E8F0; font-size:0.8rem'>{ids_str}</span>"]
                render_card("引用完整性", "notice", summary, details)
            else:
                render_card("引用完整性", "success", "文档引用逻辑闭环，未发现断链。", None)

            unused = stats.get('unused_ids', [])
            if unused:
                action = "已自动移除" if config.get('remove_unused') else "未移除，已放至文末（建议手动检查）"
                summary = f"发现 <b style='color:#F6AD55'>{len(unused)}</b> 条未引文献（列表有文献，但正文未引用）。状态：{action}。"
                ids_str = ", ".join([f"[{i}]" for i in unused])
                if len(ids_str) > 500: ids_str = ids_str[:500] + "..."
                details = [
                    f"以下序号存在文献中但未被引用（原文档序号）：<br><span style='color:#E2E8F0; font-size:0.8rem'>{ids_str}</span>"]
                render_card("文献利用率", "notice", summary, details)
            else:
                render_card("文献利用率", "success", "所有列出的文献均在正文中被引用。", None)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        b1, b2 = st.columns([3, 1], gap="small")
        with b1:
            if st.session_state.get('download_verified', False):
                st.download_button("📥 下载文档", data=file_bytes, file_name=f"Result_{int(time.time())}.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   type="primary", use_container_width=True)
            else:
                if st.button("🔒 下载文档", type="primary", use_container_width=True):
                    show_verification_modal(qr_data)

        with b2:
            if st.button("返回", use_container_width=True):
                st.session_state['download_verified'] = False;
                st.session_state['page_state'] = 'upload';
                st.rerun()
    render_footer()