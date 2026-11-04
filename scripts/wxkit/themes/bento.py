"""便当盒网格 · Bento Grid。

把信息切成大小不一的格子，整整齐齐装进一个便当盒：浅灰盒子 + 白格子 + 少量深色/蓝色重点格，
统一 8px 间距、18px 圆角。便当盒是摘要工具，不是正文容器：开头自动生成“本期速览”盒，
正文照常排版，数据列表变成数据格。适合周报、发布会总结、参数汇总。

Markdown 写法 → 便当盒组件：
  （自动）               本期速览盒：放在导语之后、第一个 ## 之前。深色标题格 + 每个编号章节一格，
                         章节数为奇数时前三节用“左大右二”，其余两两并排；第一节是蓝色重点格。
                         可编号的 ## 不足 2 个时不生成
  ## 标题                一级小标题：浅灰圆角格，左侧蓝色大号序号 01、02……
  ### 标题               二级小标题：蓝色小圆角方块
  第一个 ## 前的 1～3 段   导语格：薄荷底 +「写在前面」
  **加粗**               重点词：主色蓝加粗
  *斜体*                 重点句：浅蓝标签底
  > 引用                 浅灰圆角格
  > 💡 … / > ⚠️ …        小贴士格（浅蓝）/ 注意格（奶黄 + 警示色小标题）
  - **30h** 耳机续航     数据列表（1～3 项「**数值** 说明」）→ 一行数据格装进便当盒，第一格为蓝色重点格
  - 列表 / 1. 列表       蓝色小方块 / 浅灰圆角序号
  ---                    分割线：三个小格子
  ![说明](图.png)        18px 圆角图片格，说明居中灰字
  ```代码```             深色圆角代码格

指南里的“左二右大”“宽窄 2:1”、图片格与参数格混排、结尾的一句话总结盒
无法由 Markdown 表达，需要时把指南第六部分的模板做成图片插入。
"""

import html as html_mod
import re

from .. import render
from . import _engine
from ._engine import Theme, esc, fit_font

NAME = "便当盒网格 · Bento Grid"

C = {  # 默认简洁版，规范见《便当盒网格BentoGrid-公众号排版指南.md》
    "box": "#F2F2F5",          # 盒子底色
    "cell": "#FFFFFF",         # 普通格子
    "text": "#1D1D1F",         # 主文字：标题、数字、正文
    "text_light": "#6E6E73",   # 次要文字：格子说明、标签
    "dark": "#111111",         # 深色重点格
    "dark_sub": "#A1A1A6",     # 深色格上的副文字
    "blue": "#3B5BDB",         # 主色蓝格、重点
    "blue_bg": "#E8EEFF",      # 浅蓝标签底
    "yellow_bg": "#FFF4D6",    # 奶黄格：价格、提醒
    "yellow_text": "#8A6A10",
    "mint_bg": "#DDF5EA",      # 薄荷格：总结、结论
    "mint_text": "#1E7A55",
    "warn": "#D9480F",         # 警示色
}

GAP = 8                        # 格子间距：全盒统一，横向 margin-right、纵向 margin-bottom（不用 gap）
RADIUS = 18                    # 格子圆角：全盒统一
BOX = f'background:{C["box"]};padding:14px;border-radius:16px;'
NUM_FONT = "font-family:Helvetica,Arial,sans-serif;"
H2_NUM_RE = re.compile(r'<h2 data-num="(\d+)">(.*?)</h2>', re.S)

# 卡片：底边内距比顶边小 8px，正好抵掉最后一段的 margin-bottom；上方留 18px，紧跟列表时也不挤
CARD = f'border-radius:{RADIUS}px;padding:14px 16px 6px 16px;margin:18px 0 24px 0;'
P_CARD = f'color:{C["text"]};font-size:14px;line-height:1.75;letter-spacing:.5px;margin:0 0 8px 0;text-align:justify;'
EYEBROW = 'font-size:11px;font-weight:bold;letter-spacing:1px;line-height:1.6;margin:0 0 4px 0;'


def cell(content: str, bg: str, extra: str = "", pad: str = "12px 14px") -> str:
    return f'<section style="min-width:0;background:{bg};border-radius:{RADIUS}px;padding:{pad};{extra}">{content}</section>'


def row(cells) -> str:
    """一行格子：每格 flex:1 等分，最后一格不加右边距（否则右边多出一截，不对齐）。"""
    out = []
    for i, c in enumerate(cells):
        gap = f"margin-right:{GAP}px;" if i < len(cells) - 1 else ""
        out.append(c.replace('<section style="min-width:0;', f'<section style="flex:1;min-width:0;{gap}', 1))
    return f'<section style="display:flex;margin-bottom:{GAP}px;">{"".join(out)}</section>'


def box(rows, margin: str) -> str:
    rows = list(rows)
    # 最后一行不要下边距，盒子四周内距才一致
    rows[-1] = rows[-1].replace(f'margin-bottom:{GAP}px;', "", 1)
    return f'<section style="{BOX}margin:{margin};">{"".join(rows)}</section>'


