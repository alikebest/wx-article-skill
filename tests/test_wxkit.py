# -*- coding: utf-8 -*-
"""本地回归测试，不调用微信接口、不消耗配额。运行：python tests/test_wxkit.py"""

import base64
import json
import os
import re
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import requests  # noqa: E402

from datetime import date  # noqa: E402

from wxkit import check, config, frontmatter, preview, push, wechat, workspace  # noqa: E402
from wxkit.naming import step_output  # noqa: E402
from wxkit.themes import get_builder  # noqa: E402
from wxkit.wechat import WeChat, WeChatError, truncate_units, wx_units  # noqa: E402

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
SECRET = "SECRET_should_never_leak_123"

# 测试一律使用临时配置文件，不读用户真实的配置和环境变量
_TMP = Path(tempfile.mkdtemp(prefix="wxkit-test-"))
CFG = _TMP / "config.json"
os.environ["WX_ARTICLE_CONFIG"] = str(CFG)
for _k in ("WX_APPID", "WX_SECRET", "WX_AUTHOR", "WX_ARTICLE_DIR"):
    os.environ.pop(_k, None)


def _set_config(data):
    """data 为 None 时删除配置文件。"""
    if data is None:
        CFG.unlink(missing_ok=True)
    else:
        CFG.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


TWO_ACCOUNTS = {"default": "main", "accounts": {
    "main": {"appid": "wx_main", "secret": SECRET, "author": "主号作者"},
    "life": {"appid": "wx_life", "secret": SECRET + "_life", "author": "生活号"},
}}


# ---------------------------------------------------------------------------
# 微信接口客户端
# ---------------------------------------------------------------------------

class FakeResp:
    def __init__(self, payload, status=200):
        self.content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.status_code = status


class FakeSess:
    def __init__(self, payloads):
        self.calls, self.payloads, self.headers = [], list(payloads), {}

    def request(self, method, url, **kw):
        self.calls.append((method, url, kw))
        p = self.payloads.pop(0)
        if isinstance(p, Exception):
            raise p
        return FakeResp(p)


def _wx(payloads):
    wx = WeChat("APPID", SECRET, session=FakeSess(payloads))
    wx.token = "TOKEN"
    return wx


def test_utf8_body():
    wx = _wx([{"media_id": "OK"}])
    assert wx.add_draft({"title": "中文标题测试", "digest": "摘要"}) == "OK"
    _, _, kw = wx.sess.calls[0]
    assert b"\\u" not in kw["data"], "请求体里不应有 \\u 转义"
    assert "中文标题测试".encode("utf-8") in kw["data"]
    assert kw["headers"]["Content-Type"] == "application/json; charset=utf-8"


def test_response_decode_and_hint():
    wx = _wx([{"errcode": 40164, "errmsg": "中文错误信息"}])
    try:
        wx._post("/fake")
        raise AssertionError("应该抛出异常")
    except WeChatError as e:
        assert "中文错误信息" in str(e) and "白名单" in str(e) and e.errcode == 40164


def test_retry_on_overlong():
    wx = _wx([{"errcode": 45110, "errmsg": "author size out of limit"}, {"media_id": "RETRY_OK"}])
    assert wx.add_draft({"title": "t", "author": "示例作者超长名字", "digest": "d"}) == "RETRY_OK"
    sent = json.loads(wx.sess.calls[1][2]["data"])
    assert wx_units(sent["articles"][0]["author"]) <= 16


def test_no_retry_on_other_error():
    wx = _wx([{"errcode": 45009, "errmsg": "quota"}])
    try:
        wx.add_draft({"title": "t", "author": "a", "digest": "d"})
        raise AssertionError("应该抛出异常")
    except WeChatError as e:
        assert "45009" in str(e) and len(wx.sess.calls) == 1


def test_truncate():
    assert truncate_units("题" * 30, 128) == "题" * 21
    assert wx_units("题") == 6 and wx_units("t") == 1 and wx_units("🎉") == 12


