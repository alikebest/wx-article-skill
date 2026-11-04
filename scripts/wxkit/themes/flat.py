"""扁平化 · Flat Design。

去掉一切假装立体的东西，只留下纯色、形状和文字：零阴影、零渐变、直角，四色撞色，直接排在白底上。
兼容性最好、深色模式最稳，适合日更的科技资讯。

Markdown 写法 → 扁平组件：
  ## 标题                一级小标题：纯色方块序号 1、2、3……，按章节轮换 蓝 → 珊瑚 → 青绿 → 明黄
                         （“附”开头的、或可编号的不足 2 个时：蓝色竖条）
  ### 标题               二级小标题：纯色小圆点
  第一个 ## 前的 1～3 段   导语块：浅黄底 + 明黄「写在前面」标签
  **加粗**               重点词：主色蓝加粗
  *斜体*                 重点句：纯色反白（蓝底白字）
  > 引用                 浅灰块 + 蓝色竖条
  > 💡 … / > ⚠️ …        小贴士块（浅蓝底 + 蓝标签）/ 注意块（浅珊瑚底 + 珊瑚标签）
  - **12 张** 平均连拍   数据列表（1～3 项「**数值** 说明」）→ 纯色数据磁贴
  - 列表 / 1. 列表       蓝色圆点 / 青绿圆形数字（步骤列表）
  ---                    几何分割线：三色小方块
  ![说明](图.png)        图片下方「蓝色细条 + 灰字说明」
  ```代码```             深蓝灰代码块

指南里的几何头图、栏目标签、大标题（由微信渲染）、金句、对比块、文末关注卡
无法由 Markdown 表达，不自动生成。几何头图建议做成 900×383 的封面图。
"""

from . import _engine
from ._engine import Theme, esc, fit_font

NAME = "扁平化 · Flat Design"

C = {  # 四色撞色，规范见《扁平化FlatDesign-公众号排版指南.md》
    "ink": "#2B2D42",          # 深蓝灰：标题、正文、深色块
    "text_light": "#8D99AE",   # 次要文字：注释、图注
    "blue": "#2D7FF9",         # 主色：约占所有彩色的一半
    "coral": "#FF6B4A",        # 珊瑚红：第二序号、警示
    "yellow": "#FFC233",       # 明黄：亮点数据、标签（上面不放白字）
    "teal": "#2EC4A5",         # 青绿：步骤序号
    "blue_bg": "#EAF2FF",
    "coral_bg": "#FFEDE8",
    "yellow_bg": "#FFF6DB",
    "gray_bg": "#F2F4F7",
}

# 色块上的文字色：明黄用深蓝灰，其余用白
ON = {C["blue"]: "#FFFFFF", C["coral"]: "#FFFFFF", C["teal"]: "#FFFFFF", C["yellow"]: C["ink"], C["ink"]: "#FFFFFF"}
# 一级小标题序号的轮换顺序
ROTATION = (C["blue"], C["coral"], C["teal"], C["yellow"])

# 信息块：纯色浅底、无描边无阴影。底边内距比顶边小 8px，正好抵掉最后一段的 margin-bottom；
# 上方留 20px：扁平风对留白特别敏感，组件之间至少空出 20px
BLOCK = 'padding:12px 14px 4px 14px;margin:20px 0 22px 0;'
P_BLOCK = f'color:{C["ink"]};font-size:14px;line-height:1.8;letter-spacing:.5px;margin:0 0 8px 0;text-align:justify;'
TAG = 'display:inline-block;font-size:12px;font-weight:bold;line-height:1.6;letter-spacing:1px;padding:1px 8px;'


def tag(text: str, bg: str) -> str:
    return f'<p style="margin:0 0 8px 0;line-height:1;"><span style="{TAG}background:{bg};color:{ON[bg]};">{text}</span></p>'


