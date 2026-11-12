"""赛事战报 · 运动风。

黑、电光黄、信号红三色高对比，斜切色块 + 粗黑底线 + 黄黑警示条，像赛事直播的计分板。
适合电竞、体育、发布会对决、“A vs B 怎么选”这类对比内容。

斜切靠 transform:skewX，被微信过滤时退化成直角色块，版式不受影响。
数字用 Arial Black 斜体（中文不斜，只有数字和英文斜），是这套风格的“速度感”来源。

Markdown 写法 → 战报组件：
  ## 标题                斜切黑块「ROUND / 01」+ 标题 + 3px 粗黑底线
                         （“附”开头的、或可编号的不足 2 个时：斜切红条 + 标题 + 底线）
  ### 标题               斜切红色短条 + 加粗标题
  第一个 ## 前的 1～3 段   导语：浅灰卡 + 左侧粗黑条 + 斜切黄标签「写在前面」
  **加粗**               信号红加粗
  *斜体*                 黑底黄字反白
  > 引用                 浅灰底 + 红色竖条
  > 💡 … / > ⚠️ …        小贴士（浅灰 + 黑底黄字标签）/ 注意（浅红 + 红底白字标签）
  - **10-1** GEN 小局    数据列表（1～3 项「**数值** 说明」）→ 黑色计分板；正好 2 项时中间加红色 VS
  - 列表 / 1. 列表       斜切红色小块 / 斜切黑底黄字数字
  ---                    黄黑警示条
  表格                   黑底白字表头，像赛程表
"""

from . import _engine
from ._engine import Theme, esc, fit_font

NAME = "赛事战报 · 运动风"

C = {
    "ink": "#111216",          # 墨黑：标题、色块、计分板
    "text": "#26272B",         # 正文
    "text_light": "#75777D",   # 次要文字
    "yellow": "#FFD60A",       # 电光黄：只当背景，或放在黑底上当字色
    "red": "#E5383B",          # 信号红：重点、VS、警示
    "gray_bg": "#F3F3F5",
    "red_bg": "#FDECEC",
    "line": "#E4E4E7",
}

NUM_FONT = "font-family:Arial Black,Arial,sans-serif;font-weight:900;font-style:italic;"
SKEW, UNSKEW = "transform:skewX(-12deg);", "transform:skewX(12deg);"
CARD = 'padding:12px 14px 4px 14px;margin:20px 0 22px 0;'
P_CARD = f'color:{C["text"]};font-size:14px;line-height:1.8;letter-spacing:.5px;margin:0 0 8px 0;text-align:justify;'


def skew_tag(text: str, bg: str, color: str, size: int = 12) -> str:
    """斜切标签：外层斜切，内层反向斜切，文字保持正立。"""
    return (f'<span style="display:inline-block;background:{bg};padding:2px 10px;margin-left:3px;{SKEW}">'
            f'<span style="display:inline-block;color:{color};font-size:{size}px;font-weight:bold;letter-spacing:1px;'
            f'line-height:1.6;{UNSKEW}">{text}</span></span>')