def test_secret_not_leaked_on_network_error():
    # 模拟 requests 的真实行为：异常信息里带着含 secret 的完整地址
    err = requests.ConnectionError(f"Max retries exceeded with url: /cgi-bin/token?secret={SECRET}")
    wx = WeChat("APPID", SECRET, session=FakeSess([err]))
    try:
        wx.get_token()
        raise AssertionError("应该抛出异常")
    except WeChatError as e:
        dump = "".join(traceback.format_exception(e))
        assert SECRET not in str(e) and SECRET not in dump, "报错和堆栈里都不能出现 secret"
        assert "ConnectionError" in str(e)
    assert SECRET not in repr(wx)


def test_secret_not_leaked_real_requests():
    # 用真实的 requests 连一个不存在的端口，复现原脚本泄露 secret 的场景
    old = wechat.API_BASE
    wechat.API_BASE = "http://127.0.0.1:1"
    try:
        WeChat("APPID", SECRET).get_token()
        raise AssertionError("应该抛出异常")
    except WeChatError as e:
        assert SECRET not in "".join(traceback.format_exception(e))
    finally:
        wechat.API_BASE = old


# ---------------------------------------------------------------------------
# 排版
# ---------------------------------------------------------------------------

def _render(md, theme="lime"):
    return re.sub(r' style="[^"]*"', "", get_builder(theme)(md)[0])


def test_cjk_emphasis():
    assert "<strong>“能看到”和“会怎么用”</strong>。" in _render("而是**“能看到”和“会怎么用”**。")
    assert "<strong>“好”</strong>就走" in _render("他说**“好”**就走")
    assert "<em>“观点”</em>也行" in _render("是*“观点”*也行")
    assert "<code>x**“y”**z</code>" in _render("代码 `x**“y”**z` 不动")
    assert "转义 **保留**" in _render("转义 \\*\\*保留\\*\\*")
    assert "2*3=6" in _render("算式 2*3=6")
    assert "⸱" not in _render("而是**“能看到”**。")


def test_pink_theme():
    html = get_builder("pink")(
        "导语。\n\n## 一、**甲**\n\n正文\n\n## 乙\n\n"
        "> 💡 技巧\n\n> ⚠️\n>\n> 注意事项\n\n### 小节\n\n- 项"
    )[0]
    assert "<blockquote" not in html, "引用块应输出为 section"
    assert "写在前面" in html and "小贴士" in html and ">注意<" in html
    assert "💡" not in html and "⚠" not in html
    assert '<strong style="font-weight:bold;">甲</strong>' in html, "小标题里的加粗不应变粉"
    assert ">01</span>" in html and ">02</span>" in html and "一、" not in html
    assert html.count("<p") == html.count("</p>")


ENGINE_THEMES = ("neu", "flat", "minimal", "bento", "match", "term", "editorial", "blueprint", "pixel")
THEME_SAMPLE = (
    "导语。\n\n## 一、**甲**\n\n正文 *重点*\n\n![图注](a.png)\n\n## 乙\n\n"
    "> 💡 技巧\n\n> ⚠️\n>\n> 注意事项\n\n### 小节\n\n- 项\n\n1. 步\n\n---\n\n"
    "## 附：链接\n\n| a | b |\n|:-:|--|\n| 1 | 2 |"
)


def test_engine_themes():
    from wxkit.themes import THEMES
    for name in ENGINE_THEMES:
        assert name in THEMES, name
        html, imgs = get_builder(name)(THEME_SAMPLE)
        assert imgs == ["a.png"], name
        assert "<blockquote" not in html, f"{name}: 引用块应输出为 section"
        assert "data-" not in html, f"{name}: 结构标注属性不应漏到输出里"
        assert "小贴士" in html and ">注意<" in html, name
        assert "💡" not in html and "⚠" not in html, f"{name}: 提示卡开头的符号应由小标题代替"
        assert "一、" not in html and "<strong" in html, name
        assert "图注" in html and "text-align:center" in html, f"{name}: 图注、表格列对齐"
        assert "<h2 style=" in html and "<h3 style=" in html, name
        for tag in ("p", "section", "h2", "span"):
            assert html.count(f"<{tag}") == html.count(f"</{tag}>"), f"{name}: <{tag}> 未配对"
        if name != "minimal":
            assert "写在前面" in html, name
        assert "<script" not in _render("<script>x</script>\n\n[x](javascript:alert(1))", name), name
    flat = get_builder("flat")(THEME_SAMPLE)[0]
    assert "box-shadow" not in flat and "gradient" not in flat, "扁平化不能有阴影和渐变"


