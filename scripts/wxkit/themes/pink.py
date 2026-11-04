"""樱花粉 · 荧光笔。

柔和干净的手账风：粉色像荧光笔一样划在文字下方，不大面积铺色。
适合数码好物推荐、轻松科技话题、生活类内容。

结构标注、白名单过滤沿用 lime，只换样式和部分结构：
  - h2 包一层荧光笔 span，编号放在笔迹里、用主色；h3 前加粉色圆点
  - 引用块输出成 <section>（避开微信给 blockquote 默认加的灰色竖线），
    提示卡、导语卡开头补一行小标题，💡/⚠️ 符号由小标题代替
  - 小标题里的加粗不变粉，图注前加 ▲
"""

import html as html_mod
import re

from .. import render
from . import lime

NAME = "樱花粉 · 荧光笔"

C = {
    "title": "#333333",        # 大标题
    "text": "#444444",         # 正文、小标题（小标题不用粉色）
    "text_light": "#888888",   # 图注、注释等次要信息
    "pink": "#D96C8A",         # 主色：只用于“点”，即重点词、序号、链接，不用于整句整段
    "pink_hl": "#F9D3DE",      # 高亮粉：荧光笔、表格线
    "pink_bg": "#FCEEF2",      # 浅底粉：引用块、导语卡、序号底
    "pink_dot": "#E8A9BA",     # 分割线三点
    "violet": "#8C7AB0",       # 点缀紫：小贴士标题
    "violet_bg": "#F3F0F8",    # 浅底紫：小贴士卡
    "bg_code": "#F7F5F6",
}

# 荧光笔：从文字 58%（正文 60%）高度往下铺高亮粉，像笔划过字的下半截。
# 若发现 linear-gradient 被微信过滤，改成 False 退化为整块浅底粉高亮。
HIGHLIGHT_GRADIENT = True


def highlighter(start: int) -> str:
    if HIGHLIGHT_GRADIENT:
        return f'background:linear-gradient(transparent {start}%,{C["pink_hl"]} {start}%);padding:0 2px;'
    return f'background:{C["pink_bg"]};padding:0 4px;border-radius:3px;'


# 风格要“软”：圆角 6～12px，不用粗描边和硬阴影，描边最多 1px 浅粉。
# 卡片底边内距比顶边小 8px，正好抵掉最后一段的 margin-bottom。
CARD = 'border-radius:8px;padding:12px 14px 4px 14px;margin:0 0 20px 0;'
CARD_LABEL = 'font-size:13px;font-weight:bold;line-height:1.6;margin:0 0 4px 0;'

