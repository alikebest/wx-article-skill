"""主题排版引擎：neu / clay / flat / minimal / bento 共用（不是主题，不登记到 THEMES）。

一个主题 = 一个 Theme 子类：
  STYLE            各元素的内联样式（键名见 Theme.style_for）
  CONTAINER        外层容器样式；新拟态、黏土这类需要浅色底的主题才填
  h2 / h2_plain / h3                 小标题结构
  quote_label / lead_label           提示卡、导语卡开头的小标题
  hr / figcap / ul_mark / ol_mark    分割线、图注、列表符号
  stats            “数据列表” → 主题的数据组件（见 find_stats）
  extra_decorate   主题专属的结构改写

在 render.decorate 的结构标注（h2 编号、提示卡、导语区）之上，这里再做三件事：
  - 数据列表：顶层无序列表 1～3 项，每项都是「**数值** 简短说明」——数值含数字且 ≤8 字，
    说明 ≤14 字，加粗后面紧跟空格而不是冒号。想保持普通列表，在加粗后加冒号（- **30h**：续航）。
  - 只有图片的段落包成图片块（<section data-fig>），主题可以给它加外框；alt 有意义时下方出图注。
  - 小标题整段交给主题生成。
白名单过滤、图片收集沿用 lime 的 ListFlattener / StyleInjector。
"""

import html as html_mod
import re

from .. import render
from . import lime

HEADINGS = ("h1", "h2", "h3", "h4")

# 这些标签带 style 属性时一定是主题自己生成的结构（正文经 mistune 转义，文章本身写不出 style），原样保留
KEEP_STYLE = {"p", "span", "section", "h2", "h3", "h4"}

# 提示卡开头的 💡/⚠️ 由卡片小标题代替；符号单独占一段时连同空段一起去掉
QUOTE_ICON_RE = re.compile(r'(<blockquote data-kind="(?:tip|warn)">\s*<p>)\s*(?:💡|⚠️?)\s*(?:</p>\s*<p>)?')
IMG_PARA_RE = re.compile(r"<p>((?:\s*<img [^>]*>\s*)+)</p>")
H2_NUM_RE = re.compile(r'<h2 data-num="(\d+)">(.*?)</h2>', re.S)
H2_RE = re.compile(r"<h2>(.*?)</h2>", re.S)
H3_RE = re.compile(r"<h3>(.*?)</h3>", re.S)
INNER_UL_RE = re.compile(r"<ul>((?:(?!</?ul>).)*?)</ul>", re.S)
STAT_ITEM_RE = re.compile(r"\s*(?:<p>)?\s*<strong>([^<]{1,40})</strong>([^<]*?)(?:</p>)?\s*", re.S)


def esc(text: str) -> str:
    return html_mod.escape(text, quote=False)


def text_len(fragment: str) -> int:
    return len(html_mod.unescape(render.plain(fragment)))


def nesting(html: str, pos: int, *tags) -> int:
    """pos 之前还没闭合的 tags 层数，用来判断某个结构是不是在顶层。"""
    head = html[:pos]
    return sum(len(re.findall(rf"<{t}\b", head)) - head.count(f"</{t}>") for t in tags)


def visual_width(text: str, latin: float = 0.6) -> float:
    """估算文字宽度（单位 em）：汉字等全角字符算 1，数字字母算 latin。"""
    return sum(1.0 if ord(c) > 0x2E7F else latin for c in text)


def fit_font(values, top: int, avail: float, floor: int = 12) -> int:
    """一行数据统一字号：取最宽的那个数值刚好放得下的大小（不超过 top），各格的说明文字底边才齐。"""
    w = max(visual_width(v, 0.58) for v in values)
    return max(floor, min(top, int(avail / max(w, 1))))


# ---------------------------------------------------------------------------
# 主题基类
# ---------------------------------------------------------------------------

