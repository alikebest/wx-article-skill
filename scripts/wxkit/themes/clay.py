"""黏土拟态 · Claymorphism。

像用彩色橡皮泥捏出来的一页小报：超大圆角 + 马卡龙色 + 三层阴影
（外投影浮起、右下内阴影出厚度、左上内高光鼓起来）。适合科普小报、新功能科普、数码入门。
深色模式下白色内高光可能变成发亮的白边，发布前要用深色模式预览。

Markdown 写法 → 黏土组件：
  （整篇）               包在淡紫蓝 #EEF1FB 外层容器里，黏土阴影才看得出来
  ## 标题                一级小标题：黏土序号球 1、2、3……，按章节轮换 蓝 → 薄荷绿 → 樱花粉
                         （“附”开头的、或可编号的不足 2 个时：小号黏土蓝球）
  ### 标题               二级小标题：小黏土圆点
  第一个 ## 前的 1～3 段   导语卡：白色大黏土卡 +「写在前面」
  **加粗**               重点词：强调色加粗
  *斜体*                 重点句：奶油黄柔和底
  > 引用                 浅蓝黏土卡
  > 💡 … / > ⚠️ …        小贴士卡（薄荷绿）/ 注意卡（樱花粉）
  - **+35%** 夜景亮度    数据列表（1～3 项「**数值** 说明」）→ 并排彩色数据卡
  - 列表 / 1. 列表       奶油黄小黏土球 / 黏土蓝序号球
  ---                    分割线：三颗小黏土球
  ![说明](图.png)        图片大圆角 + 柔和投影，说明居中灰字
  ```代码```             凹陷代码槽

指南里的刊头胶囊、大标题（由微信渲染）、信息/产品卡、文末关注卡
无法由 Markdown 表达，不自动生成。
"""

from . import _engine
from ._engine import Theme, esc, fit_font

NAME = "黏土拟态 · Claymorphism"

C = {  # 规范见《黏土拟态Claymorphism-公众号排版指南.md》
    "page": "#EEF1FB",         # 页面底色（外层容器）
    "card": "#F7F8FF",         # 白色系黏土卡片，比底色略亮
    "title": "#2E3350",        # 标题
    "text": "#3A3F5C",         # 正文：偏蓝的深灰
    "text_light": "#8A8FAA",   # 注释、图注
    "accent": "#6B7BF0",       # 强调文字：正文重点词、卡片小标题
}

# 黏土彩色：(名字, 黏土色, 上面的文字色, 浅底色, 彩色投影, 内阴影, 内高光)
# 浅色黏土（粉、绿、黄）上不放白字；内阴影减弱、内高光加强
CLAY = {
    "blue":   ("#7B8CFF", "#FFFFFF", "#E9ECFF", "rgba(123,140,255,0.4)", "rgba(0,0,0,0.15)", "rgba(255,255,255,0.45)"),
    "mint":   ("#9EE6C9", "#1F5C46", "#DDF7EC", "rgba(110,200,165,0.45)", "rgba(0,0,0,0.1)", "rgba(255,255,255,0.55)"),
    "pink":   ("#FFB4C8", "#7A2E48", "#FFE8EF", "rgba(255,140,170,0.35)", "rgba(0,0,0,0.08)", "rgba(255,255,255,0.6)"),
    "yellow": ("#FFD98A", "#6B4E12", "#FFF3D6", "rgba(220,170,60,0.4)", "rgba(0,0,0,0.08)", "rgba(255,255,255,0.7)"),
}
# 序号球轮换顺序：一篇最多同时用 3 种黏土色，奶油黄留给列表圆点
BALL_ORDER = ("blue", "mint", "pink")


def clay_ball(name: str, d: int = 4) -> str:
    """彩色黏土元素：外投影换成该色的彩色投影，内阴影用黑、内高光用白。d 为外投影偏移。"""
    c, _, _, drop, dark, light = CLAY[name]
    i = max(2, d - 1)
    return (f'background:{c};box-shadow:{d}px {d}px {round(d * 2.5)}px {drop},'
            f'inset -{i}px -{i}px {2 * i}px {dark},inset {i}px {i}px {2 * i}px {light};')


# 三层阴影：外投影（浮起）+ 右下内阴影（厚度）+ 左上内高光（鼓起）
WHITE_CARD = ('box-shadow:8px 8px 18px rgba(80,90,160,0.2),inset -5px -5px 10px rgba(80,90,160,0.12),'
              'inset 5px 5px 10px rgba(255,255,255,0.95);')
SUNK = 'box-shadow:inset 3px 3px 6px rgba(80,90,160,0.15),inset -3px -3px 6px rgba(255,255,255,0.9);'