def test_no_empty_decor():
    from wxkit.themes import THEMES
    for name in THEMES:
        html = get_builder(name)(THEME_SAMPLE + "\n\n- 列表项\n  - 嵌套项")[0]
        empty = re.findall(r"<(span|section)\b[^>]*></\1>", html)
        assert not empty, f"{name}: 空元素会被公众号删掉（列表符号消失、折行缩进错位）"


def test_gallery():
    import tempfile
    from wxkit import gallery
    from wxkit.themes import THEMES
    assert set(gallery.THEME_INFO) == set(THEMES), "模板列表的主题说明要和 THEMES 一一对应"
    with tempfile.TemporaryDirectory() as d:
        out = gallery.build(Path(d) / "模板列表.html")
        page = out.read_text(encoding="utf-8")
    assert page.count('class="card"') == len(THEMES)
    for t in THEMES:
        assert f'id="{t}"' in page and f'href="#{t}"' in page, t
    assert gallery.SAMPLE_IMG not in page and "data:image/svg+xml;base64," in page, "示例图要换成内嵌示意图"


def test_stats_lists():
    from wxkit import render
    from wxkit.themes import _engine

    class Rec(_engine.Theme):
        def stats(self, items):
            self.got = items
            return "<section>STATS</section>"

    def stats_of(text):
        t = Rec()
        t.got = None
        _engine.find_stats(render.markdown_to_html(text), t)
        return t.got

    assert stats_of("- **30h** 续航\n- **+35%** 夜景") == [("30h", "续航"), ("+35%", "夜景")]
    assert stats_of("- **30h** 续航\n\n- **2** 个") == [("30h", "续航"), ("2", "个")], "宽松列表也认"
    assert stats_of("- **3倍**") == [("3倍", "")]
    for normal in ("- **30h**：续航", "- **第1步** 打开设置", "- **甲** 乙",
                   "- **1** a\n- **2** b\n- **3** c\n- **4** d", "> - **30h** 续航",
                   "- 外层\n  - **30h** 续航", "- **30h** 这一条说明文字写得太长了超过十四个字",
                   "- **30h** 续航 `x`"):
        assert stats_of(normal) is None, f"不应识别为数据列表：{normal!r}"
    lime_html = get_builder("lime")("- **30h** 续航")[0]
    assert "30h" in lime_html and "续航" in lime_html, "lime / pink 里数据列表就是普通列表"


def test_bento_toc():
    def secs(n):
        return "导语。\n\n" + "".join(f"## 第{i}节 **x{i}**\n\n正文\n\n" for i in range(1, n + 1))

    bento = get_builder("bento")
    html = bento(secs(3))[0]
    assert "本期速览" in html and "IN THIS ISSUE · 03" in html and "flex:1.15" in html, "奇数节用左大右二"
    assert html.index("写在前面") < html.index("本期速览") < html.index("<h2"), "速览盒在导语之后、第一节之前"
    toc = html[html.index("本期速览"):html.index("<h2")]
    assert "第1节 x1" in toc and "<strong" not in toc, "速览格只放标题纯文本"
    assert "flex:1.15" not in bento(secs(4))[0], "偶数节两两并排"
    assert "本期速览" not in bento(secs(1))[0], "不足 2 节不生成"


def test_minimal_blocks():
    mini = get_builder("minimal")
    html = mini("> 手机*本身*。\n>\n> —— 某发布会\n\n但是。\n\n- 但是。\n\n正文\n\n- **3倍** 速度")[0]
    assert "font-size:26px" in html and "background:#FF4A1C" in html, "短引用 → 大号金句，斜体反白"
    assert "font-size:11px" in html and "—— 某发布会" in html, "“——”开头的最后一段是出处"
    assert html.count("font-size:64px") == 1, "只有顶层单独成段的“但是。”变成转场"
    assert "font-size:96px" in html, "单项数据列表 → 超大数据"
    long_quote = mini("> " + "很长的引用。" * 12)[0]
    assert "font-size:26px" not in long_quote and "font-size:17px" in long_quote, "长引用不做金句"


def test_html_is_escaped():
    html = _render("<script>alert(1)</script>\n\n[x](javascript:alert(1))")
    assert "<script" not in html and "javascript:" not in html


