"""蓝图 · 工程图纸。

白底浅蓝网格 + 内外两道图框，细蓝线、等宽英文标注（SEC / FIG / NOTE），小标题像图纸的标题栏，
分割线是带箭头的尺寸线。适合硬件拆解、原理图解、架构或流程讲解。

网格背景靠 linear-gradient + background-size，被微信过滤时退化成纯白底，图框和其他线条元素不受影响。

Markdown 写法 → 图纸组件：
  （整篇）               浅蓝网格底 + 内外两道蓝色图框
  ## 标题                标题栏：左侧蓝底「SEC / 01」格 + 右侧标题，外框蓝线
                         （“附”开头的、或可编号的不足 2 个时：只有外框和标题）
  ### 标题               蓝色空心方块 + 标题
  第一个 ## 前的 1～3 段   导语：白底蓝色虚线框 +「NOTE」标签和「写在前面」
  **加粗**               主色蓝加粗
  *斜体*                 蓝色虚线下划线
  > 引用                 蓝色虚线竖条
  > 💡 … / > ⚠️ …        小贴士（浅蓝底蓝框）/ 注意（浅橙底橙框）
  - **12mm** 厚度        数据列表（1～3 项「**数值** 说明」）→ 参数格：蓝框 + 等宽数字
  - 列表 / 1. 列表       蓝色「+」/ 蓝色空心方框数字
  ---                    尺寸线：两端短竖线 + 箭头 + 细线
  ![说明](图.png)        图片加蓝色细框，下方「FIG.01 — 说明」
  表格                   蓝色网格线，表头浅蓝底
"""

from . import _engine
from ._engine import Theme, esc, fit_font

NAME = "蓝图 · 工程图纸"

C = {
    "blue": "#1F4FBF",         # 主色：线条、标注、重点
    "blue_soft": "#BFD0F2",    # 表格内线
    "grid": "#EAF0FB",         # 网格线
    "blue_bg": "#F0F5FD",
    "ink": "#172033",          # 标题
    "text": "#2A3244",         # 正文
    "text_light": "#6B7487",
    "orange": "#E8590C",       # 警示、标注
    "orange_bg": "#FFF3EA",
}

MONO = "font-family:Menlo,Consolas,Monaco,Courier New,monospace;"
CARD = 'padding:12px 14px 4px 14px;margin:20px 0 22px 0;'
P_CARD = f'color:{C["text"]};font-size:14px;line-height:1.8;letter-spacing:.3px;margin:0 0 8px 0;text-align:justify;'


def mono_tag(text: str, color: str, fill: bool = False) -> str:
    bg = f"background:{color};color:#FFFFFF;" if fill else f"color:{color};"
    return (f'<span style="display:inline-block;{MONO}font-size:10px;font-weight:bold;letter-spacing:1px;line-height:1.5;'
            f'padding:0 5px;border:1px solid {color};margin-right:8px;vertical-align:1px;{bg}">{text}</span>')