STYLE = {
    # 块级
    "p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.5px;margin:0 0 16px 0;text-align:justify;',
    "h1": f'color:{C["title"]};font-size:20px;font-weight:bold;line-height:1.6;margin:32px 0 14px 0;',
    # 一级小标题：块本身不上色，荧光笔画在内层 span 上，只盖住文字宽度
    "h2": f'color:{C["text"]};font-size:17px;font-weight:bold;line-height:1.6;margin:32px 0 14px 0;',
    "h2_hl": highlighter(58),
    "h2_index": f'color:{C["pink"]};margin-right:6px;',
    # 二级小标题：粉色小圆点 + 深灰加粗。文字包进一个 span，免得行内代码等被 flex 拆成单独一列；
    # 圆点 margin-top = (15px × 1.6 行高 − 6px) / 2，对齐首行中线
    "h3": f'display:flex;align-items:flex-start;color:{C["text"]};font-size:15px;font-weight:bold;line-height:1.6;margin:22px 0 10px 0;',
    "h3_dot": f'flex:none;width:6px;height:6px;border-radius:50%;background:{C["pink"]};margin:9px 8px 0 0;',
    "h4": f'color:{C["text"]};font-size:15px;font-weight:bold;line-height:1.6;margin:18px 0 8px 0;',
    # 引用块与卡片统一输出成 <section>
    "blockquote": CARD + f'background:{C["pink_bg"]};border-radius:6px;',
    "quote_tip": CARD + f'background:{C["violet_bg"]};',
    "quote_warn": CARD + f'background:{C["violet_bg"]};',
    "quote_label": CARD_LABEL + f'color:{C["violet"]};',
    "p_in_quote": f'color:{C["text"]};font-size:14px;line-height:1.8;letter-spacing:.5px;margin:0 0 8px 0;text-align:justify;',
    # 开头导语卡：浅底粉，左上角“写在前面”
    "lead": CARD.replace("margin:0 0 20px 0", "margin:0 0 24px 0") + f'background:{C["pink_bg"]};',
    "lead_label": CARD_LABEL + f'color:{C["pink"]};',
    # 代码块：浅暖灰圆角，不用黑底，免得打破整篇的柔和
    "pre": f'margin:0 0 18px 0;padding:12px 14px;background:{C["bg_code"]};border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.7;',
    # 分割线：粉色三点。letter-spacing 会在最后一个点后面也留 8px，左边补同样的内距才居中
    "hr": f'text-align:center;color:{C["pink_dot"]};font-size:16px;line-height:1;letter-spacing:8px;padding-left:8px;margin:24px 0;',
    "table": f'width:100%;border-collapse:collapse;font-size:14px;color:{C["text"]};margin:0 0 18px 0;',
    "th": f'padding:8px 10px;background:{C["pink_bg"]};color:{C["text"]};border:1px solid {C["pink_hl"]};font-weight:bold;text-align:left;',
    "td": f'padding:8px 10px;border:1px solid {C["pink_hl"]};',
    # 行内：加粗 = 重点词（主色粉）；斜体 = 重点句（荧光笔）
    "a": f'color:{C["pink"]};text-decoration:none;border-bottom:1px solid {C["pink_hl"]};word-break:break-all;',
    "strong": f'color:{C["pink"]};font-weight:bold;',
    "strong_in_heading": 'font-weight:bold;',
    "em": 'font-style:normal;' + highlighter(60),
    "del": f'text-decoration:line-through;color:{C["text_light"]};',
    "code": f'font-family:Consolas,Monaco,monospace;background:{C["bg_code"]};color:{C["text"]};padding:1px 5px;border-radius:4px;font-size:14px;',
    "pre_code": f'font-family:Consolas,Monaco,monospace;color:{C["text"]};',
    "img": 'max-width:100%;display:block;margin:10px auto;border-radius:6px;',
    "figcap": f'text-align:center;color:{C["text_light"]};font-size:12px;line-height:1.6;margin:-8px 0 18px 0;',
    "checkbox": 'margin-right:6px;vertical-align:middle;',
    # 列表：段落样式 + 悬挂缩进；无序用粉色小圆点，有序用浅粉圆底主色数字。
    # 列表项常是“名称：长网址”，两端对齐会把网址前那一行字拉得很散，所以左对齐，长网址允许折断
    "li_p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.5px;text-align:left;word-wrap:break-word;margin:0 0 8px 0;',
    "ul_mark": f'display:inline-block;width:6px;height:6px;border-radius:50%;background:{C["pink"]};margin-right:10px;vertical-align:3px;',
    "ol_mark": f'display:inline-block;min-width:18px;height:18px;line-height:18px;border-radius:9px;background:{C["pink_bg"]};color:{C["pink"]};font-size:12px;font-weight:bold;text-align:center;text-indent:0;margin-right:8px;vertical-align:1px;font-family:Arial,sans-serif;',
}

UL_MARK_W, OL_MARK_W = 16, 26

QUOTE_LABELS = {"tip": "小贴士", "warn": "注意"}
LEAD_LABEL = "写在前面"
HEADINGS = ("h1", "h2", "h3", "h4")


class PinkListFlattener(lime.ListFlattener):
    """只换列表符号和段落样式。"""

    def _open_li_para(self, bare=False):
        indent = (len(self.list_stack) - 1) * UL_MARK_W
        if self.list_stack and self.list_stack[-1][0] == "ol":
            typ, cnt = self.list_stack[-1]
            cnt += 1
            self.list_stack[-1] = (typ, cnt)
            marker, w = f'<span style="{STYLE["ol_mark"]}">{cnt}</span>', OL_MARK_W
        elif bare:
            marker, w = "", 0
        else:
            marker, w = f'<span style="{STYLE["ul_mark"]}"></span>', UL_MARK_W
        style = STYLE["li_p"] + f"padding-left:{indent + w}px;text-indent:-{w}px;"
        self.out.append(f'<p style="{style}">{marker}')
        self.li_started = True