# ---------------------------------------------------------------------------
# front matter 与命名
# ---------------------------------------------------------------------------

def test_frontmatter():
    meta, body = frontmatter.split("﻿---\r\ntitle: 标题\r\nauthor: 这里写作者\r\n"
                                   "source_url: https://a.com/x?a=1\r\ncover:\r\n---\r\n正文\r\n")
    assert meta == {"title": "标题", "source_url": "https://a.com/x?a=1"}, meta
    assert body == "正文\n"
    assert frontmatter.split("---\n---\n正文") == ({}, "正文")
    assert frontmatter.split("没有头信息")[0] == {}
    text = frontmatter.dump({"theme": "pink", "x": "1", "title": "T\n换行"}, "\n\n正文")
    assert text == "---\ntitle: T 换行\ntheme: pink\nx: 1\n---\n\n正文", text
    assert frontmatter.split(text)[0] == {"title": "T 换行", "theme": "pink", "x": "1"}


def test_step_output():
    d = Path("d")
    assert step_output(d / "article.md", "rewrite") == d / "article.rewrite.md"
    assert step_output(d / "article.rewrite.md", "layout") == d / "article.layout.md"
    assert step_output(d / "a.polish.layout.md", "push") == d / "a.push.md"
    assert step_output(d / "v1.2.md", "layout") == d / "v1.2.layout.md"
    assert step_output(d / "layout.md", "push") == d / "layout.push.md"


# ---------------------------------------------------------------------------
# 检查、预览、推送
# ---------------------------------------------------------------------------

def _article(tmp: Path, fm: str, body: str = "## 小节一\n\n正文\n\n## 小节二\n\n正文", name="a.md"):
    p = tmp / name
    p.write_text(f"---\n{fm}\n---\n\n{body}\n", encoding="utf-8")
    return p


def test_check_cover_rules():
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        assert any("没有封面" in m for m in check.inspect(_article(t, "title: T")).errors)
        (t / "c.webp").write_bytes(PNG_1PX)
        assert any("webp" in m for m in check.inspect(_article(t, "title: T\ncover: c.webp")).errors)
        assert any("不存在" in m for m in check.inspect(_article(t, "title: T\ncover: nope.png")).errors)
        (t / "c.png").write_bytes(PNG_1PX)
        r = check.inspect(_article(t, "title: T\ncover: c.png"))
        assert r.ok and r.cover == t / "c.png", r.errors
        assert check.inspect(_article(t, "title: T\nthumb_media_id: MID")).ok


def test_check_title_theme_images():
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "c.png").write_bytes(PNG_1PX)
        (t / "图 片").mkdir()
        (t / "图 片" / "一 张.png").write_bytes(PNG_1PX)
        body = ("# 正文标题\n\n![说明](<图 片/一 张.png>)\n\n![](http://x.com/a.png)\n\n"
                "![](images/missing.png)\n\n<div>残留</div>\n\n## 附：备选标题\n\n- x")
        r = check.inspect(_article(t, "cover: c.png\ntheme: PINK", body))
        assert r.title == "正文标题" and r.theme == "pink" and r.ok, r.errors
        assert "正文标题</h1>" not in r.html, "与标题相同的 H1 应去掉"
        status = {i.status for i in r.images}
        assert status == {"local", "remote", "missing"}, r.images
        joined = " ".join(r.warnings)
        assert "外链" in joined and "裂图" in joined and "HTML" in joined and "备选标题" in joined
        assert not check.inspect(_article(t, "title: T\ncover: c.png\ntheme: blue")).ok
        long = check.inspect(_article(t, f"title: {'长' * 70}\ncover: c.png\ndigest: {'摘' * 130}"))
        assert len(long.title) == 64 and len(long.digest) == 120 and long.ok


