"""
文件路径: web_app/views_upload.py
【更新说明】
- 预加载 airplane-tilt.svg 图标资源。
- 将“启动重构”按钮和“联网检索”加载条修改为清爽纯文字模式（移除 Rocket Emoji）。
- 简化 Spinner 提示语为“正在联网检索...”。
"""

import streamlit as st
import os
import time
import base64
import tempfile
import re
import html
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import styles
from .logic import scan_file_for_deferrable_citations
from .views_components import render_footer
from engines.orchestrator import Orchestrator


def get_svg_icon(file_path, color="#63B3ED", size="20", output_format="markdown"):
    """
    读取 SVG 文件，深度清洗并注入样式，返回用于 Markdown 或 HTML 的字符串。

    :param output_format: "markdown" (默认) 或 "html"。
                          Markdown 标题用 markdown 格式，HTML div 标题用 html 格式。
    """
    if not os.path.exists(file_path):
        return ""  # 文件不存在，返回空

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. 移除 XML 声明和 DOCTYPE
        content = re.sub(r'<\?xml.*?\?>', '', content, flags=re.DOTALL)
        content = re.sub(r'<!DOCTYPE.*?>', '', content, flags=re.DOTALL)
        content = content.strip()

        # 2. 提取 viewBox
        viewbox_match = re.search(r'viewBox\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
        viewbox_attr = f'viewBox="{viewbox_match.group(1)}"' if viewbox_match else ''

        # 3. 移除旧的 <svg ...> 标签头
        svg_tag_match = re.search(r'<svg[^>]*>', content, re.IGNORECASE)
        if not svg_tag_match:
            return ""

        body_content = content[svg_tag_match.end():]

        # 4. 构建新的 <svg> 标签
        # style="vertical-align: middle;" 保证图标与文字垂直居中
        # 增加 stroke-width 稍微加粗线条，使其在深色模式下更清晰（如果是线条型SVG）
        new_header = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'{viewbox_attr} '
            f'width="{size}" height="{size}" '
            f'fill="{color}" '
            f'style="vertical-align: middle; display: inline-block;">'
        )

        final_svg = new_header + body_content
        final_svg_clean = final_svg.replace('\n', '').replace('\r', '').strip()
        b64 = base64.b64encode(final_svg_clean.encode('utf-8')).decode('utf-8')
        src = f"data:image/svg+xml;base64,{b64}"

        # 5. 根据格式返回
        if output_format == "html":
            # 用于 st.markdown("<div...>", unsafe_allow_html=True) 场景
            # 增加 margin-right 让图标和文字有点间距，vertical-align: sub 微调对齐
            return f'<img src="{src}" width="{size}" height="{size}" style="vertical-align: text-bottom; margin-right: 8px;">'
        else:
            # 用于 st.markdown("### ...") 或 st.expander 场景
            return f"![icon]({src})"

    except Exception as e:
        print(f"SVG Icon Error: {e}")
        return ""


