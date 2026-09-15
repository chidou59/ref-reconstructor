"""
文件路径: engines/config.py
=========================================================
【功能】
格式化引擎的全局配置文件。
迁移自原 Ref-Brusher 项目，用于控制 API 开关和搜索策略。
=========================================================
"""

import os

# === 1. 全局身份标识 (防封号第一步: 礼貌) ===
APP_NAME = "Ref-Reconstructor/2.0"
CONTACT_EMAIL = os.getenv("REF_RECONSTRUCTOR_CONTACT_EMAIL", "developer@example.com")
USER_AGENT = f"{APP_NAME} (mailto:{CONTACT_EMAIL})"

# === 2. 网络请求与安全设置 ===
TIMEOUT = 15  # 单个请求超时时间 (秒)
MAX_RETRIES = 2  # 请求失败后的重试次数
MIN_REQUEST_INTERVAL = 1.0  # 请求冷却时间


# === 3. 数据源配置 ===
class SourceConfig:
    """
    管理各个 API 数据源的开关。
    """
    # 【核心】OpenAlex: 极其全面，免费
    OPENALEX_ENABLED = True
    OPENALEX_API_URL = "https://api.openalex.org/works"

    # Crossref: 英文 DOI 官方，数据最准
    CROSSREF_ENABLED = True
    CROSSREF_API_URL = "https://api.crossref.org/works"

    # Semantic Scholar: AI 驱动，质量高
    S2_ENABLED = True
    S2_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

    # DBLP & PubMed (如有需要可后续开启)
    DBLP_ENABLED = True
    PUBMED_ENABLED = True

    # 中文源 (暂未迁移 CNKI 爬虫，保持纯净版，后续可加)
    CNKI_ENABLED = False


# === 4. 格式化标准 ===
DEFAULT_STYLE = "gbt7714-2015"