class BentoTheme(Theme):
    UL_MARK_W = 16

    STYLE = {
        "p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.5px;margin:0 0 16px 0;text-align:justify;',
        "h1": f'color:{C["text"]};font-size:20px;font-weight:bold;line-height:1.4;margin:30px 0 14px 0;',
        # 一级小标题本身就是一个浅灰格子
        "h2": (f'display:flex;align-items:center;background:{C["box"]};border-radius:{RADIUS}px;padding:12px 14px;'
               f'color:{C["text"]};font-size:17px;font-weight:bold;line-height:1.5;margin:32px 0 16px 0;'),
        "h4": f'color:{C["text"]};font-size:15px;font-weight:bold;line-height:1.6;margin:18px 0 8px 0;',
        "blockquote": CARD + f'background:{C["box"]};',
        "quote_tip": CARD + f'background:{C["blue_bg"]};',
        "quote_warn": CARD + f'background:{C["yellow_bg"]};',
        "p_in_quote": P_CARD,
        "lead": CARD.replace("margin:18px 0 24px 0", "margin:0 0 16px 0") + f'background:{C["mint_bg"]};',
        "pre": f'margin:18px 0 22px 0;padding:14px 16px;background:{C["dark"]};border-radius:{RADIUS}px;overflow-x:auto;font-size:13px;line-height:1.7;',
        "pre_code": 'font-family:Consolas,Monaco,monospace;color:#F5F5F7;',
        "code": f'font-family:Consolas,Monaco,monospace;background:{C["box"]};color:{C["text"]};padding:1px 6px;border-radius:6px;font-size:14px;',
        "table": f'width:100%;border-collapse:collapse;font-size:14px;color:{C["text"]};margin:18px 0 22px 0;',
        "th": f'padding:8px 10px;background:{C["box"]};color:{C["text"]};font-weight:bold;text-align:left;',
        "td": f'padding:8px 10px;border-bottom:1px solid {C["box"]};',
        "a": f'color:{C["blue"]};text-decoration:none;border-bottom:1px solid {C["blue_bg"]};word-break:break-all;',
        "strong": f'color:{C["blue"]};font-weight:bold;',
        "strong_in_heading": 'font-weight:bold;',
        "em": f'font-style:normal;background:{C["blue_bg"]};color:{C["blue"]};padding:0 4px;border-radius:4px;',
        "del": f'text-decoration:line-through;color:{C["text_light"]};',
        "img": f'max-width:100%;display:block;margin:10px auto;border-radius:{RADIUS}px;',
        "fig": 'margin:4px 0 22px 0;',
        "fig_img": f'display:block;max-width:100%;margin:0 auto;border-radius:{RADIUS}px;',
        "figcap": f'text-align:center;color:{C["text_light"]};font-size:12px;line-height:1.6;margin:-12px 0 22px 0;',
        "checkbox": 'margin-right:6px;vertical-align:middle;',
        "li_p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.5px;text-align:left;word-wrap:break-word;margin:0 0 8px 0;',
        "ul_mark": f'display:inline-block;width:6px;height:6px;border-radius:2px;background:{C["blue"]};margin-right:10px;vertical-align:3px;',
        "ol_mark": (f'display:inline-block;min-width:18px;height:18px;line-height:18px;border-radius:6px;background:{C["box"]};'
                    f'color:{C["blue"]};font-size:12px;font-weight:bold;text-align:center;text-indent:0;margin-right:8px;'
                    f'vertical-align:1px;{NUM_FONT}'),
    }

    def h2(self, inner, num, idx):
        no = f'flex:none;font-size:24px;line-height:1;letter-spacing:-0.5px;color:{C["blue"]};margin-right:12px;{NUM_FONT}'
        return (f'<h2 style="{self.STYLE["h2"]}"><span style="{no}">{num}</span>'
                f'<span style="flex:1;min-width:0;">{inner}</span></h2>')

    def h2_plain(self, inner):
        return f'<h2 style="{self.STYLE["h2"]}"><span style="flex:1;min-width:0;">{inner}</span></h2>'

    def h3(self, inner):
        # 方块 margin-top = (15px × 1.6 行高 − 8px) / 2，对齐首行中线
        h3 = f'display:flex;align-items:flex-start;color:{C["text"]};font-size:15px;font-weight:bold;line-height:1.6;margin:22px 0 8px 0;'
        dot = f'flex:none;width:8px;height:8px;border-radius:2px;background:{C["blue"]};margin:8px 10px 0 0;'
        return f'<h3 style="{h3}"><span style="{dot}"></span><span>{inner}</span></h3>'

    def quote_label(self, kind):
        color = C["blue"] if kind == "tip" else C["warn"]
        return f'<p style="{EYEBROW}color:{color};">{self.QUOTE_LABELS[kind]}</p>'

    def lead_label(self):
        return f'<p style="{EYEBROW}color:{C["mint_text"]};">{self.LEAD_LABEL}</p>'

    def hr(self):
        # 三个小格子：一宽两窄，像缩小的一行便当
        part = 'display:inline-block;height:8px;border-radius:4px;margin:0 3px;'
        cells = (f'<span style="{part}width:24px;background:{C["dark"]};"></span>'
                 f'<span style="{part}width:8px;background:{C["blue"]};"></span>'
                 f'<span style="{part}width:8px;background:#D1D1D6;"></span>')
        return f'<section style="text-align:center;line-height:1;margin:30px 0;">{cells}</section>'

    def ul_mark(self, depth):
        return f'<span style="{self.STYLE["ul_mark"]}"></span>', 16

    def ol_mark(self, n, depth):
        return f'<span style="{self.STYLE["ol_mark"]}">{n}</span>', 26

    # ---- 便当盒 ----

    def stats(self, items):
        # 一行数据格：第一格蓝色重点格，其余白格；三列时数字小一号
        top, avail = {1: (32, 280), 2: (24, 120), 3: (20, 80)}[len(items)]
        fs = fit_font([v for v, _ in items], top, avail, 14)
        cells = []
        for i, (value, label) in enumerate(items):
            blue = i == 0
            fg = "#FFFFFF" if blue else C["text"]
            sub = "color:#FFFFFF;opacity:0.85;" if blue else f'color:{C["text_light"]};'
            cap = f'<p style="font-size:12px;line-height:1.5;{sub}margin:2px 0 0 0;">{esc(label)}</p>' if label else ""
            num = (f'<p style="font-size:{fs}px;font-weight:bold;line-height:1.2;color:{fg};margin:0;white-space:nowrap;'
                   f'{NUM_FONT}">{esc(value)}</p>')
            cells.append(cell(num + cap, C["blue"] if blue else C["cell"], pad="12px 14px" if len(items) < 3 else "12px"))
        return box([row(cells)], "18px 0 24px 0")

    def toc(self, heads):
        """本期速览：深色标题格 + 每节一格。heads = [(编号, 标题纯文本)]，标题已转义。"""
        def section_cell(num, title, blue, big=False):
            fg = "#FFFFFF" if blue else C["text"]
            no = (f'<p style="font-size:{28 if big else 22}px;font-weight:bold;line-height:1.1;color:{fg};margin:0;'
                  f'{NUM_FONT}">{num}</p>')
            t = (f'<p style="font-size:{15 if big else 13}px;font-weight:bold;line-height:1.5;color:{fg};'
                 f'margin:6px 0 0 0;">{title}</p>')
            return no, t

        title = cell(
            f'<p style="font-size:11px;line-height:1.6;letter-spacing:1px;color:{C["dark_sub"]};margin:0 0 4px 0;{NUM_FONT}">'
            f'IN THIS ISSUE · {len(heads):02d}</p>'
            f'<p style="font-size:20px;font-weight:bold;line-height:1.4;color:#FFFFFF;margin:0;">本期速览</p>',
            C["dark"], pad="16px")
        rows = [title.replace('<section style="min-width:0;', f'<section style="min-width:0;margin-bottom:{GAP}px;', 1)]
        rest = list(heads)
        if len(rest) % 2 == 1:
            # 左大右二：左边一个高格子（第一节，蓝色重点格，编号贴顶、标题贴底），右边上下两个小格
            (n1, t1), (n2, t2), (n3, t3) = rest[:3]
            rest = rest[3:]
            no, t = section_cell(n1, t1, True, big=True)
            left = (f'<section style="flex:1.15;min-width:0;margin-right:{GAP}px;background:{C["blue"]};'
                    f'border-radius:{RADIUS}px;padding:14px;display:flex;flex-direction:column;'
                    f'justify-content:space-between;min-height:150px;">{no}{t}</section>')
            small = []
            for k, (n, tt) in enumerate(((n2, t2), (n3, t3))):
                no, t = section_cell(n, tt, False)
                gap = f"margin-bottom:{GAP}px;" if k == 0 else ""
                small.append(f'<section style="flex:1;{gap}background:{C["cell"]};border-radius:{RADIUS}px;'
                             f'padding:12px 14px;">{no}{t}</section>')
            rows.append(f'<section style="display:flex;margin-bottom:{GAP}px;">{left}'
                        f'<section style="flex:1;min-width:0;display:flex;flex-direction:column;">{"".join(small)}</section>'
                        f'</section>')
            first_blue = False
        else:
            first_blue = True
        for i in range(0, len(rest), 2):
            pair = []
            for k, (n, tt) in enumerate(rest[i:i + 2]):
                blue = first_blue and i == 0 and k == 0
                no, t = section_cell(n, tt, blue)
                pair.append(cell(no + t, C["blue"] if blue else C["cell"]))
            rows.append(row(pair))
        return box(rows, "0 0 28px 0")

    def extra_decorate(self, html):
        heads = H2_NUM_RE.findall(html)
        if len(heads) < 2:
            return html
        items = [(num, esc(html_mod.unescape(render.plain(inner)))) for num, inner in heads]
        pos = html.find("<h2")
        return html[:pos] + self.toc(items) + html[pos:]


THEME = BentoTheme()


def build_html(md_body: str):
    """Markdown 正文 → (便当盒网格排版 HTML, 图片 src 列表)。"""
    return _engine.build(THEME, md_body)
