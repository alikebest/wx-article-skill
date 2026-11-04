"""新拟态 · Neumorphism。

像一块磨砂外壳上浮雕出来的界面：元素与背景同色（冷灰 #E6E9EF），只靠右下暗影 + 左上高光
做出凸起和凹陷，强调蓝用在数字、序号、重点词上。适合数码硬件评测、参数对比。
深色模式下浮雕感基本消失，发布前要用深色模式预览。

Markdown 写法 → 新拟态组件：
  （整篇）               包在冷灰 #E6E9EF 外层容器里，阴影才立得起来
  ## 标题                一级小标题：凸起圆形序号 01、02……（蓝字）+ 标题
                         （“附”开头的、或可编号的不足 2 个时：凸起蓝色短条）
  ### 标题               二级小标题：强调蓝小圆点
  第一个 ## 前的 1～3 段   导语卡：凸起·大 +「写在前面」
  **加粗**               重点词：强调蓝加粗
  *斜体*                 重点句：浅蓝底
  > 引用                 引用块：凹陷·大
  > 💡 … / > ⚠️ …        小贴士卡 / 注意卡：凸起卡 + 胶囊小标签
  - **35dB** 降噪        数据列表（1～3 项「**数值** 说明」）→ 凸起数据圆盘并排
  - 列表 / 1. 列表       蓝色小圆点 / 凸起小圆序号
  ---                    凹槽分割线
  ![说明](图.png)        单独成段的图片放进凸起图片框（设备外壳感），说明居中灰字
  ```代码```             凹陷代码槽

指南里的刊头胶囊、大标题（由微信渲染）、参数卡、评分条、文末关注卡
无法由 Markdown 表达，不自动生成。
"""

from . import _engine
from ._engine import Theme, esc, fit_font

NAME = "新拟态 · Neumorphism"

C = {  # 冷灰版，规范见《新拟态Neumorphism-公众号排版指南.md》
    "bg": "#E6E9EF",           # 背景 = 元素色：卡片、按钮全用这个颜色，只靠阴影区分
    "dark": "#C5C9D2",         # 右下暗阴影（≈ 背景压暗 12%～15%）
    "light": "#FFFFFF",        # 左上高光
    "title": "#2F3542",        # 标题
    "text": "#3D4454",         # 正文
    "text_light": "#7A8294",   # 注释、标签、图注
    "text_sunk": "#5A6172",    # 凹陷块里的文字（略浅，像刻进去）
    "blue": "#4F6BED",         # 强调蓝：数字、重点词、序号
    "blue_bg": "#DCE3FB",      # 强调蓝浅色：少量标签底色
    "code_bg": "#DCE0E7",      # 行内代码底（比背景略深）
}


def raise_(d: int) -> str:
    """凸起：右下暗影 + 左上高光，d 为偏移，模糊取 2d。"""
    return f'box-shadow:{d}px {d}px {2 * d}px {C["dark"]},-{d}px -{d}px {2 * d}px {C["light"]};'


def sink(d: int) -> str:
    """凹陷：方向与凸起相同，换成内阴影。"""
    return f'box-shadow:inset {d}px {d}px {2 * d}px {C["dark"]},inset -{d}px -{d}px {2 * d}px {C["light"]};'


RAISE_L, RAISE_M, RAISE_S = raise_(8), raise_(6), raise_(3)
SINK_L, SINK_S = sink(6), sink(3)

# 卡片：圆角 16～20px。底边内距比顶边小 8px，正好抵掉最后一段的 margin-bottom
CARD = f'background:{C["bg"]};border-radius:18px;padding:14px 16px 6px 16px;'
PILL = 'display:inline-block;font-size:12px;font-weight:bold;line-height:1.6;padding:1px 10px;border-radius:999px;'


