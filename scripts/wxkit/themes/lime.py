"""荧光柠绿 · 新粗野主义（默认主题）。

黑白高对比，柠绿/电紫点缀，粗黑描边 + 不模糊的硬阴影 + 零圆角。
适合 AI 工具、独立开发、效率工具、科技资讯类内容。

全部用内联样式：公众号编辑器会剥掉 <style> 和 class。
这里的 ListFlattener / StyleInjector 同时是其他主题的基类。
"""

import html as html_mod
import unicodedata
from html.parser import HTMLParser

from .. import render

NAME = "荧光柠绿 · 新粗野主义"

C = {
    "ink": "#111111",          # 墨黑：标题、描边、硬阴影、编号块
    "text": "#222222",         # 正文
    "text_light": "#666666",   # 图注、引述等次要信息
    "lime": "#B8F34A",         # 荧光柠绿：只当背景，或放在黑底上当字色，绝不在浅底上当字色
    "violet": "#8B7CF6",       # 电紫：标签、卡片彩色阴影、下划线强调
    "bg_code": "#f2f2f2",
}

# 粗野感全靠“粗黑描边 + 硬阴影 + 零圆角”撑起来，只用在标题、标签、卡片上，正文保持朴素。
# 带硬阴影的卡片右侧多留 6px，否则阴影会被手机屏幕边缘切掉。
LINE = f'2px solid {C["ink"]}'
CARD = f'margin:22px 6px 22px 0;padding:12px 14px 4px 14px;background:#fff;border:{LINE};color:{C["text"]};font-size:14px;line-height:1.8;'

STYLE = {
    # 块级
    "p": f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.5px;margin:0 0 16px 0;text-align:justify;',
    "h1": f'color:{C["ink"]};font-size:20px;font-weight:bold;line-height:1.5;margin:36px 0 16px 0;',
    # 普通 h2（“附”开头的、或整篇不编号时）：粗黑下划线
    "h2": f'color:{C["ink"]};font-size:17px;font-weight:bold;line-height:1.5;margin:36px 0 16px 0;padding:2px 0;border-bottom:2.5px solid {C["ink"]};',
    "h3": f'color:{C["ink"]};font-size:16px;font-weight:bold;line-height:1.6;margin:28px 0 12px 0;padding-left:10px;border-left:4px solid {C["ink"]};',
    "h4": f'color:{C["ink"]};font-size:15px;font-weight:bold;line-height:1.6;margin:24px 0 10px 0;',
    # 编号章节：黑底柠绿编号块 + 标题 + 粗黑下划线，是这套风格的识别符号
    "h2_num": f'display:flex;align-items:stretch;color:{C["ink"]};font-size:17px;font-weight:bold;line-height:1.5;margin:36px 0 16px 0;border-bottom:2.5px solid {C["ink"]};',
    "h2_index": f'flex:none;display:flex;align-items:center;background:{C["ink"]};color:{C["lime"]};font-size:16px;padding:2px 9px;font-family:Arial,sans-serif;',
    "h2_text": 'padding:2px 10px;',
    # 普通引用（原样引述某人的话）不做卡片，只用一道粗黑竖线，免得和提示卡片抢
    "blockquote": f'margin:22px 0;padding:2px 0 2px 14px;border-left:3px solid {C["ink"]};color:{C["text_light"]};font-size:14px;line-height:1.8;',
    "quote_tip": CARD + f'box-shadow:4px 4px 0 {C["violet"]};',
    "quote_warn": CARD + f'box-shadow:4px 4px 0 {C["ink"]};',
    "p_in_quote": 'margin:0 0 8px 0;line-height:1.8;letter-spacing:.5px;text-align:justify;',
    # 开头导语区：导语卡片，左上角一枚电紫小标签「写在前面」
    "lead": CARD.replace("margin:22px 6px 22px 0", "margin:0 6px 26px 0") + f'box-shadow:4px 4px 0 {C["ink"]};',
    "lead_tag": f'display:inline-block;background:{C["violet"]};color:{C["ink"]};font-size:12px;font-weight:bold;line-height:1.6;padding:0 6px;border:1.5px solid {C["ink"]};margin-bottom:6px;font-family:Arial,sans-serif;',
    # 代码块：黑底，呼应“终端”的联想
    "pre": f'margin:22px 0;padding:14px 16px;background:{C["ink"]};overflow-x:auto;font-size:13px;line-height:1.7;',
    # 分割线：黑线中间一颗旋转 45° 的柠绿小方块（transform 被过滤时变成正方块，不影响阅读）
    "hr": 'display:flex;align-items:center;margin:28px 0;',
    "hr_line": f'flex:1;border-top:{LINE};',
    "hr_dot": f'flex:none;width:10px;height:10px;background:{C["lime"]};border:{LINE};transform:rotate(45deg);margin:0 8px;',
    "table_wrap": 'margin:22px 0;overflow-x:auto;',
    "table": f'width:100%;border-collapse:collapse;font-size:14px;color:{C["text"]};border:{LINE};',
    "th": f'padding:8px 10px;background:{C["lime"]};color:{C["ink"]};border:1px solid {C["ink"]};font-weight:bold;text-align:left;',
    "td": f'padding:8px 10px;border:1px solid {C["ink"]};',
    # 行内：加粗 = 重要信息，整块柠绿底；斜体 = 观点/转折，电紫下划线
    "a": f'color:{C["ink"]};text-decoration:none;border-bottom:1px dashed {C["ink"]};word-break:break-all;',
    "strong": f'color:{C["ink"]};font-weight:bold;background:{C["lime"]};padding:0 3px;',
    "em": f'font-style:normal;font-weight:bold;color:{C["ink"]};border-bottom:2px solid {C["violet"]};',
    "del": f'text-decoration:line-through;color:{C["text_light"]};',
    "code": f'font-family:Consolas,Monaco,monospace;background:{C["bg_code"]};color:{C["ink"]};padding:1px 5px;font-size:14px;',
    "pre_code": 'font-family:Consolas,Monaco,monospace;color:#f0f0f0;',
    "img": 'max-width:100%;display:block;margin:10px auto;',
    "figcap": f'text-align:center;color:{C["text_light"]};font-size:12px;margin:-8px 0 20px 0;',
    "checkbox": 'margin-right:6px;vertical-align:middle;',
    # 列表符号（见 ListFlattener）：无序用柠绿方块 + 黑框，有序用黑底柠绿数字，与章节编号呼应
    "ul_mark": f'display:inline-block;width:8px;height:8px;background:{C["lime"]};border:{LINE};margin-right:8px;vertical-align:1px;',
    "ol_mark": f'display:inline-block;min-width:18px;line-height:18px;background:{C["ink"]};color:{C["lime"]};font-size:12px;font-weight:bold;text-align:center;text-indent:0;margin-right:8px;vertical-align:1px;font-family:Arial,sans-serif;',
}

