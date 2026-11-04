"""夸张极简 · Exaggerated Minimalism。

元素极少，但每个都放到极大：米白底、墨黑字、一个橙红强调色；字号极端对比、大量留白、
零装饰（不用卡片、阴影、圆角、图标）。适合观点文章、深度解读、年度盘点这类“一篇只讲一件大事”的特刊，
不适合每日快讯。

Markdown 写法 → 夸张极简组件：
  （整篇）               包在米白 #FAFAF7 外层容器里
  ## 标题                超大序号 01、02……（72px 橙红）+ 18px 小标题，整篇建议 3～4 节
                         （“附”开头的、或可编号的不足 2 个时：细线 + 小标题）
  ### 标题               16px 加粗，无装饰
  第一个 ## 前的 1～3 段   副标题：灰字 + 下方通栏细线
  **加粗**               正文重点只用加粗（强调色留给大元素）
  *斜体*                 细黑下划线；在金句里是橙红反白块
  > 一句短话（≤60 字）    大号金句 26px；里面的 *关键词* 橙红反白
  > 较长的引用           引语：17px + 左侧细黑线
  > …… / > —— 出处       引用最后一段以“——”开头时，排成极小的出处
  > 💡 … / > ⚠️ …        上下两条细线夹住的提示，小标题极小字宽字距
  - **3倍** 推理速度     数据列表（1～3 项「**数值** 说明」）：
                         1 项 → 96px 超大数据；2 项 → 双数据并排；3 项 → 三列。单位自动缩小
  单独一段「但是。」       超大关键词转场（1～4 个字 + 。！？…… 结尾），句号橙红
  - 列表 / 1. 列表       橙红斜杠 / 黑色两位数序号
  ---                    1px 墨黑通栏细线
  ![说明](图.png)        通栏图片 + FIG.01 式编号图注
  ```代码```             上下细线夹住的等宽文字

指南里的刊头行、超大标题（标题由微信渲染）、文末关注无法由 Markdown 表达，不自动生成。
"""

import re

from . import _engine
from ._engine import Theme, esc, nesting, text_len, visual_width

NAME = "夸张极简 · Exaggerated Minimalism"

C = {  # 米白 + 墨黑 + 橙红，规范见《夸张极简ExaggeratedMinimalism-公众号排版指南.md》
    "bg": "#FAFAF7",           # 米白底（外层容器）
    "ink": "#0A0A0A",          # 墨黑：超大序号以外的大元素、细线
    "text": "#333333",         # 正文
    "text_light": "#6B6B6B",   # 副标题、数据说明、图注
    "accent": "#FF4A1C",       # 橙红：序号、金句反白块、转场句号。全文 3～5 处为宜
}
# 想换强调色只改 C["accent"]：克莱因蓝 #1F3BFF、正红 #E60012。
# 荧光绿 #C6FF00 只能做反白块背景，要同时把 ACCENT_ON 改成墨黑，序号也要换回墨黑。
ACCENT_ON = C["bg"]  # 反白块上的文字色

NUM_FONT = "font-family:Helvetica,Arial,sans-serif;"  # 没有自定义字体，夸张感只能靠字号、粗细、字间距
LINE = f'1px solid {C["ink"]}'
CONTENT_W = 290          # 手机上容器内的可用宽度（px）：375 − 微信两侧留白 − 容器内边距 22×2，留一点余量
BIG_QUOTE_MAX = 60       # 引用纯文字不超过这么多字时排成大号金句
CITE_RE = re.compile(r"<p>\s*(?:——|—|－－|--)")
TRANSITION_RE = re.compile(r"<p>([一-鿿]{1,4})([。！？!?]|……|…)</p>")
NUMBER_RE = re.compile(r"([+\-−±~≈¥$€£]?\s*\d[\d.,]*)(.*)", re.S)


