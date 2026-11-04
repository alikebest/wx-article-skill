"""推送前检查：完全本地、不联网、不消耗接口配额。

问题分三级：
  错误  推送一定会失败，或会白白消耗配额（缺标题、缺封面、封面格式不对、主题不存在……）
        有错误时 push 直接拒绝
  警告  能推送，但结果可能不是你想要的（外链图显示不出来、本地图片缺失、字段会被截断……）
  提示  会自动处理的事（摘要自动生成、图片压缩或转码……）
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

from . import config, frontmatter, images, render
from .naming import step_output
from .themes import DEFAULT_THEME, THEMES, get_builder
from .wechat import AUTHOR_MAX, DIGEST_MAX, TITLE_MAX

RAW_HTML_RE = re.compile(r"<(?:/?(?:div|span|p|br|img|section|font|center|table|tr|td|strong|b|i|a)\b)[^>]*>", re.I)
ALT_TITLES_RE = re.compile(r"^##\s*附[:：]?\s*备选标题", re.M)
RECORD_ACCOUNT_RE = re.compile(r"^- 账号：(\S+)", re.M)
RECORD_THUMB_RE = re.compile(r"^- 封面 thumb_media_id：`([^`]+)`", re.M)


@dataclass
class ImageRef:
    src: str               # HTML 里的原始 src（替换时用）
    path: Path | None      # 本地文件；外链为 None
    status: str            # local / remote / missing / unsupported


@dataclass
class Report:
    md_path: Path
    meta: dict
    account: str = ""      # 推送用的账号名；空表示还没配置任何账号
    title: str = ""
    author: str = ""
    digest: str = ""
    theme: str = DEFAULT_THEME
    cover: Path | None = None
    thumb_media_id: str = ""
    html: str = ""
    images: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    infos: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _strip_code(md: str) -> str:
    return render.CODE_SPAN_RE.sub("", md)


def inspect(md_path: Path, account: str | None = None) -> Report:
    """account：命令行指定的账号名；不指定时按 文章头信息 account > 环境变量账号 > 默认账号 选择。"""
    md_path = Path(md_path)
    meta, body = frontmatter.split(md_path.read_text(encoding="utf-8"))
    r = Report(md_path=md_path, meta=meta)
    base = md_path.parent

    # 账号：决定默认作者，以及 thumb_media_id 能不能用
    default_author = ""
    try:
        r.account = config.select(account, meta.get("account"))
        if r.account:
            default_author = config.load(r.account)["author"]
        else:
            r.infos.append("还没有配置公众号账号，推送前要先运行 config --init 并填写")
    except config.ConfigError as e:
        r.errors.append(str(e))

    # 标题
    title = meta.get("title") or render.infer_title_and_digest(body)[0] or ""
    if not title:
        r.errors.append("没有标题：front matter 里没有 title，正文也没有 # 一级标题")
    elif len(title) > TITLE_MAX:
        r.warnings.append(f"标题 {len(title)} 字，超过 {TITLE_MAX} 字，推送时会截断成：{title[:TITLE_MAX]}")
        title = title[:TITLE_MAX]
    r.title = title
    if title:
        body, _ = render.strip_h1_if_title(body, title)
    if not body.strip():
        r.errors.append("正文是空的")

    # 作者
    author = meta.get("author") or default_author or ""
    if not author:
        r.infos.append("没有作者：front matter 和配置里都没填 author，草稿作者会留空")
    elif len(author) > AUTHOR_MAX:
        r.warnings.append(f"作者名超过 {AUTHOR_MAX} 字，推送时会截断成：{author[:AUTHOR_MAX]}")
        author = author[:AUTHOR_MAX]
    r.author = author

    # 摘要
    digest = meta.get("digest", "")
    if not digest:
        digest = render.infer_title_and_digest(body)[1] or ""
        r.infos.append("没写 digest，摘要会自动取正文开头 110 字")
    elif len(digest) > DIGEST_MAX:
        r.warnings.append(f"摘要 {len(digest)} 字，超过 {DIGEST_MAX} 字，推送时会截断")
    r.digest = digest[:DIGEST_MAX]

    # 主题
    r.theme = meta.get("theme", DEFAULT_THEME).lower()
    if r.theme not in THEMES:
        r.errors.append(f"主题 {r.theme} 不存在，可选：{' / '.join(THEMES)}")

    # 封面
    _check_cover(r, base)

    # 正文渲染与图片
    if r.theme in THEMES and body.strip():
        r.html, srcs = get_builder(r.theme)(body)
        _check_images(r, srcs, base)

    # 正文里的残留
    plain_md = _strip_code(body)
    if RAW_HTML_RE.search(plain_md):
        r.warnings.append("正文里有 HTML 标签，推送时会被当成普通文字原样显示，请改成 Markdown 写法")
    if ALT_TITLES_RE.search(body):
        r.warnings.append("正文末尾还留着“附：备选标题”，确认不需要的话请删掉")
    return r


def _check_cover(r: Report, base: Path):
    if r.meta.get("thumb_media_id"):
        r.thumb_media_id = r.meta["thumb_media_id"]
        r.infos.append("封面使用 thumb_media_id（已上传过的素材），不会新增素材")
        owner = _thumb_owner(r.md_path, r.thumb_media_id)
        if owner and r.account and owner != r.account:
            r.errors.append(f"thumb_media_id 是账号 {owner} 上传的素材，不能用在账号 {r.account}："
                            f"删掉 thumb_media_id 改用 cover，或者推送到账号 {owner}")
        elif not owner and len(config.accounts()[1]) > 1:
            r.warnings.append(f"thumb_media_id 只在上传它的那个账号里有效，确认它属于账号 {r.account}")
        return
    cover = r.meta.get("cover")
    if not cover:
        r.errors.append("没有封面：在 front matter 写 cover: 封面图.jpg（路径相对本 md 文件）")
        return
    p = (base / cover)
    if not p.exists():
        r.errors.append(f"封面图不存在：{p}")
    elif not p.is_file():
        r.errors.append(f"cover 指向的不是文件：{p}")
    elif p.suffix.lower() not in images.COVER_SUFFIXES:
        r.errors.append(f"封面格式 {p.suffix or '（无后缀）'} 微信不收，只接受 "
                        f"{'/'.join(sorted(s[1:] for s in images.COVER_SUFFIXES))}")
    elif p.stat().st_size == 0:
        r.errors.append(f"封面图是空文件：{p}")
    else:
        r.cover = p
        if p.stat().st_size > images.MAX_IMAGE_BYTES:
            if images.has_pillow():
                r.infos.append("封面超过 10MB，推送时会自动压缩")
            else:
                r.errors.append("封面超过 10MB，压缩需要 Pillow：pip install Pillow")


def _thumb_owner(md_path: Path, thumb: str) -> str:
    """从推送记录里查这个 thumb_media_id 是哪个账号上传的，查不到返回空字符串。"""
    record = step_output(md_path, "push")
    if not record.exists():
        return ""
    for section in re.split(r"^## ", record.read_text(encoding="utf-8"), flags=re.M):
        t = RECORD_THUMB_RE.search(section)
        a = RECORD_ACCOUNT_RE.search(section)
        if t and a and t.group(1) == thumb:
            return a.group(1)
    return ""


def _check_images(r: Report, srcs, base: Path):
    seen = set()
    for src in srcs:
        if src in seen:
            continue
        seen.add(src)
        if src.startswith(("http://", "https://")):
            r.images.append(ImageRef(src, None, "remote"))
            r.warnings.append(f"外链图片不会转存，发出去很可能显示不出来，建议下载到本地：{src}")
            continue
        if src.startswith("data:"):
            r.images.append(ImageRef(src, None, "unsupported"))
            r.warnings.append("有 data: 内嵌图片，不支持，请存成文件再引用")
            continue
        p = base / unquote(src)  # mistune 会把路径里的空格、中文转成 %xx
        if not p.is_file():
            r.images.append(ImageRef(src, None, "missing"))
            r.warnings.append(f"本地图片不存在，推送后会是裂图：{src}")
            continue
        r.images.append(ImageRef(src, p, "local"))
        _check_image_format(r, p)


def _check_image_format(r: Report, p: Path):
    suffix, size = p.suffix.lower(), p.stat().st_size
    if suffix == ".svg":
        if not (images.has_playwright() and images.has_pillow()):
            r.errors.append(f"SVG 图片 {p.name} 要先渲染，需要：pip install playwright Pillow")
        else:
            r.infos.append(f"SVG 图片 {p.name} 推送时会渲染成 PNG（有动画则转 GIF）")
    elif suffix == ".gif":
        if size > images.MAX_IMAGE_BYTES:
            r.errors.append(f"GIF {p.name} 超过 10MB，微信不收，请压缩后再推送")
    elif suffix not in images.CONTENT_SUFFIXES:
        if images.has_pillow():
            r.infos.append(f"图片 {p.name} 推送时会转成 PNG")
        else:
            r.errors.append(f"图片 {p.name} 要转成 PNG 才能上传，需要：pip install Pillow")
    elif size > images.CONTENT_MAX_BYTES:
        if images.has_pillow():
            r.infos.append(f"图片 {p.name} 超过 1MB，推送时会压缩成 JPEG")
        else:
            r.errors.append(f"图片 {p.name} 超过 1MB，压缩需要：pip install Pillow")


def format_report(r: Report) -> str:
    local = sum(i.status == "local" for i in r.images)
    lines = [
        f"文件：{r.md_path}",
        f"账号：{r.account or '（未配置）'}",
        f"标题：{r.title or '（无）'}（{len(r.title)} 字）",
        f"作者：{r.author or '（空）'}",
        f"摘要：{r.digest or '（空）'}（{len(r.digest)} 字）",
        f"封面：{r.cover.name if r.cover else ('thumb_media_id' if r.thumb_media_id else '（无）')}",
        f"主题：{r.theme}（{THEMES[r.theme][0]}）" if r.theme in THEMES else f"主题：{r.theme}",
        f"图片：{len(r.images)} 张，本地可上传 {local} 张",
        "",
    ]
    lines += [f"[错误] {m}" for m in r.errors]
    lines += [f"[警告] {m}" for m in r.warnings]
    lines += [f"[提示] {m}" for m in r.infos]
    lines.append("")
    lines.append("结论：可以推送" if r.ok else f"结论：有 {len(r.errors)} 个错误，解决后才能推送")
    return "\n".join(lines)
