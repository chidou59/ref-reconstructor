"""
文件路径: web_app/views_components.py
功能: 存放通用的 UI 组件，如页脚、公共样式等。
"""

import streamlit as st
import textwrap
from . import styles

def render_footer():
    """渲染公共页脚"""
    footer_html = textwrap.dedent(f"""
        <div class="footer-container">
            <div class="author-block">
                <!-- 修改点：更新了跳转链接 -->
                <a href="http://139.224.11.20:3000/" target="_blank" style="text-decoration: none; cursor: pointer; display: flex; align-items: center;">
                    {styles.AUTHOR_LOGO_HTML}
                </a>
                <div class="author-info">
                    <div class="author-name">Designed by 小白元宵</div>
                    <div class="social-links" style="font-size: 0.75rem; color: #718096; margin-top: 2px;"> < 点击头像 探索更多精彩</div>
                </div>
            </div>
            <div class="version-tag">
                参考文献重构大师 | Ref-Reconstructor v6.4 | @小白元宵
            </div>
        </div>
    """)
    st.markdown(footer_html, unsafe_allow_html=True)