class FlatTheme(Theme):
    UL_MARK_W = 18

    STYLE = {
        "p": f'color:{C["ink"]};font-size:15px;line-height:1.8;letter-spacing:.5px;margin:0 0 16px 0;text-align:justify;',
        "h1": f'color:{C["ink"]};font-size:21px;font-weight:bold;line-height:1.5;margin:30px 0 14px 0;',
        "h2": f'display:flex;align-items:center;color:{C["ink"]};font-size:17px;font-weight:bold;line-height:1.5;margin:32px 0 14px 0;',
        "h4": f'color:{C["ink"]};font-size:15px;font-weight:bold;line-height:1.6;margin:18px 0 8px 0;',
        "blockquote": BLOCK + f'background:{C["gray_bg"]};border-left:4px solid {C["blue"]};',
        "quote_tip": BLOCK + f'background:{C["blue_bg"]};',
        "quote_warn": BLOCK + f'background:{C["coral_bg"]};',
        "p_in_quote": P_BLOCK,
        "lead": BLOCK.replace("margin:20px 0 22px 0", "margin:0 0 26px 0") + f'background:{C["yellow_bg"]};',
        "pre": f'margin:20px 0 22px 0;padding:14px 16px;background:{C["ink"]};overflow-x:auto;font-size:13px;line-height:1.7;',
        "pre_code": 'font-family:Consolas,Monaco,monospace;color:#F2F4F7;',
        "code": f'font-family:Consolas,Monaco,monospace;background:{C["blue_bg"]};color:{C["blue"]};padding:1px 5px;font-size:14px;',
        "table": f'width:100%;border-collapse:collapse;font-size:14px;color:{C["ink"]};margin:20px 0 22px 0;',
        "th": f'padding:8px 10px;background:{C["blue"]};color:#FFFFFF;font-weight:bold;text-align:left;',
        "td": 'padding:8px 10px;border-bottom:1px solid #E1E6ED;',
        "a": f'color:{C["blue"]};text-decoration:none;border-bottom:1px solid {C["blue"]};word-break:break-all;',
        "strong": f'color:{C["blue"]};font-weight:bold;',
        "strong_in_heading": 'font-weight:bold;',
        "em": f'font-style:normal;font-weight:bold;background:{C["blue"]};color:#FFFFFF;padding:0 4px;',
        "del": f'text-decoration:line-through;color:{C["text_light"]};',
        "img": 'max-width:100%;display:block;margin:10px auto;',
        "fig": 'margin:4px 0 22px 0;',
        "fig_img": 'display:block;max-width:100%;margin:0 auto;',
        "checkbox": 'margin-right:6px;vertical-align:middle;',
        "li_p": f'color:{C["ink"]};font-size:15px;line-height:1.8;letter-spacing:.5px;text-align:left;word-wrap:break-word;margin:0 0 8px 0;',
        "ul_mark": f'display:inline-block;width:8px;height:8px;border-radius:50%;background:{C["blue"]};margin-right:10px;vertical-align:2px;',
        "ol_mark": (f'display:inline-block;min-width:20px;height:20px;line-height:20px;border-radius:50%;background:{C["teal"]};'
                    f'color:#FFFFFF;font-size:11px;font-weight:bold;text-align:center;text-indent:0;margin-right:8px;'
                    f'vertical-align:1px;font-family:Arial,sans-serif;'),
    }

    def h2(self, inner, num, idx):
        # 核心识别符号：纯色方块序号，按章节轮换颜色。line-height 居中，flex 失效时也不歪
        bg = ROTATION[(idx - 1) % len(ROTATION)]
        box = (f'flex:none;display:inline-block;width:28px;height:28px;line-height:28px;text-align:center;'
               f'background:{bg};color:{ON[bg]};font-size:15px;font-weight:bold;margin-right:10px;font-family:Arial,sans-serif;')
        return (f'<h2 style="{self.STYLE["h2"]}"><span style="{box}">{int(num)}</span>'
                f'<span style="flex:1;min-width:0;">{inner}</span></h2>')

    def h2_plain(self, inner):
        bar = f'flex:none;display:inline-block;width:6px;height:20px;background:{C["blue"]};margin-right:10px;'
        return (f'<h2 style="{self.STYLE["h2"]}"><span style="{bar}"></span>'
                f'<span style="flex:1;min-width:0;">{inner}</span></h2>')

    def h3(self, inner):
        # 圆点 margin-top = (15px × 1.6 行高 − 8px) / 2，对齐首行中线
        h3 = f'display:flex;align-items:flex-start;color:{C["ink"]};font-size:15px;font-weight:bold;line-height:1.6;margin:22px 0 8px 0;'
        dot = f'flex:none;width:8px;height:8px;border-radius:50%;background:{C["blue"]};margin:8px 10px 0 0;'
        return f'<h3 style="{h3}"><span style="{dot}"></span><span>{inner}</span></h3>'

    def quote_label(self, kind):
        return tag(self.QUOTE_LABELS[kind], C["blue"] if kind == "tip" else C["coral"])

    def lead_label(self):
        return tag(self.LEAD_LABEL, C["yellow"])

    def hr(self):
        sq = 'display:inline-block;width:8px;height:8px;margin:0 4px;'
        dots = "".join(f'<span style="{sq}background:{c};"></span>' for c in (C["blue"], C["coral"], C["yellow"]))
        return f'<section style="text-align:center;line-height:1;margin:30px 0;">{dots}</section>'

    def figcap(self, cap, n):
        # 图片 + 色条说明：左对齐，蓝色细条打头
        return (f'<section style="display:flex;align-items:center;margin:-14px 0 22px 0;">'
                f'<span style="flex:none;display:inline-block;width:24px;height:4px;background:{C["blue"]};margin-right:8px;"></span>'
                f'<span style="font-size:12px;line-height:1.6;color:{C["text_light"]};">{cap}</span></section>')

    def ul_mark(self, depth):
        return f'<span style="{self.STYLE["ul_mark"]}"></span>', 18

    def ol_mark(self, n, depth):
        return f'<span style="{self.STYLE["ol_mark"]}">{n}</span>', 28

    def stats(self, items):
        # 数据磁贴：2～3 个纯色方块并排，蓝 → 明黄 → 珊瑚；一屏之内彩色不超过 3 种
        colors = (C["blue"], C["yellow"], C["coral"])
        top = {1: 28, 2: 22, 3: 20}[len(items)]
        avail = {1: 300, 2: 140, 3: 88}[len(items)]
        fs = fit_font([v for v, _ in items], top, avail, 13)
        cells = []
        for i, (value, label) in enumerate(items):
            bg = colors[i]
            gap = "margin-right:6px;" if i < len(items) - 1 else ""
            sub = "" if bg == C["yellow"] else "opacity:0.9;"
            cap = (f'<p style="font-size:11px;line-height:1.5;color:{ON[bg]};{sub}margin:2px 0 0 0;">{esc(label)}</p>'
                   if label else "")
            cells.append(
                f'<section style="flex:1;min-width:0;{gap}background:{bg};padding:12px 10px;">'
                f'<p style="font-size:{fs}px;font-weight:bold;line-height:1.2;color:{ON[bg]};margin:0;white-space:nowrap;'
                f'font-family:Arial,sans-serif;">{esc(value)}</p>{cap}</section>')
        return f'<section style="display:flex;margin:20px 0 22px 0;">{"".join(cells)}</section>'


THEME = FlatTheme()


def build_html(md_body: str):
    """Markdown 正文 → (扁平化排版 HTML, 图片 src 列表)。"""
    return _engine.build(THEME, md_body)
