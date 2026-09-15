"""
文件路径: core/security.py
=========================================================
【功能】
负责安全审计与溯源：
1. 获取真实用户 IP (穿透 Nginx 代理)
2. 审计日志：保存用户上传的原始文件和处理后的结果文件
3. 自动清理机制：仅保留最近 7 天的记录，过期自动删除
【更新】
- 修复 _get_websocket_headers 弃用警告，迁移至 st.context.headers
=========================================================
"""

import os
import json
import shutil
import logging
from datetime import datetime, timedelta
import streamlit as st

# 配置一个简单的日志打印
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SecurityManager:
    def __init__(self, audit_dir="audit_logs", retention_days=1):
        """
        初始化审计管理器
        :param audit_dir: 审计文件存放的根目录
        :param retention_days: 数据保留天数 (默认7天)
        """
        # 获取当前项目根目录
        base_dir = os.getcwd()
        self.audit_dir = os.path.join(base_dir, audit_dir)
        self.retention_days = retention_days

        # 确保根目录存在
        if not os.path.exists(self.audit_dir):
            os.makedirs(self.audit_dir, exist_ok=True)

        # 今天的日期文件夹
        self.today_str = datetime.now().strftime("%Y-%m-%d")
        self.daily_dir = os.path.join(self.audit_dir, self.today_str)

        if not os.path.exists(self.daily_dir):
            os.makedirs(self.daily_dir, exist_ok=True)

        # 每次初始化时，顺便检查并清理过期文件
        self._cleanup_old_logs()

    def _cleanup_old_logs(self):
        """
        [内部方法] 扫描并删除超过保留期限的日期文件夹
        """
        try:
            today_date = datetime.now().date()

            # 遍历 audit_logs 下的所有子文件夹
            for dirname in os.listdir(self.audit_dir):
                dir_path = os.path.join(self.audit_dir, dirname)

                # 只处理文件夹
                if not os.path.isdir(dir_path):
                    continue

                # 尝试解析文件夹名字为日期
                try:
                    folder_date = datetime.strptime(dirname, "%Y-%m-%d").date()
                except ValueError:
                    continue

                # 计算时间差
                delta_days = (today_date - folder_date).days

                # 如果超过保留期限
                if delta_days > self.retention_days:
                    logging.info(f"♻️ [清理过期日志] 发现过期文件夹: {dirname} (已存在 {delta_days} 天)，正在删除...")
                    try:
                        shutil.rmtree(dir_path)
                        logging.info(f"✅ [清理完成] 已删除: {dirname}")
                    except Exception as e:
                        logging.error(f"❌ [清理失败] 无法删除 {dirname}: {e}")

        except Exception as e:
            logging.error(f"⚠️ [自动清理流程异常] {e}")

    def get_remote_ip(self):
        """
        尝试获取用户的真实 IP 地址。
        适配宝塔 Nginx 环境。
        【更新】优先使用 st.context.headers (Streamlit >= 1.39.0)
        """
        try:
            headers = None

            # 1. 尝试使用新版 API (推荐)
            # st.context 在 Streamlit 1.39.0+ 版本引入
            if hasattr(st, "context") and hasattr(st.context, "headers"):
                headers = st.context.headers

            # 2. 如果新版不可用，回退到旧版私有方法 (防止低版本报错)
            if headers is None:
                try:
                    from streamlit.web.server.websocket_headers import _get_websocket_headers
                    headers = _get_websocket_headers()
                except ImportError:
                    pass

            if headers is None:
                return "127.0.0.1"

            # 3. 尝试从 X-Forwarded-For 获取 (Nginx 标准配置)
            # 格式通常是: "Client-IP, Proxy1-IP, Proxy2-IP"
            x_forwarded_for = headers.get("X-Forwarded-For")
            if x_forwarded_for:
                # 取第一个 IP
                return x_forwarded_for.split(",")[0].strip()

            # 4. 尝试从 X-Real-Ip 获取
            x_real_ip = headers.get("X-Real-Ip")
            if x_real_ip:
                return x_real_ip.strip()

            return "Unknown_IP"
        except Exception:
            return "Error_Getting_IP"

    def log_transaction(self, uploaded_file_obj, processed_file_path, status="success"):
        """
        记录一次完整的处理交易
        """
        try:
            user_ip = self.get_remote_ip()
            timestamp = datetime.now().strftime("%H_%M_%S")
            # 替换 IP 中的点，方便做文件名
            safe_ip = user_ip.replace(".", "_").replace(":", "_")

            # 定义文件名 ID
            trans_id = f"{timestamp}_IP_{safe_ip}"

            # === 1. 保存原始文件 (Input) ===
            uploaded_file_obj.seek(0)
            original_filename = uploaded_file_obj.name

            # 防止文件名太长或含有特殊字符
            safe_filename = "".join([c for c in original_filename if c.isalnum() or c in "._-"])[:50]

            save_input_name = f"{trans_id}_IN_{safe_filename}"
            save_input_path = os.path.join(self.daily_dir, save_input_name)

            with open(save_input_path, "wb") as f:
                f.write(uploaded_file_obj.getvalue())

            # === 2. 保存结果文件 (Output) ===
            save_output_path = None
            if processed_file_path and os.path.exists(processed_file_path):
                ext = os.path.splitext(processed_file_path)[1]
                save_output_name = f"{trans_id}_OUT_Result{ext}"
                save_output_path = os.path.join(self.daily_dir, save_output_name)
                shutil.copy2(processed_file_path, save_output_path)

            # === 3. 写入日志索引 (Log Index) ===
            log_entry = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ip": user_ip,
                "input_file": save_input_path,
                "output_file": save_output_path,
                "original_name": original_filename,
                "status": status
            }

            # 追加写入当天的 log.jsonl 文件
            log_index_file = os.path.join(self.daily_dir, "audit_index.jsonl")
            with open(log_index_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            logging.info(f"🔒 [审计成功] IP={user_ip}, File={original_filename}")

        except Exception as e:
            logging.error(f"❌ [审计失败] {e}")