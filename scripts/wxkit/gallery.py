"""模板列表页：所有排版主题的风格、特点、适合类型，每套配一份同一篇示例文章的实时预览。

预览用的是推送时同一套主题代码（themes.get_builder），所以永远和当前主题一致；每次运行都重新生成。
新增主题时在 THEME_INFO 里补一条（测试会检查有没有漏）。
"""

import base64
import html
import tempfile
from datetime import datetime
from pathlib import Path

from .themes import DEFAULT_THEME, THEMES, get_builder

# 主题 id → 风格（一句话）、特点（识别符号）、适合的内容、注意事项（可空）
THEME_INFO = {
    "lime": {
        "style": "新粗野主义：黑白高对比，柠绿 / 电紫点缀，粗黑描边 + 不模糊的硬阴影 + 零圆角",
        "features": ["小标题：黑底柠绿编号块 + 粗黑下划线", "加粗整块柠绿底，斜体加电紫下划线",
                     "导语、提示卡：白底粗黑框 + 硬阴影", "列表柠绿方块；分割线中间一颗柠绿菱形"],
        "fit": ["AI 工具", "独立开发", "效率工具", "科技资讯"],
        "note": "",
    },
    "pink": {
        "style": "柔和手账风：粉色荧光笔划重点，浅粉、浅紫圆角卡片",
        "features": ["小标题：荧光笔划线 + 粉色序号", "加粗粉色，斜体是荧光笔划线",
                     "导语、引用、提示卡都是浅色圆角卡", "列表粉色圆点；分割线三个粉点；图注前加 ▲"],
        "fit": ["数码好物", "轻松科技话题", "生活类内容"],
        "note": "",
    },
    "neu": {
        "style": "新拟态：整篇冷灰底，元素与底同色，只靠明暗两道阴影做出凸起和凹陷，一个强调蓝",
        "features": ["小标题：凸起的圆形序号 01", "导语、提示卡凸起，引用凹陷",
                     "单独成段的图片放进凸起外框", "数据列表 → 凸起数据圆盘"],
        "fit": ["数码硬件评测", "参数对比"],
        "note": "深色模式下浮雕感会消失",
    },
    "flat": {
        "style": "扁平化：白底，纯色块、零阴影零渐变、直角，蓝 / 珊瑚 / 青绿 / 明黄四色撞色；深色模式下最稳",
        "features": ["小标题：纯色方块序号，按章节轮换颜色", "斜体是蓝底白字反白",
                     "信息块纯色浅底，无描边无阴影", "数据列表 → 纯色数据磁贴；分割线三色小方块"],
        "fit": ["日更资讯", "快讯"],
        "note": "",
    },
    "minimal": {
        "style": "夸张极简：米白底，超大序号、超大数字、大量留白，只用一个橙红强调色",
        "features": ["小标题：72px 橙红序号单独一行", "短引用 → 26px 大号金句",
                     "单独成段的「但是。」→ 超大关键词转场", "数据列表 → 96px 超大数字；FIG.01 编号图注"],
        "fit": ["观点", "深度解读", "年度盘点"],
        "note": "一篇只讲一件大事，最好 3~4 节；不适合快讯、参数汇总",
    },
    "bento": {
        "style": "便当盒网格：浅灰盒子装白格子，统一间距和圆角，开头自动生成本期速览",
        "features": ["导语后自动生成「本期速览」格子盒", "小标题：浅灰圆角格 + 蓝色大号序号",
                     "导语、引用、提示卡都是圆角格子", "数据列表 → 一行数据格"],
        "fit": ["周报", "发布会总结", "参数汇总"],
        "note": "小标题超过 12 个字，在速览格里会折成好几行",
    },
    "match": {
        "style": "赛事战报 · 运动风：黑、电光黄、信号红高对比，斜切色块 + 粗黑底线，像直播计分板",
        "features": ["小标题：斜切黑块「ROUND 01」+ 粗黑底线", "加粗信号红，斜体黑底黄字",
                     "数据列表 → 黑色计分板，正好 2 项时中间加 VS", "分割线黄黑警示条；表头黑底白字"],
        "fit": ["电竞", "体育", "发布会对决", "A vs B 对比"],
        "note": "斜切、警示条被公众号过滤时退成直角色块、纯黄条",
    },
    "term": {
        "style": "终端 · 命令行：白底，墨绿提示符、琥珀色警告，等宽字体点缀英文数字",
        "features": ["小标题：注释行「# 01」+「$ 标题」", "提示卡是「[INFO]」「[WARN]」日志行",
                     "代码块是带三个圆点标题栏的终端窗口", "列表绿色「-」「[1]」"],
        "fit": ["配置教程", "命令行工具", "独立开发"],
        "note": "",
    },
    "editorial": {
        "style": "编辑部 · 杂志社论：暖白纸色底，衬线标题、细线与双线，像纸质杂志里的长文",
        "features": ["小标题：双细线 + 红色罗马数字 + 居中衬线标题", "导语首字下沉",
                     "短引用 → 居中拉页金句", "三线表；「图 1」红色图号"],
        "fit": ["深度长文", "行业 / 人物故事", "年度回顾"],
        "note": "没有中文衬线字体的安卓手机上标题退回黑体；首字下沉被过滤时退成段首大字",
    },
    "blueprint": {
        "style": "蓝图 · 工程图纸：浅蓝网格底 + 内外两道图框，细蓝线、等宽英文标注",
        "features": ["小标题像图纸标题栏：蓝底「SEC 01」格", "图片加蓝色细框 +「FIG.01 —」图注",
                     "分割线是带箭头的尺寸线", "数据列表 → 蓝框参数格"],
        "fit": ["硬件拆解", "原理图解", "架构 / 流程讲解"],
        "note": "网格背景被公众号过滤时退成纯白底",
    },
    "pixel": {
        "style": "像素 · 8-bit：缺角像素边框，红黄蓝三色，像一款复古小游戏",
        "features": ["小标题：黄色像素标签「STAGE 01」", "列表是像素爱心，小标题前是像素箭头",
                     "导语是像素对话框；图片放进像素相框", "分割线是一条血条 HP"],
        "fit": ["游戏内容", "轻松科技八卦"],
        "note": "不适合严肃话题",
    },
}

