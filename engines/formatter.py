"""
文件路径: engines/formatter.py
=========================================================
【功能】
将 CitationData 对象转换为标准的 GB/T 7714-2015 字符串。
遵循最严格的国标规定：
1. 姓氏全部大写 (EINSTEIN)
2. 名字首字母大写，无缩写点 (A)
3. 支持 van, von 等复姓识别
4. 【精准版】支持中国学者拼音双名自动拆分 (Han Shaoheng -> HAN S H)
5. 【V4.0】智能纠正 API 返回的 "姓在前名在后" 格式
6. 【V5.0】新增中英文环境检测，自动切换 'et al' / '等'
7. 【V5.1 修复】修复页码显示为 "None-None" 的问题，无效页码自动隐藏
8. 【V6.5 新增】支持文章编号 (Article Number) 替代页码
9. 【V6.7 新增】支持 DOI 著录
10.【V6.8 终极国标化】支持英文题名 Sentence Case 转换、增强 [M] 图书识别
11.【V6.9】响应用户需求：仅“电子期刊”([J]且无页码)强制显示 DOI，其他类型默认隐藏。
=========================================================
"""

import re
import html
from .models.citation_model import CitationData

# === 1. 数据准备 (完整保留旧项目数据) ===
COMMON_CN_SURNAMES = {
    "LI", "WANG", "ZHANG", "LIU", "CHEN", "YANG", "ZHAO", "HUANG", "ZHOU", "WU",
    "XU", "SUN", "HU", "ZHU", "GAO", "LIN", "HE", "GUO", "MA", "LUO",
    "LIANG", "SONG", "ZHENG", "XIE", "HAN", "TANG", "FENG", "YU", "DONG", "XIAO",
    "CHENG", "CAO", "YUAN", "DENG", "FU", "SHEN", "ZENG", "PENG", "LV",
    "SU", "LU", "JIANG", "CAI", "JIA", "DING", "WEI", "XUE", "YE", "YAN",
    "PAN", "DU", "DAI", "XIA", "ZHONG", "TIAN", "REN", "FAN", "FANG", "SHI",
    "YAO", "TAN", "SHENG", "ZOU", "XIONG", "JIN", "HAO", "KONG", "BAI", "CUI",
    "KANG", "MAO", "QIU", "QIN", "GU", "HOU", "SHAO", "MENG", "LONG", "WAN",
    "DUAN", "QIAN", "YIN", "YI", "CHANG", "XI", "WEN", "NIE", "ZHUANG", "YAN",
    "QU", "GE", "PU", "BA", "BIE", "BING", "BO", "BU", "CEN", "CHAI", "CHE",
    "CHI", "CHU", "CHUAN", "CHUN", "CONG", "CUO", "DA", "DAN", "DAO", "DI",
    "DIAN", "DIAO", "DIE", "DOU", "DU", "DUN", "E", "EN", "ER", "FA", "FEI",
    "FO", "FOU", "GAI", "GAN", "GANG", "GEN", "GENG", "GONG", "GOU", "GUAN",
    "GUI", "GUN", "HAI", "HANG", "HEI", "HEN", "HENG", "HONG", "HUA", "HUAI",
    "HUAN", "HUI", "HUN", "HUO", "JI", "JIAN", "JIANG", "JIAO", "JIE", "JING",
    "JIONG", "JIU", "JU", "JUAN", "JUE", "JUN", "KA", "KAI", "KAN", "KAO", "KE",
    "KEN", "KENG", "KOU", "KU", "KUA", "KUAI", "KUAN", "KUANG", "KUI", "KUN",
    "KUO", "LA", "LAI", "LAN", "LANG", "LAO", "LE", "LEI", "LENG", "LIA", "LIAN",
    "LIAO", "LIE", "LIN", "LING", "LIU", "LONG", "LOU", "LUAN", "LUE", "LUN",
    "LUO", "MEI", "MEN", "MENG", "MI", "MIAN", "MIAO", "MIE", "MIN", "MING", "MIU",
    "MO", "MOU", "MU", "NA", "NAI", "NAN", "NANG", "NAO", "NE", "NEI", "NEN",
    "NENG", "NI", "NIAN", "NIANG", "NIAO", "NIE", "NIN", "NING", "NIU", "NONG",
    "NOU", "NU", "NUAN", "NUE", "NUO", "OU", "PA", "PAI", "PAN", "PANG", "PAO",
    "PEI", "PEN", "PENG", "PI", "PIAN", "PIAO", "PIE", "PIN", "PING", "PO", "POU",
    "QI", "QIA", "QIAN", "QIANG", "QIAO", "QIE", "QIN", "QING", "QIONG", "QIU",
    "QU", "QUAN", "QUE", "QUN", "RAN", "RANG", "RAO", "RE", "REN", "RENG", "RI",
    "RONG", "ROU", "RU", "RUAN", "RUI", "RUN", "RUO", "SA", "SAI", "SAN", "SANG",
    "SAO", "SE", "SEN", "SENG", "SHA", "SHAI", "SHAN", "SHANG", "SHE", "SHEI",
    "SHEN", "SHU", "SHUA", "SHUAI", "SHUAN", "SHUANG", "SHUI", "SHUN", "SHUO",
    "SI", "SONG", "SOU", "SUAN", "SUI", "SUN", "SUO", "TA", "TAI", "TAN", "TANG",
    "TAO", "TE", "TENG", "TI", "TIAN", "TIAO", "TIE", "TING", "TONG", "TOU", "TU",
    "TUAN", "TUI", "TUN", "TUO", "WA", "WAI", "WAN", "WANG", "WEI", "WEN", "WENG",
    "WO", "WU", "XI", "XIA", "XIAN", "XIANG", "XIAO", "XIE", "XIN", "XING", "XIONG",
    "XIU", "XU", "XUAN", "XUE", "XUN", "YA", "YAN", "YANG", "YAO", "YE", "YI",
    "YIN", "YING", "YONG", "YOU", "YU", "YUAN", "YUE", "YUN", "ZA", "ZAI", "ZAN",
    "ZANG", "ZAO", "ZE", "ZEI", "ZEN", "ZENG", "ZHA", "ZHAI", "ZHAN", "ZHANG",
    "ZHAO", "ZHE", "ZHEI", "ZHEN", "ZHENG", "ZHI", "ZHONG", "ZHOU", "ZHU", "ZHUA",
    "ZHUAI", "ZHUAN", "ZHUANG", "ZHUI", "ZHUN", "ZHUO", "ZI", "ZONG", "ZOU", "ZU",
    "ZUAN", "ZUI", "ZUN", "ZUO"
}

