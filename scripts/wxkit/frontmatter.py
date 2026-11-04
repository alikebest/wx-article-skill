"""front matter 读写：只支持单行 key: value，够用且零依赖。

所有步骤共用这一套字段，未知字段原样保留、推送时忽略：
  title           标题（≤64 字）
  author          作者（≤16 字，留空用配置里的 author）
  digest          摘要（≤120 字，留空自动取正文开头）
  cover           封面图，路径相对本 md 文件
  thumb_media_id  已上传过的封面素材 ID，优先于 cover
  theme           排版主题：lime / pink
  account         推送到哪个公众号账号（配置里的账号名），不写则用默认账号
  source_url      来源文章链接（抓取时写入）
  source_author   来源作者或公众号名
  source_time     来源发布时间
"""

import re

FM_RE = re.compile(r"\A---[ \t]*\n(.*?)^---[ \t]*(?:\n|\Z)", re.S | re.M)

# 模板里的占位文字视为未填写
PLACEHOLDERS = ("这里写", "这里填")

KEY_ORDER = ("title", "author", "digest", "cover", "thumb_media_id", "theme", "account",
             "source_url", "source_author", "source_time")


def normalize(text: str) -> str:
    """去掉 BOM，统一换行符。"""
    return text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")


def split(text: str):
    """拆出 front matter，返回 (meta, body)。值为空或是占位文字的字段不进 meta。"""
    text = normalize(text)
    m = FM_RE.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        k, v = k.strip().lower(), v.strip().strip("'\"")
        if sep and k and v and not any(p in v for p in PLACEHOLDERS):
            meta[k] = v
    return meta, text[m.end():]


def dump(meta: dict, body: str) -> str:
    """把 meta 和正文拼回完整的 md。常用字段按固定顺序，其余按原顺序排在后面。"""
    keys = [k for k in KEY_ORDER if k in meta] + [k for k in meta if k not in KEY_ORDER]
    lines = [f"{k}: {_one_line(meta[k])}".rstrip() for k in keys]
    return "---\n" + "\n".join(lines) + "\n---\n\n" + body.lstrip("\n")


def _one_line(v) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()