def view_upload():
    """视图：首页上传"""

    # === 1. 预加载并配置 SVG 图标 (视觉升级版) ===

    # [Markdown格式] 文档上传 - 尺寸放大至 30 (匹配 H3)，颜色：标准蓝 (#63B3ED)
    icon_scroll_md = get_svg_icon("assets/icons/scroll.svg", color="#63B3ED", size="30",
                                  output_format="markdown") or "📄"

    # [Markdown格式] 文献快捷刷 - 尺寸放大至 26 (匹配 Expander)，颜色：醒目金 (#ECC94B)
    icon_lightning_md = get_svg_icon("assets/icons/lightning.svg", color="#ECC94B", size="26",
                                     output_format="markdown") or "⚡"

    # [HTML格式] 核心功能 - 尺寸放大至 24，颜色：标准蓝 (#63B3ED)
    icon_toolbox_html = get_svg_icon("assets/icons/toolbox.svg", color="#63B3ED", size="24",
                                     output_format="html") or "⚙️"

    # [HTML格式] 功能亮点 - 尺寸放大至 26，颜色：醒目金 (#ECC94B)
    icon_sparkle_html = get_svg_icon("assets/icons/sparkle.svg", color="#ECC94B", size="26",
                                     output_format="html") or "✨"

    # [备用] 预加载飞机图标 (Airplane - Blue)，供后续功能使用
    # 注意：st.button 和 st.spinner 暂不支持显示 SVG，故暂未直接用于界面
    icon_airplane_md = get_svg_icon("assets/icons/airplane-tilt.svg", color="#63B3ED", size="20",
                                    output_format="markdown") or "✈️"

    st.markdown("""
        <div class="hero-container hero-background">
            <div class="hero-title">参 考 文 献 重 构 大 师</div>
            <div class="hero-subtitle">
                引用序号不再乱，国标格式一键换。<br>
                智能序号重排/国标清洗/文献体检。
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_params, col_upload = st.columns([1.1, 2.4], gap="large")

    selected_defer_indices = []
    saved_cfg = st.session_state.get('config', {})

    with col_params:
        # === 核心功能 (Toolbox - Blue) ===
        st.markdown(f'<div class="params-header">{icon_toolbox_html} 核心功能</div>', unsafe_allow_html=True)

        # === 第一类：正文索引序号 ===
        st.markdown(
            '<div style="font-weight: 700; color: #FFFFFF; margin: 2px 0 8px 0; font-size: 0.95rem;">正文索引序号</div>',
            unsafe_allow_html=True)

        _, col_g1 = st.columns([0.05, 0.95])
        with col_g1:
            sort_by_appearance = st.toggle("索引序号重排", value=saved_cfg.get('sort_by_appearance', True))
            st.markdown(
                '<div class="setting-desc">正文索引序号按阅读顺序重排，并自动对应改变参考文献顺序。<br><i>自动附带交叉引用，点击索引直达文献。</i></div>',
                unsafe_allow_html=True)

            defer_captions_mode = st.toggle("图表索引延后", value=saved_cfg.get('defer_captions_mode', False))
            st.markdown(
                """<div class="setting-desc" style="color: #F6AD55 !important;">
                开启后，可将您勾选的图表中的索引序号放在本章节正文后再编号。<br>
                <i>选择 “索引序号重排” 后该项才生效。</i>
                </div>""",
                unsafe_allow_html=True)

            defer_config_container = st.container()

            use_superscript = st.toggle("索引序号上标", value=saved_cfg.get('use_superscript', True))
            st.markdown('<div class="setting-desc">开启后，文中 [1] 自动变为上标格式 <sup>[1]</sup>。</div>',
                        unsafe_allow_html=True)

        # === 第二类：参考文献列表 ===
        st.markdown('<div style="height: 5px;"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-weight: 700; color: #FFFFFF; margin: 15px 0 10px 0; font-size: 0.95rem;">参考文献列表</div>',
            unsafe_allow_html=True)

        _, col_g2 = st.columns([0.05, 0.95])
        with col_g2:
            pdf_filename = "《参考文献著录规则》GBT7714—2015.pdf"
            pdf_link_html = "国标( <b>GB/T 7714</b> )"
            if os.path.exists(pdf_filename):
                try:
                    with open(pdf_filename, "rb") as f:
                        b64_pdf = base64.b64encode(f.read()).decode()
                    pdf_link_html = f'''
                    <a href="data:application/pdf;base64,{b64_pdf}" download="{pdf_filename}" 
                       style="color: #63B3ED; text-decoration: none; border-bottom: 1px dashed #63B3ED; transition: all 0.2s;"
                       title="点击下载 PDF 原文"
                       onmouseover="this.style.color='#90CDF4';this.style.borderBottomStyle='solid'" 
                       onmouseout="this.style.color='#63B3ED';this.style.borderBottomStyle='dashed'">
                       国标( <b>GB/T 7714</b> )
                    </a>
                    '''
                except Exception:
                    pass

            use_gb_format = st.toggle("国标格式清洗", value=saved_cfg.get('use_gb_format', False))
            st.markdown(
                f'<div class="setting-desc">联网搜索，将参考文献替换为{pdf_link_html}格式。<br><i>集成AI精准补刀，严格规则，无需担心编造。</i></div>',
                unsafe_allow_html=True)

            use_ai_fallback = use_gb_format
            merge_duplicates = st.toggle("智能文献去重", value=saved_cfg.get('merge_duplicates', True))
            st.markdown('<div class="setting-desc">自动合并相同的文献，并同步更新引用。</div>', unsafe_allow_html=True)

            remove_unused = st.toggle("移除未引文献", value=saved_cfg.get('remove_unused', False))
            st.markdown(
                '<div class="setting-desc" style="color: #F87171 !important;"><b>慎用</b>。删除参考文献存在但正文中未引用的条目。</div>',
                unsafe_allow_html=True)

        style_config = None

    with col_upload:
        # === 文档上传 (Scroll - Blue) ===
        # 使用 Markdown H3 语法，图标尺寸已在 get_svg_icon 中设为 30
        st.markdown(f"### {icon_scroll_md} 文档上传")

        uploaded_file = st.file_uploader("请拖入或选择 Word 文档", type=["docx"], label_visibility="collapsed")

        if uploaded_file and defer_captions_mode:
            cache_key = f"scan_res_v2_{uploaded_file.name}_{uploaded_file.size}"

            if 'scan_cache_key' not in st.session_state or st.session_state['scan_cache_key'] != cache_key:
                with st.spinner("正在扫描文档中的图表引用..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_scan:
                        tmp_scan.write(uploaded_file.getvalue())
                        tmp_scan_path = tmp_scan.name

                    try:
                        candidates = scan_file_for_deferrable_citations(tmp_scan_path)
                        st.session_state['scan_candidates'] = candidates
                        st.session_state['scan_cache_key'] = cache_key
                    except Exception as e:
                        st.error(f"扫描失败: {e}")
                        st.session_state['scan_candidates'] = []
                    finally:
                        try:
                            os.remove(tmp_scan_path)
                        except:
                            pass

            groups = st.session_state.get('scan_candidates', [])

            with defer_config_container:
                if not groups:
                    st.info("ℹ️ 文档中未检测到图表/表格中的引用。")
                else:
                    st.markdown("""
                    <style>
                    .stMultiSelect div[data-baseweb="tag"] span { font-size: 0.8rem !important; }
                    div[data-baseweb="popover"] li div { font-size: 0.8rem !important; font-family: 'Noto Sans SC', sans-serif !important; }
                    .stMultiSelect div[data-baseweb="select"] { font-size: 0.85rem !important; }
                    </style>
                    """, unsafe_allow_html=True)

                    with st.expander(f"选择延后目标 ({len(groups)}个对象)", expanded=True):
                        st.markdown(f"""<div style="font-size: 0.8rem; color: #A0AEC0; margin-bottom: 8px;">
                            按 <b>图表/图注</b> 分组列出。勾选后，该对象内的所有引用都将延后。
                            </div>""", unsafe_allow_html=True)
                        options_map = {g["display_label"]: g["indices"] for g in groups}
                        selected_labels = st.multiselect("选择延后项", options=list(options_map.keys()),
                                                         default=list(options_map.keys()), label_visibility="collapsed")
                        for label in selected_labels: selected_defer_indices.extend(options_map[label])

        if uploaded_file:
            st.session_state['uploaded_file'] = uploaded_file
            st.markdown(
                """<style>div[data-testid="column"] {display: flex; flex-direction: column; justify-content: center;}</style>""",
                unsafe_allow_html=True)
            col_info, col_btn = st.columns([2.8, 1.2], gap="small")
            with col_info:
                file_name = uploaded_file.name
                st.markdown(f"""
                <div class="action-bar-container fade-in-up" style="margin: 0; padding: 0.6rem 1rem;">
                    <div class="file-info" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        <span class="file-icon">✅</span>
                        <span>已就绪: <b>{file_name}</b></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                # 【修改】移除了 Rocket Emoji，使用清爽纯文字
                if st.button("启动重构", type="primary", use_container_width=True):
                    st.session_state['start_time'] = time.time()
                    st.session_state['page_state'] = 'processing'
                    st.rerun()
        else:
            st.markdown(
                "<div style='margin-top: 15px; color: #94A3B8; font-size: 0.85rem; text-align: center;'>拖入或选择 .docx 文件，系统将自动识别并重构引用。</div>",
                unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")

        # =================================================================
        # ⚡ 文献快捷刷 (Batch Mode)
        # =================================================================

        # 使用 Markdown 格式的 SVG (Lightning - Gold)
        expander_title = f"{icon_lightning_md} 文献快捷刷"

        with st.expander(expander_title, expanded=False):
            st.markdown("""
                <style>
                /* === 样式代码保持不变，省略以节省篇幅 ... === */
                div[data-testid="stExpander"] details {
                    background: linear-gradient(180deg, rgba(22, 27, 34, 0.95) 0%, rgba(13, 17, 23, 0.95) 100%) !important;
                    backdrop-filter: blur(16px);
                    border: 1px solid rgba(255, 255, 255, 0.08) !important;
                    border-radius: 12px !important;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(0,0,0,0.2) !important;
                    margin-bottom: 10px;
                }
                div[data-testid="stExpander"] summary {
                    background-color: transparent !important;
                    color: #A0AEC0 !important;
                    font-weight: 600 !important;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                    padding: 1rem 1.2rem !important;
                }
                div[data-testid="stExpander"] summary p {
                    display: flex !important;
                    align-items: center !important;
                    gap: 8px !important;
                }
                div[data-testid="stExpander"] summary img {
                    vertical-align: middle !important;
                    margin-right: 6px !important; /* 微调图标间距 */
                    transform: translateY(-1px);
                }
                div[data-testid="stExpander"] summary:hover {
                    color: #63B3ED !important;
                    background-color: rgba(255, 255, 255, 0.02) !important;
                }
                div[data-testid="stExpander"] textarea {
                    font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace !important;
                    font-size: 0.85rem !important;
                    line-height: 1.6 !important;
                    background-color: #090C10 !important;
                    border: 1px solid rgba(50, 60, 70, 0.5) !important;
                    border-radius: 6px !important;
                    color: #A0AEC0 !important;
                    caret-color: #63B3ED !important;
                    padding: 10px !important;
                }
                div[data-testid="stExpander"] textarea::placeholder {
                    color: #6E7681 !important;
                    opacity: 1;
                }
                div[data-testid="stExpander"] textarea:focus {
                    border-color: #3182CE !important;
                    background-color: #0D1117 !important;
                    color: #E2E8F0 !important;
                }
                div[data-testid="stExpander"] .stButton > button {
                    height: 38px !important;
                    line-height: 38px !important;
                    border: 1px solid rgba(99, 179, 237, 0.2) !important;
                    background: rgba(49, 130, 206, 0.1) !important;
                    color: #90CDF4 !important;
                    border-radius: 6px !important;
                    font-size: 0.9rem !important;
                }
                div[data-testid="stExpander"] .stButton > button:hover {
                    border-color: #63B3ED !important;
                    color: #FFFFFF !important;
                    background: rgba(49, 130, 206, 0.6) !important;
                }
                div[data-testid="stExpander"] [data-testid="stTabs"] button {
                    font-size: 0.8rem !important;
                    color: #718096 !important;
                }
                div[data-testid="stExpander"] [data-testid="stTabs"] button[aria-selected="true"] {
                    color: #63B3ED !important;
                    border-bottom-color: #63B3ED !important;
                }
                .results-monitor::-webkit-scrollbar { width: 4px; }
                .results-monitor::-webkit-scrollbar-thumb { background: #2D3748; border-radius: 2px; }
                .batch-section-title { font-size: 0.75rem; color: #718096; text-transform: uppercase; letter-spacing: 0.08em; margin: 10px 0 6px 0; font-weight: 600; }
                </style>
            """, unsafe_allow_html=True)

            st.markdown('<div class="batch-section-title">原始文献 INPUT</div>', unsafe_allow_html=True)
            quick_query_block = st.text_area(
                "批量引用生成",
                placeholder="在此粘贴多行文献 (支持DOI或标题，每行一条)...\n例如：\n[1] 10.1038/s41586-020-2649-2\n[2] Attention is all you need",
                height=120,
                label_visibility="collapsed"
            )

            st.markdown('<div style="height: 4px;"></div>', unsafe_allow_html=True)

            generate_btn = st.button("立即批量生成", type="secondary", use_container_width=True)

            if generate_btn and quick_query_block:
                st.session_state['batch_result_timestamp'] = str(int(time.time()))

                # 【修改】移除了 Rocket Emoji，使用清爽纯文字，并预留了 SVG 说明
                with st.spinner("正在联网检索..."):
                    orch = Orchestrator()
                    lines = quick_query_block.strip().split('\n')
                    valid_tasks = []
                    results_container = [None] * len(lines)

                    for i, line in enumerate(lines):
                        original_line = line.strip()
                        if not original_line: continue
                        match = re.match(r'^\s*(\[\d+\]|\d+\.|\d+、|\(\d+\))\s*(.*)', original_line)
                        prefix = ""
                        clean_query = original_line
                        if match:
                            prefix = match.group(1)
                            clean_query = match.group(2)
                        valid_tasks.append((i, clean_query, prefix))

                    workers = 3 if use_ai_fallback else 5

                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        future_to_info = {
                            executor.submit(orch.format_single_with_status, query, use_ai_fallback): (idx, query, pfx)
                            for idx, query, pfx in valid_tasks
                        }

                        for future in as_completed(future_to_info):
                            idx, query, prefix = future_to_info[future]
                            try:
                                formatted_content, is_success, url = future.result()
                                base_text_line = f"{prefix} {formatted_content}" if prefix else formatted_content
                                text_for_txt = base_text_line
                                if not is_success: text_for_txt += " ❌"
                                safe_text_html = html.escape(base_text_line)

                                if is_success:
                                    if url and url != "AI_ABORTED":
                                        html_line = f'<div style="margin-bottom: 12px;"><a href="{url}" target="_blank" style="color: #63B3ED; text-decoration: none; border-bottom: 1px dashed rgba(99, 179, 237, 0.4); transition: all 0.2s;" onmouseover="this.style.borderBottomStyle=\'solid\'" onmouseout="this.style.borderBottomStyle=\'dashed\'">{safe_text_html}</a></div>'
                                    else:
                                        html_line = f'<div style="margin-bottom: 12px; color:#E2E8F0;">{safe_text_html}</div>'
                                else:
                                    html_line = f'<div style="margin-bottom: 12px; color:#FC8181; opacity: 0.9;">{safe_text_html} <span style="font-size:0.8em; margin-left:5px;">(检索失败)</span></div>'

                                results_container[idx] = {"full": text_for_txt, "html": html_line}
                            except Exception:
                                results_container[idx] = {"full": f"{prefix} Error ❌",
                                                          "html": f'<div style="color:#FC8181;">{prefix} 处理异常</div>'}

                    list_with_num = []
                    list_html = []
                    for item in results_container:
                        if item:
                            list_with_num.append(item["full"])
                            list_html.append(item["html"])

                    st.session_state['batch_results'] = {
                        "with_num": "\n".join(list_with_num),
                        "display_html": "".join(list_html)
                    }

            if 'batch_results' in st.session_state and st.session_state['batch_results']:
                results = st.session_state['batch_results']
                st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
                st.markdown('<div class="batch-section-title">生成结果 OUTPUT</div>', unsafe_allow_html=True)

                # 【注意】st.tabs 不支持 SVG，保持使用纯文字
                tab_preview, tab_code = st.tabs(["直达链接", "纯文本条目"])

                with tab_preview:
                    scrollable_html_container = f"""
                    <div class="results-monitor" style="max-height: 180px; overflow-y: auto; padding: 12px; border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; background: #0D1117; color: #E2E8F0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 0.9rem; box-shadow: inset 0 2px 6px rgba(0,0,0,0.3);">
                        {results["display_html"]}
                    </div>
                    """
                    st.markdown(scrollable_html_container, unsafe_allow_html=True)
                    st.caption("点击蓝色链接可直接跳转原文")

                with tab_code:
                    dynamic_key_suffix = st.session_state.get('batch_result_timestamp', 'init')
                    st.text_area(
                        "纯文本结果",
                        value=results["with_num"],
                        height=180,
                        label_visibility="collapsed",
                        key=f"result_text_area_code_{dynamic_key_suffix}"
                    )
                    st.caption("全选 (Ctrl+A) 即可复制全部内容。注意：❌的条目表示检索失败，需手动修改。")

    config = {
        "sort_by_appearance": sort_by_appearance,
        "use_superscript": use_superscript,
        "use_gb_format": use_gb_format,
        "merge_duplicates": merge_duplicates,
        "remove_unused": remove_unused,
        "deferred_indices": selected_defer_indices if defer_captions_mode else [],
        "style": style_config,
        "use_ai_fallback": use_ai_fallback,
        "defer_captions_mode": defer_captions_mode
    }
    st.session_state['config'] = config

    # === 功能亮点 (Sparkle - Gold) ===
    st.markdown(f'<div class="feature-section-title">{icon_sparkle_html} 功能亮点</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="feature-row">
        <div class="feature-card-mini">
            <div class="feature-icon-large">⛓️</div>
            <div class="feature-text-box">
                <div class="feature-title-mini">文献顺序重排</div>
                <div class="feature-desc-mini">按照正文顺序排列文献<br>生成Word原生超链接。</div>
            </div>
        </div>
        <div class="feature-card-mini">
            <div class="feature-icon-large">🌍</div>
            <div class="feature-text-box">
                <div class="feature-title-mini">深度国标清洗</div>
                <div class="feature-desc-mini">连接 Crossref/OpenAlex<br>一键标准化为 GB/T 7714。</div>
            </div>
        </div>
        <div class="feature-card-mini">
            <div class="feature-icon-large">📊</div>
            <div class="feature-text-box">
                <div class="feature-title-mini">图表引用局部延后</div>
                <div class="feature-desc-mini">章节内的表格/图注引用<br>统一排在章节末尾编号。</div>
            </div>
        </div>
        <div class="feature-card-mini">
            <div class="feature-icon-large">✨</div>
            <div class="feature-text-box">
                <div class="feature-title-mini">智能规整美化</div>
                <div class="feature-desc-mini">合并重复文献并更新引用<br>统一引用序号为上标格式。</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    render_footer()