"""编辑部 · 杂志社论。

暖白纸色底，衬线标题、双细线、罗马数字章节、首字下沉、居中的拉页金句，表格是三线表，像纸质杂志里的长文。
和 minimal 的区别：minimal 靠超大数字和留白，这套靠字体、细线这些排版细节。
适合深度长文、行业或人物故事、年度回顾。

很多安卓手机没有中文衬线字体，会退回黑体：细线、首字下沉、罗马数字这些识别符号都不依赖中文衬线字体。
正文保持黑体，手机上读长文更清楚。

Markdown 写法 → 杂志组件：
  （整篇）               包在暖白纸色容器里
  ## 标题                居中：双细线 + 红色罗马数字「— II —」+ 衬线大标题
                         （“附”开头的、或可编号的不足 2 个时：双细线 + 衬线标题）
  ### 标题               衬线加粗 + 下方细线
  第一个 ## 前的 1～3 段   导语：衬线大字 + 首字下沉 + 红色小字「写在前面」，下方细线收住
  **加粗**               墨黑加粗
  *斜体*                 深红加粗
  > 一句短话（≤60 字）    拉页金句：居中衬线 18px，上方红色大引号，上下细线
  > 较长的引用           衬线灰字 + 左侧红线
  > 💡 … / > ⚠️ …        细线框编者按（红色宽字距小标题）/ 双线框
  - 列表 / 1. 列表       深红小方块 / 深红衬线数字
  ---                    居中短双线
  ![说明](图.png)        「图 1　说明」，红色图号
  表格                   三线表：上下粗线，表头下细线
"""

import re
import unicodedata

from . import _engine
from ._engine import Theme, esc, fit_font, text_len

NAME = "编辑部 · 杂志社论"

C = {
    "paper": "#F8F5EE",        # 纸色底（外层容器）
    "ink": "#1A1A1A",          # 标题、粗线
    "text": "#2E2E2E",         # 正文
    "text_light": "#77736A",   # 图注、次要文字
    "red": "#A61B1B",          # 深红：罗马数字、首字、金句引号。全文少量使用
    "rule": "#D9D3C5",         # 细线
    "box": "#F1ECE1",          # 代码等浅底块
}

# Times New Roman 打头：Georgia 的数字是高低错落的旧式数字，夹在中文里像排错了；罗马数字章节号仍用 Georgia
SERIF = "font-family:Times New Roman,Songti SC,STSong,Noto Serif CJK SC,Source Han Serif SC,SimSun,serif;"
PULL_MAX = 60                  # 引用纯文字不超过这么多字时排成拉页金句
LEAD_FIRST_RE = re.compile(r'(<section data-lead="1">\s*<p>)([^<\s])')
QUOTE_RE = re.compile(r"<blockquote>(.*?)</blockquote>", re.S)
ROMAN = ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
CARD = 'padding:12px 16px 4px 16px;margin:24px 0 24px 0;'
P_CARD = f'color:{C["text"]};font-size:14px;line-height:1.85;letter-spacing:.3px;margin:0 0 8px 0;text-align:justify;'


def roman(n: int) -> str:
    out = ""
    for v, s in ROMAN:
        while n >= v:
            out += s
            n -= v
    return out


