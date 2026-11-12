"""终端 · 命令行。

白底，墨绿提示符 + 琥珀色警告，等宽字体只用在提示符、编号、标签这些英文数字上（中文没有等宽字体），
像在终端里读一篇教程。代码块带窗口标题栏。不做整篇黑底：深色模式下微信自动反色，大面积黑底容易出怪色。
适合配置教程、命令行工具、独立开发。

Markdown 写法 → 终端组件：
  ## 标题                上一行灰色注释「# 01 ----」，下一行「$ 标题」
                         （“附”开头的、或可编号的不足 2 个时：只有「$ 标题」）
  ### 标题               「> 标题」
  第一个 ## 前的 1～3 段   导语：浅灰圆角块 + 注释式标签「# 写在前面」
  **加粗**               浅绿底深绿字，像终端里选中的文字
  *斜体*                 绿色虚线下划线
  > 引用                 灰色竖线 + 灰字
  > 💡 … / > ⚠️ …        日志行：「[INFO] 小贴士」绿 / 「[WARN] 注意」琥珀
  - 列表 / 1. 列表       绿色「-」/ 绿色「[1]」
  ---                    灰色虚线
  ![说明](图.png)        图片下方「↑ 说明」
  ```代码```             深色终端窗口，顶部三个圆点标题栏
"""

import re

from . import _engine
from ._engine import Theme, esc

NAME = "终端 · 命令行"

C = {
    "ink": "#1F2328",          # 标题
    "text": "#2D333B",         # 正文
    "text_light": "#6E7781",   # 注释、次要文字
    "green": "#15803D",        # 提示符、重点（浅底上的字色）
    "green_bg": "#E9F8EE",
    "amber": "#B45309",        # 警告
    "amber_bg": "#FFF5E5",
    "gray_bg": "#F6F8FA",
    "line": "#D0D7DE",
    "term_bg": "#161B22",      # 终端窗口
    "term_bar": "#2A313C",
    "term_text": "#E6EDF3",
}

MONO = "font-family:Menlo,Consolas,Monaco,Courier New,monospace;"
CARD = 'padding:10px 14px 2px 14px;margin:20px 0 22px 0;border-radius:6px;'
P_CARD = f'color:{C["text"]};font-size:14px;line-height:1.8;letter-spacing:.3px;margin:0 0 8px 0;text-align:justify;'
PRE_RE = re.compile(r"<pre>(.*?)</pre>", re.S)


def log_tag(level: str, text: str, color: str) -> str:
    return (f'<p style="margin:0 0 6px 0;font-size:12px;line-height:1.6;">'
            f'<span style="{MONO}font-weight:bold;color:{color};margin-right:6px;">[{level}]</span>'
            f'<span style="font-weight:bold;color:{color};">{text}</span></p>')


