"""
文件路径: engines/orchestrator.py
=========================================================
【更新记录】
- V7.6: 适配 QwenEngine 的双重验证逻辑。
- 识别 'AI_GAVE_UP_FLAG' 并返回特殊状态码 'AI_ABORTED'。
=========================================================
"""

import sys
import os
import time
import re
import html
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

# 相对导入
from . import config
from . import formatter
from .api_providers.openalex_engine import OpenAlexEngine
from .api_providers.crossref import CrossrefEngine
from .api_providers.semantic_scholar import SemanticScholarEngine

# 安全导入 QwenEngine
try:
    from .api_providers.qwen_engine import QwenEngine
except ImportError:
    QwenEngine = None


class Orchestrator:
    """总指挥"""

    def __init__(self):
        self.engines = []
        if QwenEngine:
            self.qwen_engine = QwenEngine()
        else:
            self.qwen_engine = None

        self._init_engines()
        self.completion_stats = {
            "total_filled": 0,
            "details": {"year": 0, "volume": 0, "issue": 0, "pages": 0, "ai_repair": 0}
        }

    def _init_engines(self):
        # ... (保持原逻辑) ...
        print("--- [调试] 正在初始化引擎 ---")
        if config.SourceConfig.OPENALEX_ENABLED: self.engines.append(OpenAlexEngine())
        if config.SourceConfig.CROSSREF_ENABLED: self.engines.append(CrossrefEngine())
        if config.SourceConfig.S2_ENABLED: self.engines.append(SemanticScholarEngine())
        print(f"--- [调试] 引擎初始化完毕，共加载 {len(self.engines)} 个引擎")

    def _track_completion(self, citation_data):
        # ... (保持原逻辑) ...
        if not citation_data: return
        if citation_data.year:
            self.completion_stats["details"]["year"] += 1
            self.completion_stats["total_filled"] += 1
        if citation_data.volume:
            self.completion_stats["details"]["volume"] += 1
            self.completion_stats["total_filled"] += 1
        if citation_data.issue:
            self.completion_stats["details"]["issue"] += 1
            self.completion_stats["total_filled"] += 1
        if citation_data.pages:
            self.completion_stats["details"]["pages"] += 1
            self.completion_stats["total_filled"] += 1

    def format_single_with_status(self, query: str, use_ai_fallback: bool = False) -> (str, bool, str):
        """
        单条处理
        :return: (格式化后的文本, 是否成功, URL或状态码)
        """
        if not self.engines:
            return query, False, ""

        extracted_dois, text_without_doi = self._extract_and_clean_doi(query)

        # === 1. DOI 优先策略 (保持不变) ===
        if not extracted_dois:
            broken_doi = self._try_fix_broken_doi(query)
            if broken_doi:
                extracted_dois = [broken_doi]
                text_without_doi = query.replace("doi", "").replace("DOI", "")

        if extracted_dois:
            target_doi = extracted_dois[0]
            for engine in self.engines:
                if "Crossref" in engine.name or "OpenAlex" in engine.name:
                    try:
                        citation_data = engine.search(target_doi)
                        if citation_data and citation_data.title:
                            if len(text_without_doi) > 15:
                                is_match, reason = self._validate_result(text_without_doi, citation_data,
                                                                         strict_mode=False)
                                if is_match:
                                    self._track_completion(citation_data)
                                    return formatter.to_gbt7714(citation_data), True, citation_data.url
                            else:
                                self._track_completion(citation_data)
                                return formatter.to_gbt7714(citation_data), True, citation_data.url
                    except Exception:
                        pass

        # === 2. 常规文本搜索策略 (保持不变) ===
        search_query = text_without_doi if text_without_doi else query
        if len(search_query) >= 4:
            for engine in self.engines:
                try:
                    citation_data = engine.search(search_query)
                    if citation_data:
                        is_match, reason = self._validate_result(search_query, citation_data, strict_mode=True)
                        if is_match:
                            self._track_completion(citation_data)
                            return formatter.to_gbt7714(citation_data), True, citation_data.url
                except Exception:
                    continue

        # === 3. AI 双重验证补刀 (更新) ===
        if use_ai_fallback and self.qwen_engine and self.qwen_engine.api_key:
            try:
                # 调用 AI 引擎 (内部已包含双重验证)
                ai_data = self.qwen_engine.search(search_query)

                if ai_data:
                    if ai_data.title == "AI_REPAIRED_FLAG":
                        # 成功修复
                        repaired_text = ai_data.source
                        if len(repaired_text) > 10:
                            self.completion_stats["details"]["ai_repair"] += 1
                            self.completion_stats["total_filled"] += 1
                            return repaired_text, True, ""

                    elif ai_data.title == "AI_GAVE_UP_FLAG":
                        # AI 决定放弃 (返回“不知道”或结果不一致)
                        # 返回 False 表示失败，但在第3个返回值带上 "AI_ABORTED" 标记
                        return query, False, "AI_ABORTED"

            except Exception as e:
                print(f"   [AI错误] {e}")

        # 彻底失败
        return query, False, ""

    # ... (保留原文件所有其他 helper functions: format_batch, _validate_result 等) ...
    # 为了防止代码覆盖错误，这里简写，请务必保留 _validate_result, _check_author_consistency 等所有方法！

    # [Start of Mandatory Helper Functions Retention]
    def format_batch(self, raw_text_block: str, callback_signal=None) -> dict:
        # (完全保留原代码逻辑)
        # ... 请复制原有的 format_batch 代码 ...
        lines = raw_text_block.split('\n')
        valid_tasks = []
        results_container = [None] * len(lines)
        for i, line in enumerate(lines):
            original_line = line.strip()
            if not original_line:
                results_container[i] = {"text": "", "full": "", "html": ""}
                continue
            match = re.match(r'^\s*(\[\d+\]|\d+\.|\d+、|\(\d+\))\s*(.*)', original_line)
            prefix = ""
            clean_query = original_line
            if match:
                prefix = match.group(1)
                clean_query = match.group(2)
            valid_tasks.append((i, clean_query, prefix))
        total_tasks = len(valid_tasks)
        finished_count = 0
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_info = {
                executor.submit(self.format_single_with_status, query, False): (idx, query, pfx)
                for idx, query, pfx in valid_tasks
            }
            for future in as_completed(future_to_info):
                idx, query, prefix = future_to_info[future]
                finished_count += 1
                try:
                    formatted_content, is_success, url = future.result()
                    full_text_line = f"{prefix} {formatted_content}" if prefix else formatted_content
                    safe_text = html.escape(full_text_line)
                    if is_success and url:
                        html_line = (
                            f'<div style="margin-bottom: 14px;"><a href="{url}" target="_blank" style="color: #3182CE; text-decoration: none; border-bottom: 1px dashed rgba(49, 130, 206, 0.4); padding-bottom: 2px; transition: all 0.2s; display: inline-block; line-height: 1.6;" onmouseover="this.style.color=\'#63B3ED\';this.style.borderBottomStyle=\'solid\'" onmouseout="this.style.color=\'#3182CE\';this.style.borderBottomStyle=\'dashed\'" title="点击跳转原文: {url}">{safe_text}</a></div>')
                    elif is_success:
                        html_line = f'<div style="margin-bottom: 14px; color:#2c3e50; line-height: 1.6;">{safe_text}</div>'
                    else:
                        html_line = f'<div style="margin-bottom: 14px; color:#95a5a6; line-height: 1.6;">{safe_text}</div>'
                    results_container[idx] = {"text": formatted_content, "full": full_text_line, "html": html_line}
                except Exception as e:
                    results_container[idx] = {"text": "Error", "full": "Error", "html": "Error"}
        list_with_num = []
        list_no_num = []
        list_html = []
        for item in results_container:
            if item:
                if item["text"]:
                    list_no_num.append(item["text"])
                    list_with_num.append(item["full"])
                    list_html.append(item["html"])
        return {"with_num": "\n\n".join(list_with_num), "no_num": "\n\n".join(list_no_num),
                "display_html": "".join(list_html)}

    def _validate_result(self, user_query: str, data, strict_mode: bool = True) -> (bool, str):
        # (完全保留原代码逻辑)
        if not data.title: return False, "数据缺失:无标题"
        query_lower = user_query.lower()

        def super_clean(t):
            return re.sub(r'[\W_]+', '', t).lower()

        q_super = super_clean(user_query)
        t_super = super_clean(data.title)
        title_score = 0
        if len(t_super) > 15 and t_super in q_super:
            title_score = 100
        elif len(q_super) > 15 and q_super in t_super:
            title_score = 95
        else:
            def get_tokens(text):
                if not text: return []
                clean = re.sub(r'[^\w\s]', ' ', text)
                return [w for w in clean.split() if len(w) > 2]

            query_tokens = set(get_tokens(query_lower))
            title_tokens = set(get_tokens(data.title.lower()))
            if not title_tokens: return False, "API标题无法分词"
            overlap = query_tokens.intersection(title_tokens)
            coverage = len(overlap) / len(title_tokens)
            if coverage >= 0.9:
                title_score = 90
            elif coverage >= 0.7:
                title_score = 75
            elif coverage >= 0.5:
                title_score = 50
            else:
                title_score = 0
        if title_score < 50: return False, f"标题差异过大 (TitleScore: {title_score})"
        if not strict_mode and title_score >= 75: return True, "DOI来源+标题吻合"
        author_check_pass, author_msg = self._check_author_consistency(user_query, data.authors)
        year_check_pass, year_msg = self._check_year_consistency(user_query, data.year)
        if title_score >= 90 and not author_check_pass: return False, f"标题一致但作者严重冲突 ({author_msg})"
        if title_score >= 90 and not year_check_pass: return False, f"标题一致但年份严重冲突 ({year_msg})"
        if 50 <= title_score < 90:
            if (not author_check_pass) or (not year_check_pass):
                return False, f"标题匹配度一般且元数据冲突 Author:{author_check_pass}, Year:{year_check_pass}"
        return True, "综合验证通过"

    def _check_author_consistency(self, user_query: str, api_authors: list) -> (bool, str):
        # (完全保留原代码逻辑)
        if not api_authors: return True, "API无作者数据"
        query_head = user_query[:min(len(user_query), 60, int(len(user_query) * 0.6))].lower()
        looks_like_has_author = "et al" in query_head or "," in query_head or " and " in query_head
        if not looks_like_has_author: return True, "用户输入似乎未包含作者"
        api_surnames = []
        for auth in api_authors:
            parts = re.sub(r'[^\w\s]', '', auth.lower()).split()
            if parts: api_surnames.extend([p for p in parts if len(p) > 2])
        api_surnames = set(api_surnames)
        if not api_surnames: return True, "API作者名无法提取"
        match_found = False
        for surname in api_surnames:
            if surname in query_head:
                match_found = True
                break
        if match_found:
            return True, "作者匹配成功"
        else:
            return False, f"用户疑似作者段 '{query_head[:20]}...' 与 API 作者无交集"

    def _check_year_consistency(self, user_query: str, api_year_str: str) -> (bool, str):
        # (完全保留原代码逻辑)
        if not api_year_str: return True, "API无年份"
        try:
            api_year = int(str(api_year_str).strip())
        except:
            return True, "API年份格式错误"
        user_years = re.findall(r'\b(19\d{2}|20\d{2})\b', user_query)
        if not user_years: return True, "用户未输入年份"
        for y_str in user_years:
            u_year = int(y_str)
            if abs(u_year - api_year) <= 1: return True, "年份匹配"
        return False, f"用户年份 {user_years} 与 API 年份 {api_year} 偏差过大"

    def _extract_and_clean_doi(self, text: str):
        # (完全保留原代码逻辑)
        valid_dois = []
        cleaned_text = text
        broken_pattern = r'doi\.org/(10\.[0-9a-zA-Z./_:;()\-]+(?:\s+[0-9a-zA-Z./_:;()\-]+)+)'
        broken_matches = re.findall(broken_pattern, cleaned_text, re.IGNORECASE)
        for raw_broken in broken_matches:
            fixed_doi = raw_broken.replace(" ", "").replace("\t", "").rstrip(".")
            if "/" in fixed_doi and len(fixed_doi) > 10:
                valid_dois.append(fixed_doi)
                remove_pattern = r'(https?://(dx\.)?doi\.org/)?\s*' + re.escape(raw_broken)
                cleaned_text = re.sub(remove_pattern, '', cleaned_text, flags=re.IGNORECASE)
        doi_pattern = r'(10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+)'
        found_dois = re.findall(doi_pattern, cleaned_text)
        for raw_doi in found_dois:
            clean_doi = raw_doi.rstrip(".")
            if clean_doi not in valid_dois: valid_dois.append(clean_doi)
            remove_pattern = r'(https?://(dx\.)?doi\.org/)?\s*' + re.escape(clean_doi)
            cleaned_text = re.sub(remove_pattern, '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return valid_dois, cleaned_text

    def _try_fix_broken_doi(self, text: str):
        # (完全保留原代码逻辑)
        match = re.search(r'doi\.org/(10\..+)', text, re.IGNORECASE)
        if match:
            potential_part = match.group(1)
            fixed_doi = potential_part.replace(" ", "").replace("\t", "").rstrip(".")
            return fixed_doi
        return None