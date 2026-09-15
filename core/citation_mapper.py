"""
文件路径: core/citation_mapper.py
=========================================================
【可用接口】
class CitationMapper:
    def __init__(self): ...
    def process(self, ... deferred_indices=None): ...

class BibDeduplicator:
    def deduplicate(self, bib_list, current_mapping): ...
=========================================================
"""

import re
import difflib
from typing import List, Dict, Tuple, Set


class CitationMapper:
    def __init__(self):
        self.bib_id_pattern = re.compile(r'^\s*(?:\[(\d+)\]|(\d+)\.|(\d+)、|\((\d+)\))\s*')

    def process(self, body_citations: List[dict], raw_bib_lines: List[str],
                remove_unused: bool = False, sort_by_appearance: bool = True,
                deferred_indices: Set[int] = None):
        """
        核心处理函数
        :param deferred_indices: 需要延后的引用 original_idx 集合。
                                 若不为空，则仅将集合内的引用延后处理。
        """
        # 1. 构建旧文献数据库
        bib_db, build_report = self._build_bib_database(raw_bib_lines)

        all_cited_ids = set()
        for citation in body_citations:
            all_cited_ids.update(citation['nums'])

        old_to_new_map = {}
        new_bib_list = []
        unused_ids = []
        missing_ids = sorted(list(all_cited_ids - set(bib_db.keys())))

        current_new_id = 1

        if sort_by_appearance:
            # === 模式 A: 按阅读顺序排序 (Sort by Appearance) ===

            processing_queue = list(body_citations)  # 浅拷贝

            # 支持定点延后
            if deferred_indices:
                def get_sort_key(item):
                    sec = item.get('section_idx', 0)
                    orig = item.get('original_idx', 0)
                    is_deferred = orig in deferred_indices
                    priority = 1 if is_deferred else 0
                    return (sec, priority, orig)

                processing_queue.sort(key=get_sort_key)
            else:
                # 默认排序: 章节 -> 出现顺序
                processing_queue.sort(key=lambda x: (x.get('section_idx', 0), 0, x.get('original_idx', 0)))

            # --- 阶段一：处理正文中引用的文献 ---
            for citation in processing_queue:
                for old_id in citation['nums']:
                    if old_id in old_to_new_map:
                        continue
                    if old_id not in bib_db:
                        continue

                    old_to_new_map[old_id] = current_new_id
                    new_bib_list.append(bib_db[old_id])
                    current_new_id += 1

            # --- 阶段二：处理未引用的文献 ---
            all_db_ids = set(bib_db.keys())
            mapped_ids = set(old_to_new_map.keys())
            # 计算未引用的 ID (无论是否移除，先算出来)
            unused_ids = sorted(list(all_db_ids - mapped_ids))

            # 如果不移除，则将它们追加到末尾
            if not remove_unused:
                for old_id in unused_ids:
                    old_to_new_map[old_id] = current_new_id
                    new_bib_list.append(bib_db[old_id])
                    current_new_id += 1

        else:
            # === 模式 B: 保持原文档参考文献顺序 (Keep Original Order) ===
            # 【修复】在此模式下，之前 unused_ids 只有在 remove_unused=True 时才会被填充
            # 现在的逻辑：无论是否移除，都先统计 unused_ids

            for old_id, content in bib_db.items():
                is_used = old_id in all_cited_ids

                if not is_used:
                    unused_ids.append(old_id)

                # 如果开启了移除功能，且该文献未被引用，则跳过（不加入新列表）
                if remove_unused and not is_used:
                    continue

                old_to_new_map[old_id] = current_new_id
                new_bib_list.append(content)
                current_new_id += 1

        return {
            "new_bibs": new_bib_list,
            "mapping": old_to_new_map,
            "missing": missing_ids,
            "unused": unused_ids,  # 现在这里永远包含准确的未引ID列表
            "build_report": build_report,
            "removed_unused": remove_unused
        }

    def _build_bib_database(self, raw_lines: List[str]) -> Tuple[Dict[int, str], Dict]:
        """将文本列表解析为 ID -> Content 的字典"""
        db = {}
        report = {"total_raw": len(raw_lines), "explicit_mode": False, "no_id_lines": []}
        temp_entries = []
        explicit_count = 0
        max_explicit_id = 0

        for i, line in enumerate(raw_lines):
            line = line.strip()
            match = self.bib_id_pattern.match(line)
            found_id = None
            content = line
            if match:
                id_str = next(g for g in match.groups() if g is not None)
                try:
                    found_id = int(id_str)
                    content = line[match.end():].strip()
                    explicit_count += 1
                    max_explicit_id = max(max_explicit_id, found_id)
                except ValueError:
                    pass
            else:
                report["no_id_lines"].append(i + 1)
            temp_entries.append({"line_idx": i + 1, "explicit_id": found_id, "content": content if content else line})

        use_explicit = (len(raw_lines) > 0 and (explicit_count / len(raw_lines)) > 0.5)
        report["explicit_mode"] = use_explicit
        safe_id_counter = max_explicit_id + 10000

        for entry in temp_entries:
            if use_explicit:
                final_id = entry["explicit_id"] if entry["explicit_id"] is not None else safe_id_counter
                if entry["explicit_id"] is None: safe_id_counter += 1
            else:
                final_id = entry["line_idx"]
            db[final_id] = entry["content"]

        return db, report


class BibDeduplicator:
    """文献去重器"""

    def deduplicate(self, bib_list: List[str], current_mapping: Dict[int, int]):
        n = len(bib_list)
        if n < 2: return bib_list, current_mapping, []
        merged_indices = {}
        keep_indices = []
        merge_logs = []

        for i in range(n):
            if i in merged_indices: continue
            keep_indices.append(i)
            for j in range(i + 1, n):
                if j in merged_indices: continue
                if self._is_duplicate(bib_list[i], bib_list[j]):
                    merged_indices[j] = i
                    merge_logs.append(f"重复合并: [{j + 1}] -> [{i + 1}]")

        if not merged_indices: return bib_list, current_mapping, []

        final_bib_list = [bib_list[i] for i in keep_indices]
        id_trans_table = {}
        for old_idx in range(n):
            target_old_idx = old_idx
            while target_old_idx in merged_indices: target_old_idx = merged_indices[target_old_idx]
            try:
                id_trans_table[old_idx + 1] = keep_indices.index(target_old_idx) + 1
            except ValueError:
                pass

        final_mapping = {doc_id: id_trans_table.get(temp_id, temp_id) for doc_id, temp_id in current_mapping.items()}
        return final_bib_list, final_mapping, merge_logs

    def _is_duplicate(self, text1, text2):
        def clean(s):
            return re.sub(r'[\W_]+', '', s).lower()

        s1, s2 = clean(text1), clean(text2)
        if not s1 or not s2: return False
        if s1 == s2: return True
        return difflib.SequenceMatcher(None, s1, s2).ratio() > 0.95