def test_preview():
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "c.png").write_bytes(PNG_1PX)
        (t / "images").mkdir()
        (t / "images" / "x.png").write_bytes(PNG_1PX)
        md = _article(t, "title: 预览<测试>\ncover: c.png", "导语\n\n## 一\n\n![图](images/x.png)\n\n## 二\n\n正文",
                      name="a.layout.md")
        out = preview.build(check.inspect(md))
        assert out == t / "a.layout.html"
        page = out.read_text(encoding="utf-8")
        assert preview.MARKER in page and 'src="images/x.png"' in page and 'src="c.png"' in page
        assert "预览&lt;测试&gt;" in page and "<测试>" not in page, "标题要转义"
        preview.build(check.inspect(md))  # 自己生成的预览页可以覆盖
        (t / "b.html").write_text("<html>用户自己的页面</html>", encoding="utf-8")
        try:
            preview.build(check.inspect(_article(t, "title: T", name="b.md")))
            raise AssertionError("不应覆盖用户自己的 HTML")
        except FileExistsError:
            pass


class FakeWx:
    def __init__(self):
        self.calls = []

    def upload_content_image(self, p):
        self.calls.append(("img", p.name))
        return f"https://mmbiz.example/{p.name}"

    def upload_content_gif(self, p):
        return self.upload_content_image(p)

    def upload_permanent_image(self, p):
        self.calls.append(("cover", p.name))
        return "THUMB"

    def add_draft(self, article):
        self.calls.append(("draft", article))
        return "MEDIA"


def test_push_flow():
    _set_config(TWO_ACCOUNTS)
    try:
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "c.png").write_bytes(PNG_1PX)
            (t / "x.png").write_bytes(PNG_1PX)
            md = _article(t, "title: 推送\ncover: c.png", "## 一\n\n![](x.png)\n\n## 二\n\n![](x.png)",
                          name="a.layout.md")
            wx = FakeWx()
            info = push.push_one(md, wx)
            assert info["media_id"] == "MEDIA" and info["account"] == "main"
            kinds = [c[0] for c in wx.calls]
            assert kinds == ["img", "cover", "draft"], kinds  # 同一张图只传一次
            draft = wx.calls[-1][1]
            assert draft["author"] == "主号作者" and draft["thumb_media_id"] == "THUMB"
            assert 'src="https://mmbiz.example/x.png"' in draft["content"] and 'src="x.png"' not in draft["content"]
            record = t / "a.push.md"
            assert info["record"] == record
            info2 = push.push_one(md, FakeWx(), "life")
            assert info2["account"] == "life"
            text = record.read_text(encoding="utf-8")
            assert text.count("# 推送记录") == 1 and text.count("- 草稿 media_id") == 2
            assert "- 账号：main" in text and "- 账号：life" in text

            bad = _article(t, "title: 无封面", name="bad.md")
            wx = FakeWx()
            assert push.push_one(bad, wx) is None and wx.calls == [], "检查不通过时不能调用任何接口"
    finally:
        _set_config(None)


def test_check_account_rules():
    _set_config(TWO_ACCOUNTS)
    try:
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "c.png").write_bytes(PNG_1PX)
            r = check.inspect(_article(t, "title: T\ncover: c.png\naccount: life"))
            assert r.ok and r.account == "life" and r.author == "生活号", r.errors
            assert check.inspect(_article(t, "title: T\ncover: c.png\naccount: life"), "main").account == "main"
            assert any("nope" in m for m in check.inspect(_article(t, "title: T\ncover: c.png\naccount: nope")).errors)

            # 推送记录显示 THUMB1 是 main 上传的：用在 life 要报错，用在 main 没问题
            (t / "a.push.md").write_text(
                "# 推送记录：T\n\n## 2026-11-04 10:00:00\n\n- 文件：`a.md`\n- 账号：main\n"
                "- 封面 thumb_media_id：`THUMB1`\n", encoding="utf-8")
            r = check.inspect(_article(t, "title: T\nthumb_media_id: THUMB1\naccount: life"))
            assert any("main 上传" in m for m in r.errors), r.errors
            assert check.inspect(_article(t, "title: T\nthumb_media_id: THUMB1")).ok
            r = check.inspect(_article(t, "title: T\nthumb_media_id: OTHER"))
            assert r.ok and any("只在上传它的那个账号" in m for m in r.warnings), "多账号时提醒确认来源"
    finally:
        _set_config(None)


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

def _expect_config_error(fn, *needles):
    try:
        fn()
    except config.ConfigError as e:
        text = "".join(traceback.format_exception(e))
        assert SECRET not in text, "报错里不能出现密钥"
        for n in needles:
            assert n in str(e), (n, str(e))
        return
    raise AssertionError("应该抛出 ConfigError")