def split_unit(value: str):
    """“3倍”→（“3”，“倍”）：数值部分用大字号，单位缩到约 40%，数字才显得更大。"""
    m = NUMBER_RE.fullmatch(value)
    return (m.group(1), m.group(2).strip()) if m else (value, "")


def number_size(values, max_fs: int, avail: int) -> int:
    """一行数字统一字号：按最宽的那个自动缩小，避免意外换行，底边也齐。"""
    def width(v):
        num, unit = split_unit(v)
        return visual_width(num, 0.6) + 0.42 * visual_width(unit, 0.6)
    return max(24, min(max_fs, int(avail / max(max(width(v) for v in values), 0.6))))


def big_number(value: str, fs: int, color: str) -> str:
    num, unit = split_unit(value)
    ls = -max(1, round(fs / 24))  # 数字和英文的负字间距：96px 时 −4px
    unit_html = (f'<span style="font-size:{round(fs * 0.42)}px;letter-spacing:0;">{esc(unit)}</span>'
                 if unit else "")
    return (f'<p style="font-size:{fs}px;font-weight:bold;line-height:0.9;letter-spacing:{ls}px;color:{color};'
            f'white-space:nowrap;margin:0 0 8px 0;{NUM_FONT}">{esc(num)}{unit_html}</p>')