def tint_card(drop: str, dark: str) -> str:
    """彩色浅底卡片的阴影（小贴士、注意、数据卡）。"""
    return f'box-shadow:7px 7px 16px {drop},inset -4px -4px 8px {dark},inset 4px 4px 8px rgba(255,255,255,0.85);'


# 黏土卡片右侧和下方留 8px，免得投影被屏幕边缘切掉。卡片上方留 18px，紧跟列表时也不挤。
# 底边内距比顶边小 8px，正好抵掉最后一段的 margin-bottom
CARD = 'border-radius:22px;padding:14px 16px 6px 16px;margin:18px 8px 26px 0;'
P_CARD = 'font-size:14px;line-height:1.8;letter-spacing:.5px;margin:0 0 8px 0;text-align:justify;'
LABEL = 'font-size:13px;font-weight:bold;line-height:1.6;margin:0 0 2px 0;'


class ClayTheme(Theme):
    CONTAINER = f'background:{C["page"]};padding:20px 16px 26px 16px;border-radius:16px;color:{C["text"]};'
    UL_MARK_W = 22

    STYLE = {
        # 正文直接排在背景上，不放进黏土卡片
        "p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.5px;margin:0 0 16px 0;text-align:justify;',
        "h1": f'color:{C["title"]};font-size:20px;font-weight:bold;line-height:1.55;margin:30px 0 14px 0;',
        "h2": f'display:flex;align-items:center;color:{C["title"]};font-size:17px;font-weight:bold;line-height:1.5;margin:30px 0 14px 0;',
        "h4": f'color:{C["title"]};font-size:15px;font-weight:bold;line-height:1.6;margin:18px 0 8px 0;',
        "blockquote": CARD + f'background:{CLAY["blue"][2]};border-radius:20px;'
                      + tint_card("rgba(123,140,255,0.3)", "rgba(80,90,200,0.12)"),
        "quote_tip": CARD + f'background:{CLAY["mint"][2]};border-radius:20px;'
                     + tint_card("rgba(110,200,165,0.3)", "rgba(60,150,115,0.12)"),
        "quote_warn": CARD + f'background:{CLAY["pink"][2]};border-radius:20px;'
                      + tint_card("rgba(255,140,170,0.28)", "rgba(200,90,120,0.12)"),
        "p_in_quote": f'color:{C["text"]};' + P_CARD,
        "lead": CARD.replace("margin:18px 8px 26px 0", "margin:0 8px 28px 0") + f'background:{C["card"]};' + WHITE_CARD,
        # 代码块：卡片色凹陷槽
        "pre": f'margin:18px 8px 22px 0;padding:14px 16px;background:{C["card"]};border-radius:18px;overflow-x:auto;font-size:13px;line-height:1.7;{SUNK}',
        "pre_code": f'font-family:Consolas,Monaco,monospace;color:{C["text"]};',
        "code": f'font-family:Consolas,Monaco,monospace;background:{C["card"]};color:#5A63C8;padding:1px 6px;border-radius:6px;font-size:14px;',
        "table": f'width:100%;border-collapse:collapse;font-size:14px;color:{C["text"]};margin:0 0 22px 0;',
        "th": f'padding:8px 10px;background:{CLAY["blue"][2]};color:{C["title"]};font-weight:bold;text-align:left;border-bottom:2px solid #D5DBF7;',
        "td": f'padding:8px 10px;background:{C["card"]};border-bottom:1px solid #E1E5F6;',
        "a": f'color:{C["accent"]};text-decoration:none;border-bottom:1px dashed {C["accent"]};word-break:break-all;',
        "strong": f'color:{C["accent"]};font-weight:bold;',
        "strong_in_heading": 'font-weight:bold;',
        "em": f'font-style:normal;background:#FFEDC2;color:{C["title"]};padding:0 4px;border-radius:6px;',
        "del": f'text-decoration:line-through;color:{C["text_light"]};',
        "img": 'max-width:100%;display:block;margin:10px auto;border-radius:20px;',
        # 图片容器：大圆角 + 柔和投影，右侧留 8px 给投影
        "fig": 'margin:4px 8px 24px 0;',
        "fig_img": 'display:block;max-width:100%;margin:0 auto;border-radius:20px;box-shadow:8px 8px 18px rgba(80,90,160,0.2);',
        "figcap": f'text-align:center;color:{C["text_light"]};font-size:12px;line-height:1.6;margin:-10px 0 24px 0;',
        "checkbox": 'margin-right:6px;vertical-align:middle;',
        "li_p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.5px;text-align:left;word-wrap:break-word;margin:0 0 8px 0;',
        "ul_mark": f'display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:10px;vertical-align:-1px;{clay_ball("yellow", 2)}',
        "ol_mark": (f'display:inline-block;min-width:20px;height:20px;line-height:20px;border-radius:50%;color:#FFFFFF;'
                    f'font-size:12px;font-weight:bold;text-align:center;text-indent:0;margin-right:8px;vertical-align:1px;'
                    f'font-family:Arial,sans-serif;{clay_ball("blue", 2)}'),
    }

    def h2(self, inner, num, idx):
        # 核心识别符号：黏土序号球，按章节轮换颜色。line-height 居中，flex 失效时也不歪
        name = BALL_ORDER[(idx - 1) % len(BALL_ORDER)]
        ball = (f'flex:none;display:inline-block;width:32px;height:32px;line-height:32px;text-align:center;'
                f'border-radius:50%;color:{CLAY[name][1]};font-size:15px;font-weight:bold;margin-right:10px;'
                f'font-family:Arial,sans-serif;{clay_ball(name)}')
        return (f'<h2 style="{self.STYLE["h2"]}"><span style="{ball}">{int(num)}</span>'
                f'<span style="flex:1;min-width:0;">{inner}</span></h2>')

    def h2_plain(self, inner):
        ball = f'flex:none;display:inline-block;width:16px;height:16px;border-radius:50%;margin-right:12px;{clay_ball("blue", 3)}'
        return (f'<h2 style="{self.STYLE["h2"]}"><span style="{ball}"></span>'
                f'<span style="flex:1;min-width:0;">{inner}</span></h2>')

    def h3(self, inner):
        # 圆点 margin-top = (15px × 1.6 行高 − 12px) / 2，对齐首行中线
        h3 = f'display:flex;align-items:flex-start;color:{C["title"]};font-size:15px;font-weight:bold;line-height:1.6;margin:20px 0 8px 0;'
        dot = f'flex:none;width:12px;height:12px;border-radius:50%;margin:6px 10px 0 0;{clay_ball("blue", 2)}'
        return f'<h3 style="{h3}"><span style="{dot}"></span><span>{inner}</span></h3>'

    def quote_label(self, kind):
        color = "#2F8A66" if kind == "tip" else "#C24D72"
        return f'<p style="{LABEL}color:{color};">{self.QUOTE_LABELS[kind]}</p>'

    def lead_label(self):
        return f'<p style="{LABEL}color:{C["accent"]};">{self.LEAD_LABEL}</p>'

    def hr(self):
        ball = 'display:inline-block;width:10px;height:10px;border-radius:50%;margin:0 6px;'
        balls = "".join(f'<span style="{ball}{clay_ball(n, 2)}"></span>' for n in BALL_ORDER)
        return f'<section style="text-align:center;line-height:1;margin:28px 0;">{balls}</section>'

    def ul_mark(self, depth):
        return f'<span style="{self.STYLE["ul_mark"]}"></span>', 22

    def ol_mark(self, n, depth):
        return f'<span style="{self.STYLE["ol_mark"]}">{n}</span>', 28

    def stats(self, items):
        # 数据卡：并排彩色黏土块，大数字。蓝 → 黄 → 薄荷，数字用各自的深色
        palette = (("blue", "#6B7BF0", "rgba(123,140,255,0.3)", "rgba(80,90,200,0.12)"),
                   ("yellow", "#B07D12", "rgba(220,170,60,0.3)", "rgba(180,130,30,0.12)"),
                   ("mint", "#2F8A66", "rgba(110,200,165,0.3)", "rgba(60,150,115,0.12)"))
        top = {1: 30, 2: 24, 3: 20}[len(items)]
        avail = {1: 260, 2: 120, 3: 76}[len(items)]
        fs = fit_font([v for v, _ in items], top, avail, 13)
        cells = []
        for i, (value, label) in enumerate(items):
            name, fg, drop, dark = palette[i]
            gap = "margin-right:12px;" if i < len(items) - 1 else ""
            cap = (f'<p style="font-size:12px;line-height:1.5;color:{C["text_light"]};margin:4px 0 0 0;">{esc(label)}</p>'
                   if label else "")
            cells.append(
                f'<section style="flex:1;min-width:0;{gap}background:{CLAY[name][2]};border-radius:20px;'
                f'padding:14px 8px;text-align:center;{tint_card(drop, dark)}">'
                f'<p style="font-size:{fs}px;font-weight:bold;line-height:1.2;color:{fg};margin:0;white-space:nowrap;'
                f'font-family:Arial,sans-serif;">{esc(value)}</p>{cap}</section>')
        return f'<section style="display:flex;margin:18px 8px 28px 0;">{"".join(cells)}</section>'


THEME = ClayTheme()


def build_html(md_body: str):
    """Markdown 正文 → (黏土拟态排版 HTML, 图片 src 列表)。"""
    return _engine.build(THEME, md_body)
