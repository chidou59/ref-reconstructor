"""
文件路径: core/utils.py
=========================================================
【功能】
存放正则表达式和通用字符串处理函数。
辅助 doc_parser 识别各种格式的引用。
【更新 V6.6】
1. 增强 CITATION_PATTERN：支持 [1][2] 或 [1] [2] 这种连续引用格式的捕获与合并。
2. 增强 parse_citation_ranges：支持中文逗号分隔及相邻方括号的自动清洗。
【更新 V7.0 (本次更新)】
1. 智能识别模糊引用格式：
   - 支持 [3]-[5] (标准连字符连接两个括号)
   - 支持 [3]-5] (右侧括号缺失或错位)
   - 支持 [3-[5] (左侧括号缺失或错位)
   - 支持 [3, 4] 及 [3，4] (中英文逗号混用)
=========================================================
"""

import re

# === 正则表达式常量 ===

# 1. 宽松匹配引用标记 (Smart Fuzzy Match)
# 原逻辑：严格匹配成对的 [ ]
# 新逻辑：只要以 [ 开头，以 ] 结尾，且中间只包含 "数字、空格、逗号(中英)、连字符、内部方括号"，即视为一个引用块。
# 这样可以捕获 [3]-5] 或 [3-[5] 或 [1] [2] 或 [1]-[3] 等所有变体。
# 字符集说明：\d (数字), \s (空格), ,， (逗号), –- (连字符), \[\] (方括号)
CITATION_PATTERN = re.compile(r'(\[(?:[\d\s,，–\-\[\]]+)\])')

# 2. 宽松匹配参考文献列表项 (用于识别文末的列表)
# 匹配: "[1] ...", "1. ...", "(1) ...", "1、..."
BIB_ITEM_PATTERN = re.compile(r'^\s*(\[\d+\]|\d+\.|\(\d+\)|\d+、)\s*(.*)')

# 3. 参考文献章节标题关键词 (用于定位哪里开始是参考文献)
BIB_SECTION_KEYWORDS = ["参考文献", "reference", "bibliography", "引用文献"]

# 4. 章节标题识别模式 (用于判断参考文献何时结束)
# 匹配: "一、", "二、", "1.", "2.", "1、", "第一章"
SECTION_HEADER_PATTERN = re.compile(
    r'^\s*(?:[一二三四五六七八九十]+、|第[一二三四五六七八九十]+章|[1-9]\d*\.|[1-9]\d*、)\s*')


def parse_citation_ranges(text_block: str) -> list:
    """
    解析引用字符串，提取所有涉及的数字。
    输入可能是 "1-3", "[3]-[5]", "[3]-5]", "[3-[5]", "[1, 3，5]"
    返回: [1, 3, 4, 5]
    """
    nums = set()

    # === 预处理：归一化 ===

    # 1. 处理 [6]-[8] 这种情况：把 ]-[ (以及中间可能的空格) 替换为 -
    # 结果: [6-8]
    s = re.sub(r'\]\s*[-–]\s*\[', '-', text_block)

    # 2. 处理 [1][2] 或 [1] [2] (相邻括号) 这种情况
    # 逻辑：如果两个方括号之间不是连字符（已被上面处理掉），那就默认它们是并列关系，用逗号连接
    # 结果: [1,2]
    s = re.sub(r'\][\s,，]*\[', ',', s)

    # 3. 【核心清洗】彻底去掉所有的 [ 和 ]
    # 因为 Regex 已经保证了我们只抓取了包含数字和分隔符的块，
    # 所以像 [3]-5] 或 [3-[5] 这种格式，去掉括号后都会变成干净的 3-5
    s = s.replace('[', '').replace(']', '')

    # 4. 替换中文逗号 (防止用户在括号内写中文逗号)
    s = s.replace('，', ',')

    # 现在字符串应该是类似 "1, 3-5, 6-8" 的纯净格式

    # 按逗号分割
    parts = re.split(r'\s*,\s*', s)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # 统一连字符格式 (处理 - – —)
        if '-' in part or '–' in part or '—' in part:
            # 找到具体是哪种分隔符
            splitter = '-'
            if '–' in part:
                splitter = '–'
            elif '—' in part:
                splitter = '—'

            try:
                # 处理区间，如 6-8
                sub_parts = part.split(splitter)
                # 取首尾（防止 1-2-3 这种奇怪写法）
                if len(sub_parts) >= 2:
                    start_str = sub_parts[0].strip()
                    end_str = sub_parts[-1].strip()
                    if start_str.isdigit() and end_str.isdigit():
                        start, end = int(start_str), int(end_str)
                        # 安全限制：防止 [1-9999] 这种错误导致内存爆炸
                        if start <= end < start + 1000:
                            nums.update(range(start, end + 1))
                        else:
                            # 如果区间太离谱或倒序，只取端点
                            nums.add(start)
                            nums.add(end)
            except ValueError:
                pass
        else:
            try:
                if part.isdigit():
                    nums.add(int(part))
            except ValueError:
                pass

    return sorted(list(nums))


def is_likely_section_header(text: str) -> bool:
    """判断是否像一个新的章节标题（辅助判断参考文献结束）"""
    text = text.strip()
    if not text: return False
    # 标题通常不长，比如超过50个字就不太像标题了
    if len(text) > 50: return False

    return bool(SECTION_HEADER_PATTERN.match(text))