def test_config_init_and_template():
    _set_config(None)
    try:
        assert config.init() == (CFG, True) and config.init() == (CFG, False)
        assert config.load() == {"name": "main", "appid": "", "secret": "", "author": ""}, "模板占位文字应视为未填"
        _expect_config_error(config.require_credentials, "main", "appid", "secret")
        _set_config(None)
        assert config.load()["name"] == "" and config.select() == ""
        _expect_config_error(config.require_credentials, "config --init")
    finally:
        _set_config(None)


def test_config_accounts_and_select():
    _set_config(TWO_ACCOUNTS)
    try:
        assert config.select() == "main"
        assert config.select(article="life") == "life"
        assert config.select("main", "life") == "main", "命令行优先于文章头信息"
        _expect_config_error(lambda: config.select("nope"), "nope", "main", "life")
        assert config.require_credentials("life")["secret"] == SECRET + "_life"
        st = json.dumps(config.status(), ensure_ascii=False)
        assert SECRET not in st and "wx_main" not in st and "wx_life" not in st, "状态里不能出现密钥和 appid"
        assert "主号作者" in st and "生活号" in st

        # 旧的单账号写法视为 main
        _set_config({"appid": "wx1", "secret": SECRET, "author": "我"})
        assert config.select() == "main" and config.require_credentials()["author"] == "我"

        # 环境变量账号：没明确指定账号时优先用它，明确指定时不影响
        os.environ["WX_APPID"], os.environ["WX_SECRET"] = "wx_env", SECRET
        try:
            assert config.select() == "env" and config.load()["appid"] == "wx_env"
            assert config.select("main") == "main" and config.load("main")["appid"] == "wx1"
        finally:
            os.environ.pop("WX_APPID"), os.environ.pop("WX_SECRET")

        CFG.write_text("{ bad json " + SECRET, encoding="utf-8")
        _expect_config_error(config.load, "JSON")
    finally:
        _set_config(None)


def test_config_add_and_default():
    _set_config({"appid": "wx1", "secret": SECRET, "author": "我", "gemini_model": "保留我"})
    try:
        config.add_account("life")
        data = json.loads(CFG.read_text(encoding="utf-8"))
        assert data["default"] == "main" and data["gemini_model"] == "保留我", "其他字段要原样保留"
        assert data["accounts"]["main"] == {"appid": "wx1", "secret": SECRET, "author": "我"}, "原账号不能丢"
        assert config.load("life")["appid"] == "", "新账号是占位文字，视为未填"
        _expect_config_error(lambda: config.add_account("life"), "已经存在")
        _expect_config_error(lambda: config.add_account("env"), "保留")
        _expect_config_error(lambda: config.add_account("a b"), "账号名")
        config.set_default("life")
        assert config.select() == "life"
        _expect_config_error(lambda: config.set_default("nope"), "nope")
        _set_config(None)
        config.add_account("first")
        assert config.select() == "first", "第一个账号自动成为默认"
    finally:
        _set_config(None)


def test_config_articles_dir():
    _set_config(None)
    tmp = Path(tempfile.mkdtemp(prefix="wxkit-root-"))
    try:
        assert config.articles_dir() == (None, "")
        config.init()
        assert config.articles_dir() == (None, ""), "模板里的占位文字视为未配置"

        _set_config(TWO_ACCOUNTS)
        root = config.set_articles_dir(str(tmp / "文章"))
        assert root.is_absolute() and config.articles_dir() == (root, "配置文件")
        data = json.loads(CFG.read_text(encoding="utf-8"))
        assert data["accounts"] == TWO_ACCOUNTS["accounts"], "设置根目录不能动账号"
        config.add_account("third")
        assert config.articles_dir()[0] == root, "新增账号时根目录要保留"
        st = json.dumps(config.status(), ensure_ascii=False)
        assert str(root).replace("\\", "\\\\") in st and SECRET not in st

        os.environ["WX_ARTICLE_DIR"] = str(tmp / "env")
        try:
            assert config.articles_dir() == (tmp / "env", "环境变量")
            assert workspace.resolve_root(str(tmp / "cli"))[1] == "命令行"
        finally:
            os.environ.pop("WX_ARTICLE_DIR")

        _set_config({"articles_dir": "relative/path"})
        _expect_config_error(config.articles_dir, "绝对路径")
        (tmp / "f.txt").write_text("x")
        _expect_config_error(lambda: config.set_articles_dir(str(tmp / "f.txt")), "不是文件夹")

        _set_config(None)
        config.set_articles_dir(str(tmp))
        assert config.load()["name"] == "main", "配置文件不存在时先从模板生成"
    finally:
        _set_config(None)