class MinimalTheme(Theme):
    CONTAINER = f'background:{C["bg"]};padding:28px 22px 32px 22px;color:{C["ink"]};'
    UL_MARK_W = 20

    STYLE = {
        # 正文小而疏，不小于 14px；整个小节结束后才留大空白（由下一个大元素的 margin-top 撑开）
        "p": f'color:{C["text"]};font-size:15px;line-height:1.85;letter-spacing:.5px;margin:0 0 16px 0;text-align:justify;',
        "h1": f'color:{C["ink"]};font-size:40px;font-weight:bold;line-height:1.08;letter-spacing:-1px;margin:48px 0 16px 0;',
        "h2": f'color:{C["ink"]};font-size:18px;font-weight:bold;line-height:1.5;margin:48px 0 12px 0;',
        "h4": f'color:{C["ink"]};font-size:15px;font-weight:bold;line-height:1.6;margin:22px 0 8px 0;',
        # 引语：17px + 左侧细黑线；大号金句见 quote_big
        "blockquote": f'margin:40px 0 40px 0;padding:2px 0 2px 16px;border-left:2px solid {C["ink"]};',
        "p_in_quote": f'color:{C["ink"]};font-size:17px;font-weight:bold;line-height:1.7;margin:0 0 12px 0;',
        "quote_big": 'margin:48px 0 48px 0;',
        "p_in_big": f'color:{C["ink"]};font-size:26px;font-weight:bold;line-height:1.35;margin:0 0 12px 0;',
        "em_in_big": f'font-style:normal;background:{C["accent"]};color:{ACCENT_ON};padding:0 4px;',
        "em_in_quote": f'font-style:normal;background:{C["accent"]};color:{ACCENT_ON};padding:0 4px;',
        "cite": f'color:{C["text_light"]};font-size:11px;font-weight:normal;line-height:1.6;letter-spacing:1px;margin:4px 0 0 0;',
        # 提示：零装饰，上下两条细线夹住
        "quote_tip": f'margin:40px 0 40px 0;padding:16px 0 8px 0;border-top:{LINE};border-bottom:{LINE};',
        "quote_warn": f'margin:40px 0 40px 0;padding:16px 0 8px 0;border-top:{LINE};border-bottom:{LINE};',
        "p_in_tip": f'color:{C["text"]};font-size:15px;line-height:1.85;letter-spacing:.5px;margin:0 0 8px 0;text-align:justify;',
        "p_in_warn": f'color:{C["text"]};font-size:15px;line-height:1.85;letter-spacing:.5px;margin:0 0 8px 0;text-align:justify;',
        # 副标题：灰字 + 下方通栏细线
        "lead": f'margin:0 0 8px 0;padding:0 0 20px 0;border-bottom:{LINE};',
        "p_in_lead": f'color:{C["text_light"]};font-size:15px;line-height:1.85;letter-spacing:.5px;margin:0 0 12px 0;text-align:justify;',
        "strong_in_lead": f'color:{C["ink"]};font-weight:bold;',
        "pre": f'margin:28px 0 28px 0;padding:12px 0;border-top:{LINE};border-bottom:{LINE};overflow-x:auto;font-size:13px;line-height:1.7;',
        "pre_code": f'font-family:Consolas,Monaco,monospace;color:{C["ink"]};',
        "code": f'font-family:Consolas,Monaco,monospace;background:#EEEDE8;color:{C["ink"]};padding:1px 4px;font-size:14px;',
        "hr": f'border-top:{LINE};margin:44px 0 44px 0;height:0;',
        "table": f'width:100%;border-collapse:collapse;font-size:14px;color:{C["text"]};margin:32px 0 32px 0;border-top:{LINE};border-bottom:{LINE};',
        "th": f'padding:10px 8px;color:{C["ink"]};font-size:12px;letter-spacing:1px;font-weight:bold;text-align:left;border-bottom:{LINE};',
        "td": 'padding:10px 8px;border-bottom:1px solid #E5E5E0;',
        "a": f'color:{C["ink"]};text-decoration:none;border-bottom:{LINE};word-break:break-all;',
        "strong": f'color:{C["ink"]};font-weight:bold;',
        "strong_in_heading": 'font-weight:bold;',
        "em": f'font-style:normal;color:{C["ink"]};border-bottom:{LINE};padding-bottom:1px;',
        "del": f'text-decoration:line-through;color:{C["text_light"]};',
        "img": 'max-width:100%;display:block;margin:10px auto;',
        "fig": 'margin:32px 0 44px 0;',
        "fig_img": 'display:block;max-width:100%;margin:0 auto;',
        "checkbox": 'margin-right:6px;vertical-align:middle;',
        "li_p": f'color:{C["ink"]};font-size:15px;line-height:1.8;letter-spacing:.5px;text-align:left;word-wrap:break-word;margin:0 0 10px 0;',
        "ul_mark": f'display:inline-block;width:20px;color:{C["accent"]};font-size:17px;font-weight:bold;text-indent:0;{NUM_FONT}',
        "ol_mark": f'display:inline-block;width:28px;color:{C["ink"]};font-size:14px;font-weight:bold;text-indent:0;{NUM_FONT}',
    }

    def style_for(self, tag, raw, kind, container, heading, in_pre, in_fig):
        if tag == "p" and raw.get("data-cite"):
            return self.STYLE["cite"]
        return super().style_for(tag, raw, kind, container, heading, in_pre, in_fig)

    def h2(self, inner, num, idx):
        # 核心识别符号：72px 强调色序号单独一行。white-space:nowrap 防止读者调大字号后序号被拆行
        no = (f'display:block;font-size:72px;line-height:0.9;letter-spacing:-2px;color:{C["accent"]};'
              f'white-space:nowrap;margin:0 0 10px 0;{NUM_FONT}')
        return (f'<h2 style="{self.STYLE["h2"]}"><span style="{no}">{num}</span>'
                f'<span style="display:block;">{inner}</span></h2>')

    def h2_plain(self, inner):
        # 不加细线：前面常常紧跟一条 --- 分割线，叠成两条反而乱
        return f'<h2 style="{self.STYLE["h2"]}">{inner}</h2>'

    def h3(self, inner):
        return f'<h3 style="color:{C["ink"]};font-size:16px;font-weight:bold;line-height:1.6;margin:28px 0 10px 0;">{inner}</h3>'

    def quote_label(self, kind):
        color = C["text_light"] if kind == "tip" else C["accent"]
        return (f'<p style="font-size:11px;letter-spacing:2px;line-height:1.6;color:{color};margin:0 0 8px 0;">'
                f'{self.QUOTE_LABELS[kind]}</p>')

    def hr(self):
        return f'<section style="{self.STYLE["hr"]}"></section>'

    def figcap(self, cap, n):
        # 编号图注：左 FIG.01，右说明；极小字号、宽字距
        return (f'<section style="display:flex;justify-content:space-between;align-items:flex-start;font-size:10px;'
                f'letter-spacing:1px;line-height:1.6;color:{C["text_light"]};margin:-36px 0 44px 0;">'
                f'<span style="flex:none;margin-right:16px;{NUM_FONT}">FIG.{n:02d}</span>'
                f'<span style="text-align:right;">{cap}</span></section>')

    def ul_mark(self, depth):
        return f'<span style="{self.STYLE["ul_mark"]}">/</span>', 20

    def ol_mark(self, n, depth):
        return f'<span style="{self.STYLE["ol_mark"]}">{n:02d}</span>', 28

    def stats(self, items):
        label = f'font-size:12px;line-height:1.7;color:{C["text_light"]};margin:0;'
        if len(items) == 1:
            # 超大数据：全文最重要的那个数字
            value, text = items[0]
            cap = f'<p style="{label}">{esc(text)}</p>' if text else ""
            return (f'<section style="margin:48px 0 48px 0;">'
                    f'{big_number(value, number_size([value], 96, CONTENT_W), C["ink"])}{cap}</section>')
        # 双数据并排 / 三列：最后一个用强调色
        max_fs, avail = (56, CONTENT_W // 2 - 10) if len(items) == 2 else (40, CONTENT_W // 3 - 8)
        fs = number_size([v for v, _ in items], max_fs, avail)
        cells = []
        for i, (value, text) in enumerate(items):
            color = C["accent"] if i == len(items) - 1 else C["ink"]
            cap = f'<p style="{label}">{esc(text)}</p>' if text else ""
            gap = "margin-right:12px;" if i < len(items) - 1 else ""
            cells.append(f'<section style="flex:1;min-width:0;{gap}">{big_number(value, fs, color)}{cap}</section>')
        return f'<section style="display:flex;margin:48px 0 48px 0;">{"".join(cells)}</section>'

    def extra_decorate(self, html):
        # 引用：最后一段以“——”开头的是出处；去掉出处后的纯文字够短就排成大号金句
        def quote(m):
            body = m.group(1)
            paras = re.findall(r"<p>.*?</p>", body, re.S)
            if paras and CITE_RE.match(paras[-1]):
                cite = paras[-1]
                body = body.replace(cite, '<p data-cite="1">' + cite[3:], 1)
                rest = text_len(body) - text_len(cite)
            else:
                rest = text_len(body)
            if "<blockquote" not in body and not re.search(r"<(?:ul|ol|pre|table|img)\b", body) and rest <= BIG_QUOTE_MAX:
                return f'<blockquote data-kind="big">{body}</blockquote>'
            return f"<blockquote>{body}</blockquote>"

        html = re.sub(r"<blockquote>(.*?)</blockquote>", quote, html, flags=re.S)

        # 超大关键词转场：单独成段的“但是。”“然而。”，只认顶层段落
        def transition(m):
            if nesting(html, m.start(), "li", "blockquote", "section"):
                return m.group(0)
            word, punct = m.group(1), m.group(2)
            fs = min(64, int(CONTENT_W / (len(word) + len(punct))))
            return (f'<section style="margin:56px 0 56px 0;"><p style="font-size:{fs}px;font-weight:bold;line-height:1;'
                    f'letter-spacing:-1px;color:{C["ink"]};white-space:nowrap;margin:0;">{word}'
                    f'<span style="color:{C["accent"]};">{punct}</span></p></section>')

        return TRANSITION_RE.sub(transition, html)


THEME = MinimalTheme()


def build_html(md_body: str):
    """Markdown 正文 → (夸张极简排版 HTML, 图片 src 列表)。"""
    return _engine.build(THEME, md_body)
