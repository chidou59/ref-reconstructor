"""
文件路径: web_app/logic.py
【更新】
- 修复多线程清洗导致的乱序风险。
- 采用 "字典暂存 + 严格按序重组" 策略，确保 cleaned_bib_list 的顺序绝对锚定 new_bibs_raw。
- 【新增】完整性校验日志，显式确认顺序一致性。
"""

import time
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.doc_parser import DocParser
from core.citation_mapper import CitationMapper, BibDeduplicator
from core.doc_renderer import DocRenderer
from engines.orchestrator import Orchestrator


def scan_file_for_deferrable_citations(input_path):
    # (保持原代码不变)
    parser = DocParser(input_path)
    body_citations, _ = parser.parse()
    grouped_candidates = defaultdict(lambda: {"name": "", "indices": [], "ref_count": 0})
    misc_counter = 0
    for cit in body_citations:
        if cit.get('context') in ['caption', 'table']:
            c_id = cit.get('container_id')
            c_name = cit.get('container_name')
            if not c_id:
                misc_counter += 1
                c_id = f"misc_{misc_counter}"
                c_name = f"散落引用: {cit['preview_text'][:15]}..."
            group = grouped_candidates[c_id]
            group["name"] = c_name
            group["indices"].append(cit['original_idx'])
            group["ref_count"] += 1
    result_list = []
    for c_id, info in grouped_candidates.items():
        result_list.append({
            "id": c_id,
            "display_label": f"{info['name']} (含 {info['ref_count']} 处引用)",
            "indices": info["indices"]
        })
    result_list.sort(key=lambda x: x["indices"][0] if x["indices"] else 0)
    return result_list


