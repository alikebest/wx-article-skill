"""每一步的输出文件命名：去掉输入文件名里已有的步骤后缀，再加上本步后缀。

  article.md          → article.rewrite.md / article.polish.md / article.layout.md
  article.rewrite.md  → article.layout.md
  article.layout.md   → article.push.md
预览页与 md 同名，只换扩展名：article.layout.md → article.layout.html
"""

from pathlib import Path

STEPS = ("facts", "rewrite", "polish", "layout", "push")


def base_stem(path: Path) -> str:
    stem = Path(path).stem
    while True:
        head, dot, tail = stem.rpartition(".")
        if dot and head and tail in STEPS:
            stem = head
        else:
            return stem


def step_output(path: Path, step: str) -> Path:
    path = Path(path)
    return path.with_name(f"{base_stem(path)}.{step}.md")
