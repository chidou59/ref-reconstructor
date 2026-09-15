"""
文件路径: engines/api_providers/qwen_engine.py
=========================================================
【功能】
Qwen (通义千问) AI 补全引擎。
【可用接口】
class QwenEngine:
    def __init__(self): ...
    def search(self, query: str) -> Optional[CitationData]: ...
=========================================================
"""

import logging
import difflib  # 用于计算文本重合度
import os
import re
from typing import Optional
from .base_engine import BaseEngine
from ..models.citation_model import CitationData
from .. import config
import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class QwenEngine(BaseEngine):
    def __init__(self):
        super().__init__()
        self.name = "QwenAI"

        self.api_key = None
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model_name = "qwen-plus"

        try:
            creds = st.secrets.get("ai_credentials", {})
            if creds:
                self.api_key = creds.get("qwen_api_key")
                self.base_url = creds.get("qwen_base_url", self.base_url)
                self.model_name = creds.get("qwen_model_name", self.model_name)
        except Exception:
            pass

        if not self.api_key:
            self.api_key = os.environ.get("qwen_API_KEY") or os.environ.get("QWEN_API_KEY")
            self.base_url = os.environ.get("QWEN_BASE_URL", self.base_url)
            self.model_name = os.environ.get("QWEN_MODEL_NAME", self.model_name)

        self.client = None
        if OpenAI and self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            if not OpenAI:
                self.logger.warning(f"[{self.name}] 未安装 openai 库，AI 功能不可用。")

    def search(self, query: str) -> Optional[CitationData]:
        if not self.client:
            return None
        return self._search_with_double_check(query)

    def _call_qwen_once(self, raw_text: str) -> str:
        """
        执行单次请求。每次调用都是独立的 API 请求，天然隔离上下文。
        """
        # 【修改点】放宽 Prompt 限制，鼓励 AI 尝试补全，依靠后端的重合度检测来兜底。
        system_prompt = """你是一个严谨的学术参考文献修正专家。任务是将用户提供的参考文献文本转换为标准的 GB/T 7714-2015 格式。

【绝对指令】
1. **积极补全**：如果原文缺失年份、卷期、页码等关键信息，请**积极利用你的知识库进行检索和补全**。只有在你完全查不到该文献的任何踪迹时，才回答“**不知道**”。
2. **基于事实**：请确保补全的信息是基于你掌握的知识，而非凭空捏造。
3. **禁止翻译**：如果是中文文献，仅输出中文格式；如果是英文文献，仅输出英文格式。**严禁**输出中英文对照（如 "中文... English..."），严禁画蛇添足。
4. **单行输出**：结果不要换行，只输出一条最终的字符串。
5. **格式规范**：
   - 期刊: 作者. 题名[J]. 刊名, 年, 卷(期): 页码.
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"请修复此文献（禁止附带翻译）：{raw_text}"}
                ],
                temperature=0.01,  # 接近绝对零度，最大程度降低随机性
                max_tokens=300,
                # 【关键修改】开启 DashScope 的联网搜索功能
                extra_body={"enable_search": True}
            )
            content = response.choices[0].message.content.strip()

            # 结果清洗：如果 AI 还是输出了多行，我们只取第一行
            lines = content.split('\n')
            first_valid_line = ""
            for line in lines:
                line = line.strip()
                if len(line) > 5:  # 忽略太短的空行或无关字符
                    first_valid_line = line
                    break

            return first_valid_line if first_valid_line else "ERROR"

        except Exception as e:
            self.logger.error(f"[{self.name}] 调用异常: {e}")
            return "ERROR"

    def _normalize_for_comparison(self, text: str) -> str:
        """
        【关键算法】剥皮清洗
        仅保留：汉字、字母、数字。
        """
        text = text.lower()
        chars = re.findall(r'[\w\u4e00-\u9fa5]+', text)
        return "".join(chars)

    def _search_with_double_check(self, query: str) -> Optional[CitationData]:
        """
        双重验证核心逻辑 (Strict Mode)
        """
        short_query = query[:30].replace("\n", " ") + "..." if len(query) > 30 else query
        print(f"\n======== [AI调试] 开始处理: {short_query} ========")

        # === Round 1 ===
        res1 = self._call_qwen_once(query)
        print(f"   [AI调试] Round 1 结果: {res1}")

        if not res1 or "不知道" in res1 or "ERROR" in res1:
            print(f"   [AI调试] ❌ Round 1 失败/放弃")
            return self._create_give_up_signal()

        # === Round 2 ===
        res2 = self._call_qwen_once(query)
        print(f"   [AI调试] Round 2 结果: {res2}")

        if not res2 or "不知道" in res2 or "ERROR" in res2:
            print(f"   [AI调试] ❌ Round 2 失败/放弃")
            return self._create_give_up_signal()

        # === 剥皮比对 ===
        norm1 = self._normalize_for_comparison(res1)
        norm2 = self._normalize_for_comparison(res2)

        if len(norm1) < 5 or len(norm2) < 5:
            print(f"   [AI调试] ❌ 结果过短")
            return self._create_give_up_signal()

        # 计算相似度
        similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        print(f"   [AI调试] 🔄 相似度计算: {similarity:.4f} (阈值: 0.99)")

        # 极高阈值
        if similarity < 0.99:
            print(f"   [AI调试] ⚠️ 相似度不足，判定为幻觉或格式不一，放弃修复！")
            return self._create_give_up_signal()

        # === 通过验证 ===
        print(f"   [AI调试] ✅ 验证通过！成功修复。")
        final_text = res1.strip('"').strip("'")
        data = CitationData()
        data.title = "AI_REPAIRED_FLAG"
        data.source = final_text
        return data

    def _create_give_up_signal(self):
        """返回一个代表“AI 放弃”的信号"""
        data = CitationData()
        data.title = "AI_GAVE_UP_FLAG"
        return data