class MatchTheme(Theme):
    UL_MARK_W = 18

    STYLE = {
        "p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.5px;margin:0 0 16px 0;text-align:justify;',
        "h1": f'color:{C["ink"]};font-size:20px;font-weight:bold;line-height:1.5;margin:34px 0 16px 0;',
        "h2": (f'display:flex;align-items:stretch;color:{C["ink"]};font-size:18px;font-weight:bold;line-height:1.5;'
               f'margin:38px 0 16px 0;border-bottom:3px solid {C["ink"]};'),
        "h4": f'color:{C["ink"]};font-size:15px;font-weight:bold;line-height:1.6;margin:22px 0 10px 0;',
        "blockquote": CARD + f'background:{C["gray_bg"]};border-left:4px solid {C["red"]};',
        "quote_tip": CARD + f'background:{C["gray_bg"]};',
        "quote_warn": CARD + f'background:{C["red_bg"]};',
        "p_in_quote": P_CARD,
        "lead": CARD.replace("margin:20px 0 22px 0", "margin:0 0 28px 0") + f'background:{C["gray_bg"]};border-left:6px solid {C["ink"]};',
        "pre": f'margin:20px 0 22px 0;padding:14px 16px;background:{C["ink"]};overflow-x:auto;font-size:13px;line-height:1.7;',
        "pre_code": 'font-family:Consolas,Monaco,monospace;color:#EDEDED;',
        "code": f'font-family:Consolas,Monaco,monospace;background:{C["gray_bg"]};color:{C["ink"]};padding:1px 5px;font-size:14px;',
        "table": f'width:100%;border-collapse:collapse;font-size:13px;color:{C["text"]};margin:20px 0 22px 0;border-bottom:3px solid {C["ink"]};',
        "th": f'padding:8px 8px;background:{C["ink"]};color:#FFFFFF;font-weight:bold;text-align:left;',
        "td": f'padding:8px 8px;border-bottom:1px solid {C["line"]};',
        "a": f'color:{C["ink"]};text-decoration:none;border-bottom:2px solid {C["yellow"]};word-break:break-all;',
        "strong": f'color:{C["red"]};font-weight:bold;',
        "strong_in_heading": 'font-weight:bold;',
        "em": f'font-style:normal;font-weight:bold;background:{C["ink"]};color:{C["yellow"]};padding:0 4px;',
        "del": f'text-decoration:line-through;color:{C["text_light"]};',
        "img": 'max-width:100%;display:block;margin:10px auto;',
        "fig": f'margin:4px 0 22px 0;border-bottom:3px solid {C["ink"]};',
        "fig_img": 'display:block;max-width:100%;margin:0 auto;',
        "checkbox": 'margin-right:6px;vertical-align:middle;',
        "li_p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.5px;text-align:left;word-wrap:break-word;margin:0 0 10px 0;',
        "ul_mark": f'display:inline-block;width:9px;height:9px;background:{C["red"]};margin-right:9px;vertical-align:1px;{SKEW}',
    }

    def _num_block(self, num):
        # 斜切黑块：上小字 ROUND，下大号斜体数字；与粗黑底线连成一体
        return (f'<span style="flex:none;display:inline-block;background:{C["ink"]};padding:3px 12px 2px 12px;'
                f'margin:0 12px 0 4px;text-align:center;{SKEW}">'
                f'<span style="display:block;{UNSKEW}">'
                f'<span style="display:block;color:{C["yellow"]};font-size:8px;letter-spacing:2px;line-height:1.2;font-family:Arial,sans-serif;font-weight:bold;">ROUND</span>'
                f'<span style="display:block;color:{C["yellow"]};font-size:20px;line-height:1.1;{NUM_FONT}">{num}</span>'
                f'</span></span>')

    def h2(self, inner, num, idx):
        return (f'<h2 style="{self.STYLE["h2"]}">{self._num_block(num)}'
                f'<span style="flex:1;min-width:0;align-self:center;padding:4px 0;">{inner}</span></h2>')

    def h2_plain(self, inner):
        bar = f'flex:none;display:inline-block;width:8px;background:{C["red"]};margin:0 12px 0 3px;{SKEW}'
        return (f'<h2 style="{self.STYLE["h2"]}"><span style="{bar}"></span>'
                f'<span style="flex:1;min-width:0;padding:4px 0;">{inner}</span></h2>')

    def h3(self, inner):
        # 红条 margin-top = (16px × 1.6 行高 − 16px) / 2，对齐首行
        h3 = f'display:flex;align-items:flex-start;color:{C["ink"]};font-size:16px;font-weight:bold;line-height:1.6;margin:26px 0 10px 0;'
        bar = f'flex:none;width:6px;height:16px;background:{C["red"]};margin:5px 10px 0 2px;{SKEW}'
        return f'<h3 style="{h3}"><span style="{bar}"></span><span>{inner}</span></h3>'

    def quote_label(self, kind):
        tag = (skew_tag(self.QUOTE_LABELS[kind], C["ink"], C["yellow"]) if kind == "tip"
               else skew_tag(self.QUOTE_LABELS[kind], C["red"], "#FFFFFF"))
        return f'<p style="margin:0 0 8px 0;line-height:1;">{tag}</p>'

    def lead_label(self):
        return f'<p style="margin:0 0 8px 0;line-height:1;">{skew_tag(self.LEAD_LABEL, C["yellow"], C["ink"])}</p>'

    def hr(self):
        # 黄黑警示条；斜纹渐变被过滤时剩一条纯黄条
        return (f'<section style="height:8px;margin:32px 0;background-color:{C["yellow"]};'
                f'background-image:repeating-linear-gradient(-45deg,{C["ink"]} 0,{C["ink"]} 6px,transparent 6px,transparent 12px);"></section>')

    def figcap(self, cap, n):
        return (f'<p style="font-size:12px;line-height:1.6;color:{C["text_light"]};margin:-14px 0 22px 0;">'
                f'<span style="color:{C["red"]};font-weight:bold;margin-right:6px;{NUM_FONT}">▲ {n:02d}</span>{cap}</p>')

    def ul_mark(self, depth):
        return f'<span style="{self.STYLE["ul_mark"]}"></span>', 18

    def ol_mark(self, n, depth):
        box = (f'display:inline-block;min-width:22px;height:20px;line-height:20px;background:{C["ink"]};text-align:center;'
               f'text-indent:0;margin:0 9px 0 1px;vertical-align:1px;{SKEW}')
        digit = f'display:inline-block;color:{C["yellow"]};font-size:12px;{NUM_FONT}{UNSKEW}'
        return f'<span style="{box}"><span style="{digit}">{n}</span></span>', 32

    def stats(self, items):
        # 计分板：黑底，黄色斜体大数字；正好 2 项时是“对阵”，中间一枚红色 VS
        top = {1: 40, 2: 30, 3: 24}[len(items)]
        avail = {1: 280, 2: 110, 3: 86}[len(items)]
        fs = fit_font([v for v, _ in items], top, avail, 14)
        cells = []
        for value, label in items:
            cap = (f'<p style="font-size:11px;line-height:1.5;color:#B5B7BD;margin:4px 0 0 0;letter-spacing:.5px;">{esc(label)}</p>'
                   if label else "")
            cells.append(f'<section style="flex:1;min-width:0;text-align:center;padding:4px 2px;">'
                         f'<p style="font-size:{fs}px;line-height:1.1;color:{C["yellow"]};margin:0;white-space:nowrap;{NUM_FONT}">'
                         f'{esc(value)}</p>{cap}</section>')
        if len(items) == 2:
            vs = (f'<section style="flex:none;align-self:center;width:34px;height:34px;line-height:34px;border-radius:50%;'
                  f'background:{C["red"]};color:#FFFFFF;text-align:center;font-size:13px;margin:0 6px;{NUM_FONT}">VS</section>')
            cells.insert(1, vs)
        return (f'<section style="display:flex;align-items:stretch;background:{C["ink"]};padding:14px 10px;margin:20px 0 22px 0;'
                f'border-bottom:4px solid {C["yellow"]};">{"".join(cells)}</section>')


THEME = MatchTheme()


def build_html(md_body: str):
    """Markdown 正文 → (赛事战报排版 HTML, 图片 src 列表)。"""
    return _engine.build(THEME, md_body)
