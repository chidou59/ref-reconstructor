"""
文件路径: engines/api_providers/semantic_scholar.py
=========================================================
Semantic Scholar 搜索引擎实现。
=========================================================
"""
from typing import Optional
from .base_engine import BaseEngine
from ..models.citation_model import CitationData
from .. import config


class SemanticScholarEngine(BaseEngine):
    def __init__(self):
        super().__init__()
        self.name = "SemanticScholar"
        self.api_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.api_key = config.SourceConfig.S2_API_KEY

    def get_headers(self) -> dict:
        headers = super().get_headers()
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def search(self, query: str) -> Optional[CitationData]:
        if not config.SourceConfig.S2_ENABLED:
            return None

        params = {
            "query": query,
            "limit": 1,
            "fields": "title,authors,year,venue,url,externalIds,publicationTypes"
        }

        data = self.safe_request(self.api_url, params)
        if not data or "data" not in data or not data["data"]:
            return None

        best_match = data["data"][0]
        return self._parse_json_to_model(best_match)

    def _parse_json_to_model(self, item: dict) -> CitationData:
        citation = CitationData()
        citation.raw_data = item

        citation.title = item.get("title", "")
        if "authors" in item and item["authors"]:
            citation.authors = [a["name"] for a in item["authors"] if "name" in a]
        citation.year = str(item.get("year", ""))
        citation.source = item.get("venue", "")
        citation.url = item.get("url", "")
        if "externalIds" in item and item["externalIds"]:
            citation.doi = item["externalIds"].get("DOI", "")

        return citation