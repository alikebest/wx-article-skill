"""像素 · 8-bit。

阶梯缺角的像素边框（四道不模糊的 box-shadow，四个角留空）、用 box-shadow 逐点画的像素爱心和箭头、
饱和的红黄蓝三色，像一款复古小游戏。分割线是一条血条。适合游戏内容、轻松的科技八卦。

中文没有像素字体，像素感全靠边框和小图标撑起来；英文数字用 Courier New 粗体。
带像素边框的元素左右各留 4px，边框画在盒子外面，不留就会贴住甚至超出正文边缘。

Markdown 写法 → 像素组件：
  ## 标题                黄色像素标签「STAGE 01」+ 标题 + 粗虚线底边
                         （“附”开头的、或可编号的不足 2 个时：像素箭头 + 标题 + 粗虚线底边）
  ### 标题               蓝色像素箭头 + 标题
  第一个 ## 前的 1～3 段   导语：像素对话框 + 红色像素标签「写在前面」
  **加粗**               红色加粗
  *斜体*                 黄色底
  > 引用                 浅灰像素框
  > 💡 … / > ⚠️ …        小贴士（浅黄像素框 + 黄标签）/ 注意（浅红像素框 + 红标签）
  - **999** 金币         数据列表（1～3 项「**数值** 说明」）→ 像素计分格
  - 列表 / 1. 列表       像素爱心 / 蓝色像素方块数字
  ---                    血条「HP ▮▮▮▮▮▮▯▯」
  ![说明](图.png)        像素相框，说明居中
  表格                   2px 粗黑格线，表头蓝底白字
"""

from . import _engine
from ._engine import Theme, esc, fit_font

NAME = "像素 · 8-bit"

C = {
    "ink": "#1B1B1F",          # 像素边框、标题
    "text": "#2A2A30",         # 正文
    "text_light": "#6B6B75",
    "red": "#E4433B",
    "yellow": "#FFCE3A",
    "blue": "#3D6DEB",
    "green": "#7CF29A",        # 代码块字色
    "gray_bg": "#F2F2F2",
    "yellow_bg": "#FFF6D6",
    "red_bg": "#FFE9E7",
    "empty": "#DADADA",        # 血条空格
}

MONO = "font-family:Courier New,Menlo,Consolas,monospace;"
PX = 2  # 一个像素点的边长

HEART = (".X.X.",
         "XWXXX",
         "XXXXX",
         ".XXX.",
         "..X..")
ARROW = ("X...",
         "XX..",
         "XXX.",
         "XX..",
         "X...")


def pixel_border(color: str, w: int) -> str:
    """像素边框：上下左右各一道实心阴影，四个角空出来，就是阶梯缺角。"""
    return f'box-shadow:0 -{w}px 0 0 {color},0 {w}px 0 0 {color},-{w}px 0 0 0 {color},{w}px 0 0 0 {color};'


def pixel_art(rows, colors) -> str:
    """用 box-shadow 逐点画小图标：元素本身是左上角那一个点，其余每个点一道阴影。
    阴影不占位置，调用方要用 margin 给图标留出 len(row)×PX 宽、len(rows)×PX 高的空间。"""
    shadows = [f"{x * PX}px {y * PX}px 0 0 {colors[ch]}"
               for y, row in enumerate(rows) for x, ch in enumerate(row)
               if ch != "." and (x, y) != (0, 0)]
    first = rows[0][0]
    bg = f"background:{colors[first]};" if first != "." else ""
    return f'display:inline-block;width:{PX}px;height:{PX}px;{bg}box-shadow:{",".join(shadows)};'


def pixel_tag(text: str, bg: str, color: str) -> str:
    return (f'<span style="display:inline-block;background:{bg};color:{color};font-size:12px;font-weight:bold;'
            f'line-height:1;padding:4px 8px;margin:2px 0 0 2px;{pixel_border(C["ink"], 2)}">{text}</span>')


CARD = 'padding:12px 14px 4px 14px;margin:24px 4px 24px 4px;'
P_CARD = f'color:{C["text"]};font-size:14px;line-height:1.8;letter-spacing:.3px;margin:0 0 8px 0;text-align:justify;'
HEART_COLORS = {"X": C["red"], "W": "#FFFFFF"}