SAMPLE_TITLE = "同一篇示例文章，换一套主题"
SAMPLE_IMG = "sample-figure.png"  # 渲染后换成内嵌的示意图（mistune 会拦掉 svg 的 data: 地址）
SAMPLE = f"""这是导语。排版主题只改样式、不改内容，同一篇文章换一套主题，就是另一种气质。

导语可以有 1~3 段，会排成每套主题自己的导语卡。

## 一、先说结论

正文里可以有**加粗的重点词**，也可以有*一句强调的话*，还有 `行内代码`。

- **30h** 综合续航
- **35dB** 降噪深度
- **¥999** 首发价格

### 小节标题

- 无序列表第一项，这一项写得长一点，看看折行之后续行是不是和首行文字对齐
- 无序列表第二项

1. 打开设置
2. 找到「通用」，进入「高级选项」
3. 打开开关

> 💡 技巧卡片：适合放一句实用的小技巧。

> ⚠️ 避坑卡片：适合放风险和容易踩的坑。

## 二、对比和引用

| 项目 | 方案 A | 方案 B |
|---|---|---|
| 价格 | 999 元 | 1299 元 |
| 续航 | 30 小时 | 24 小时 |

> 好的排版，是让读者感觉不到排版。

![示意图：图片下方会显示这行说明]({SAMPLE_IMG})

---

```
python wxflow.py gallery
```

最后一段正文，文章到这里结束。
"""

