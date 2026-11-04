"""排版主题注册表。新增主题：写一个模块，提供 NAME 和 build_html(md_body) -> (html, img_srcs)，再登记到 THEMES。

neu / clay / flat / minimal / bento 共用 _engine.py（主题类 + 样式注入），写新主题时也可以照着它们来。
"""

from importlib import import_module

# 主题 id → (显示名, 适合的内容)
THEMES = {
    "lime": ("荧光柠绿 · 新粗野主义", "黑白高对比、粗描边硬阴影，适合 AI 工具、独立开发、效率工具、科技资讯"),
    "pink": ("樱花粉 · 荧光笔", "柔和手账风、荧光笔划重点，适合数码好物、轻松科技话题、生活类内容"),
    "neu": ("新拟态 · Neumorphism", "同色浮雕、一个强调蓝，适合数码硬件评测、参数对比；深色模式下浮雕感会消失"),
    "clay": ("黏土拟态 · Claymorphism", "马卡龙色、超大圆角、三层阴影，适合科普小报、新功能科普、数码入门"),
    "flat": ("扁平化 · Flat Design", "纯色块、零阴影零渐变、四色撞色，适合日更资讯，深色模式最稳"),
    "minimal": ("夸张极简 · Exaggerated Minimalism", "超大字号、大量留白、一个橙红强调色，适合观点、深度解读、年度盘点"),
    "bento": ("便当盒网格 · Bento Grid", "开头自动生成“本期速览”格子盒，适合周报、发布会总结、参数汇总"),
}
DEFAULT_THEME = "lime"


def get_builder(theme: str):
    if theme not in THEMES:
        raise KeyError(theme)
    return import_module(f"{__name__}.{theme}").build_html
