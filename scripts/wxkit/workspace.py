"""一篇文章一个文件夹：<根目录>/<年-月-日-序号>/article.md，例如 2026-11-12-01。

后续每一步的输出都写在输入文件旁边（见 naming.py），封面 cover.jpg 也放在 md 旁边，
所以文章从这里开始，重写、排版、推送的产物就都落在同一个文件夹里。

  序号    当天已有的最大序号加 1，删掉中间某篇也不会撞号；两位起，超过 99 自然变成三位
  根目录  命令行 -o > 环境变量 WX_ARTICLE_DIR > 配置 articles_dir > 当前目录下的 articles/
  进度    list 从文件夹里已有哪些文件推断，不另记状态，也就不会和实际情况对不上
"""

import re
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from . import config, frontmatter
from .naming import STEPS

DIR_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{2,})$")
ARTICLE = "article.md"
TITLE_PLACEHOLDER = "这里写标题"
PUSH_ENTRY_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2})", re.M)
PUSH_ACCOUNT_RE = re.compile(r"^- 账号：(.+)$", re.M)


def resolve_root(cli=None):
    """返回 (根目录, 来源)。来源为空字符串表示没有配置固定根目录，用的是当前目录下的 articles/。"""
    if cli:
        return Path(cli).expanduser().resolve(), "命令行"
    root, source = config.articles_dir()
    if root:
        return root, source
    return (Path.cwd() / "articles").resolve(), ""


# ---------------------------------------------------------------------------
# 新建
# ---------------------------------------------------------------------------

def next_name(root: Path, day: date = None) -> str:
    day_s = (day or date.today()).isoformat()
    # 文件也算进来：同名文件存在时 mkdir 同样会失败
    seqs = [int(m.group(2)) for p in _children(root)
            if (m := DIR_RE.match(p.name)) and m.group(1) == day_s]
    return f"{day_s}-{max(seqs, default=0) + 1:02d}"