class PixelTheme(Theme):
    UL_MARK_W = 18

    STYLE = {
        "p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.3px;margin:0 0 16px 0;text-align:justify;',
        "h1": f'color:{C["ink"]};font-size:20px;font-weight:bold;line-height:1.5;margin:32px 0 14px 0;',
        "h2": (f'display:flex;align-items:center;color:{C["ink"]};font-size:18px;font-weight:bold;line-height:1.5;'
               f'margin:38px 0 18px 0;padding-bottom:10px;border-bottom:3px dashed {C["ink"]};'),
        "h4": f'color:{C["ink"]};font-size:15px;font-weight:bold;line-height:1.6;margin:20px 0 8px 0;',
        "blockquote": CARD + f'background:{C["gray_bg"]};{pixel_border("#BDBDC2", 4)}',
        "quote_tip": CARD + f'background:{C["yellow_bg"]};{pixel_border(C["ink"], 4)}',
        "quote_warn": CARD + f'background:{C["red_bg"]};{pixel_border(C["ink"], 4)}',
        "p_in_quote": P_CARD,
        "lead": CARD.replace("margin:24px 4px 24px 4px", "margin:4px 4px 30px 4px") + f'background:#FFFFFF;{pixel_border(C["ink"], 4)}',
        "p_in_lead": P_CARD,
        "pre": f'margin:24px 4px 26px 4px;padding:14px 16px;background:{C["ink"]};overflow-x:auto;font-size:13px;line-height:1.7;{pixel_border(C["ink"], 4)}',
        "pre_code": f'{MONO}color:{C["green"]};',
        "code": f'{MONO}background:{C["gray_bg"]};color:{C["ink"]};padding:1px 5px;font-size:14px;font-weight:bold;',
        "table": f'width:100%;border-collapse:collapse;font-size:13px;color:{C["text"]};margin:20px 0 22px 0;border:2px solid {C["ink"]};',
        "th": f'padding:7px 8px;background:{C["blue"]};color:#FFFFFF;font-weight:bold;text-align:left;border:2px solid {C["ink"]};',
        "td": f'padding:7px 8px;border:2px solid {C["ink"]};',
        "a": f'color:{C["blue"]};text-decoration:none;border-bottom:2px solid {C["blue"]};word-break:break-all;',
        "strong": f'color:{C["red"]};font-weight:bold;',
        "strong_in_heading": 'font-weight:bold;',
        "em": f'font-style:normal;font-weight:bold;background:{C["yellow"]};color:{C["ink"]};padding:0 3px;',
        "del": f'text-decoration:line-through;color:{C["text_light"]};',
        "img": 'max-width:100%;display:block;margin:10px auto;',
        "fig": f'margin:10px 4px 24px 4px;line-height:0;{pixel_border(C["ink"], 4)}',
        "fig_img": 'display:block;max-width:100%;margin:0 auto;',
        "checkbox": 'margin-right:6px;vertical-align:middle;',
        "li_p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.3px;text-align:left;word-wrap:break-word;margin:0 0 8px 0;',
        # 爱心 10×10：元素是 2px 的左上角点，margin-right 补足图标剩下的 8px 宽 + 8px 间距；
        # vertical-align 让图标中线落在汉字中线（基线上方约 6px）
        "ul_mark": pixel_art(HEART, HEART_COLORS) + f'margin-right:{len(HEART[0]) * PX - PX + 8}px;vertical-align:9px;',
        "ol_mark": (f'display:inline-block;min-width:16px;height:16px;line-height:16px;background:{C["blue"]};color:#FFFFFF;'
                    f'{MONO}font-size:12px;font-weight:bold;text-align:center;text-indent:0;margin:0 10px 0 2px;'
                    f'vertical-align:2px;{pixel_border(C["ink"], 2)}'),
    }

    def _arrow(self, color, top):
        # 箭头 8×10，作为 flex 子项：margin-top 让它对齐首行中线，margin-right 补足图标宽度
        return (f'<span style="flex:none;{pixel_art(ARROW, {"X": color})}'
                f'margin:{top}px {len(ARROW[0]) * PX - PX + 10}px 0 0;"></span>')

    def h2(self, inner, num, idx):
        tag = (f'flex:none;display:inline-block;background:{C["yellow"]};color:{C["ink"]};{MONO}font-size:13px;'
               f'font-weight:bold;line-height:1;padding:6px 8px;margin:3px 14px 3px 3px;{pixel_border(C["ink"], 3)}')
        return (f'<h2 style="{self.STYLE["h2"]}"><span style="{tag}">STAGE {num}</span>'
                f'<span style="flex:1;min-width:0;">{inner}</span></h2>')

    def h2_plain(self, inner):
        h2 = self.STYLE["h2"].replace("align-items:center", "align-items:flex-start")
        return f'<h2 style="{h2}">{self._arrow(C["red"], 9)}<span style="flex:1;min-width:0;">{inner}</span></h2>'

    def h3(self, inner):
        # 16px × 1.6 行高 = 25.6px，箭头高 10px：margin-top 8px 落在首行中线
        h3 = f'display:flex;align-items:flex-start;color:{C["ink"]};font-size:16px;font-weight:bold;line-height:1.6;margin:26px 0 10px 0;'
        return f'<h3 style="{h3}">{self._arrow(C["blue"], 8)}<span>{inner}</span></h3>'

    def quote_label(self, kind):
        tag = (pixel_tag(self.QUOTE_LABELS[kind], C["yellow"], C["ink"]) if kind == "tip"
               else pixel_tag(self.QUOTE_LABELS[kind], C["red"], "#FFFFFF"))
        return f'<p style="margin:0 0 10px 0;line-height:1;">{tag}</p>'

    def lead_label(self):
        return f'<p style="margin:0 0 10px 0;line-height:1;">{pixel_tag(self.LEAD_LABEL, C["red"], "#FFFFFF")}</p>'

    def hr(self):
        # 血条：6 格红 + 2 格空
        segs = "".join(f'<span style="display:inline-block;width:10px;height:8px;margin-right:2px;background:{c};"></span>'
                       for c in [C["red"]] * 6 + [C["empty"]] * 2)
        bar = (f'<span style="display:inline-block;padding:2px 0 2px 2px;background:#FFFFFF;line-height:0;font-size:0;'
               f'{pixel_border(C["ink"], 2)}">{segs}</span>')
        label = f'<span style="{MONO}font-size:13px;font-weight:bold;color:{C["red"]};line-height:1;margin-right:10px;">HP</span>'
        return f'<section style="display:flex;justify-content:center;align-items:center;margin:34px 0;">{label}{bar}</section>'

    def figcap(self, cap, n):
        return (f'<p style="text-align:center;font-size:12px;line-height:1.6;color:{C["text_light"]};margin:-10px 0 24px 0;">'
                f'<span style="{MONO}font-weight:bold;color:{C["ink"]};margin-right:6px;">#{n}</span>{cap}</p>')

    def ul_mark(self, depth):
        return f'<span style="{self.STYLE["ul_mark"]}"></span>', 18

    def ol_mark(self, n, depth):
        return f'<span style="{self.STYLE["ol_mark"]}">{n}</span>', 28

    def stats(self, items):
        # 像素计分格：浅黄底 + 像素边框，红色等宽大数字
        top = {1: 34, 2: 26, 3: 22}[len(items)]
        avail = {1: 270, 2: 120, 3: 76}[len(items)]
        fs = fit_font([v for v, _ in items], top, avail, 13)
        cells = []
        for i, (value, label) in enumerate(items):
            gap = "margin-right:14px;" if i < len(items) - 1 else ""
            cap = f'<p style="font-size:11px;line-height:1.5;color:{C["text_light"]};margin:4px 0 0 0;">{esc(label)}</p>' if label else ""
            cells.append(f'<section style="flex:1;min-width:0;{gap}padding:10px 8px;text-align:center;background:{C["yellow_bg"]};'
                         f'{pixel_border(C["ink"], 3)}">'
                         f'<p style="{MONO}font-size:{fs}px;font-weight:bold;line-height:1.15;color:{C["red"]};margin:0;white-space:nowrap;">'
                         f'{esc(value)}</p>{cap}</section>')
        return f'<section style="display:flex;margin:24px 4px 26px 4px;">{"".join(cells)}</section>'


THEME = PixelTheme()


def build_html(md_body: str):
    """Markdown 正文 → (像素排版 HTML, 图片 src 列表)。"""
    return _engine.build(THEME, md_body)