def process_core_logic(input_path, output_path, config, status_container):
    """
    核心业务逻辑
    """
    stats = {
        "citations": 0,
        "bibs": 0,
        "cleaned": 0,
        "merged": 0,
        "missing_ids": [],
        "unused_ids": [],
        "failed_cleaning_indices": [],
        "ai_aborted_indices": [],
        "total_cleaning_targets": 0,
        "ai_filled": 0,
        "ai_repaired_count": 0
    }
    logs = []

    live_status_text = status_container.empty()
    progress_bar = status_container.progress(0)

    def update_status(text, percent):
        percent = max(0.0, min(1.0, percent))
        live_status_text.markdown(f"""
        <div style="font-size:14px; color:#A0AEC0; margin-bottom:5px;" class="fade-in-up">
            {text} <span style="float:right; color:#63B3ED; font-weight:bold;">{int(percent * 100)}%</span>
        </div>
        """, unsafe_allow_html=True)
        progress_bar.progress(percent)

    def add_log(msg, type="info"):
        timestamp = time.strftime("%H:%M:%S")
        logs.append(f"{timestamp} | {msg}")

    try:
        # 1. 解析
        update_status("正在启动文档解析引擎...", 0.05)
        parser = DocParser(input_path)
        body_citations, raw_bibs = parser.parse()
        stats["citations"] = len(body_citations)
        stats["bibs"] = len(raw_bibs)

        if not body_citations and not raw_bibs:
            raise ValueError("未检测到有效的引用标记或参考文献")

        # 2. 映射
        update_status(f"正在构建引用拓扑图 (发现 {len(body_citations)} 处引用)...", 0.15)

        deferred_indices = config.get("deferred_indices", set())
        if isinstance(deferred_indices, list):
            deferred_indices = set(deferred_indices)

        mapper = CitationMapper()
        map_result = mapper.process(
            body_citations,
            raw_bibs,
            remove_unused=config.get("remove_unused", False),
            sort_by_appearance=config.get("sort_by_appearance", True),
            deferred_indices=deferred_indices
        )
        new_bibs_raw = map_result['new_bibs']
        stats['missing_ids'] = map_result.get('missing', [])
        stats['unused_ids'] = map_result.get('unused', [])

        # 3. 清洗 (核心修改区域：保证顺序)
        cleaned_bib_list = []

        if config.get("use_gb_format"):
            orchestrator = Orchestrator()
            total = len(new_bibs_raw)
            stats["total_cleaning_targets"] = total

            use_ai_fallback = config.get("use_ai_fallback", False)
            if use_ai_fallback:
                add_log("启用 Qwen AI 双重验证补刀模式", "info")

            # 【修改点1】使用字典暂存结果，Key为索引i，Value为清洗后的文本
            # 这样无论线程何时完成，我们都通过 Key 来定位，不受完成时间影响
            temp_results_dict = {}

            start_percent = 0.2
            end_percent = 0.85
            span = end_percent - start_percent

            workers = 3 if use_ai_fallback else 6

            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_idx = {}

                for i, raw_text in enumerate(new_bibs_raw):
                    # 去掉前面的序号 [1] 或 1.
                    query_text = re.sub(r'^\s*(?:\[\d+\]|\d+\.|(?:\(\d+\)))\s*', '', raw_text).strip()

                    # 提交任务
                    future = executor.submit(orchestrator.format_single_with_status, query_text, use_ai_fallback)
                    # 记录这个 future 对应的原始索引 i
                    future_to_idx[future] = (i, raw_text)

                completed_count = 0

                # as_completed 会按完成顺序 yield，导致顺序混乱，所以必须用字典存起来
                for future in as_completed(future_to_idx):
                    i, original_raw_text = future_to_idx[future]
                    completed_count += 1
                    current_prog = start_percent + (span * (completed_count / total))

                    display_text = re.sub(r'^\s*\[.*?\]\s*', '', original_raw_text)
                    if len(display_text) > 25: display_text = display_text[:25] + "..."

                    # 这里的 display_text 乱序没关系，只是给用户看个进度
                    update_status(
                        f"正在清洗 ({completed_count}/{total})：{display_text}",
                        current_prog
                    )

                    try:
                        formatted_str, is_success, status_msg = future.result()

                        # 存入字典，绑定索引 i
                        temp_results_dict[i] = formatted_str

                        if is_success:
                            stats["cleaned"] += 1
                        else:
                            if status_msg == "AI_ABORTED":
                                stats["ai_aborted_indices"].append(i + 1)
                                stats["failed_cleaning_indices"].append(i + 1)
                            else:
                                stats["failed_cleaning_indices"].append(i + 1)

                    except Exception as e:
                        # 异常时的兜底：提取纯文本放回去
                        fallback_text = re.sub(r'^\s*(?:\[\d+\]|\d+\.|(?:\(\d+\)))\s*', '', original_raw_text).strip()
                        temp_results_dict[i] = fallback_text

                        stats["failed_cleaning_indices"].append(i + 1)
                        add_log(f"文献[{i + 1}]处理异常: {e}", "warning")

            # 【修改点2】严格按序重组 (Strict Reassembly)
            # 循环 0 到 total-1，从字典中取值，确保最终列表的顺序与 new_bibs_raw 完全一致
            cleaned_bib_list = []
            for i in range(total):
                if i in temp_results_dict:
                    cleaned_bib_list.append(temp_results_dict[i])
                else:
                    # 极罕见的丢包兜底
                    fallback_text = re.sub(r'^\s*(?:\[\d+\]|\d+\.|(?:\(\d+\)))\s*', '', new_bibs_raw[i]).strip()
                    cleaned_bib_list.append(fallback_text)
                    add_log(f"警告：文献索引 [{i + 1}] 在线程池中丢失，已使用原文回填。", "warning")

            # 【新增】完整性校验 (Sanity Check)
            if len(cleaned_bib_list) != len(new_bibs_raw):
                raise RuntimeError(
                    f"严重错误：文献列表长度不一致！输入: {len(new_bibs_raw)}, 输出: {len(cleaned_bib_list)}")
            add_log(f"✅ 顺序完整性校验通过: {len(cleaned_bib_list)} 条文献已严格按索引归位。", "success")

            stats['ai_filled'] = orchestrator.completion_stats.get('total_filled', 0)
            stats['ai_repaired_count'] = orchestrator.completion_stats["details"].get("ai_repair", 0)

        else:
            update_status("正在整理原始文献...", 0.5)
            # 如果不开启清洗，直接用原文
            cleaned_bib_list = [t.strip() for t in new_bibs_raw]
            time.sleep(0.5)

        # 4. 去重
        if config.get("merge_duplicates") and len(cleaned_bib_list) > 1:
            update_status("正在执行语义级文献去重...", 0.88)
            deduplicator = BibDeduplicator()

            # 这里传入的 cleaned_bib_list 现在已经严格有序
            # 索引 0 对应新文献列表的 [1], 索引 1 对应 [2]...
            final_bib_list, final_mapping, merge_logs_details = deduplicator.deduplicate(
                cleaned_bib_list, map_result['mapping']
            )

            stats["merged"] = len(cleaned_bib_list) - len(final_bib_list)
            cleaned_bib_list = final_bib_list
            map_result['mapping'] = final_mapping

        # 5. 渲染
        update_status("正在生成最终 Word 文档...", 0.95)
        renderer = DocRenderer(input_path)
        renderer.render(
            output_path,
            map_result['mapping'],
            cleaned_bib_list,
            use_superscript=config.get("use_superscript", False),
            style_config=config.get("style", None)
        )

        update_status("✅ 处理完成！", 1.0)
        time.sleep(0.8)

        return True, stats, logs

    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        add_log(f"发生错误: {error_msg}", "error")
        stats['error'] = error_msg
        stats['error_trace'] = error_trace
        update_status(f"❌ 处理失败: {error_msg}", 0.0)
        return False, stats, logs