class TermTheme(Theme):
    UL_MARK_W = 16

    STYLE = {
        "p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.3px;margin:0 0 16px 0;text-align:justify;',
        "h1": f'color:{C["ink"]};font-size:20px;font-weight:bold;line-height:1.5;margin:32px 0 14px 0;',
        "h2": f'color:{C["ink"]};font-size:18px;font-weight:bold;line-height:1.5;margin:36px 0 14px 0;',
        "h4": f'color:{C["ink"]};font-size:15px;font-weight:bold;line-height:1.6;margin:20px 0 8px 0;',
        "blockquote": 'padding:2px 0 2px 14px;margin:20px 0 22px 0;' + f'border-left:3px solid {C["line"]};',
        "quote_tip": CARD + f'background:{C["green_bg"]};border-left:3px solid {C["green"]};border-radius:0 6px 6px 0;',
        "quote_warn": CARD + f'background:{C["amber_bg"]};border-left:3px solid {C["amber"]};border-radius:0 6px 6px 0;',
        "p_in_quote": P_CARD.replace(f'color:{C["text"]}', f'color:{C["text_light"]}'),
        "p_in_tip": P_CARD,
        "p_in_warn": P_CARD,
        "lead": CARD.replace("margin:20px 0 22px 0", "margin:0 0 26px 0") + f'background:{C["gray_bg"]};border:1px solid {C["line"]};',
        "p_in_lead": P_CARD,
        "pre": (f'margin:0;padding:12px 14px 14px 14px;background:{C["term_bg"]};overflow-x:auto;font-size:13px;line-height:1.7;'
                f'border-radius:0 0 8px 8px;'),
        "pre_code": f'{MONO}color:{C["term_text"]};',
        "code": f'{MONO}background:{C["gray_bg"]};color:{C["ink"]};padding:1px 5px;border:1px solid {C["line"]};border-radius:4px;font-size:13px;',
        "table": f'width:100%;border-collapse:collapse;font-size:13px;color:{C["text"]};margin:20px 0 22px 0;',
        "th": f'padding:7px 8px;background:{C["gray_bg"]};color:{C["ink"]};font-weight:bold;text-align:left;border:1px solid {C["line"]};',
        "td": f'padding:7px 8px;border:1px solid {C["line"]};',
        "a": f'color:{C["green"]};text-decoration:none;border-bottom:1px solid {C["green"]};word-break:break-all;',
        "strong": f'color:#14532D;font-weight:bold;background:{C["green_bg"]};padding:0 3px;',
        "strong_in_heading": 'font-weight:bold;',
        "em": f'font-style:normal;color:{C["ink"]};border-bottom:1px dashed {C["green"]};',
        "del": f'text-decoration:line-through;color:{C["text_light"]};',
        "img": f'max-width:100%;display:block;margin:10px auto;border:1px solid {C["line"]};border-radius:6px;',
        "fig": 'margin:4px 0 22px 0;',
        "fig_img": f'display:block;max-width:100%;margin:0 auto;border:1px solid {C["line"]};border-radius:6px;',
        "checkbox": 'margin-right:6px;vertical-align:middle;',
        "li_p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.3px;text-align:left;word-wrap:break-word;margin:0 0 8px 0;',
        "ul_mark": f'display:inline-block;width:16px;{MONO}font-weight:bold;color:{C["green"]};text-indent:0;',
        "ol_mark": f'display:inline-block;width:28px;{MONO}font-size:13px;font-weight:bold;color:{C["green"]};text-indent:0;',
    }

    def _prompt_row(self, inner, sign="$"):
        return (f'<span style="display:flex;align-items:flex-start;">'
                f'<span style="flex:none;{MONO}color:{C["green"]};margin-right:10px;">{sign}</span>'
                f'<span style="flex:1;min-width:0;">{inner}</span></span>')

    def h2(self, inner, num, idx):
        comment = (f'<span style="display:flex;align-items:center;{MONO}font-size:12px;font-weight:normal;'
                   f'color:{C["text_light"]};line-height:1.6;margin-bottom:4px;">'
                   f'<span style="flex:none;margin-right:8px;"># {num}</span>'
                   f'<span style="flex:1;border-top:1px dashed {C["line"]};"></span></span>')
        return f'<h2 style="{self.STYLE["h2"]}">{comment}{self._prompt_row(inner)}</h2>'

    def h2_plain(self, inner):
        return f'<h2 style="{self.STYLE["h2"]}">{self._prompt_row(inner)}</h2>'

    def h3(self, inner):
        h3 = f'color:{C["ink"]};font-size:16px;font-weight:bold;line-height:1.6;margin:26px 0 10px 0;'
        return f'<h3 style="{h3}">{self._prompt_row(inner, "&gt;")}</h3>'

    def quote_label(self, kind):
        return (log_tag("INFO", self.QUOTE_LABELS[kind], C["green"]) if kind == "tip"
                else log_tag("WARN", self.QUOTE_LABELS[kind], C["amber"]))

    def lead_label(self):
        return (f'<p style="{MONO}font-size:12px;line-height:1.6;color:{C["text_light"]};margin:0 0 6px 0;">'
                f'# {self.LEAD_LABEL}</p>')

    def hr(self):
        return f'<section style="border-top:1px dashed {C["line"]};height:0;margin:32px 0;"></section>'

    def figcap(self, cap, n):
        return (f'<p style="font-size:12px;line-height:1.6;color:{C["text_light"]};margin:-14px 0 22px 0;">'
                f'<span style="{MONO}color:{C["green"]};margin-right:6px;">↑</span>{cap}</p>')

    def ul_mark(self, depth):
        return f'<span style="{self.STYLE["ul_mark"]}">-</span>', 16

    def ol_mark(self, n, depth):
        return f'<span style="{self.STYLE["ol_mark"]}">[{n}]</span>', 28

    def stats(self, items):
        # 像一段命令输出：深色块里每行「数值  说明」
        rows = []
        for value, label in items:
            rows.append(f'<p style="display:flex;align-items:baseline;margin:0 0 4px 0;line-height:1.4;">'
                        f'<span style="flex:none;min-width:96px;{MONO}font-size:20px;font-weight:bold;color:#7EE787;margin-right:12px;">{esc(value)}</span>'
                        f'<span style="font-size:13px;color:#9DA7B3;">{esc(label)}</span></p>')
        head = f'<p style="{MONO}font-size:11px;color:#6E7681;margin:0 0 8px 0;line-height:1.4;">$ stats</p>'
        return (f'<section style="background:{C["term_bg"]};border-radius:8px;padding:12px 14px 8px 14px;margin:20px 0 22px 0;">'
                f'{head}{"".join(rows)}</section>')

    def extra_decorate(self, html):
        # 代码块外面套一个终端窗口：深色标题栏 + 三个圆点
        dots = "".join(f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{c};margin-right:6px;"></span>'
                       for c in ("#FF5F57", "#FEBC2E", "#28C840"))
        bar = (f'<section style="background:{C["term_bar"]};border-radius:8px 8px 0 0;padding:8px 12px;line-height:0;">'
               f'{dots}</section>')
        return PRE_RE.sub(lambda m: f'<section style="margin:20px 0 22px 0;">{bar}<pre>{m.group(1)}</pre></section>', html)


THEME = TermTheme()


def build_html(md_body: str):
    """Markdown 正文 → (终端排版 HTML, 图片 src 列表)。"""
    return _engine.build(THEME, md_body)