class BlueprintTheme(Theme):
    CONTAINER = (f'background-color:#FFFFFF;'
                 f'background-image:linear-gradient({C["grid"]} 1px,transparent 1px),linear-gradient(90deg,{C["grid"]} 1px,transparent 1px);'
                 f'background-size:16px 16px;border:1px solid {C["blue"]};'
                 f'box-shadow:inset 0 0 0 4px #FFFFFF,inset 0 0 0 5px {C["blue"]};'
                 f'padding:22px 16px 26px 16px;color:{C["text"]};')
    UL_MARK_W = 16

    STYLE = {
        "p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.3px;margin:0 0 16px 0;text-align:justify;',
        "h1": f'color:{C["ink"]};font-size:20px;font-weight:bold;line-height:1.5;margin:30px 0 14px 0;',
        "h2": (f'display:flex;align-items:stretch;border:1.5px solid {C["blue"]};background:#FFFFFF;'
               f'color:{C["ink"]};font-size:17px;font-weight:bold;line-height:1.5;margin:34px 0 16px 0;'),
        "h4": f'color:{C["ink"]};font-size:15px;font-weight:bold;line-height:1.6;margin:20px 0 8px 0;',
        "blockquote": 'padding:2px 0 2px 14px;margin:20px 0 22px 0;' + f'border-left:2px dashed {C["blue"]};',
        "quote_tip": CARD + f'background:{C["blue_bg"]};border:1px solid {C["blue"]};',
        "quote_warn": CARD + f'background:{C["orange_bg"]};border:1px solid {C["orange"]};',
        "p_in_quote": P_CARD.replace(f'color:{C["text"]}', f'color:{C["text_light"]}'),
        "p_in_tip": P_CARD,
        "p_in_warn": P_CARD,
        "lead": CARD.replace("margin:20px 0 22px 0", "margin:0 0 26px 0") + f'background:#FFFFFF;border:1px dashed {C["blue"]};',
        "p_in_lead": P_CARD,
        "pre": f'margin:20px 0 22px 0;padding:14px 16px;background:#0B1E46;border:1px solid {C["blue"]};overflow-x:auto;font-size:13px;line-height:1.7;',
        "pre_code": f'{MONO}color:#DCE6FA;',
        "code": f'{MONO}background:{C["blue_bg"]};color:{C["blue"]};padding:1px 5px;font-size:13px;',
        "table": f'width:100%;border-collapse:collapse;font-size:13px;color:{C["text"]};margin:20px 0 22px 0;border:1.5px solid {C["blue"]};background:#FFFFFF;',
        "th": f'padding:7px 8px;background:{C["blue_bg"]};color:{C["blue"]};font-weight:bold;text-align:left;border:1px solid {C["blue"]};',
        "td": f'padding:7px 8px;border:1px solid {C["blue_soft"]};',
        "a": f'color:{C["blue"]};text-decoration:none;border-bottom:1px solid {C["blue"]};word-break:break-all;',
        "strong": f'color:{C["blue"]};font-weight:bold;',
        "strong_in_heading": 'font-weight:bold;',
        "em": f'font-style:normal;font-weight:bold;color:{C["ink"]};border-bottom:1.5px dashed {C["blue"]};',
        "del": f'text-decoration:line-through;color:{C["text_light"]};',
        "img": 'max-width:100%;display:block;margin:10px auto;',
        "fig": f'margin:6px 0 22px 0;padding:6px;border:1px solid {C["blue"]};background:#FFFFFF;',
        "fig_img": 'display:block;max-width:100%;margin:0 auto;',
        "checkbox": 'margin-right:6px;vertical-align:middle;',
        "li_p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.3px;text-align:left;word-wrap:break-word;margin:0 0 8px 0;',
        "ul_mark": f'display:inline-block;width:16px;{MONO}font-weight:bold;color:{C["blue"]};text-indent:0;',
        "ol_mark": (f'display:inline-block;min-width:18px;height:18px;line-height:18px;border:1px solid {C["blue"]};'
                    f'color:{C["blue"]};{MONO}font-size:11px;font-weight:bold;text-align:center;text-indent:0;'
                    f'margin-right:8px;vertical-align:1px;'),
    }

    def h2(self, inner, num, idx):
        cell = (f'flex:none;display:inline-block;background:{C["blue"]};color:#FFFFFF;text-align:center;'
                f'padding:5px 10px;{MONO}')
        return (f'<h2 style="{self.STYLE["h2"]}"><span style="{cell}">'
                f'<span style="display:block;font-size:9px;letter-spacing:2px;line-height:1.3;font-weight:normal;">SEC</span>'
                f'<span style="display:block;font-size:18px;line-height:1.2;">{num}</span></span>'
                f'<span style="flex:1;min-width:0;align-self:center;padding:7px 12px;">{inner}</span></h2>')

    def h2_plain(self, inner):
        return (f'<h2 style="{self.STYLE["h2"]}">'
                f'<span style="flex:1;min-width:0;padding:7px 12px;">{inner}</span></h2>')

    def h3(self, inner):
        # 方块 margin-top = (16px × 1.6 行高 − 10px) / 2，对齐首行中线
        h3 = f'display:flex;align-items:flex-start;color:{C["ink"]};font-size:16px;font-weight:bold;line-height:1.6;margin:26px 0 10px 0;'
        box = f'flex:none;width:8px;height:8px;border:1.5px solid {C["blue"]};margin:7px 10px 0 0;'
        return f'<h3 style="{h3}"><span style="{box}"></span><span>{inner}</span></h3>'

    def quote_label(self, kind):
        color = C["blue"] if kind == "tip" else C["orange"]
        code = "TIP" if kind == "tip" else "WARN"
        return (f'<p style="margin:0 0 6px 0;font-size:12px;font-weight:bold;line-height:1.6;color:{color};">'
                f'{mono_tag(code, color, fill=True)}{self.QUOTE_LABELS[kind]}</p>')

    def lead_label(self):
        return (f'<p style="margin:0 0 6px 0;font-size:12px;font-weight:bold;line-height:1.6;color:{C["blue"]};">'
                f'{mono_tag("NOTE", C["blue"])}{self.LEAD_LABEL}</p>')

    def hr(self):
        # 尺寸线 |◀────────▶|
        tick = f'flex:none;width:0;height:12px;border-left:1px solid {C["blue"]};'
        left = f'flex:none;width:0;height:0;border-top:4px solid transparent;border-bottom:4px solid transparent;border-right:7px solid {C["blue"]};'
        right = left.replace("border-right:", "border-left:")
        line = f'flex:1;height:0;border-top:1px solid {C["blue"]};'
        spans = "".join('<span style="' + p + '"></span>' for p in (tick, left, line, right, tick))
        return f'<section style="display:flex;align-items:center;margin:30px 8px;">{spans}</section>'

    def figcap(self, cap, n):
        return (f'<p style="font-size:12px;line-height:1.6;color:{C["text_light"]};margin:-16px 0 22px 0;">'
                f'<span style="{MONO}font-size:11px;font-weight:bold;color:{C["blue"]};margin-right:8px;">FIG.{n:02d} —</span>{cap}</p>')

    def ul_mark(self, depth):
        return f'<span style="{self.STYLE["ul_mark"]}">+</span>', 16

    def ol_mark(self, n, depth):
        return f'<span style="{self.STYLE["ol_mark"]}">{n}</span>', 28

    def stats(self, items):
        # 参数格：并排的蓝框格子，等宽大数字 + 说明
        top = {1: 34, 2: 26, 3: 22}[len(items)]
        avail = {1: 270, 2: 120, 3: 78}[len(items)]
        fs = fit_font([v for v, _ in items], top, avail, 13)
        cells = []
        for i, (value, label) in enumerate(items):
            sep = f'border-left:1px solid {C["blue"]};' if i else ""
            cap = f'<p style="font-size:11px;line-height:1.5;color:{C["text_light"]};margin:4px 0 0 0;">{esc(label)}</p>' if label else ""
            cells.append(f'<section style="flex:1;min-width:0;padding:10px 8px;{sep}">'
                         f'<p style="{MONO}font-size:{fs}px;font-weight:bold;line-height:1.15;color:{C["blue"]};margin:0;white-space:nowrap;">'
                         f'{esc(value)}</p>{cap}</section>')
        return (f'<section style="display:flex;border:1.5px solid {C["blue"]};background:#FFFFFF;margin:20px 0 22px 0;">'
                f'{"".join(cells)}</section>')


THEME = BlueprintTheme()


def build_html(md_body: str):
    """Markdown 正文 → (工程图纸排版 HTML, 图片 src 列表)。"""
    return _engine.build(THEME, md_body)
