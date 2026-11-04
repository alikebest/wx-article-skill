# -*- coding: utf-8 -*-
"""把 skill 打成 zip，用于上传到 WorkBuddy 等平台。运行：python tools/pack_zip.py

只打包运行需要的文件：SKILL.md、references/、scripts/、requirements.txt、config.example.json、README.md。
不打包：articles/（你的文章）、.claude/（本机设置）、tests/、tools/、dist/、缓存，以及任何 config.json。

输出两种结构，平台要求不明确时都可以试：
  dist/wx-article.zip         SKILL.md 在 zip 根目录（阿里云百炼、Qoder 等的要求）
  dist/wx-article-folder.zip  外面多一层 wx-article/ 文件夹（解压到 skills 目录即可用的结构）

SKILL.md 里只有 Claude Code 认识的头信息字段（argument-hint）会在包里去掉，避免严格校验的平台报错。
"""

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "wx-article"
INCLUDE_FILES = ["SKILL.md", "README.md", "requirements.txt", "config.example.json"]
INCLUDE_DIRS = ["references", "scripts"]
CLAUDE_ONLY_FIELDS = ("argument-hint",)


def collect():
    files = [ROOT / f for f in INCLUDE_FILES]
    for d in INCLUDE_DIRS:
        files += [p for p in sorted((ROOT / d).rglob("*"))
                  if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    for p in files:
        if not p.exists():
            sys.exit(f"缺少文件：{p}")
        if p.name == "config.json":
            sys.exit(f"发现 config.json，可能含密钥，已停止：{p}")
    return files


def portable_skill_md(text: str) -> str:
    """去掉只有 Claude Code 认识的头信息字段。"""
    head, sep, body = text.partition("\n---\n")
    lines = [l for l in head.splitlines() if not l.split(":", 1)[0].strip() in CLAUDE_ONLY_FIELDS]
    return "\n".join(lines) + sep + body


def write_zip(out: Path, files, prefix: str):
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            arc = prefix + p.relative_to(ROOT).as_posix()
            if p.name == "SKILL.md" and p.parent == ROOT:
                z.writestr(arc, portable_skill_md(p.read_text(encoding="utf-8")))
            else:
                z.write(p, arc)


def main():
    files = collect()
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    name = re.search(r"^name:\s*(\S+)", skill, re.M)
    if not name or name.group(1) != NAME:
        sys.exit(f"SKILL.md 的 name 应该是 {NAME}")
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    outs = [(dist / f"{NAME}.zip", ""), (dist / f"{NAME}-folder.zip", f"{NAME}/")]
    for out, prefix in outs:
        write_zip(out, files, prefix)
    print(f"打包了 {len(files)} 个文件：")
    for p in files:
        print(f"  {p.relative_to(ROOT).as_posix()}")
    for out, prefix in outs:
        print(f"\n{out}（{out.stat().st_size / 1024:.1f} KB）"
              + ("：SKILL.md 在根目录" if not prefix else f"：外面一层 {prefix}"))


if __name__ == "__main__":
    main()
