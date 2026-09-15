"""
文件路径: core/doc_parser.py
=========================================================
【功能】
负责解析 Word 文档。
1. 【核心优化】支持“阅读顺序”扫描。
2. 【新增】支持参考文献在文档中间的情况。
3. 【V5.9】支持上下文类型识别 (正文/表格/图注)。
4. 【V6.0】支持“分节”识别 (Heading/Checkpoint)，实现局部延后编号。
5. 【V6.1】新增 preview_text 字段，支持前端选择性延后。
6. 【V6.2】支持容器级聚合 (container_id)，按图/表分组。
7. 【V6.3】表格名称智能提取：自动关联表格上方的“表注”内容。
=========================================================
"""

import re
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.oxml.ns import qn
from .utils import CITATION_PATTERN, BIB_SECTION_KEYWORDS, parse_citation_ranges, is_likely_section_header


class DocParser:
    def __init__(self, file_path):
        self.doc = Document(file_path)
        # 章节计数器，用于实现“局部延后”
        self.current_section_index = 0
        # 容器计数器
        self.table_counter = 0

    def parse(self):
        """
        解析文档，返回:
        1. body_citations: 正文引用列表 (含上下文标记、章节标记、容器标记)
        2. raw_bibs: 文末参考文献原文列表
        """
        body_citations = []
        raw_bibs = []

        # 1. 定位参考文献的起始段落
        bib_start_para = self._find_bib_start_paragraph()

        # 状态标记：是否处于参考文献区
        in_bib_section = False

        # 【新增】用于暂存最近遇到的“表注”文本
        last_potential_table_caption = None

        if bib_start_para is None:
            pass

        # 2. 按照"阅读顺序"遍历文档所有块 (段落 + 表格)
        for i, block in enumerate(self._iter_block_items(self.doc)):

            if isinstance(block, Paragraph):
                # 检查是否进入参考文献区
                if bib_start_para is not None and block._element == bib_start_para._element:
                    in_bib_section = True
                    continue

                if in_bib_section:
                    # === 检查是否退出了参考文献区 ===
                    text = block.text.strip()
                    if self._is_section_boundary(block):
                        in_bib_section = False
                        self.current_section_index += 1
                        self._scan_citations_in_text(block.text, body_citations, context_type='text')
                        # 新章节开始，清空之前的表名缓存
                        last_potential_table_caption = None
                    else:
                        if text: raw_bibs.append(text)
                else:
                    # === 正文区 ===

                    if self._is_section_boundary(block):
                        self.current_section_index += 1
                        last_potential_table_caption = None

                    text = block.text.strip()

                    # 智能判断：这是普通正文，还是图片/表格的标题(Caption)
                    ctx = 'text'
                    container_info = None

                    if self._is_caption(block):
                        ctx = 'caption'

                        # 【核心逻辑】如果是 Caption，检查是否包含“表”字
                        if "表" in text or "Table" in text:
                            last_potential_table_caption = text

                        # 图注本身也是一个容器，它的名字就是它自己
                        preview = text
                        if len(preview) > 40: preview = preview[:40] + "..."
                        container_info = {
                            "id": f"caption_{i}",
                            "name": f"【图注】{preview}"
                        }
                    else:
                        # 如果是普通非空段落，说明它隔断了 Caption 和 Table 的联系
                        if text:
                            last_potential_table_caption = None

                    self._scan_citations_in_text(block.text, body_citations, context_type=ctx,
                                                 container_info=container_info)

            elif isinstance(block, Table):
                if in_bib_section:
                    in_bib_section = False
                    self.current_section_index += 1

                self.table_counter += 1

                # 【核心逻辑】确定表格名称
                if last_potential_table_caption:
                    preview_name = last_potential_table_caption
                    last_potential_table_caption = None
                else:
                    preview_name = f"表格 {self.table_counter}"
                    try:
                        first_cell = block.rows[0].cells[0].text.strip()
                        if first_cell:
                            if len(first_cell) > 15: first_cell = first_cell[:15] + "..."
                            preview_name += f": {first_cell}"
                    except:
                        pass

                if len(preview_name) > 50:
                    preview_name = preview_name[:50] + "..."

                table_info = {
                    "id": f"table_{self.table_counter}",
                    "name": preview_name
                }

                # 扫描表格
                self._scan_table(block, body_citations, table_info)

                last_potential_table_caption = None

        return body_citations, raw_bibs

    def _iter_block_items(self, parent):
        """核心生成器：按文档 XML 顺序产生 Paragraph 或 Table 对象"""
        if parent is self.doc:
            parent_elm = parent.element.body
        elif hasattr(parent, '_element'):
            parent_elm = parent._element
        else:
            return

        for child in parent_elm.iterchildren():
            if child.tag == qn('w:p'):
                yield Paragraph(child, parent)
            elif child.tag == qn('w:tbl'):
                yield Table(child, parent)

    def _scan_table(self, table, citations_list, container_info=None):
        """递归扫描表格内容"""
        for row in table.rows:
            for cell in row.cells:
                for block in self._iter_block_items(cell):
                    if isinstance(block, Paragraph):
                        self._scan_citations_in_text(block.text, citations_list, context_type='table',
                                                     container_info=container_info)
                    elif isinstance(block, Table):
                        self._scan_table(block, citations_list, container_info)

    def _find_bib_start_paragraph(self):
        """倒序扫描，找到“参考文献”标题所在的段落对象"""
        paras = self.doc.paragraphs
        for i in range(len(paras) - 1, -1, -1):
            text = paras[i].text.strip().lower()
            if len(text) < 20:
                for kw in BIB_SECTION_KEYWORDS:
                    if kw in text:
                        return paras[i]
        return None

    def _is_section_boundary(self, paragraph):
        """判断是否为章节分界线"""
        text = paragraph.text.strip()
        if text == '[---]': return True
        if paragraph.style and paragraph.style.name:
            style_name = paragraph.style.name.lower()
            if style_name.startswith('heading 1') or style_name == '标题 1':
                return True
        if is_likely_section_header(text):
            return True
        return False

    def _is_caption(self, paragraph):
        """判断一个段落是否可能是图注或表注"""
        if paragraph.style and paragraph.style.name:
            style_name = paragraph.style.name.lower()
            if 'caption' in style_name or '题注' in style_name:
                return True
        text = paragraph.text.strip()
        if len(text) > 100: return False
        if re.match(r'^(图|表|Figure|Table|Fig\.)\s*\d+', text, re.IGNORECASE):
            return True
        return False

    def _scan_citations_in_text(self, text, citations_list, context_type='text', container_info=None):
        """正则匹配文本中的引用"""
        if not text.strip():
            return

        matches = CITATION_PATTERN.finditer(text)
        for m in matches:
            inner_text = m.group(1)
            nums = parse_citation_ranges(inner_text)

            preview = text.strip().replace('\n', ' ')
            if len(preview) > 60:
                preview = preview[:60] + "..."

            cit_data = {
                'full_match': m.group(0),
                'inner_text': inner_text,
                'nums': nums,
                'context': context_type,
                'section_idx': self.current_section_index,
                'original_idx': len(citations_list),
                'preview_text': preview
            }

            if container_info:
                cit_data['container_id'] = container_info['id']
                cit_data['container_name'] = container_info['name']

            citations_list.append(cit_data)