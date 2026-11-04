"""本地预览页：模拟手机上的文章页，加上封面裁切和检查结果。不联网、不消耗配额。

正文 HTML 与推送时发给微信的完全相同（同一个主题函数生成），只是图片还是本地路径。
预览页写在 md 旁边、与 md 同名，所以正文和封面的相对路径都能直接显示。
"""

import html as html_mod
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from .check import Report
from .themes import THEMES

MARKER = "<!-- wx-article preview -->"

PAGE = """<!doctype html>
{marker}
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>预览 · {title}</title>
<style>
  :root {{ --bg:#ededed; --card:#fff; --ink:#1f1f1f; --muted:#8a8a8a; --line:#e5e5e5;
          --err:#c62828; --warn:#b26a00; --info:#4a6a8a; --link:#576b95; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
         font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif; }}
  .wrap {{ display:flex; flex-wrap:wrap; gap:24px; justify-content:center; align-items:flex-start;
          padding:24px 16px 48px; }}
  .side {{ width:340px; max-width:100%; display:flex; flex-direction:column; gap:16px; }}
  .card {{ background:var(--card); border-radius:10px; padding:16px; font-size:13px; line-height:1.7; }}
  .card h2 {{ margin:0 0 10px; font-size:14px; }}
  .kv {{ display:grid; grid-template-columns:4.5em 1fr; gap:4px 8px; }}
  .kv dt {{ color:var(--muted); }} .kv dd {{ margin:0; overflow-wrap:anywhere; }}
  .feed {{ display:flex; gap:10px; align-items:center; border:1px solid var(--line); border-radius:8px;
          padding:10px; }}
  .feed .t {{ flex:1; font-size:15px; font-weight:600; line-height:1.4; }}
  .c235 {{ width:100%; aspect-ratio:2.35/1; object-fit:cover; border-radius:6px; display:block; background:#ddd; }}
  .c11 {{ width:64px; height:64px; object-fit:cover; border-radius:4px; flex:none; background:#ddd; }}
  .none {{ display:flex; align-items:center; justify-content:center; color:var(--err); font-size:12px; }}
  .cap {{ color:var(--muted); font-size:12px; margin:6px 0 12px; }}
  ul.msg {{ margin:0; padding-left:1.2em; }} ul.msg li {{ margin:2px 0; overflow-wrap:anywhere; }}
  .e {{ color:var(--err); }} .w {{ color:var(--warn); }} .i {{ color:var(--info); }}
  .ok {{ color:#2e7d32; font-weight:600; }} .bad {{ color:var(--err); font-weight:600; }}
  .phone {{ width:375px; max-width:100%; background:#fff; border-radius:12px; overflow:hidden;
           box-shadow:0 2px 16px rgba(0,0,0,.08); }}
  .article {{ padding:22px 16px 40px; overflow-wrap:break-word; }}  /* 与公众号文章页一致：长串可折行 */
  .a-title {{ font-size:22px; font-weight:bold; line-height:1.4; margin:0 0 14px; }}
  .a-meta {{ font-size:15px; color:rgba(0,0,0,.3); margin-bottom:22px; }}
  .a-meta span {{ color:var(--link); margin-right:8px; }}
  .note {{ color:var(--muted); font-size:12px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="side">
    <div class="card">
      <h2>推送信息</h2>
      <dl class="kv">
        <dt>账号</dt><dd>{account}</dd>
        <dt>标题</dt><dd>{title}（{title_len} 字）</dd>
        <dt>作者</dt><dd>{author}</dd>
        <dt>摘要</dt><dd>{digest}（{digest_len} 字）</dd>
        <dt>主题</dt><dd>{theme}</dd>
        <dt>文件</dt><dd>{md_name}</dd>
      </dl>
    </div>
    <div class="card">
      <h2>封面</h2>
      {cover_block}
    </div>
    <div class="card">
      <h2>检查结果</h2>
      <p class="{verdict_cls}">{verdict}</p>
      {messages}
    </div>
    <p class="note">生成于 {now}。手机宽度 375px 模拟，最终效果以公众号后台的预览为准。</p>
  </div>
  <div class="phone">
    <div class="article">
      <h1 class="a-title">{title}</h1>
      <div class="a-meta"><span>{author}</span>{date}</div>
      {content}
    </div>
  </div>
</div>
</body>
</html>
"""


def _e(s) -> str:
    return html_mod.escape(str(s or ""), quote=True)


def _cover_block(r: Report, page_dir: Path) -> str:
    if r.cover:
        rel = quote(Path(r.cover).resolve().relative_to(page_dir.resolve()).as_posix()) \
            if _is_under(r.cover, page_dir) else Path(r.cover).resolve().as_uri()
        return (f'<img class="c235" src="{_e(rel)}" alt="">'
                f'<p class="cap">订阅号消息列表里的大图，按 2.35:1 裁切</p>'
                f'<div class="feed"><div class="t">{_e(r.title)}</div>'
                f'<img class="c11" src="{_e(rel)}" alt=""></div>'
                f'<p class="cap">次条和转发卡片里的小图，按 1:1 裁切</p>')
    if r.thumb_media_id:
        return '<p class="cap">使用已上传的封面素材（thumb_media_id），本地无法预览</p>'
    return '<div class="c235 none">没有封面，推送会被拒绝</div>'


def _is_under(p: Path, d: Path) -> bool:
    try:
        Path(p).resolve().relative_to(Path(d).resolve())
        return True
    except ValueError:
        return False


def _messages(r: Report) -> str:
    items = ([f'<li class="e">错误：{_e(m)}</li>' for m in r.errors]
             + [f'<li class="w">警告：{_e(m)}</li>' for m in r.warnings]
             + [f'<li class="i">提示：{_e(m)}</li>' for m in r.infos])
    return f'<ul class="msg">{"".join(items)}</ul>' if items else ""


def build(r: Report) -> Path:
    """生成预览页，返回路径（md 同名 .html）。"""
    out = r.md_path.with_suffix(".html")
    if out.exists() and MARKER not in out.read_text(encoding="utf-8", errors="ignore")[:200]:
        raise FileExistsError(f"{out} 已存在且不是本工具生成的预览页，为避免覆盖已停止")
    theme = f"{r.theme}（{THEMES[r.theme][0]}）" if r.theme in THEMES else r.theme
    page = PAGE.format(
        marker=MARKER,
        account=_e(r.account or "（未配置）"),
        title=_e(r.title or "（无标题）"), title_len=len(r.title),
        author=_e(r.author or "（未填作者）"),
        digest=_e(r.digest or "（空）"), digest_len=len(r.digest),
        theme=_e(theme), md_name=_e(r.md_path.name),
        cover_block=_cover_block(r, out.parent),
        verdict_cls="ok" if r.ok else "bad",
        verdict="可以推送" if r.ok else f"有 {len(r.errors)} 个错误，解决后才能推送",
        messages=_messages(r),
        now=datetime.now().strftime("%Y-%m-%d %H:%M"),
        date=datetime.now().strftime("%Y年%m月%d日"),
        content=r.html or '<p style="color:#c62828">正文没有渲染出来，见左侧检查结果</p>',
    )
    out.write_text(page, encoding="utf-8")
    return out