# ---------------------------------------------------------------------------
# 文章文件夹：新建、抓取落点、列出
# ---------------------------------------------------------------------------

DAY = date(2026, 11, 12)


def test_workspace_numbering():
    root = Path(tempfile.mkdtemp(prefix="wxkit-ws-"))
    assert workspace.next_name(root / "不存在", DAY) == "2026-11-12-01"
    for n in ("2026-11-12-01", "2026-11-12-03", "2026-11-11-07", "2026-11-12_旧标题", "笔记"):
        (root / n).mkdir()
    assert workspace.next_name(root, DAY) == "2026-11-12-04", "取最大序号加 1，不按个数数"
    assert workspace.next_name(root, date(2026, 11, 11)) == "2026-11-11-08"
    assert workspace.next_name(root, date(2026, 11, 13)) == "2026-11-13-01"
    (root / "2026-11-12-04").write_text("同名文件")
    assert workspace.make_dir(root, DAY).name == "2026-11-12-05", "同名文件也要跳过"
    (root / "2026-11-12-99").mkdir()
    assert workspace.next_name(root, DAY) == "2026-11-12-100"


def test_workspace_new():
    root = Path(tempfile.mkdtemp(prefix="wxkit-ws-")) / "根目录不存在也能建"
    md = workspace.new_article(root, "我的标题", DAY)
    assert md == root / "2026-11-12-01" / "article.md"
    meta, body = frontmatter.split(md.read_text(encoding="utf-8"))
    assert meta == {"title": "我的标题"} and not body.strip(), (meta, body)
    md2 = workspace.new_article(root, day=DAY)
    assert md2.parent.name == "2026-11-12-02"
    assert frontmatter.split(md2.read_text(encoding="utf-8"))[0] == {}, "没给标题时是占位文字，视为未填"
    assert not workspace.has_body(md2)


def test_workspace_url_key():
    k = workspace.url_key
    assert k("https://mp.weixin.qq.com/s/AbC-1_x") == k("http://mp.weixin.qq.com/s/AbC-1_x?scene=1#rd")
    long1 = "https://mp.weixin.qq.com/s?__biz=MzA&mid=22&idx=1&sn=abc&chksm=111&scene=21#wechat_redirect"
    long2 = "https://mp.weixin.qq.com/s?__biz=MzA&mid=22&idx=1&sn=abc&chksm=999"
    assert k(long1) == k(long2)
    assert k(long1) != k(long1.replace("idx=1", "idx=2")), "同一次群发的第二篇是另一篇文章"
    assert k("https://mp.weixin.qq.com/s/AAA") != k("https://mp.weixin.qq.com/s/BBB")


def _fetched(root: Path, name: str, meta: dict, body="正文"):
    d = root / name
    d.mkdir(parents=True)
    (d / "article.md").write_text(frontmatter.dump(meta, body), encoding="utf-8")
    return d


