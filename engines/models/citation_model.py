"""
文件路径: engines/models/citation_model.py
=========================================================
【可用接口说明】
class CitationData:
    - title: str
    - authors: list
    - source: str
    - year: str
    - article_number: str  # <--- 新增字段
    ...
=========================================================
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class CitationData:
    """
    统一的文献数据模型。
    """
    # 核心字段
    title: str = ""
    authors: List[str] = field(default_factory=list)
    source: str = ""  # 期刊名、会议名或出版社
    year: str = ""

    # 详细字段
    volume: str = ""  # 卷
    issue: str = ""  # 期
    pages: str = ""  # 页码 (起止页)
    article_number: str = ""  # 【新增】论文编号 (Article Number)，用于替代页码
    doi: str = ""  # Digital Object Identifier
    url: str = ""  # 链接

    # 元数据
    entry_type: str = "article"
    raw_data: dict = field(default_factory=dict)

    def is_valid(self) -> bool:
        """判断数据是否基本完整"""
        required_fields = [self.title, self.authors, self.source, self.year]
        return all(required_fields)

    def get_formatted_authors(self, max_authors=3) -> str:
        """UI 预览用的简单作者格式化"""
        if not self.authors:
            return "[佚名]"
        cleaned_authors = [str(a).strip() for a in self.authors if str(a).strip()]
        if not cleaned_authors:
            return "[佚名]"
        if len(cleaned_authors) <= max_authors:
            return ", ".join(cleaned_authors)
        else:
            return ", ".join(cleaned_authors[:max_authors]) + ", 等"