FIGURE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420">
<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#C9DCF5"/><stop offset="1" stop-color="#EEF3FA"/></linearGradient></defs>
<rect width="900" height="420" fill="url(#g)"/><circle cx="690" cy="120" r="54" fill="#FFD27A"/>
<path d="M0 330 L210 170 L360 280 L520 140 L900 360 L900 420 L0 420 Z" fill="#7C9CC9"/>
<path d="M0 380 L260 260 L470 350 L650 250 L900 390 L900 420 L0 420 Z" fill="#4E6FA3"/></svg>"""

PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>模板列表 · 公众号排版主题</title>
<style>
  :root {{ --bg:#F2F2F5; --card:#FFFFFF; --ink:#1D1D1F; --muted:#6E6E73; --line:#E3E3E8; --chip:#F5F5F7;
          --accent:#3B5BDB; --accent-bg:#E8EEFF; --note:#9A5B00; --note-bg:#FFF5E0; --stage:#E9E9ED; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#141416; --card:#1F1F23; --ink:#F2F2F5; --muted:#A1A1A8; --line:#34343A; --chip:#2A2A30;
            --accent:#8EA6FF; --accent-bg:#2A3256; --note:#F3C06B; --note-bg:#3A2E17; --stage:#2A2A30; }}
  }}
  * {{ box-sizing:border-box; }}
  html, body {{ margin:0; background:var(--bg); color:var(--ink); }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif; }}
  header {{ padding:28px 24px 8px; }}
  header h1 {{ margin:0 0 6px; font-size:24px; }}
  header p {{ margin:0; color:var(--muted); font-size:14px; line-height:1.7; }}
  header code {{ background:var(--chip); padding:1px 6px; border-radius:4px; font-size:13px; }}
  nav {{ display:flex; flex-wrap:wrap; gap:8px; padding:14px 24px 4px; }}
  nav a {{ text-decoration:none; color:var(--ink); background:var(--card); border:1px solid var(--line);
          border-radius:999px; padding:4px 12px; font-size:13px; }}
  nav a:hover {{ border-color:var(--accent); color:var(--accent); }}
  nav a b {{ font-family:Menlo,Consolas,monospace; font-weight:600; margin-right:4px; }}
  main {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(min(100%, 420px), 1fr));
         gap:20px; padding:16px 24px 48px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; overflow:hidden;
          display:flex; flex-direction:column; scroll-margin-top:16px; }}
  .info {{ flex:1; padding:18px 20px 16px; }}
  .id-row {{ display:flex; align-items:center; gap:8px; margin-bottom:4px; }}
  .id {{ font-family:Menlo,Consolas,monospace; font-size:13px; font-weight:600; color:var(--accent);
        background:var(--accent-bg); padding:2px 8px; border-radius:6px; }}
  .badge {{ font-size:11px; font-weight:600; color:#FFFFFF; background:var(--accent); padding:2px 7px; border-radius:6px; }}
  .info h2 {{ margin:6px 0 6px; font-size:18px; line-height:1.4; }}
  .style {{ margin:0 0 12px; color:var(--muted); font-size:13.5px; line-height:1.7; }}
  .label {{ font-size:12px; font-weight:600; color:var(--muted); margin:0 0 6px; letter-spacing:.5px; }}
  .features {{ margin:0 0 12px; padding-left:18px; font-size:13.5px; line-height:1.75; }}
  .tags {{ display:flex; flex-wrap:wrap; gap:6px; margin:0 0 4px; }}
  .tag {{ font-size:12.5px; background:var(--chip); border-radius:6px; padding:3px 9px; }}
  .note {{ margin:12px 0 0; font-size:12.5px; line-height:1.6; color:var(--note); background:var(--note-bg);
          border-radius:8px; padding:7px 10px; }}
  .stage {{ background:var(--stage); padding:20px 0 0; position:relative; }}
  .stage.collapsed .phone-clip {{ max-height:620px; overflow:hidden; }}
  .stage.collapsed::after {{ content:""; position:absolute; left:0; right:0; bottom:52px; height:90px;
                            background:linear-gradient(transparent, var(--stage)); pointer-events:none; }}
  .phone {{ width:375px; max-width:calc(100% - 24px); margin:0 auto; background:#FFFFFF; color:#1F1F1F;
           border-radius:14px 14px 0 0; box-shadow:0 2px 16px rgba(0,0,0,.08); }}
  .stage:not(.collapsed) .phone {{ border-radius:14px; }}
  /* 以下与预览页（preview.py）一致，保证渲染效果相同 */
  .article {{ padding:22px 16px 40px; overflow-wrap:break-word; }}
  .a-title {{ font-size:22px; font-weight:bold; line-height:1.4; margin:0 0 14px; }}
  .a-meta {{ font-size:15px; color:rgba(0,0,0,.3); margin-bottom:22px; }}
  .a-meta span {{ color:#576B95; margin-right:8px; }}
  .toggle {{ display:block; width:100%; height:52px; border:0; border-top:1px solid var(--line); background:var(--card);
            color:var(--accent); font-size:14px; cursor:pointer; position:relative; z-index:1; }}
  .toggle:hover {{ background:var(--chip); }}
  footer {{ padding:0 24px 32px; color:var(--muted); font-size:12px; }}
  @media (max-width:480px) {{
    header, nav, main, footer {{ padding-left:16px; padding-right:16px; }}
  }}
</style>
</head>
<body>
<header>
  <h1>模板列表</h1>
  <p>共 {count} 套排版主题。在文章头信息里写 <code>theme: 主题名</code>（如 <code>theme: match</code>），或者对 Claude 说「用 xx 主题排版」。
  下面每套主题的预览都是同一篇示例文章，和推送用的是同一套排版代码。</p>
</header>
<nav>{nav}</nav>
<main>
{cards}
</main>
<footer>生成于 {now}。手机宽度 375px 模拟，示例图片是示意，最终效果以公众号后台的预览为准。</footer>
<script>
  document.querySelectorAll(".toggle").forEach(function (btn) {{
    btn.addEventListener("click", function () {{
      var stage = btn.closest(".stage");
      var collapsed = stage.classList.toggle("collapsed");
      btn.textContent = collapsed ? "展开完整预览" : "收起预览";
      if (collapsed) stage.closest(".card").scrollIntoView({{ block: "nearest" }});
    }});
  }});
</script>
</body>
</html>
"""