def test_fetch_target():
    root = Path(tempfile.mkdtemp(prefix="wxkit-ws-"))
    url = "https://mp.weixin.qq.com/s/SAME"
    meta = {"title": "标题", "source_url": url, "source_author": "某号", "source_time": "2026-09-14 16:51"}

    d, how = workspace.fetch_target(root, url, meta, day=DAY)
    assert (d.name, how) == ("2026-11-12-01", "新建")

    old = _fetched(root, "2026-09-14_标题", meta)  # 旧命名的抓取结果
    assert workspace.fetch_target(root, url + "?scene=1", meta, day=DAY) == (old, "沿用")
    long_url = "https://mp.weixin.qq.com/s?__biz=MzA&mid=1&idx=1&sn=x"
    assert workspace.fetch_target(root, long_url, {**meta, "source_url": long_url}, day=DAY) == (old, "沿用"), \
        "短链接和长链接：标题、作者、时间都相同算同一篇"
    other = {**meta, "source_time": "2026-09-15 08:00"}
    assert workspace.fetch_target(root, long_url, other, day=DAY)[1] == "新建", "发布时间不同不算同一篇"

    # --into：空稿可以覆盖，已有别的正文拒绝，同一篇允许重抓
    empty = workspace.new_article(root, day=DAY).parent
    assert workspace.fetch_target(root, url, meta, into=empty.name) == (empty, "指定")
    assert workspace.fetch_target(root, url, meta, into=str(empty)) == (empty, "指定"), "也接受完整路径"
    draft = _fetched(root, "2026-11-12-09", {"title": "我写的"}, "我写了一半的稿子")
    try:
        workspace.fetch_target(root, url, meta, into=draft.name)
        raise AssertionError("应该拒绝覆盖")
    except RuntimeError as e:
        assert "已经有正文" in str(e)
    assert workspace.fetch_target(root, url, meta, into=old.name) == (old, "指定")
    try:
        workspace.fetch_target(root, url, meta, into="2026-01-01-01")
        raise AssertionError("应该报文件夹不存在")
    except RuntimeError as e:
        assert "不存在" in str(e) and "new" in str(e)


def test_list_entries():
    root = Path(tempfile.mkdtemp(prefix="wxkit-ws-"))
    assert workspace.entries(root / "不存在") == []
    workspace.new_article(root, day=DAY)                                          # 01 空稿
    _fetched(root, "2026-11-12-02", {"title": "我写的"}, "正文")                    # 02 写稿中
    _fetched(root, "2026-11-12-03", {"title": "原标题", "source_url": "https://x/s/1"})
    d4 = _fetched(root, "2026-11-12-04", {"title": "原标题", "source_url": "https://x/s/2"})
    (d4 / "article.rewrite.md").write_text("---\ntitle: 重写后的标题\n---\n\n正文", encoding="utf-8")
    (d4 / "article.layout.md").write_text("---\ncover: cover.jpg\n---\n\n# 排版后的标题\n\n正文", encoding="utf-8")
    d5 = _fetched(root, "2026-11-12-05", {"title": "推过的"})
    (d5 / "article.layout.md").write_text("---\ntitle: 推过的\n---\n\n正文", encoding="utf-8")
    (d5 / "article.push.md").write_text(
        "# 推送记录：推过的\n\n## 2026-11-12 10:00:00\n\n- 账号：main\n\n"
        "## 2026-11-12 15:30:00\n\n- 账号：life\n", encoding="utf-8")
    (root / "随手放的文件夹").mkdir()
    (root / "v1.2.md").write_text("x")

    rows = {e["name"]: e for e in workspace.entries(root)}
    assert list(rows) == [f"2026-11-12-0{i}" for i in range(1, 6)], list(rows)
    assert [rows[n]["stage"] for n in rows] == ["空稿", "写稿中", "已抓取", "已排版", "已推送"]
    assert rows["2026-11-12-01"]["title"] == ""
    assert rows["2026-11-12-03"]["title"] == "原标题"
    assert rows["2026-11-12-04"]["title"] == "排版后的标题", "取最靠后一步的标题，头信息没有就取 # 标题"
    assert rows["2026-11-12-05"]["pushes"] == 2 and rows["2026-11-12-05"]["last_account"] == "life"

    line = workspace.format_entry(rows["2026-11-12-04"])
    assert "缺封面" in line
    (d4 / "cover.jpg").write_bytes(PNG_1PX)
    assert "缺封面" not in workspace.format_entry(workspace.describe(d4))
    assert "已推送 2 次（最近 11-12 15:30 · life）" in workspace.format_entry(rows["2026-11-12-05"])
    assert "（无标题）" in workspace.format_entry(rows["2026-11-12-01"])

    # 汉字占两格：不同长度的标题，后面的进度列要对齐
    w = workspace._width
    a = workspace.format_entry({**rows["2026-11-12-03"], "title": "短"})
    b = workspace.format_entry({**rows["2026-11-12-03"], "title": "很长很长很长很长很长很长很长很长很长的标题 abc"})
    assert w(a.split("已抓取")[0]) == w(b.split("已抓取")[0]), (a, b)
    assert "..." in b


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} 通过")
    sys.exit(1 if failed else 0)
