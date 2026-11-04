"""与主题无关的 Markdown 处理：解析、中文加粗修正、结构标注、标题摘要推断。

各主题（themes/）在这里的输出上做白名单过滤和内联样式注入。
"""

import re

try:
    import mistune
except ImportError:
    raise SystemExit("[错误] 缺少依赖 mistune，请先运行：pip install mistune")

# 公众号会剥掉白名单以外的标签和属性
ALLOWED_TAGS = {
    "p", "h1", "h2", "h3", "h4", "blockquote", "pre", "code", "hr", "br",
    "strong", "em", "del", "a", "img", "ul", "ol", "li", "table", "thead",
    "tbody", "tr", "th", "td", "section", "span", "figure", "figcaption",
}
ALLOWED_ATTRS = {
    "a": {"href"},
    "img": {"src", "alt"},
}
VOID_TAGS = {"img", "hr", "br"}


# ---------------------------------------------------------------------------
# 中文加粗/斜体修正
# ---------------------------------------------------------------------------
# CommonMark 的定界规则对中文不友好：星号一侧紧贴标点、另一侧是汉字时（如 是**“能看到”**的），
# 加粗/斜体不被识别，正文里原样显示星号。在汉字那一侧塞一个罕用标点 EMPH_SENTINEL，
# 让两侧都是标点从而满足定界条件，渲染后再删掉。mistune 把“非空白、非字母数字”都算标点。
EMPH_SENTINEL = "⸱"
CODE_SPAN_RE = re.compile(r"(```.*?```|~~~.*?~~~|`[^`\n]+`)", re.S)
STAR_RUN_RE = re.compile(r"(?<![*\\])\*{1,3}(?!\*)")


def _is_md_punct(c: str) -> bool:
    return not c.isspace() and not c.isalnum()


def fix_cjk_emphasis(markdown: str) -> str:
    """修正紧贴中文标点的 * / ** / ***，代码块与行内代码里的星号不动。"""
    def fix(text):
        def sub(m):
            before = text[m.start() - 1] if m.start() else " "
            after = text[m.end()] if m.end() < len(text) else " "
            if before.isspace() or after.isspace():
                return m.group(0)
            if _is_md_punct(after) and not _is_md_punct(before):
                return EMPH_SENTINEL + m.group(0)
            if _is_md_punct(before) and not _is_md_punct(after):
                return m.group(0) + EMPH_SENTINEL
            return m.group(0)
        return STAR_RUN_RE.sub(sub, text)

    parts = CODE_SPAN_RE.split(markdown)
    return "".join(p if i % 2 else fix(p) for i, p in enumerate(parts))


def markdown_to_html(md_body: str) -> str:
    """Markdown → 原始 HTML（escape=True：文章里写的 HTML 标签会被转义成文字，无法注入）。"""
    md = mistune.create_markdown(escape=True, plugins=["table", "task_lists", "strikethrough"])
    return md(fix_cjk_emphasis(md_body)).replace(EMPH_SENTINEL, "")


# ---------------------------------------------------------------------------
# 结构标注
# ---------------------------------------------------------------------------

# 章节标题前加编号（01、02……）。改成 False 则所有主题都不编号。
H2_NUMBERED = True

# 小标题自带的编号（“一、”“1.”“01 ”），自动编号时去掉以免出现“01 一、……”。
# “3.5 版本”“第一步”这类不是编号，不动。
SECTION_NO_RE = re.compile(r"^\s*(?:[一二三四五六七八九十]+[、．.]|\d{1,2}[、．.)）](?!\d)|0\d(?=\s))\s*")

# 没有信息量的 alt（编辑器默认值、泛称、文件名）不显示成图注
GENERIC_ALTS = {"alt text", "image", "img", "picture", "photo", "cover",
                "图片", "配图", "头图", "截图", "封面", "插图"}


def caption_of(alt: str):
    """alt 有实际意义时返回图注文字，否则 None。"""
    a = alt.strip()
    if not a or a.lower() in GENERIC_ALTS:
        return None
    if re.fullmatch(r"[\w\-. ()（）]+\.(?:png|jpe?g|gif|webp|bmp|svg)", a, re.I):
        return None
    return a


def plain(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()


def decorate(html: str) -> str:
    """在 mistune 输出上做结构标注，主题据此选样式（data-* 属性不会输出到最终 HTML）：
    - h2 编号：data-num="01"……；“附”开头的小标题不编号；可编号的不足 2 个时整篇不编号。
    - 提示卡片：以 💡 / ⚠️ 开头的引用块标 data-kind="tip" / "warn"。
    - 导语区：第一个 h2 之前的 1～3 个文字段落包进 <section data-lead>。
    输入来自 escape=True 的 mistune，文章本身无法伪造这些属性。"""
    heads = re.findall(r"<h2>(.*?)</h2>", html, re.S)
    if H2_NUMBERED and sum(not plain(h).startswith("附") for h in heads) >= 2:
        n = 0

        def number(m):
            nonlocal n
            inner = m.group(1)
            if plain(inner).startswith("附"):
                return m.group(0)
            n += 1
            return f'<h2 data-num="{n:02d}">{SECTION_NO_RE.sub("", inner, count=1)}</h2>'

        html = re.sub(r"<h2>(.*?)</h2>", number, html, flags=re.S)

    html = re.sub(r"<blockquote>(?=\s*<p>\s*(💡|⚠))",
                  lambda m: f'<blockquote data-kind="{"tip" if m.group(1) == "💡" else "warn"}">', html)

    first_h2 = html.find("<h2")
    if first_h2 > 0:
        head = html[:first_h2]
        texts = [b for b in re.findall(r"<p>.*?</p>", head, re.S) if plain(b)]
        if 1 <= len(texts) <= 3:
            s = head.find(texts[0])
            e = head.rfind(texts[-1]) + len(texts[-1])
            if not re.search(r"<(?:pre|blockquote|table|ul|ol|h[1-6])\b", head[s:e]):
                html = (head[:s] + '<section data-lead="1">' + head[s:e] + "</section>"
                        + head[e:] + html[first_h2:])
    return html


# ---------------------------------------------------------------------------
# 标题与摘要
# ---------------------------------------------------------------------------

def strip_h1_if_title(markdown: str, title: str):
    """正文首个 H1 与标题相同时去掉，免得正文里重复一遍。返回 (body, was_stripped)。"""
    m = re.match(r"^\s*#\s+(.+?)\s*$", markdown, re.M)
    if m and m.group(1).strip() == title.strip():
        return markdown[m.end():], True
    return markdown, False


def infer_title_and_digest(md_body: str):
    """标题取正文第一个 H1；摘要取正文开头的纯文本前 110 字。"""
    m = re.search(r"^\s*#\s+(.+?)\s*$", md_body, re.M)
    title = m.group(1).strip() if m else None
    text = CODE_SPAN_RE.sub("", md_body)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)        # 图片整段去掉
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)    # 链接只留文字
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[#>*`_\-\[\]()!]", "", text)
    text = re.sub(r"^\s*\d+\.\s*", "", text, flags=re.M)
    text = re.sub(r"\s+", " ", text).strip()
    return title, (text[:110] or None)
