# -*- coding: utf-8 -*-
"""把 skill 打成 zip，用于上传到 WorkBuddy 等平台。运行：python tools/pack_zip.py [--skip-tests]

只打包运行需要的文件：SKILL.md、references/、scripts/、requirements.txt、config.example.json、README.md。
不打包：articles/（你的文章）、.claude/（本机设置）、tests/、tools/、dist/、缓存，以及任何 config.json。

输出两种结构，平台要求不明确时都可以试：
  dist/wx-article.zip         SKILL.md 在 zip 根目录（阿里云百炼、Qoder 等的要求）
  dist/wx-article-folder.zip  外面多一层 wx-article/ 文件夹（解压到 skills 目录即可用的结构）

SKILL.md 里只有 Claude Code 认识的头信息字段（argument-hint）会在包里去掉，避免严格校验的平台报错。

步骤：
  1. 跑 tests/test_wxkit.py，有失败就停止，不动 dist/（--skip-tests 跳过）
  2. 打包。包里是工作区里的文件：有未提交的改动或没加入 git 的文件会列出来提醒
  3. 把包解压到临时目录自检：导入全部模块，跑 themes 和 gallery（所有主题渲染一遍），
     确认包里不缺文件。自检失败时 dist/ 里旧的包保持不动
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "wx-article"
INCLUDE_FILES = ["SKILL.md", "README.md", "requirements.txt", "config.example.json"]
INCLUDE_DIRS = ["references", "scripts"]
CLAUDE_ONLY_FIELDS = ("argument-hint",)

# 自检：在解压出来的包里导入全部模块（不联网、不读配置）
IMPORT_ALL = r"""
import importlib, pkgutil, sys
sys.path.insert(0, "scripts")
import wxkit, wxkit.themes
for pkg in (wxkit, wxkit.themes):
    for m in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        importlib.import_module(m.name)
print("ok")
"""


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


def git(*args) -> str:
    """在 skill 目录跑 git，git 不可用或不是仓库时返回空字符串。"""
    try:
        r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return r.stdout if r.returncode == 0 else ""


def git_state(files):
    """返回 (当前提交, [(状态, 相对路径)])：打进包里、但和当前提交不一致的文件。"""
    commit = git("rev-parse", "--short", "HEAD").strip()
    if not commit:
        return "", []
    rel = {p.relative_to(ROOT).as_posix() for p in files}
    dirty = []
    # -z：路径原样输出，中文文件名不会被转义；--untracked-files=all 列出新文件夹里的每个文件
    out = git("status", "--porcelain", "-z", "--untracked-files=all", "--", *INCLUDE_FILES, *INCLUDE_DIRS)
    prefix = git("rev-parse", "--show-prefix").strip()  # skill 目录在仓库里的相对位置
    for entry in filter(None, out.split("\0")):
        code, path = entry[:2], entry[3:]
        path = path[len(prefix):] if prefix and path.startswith(prefix) else path
        if path in rel:
            dirty.append(("未加入 git" if code == "??" else "有未提交的改动", path))
    return commit, dirty


def write_zip(out: Path, files, prefix: str, comment: str):
    tmp = out.with_name(out.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        z.comment = comment.encode("utf-8")
        for p in files:
            arc = prefix + p.relative_to(ROOT).as_posix()
            if p.name == "SKILL.md" and p.parent == ROOT:
                z.writestr(arc, portable_skill_md(p.read_text(encoding="utf-8")))
            else:
                z.write(p, arc)
    return tmp


def run(cmd, cwd):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}  # 免得导入到仓库里的代码
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def smoke_test(zip_path: Path, prefix: str, n_files: int):
    """解压到临时目录，确认包能独立运行。返回错误说明，没问题返回空字符串。"""
    with tempfile.TemporaryDirectory(prefix="wx-article-pack-", ignore_cleanup_errors=True) as d:
        with zipfile.ZipFile(zip_path) as z:
            if len(z.namelist()) != n_files:
                return f"包里有 {len(z.namelist())} 个文件，应该是 {n_files} 个"
            z.extractall(d)
        pkg = Path(d) / prefix
        skill = (pkg / "SKILL.md").read_text(encoding="utf-8")
        if any(re.search(rf"^{f}:", skill, re.M) for f in CLAUDE_ONLY_FIELDS):
            return "包里的 SKILL.md 还带着只有 Claude Code 认识的头信息字段"
        checks = [
            ("导入全部模块", [sys.executable, "-c", IMPORT_ALL]),
            ("themes", [sys.executable, "scripts/wxflow.py", "themes"]),
            ("gallery", [sys.executable, "scripts/wxflow.py", "gallery", "--no-open", "-o", str(Path(d) / "gallery.html")]),
        ]
        for label, cmd in checks:
            r = run(cmd, pkg)
            if r.returncode != 0 or "[错误]" in r.stdout:
                return f"{label} 失败：\n{(r.stdout + r.stderr).strip()}"
    return ""


def main():
    ap = argparse.ArgumentParser(description="把 wx-article skill 打成 zip，输出到 dist/")
    ap.add_argument("--skip-tests", action="store_true", help="不跑 tests/test_wxkit.py（解压自检照做）")
    args = ap.parse_args()

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    name = re.search(r"^name:\s*(\S+)", skill, re.M)
    if not name or name.group(1) != NAME:
        sys.exit(f"SKILL.md 的 name 应该是 {NAME}")

    if not args.skip_tests:
        print("跑测试 ...")
        r = run([sys.executable, str(ROOT / "tests" / "test_wxkit.py")], ROOT)
        last = (r.stdout.strip().splitlines() or ["（没有输出）"])[-1]
        if r.returncode != 0:
            print((r.stdout + r.stderr).strip())
            sys.exit(f"\n测试没通过，没有打包：{last}")
        print(f"  {last}")

    files = collect()
    commit, dirty = git_state(files)
    comment = f"{NAME} {commit or '（不在 git 仓库里）'}" + ("，含未提交的改动" if dirty else "")

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    outs = [(dist / f"{NAME}.zip", ""), (dist / f"{NAME}-folder.zip", f"{NAME}/")]
    tmps = []
    try:
        for out, prefix in outs:
            tmp = write_zip(out, files, prefix, comment)
            tmps.append(tmp)
            print(f"自检 {out.name} ...")
            err = smoke_test(tmp, prefix, len(files))
            if err:
                sys.exit(f"{out.name} 自检失败，dist/ 里的旧包没动：\n{err}")
        for (out, _), tmp in zip(outs, tmps):
            os.replace(tmp, out)  # 两个包都自检通过才一起替换
    finally:
        for tmp in tmps:
            tmp.unlink(missing_ok=True)

    print(f"\n打包了 {len(files)} 个文件：")
    for p in files:
        print(f"  {p.relative_to(ROOT).as_posix()}")
    for out, prefix in outs:
        print(f"\n{out}（{out.stat().st_size / 1024:.1f} KB）"
              + ("：SKILL.md 在根目录" if not prefix else f"：外面一层 {prefix}"))
    print(f"\n基于提交：{commit or '（不在 git 仓库里）'}")
    if dirty:
        print("注意：下面这些文件和当前提交不一致，包里用的是工作区的版本：")
        for state, path in dirty:
            print(f"  [{state}] {path}")


if __name__ == "__main__":
    main()