class PinkStyleInjector(lime.StyleInjector):
    OUT_TAG = {"blockquote": "section"}

    def __init__(self, img_collector):
        super().__init__(img_collector)
        self.heading_tail = ""  # 当前小标题闭合前要补的收尾标签

    def _checkbox(self, attrs):
        checked = any(k == "checked" for k, _ in attrs)
        self.out.append('<input type="checkbox" disabled' + (" checked" if checked else "")
                        + f' style="{STYLE["checkbox"]}">')

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            self._checkbox(attrs)
            return
        if tag not in render.ALLOWED_TAGS:
            return
        if tag == "hr":
            self.out.append(f'<section style="{STYLE["hr"]}">• • •</section>')
            return
        raw = dict(attrs)
        style = STYLE.get(tag, "")
        if tag in ("p", "span") and raw.get("style"):
            style = raw["style"]
        elif tag == "p" and ("blockquote" in self.stack or "section" in self.stack):
            style = STYLE["p_in_quote"]
        elif tag == "code" and "pre" in self.stack:
            style = STYLE["pre_code"]
        elif tag == "strong" and any(h in self.stack for h in HEADINGS):
            style = STYLE["strong_in_heading"]  # 小标题文字不用粉色
        elif tag == "blockquote" and raw.get("data-kind") in QUOTE_LABELS:
            style = STYLE["quote_" + raw["data-kind"]]
        elif tag == "section" and raw.get("data-lead"):
            style = STYLE["lead"]
        clean = self._clean_attrs(tag, raw)
        attrs_str = "".join(f' {k}="{html_mod.escape(v, quote=True)}"' for k, v in clean.items())
        style_str = f' style="{style}"' if style else ""
        self.out.append(f"<{self.OUT_TAG.get(tag, tag)}{attrs_str}{style_str}>")

        if tag == "h2":
            num = raw.get("data-num")
            self.out.append(f'<span style="{STYLE["h2_hl"]}">')
            if num:
                self.out.append(f'<span style="{STYLE["h2_index"]}">{html_mod.escape(num)}</span>')
            self.heading_tail = "</span>"
        elif tag == "h3":
            self.out.append(f'<span style="{STYLE["h3_dot"]}"></span><span>')
            self.heading_tail = "</span>"
        elif tag == "blockquote" and raw.get("data-kind") in QUOTE_LABELS:
            self.out.append(f'<p style="{STYLE["quote_label"]}">{QUOTE_LABELS[raw["data-kind"]]}</p>')
        elif tag == "section" and raw.get("data-lead"):
            self.out.append(f'<p style="{STYLE["lead_label"]}">{LEAD_LABEL}</p>')
        if tag not in render.VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag not in render.ALLOWED_TAGS or tag in render.VOID_TAGS:
            return
        if tag in ("h2", "h3") and self.heading_tail:
            self.out.append(self.heading_tail)
            self.heading_tail = ""
        self.out.append(f"</{self.OUT_TAG.get(tag, tag)}>")
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        if tag == "p" and self.captions:
            self.out.append(f'<p style="{STYLE["figcap"]}">▲ {self._caption_text()}</p>')
            self.captions = []

    def close_all(self):
        while self.stack:
            tag = self.stack.pop()
            self.out.append(f"</{self.OUT_TAG.get(tag, tag)}>")


# 提示卡开头的 💡/⚠️ 由卡片小标题代替；符号单独占一段时连同空段一起去掉
QUOTE_ICON_RE = re.compile(r'(<blockquote data-kind="(?:tip|warn)">\s*<p>)\s*(?:💡|⚠️?)\s*(?:</p>\s*<p>)?')


def build_html(md_body: str):
    """Markdown 正文 → (樱花粉排版 HTML, 图片 src 列表)。"""
    raw = QUOTE_ICON_RE.sub(r"\1", render.decorate(render.markdown_to_html(md_body)))
    return lime._run(PinkListFlattener, PinkStyleInjector, raw)
