"""
文件路径: web_app/styles.py
=========================================================
【功能】
定义网页版的视觉系统。
【修改记录】
- V7.5: 【修复】移动端弹窗 Z-Index 提升至最大值 (2147483647)，防止无法点击。
- V7.4: 【新增】移动端适配 (Mobile)。
=========================================================
"""

import streamlit as st
import base64
import os


def local_image_to_base64(file_path):
    """将本地图片转换为 Base64 字符串"""
    try:
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


# === 资源预加载 ===
# 这些变量将被 views.py 引用

# 1. Banner 背景
_banner_b64 = local_image_to_base64("assets/banner_bg.png")
if _banner_b64:
    BANNER_CSS = f"""
    .hero-background {{
        background-image: linear-gradient(rgba(14, 17, 23, 0.9), rgba(14, 17, 23, 0.8)), url("data:image/png;base64,{_banner_b64}");
        background-size: cover;
        background-position: center;
    }}
    """
else:
    BANNER_CSS = """
    .hero-background {
        background: linear-gradient(135deg, rgba(15, 32, 39, 0.9) 0%, rgba(32, 58, 67, 0.9) 50%, rgba(44, 83, 100, 0.9) 100%);
    }
    """

# 2. 作者 Logo
_author_logo_b64 = local_image_to_base64("assets/本人logo.png")
AUTHOR_LOGO_HTML = ""
if _author_logo_b64:
    AUTHOR_LOGO_HTML = f"""<img src="data:image/png;base64,{_author_logo_b64}" class="author-avatar">"""
else:
    AUTHOR_LOGO_HTML = """<div class="author-avatar" style="display:flex;align-items:center;justify-content:center;background:#2D3748;color:white;font-weight:bold;">元宵</div>"""