class Theme:
    STYLE = {}
    CONTAINER = ""                          # 外层容器样式；空则不包
    QUOTE_LABELS = {"tip": "小贴士", "warn": "注意"}
    LEAD_LABEL = "写在前面"
    UL_MARK_W = 16                          # 嵌套列表每层的缩进

    # ---- 小标题：返回整段 HTML（inner 里的行内标签之后还会被样式注入） ----
    def h2(self, inner: str, num: str, idx: int) -> str:
        return f'<h2 style="{self.STYLE["h2"]}">{inner}</h2>'

    def h2_plain(self, inner: str) -> str:
        return f'<h2 style="{self.STYLE["h2"]}">{inner}</h2>'

    def h3(self, inner: str) -> str:
        return f'<h3 style="{self.STYLE["h3"]}">{inner}</h3>'

    # ---- 卡片小标题、分割线、图注、列表符号 ----
    def quote_label(self, kind: str) -> str:
        return ""

    def lead_label(self) -> str:
        return ""

    def hr(self) -> str:
        return f'<section style="{self.STYLE["hr"]}"></section>'

    def figcap(self, cap: str, n: int) -> str:
        return f'<p style="{self.STYLE["figcap"]}">{cap}</p>'

    def ul_mark(self, depth: int):
        """返回 (符号 HTML, 符号连同右边距的宽度)，宽度用来给折行做悬挂缩进。"""
        return f'<span style="{self.STYLE["ul_mark"]}"></span>', 16

    def ol_mark(self, n: int, depth: int):
        return f'<span style="{self.STYLE["ol_mark"]}">{n}</span>', 26

    # ---- 主题专属结构 ----
    def stats(self, items):
        """items = [(数值, 说明)]，均为未转义文本。返回 HTML；None 表示按普通列表排。"""
        return None

    def extra_decorate(self, html: str) -> str:
        return html

    def wrap(self, html: str) -> str:
        return f'<section style="{self.CONTAINER}">{html}</section>' if self.CONTAINER else html

    # ---- 样式选择 ----
    def style_for(self, tag, raw, kind, container, heading, in_pre, in_fig) -> str:
        """kind：当前元素自身的容器类型（lead / tip / warn / quote / fig，或主题自定义的类型）；
        container：最近一层外围容器的类型。按“越具体越优先”查 STYLE：
          lead、quote_<kind>（普通引用用 blockquote）、fig
          pre_code、<tag>_in_heading、p_in_<容器>（缺省 p_in_quote）、<tag>_in_<容器>、fig_img、<tag>"""
        S = self.STYLE
        if kind == "lead":
            return S["lead"]
        if kind == "fig":
            return S.get("fig", "")
        if tag == "blockquote":
            return S["blockquote"] if kind == "quote" else S.get("quote_" + kind, S["blockquote"])
        if tag == "code" and in_pre:
            return S["pre_code"]
        if heading and tag in ("strong", "em", "code", "a"):
            return S.get(tag + "_in_heading", S.get(tag, ""))
        if container:
            if tag == "p":
                return S.get("p_in_" + container, S["p_in_quote"])
            if tag in ("strong", "em", "a", "code") and f"{tag}_in_{container}" in S:
                return S[f"{tag}_in_{container}"]
        if tag == "img" and in_fig:
            return S.get("fig_img", S["img"])
        return S.get(tag, "")


# ---------------------------------------------------------------------------
# 结构标注：在 mistune 输出上改写（输入来自 escape=True，文章本身伪造不了这些结构）
# ---------------------------------------------------------------------------

def find_stats(html: str, theme: Theme) -> str:
    """顶层的“数据列表”交给 theme.stats() 渲染成数据组件，规则见文件头。"""
    def stat_items(body):
        items = re.findall(r"<li>(.*?)</li>", body, re.S)
        if not 1 <= len(items) <= 3 or not re.fullmatch(r"\s*(?:<li>.*?</li>\s*)+", body, re.S):
            return None
        out = []
        for it in items:
            m = STAT_ITEM_RE.fullmatch(it)
            if not m:
                return None
            value = html_mod.unescape(m.group(1)).strip()
            label = html_mod.unescape(m.group(2)).strip()
            if not (len(value) <= 8 and re.search(r"\d", value) and not value.startswith("第")):
                return None
            if len(label) > 14 or (label and re.match(r"[:：,，、。.;；—\-–(（]", label)):
                return None
            out.append((value, label))
        return out

    def sub(m):
        if nesting(html, m.start(), "li", "blockquote"):
            return m.group(0)
        items = stat_items(m.group(1))
        rendered = theme.stats(items) if items else None
        return rendered if rendered is not None else m.group(0)

    return INNER_UL_RE.sub(sub, html)


def build_headings(html: str, theme: Theme) -> str:
    n = 0

    def numbered(m):
        nonlocal n
        n += 1
        return theme.h2(m.group(2), m.group(1), n)

    html = H2_NUM_RE.sub(numbered, html)
    html = H2_RE.sub(lambda m: theme.h2_plain(m.group(1)), html)
    return H3_RE.sub(lambda m: theme.h3(m.group(1)), html)


def decorate(html: str, theme: Theme) -> str:
    """render.decorate → 去提示卡符号 → 主题改写 → 数据列表 → 图片块 → 小标题结构。"""
    html = QUOTE_ICON_RE.sub(r"\1", render.decorate(html))
    html = theme.extra_decorate(html)
    html = find_stats(html, theme)
    html = IMG_PARA_RE.sub(r'<section data-fig="1">\1</section>', html)
    return build_headings(html, theme)


# ---------------------------------------------------------------------------
# 列表降级与样式注入
# ---------------------------------------------------------------------------

