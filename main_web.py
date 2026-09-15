"""
文件路径: main_web.py
=========================================================
【旗舰版 UI】参考文献重构大师 网页入口
版本: v11.2 (Fix HTML Code Block Rendering)
说明:
1. 【关键修复】解决了弹窗按钮显示为“代码块”的问题。
   原理：引入 re 模块，使用正则 (^\s+) 暴力清除 HTML 字符串中每一行的行首缩进。
   效果：无论代码里缩进多深，传给 st.markdown 时都是顶格的，杜绝 Markdown 代码块误判。
2. 保持 v11.0 的纯 CSS 状态机逻辑 (Checkbox Hack)，确保弹窗能关掉且不报错。
=========================================================
"""

import streamlit as st
import time
import sys
import streamlit.components.v1 as components
import textwrap
import re  # <--- 新增核心模块，用于清除缩进

# === 1. 页面配置 (必须在第一行) ===
st.set_page_config(
    page_title="参考文献重构大师",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === 2. 快速导入样式模块 ===
from web_app import styles

# 注入 CSS
styles.inject_custom_css()


# === 3. 【V11.2 扁平化修复版】移动端警告弹窗 ===
def show_mobile_warning():
    """
    完全不依赖 JS 的弹窗方案 (纯 CSS Checkbox Hack)。
    【V11.2 修复】使用 re.sub 去除每一行的前导空格，防止 Markdown 渲染成代码块。
    """

    # 原始 HTML 字符串 (保持缩进以便于阅读和维护)
    raw_html = """
    <!-- 1. 状态控制器：一个隐藏的复选框 -->
    <input type="checkbox" id="mw-toggle-state" class="mw-state-checkbox">

    <!-- 2. 弹窗主体 -->
    <div class="mw-overlay">
        <div class="mw-card">
            <div style="font-size: 3rem; margin-bottom: 10px;">💻</div>
            <div class="mw-header">推荐使用电脑访问</div>
            <div class="mw-text">
                检测到小屏幕设备。<br>
                为了获得最佳的排版与交互体验，建议使用 PC 浏览器。
            </div>

            <!-- 3. 关闭按钮：Label 关联 Checkbox -->
            <label for="mw-toggle-state" class="mw-close-btn">
                我已知晓，继续访问
            </label>
        </div>
    </div>

    <style>
    /* === 基础隐藏逻辑 === */
    .mw-state-checkbox { display: none; }
    .mw-overlay { display: none; }

    /* === 核心：手机端触发显示 === */
    @media only screen and (max-width: 900px) {
        .mw-overlay {
            display: flex !important;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(0, 0, 0, 0.9);
            z-index: 2147483647;
            justify-content: center;
            align-items: center;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }
    }

    /* === 核心：关闭逻辑 (Checkbox Hack) === */
    /* 选中复选框后，隐藏后面的遮罩层 */
    .mw-state-checkbox:checked ~ .mw-overlay {
        display: none !important;
    }

    /* === 弹窗样式 === */
    .mw-card {
        background: #1A202C;
        border: 1px solid rgba(99, 179, 237, 0.3);
        border-radius: 16px;
        padding: 2rem;
        width: 85%;
        max-width: 320px;
        text-align: center;
        box-shadow: 0 10px 40px rgba(0,0,0,0.8);
        animation: mw-fadeIn 0.3s ease-out;
    }

    .mw-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #E2E8F0;
        margin-bottom: 1rem;
        font-family: sans-serif;
    }

    .mw-text {
        font-size: 0.95rem;
        color: #A0AEC0;
        margin-bottom: 2rem;
        line-height: 1.6;
    }

    /* 按钮样式：确保它看起来像个按钮，而不是文本 */
    .mw-close-btn {
        display: block;
        background: linear-gradient(135deg, #3182CE 0%, #2B6CB0 100%);
        color: white;
        text-align: center;
        padding: 0.8rem 0;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        user-select: none;
        box-shadow: 0 4px 15px rgba(49, 130, 206, 0.4);
        transition: transform 0.1s;
    }
    .mw-close-btn:active { transform: scale(0.98); }

    @keyframes mw-fadeIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
    }
    </style>

    <!-- 辅助 JS：记录状态 (即使 JS 挂了，上面的 CSS 关闭功能依然有效) -->
    <script>
    (function() {
        try {
            var checkbox = document.getElementById('mw-toggle-state');
            var KEY = 'mw_closed_v11';

            if (sessionStorage.getItem(KEY) === 'true') {
                if(checkbox) checkbox.checked = true;
            }

            if(checkbox) {
                checkbox.addEventListener('change', function() {
                    if (this.checked) {
                        sessionStorage.setItem(KEY, 'true');
                    }
                });
            }
        } catch(e) {}
    })();
    </script>
    """

    # 【核心修复】暴力清除每一行的行首空格
    # flags=re.MULTILINE 让 ^ 匹配每一行的开头
    flat_html = re.sub(r'^\s+', '', raw_html, flags=re.MULTILINE)

    # 直接注入到主页面
    st.markdown(flat_html, unsafe_allow_html=True)


# 立即调用以注入弹窗结构
show_mobile_warning()


# === 4. 定义加载页逻辑 (接收 container 参数) ===
def show_loading_animation(container):
    """
    显示全屏加载动画，并分步预加载核心模块。
    :param container: 外部传入的 st.empty() 占位符对象
    """

    # 定义更新状态的辅助函数
    def update_status(text):
        container.markdown(f"""
            <div style="
                display: flex; 
                flex-direction: column; 
                justify-content: center; 
                align-items: center; 
                height: 70vh; 
                width: 100%;
            ">
                <div class="quantum-spinner" style="width: 60px; height: 60px; margin-bottom: 20px;"></div>
                <div style="
                    font-size: 1.2rem; 
                    font-weight: bold; 
                    color: #63B3ED; 
                    animation: pulse-glow 2s infinite;
                    font-family: 'Noto Serif SC', serif;
                ">
                    {text}
                </div>
                <div style="
                    margin-top: 10px; 
                    color: #718096; 
                    font-size: 0.9rem;
                ">
                    首次加载可能需要 10-20 秒，系统正在唤醒 AI 引擎...
                </div>
            </div>
        """, unsafe_allow_html=True)

    try:
        # 初始状态
        update_status("正在初始化系统环境...")
        time.sleep(0.1)

        # 阶段 1: 基础工具
        update_status("正在加载文档解析器 (DocParser)...")
        import core.doc_parser
        import core.citation_mapper

        # 阶段 2: AI 引擎
        update_status("正在连接 AI 知识库 (Crossref/OpenAlex)...")
        import engines.orchestrator
        import engines.formatter

        # 阶段 3: 业务逻辑
        update_status("正在渲染用户界面...")
        import web_app.logic

        time.sleep(0.5)

    except Exception as e:
        container.error(f"系统启动失败: {e}")
        st.stop()

    # 动画结束后清空容器
    container.empty()


# === 5. 主程序入口 (核心修复点) ===

# 初始化 Session State
if 'first_load_done' not in st.session_state:
    st.session_state['first_load_done'] = False

# 【关键修复】
# 无论是否首次加载，都在这里先创建一个占位符。
animation_placeholder = st.empty()

if not st.session_state['first_load_done']:
    # 将占位符传给动画函数
    show_loading_animation(animation_placeholder)
    st.session_state['first_load_done'] = True
else:
    # 如果不是首次加载，确保这个占位符是空的，不占位置，但它在逻辑上必须存在
    animation_placeholder.empty()

# === 6. 正式加载应用视图 ===
from web_app import views

# 状态初始化
if 'page_state' not in st.session_state:
    st.session_state['page_state'] = 'upload'
if 'config' not in st.session_state:
    st.session_state['config'] = {}
if 'process_stats' not in st.session_state:
    st.session_state['process_stats'] = {}

# 路由分发
if st.session_state['page_state'] == 'upload':
    views.view_upload()
elif st.session_state['page_state'] == 'processing':
    views.view_processing()
elif st.session_state['page_state'] == 'result':
    views.view_result()


# === 7. 网站统计模块 (51.LA) ===
def add_51la_tracker():
    try:
        # 這是你的 51.LA 代码
        tracker_code = """
        <script charset="UTF-8" id="LA_COLLECT" src="//sdk.51.la/js-sdk-pro.min.js"></script>
        <script>LA.init({id:"3OvoBJNYFlTJB494",ck:"3OvoBJNYFlTJB494",autoTrack:true})</script>
        """

        # 将代码嵌入页面，height=0 让它不可见
        components.html(tracker_code, height=0, width=0)
    except Exception:
        pass


# 执行统计
add_51la_tracker()