def inject_custom_css():
    """注入全局 CSS 样式"""
    st.markdown(f"""
<style>
    /* ========== 🚀 核心优化：字体栈 (解决大陆加载慢) ========== */
    .stApp {{
        background: linear-gradient(135deg, #0E1117 0%, #1A1F2E 50%, #0E1117 100%);
        background-attachment: fixed;
        color: #E0E0E0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
    }}

    .stApp::before {{
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 20% 50%, rgba(99, 179, 237, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(16, 185, 129, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(139, 92, 246, 0.03) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }}

    h1, h2, h3 {{ 
        font-family: "Noto Serif SC", "Songti SC", "SimSun", serif !important; 
        color: #F8F9FA !important; 
    }}

    /* ========== 修复全局输入框 (解决验证码白底白字问题) ========== */
    .stTextInput > div > div > input {{
        color: #E2E8F0 !important;
        background-color: #0D1117 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 6px !important;
        caret-color: #63B3ED !important;
    }}

    .stTextInput > div > div > input:focus {{
        border-color: #63B3ED !important;
        background-color: #161B22 !important;
        box-shadow: 0 0 0 1px #63B3ED !important;
    }}

    .stTextInput input::placeholder {{
        color: #6E7681 !important;
        opacity: 1;
    }}

    /* ========== 🔄 新增：量子加载动画 (Quantum Spinner) ========== */
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    @keyframes pulse-glow {{
        0% {{ box-shadow: 0 0 0 0 rgba(99, 179, 237, 0.4); }}
        70% {{ box-shadow: 0 0 0 10px rgba(99, 179, 237, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(99, 179, 237, 0); }}
    }}

    .loader-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 2rem;
    }}

    .quantum-spinner {{
        width: 50px;
        height: 50px;
        border: 3px solid rgba(99, 179, 237, 0.1);
        border-radius: 50%;
        border-top-color: #63B3ED;
        animation: spin 1s ease-in-out infinite, pulse-glow 2s infinite;
        margin-bottom: 1rem;
    }}

    .loader-text {{
        font-size: 1rem;
        color: #A0AEC0;
        letter-spacing: 0.05em;
        font-weight: 500;
    }}

    /* ========== 动画系统 (Animation) ========== */
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .fade-in-up {{
        animation: fadeInUp 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
    }}

    @keyframes pulse-border {{
        0% {{ 
            border-color: rgba(99, 179, 237, 0.4); 
            box-shadow: 0 0 0 0 rgba(99, 179, 237, 0); 
        }}
        50% {{ 
            border-color: rgba(99, 179, 237, 0.7); 
            box-shadow: 0 0 20px 0 rgba(99, 179, 237, 0.3); 
        }}
        100% {{ 
            border-color: rgba(99, 179, 237, 0.4); 
            box-shadow: 0 0 0 0 rgba(99, 179, 237, 0); 
        }}
    }}

    ::selection {{
        background: rgba(64, 158, 255, 0.3);
        color: #fff;
    }}

    p, label, li, span {{ color: #CBD5E0 !important; }}

    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{ padding-top: 1rem; padding-bottom: 2rem; max_width: 1100px; }}

    ::-webkit-scrollbar {{ width: 8px; background: #0E1117; }}
    ::-webkit-scrollbar-thumb {{ background: #2D3748; border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #4A5568; }}

    /* ========== Hero 区域 ========== */
    .hero-container {{
        padding: 3rem 2rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 2rem;
        text-align: center;
        border-radius: 20px;
        box-shadow: 
            0 8px 32px rgba(0,0,0,0.3),
            0 0 0 1px rgba(255,255,255,0.05) inset,
            0 2px 8px rgba(99, 179, 237, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    }}

    .hero-container::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(99, 179, 237, 0.5), transparent);
        animation: shimmer 3s ease-in-out infinite;
    }}

    @keyframes shimmer {{
        0% {{ transform: translateX(-100%); }}
        100% {{ transform: translateX(100%); }}
    }}
    {BANNER_CSS}

    .hero-title {{
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, #CBD5E0 50%, #A0AEC0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.8rem;
        letter-spacing: 0.02em;
        text-shadow: 0 4px 20px rgba(255,255,255,0.1);
        position: relative;
    }}

    .hero-subtitle {{
        font-size: 1rem;
        color: #CBD5E0;
        line-height: 1.6;
        max-width: 650px;
        margin: 0 auto;
        opacity: 0.9;
        text-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}

    /* ========== 参数面板 (Params Box) ========== */
    .params-header {{
        font-size: 1.1rem;
        font-weight: 600;
        color: #fff;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }}

    .stToggle {{
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
    }}

    .stToggle label {{ 
        font-size: 0.95rem; 
        font-weight: 500;
        color: #E2E8F0 !important;
    }}

    .setting-desc {{
        font-size: 0.75rem;
        color: #718096 !important;
        margin-top: -16px !important; 
        margin-bottom: 14px !important; 
        line-height: 1.4;
        margin-left: 2px;
        position: relative;
        z-index: 1;
    }}

    /* ========== 上传区域 (Compact Workbench) ========== */
    [data-testid="stFileUploader"] {{
        padding: 2rem 1rem;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0.01) 100%);
        border: 2px dashed rgba(99, 179, 237, 0.4);
        border-radius: 16px;
        text-align: center;
        animation: pulse-border 3s infinite;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }}

    [data-testid="stFileUploader"]:hover {{
        border-color: rgba(99, 179, 237, 0.6);
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.02) 100%);
        box-shadow: 0 4px 20px rgba(99, 179, 237, 0.15);
    }}

    [data-testid="stFileUploader"] button {{
        background: linear-gradient(135deg, #3182CE 0%, #2B6CB0 100%) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        transition: all 0.3s ease;
        font-weight: 600;
    }}

    [data-testid="stFileUploader"] button:hover {{
        background: linear-gradient(135deg, #4299E1 0%, #3182CE 100%) !important;
        border-color: #63B3ED !important;
        box-shadow: 0 4px 12px rgba(49, 130, 206, 0.4);
    }}

    [data-testid="stFileUploaderFile"] {{
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        margin-top: 10px;
        color: #E2E8F0 !important;
    }}

    [data-testid="stFileUploaderFile"] div, 
    [data-testid="stFileUploaderFile"] span,
    [data-testid="stFileUploaderFile"] small {{
        color: #E2E8F0 !important;
    }}

    [data-testid="stFileUploaderFile"] button {{
        width: auto !important;
        height: auto !important;
        line-height: 1 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #A0AEC0 !important;
        padding: 4px 8px !important;
        margin: 0 !important;
    }}

    [data-testid="stFileUploaderFile"] button:hover {{
        background: rgba(255, 255, 255, 0.1) !important;
        color: #FC8181 !important;
        transform: none !important;
        box-shadow: none !important;
    }}

    [data-testid="stFileUploaderFile"] button::before {{
        display: none !important;
    }}

    [data-testid="stFileUploaderFile"] svg {{
        width: 1.2rem !important;
        height: 1.2rem !important;
        color: inherit !important;
    }}

    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploader"] div {{
        background-color: transparent !important;
    }}

    [data-testid="stFileUploader"] section {{ padding: 0; }}
    [data-testid="stFileUploader"] small {{ display: none; }}

    [data-testid="stFileUploader"] > div:first-child svg {{
        color: #63B3ED !important;
        width: 3rem !important;
        height: 3rem !important;
    }}

    /* ========== 核心亮点卡片 (Mini) ========== */
    .feature-row {{
        display: flex; 
        gap: 1rem; 
        margin-top: 1rem;
    }}

    .feature-card-mini {{
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem 1rem;
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }}

    .feature-card-mini:hover {{
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.04) 100%);
        transform: translateY(-4px) scale(1.02);
        border-color: rgba(99, 179, 237, 0.3);
        box-shadow: 
            0 8px 24px rgba(0,0,0,0.2),
            0 0 0 1px rgba(99, 179, 237, 0.2) inset,
            0 0 20px rgba(99, 179, 237, 0.1);
    }}

    .feature-icon-large {{
        position: absolute;
        left: -15px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 6rem;
        line-height: 1;
        opacity: 0.35;
        pointer-events: none;
        z-index: 0;
        -webkit-mask-image: linear-gradient(to right, rgba(0,0,0,1) 20%, rgba(0,0,0,0) 100%);
        mask-image: linear-gradient(to right, rgba(0,0,0,1) 20%, rgba(0,0,0,0) 100%);
    }}

    .feature-text-box {{
        position: relative;
        z-index: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-align: center;
        width: 65%;
    }}

    .feature-title-mini {{
        font-size: 0.95rem; 
        font-weight: 700; 
        color: #E2E8F0; 
        margin: 0 0 0.2rem 0;
        letter-spacing: 0.02em;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }}

    .feature-desc-mini {{ 
        font-size: 0.75rem; 
        color: #94A3B8 !important; 
        line-height: 1.4; 
    }}

    /* ========== 结果页数据看板 (Glass Card) ========== */
    .glass-card {{
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.02) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.2),
            0 0 0 1px rgba(255,255,255,0.05) inset;
        position: relative;
        overflow: hidden;
    }}

    .glass-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    }}

    .metric-box {{
        text-align: center;
        padding: 0.5rem;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }}

    .metric-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: #fff;
        font-family: 'Noto Serif SC', serif;
    }}

    .metric-label {{
        font-size: 0.85rem;
        color: #A0AEC0;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* ========== Action Bar ========== */
    .action-bar-container {{
        background: linear-gradient(135deg, rgba(49, 130, 206, 0.15) 0%, rgba(30, 41, 59, 0.6) 100%);
        border: 1px solid rgba(49, 130, 206, 0.3);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-top: 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 
            0 4px 16px rgba(49, 130, 206, 0.2),
            0 0 0 1px rgba(255,255,255,0.05) inset;
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        transition: all 0.3s ease;
    }}

    .action-bar-container:hover {{
        border-color: rgba(49, 130, 206, 0.5);
        box-shadow: 
            0 6px 20px rgba(49, 130, 206, 0.3),
            0 0 0 1px rgba(255,255,255,0.1) inset;
    }}

    /* ========== 按钮样式 (修复高度) ========== */
    .stButton > button, 
    .stDownloadButton > button {{
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0 1rem; 
        transition: all 0.2s;
        height: 3rem !important; 
        line-height: 3rem !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    div.stButton > button {{
        background: linear-gradient(135deg, #3182CE 0%, #2B6CB0 100%);
        color: white !important;
        box-shadow: 
            0 4px 16px rgba(49, 130, 206, 0.4),
            0 0 0 1px rgba(255,255,255,0.1) inset;
        position: relative;
        overflow: hidden;
    }}

    div.stButton > button::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }}

    div.stButton > button:hover::before {{
        left: 100%;
    }}

    div.stButton > button:hover {{
        background: linear-gradient(135deg, #4299E1 0%, #3182CE 100%);
        transform: translateY(-2px);
        box-shadow: 
            0 8px 24px rgba(49, 130, 206, 0.5),
            0 0 0 1px rgba(255,255,255,0.2) inset;
    }}

    div.stButton > button:active {{
        transform: translateY(0);
    }}

    .stDownloadButton > button {{
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        box-shadow: 
            0 4px 16px rgba(16, 185, 129, 0.4),
            0 0 0 1px rgba(255,255,255,0.1) inset !important;
        border: none !important;
        outline: none !important;
        position: relative;
        overflow: hidden;
    }}

    .stDownloadButton > button::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }}

    .stDownloadButton > button:hover::before {{
        left: 100%;
    }}

    .stDownloadButton > button:hover {{
        background: linear-gradient(135deg, #34D399 0%, #10B981 100%) !important;
        transform: translateY(-2px);
        box-shadow: 
            0 8px 24px rgba(16, 185, 129, 0.5),
            0 0 0 1px rgba(255,255,255,0.2) inset !important;
    }}

    .stDownloadButton > button:focus {{
        border: none !important;
        outline: none !important;
    }}

    .stDownloadButton > button:active {{
        transform: translateY(0);
    }}

    /* ========== Footer ========== */
    .footer-container {{
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid rgba(255,255,255,0.05);
        text-align: center;
        color: #718096;
    }}
    .author-block {{
        display: inline-flex;
        align-items: center;
        gap: 12px;
        background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
        padding: 8px 20px;
        border-radius: 50px;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }}

    .author-block:hover {{
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.04) 100%);
        border-color: rgba(99, 179, 237, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }}

    .author-avatar {{ 
        width: 36px; 
        height: 36px; 
        border-radius: 50%;
        border: 2px solid rgba(255,255,255,0.2);
        object-fit: cover;
        transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
    }}

    .author-avatar:hover {{
        transform: rotate(360deg) scale(1.1);
        border-color: #63B3ED;
        box-shadow: 0 0 12px rgba(99, 179, 237, 0.5);
        cursor: pointer;
    }}

    .author-name {{ font-size: 1 rem; font-weight: 600; color: #E2E8F0; }}
    .version-tag {{
        margin-top: 0.5rem;
        font-size: 0.7rem;
        color: #4A5568;
        font-family: monospace;
        letter-spacing: 1px;
    }}
    .feature-section-title {{
        text-align: center;
        margin-top: 2.5rem;
        margin-bottom: 0.8rem;
        font-size: 1.1rem;
        font-weight: 700;
        color: #A0AEC0;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        position: relative;
        display: inline-block;
        width: 100%;
    }}
    .feature-section-title::after {{
        content: '';
        display: block;
        width: 30px;
        height: 2px;
        background: #63B3ED;
        margin: 6px auto 0;
        border-radius: 2px;
        opacity: 0.6;
    }}

    /* ========== 修复 st.expander (折叠面板) 在浅色模式下的显示问题 ========== */
    div[data-testid="stExpander"] details {{
        background-color: #171923 !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #E2E8F0 !important;
    }}

    div[data-testid="stExpander"] summary {{
        background-color: #171923 !important;
        color: #E2E8F0 !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }}

    div[data-testid="stExpander"] summary:hover {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #63B3ED !important;
    }}

    div[data-testid="stExpander"] summary svg {{
        fill: #A0AEC0 !important;
    }}
    div[data-testid="stExpander"] summary:hover svg {{
        fill: #63B3ED !important;
    }}

    div[data-testid="stExpander"] div[data-testid="stExpanderContent"] {{
        color: #CBD5E0 !important;
    }}

    /* ========== 📱 移动端适配 (Mobile Responsive) ========== */

    @media (max-width: 768px) {{
        .feature-row {{
            flex-direction: column !important;
            gap: 1.2rem !important;
        }}

        .feature-card-mini {{
            margin-bottom: 0.5rem;
            width: 100% !important;
        }}

        .hero-title {{
            font-size: 1.8rem !important;
        }}
        .hero-subtitle {{
            font-size: 0.9rem !important;
        }}

        /* 【修复】强制显示弹窗
           注意：这里虽然有 !important，但我们在 JS 中使用了 element.remove()，
           元素被移除后，这条规则将不再生效，从而完美解决无法关闭的问题。
        */
        #mobile-warning-overlay {{
            display: flex !important;
        }}
    }}

    /* 电脑端默认隐藏弹窗 */
    #mobile-warning-overlay {{
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.85);

        /* 【关键修复】将 Z-Index 提升到最大值 (2^31 - 1) */
        z-index: 2147483647 !important;

        justify-content: center;
        align-items: center;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }}

    #mobile-warning-box {{
        background: #1A202C;
        border: 1px solid rgba(99, 179, 237, 0.3);
        border-radius: 16px;
        padding: 2rem;
        width: 85%;
        max-width: 320px;
        text-align: center;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }}

    .mw-title {{
        font-size: 1.2rem;
        font-weight: bold;
        color: #E2E8F0;
        margin-bottom: 1rem;
        font-family: "Noto Serif SC", serif;
    }}

    .mw-desc {{
        font-size: 0.9rem;
        color: #A0AEC0;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }}

    .mw-btn {{
        background: linear-gradient(135deg, #3182CE 0%, #2B6CB0 100%);
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 8px;
        font-size: 0.95rem;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.2s;
        width: 100%;
    }}

    .mw-btn:active {{
        transform: scale(0.95);
    }}

</style>
""", unsafe_allow_html=True)