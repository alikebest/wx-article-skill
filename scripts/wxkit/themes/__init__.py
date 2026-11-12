"""排版主题注册表。新增主题：写一个模块，提供 NAME 和 build_html(md_body) -> (html, img_srcs)，再登记到 THEMES。

neu / flat / minimal / bento / match / term / editorial / blueprint / pixel 共用 _engine.py（主题类 + 样式注入），写新主题时也可以照着它们来。
公众号会删掉空元素，get_builder 统一给空的 <span style>/<section style> 装饰补占位（render.keep_empty_decor），
主题里照常写空元素即可。
"""

from importlib import import_module

from .. import render

# 主题 id → (显示名, 适合的内容)
THEMES = {
    "lime": ("荧光柠绿 · 新粗野主义", "黑白高对比、粗描边硬阴影，适合 AI 工具、独立开发、效率工具、科技资讯"),
    "pink": ("樱花粉 · 荧光笔", "柔和手账风、荧光笔划重点，适合数码好物、轻松科技话题、生活类内容"),
    "neu": ("新拟态 · Neumorphism", "同色浮雕、一个强调蓝，适合数码硬件评测、参数对比；深色模式下浮雕感会消失"),
    "flat": ("扁平化 · Flat Design", "纯色块、零阴影零渐变、四色撞色，适合日更资讯，深色模式最稳"),
    "minimal": ("夸张极简 · Exaggerated Minimalism", "超大字号、大量留白、一个橙红强调色，适合观点、深度解读、年度盘点"),
    "bento": ("便当盒网格 · Bento Grid", "开头自动生成“本期速览”格子盒，适合周报、发布会总结、参数汇总"),
    "match": ("赛事战报 · 运动风", "黑黄红高对比、斜切色块、计分板，适合电竞、体育、发布会对决、A vs B 对比"),
    "term": ("终端 · 命令行", "白底墨绿提示符、终端窗口代码块、日志式提示卡，适合配置教程、命令行工具、独立开发"),
    "editorial": ("编辑部 · 杂志社论", "衬线标题、罗马数字章节、首字下沉、拉页金句、三线表，适合深度长文、人物故事"),
    "blueprint": ("蓝图 · 工程图纸", "浅蓝网格底、标题栏小标题、尺寸线分割，适合硬件拆解、原理图解、架构讲解"),
    "pixel": ("像素 · 8-bit", "像素缺角边框、像素爱心和箭头、血条分割线，适合游戏内容、轻松的科技八卦"),
}
DEFAULT_THEME = "lime"


def get_builder(theme: str):
    if theme not in THEMES:
        raise KeyError(theme)
    build = import_module(f"{__name__}.{theme}").build_html

    def build_html(md_body: str):
        html, imgs = build(md_body)
        return render.keep_empty_decor(html), imgs  # 空装饰元素会被公众号删掉，统一补占位
    return build_html
