"""抓取公众号文章：正文转 Markdown，图片下载到本地。

输出：<根目录>/<发布日期>_<标题>/article.md + images/
同一篇重复抓取会落到同一个目录（覆盖 article.md，已下载的图片不重复下载）。

front matter 只写来源信息，不写 author / cover：
  title          原标题
  source_url     原文链接
  source_author  原作者或公众号名
  source_time    原文发布时间
"""

import glob
import hashlib
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

from . import frontmatter

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif",
       "image/webp": ".webp", "image/svg+xml": ".svg"}


def _deps():
    try:
        from bs4 import BeautifulSoup
        from markdownify import markdownify
    except ImportError:
        raise RuntimeError("抓取需要 beautifulsoup4 和 markdownify：pip install beautifulsoup4 markdownify")
    return BeautifulSoup, markdownify


def safe_name(s: str, maxlen: int = 60) -> str:
    """Windows 文件名不能含 \\/:*?"<>| 和控制字符，也不能以点或空格结尾。"""
    s = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", s).strip()
    return s[:maxlen].rstrip(". ")


def _save_image(session, url: str, img_dir: Path):
    # 去掉 tp=webp 拿原始格式；#imgIndex 片段对图片无意义
    u = urlsplit(url)
    url = urlunsplit(u._replace(query=urlencode([(k, v) for k, v in parse_qsl(u.query) if k != "tp"]),
                                fragment=""))
    name = hashlib.md5(url.encode()).hexdigest()[:16]
    if old := glob.glob(str(img_dir / (name + ".*"))):
        return Path(old[0])
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"  [警告] 图片下载失败（{type(e).__name__}）：{url}", file=sys.stderr)
        return None
    ctype = r.headers.get("Content-Type", "").split(";")[0].strip()
    if not ctype.startswith("image/"):
        print(f"  [警告] 图片下载失败（Content-Type: {ctype}）：{url}", file=sys.stderr)
        return None
    path = img_dir / (name + EXT.get(ctype, ".jpg"))
    path.write_bytes(r.content)
    return path


def _download_images(body, out_dir: Path):
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Referer": "https://mp.weixin.qq.com/"})
    saved, total = {}, 0
    for img in body.find_all("img"):
        src = img.get("src", "")
        if not src.startswith("http"):
            continue
        total += 1
        if src not in saved:
            saved[src] = _save_image(session, src, img_dir)
        if saved[src]:  # 下载失败的保留远程地址，check 会提示
            img["src"] = "images/" + saved[src].name
    ok = sum(map(bool, saved.values()))
    return ok, len(saved), total


def tidy(md: str) -> str:
    """清理 markdownify 输出：不间断空格、只有空白的行、连续空行。"""
    md = md.replace("\xa0", " ").replace("​", "")
    md = re.sub(r"^[ \t]+$", "", md, flags=re.M)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def fetch(url: str, root: Path) -> dict:
    BeautifulSoup, markdownify = _deps()
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError(f"打开文章失败（{type(e).__name__}），请检查链接和网络") from None
    html = r.text
    if 'id="js_content"' not in html:
        raise RuntimeError(f"没拿到正文（HTTP {r.status_code}）：链接不是公众号文章页，"
                           "或者被微信的访问验证拦截了，过一会儿再试或换个网络")
    soup = BeautifulSoup(html, "html.parser")

    def text(sel):
        el = soup.select_one(sel)
        return el.get_text(strip=True) if el else None

    title = text("h1#activity-name") or ""
    # #publish_time 由 JS 填充，静态 HTML 里为空，改从 var ct 时间戳取
    ct = re.search(r'var ct\s*=\s*"(\d+)"', html)
    publish_time = text("#publish_time") or (
        datetime.fromtimestamp(int(ct.group(1))).strftime("%Y-%m-%d %H:%M") if ct else "")
    author = text("#js_author_name") or text("#js_name") or ""

    body = soup.select_one("#js_content")
    for img in body.find_all("img"):
        if img.get("data-src"):
            img["src"] = img["data-src"]

    name = "_".join(filter(None, [publish_time[:10], title])) or hashlib.md5(url.encode()).hexdigest()[:8]
    out_dir = Path(root) / safe_name(name)
    out_dir.mkdir(parents=True, exist_ok=True)
    ok, uniq, total = _download_images(body, out_dir)

    # 秀米等编辑器会把整段正文包进 <h1>，转 Markdown 时段落会被压成一行、图片只剩 alt
    for h in body.find_all(re.compile(r"^h[1-6]$")):
        if h.find(["p", "section", "img"]):
            h.name = "div"
    content = tidy(markdownify(str(body), heading_style="ATX"))

    meta = {"title": title, "source_url": url, "source_author": author, "source_time": publish_time}
    md_path = out_dir / "article.md"
    existed = md_path.exists()
    md_path.write_text(frontmatter.dump({k: v for k, v in meta.items() if v}, content), encoding="utf-8")
    return {"path": md_path, "overwritten": existed, "title": title, "author": author,
            "publish_time": publish_time, "images_ok": ok, "images_unique": uniq,
            "images_total": total, "chars": len(content)}
