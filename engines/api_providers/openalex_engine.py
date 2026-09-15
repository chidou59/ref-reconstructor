"""
文件路径: engines/api_providers/openalex_engine.py
=========================================================
OpenAlex 搜索引擎实现。
=========================================================
"""
from typing import Optional
# 【关键修改】相对导入
from .base_engine import BaseEngine
from ..models.citation_model import CitationData
from .. import config


class OpenAlexEngine(BaseEngine):
    def __init__(self):
        super().__init__()
        self.name = "OpenAlex"
        self.api_url = config.SourceConfig.OPENALEX_API_URL

    def search(self, query: str) -> Optional[CitationData]:
        if not config.SourceConfig.OPENALEX_ENABLED:
            return None

        # 判断纯 DOI
        is_pure_doi = "10." in query and "/" in query and " " not in query
        params = {}

        if is_pure_doi:
            clean_doi = query.strip()
            if not clean_doi.startswith("https://doi.org/") and not clean_doi.startswith("http://doi.org/"):
                doi_url = f"https://doi.org/{clean_doi}"
            else:
                doi_url = clean_doi
            params = {"filter": f"doi:{doi_url}", "per_page": 1}
        else:
            params = {"search": query, "per_page": 1}

        data = self.safe_request(self.api_url, params)

        if not data or "results" not in data or not data["results"]:
            return None

        best_match = data["results"][0]
        return self._parse_json_to_model(best_match)

    def _parse_json_to_model(self, json_data: dict) -> CitationData:
        citation = CitationData()
        citation.title = json_data.get("display_name", "")

        authors_raw = json_data.get("authorships", [])
        citation.authors = [
            item.get("author", {}).get("display_name", "")
            for item in authors_raw
        ]

        primary_loc = json_data.get("primary_location") or {}
        source_info = primary_loc.get("source") or {}
        citation.source = source_info.get("display_name", "")

        citation.year = str(json_data.get("publication_year", ""))

        biblio = json_data.get("biblio", {})
        citation.volume = biblio.get("volume", "")
        citation.issue = biblio.get("issue", "")
        citation.pages = f"{biblio.get('first_page', '')}-{biblio.get('last_page', '')}"

        # 清洗页码
        if citation.pages == "-":
            citation.pages = ""
        elif citation.pages.endswith("-"):
            citation.pages = citation.pages.strip("-")

        doi_url = json_data.get("doi", "")
        if doi_url:
            citation.doi = doi_url.replace("https://doi.org/", "").replace("http://doi.org/", "")
            citation.url = doi_url

        citation.raw_data = json_data
        return citation