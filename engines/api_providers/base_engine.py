"""
文件路径: engines/api_providers/base_engine.py
=========================================================
所有 API 引擎的父类。
=========================================================
"""

from abc import ABC, abstractmethod
import requests
import time
from typing import Optional
import logging

# 【关键修改】使用相对路径导入，适配 engines 包结构
from ..models.citation_model import CitationData
from .. import config


class BaseEngine(ABC):
    def __init__(self):
        self.name = "BaseEngine"
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.name)

    def get_headers(self) -> dict:
        return {
            "User-Agent": config.USER_AGENT,
            "Accept": "application/json"
        }

    @abstractmethod
    def search(self, query: str) -> Optional[CitationData]:
        pass

    def safe_request(self, url: str, params: dict = None) -> Optional[dict]:
        try:
            # 【关键修改】增加请求间隔，防止 429 错误
            if hasattr(config, 'MIN_REQUEST_INTERVAL'):
                time.sleep(config.MIN_REQUEST_INTERVAL)
            else:
                time.sleep(1.0)

            response = requests.get(
                url,
                headers=self.get_headers(),
                params=params,
                timeout=config.TIMEOUT
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.logger.warning(f"[{self.name}] 请求过于频繁 (429 Too Many Requests)，正在被限流。")
            else:
                self.logger.warning(f"[{self.name}] HTTP 错误: {e}")
            return None

        except requests.exceptions.RequestException as e:
            self.logger.warning(f"[{self.name}] 网络请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"[{self.name}] 未知错误: {e}")
            return None