def make_dir(root: Path, day: date = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for _ in range(20):  # 两个进程同时新建时，后建的那个重新取号
        d = root / next_name(root, day)
        try:
            d.mkdir()
            return d
        except FileExistsError:
            continue
    raise RuntimeError(f"在 {root} 里新建文件夹失败，请检查是否有同名文件")


def new_article(root: Path, title: str = "", day: date = None) -> Path:
    """新建文件夹和一个只有头信息的 article.md，返回 article.md 的路径。"""
    md = make_dir(root, day) / ARTICLE
    md.write_text(frontmatter.dump({"title": title.strip() or TITLE_PLACEHOLDER}, ""), encoding="utf-8")
    return md


# ---------------------------------------------------------------------------
# 抓取落到哪个文件夹
# ---------------------------------------------------------------------------

def url_key(url: str) -> str:
    """同一篇文章的不同链接写法归一：忽略协议、chksm、scene 等跟踪参数和 #rd。"""
    u = urlsplit((url or "").strip())
    host = u.netloc.lower()
    if u.path.startswith("/s/") and len(u.path.rstrip("/")) > 3:
        return host + u.path.rstrip("/")
    q = dict(parse_qsl(u.query))
    ids = [q.get(k, "") for k in ("__biz", "mid", "idx", "sn")]
    if any(ids):
        return host + u.path + "?" + "&".join(ids)
    return host + u.path + "?" + u.query


def find_fetched(root: Path, url: str, meta: dict):
    """找以前抓过同一篇的文件夹。先比链接；短链接和长链接指向同一篇时比不出来，
    再比 标题 + 来源作者 + 发布时间，三项都相同才算。"""
    dirs = [(d, _meta(d / ARTICLE)) for d in _article_dirs(root)]
    key = url_key(url)
    for d, m in dirs:
        if m.get("source_url") and url_key(m["source_url"]) == key:
            return d
    fields = ("title", "source_author", "source_time")
    if all(meta.get(k) for k in fields):
        for d, m in dirs:
            if all(m.get(k) == meta[k] for k in fields):
                return d
    return None


def fetch_target(root: Path, url: str, meta: dict, into=None, day: date = None):
    """返回 (文件夹, 方式)。方式：指定 / 沿用 / 新建。

    --into 指定时：文件夹必须已存在；里面的 article.md 已经有正文、又不是同一篇时拒绝，免得冲掉写好的稿子。
    没指定时：同一篇以前抓过就沿用原文件夹，否则按今天的日期新建。"""
    if into:
        d = Path(into).expanduser()
        if not d.is_dir():
            d = root / into
        if not d.is_dir():
            raise RuntimeError(f"文件夹不存在：{into}。先用 new 新建，或者去掉 --into 让抓取自动新建")
        md = d / ARTICLE
        if has_body(md) and url_key(_meta(md).get("source_url", "")) != url_key(url):
            raise RuntimeError(f"{md} 里已经有正文，不能覆盖。换一个文件夹，或者去掉 --into 让抓取自动新建")
        return d, "指定"
    found = find_fetched(root, url, meta)
    if found:
        return found, "沿用"
    return make_dir(root, day), "新建"


def has_body(md: Path) -> bool:
    if not md.is_file():
        return False
    return bool(frontmatter.split(md.read_text(encoding="utf-8"))[1].strip())


# ---------------------------------------------------------------------------
# 列出文章
# ---------------------------------------------------------------------------

# 进度从高到低；标题也按这个顺序取，后面的步骤常会改标题
STAGES = (("push", "已推送"), ("layout", "已排版"), ("rewrite", "已重写"),
          ("polish", "已美化"), ("facts", "重写中"))


def entries(root: Path) -> list:
    return [describe(d) for d in _article_dirs(root, include_empty=True)]


def describe(d: Path) -> dict:
    by_step = {}
    for p in d.glob("*.md"):
        head, dot, tail = p.stem.rpartition(".")
        by_step.setdefault(tail if dot and head and tail in STEPS else "", []).append(p)

    stage = next((label for step, label in STAGES if step in by_step), "")
    article = d / ARTICLE
    if not stage:
        if _meta(article).get("source_url"):
            stage = "已抓取"
        elif has_body(article) or any(has_body(p) for p in by_step.get("", [])):
            stage = "写稿中"
        else:
            stage = "空稿"

    title = ""
    for step in ("layout", "rewrite", "polish", ""):
        for p in sorted(by_step.get(step, []), key=lambda p: p.stat().st_mtime, reverse=True):
            title = _title(p)
            if title:
                break
        if title:
            break

    pushes, last_push, last_account = 0, "", ""
    for p in by_step.get("push", []):
        text = p.read_text(encoding="utf-8")
        times = PUSH_ENTRY_RE.findall(text)
        pushes += len(times)
        if times and times[-1] > last_push:
            last_push = times[-1]
            accounts = PUSH_ACCOUNT_RE.findall(text)
            last_account = accounts[-1].strip() if accounts else ""

    return {"name": d.name, "dir": d, "title": title, "stage": stage,
            "cover": (d / "cover.jpg").is_file(), "pushes": pushes,
            "last_push": last_push, "last_account": last_account}


def format_entry(e: dict, title_width: int = 32) -> str:
    title = _fit(e["title"] or "（无标题）", title_width)
    status = e["stage"]
    if e["pushes"]:
        status = f"已推送 {e['pushes']} 次（最近 {e['last_push'][5:]}"
        status += f" · {e['last_account']}）" if e["last_account"] else "）"
    elif e["stage"] == "已排版" and not e["cover"]:
        status += "  缺封面 cover.jpg"
    return f"{e['name']}  {title}  {status}"


# ---------------------------------------------------------------------------

def _children(root: Path):
    return list(root.iterdir()) if root.is_dir() else []


def _article_dirs(root: Path, include_empty=False):
    """新格式的文件夹，以及含 article.md 的旧文件夹（如以前按 日期_标题 命名的抓取结果）。"""
    return sorted(p for p in _children(root) if p.is_dir() and (
        (p / ARTICLE).is_file() or (include_empty and DIR_RE.match(p.name))))


def _meta(md: Path) -> dict:
    if not md.is_file():
        return {}
    return frontmatter.split(md.read_text(encoding="utf-8"))[0]


def _title(md: Path) -> str:
    meta, body = frontmatter.split(md.read_text(encoding="utf-8"))
    if meta.get("title"):
        return meta["title"]
    m = re.search(r"^#[ \t]+(.+)$", body, re.M)
    return m.group(1).strip() if m else ""


def _width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def _fit(s: str, width: int) -> str:
    """按终端显示宽度截断并补齐（汉字占两格），让后面的进度列对齐。"""
    if _width(s) > width:
        while _width(s) > width - 3:
            s = s[:-1]
        s += "..."
    return s + " " * (width - _width(s))