class EditorialTheme(Theme):
    CONTAINER = f'background:{C["paper"]};padding:26px 18px 30px 18px;color:{C["text"]};'
    UL_MARK_W = 16

    STYLE = {
        "p": f'color:{C["text"]};font-size:15px;line-height:1.9;letter-spacing:.3px;margin:0 0 18px 0;text-align:justify;',
        "h1": f'color:{C["ink"]};font-size:22px;font-weight:bold;line-height:1.4;margin:36px 0 16px 0;{SERIF}',
        "h2": (f'text-align:center;color:{C["ink"]};border-top:3px double {C["ink"]};padding-top:16px;'
               f'margin:46px 0 22px 0;line-height:1.45;'),
        "h4": f'color:{C["ink"]};font-size:15px;font-weight:bold;line-height:1.6;margin:22px 0 10px 0;{SERIF}',
        "blockquote": CARD.replace("padding:12px 16px 4px 16px", "padding:2px 0 2px 16px") + f'border-left:2px solid {C["red"]};',
        "quote_pull": (f'margin:34px 14px 34px 14px;padding:4px 0 10px 0;text-align:center;'
                       f'border-top:1px solid {C["ink"]};border-bottom:1px solid {C["ink"]};'),
        "quote_tip": CARD + f'border:1px solid {C["ink"]};',
        "quote_warn": CARD + f'border:3px double {C["ink"]};',
        "p_in_quote": f'color:{C["text_light"]};font-size:15px;line-height:1.85;margin:0 0 8px 0;text-align:justify;{SERIF}',
        "p_in_pull": f'color:{C["ink"]};font-size:18px;font-weight:bold;line-height:1.7;margin:0 0 6px 0;text-align:center;{SERIF}',
        "p_in_tip": P_CARD,
        "p_in_warn": P_CARD,
        "lead": 'margin:0 0 8px 0;',  # 不加底线：紧跟的 ## 自带双线，叠在一起重复
        # overflow:hidden 让段落包住下沉的首字，导语只有一行时首字也不会戳进下一段
        "p_in_lead": f'color:#3A3A3A;font-size:16px;line-height:1.9;margin:0 0 12px 0;text-align:justify;overflow:hidden;{SERIF}',
        "pre": f'margin:22px 0 24px 0;padding:14px 16px;background:{C["box"]};overflow-x:auto;font-size:13px;line-height:1.7;',
        "pre_code": f'font-family:Consolas,Monaco,monospace;color:{C["ink"]};',
        "code": f'font-family:Consolas,Monaco,monospace;background:{C["box"]};color:{C["ink"]};padding:1px 5px;font-size:14px;',
        "table": (f'width:100%;border-collapse:collapse;font-size:13px;color:{C["text"]};margin:24px 0 26px 0;'
                  f'border-top:2px solid {C["ink"]};border-bottom:2px solid {C["ink"]};'),
        "th": f'padding:8px 6px;border-bottom:1px solid {C["ink"]};font-weight:bold;text-align:left;color:{C["ink"]};{SERIF}',
        "td": f'padding:8px 6px;border-bottom:1px solid {C["rule"]};',
        "a": f'color:{C["red"]};text-decoration:none;border-bottom:1px solid {C["red"]};word-break:break-all;',
        "strong": f'color:{C["ink"]};font-weight:bold;',
        "strong_in_heading": 'font-weight:bold;',
        "em": f'font-style:normal;color:{C["red"]};font-weight:bold;',
        "del": f'text-decoration:line-through;color:{C["text_light"]};',
        "img": 'max-width:100%;display:block;margin:10px auto;',
        "fig": 'margin:6px 0 24px 0;',
        "fig_img": 'display:block;max-width:100%;margin:0 auto;',
        "checkbox": 'margin-right:6px;vertical-align:middle;',
        "li_p": f'color:{C["text"]};font-size:15px;line-height:1.85;letter-spacing:.3px;text-align:left;word-wrap:break-word;margin:0 0 10px 0;',
        "ul_mark": f'display:inline-block;width:5px;height:5px;background:{C["red"]};margin-right:11px;vertical-align:4px;',
        "ol_mark": (f'display:inline-block;min-width:20px;{SERIF}font-size:15px;font-weight:bold;color:{C["red"]};'
                    f'text-indent:0;margin-right:4px;'),
    }

    def _title(self, inner):
        return f'<span style="display:block;font-size:21px;font-weight:bold;{SERIF}">{inner}</span>'

    def h2(self, inner, num, idx):
        no = (f'display:block;font-size:13px;letter-spacing:4px;color:{C["red"]};margin-bottom:8px;'
              f'font-family:Georgia,Times New Roman,serif;')
        return f'<h2 style="{self.STYLE["h2"]}"><span style="{no}">— {roman(int(num))} —</span>{self._title(inner)}</h2>'

    def h2_plain(self, inner):
        return f'<h2 style="{self.STYLE["h2"]}">{self._title(inner)}</h2>'

    def h3(self, inner):
        h3 = (f'color:{C["ink"]};font-size:17px;font-weight:bold;line-height:1.6;margin:30px 0 12px 0;'
              f'padding-bottom:6px;border-bottom:1px solid {C["rule"]};{SERIF}')
        return f'<h3 style="{h3}">{inner}</h3>'

    def quote_label(self, kind):
        return (f'<p style="font-size:12px;font-weight:bold;letter-spacing:4px;line-height:1.6;color:{C["red"]};'
                f'margin:0 0 6px 0;">{self.QUOTE_LABELS[kind]}</p>')

    def lead_label(self):
        return (f'<p style="font-size:12px;font-weight:bold;letter-spacing:4px;line-height:1.6;color:{C["red"]};'
                f'margin:0 0 10px 0;">{self.LEAD_LABEL}</p>')

    def hr(self):
        return f'<section style="width:56px;height:0;margin:38px auto;border-top:3px double {C["ink"]};"></section>'

    def figcap(self, cap, n):
        return (f'<p style="font-size:12px;line-height:1.7;color:{C["text_light"]};margin:-14px 0 26px 0;">'
                f'<span style="color:{C["red"]};font-weight:bold;margin-right:8px;{SERIF}">图 {n}</span>{cap}</p>')

    def ul_mark(self, depth):
        return f'<span style="{self.STYLE["ul_mark"]}"></span>', 16

    def ol_mark(self, n, depth):
        return f'<span style="{self.STYLE["ol_mark"]}">{n}.</span>', 24

    def stats(self, items):
        # 数据栏：衬线大数字，栏与栏之间一道竖细线
        top = {1: 48, 2: 36, 3: 28}[len(items)]
        avail = {1: 290, 2: 130, 3: 84}[len(items)]
        fs = fit_font([v for v, _ in items], top, avail, 16)
        cells = []
        for i, (value, label) in enumerate(items):
            sep = f'border-left:1px solid {C["rule"]};' if i else ""
            cap = f'<p style="font-size:12px;line-height:1.6;color:{C["text_light"]};margin:4px 0 0 0;">{esc(label)}</p>' if label else ""
            cells.append(f'<section style="flex:1;min-width:0;text-align:center;padding:0 6px;{sep}">'
                         f'<p style="font-size:{fs}px;line-height:1.1;color:{C["red"]};margin:0;white-space:nowrap;'
                         f'font-family:Times New Roman,serif;">{esc(value)}</p>{cap}</section>')
        return (f'<section style="display:flex;padding:16px 0;margin:26px 0 28px 0;border-top:1px solid {C["ink"]};'
                f'border-bottom:1px solid {C["ink"]};">{"".join(cells)}</section>')

    def extra_decorate(self, html):
        # 短引用 → 拉页金句，上方加一枚红色大引号
        def quote(m):
            body = m.group(1)
            if (text_len(body) <= PULL_MAX and "<blockquote" not in body
                    and not re.search(r"<(?:ul|ol|pre|table|img)\b", body)):
                mark = (f'<p style="font-size:44px;line-height:1;color:{C["red"]};margin:6px 0 -6px 0;text-align:center;'
                        f'font-family:Georgia,Times New Roman,serif;">“</p>')
                return f'<blockquote data-kind="pull">{mark}{body}</blockquote>'
            return m.group(0)

        html = QUOTE_RE.sub(quote, html)

        # 导语首字下沉：只认汉字、字母、数字开头的段落
        def drop(m):
            ch = m.group(2)
            if not unicodedata.category(ch).startswith(("L", "N")):
                return m.group(0)
            cap = (f'float:left;font-size:50px;line-height:1;font-weight:bold;color:{C["red"]};'
                   f'margin:4px 8px 0 0;{SERIF}')
            return f'{m.group(1)}<span style="{cap}">{esc(ch)}</span>'

        return LEAD_FIRST_RE.sub(drop, html, count=1)


THEME = EditorialTheme()


def build_html(md_body: str):
    """Markdown 正文 → (杂志社论排版 HTML, 图片 src 列表)。"""
    return _engine.build(THEME, md_body)
