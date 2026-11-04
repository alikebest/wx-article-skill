"""推送到公众号草稿箱，并把结果追加到 <文章>.push.md。

顺序：本地检查（有错误直接拒绝，不调用任何接口）→ 上传正文图 → 上传封面 → 创建草稿。
个人主体订阅号只能推到草稿箱，发表要去后台手动点。
"""

from __future__ import annotations

import html as html_mod
import tempfile
from datetime import datetime
from pathlib import Path

from . import check, images
from .naming import step_output
from .themes import THEMES
from .wechat import WeChat


def upload_body_image(p: Path, wx: WeChat, tmp_dir: Path) -> str:
    """按格式分流上传一张正文图（规则见 images.py 开头），返回微信 CDN 地址。"""
    if p.suffix.lower() == ".svg":
        p = images.render_svg(p, tmp_dir)
    if p.suffix.lower() == ".gif":
        if p.stat().st_size > images.MAX_IMAGE_BYTES:
            raise RuntimeError(f"GIF {p.name} 超过 10MB，微信不收")
        return wx.upload_content_gif(p)
    if p.suffix.lower() not in images.CONTENT_SUFFIXES:
        p = images.convert_to_png(p, tmp_dir)
    return wx.upload_content_image(images.compress_image(p, images.CONTENT_MAX_BYTES, tmp_dir))


def apply_img_mapping(html: str, mapping: dict) -> str:
    for old, new in mapping.items():
        html = html.replace(f'src="{html_mod.escape(old, quote=True)}"',
                            f'src="{html_mod.escape(new, quote=True)}"')
    return html


def push_one(md_path: Path, wx: WeChat, account: str | None = None) -> dict | None:
    """推送一篇。wx 必须是 account 这个账号的客户端。检查不通过返回 None；成功返回推送信息。"""
    md_path = Path(md_path)
    print(f"\n===== 推送 {md_path.name} =====")
    r = check.inspect(md_path, account)
    if not r.ok:
        print(check.format_report(r))
        print("  [拒绝] 检查没通过，没有调用任何接口")
        return None
    print(f"  推送到账号：{r.account}（作者：{r.author or '空'}）")
    for w in r.warnings:
        print(f"  [警告] {w}")

    with tempfile.TemporaryDirectory(prefix="wx-article-") as tmp:
        tmp = Path(tmp)
        mapping = {}
        local = [i for i in r.images if i.status == "local"]
        for n, img in enumerate(local, 1):
            print(f"  上传正文图 {n}/{len(local)}：{img.path.name}")
            mapping[img.src] = upload_body_image(img.path, wx, tmp)
        content = apply_img_mapping(r.html, mapping)

        thumb = r.thumb_media_id
        if r.cover is not None:
            thumb = wx.upload_permanent_image(images.compress_image(r.cover, images.MAX_IMAGE_BYTES, tmp))
            print(f"  封面已上传 thumb_media_id = {thumb}")

    media_id = wx.add_draft({
        "title": r.title,
        "author": r.author,
        "digest": r.digest,
        "content": content,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
        "thumb_media_id": thumb,
    })
    print(f"  [成功] 草稿已创建 media_id = {media_id}")
    info = {
        "md": md_path, "account": r.account, "title": r.title, "theme": r.theme, "media_id": media_id,
        "thumb_media_id": thumb, "new_cover": r.cover is not None,
        "uploaded": len(local), "warnings": r.warnings,
    }
    info["record"] = write_record(info)
    print(f"  推送记录：{info['record']}")
    print("  下一步：打开 https://mp.weixin.qq.com → 草稿箱 → 预览确认后点「发表」")
    return info


def write_record(info: dict) -> Path:
    """追加一条推送记录。每推一次就新增一份草稿，所以记录是追加而不是覆盖。"""
    out = step_output(info["md"], "push")
    lines = []
    if not out.exists():
        lines += [f"# 推送记录：{info['title']}", "",
                  "每推送一次在下面追加一条。去 https://mp.weixin.qq.com → 草稿箱 预览后点「发表」。", ""]
    lines += [
        f"## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "",
        f"- 文件：`{info['md'].name}`",
        f"- 账号：{info['account']}",
        f"- 标题：{info['title']}",
        f"- 主题：{info['theme']}（{THEMES[info['theme']][0]}）",
        f"- 草稿 media_id：`{info['media_id']}`",
        f"- 封面 thumb_media_id：`{info['thumb_media_id']}`",
        f"- 正文图片：上传 {info['uploaded']} 张",
    ]
    if info["new_cover"]:
        lines.append("- 这次新增了一张封面素材。想复用它，在 md 的 front matter 写 "
                     f"`thumb_media_id: {info['thumb_media_id']}`，就不会重复上传"
                     f"（只能在账号 {info['account']} 里用）")
    lines += [f"- 警告：{w}" for w in info["warnings"]]
    lines.append("")
    with open(out, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return out
