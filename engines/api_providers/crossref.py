"""
文件路径: engines/api_providers/crossref.py
=========================================================
Crossref 搜索引擎实现。
【更新】支持提取 article-number 字段。
=========================================================
"""
from typing import Optional
from .base_engine import BaseEngine
from ..models.citation_model import CitationData
from .. import config


class CrossrefEngine(BaseEngine):
    def __init__(self):
        super().__init__()
        self.name = "Crossref"
        self.api_url = config.SourceConfig.CROSSREF_API_URL
        self.email = config.CONTACT_EMAIL

    def get_headers(self) -> dict:
        headers = super().get_headers()
        if self.email and "example.com" not in self.email:
            headers["User-Agent"] += f" (mailto:{self.email})"
        return headers

    def search(self, query: str) -> Optional[CitationData]:
        if not config.SourceConfig.CROSSREF_ENABLED:
            return None

        is_pure_doi = "10." in query and "/" in query and " " not in query
        params = {}
        if is_pure_doi:
            clean_doi = query.strip()
            if "doi.org/" in clean_doi:
                clean_doi = clean_doi.split("doi.org/")[-1]
            params = {"query.bibliographic": clean_doi, "rows": 1}
        else:
            params = {"query.bibliographic": query, "rows": 1, "sort": "relevance"}

        data = self.safe_request(self.api_url, params)
        if not data or "message" not in data or "items" not in data["message"]:
            return None

        items = data["message"]["items"]
        if not items: return None

        return self._parse_json_to_model(items[0])

    def _parse_json_to_model(self, item: dict) -> CitationData:
        citation = CitationData()
        citation.raw_data = item

        if "title" in item and item["title"]:
            citation.title = item["title"][0]

        if "author" in item:
            authors = []
            for a in item["author"]:
                given = a.get("given", "")
                family = a.get("family", "")
                full_name = f"{given} {family}".strip()
                if full_name: authors.append(full_name)
            citation.authors = authors

        if "container-title" in item and item["container-title"]:
            citation.source = item["container-title"][0]

        date_parts = None
        if "published-print" in item:
            date_parts = item["published-print"]["date-parts"]
        elif "published-online" in item:
            date_parts = item["published-online"]["date-parts"]

        if date_parts and date_parts[0]:
            citation.year = str(date_parts[0][0])

        citation.volume = item.get("volume", "")
        citation.issue = item.get("issue", "")
        citation.pages = item.get("page", "")

        # 【新增】提取文章编号
        # Crossref 标准字段为 "article-number"
        citation.article_number = item.get("article-number", "")

        citation.doi = item.get("DOI", "")
        citation.url = item.get("URL", "")

        return citation