def _e(s: str) -> str:
    return html.escape(s, quote=True)


def _card(theme: str, figure_uri: str) -> str:
    name = THEMES[theme][0]
    info = THEME_INFO[theme]
    body = get_builder(theme)(SAMPLE)[0].replace(f'src="{SAMPLE_IMG}"', f'src="{figure_uri}"')
    badge = '<span class="badge">默认</span>' if theme == DEFAULT_THEME else ""
    features = "".join(f"<li>{_e(f)}</li>" for f in info["features"])
    tags = "".join(f'<span class="tag">{_e(t)}</span>' for t in info["fit"])
    note = f'<p class="note">注意：{_e(info["note"])}</p>' if info["note"] else ""
    return f"""<section class="card" id="{theme}">
  <div class="info">
    <div class="id-row"><span class="id">{theme}</span>{badge}</div>
    <h2>{_e(name)}</h2>
    <p class="style">{_e(info["style"])}</p>
    <p class="label">特点</p>
    <ul class="features">{features}</ul>
    <p class="label">适合</p>
    <div class="tags">{tags}</div>
    {note}
  </div>
  <div class="stage collapsed">
    <div class="phone-clip"><div class="phone"><div class="article">
      <h1 class="a-title">{_e(SAMPLE_TITLE)}</h1>
      <div class="a-meta"><span>示例作者</span>{datetime.now():%Y年%m月%d日}</div>
      {body}
    </div></div></div>
    <button class="toggle" type="button">展开完整预览</button>
  </div>
</section>"""


def default_path() -> Path:
    return Path(tempfile.gettempdir()) / "wx-article" / "模板列表.html"


def build(out: Path | None = None) -> Path:
    """生成模板列表页，返回路径。"""
    missing = [t for t in THEMES if t not in THEME_INFO]
    if missing:
        raise KeyError(f"THEME_INFO 里缺少主题说明：{', '.join(missing)}")
    out = Path(out) if out else default_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    figure_uri = "data:image/svg+xml;base64," + base64.b64encode(FIGURE_SVG.encode("utf-8")).decode("ascii")
    nav = "".join(f'<a href="#{t}"><b>{t}</b>{_e(THEMES[t][0].split(" · ")[0])}</a>' for t in THEMES)
    page = PAGE.format(count=len(THEMES), nav=nav, now=f"{datetime.now():%Y-%m-%d %H:%M}",
                       cards="\n".join(_card(t, figure_uri) for t in THEMES))
    out.write_text(page, encoding="utf-8")
    return out