class ThemeListFlattener(lime.ListFlattener):
    """列表 = 段落 + 符号，符号和段落样式由主题提供。"""

    def __init__(self, theme: Theme):
        super().__init__()
        self.theme = theme

    def _open_li_para(self, bare=False):
        depth = len(self.list_stack) - 1
        if self.list_stack and self.list_stack[-1][0] == "ol":
            typ, cnt = self.list_stack[-1]
            cnt += 1
            self.list_stack[-1] = (typ, cnt)
            marker, w = self.theme.ol_mark(cnt, depth)
        elif bare:
            marker, w = "", 0  # 列表项自带 ❌/✅/💡 等符号开头时不再加符号
        else:
            marker, w = self.theme.ul_mark(depth)
        indent = depth * self.theme.UL_MARK_W  # 嵌套列表的符号对齐到上一层的文字
        style = self.theme.STYLE["li_p"] + f"padding-left:{indent + w}px;text-indent:-{w}px;"
        self.out.append(f'<p style="{style}">{marker}')
        self.li_started = True


class ThemeInjector(lime.StyleInjector):
    """白名单过滤 + 内联样式 + 收集图片，样式和卡片小标题交给主题；
    引用块输出成 <section>，避开微信给 blockquote 默认加的灰色左竖线。"""

    OUT_TAG = {"blockquote": "section"}

    def __init__(self, img_collector, theme: Theme):
        super().__init__(img_collector)
        self.theme = theme
        self.kinds = []  # 与 self.stack 平行：每层的容器类型，非容器为 None
        self.fig_no = 0

    def _container(self):
        for k in reversed(self.kinds):
            if k and k != "fig":
                return k
        return None

    def _checkbox(self, attrs):
        checked = any(k == "checked" for k, _ in attrs)
        self.out.append('<input type="checkbox" disabled' + (" checked" if checked else "")
                        + f' style="{self.theme.STYLE.get("checkbox", "")}">')

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            self._checkbox(attrs)
            return
        if tag not in render.ALLOWED_TAGS:
            return  # 丢弃未知标签，内容保留
        if tag == "hr":
            self.out.append(self.theme.hr())
            return
        raw = dict(attrs)
        kind = None
        if tag == "blockquote":
            kind = raw.get("data-kind") or "quote"
        elif tag == "section" and raw.get("data-lead"):
            kind = "lead"
        elif tag == "section" and raw.get("data-fig"):
            kind = "fig"
        elif tag == "section" and raw.get("data-kind"):
            kind = raw["data-kind"]
        in_fig = bool(self.kinds) and self.kinds[-1] == "fig"

        if raw.get("style") and tag in KEEP_STYLE:
            style = raw["style"]
        else:
            style = self.theme.style_for(
                tag, raw, kind, self._container(),
                heading=any(h in self.stack for h in HEADINGS),
                in_pre="pre" in self.stack,
                in_fig=in_fig,
            )
            if tag in ("th", "td") and raw.get("style"):
                style += raw["style"]  # 表格列对齐（mistune 生成的 text-align）
        clean = self._clean_attrs(tag, raw)  # 段落里的图片在这里记下图注
        if tag == "img" and in_fig:
            cap = render.caption_of(raw.get("alt", ""))
            if cap:
                self.captions.append(cap)
        attrs_str = "".join(f' {k}="{html_mod.escape(v, quote=True)}"' for k, v in clean.items())
        style_str = f' style="{style}"' if style else ""
        self.out.append(f"<{self.OUT_TAG.get(tag, tag)}{attrs_str}{style_str}>")

        if kind in self.theme.QUOTE_LABELS:
            self.out.append(self.theme.quote_label(kind))
        elif kind == "lead":
            self.out.append(self.theme.lead_label())
        if tag not in render.VOID_TAGS:
            self.stack.append(tag)
            self.kinds.append(kind)

    def handle_endtag(self, tag):
        if tag not in render.ALLOWED_TAGS or tag in render.VOID_TAGS:
            return
        self.out.append(f"</{self.OUT_TAG.get(tag, tag)}>")
        kind = None
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
            kind = self.kinds.pop()
        if self.captions and (tag == "p" or kind == "fig"):
            self.fig_no += 1
            self.out.append(self.theme.figcap(self._caption_text(), self.fig_no))
            self.captions = []

    def close_all(self):
        while self.stack:
            tag = self.stack.pop()
            self.kinds.pop()
            self.out.append(f"</{self.OUT_TAG.get(tag, tag)}>")


def build(theme: Theme, md_body: str):
    """Markdown 正文 → (主题排版 HTML, 图片 src 列表)。"""
    raw = decorate(render.markdown_to_html(md_body), theme)
    f = ThemeListFlattener(theme)
    f.feed(raw)
    f.close()
    imgs = []
    p = ThemeInjector(imgs, theme)
    p.feed(f.result())
    p.close()
    return theme.wrap(p.result()), imgs