class NeuTheme(Theme):
    # 阴影四面扩散，左右都要留空间：外层容器内边距 20px
    CONTAINER = f'background:{C["bg"]};padding:24px 20px 28px 20px;border-radius:16px;color:{C["text"]};'
    UL_MARK_W = 18

    STYLE = {
        "p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.5px;margin:0 0 16px 0;text-align:justify;',
        "h1": f'color:{C["title"]};font-size:20px;font-weight:bold;line-height:1.55;margin:32px 0 16px 0;',
        "h2": f'display:flex;align-items:center;color:{C["title"]};font-size:17px;font-weight:bold;line-height:1.5;margin:32px 0 16px 0;',
        "h4": f'color:{C["title"]};font-size:15px;font-weight:bold;line-height:1.6;margin:18px 0 8px 0;',
        # 凹陷·大：引用块
        # 卡片上方留 18px：紧跟列表（段距只有 8px）时阴影不会挤在一起
        "blockquote": f'background:{C["bg"]};border-radius:16px;padding:14px 16px 6px 16px;margin:18px 0 24px 0;{SINK_L}',
        "quote_tip": CARD + f'margin:18px 0 24px 0;{RAISE_M}',
        "quote_warn": CARD + f'margin:18px 0 24px 0;{RAISE_M}',
        "p_in_quote": f'color:{C["text_sunk"]};font-size:14px;line-height:1.8;letter-spacing:.5px;margin:0 0 8px 0;text-align:justify;',
        "p_in_tip": f'color:{C["text"]};font-size:14px;line-height:1.8;letter-spacing:.5px;margin:0 0 8px 0;text-align:justify;',
        "p_in_warn": f'color:{C["text"]};font-size:14px;line-height:1.8;letter-spacing:.5px;margin:0 0 8px 0;text-align:justify;',
        "p_in_lead": f'color:{C["text"]};font-size:14px;line-height:1.8;letter-spacing:.5px;margin:0 0 8px 0;text-align:justify;',
        # 凸起·大：导语卡
        "lead": CARD + f'margin:0 0 28px 0;{RAISE_L}',
        # 代码块：凹陷代码槽
        "pre": f'margin:0 0 22px 0;padding:14px 16px;background:{C["bg"]};border-radius:14px;overflow-x:auto;font-size:13px;line-height:1.7;{SINK_S}',
        "pre_code": f'font-family:Consolas,Monaco,monospace;color:{C["text"]};',
        "code": f'font-family:Consolas,Monaco,monospace;background:{C["code_bg"]};color:{C["title"]};padding:1px 5px;border-radius:5px;font-size:14px;',
        # 凹槽分割线
        "hr": f'margin:30px 20%;height:6px;border-radius:999px;background:{C["bg"]};{sink(2)}',
        "table": f'width:100%;border-collapse:collapse;font-size:14px;color:{C["text"]};margin:0 0 22px 0;',
        "th": f'padding:8px 10px;color:{C["title"]};font-weight:bold;text-align:left;border-bottom:2px solid {C["dark"]};',
        "td": f'padding:8px 10px;border-bottom:1px solid #D3D7DF;',
        "a": f'color:{C["blue"]};text-decoration:none;border-bottom:1px dashed {C["blue"]};word-break:break-all;',
        "strong": f'color:{C["blue"]};font-weight:bold;',
        "strong_in_heading": 'font-weight:bold;',
        "em": f'font-style:normal;background:{C["blue_bg"]};color:{C["title"]};padding:0 4px;border-radius:4px;',
        "del": f'text-decoration:line-through;color:{C["text_light"]};',
        "img": 'max-width:100%;display:block;margin:10px auto;border-radius:14px;',
        # 图片框：凸起边框，像嵌在设备外壳里
        "fig": f'background:{C["bg"]};border-radius:22px;padding:10px;margin:0 0 24px 0;{RAISE_L}',
        "fig_img": 'display:block;max-width:100%;margin:0 auto;border-radius:14px;',
        "figcap": f'text-align:center;color:{C["text_light"]};font-size:12px;line-height:1.6;margin:-12px 0 24px 0;',
        "checkbox": 'margin-right:6px;vertical-align:middle;',
        "li_p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.5px;text-align:left;word-wrap:break-word;margin:0 0 8px 0;',
        "ul_mark": f'display:inline-block;width:8px;height:8px;border-radius:50%;background:{C["blue"]};margin-right:10px;vertical-align:2px;',
        "ol_mark": f'display:inline-block;min-width:20px;height:20px;line-height:20px;border-radius:50%;background:{C["bg"]};color:{C["blue"]};font-size:12px;font-weight:bold;text-align:center;text-indent:0;margin-right:8px;vertical-align:1px;font-family:Arial,sans-serif;{raise_(2)}',
    }

    def h2(self, inner, num, idx):
        # 核心识别符号：凸起圆形序号 + 蓝色数字。line-height 居中，flex 失效时也不歪
        ball = (f'flex:none;display:inline-block;width:34px;height:34px;line-height:34px;text-align:center;'
                f'border-radius:50%;background:{C["bg"]};color:{C["blue"]};font-size:15px;font-weight:bold;'
                f'margin-right:12px;font-family:Arial,sans-serif;{raise_(4)}')
        return (f'<h2 style="{self.STYLE["h2"]}"><span style="{ball}">{num}</span>'
                f'<span style="flex:1;min-width:0;">{inner}</span></h2>')

    def h2_plain(self, inner):
        bar = (f'flex:none;display:inline-block;width:6px;height:20px;border-radius:999px;background:{C["blue"]};'
               f'margin-right:12px;{raise_(2)}')
        return (f'<h2 style="{self.STYLE["h2"]}"><span style="{bar}"></span>'
                f'<span style="flex:1;min-width:0;">{inner}</span></h2>')

    def h3(self, inner):
        # 圆点 margin-top = (15px × 1.6 行高 − 8px) / 2，对齐首行中线；文字包进 span，免得被 flex 拆列
        h3 = f'display:flex;align-items:flex-start;color:{C["title"]};font-size:15px;font-weight:bold;line-height:1.6;margin:22px 0 10px 0;'
        dot = f'flex:none;width:8px;height:8px;border-radius:50%;background:{C["blue"]};margin:8px 10px 0 0;{raise_(2)}'
        return f'<h3 style="{h3}"><span style="{dot}"></span><span>{inner}</span></h3>'

    def quote_label(self, kind):
        # 小贴士：浅蓝胶囊；注意：实心蓝胶囊（全篇只有一个强调色，靠深浅区分）
        color = (f'background:{C["blue_bg"]};color:{C["blue"]};' if kind == "tip"
                 else f'background:{C["blue"]};color:#FFFFFF;')
        return (f'<p style="margin:0 0 8px 0;line-height:1;"><span style="{PILL}{color}">'
                f'{self.QUOTE_LABELS[kind]}</span></p>')

    def lead_label(self):
        return f'<p style="font-size:13px;font-weight:bold;line-height:1.6;color:{C["blue"]};margin:0 0 4px 0;">{self.LEAD_LABEL}</p>'

    def figcap(self, cap, n):
        return f'<p style="{self.STYLE["figcap"]}">{cap}</p>'

    def ul_mark(self, depth):
        return f'<span style="{self.STYLE["ul_mark"]}"></span>', 18

    def ol_mark(self, n, depth):
        return f'<span style="{self.STYLE["ol_mark"]}">{n}</span>', 28

    def stats(self, items):
        # 数据圆盘：数值放在凸起圆里，说明放在圆下方（说明长了也不会撑出圆外）
        fs = fit_font([v for v, _ in items], 18, 60)
        cells = []
        for value, label in items:
            disk = (f'width:72px;height:72px;line-height:72px;margin:0 auto 10px auto;border-radius:50%;'
                    f'background:{C["bg"]};text-align:center;font-size:{fs}px;font-weight:bold;color:{C["blue"]};'
                    f'white-space:nowrap;font-family:Arial,sans-serif;{RAISE_M}')
            cap = (f'<p style="font-size:12px;line-height:1.5;color:{C["text_light"]};text-align:center;margin:0;">'
                   f'{esc(label)}</p>' if label else "")
            cells.append(f'<section style="flex:1;min-width:0;padding:4px 0;"><p style="{disk}">{esc(value)}</p>{cap}</section>')
        return f'<section style="display:flex;justify-content:space-around;margin:6px 0 28px 0;">{"".join(cells)}</section>'


THEME = NeuTheme()


def build_html(md_body: str):
    """Markdown 正文 → (新拟态排版 HTML, 图片 src 列表)。"""
    return _engine.build(THEME, md_body)