# 列表符号连同右边距的宽度，用来给折行做悬挂缩进（续行与首行文字对齐）
UL_MARK_W, OL_MARK_W = 20, 26


class ListFlattener(HTMLParser):
    """把 <ol>/<ul>/<li> 降级为“段落 + 符号前缀”。

    微信编辑器对原生列表支持差（剥 list-style、编号丢失、缩进错位），
    公众号正文的通行做法就是“列表 = 段落 + 符号”。
    - ol/ul/li 本身不输出，每个 li 开始处输出一个带前缀的 <p>，li 结束时输出 </p>；
    - li 内 mistune 包的宽松 <p> 壳吞掉，免得 p 套 p；
    - 列表项以 ❌/✅/💡 这类符号开头时不再加前缀符号。
    子类改 _open_li_para 就能换符号和段落样式。
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.list_stack = []     # [('ol'|'ul', li_count)]
        self.in_li = False
        self.li_started = False  # 当前 li 是否已输出前缀段落

    def _open_li_para(self, bare=False):
        indent = (len(self.list_stack) - 1) * UL_MARK_W  # 嵌套列表的符号对齐到上一层的文字
        if self.list_stack and self.list_stack[-1][0] == "ol":
            typ, cnt = self.list_stack[-1]
            cnt += 1
            self.list_stack[-1] = (typ, cnt)
            marker, w = f'<span style="{STYLE["ol_mark"]}">{cnt}</span>', OL_MARK_W
        elif bare:
            marker, w = "", 0
        else:
            marker, w = f'<span style="{STYLE["ul_mark"]}"></span>', UL_MARK_W
        # 悬挂缩进：首行左移符号宽度，折行的续行与首行文字对齐。
        # 列表项常是“名称：长网址”，两端对齐会把网址前那一行字拉得很散，所以左对齐，长网址允许折断
        style = (
            f'color:{C["text"]};font-size:15px;line-height:1.8;letter-spacing:.5px;'
            f'text-align:left;word-wrap:break-word;'
            f'margin:0 0 10px 0;padding-left:{indent + w}px;text-indent:-{w}px;'
        )
        self.out.append(f'<p style="{style}">{marker}')
        self.li_started = True

    def _ensure_prefix(self):
        if self.in_li and not self.li_started:
            self._open_li_para()

    def handle_starttag(self, tag, attrs):
        if tag in ("ol", "ul"):
            self.list_stack.append((tag, 0))
            return
        if tag == "li":
            self.in_li = True
            self.li_started = False
            return
        if tag == "p" and self.in_li:
            return
        self._ensure_prefix()
        self.out.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag == "li":
            if self.in_li and not self.li_started:
                self._open_li_para()  # 空 li 也补前缀
            if self.li_started:
                self.out.append("</p>")
                self.li_started = False
            self.in_li = False
            return
        if tag in ("ol", "ul"):
            if self.list_stack:
                self.list_stack.pop()
            return
        if tag == "p" and self.in_li:
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if self.in_li and not self.li_started:
            if not data.strip():
                return  # li 开头的空白不触发前缀，等真正的内容来决定加不加符号
            self._open_li_para(bare=unicodedata.category(data.lstrip()[0]) == "So")
        self.out.append(html_mod.escape(data, quote=False))

    def handle_entityref(self, name):
        self._ensure_prefix()
        self.out.append(f"&{name};")

    def handle_startendtag(self, tag, attrs):
        self._ensure_prefix()
        self.out.append(self.get_starttag_text())

    def result(self):
        return "".join(self.out)


class StyleInjector(HTMLParser):
    """白名单过滤 + 注入内联样式 + 收集图片 src。输入需已经过 ListFlattener。"""

    def __init__(self, img_collector):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.img_collector = img_collector
        self.stack = []         # 当前打开的非 void 标签
        self.captions = []      # 当前段落里待输出的图注（段落结束后补一行）
        self.in_num_h2 = False  # 是否在编号章节标题里（标题文字包在 span 里，闭合前要收尾）

    def _checkbox(self, attrs):
        # task_lists 的 checkbox：微信编辑器允许 input[type=checkbox][disabled] 保留
        checked = any(k == "checked" for k, _ in attrs)
        self.out.append('<input type="checkbox" disabled' + (" checked" if checked else "")
                        + f' style="{STYLE["checkbox"]}">')

    def _clean_attrs(self, tag, raw):
        clean = {k: v for k, v in raw.items() if k in render.ALLOWED_ATTRS.get(tag, set())}
        if tag == "a":
            if raw.get("href", "").startswith(("http://", "https://")):
                clean["href"] = raw["href"]
            else:
                clean.pop("href", None)
        if tag == "img":
            src = raw.get("src", "")
            if src:
                self.img_collector.append(src)
                clean["src"] = src
            alt = raw.get("alt", "")
            if alt:
                clean["alt"] = alt
            cap = render.caption_of(alt)
            if cap and self.stack and self.stack[-1] == "p":
                self.captions.append(cap)
        return clean

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            self._checkbox(attrs)
            return
        if tag not in render.ALLOWED_TAGS:
            return  # 丢弃未知标签，内容保留
        if tag == "hr":
            self.out.append(f'<section style="{STYLE["hr"]}"><span style="{STYLE["hr_line"]}"></span>'
                            f'<span style="{STYLE["hr_dot"]}"></span><span style="{STYLE["hr_line"]}"></span></section>')
            return
        raw = dict(attrs)
        style = STYLE.get(tag, "")
        if tag in ("p", "span") and raw.get("style"):
            # ListFlattener 生成的列表段落与符号自带样式。正文经 mistune 转义，这里的 style 不可能来自文章本身
            style = raw["style"]
        elif tag == "p" and ("blockquote" in self.stack or "section" in self.stack):
            style = STYLE["p_in_quote"]  # 引用块、导语区里的段落继承容器的颜色字号
        elif tag == "code" and "pre" in self.stack:
            style = STYLE["pre_code"]
        elif tag == "h2" and raw.get("data-num"):
            style = STYLE["h2_num"]
        elif tag == "blockquote" and raw.get("data-kind") in ("tip", "warn"):
            style = STYLE["quote_" + raw["data-kind"]]
        elif tag == "section" and raw.get("data-lead"):
            style = STYLE["lead"]
        clean = self._clean_attrs(tag, raw)
        attrs_str = "".join(f' {k}="{html_mod.escape(v, quote=True)}"' for k, v in clean.items())
        style_str = f' style="{style}"' if style else ""
        self.out.append(f"<{tag}{attrs_str}{style_str}>")
        if tag == "h2" and raw.get("data-num"):
            self.out.append(f'<span style="{STYLE["h2_index"]}">{html_mod.escape(raw["data-num"])}</span>'
                            f'<span style="{STYLE["h2_text"]}">')
            self.in_num_h2 = True
        elif tag == "section" and raw.get("data-lead"):
            self.out.append(f'<span style="{STYLE["lead_tag"]}">写在前面</span>')
        if tag not in render.VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag not in render.ALLOWED_TAGS or tag in render.VOID_TAGS:
            return
        if tag == "h2" and self.in_num_h2:
            self.out.append("</span>")
            self.in_num_h2 = False
        self.out.append(f"</{tag}>")
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        if tag == "p" and self.captions:
            self.out.append(f'<p style="{STYLE["figcap"]}">{self._caption_text()}</p>')
            self.captions = []

    def _caption_text(self):
        return html_mod.escape("　".join(self.captions), quote=False)

    def handle_data(self, data):
        self.out.append(html_mod.escape(data, quote=False))

    def handle_entityref(self, name):
        self.out.append(f"&{name};")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)  # img/hr/br 等自闭合标签按 starttag 处理（不入栈）

    def close_all(self):
        while self.stack:
            self.out.append(f"</{self.stack.pop()}>")

    def result(self):
        self.close_all()
        return "".join(self.out)


def _run(parser_cls, injector_cls, html: str):
    f = parser_cls()
    f.feed(html)
    f.close()
    imgs = []
    p = injector_cls(imgs)
    p.feed(f.result())
    p.close()
    return p.result(), imgs


def build_html(md_body: str):
    """Markdown 正文 → (排版后的 HTML, 图片 src 列表)。"""
    raw = render.decorate(render.markdown_to_html(md_body))
    return _run(ListFlattener, StyleInjector, raw)