VALID_PINYINS = {
    "a", "ai", "an", "ang", "ao", "ba", "bai", "ban", "bang", "bao", "bei", "ben",
    "beng", "bi", "bian", "biao", "bie", "bin", "bing", "bo", "bu", "ca", "cai",
    "can", "cang", "cao", "ce", "cen", "ceng", "cha", "chai", "chan", "chang",
    "chao", "che", "chen", "cheng", "chi", "chong", "chou", "chu", "chua", "chuai",
    "chuan", "chuang", "chui", "chun", "chuo", "ci", "cong", "cou", "cu", "cuan",
    "cui", "cun", "cuo", "da", "dai", "dan", "dang", "dao", "de", "dei", "deng",
    "di", "dian", "diao", "die", "ding", "diu", "dong", "dou", "du", "duan", "dui",
    "dun", "duo", "e", "ei", "en", "eng", "er", "fa", "fan", "fang", "fei", "fen",
    "feng", "fo", "fou", "fu", "ga", "gai", "gan", "gang", "gao", "ge", "gei",
    "gen", "geng", "gong", "gou", "gu", "gua", "guai", "guan", "guang", "gui",
    "gun", "guo", "ha", "hai", "han", "hang", "hao", "he", "hei", "hen", "heng",
    "hong", "hou", "hu", "hua", "huai", "huan", "huang", "hui", "hun", "huo", "ji",
    "jia", "jian", "jiang", "jiao", "jie", "jin", "jing", "jiong", "jiu", "ju",
    "juan", "jue", "jun", "ka", "kai", "kan", "kang", "kao", "ke", "ken", "keng",
    "kong", "kou", "ku", "kua", "kuai", "kuan", "kuang", "kui", "kun", "kuo", "la",
    "lai", "lan", "lang", "lao", "le", "lei", "leng", "li", "lia", "lian", "liang",
    "liao", "lie", "lin", "ling", "liu", "long", "lou", "lu", "luan", "lue", "lun",
    "luo", "lv", "ma", "mai", "man", "mang", "mao", "me", "mei", "men", "meng",
    "mi", "mian", "miao", "mie", "min", "ming", "miu", "mo", "mou", "mu", "na",
    "nai", "nan", "nang", "nao", "ne", "nei", "nen", "neng", "ni", "nian", "niang",
    "niao", "nie", "nin", "ning", "niu", "nong", "nou", "nu", "nuan", "nue", "nuo",
    "nv", "o", "ou", "pa", "pai", "pan", "pang", "pao", "pei", "pen", "peng", "pi",
    "pian", "piao", "pie", "pin", "ping", "po", "pou", "pu", "qi", "qia", "qian",
    "qiang", "qiao", "qie", "qin", "qing", "qiong", "qiu", "qu", "quan", "que",
    "qun", "ran", "rang", "rao", "re", "ren", "reng", "ri", "rong", "rou", "ru",
    "ruan", "rui", "run", "ruo", "sa", "sai", "san", "sang", "sao", "se", "sen",
    "seng", "sha", "shai", "shan", "shang", "shao", "she", "shei", "shen", "sheng",
    "shi", "shou", "shu", "shua", "shuai", "shuan", "shuang", "shui", "shun",
    "shuo", "si", "song", "sou", "su", "suan", "sui", "sun", "suo", "ta", "tai",
    "tan", "tang", "tao", "te", "teng", "ti", "tian", "tiao", "tie", "ting",
    "tong", "tou", "tu", "tuan", "tui", "tun", "tuo", "wa", "wai", "wan", "wang",
    "wei", "wen", "weng", "wo", "wu", "xi", "xia", "xian", "xiang", "xiao", "xie",
    "xin", "xing", "xiong", "xiu", "xu", "xuan", "xue", "xun", "ya", "yan", "yang",
    "yao", "ye", "yi", "yin", "ying", "yong", "you", "yu", "yuan", "yue", "yun",
    "za", "zai", "zan", "zang", "zao", "ze", "zei", "zen", "zeng", "zha", "zhai",
    "zhan", "zhang", "zhao", "zhe", "zhei", "zhen", "zheng", "zhi", "zhong",
    "zhou", "zhu", "zhua", "zhuai", "zhuan", "zhuang", "zhui", "zhun", "zhuo",
    "zi", "zong", "zou", "zu", "zuan", "zui", "zun", "zuo"
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    clean_str = re.sub(r'<[^>]+>', '', text)
    clean_str = html.unescape(clean_str)
    return clean_str.strip()


def try_split_pinyin(given_name: str) -> str:
    given_name = given_name.strip()
    length = len(given_name)
    if length < 3 or length > 12: return given_name
    if given_name.lower() in VALID_PINYINS: return given_name
    for i in range(1, length):
        part1 = given_name[:i].lower()
        part2 = given_name[i:].lower()
        if part1 in VALID_PINYINS and part2 in VALID_PINYINS:
            return f"{given_name[:i]} {given_name[i:]}"
    return given_name


def format_western_name(name_str: str) -> str:
    """西文人名格式化：姓前名后，姓大写，名首字母"""
    name_str = clean_text(name_str)
    if not name_str: return ""
    if re.search(r'[\u4e00-\u9fff]', name_str): return name_str

    surname_prefixes = ['van', 'von', 'de', 'du', 'da', 'del', 'la', 'le']
    family, given = "", ""

    if ',' in name_str:
        parts = name_str.split(',', 1)
        family = parts[0].strip()
        given = parts[1].strip()
    else:
        tokens = name_str.split()
        if not tokens: return ""
        if len(tokens) == 1: return tokens[0].upper()
        if len(tokens) > 2 and tokens[-2].lower() in surname_prefixes:
            family = " ".join(tokens[-2:])
            given = " ".join(tokens[:-2])
        else:
            family = tokens[-1]
            given = " ".join(tokens[:-1])
            # 反序纠错逻辑...
            first_token_upper = tokens[0].upper()
            is_family_hyphenated = '-' in family
            is_first_token_cn_surname = first_token_upper in COMMON_CN_SURNAMES
            family_upper = family.upper()
            is_family_cn_surname = family_upper in COMMON_CN_SURNAMES
            should_swap = False
            if is_family_hyphenated and is_first_token_cn_surname:
                should_swap = True
            elif len(tokens) == 2 and (not is_family_cn_surname) and is_first_token_cn_surname:
                should_swap = True
            if should_swap:
                family = tokens[0]
                given = " ".join(tokens[1:])

    family_fmt = family.upper()
    if family_fmt in COMMON_CN_SURNAMES and ' ' not in given and '-' not in given:
        given = try_split_pinyin(given)

    given_clean = given.replace('.', ' ').replace('-', ' ')
    given_tokens = given_clean.split()
    given_initials = [t[0].upper() for t in given_tokens if t]
    given_fmt = " ".join(given_initials)

    return f"{family_fmt} {given_fmt}" if given_fmt else family_fmt


def has_chinese_char(text: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def format_authors(authors: list) -> str:
    """格式化作者列表 (前3位 + 等/et al)"""
    if not authors: return "[佚名]"
    formatted_authors = []
    cn_name_count = 0
    for auth in authors:
        if has_chinese_char(auth):
            cn_name_count += 1
            formatted_authors.append(auth.strip())
        else:
            formatted_authors.append(format_western_name(auth))

    is_chinese_context = False
    if authors and has_chinese_char(authors[0]): is_chinese_context = True

    if len(formatted_authors) > 3:
        suffix = ", 等" if is_chinese_context else ", et al"
        return ", ".join(formatted_authors[:3]) + suffix
    else:
        return ", ".join(formatted_authors)


def _smart_title_case(title: str) -> str:
    """
    【智能转换题名大小写】
    国标要求英文文章题名采用 Sentence case (首词首字母大写，其余小写)。
    但为了防止将专有名词 (如 DNA, AI, China) 错误转为小写，采用保守策略：
    1. 只有当标题是 "全部大写" 时，才强制转为 Sentence case。
    2. 否则，保持原样 (信任数据源的 Title Case)。
    """
    if not title: return ""

    # 检测是否全是中文
    if has_chinese_char(title):
        return title

    # 检测是否全大写 (允许少量的非字母字符)
    # 比如 "EFFECTS OF AI ON..."
    clean_t = re.sub(r'[^a-zA-Z]', '', title)
    if clean_t and clean_t.isupper():
        # 强制转为 Sentence case: 首字母大写，其余小写
        # 注意：这里会把 AI 变成 Ai，但在数据源极其糟糕(全大写)的情况下，这是这种妥协
        # 更好的做法是 capitalize() 整个句子
        return title.capitalize()

    return title


def to_gbt7714(data: CitationData) -> str:
    """转换为国标字符串"""

    # 1. 作者
    authors_str = format_authors(data.authors)

    # 2. 题名 (应用智能大小写转换)
    title = clean_text(data.title)
    if not has_chinese_char(title):
        title = _smart_title_case(title)

    source = clean_text(data.source)

    # 3. 文献类型标识
    doc_type = "[J]"  # 默认期刊
    lower_source = source.lower()

    if "conference" in lower_source or "proceedings" in lower_source:
        doc_type = "[C]"  # 会议
    elif "thesis" in lower_source or "dissertation" in lower_source:
        doc_type = "[D]"  # 学位论文
    elif "press" in lower_source or "publishing" in lower_source or "出版社" in source:
        # 如果来源包含“出版社”，则极大可能是图书
        doc_type = "[M]"  # 图书

    # 拼装主体: 作者. 题名[类型].
    result = f"{authors_str}. {title}{doc_type}"

    # 4. 来源与出版信息
    if source: result += f". {source}"
    if data.year: result += f", {data.year}"

    # 5. 卷期页信息
    if doc_type == "[M]":
        # 如果是图书，不需要卷期，通常格式是: 出版地: 出版者, 年: 页码.
        # 由于 API 通常不返回出版地，这里只能展示: 出版社, 年: 页码.
        pass
    else:
        # 期刊/会议的标准格式
        if data.volume:
            result += f", {data.volume}"
            if data.issue: result += f"({data.issue})"
        elif data.issue:
            result += f"({data.issue})"

    # === 页码清洗 ===
    has_pages = False
    if data.pages:
        clean_pages = re.sub(r'(?i)(none|null)', '', str(data.pages))
        clean_pages = clean_pages.replace(" ", "").replace("--", "-").strip("-")
        if clean_pages:
            result += f": {clean_pages}"
            has_pages = True

    # === 电子资源判定与文章编号 ===
    is_electronic_resource = False

    # 如果没有页码，但有文章编号，则使用文章编号
    if not has_pages and data.article_number:
        clean_art_no = str(data.article_number).strip()
        clean_art_no = re.sub(r'(?i)(none|null)', '', clean_art_no)
        if clean_art_no:
            result += f": {clean_art_no}"
            is_electronic_resource = True

    # 既无页码也无文章编号，判定为电子资源 (Online First等)
    if not has_pages and not is_electronic_resource:
        is_electronic_resource = True

    # === DOI 著录 (智能判断电子资源) ===
    # 【修改】响应用户需求：只有“电子期刊”([J] 且被认定为电子资源) 才加 DOI。
    # 其他类型(如 [M], [C]) 即使是电子版也不加，除非以后有特殊需求。
    if data.doi and is_electronic_resource and doc_type == "[J]":
        clean_doi = data.doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
        clean_doi = clean_doi.replace("doi:", "").replace("DOI:", "").strip()

        if clean_doi:
            result += f". DOI:{clean_doi}"

    result += "."
    return result