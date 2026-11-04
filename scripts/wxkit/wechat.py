"""微信公众号接口客户端。

安全约定：secret 和 access_token 都在请求地址的参数里，而 requests 的网络异常信息会带上
完整地址。所以这里捕获所有网络异常，只报异常类型，并用 `from None` 丢掉原异常，
保证任何报错、包括调试时打印的堆栈，都不会带出密钥。
"""

import json
from pathlib import Path

import requests

API_BASE = "https://api.weixin.qq.com"
UA = "wx-article/1.0"

TITLE_MAX, AUTHOR_MAX, DIGEST_MAX = 64, 16, 120

# 常见错误码的中文提示
ERR_HINTS = {
    40001: "access_token 无效：AppSecret 可能填错了，或者在后台被重置过",
    40013: "AppID 无效：检查配置里的 appid",
    40125: "AppSecret 无效：检查配置里的 secret，后台重置过的话要同步更新",
    40164: "本机 IP 不在白名单：去 公众号后台 → 设置与开发 → 基本配置 → IP白名单 加入本机公网 IP",
    45009: "接口今日调用次数已用完，明天再试",
    48001: "没有这个接口的权限（账号类型或认证状态不支持）",
}


class WeChatError(RuntimeError):
    def __init__(self, msg, errcode=None):
        super().__init__(msg)
        self.errcode = errcode


class WeChat:
    def __init__(self, appid: str, secret: str, session=None):
        self._appid = appid
        self._secret = secret
        self.token = None
        self.sess = session or requests.Session()
        self.sess.headers["User-Agent"] = UA

    def __repr__(self):
        return "<WeChat>"  # 不在 repr 里暴露 appid / secret

    # -- 底层请求 --
    def _request(self, method: str, path: str, **kw) -> dict:
        try:
            r = self.sess.request(method, f"{API_BASE}{path}", **kw)
        except requests.RequestException as e:
            raise WeChatError(f"{path} 网络请求失败（{type(e).__name__}），请检查网络后重试") from None
        try:
            # 微信返回 text/plain 且不带 charset，requests 会误按 ISO-8859-1 解码，这里手动按 UTF-8 解
            data = json.loads(r.content.decode("utf-8"))
        except ValueError:
            raise WeChatError(f"{path} 返回的不是 JSON（HTTP {r.status_code}）") from None
        code = data.get("errcode")
        if code not in (None, 0):
            hint = ERR_HINTS.get(code)
            msg = f"{path} 调用失败：errcode={code} {data.get('errmsg', '')}"
            raise WeChatError(msg + (f"\n  → {hint}" if hint else ""), code)
        return data

    def get_token(self, force=False) -> str:
        if self.token and not force:
            return self.token
        data = self._request("GET", "/cgi-bin/token", timeout=15, params={
            "grant_type": "client_credential", "appid": self._appid, "secret": self._secret,
        })
        if "access_token" not in data:
            raise WeChatError("获取 access_token 失败：返回里没有 access_token")
        self.token = data["access_token"]
        return self.token

    def _post(self, path, *, params=None, files=None, json_body=None) -> dict:
        params = dict(params or {})
        params["access_token"] = self.get_token()
        data, headers = None, {}
        if json_body is not None:
            # 必须 ensure_ascii=False 发 UTF-8 明文：默认的 \uXXXX 转义微信不解析，
            # 会原样存进草稿，标题、正文全变成转义字面量
            data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        return self._request("POST", path, params=params, files=files, data=data,
                             headers=headers, timeout=60)

    # -- 素材与图片 --
    def _add_image_material(self, path: Path) -> dict:
        with open(path, "rb") as f:
            return self._post("/cgi-bin/material/add_material", params={"type": "image"},
                              files={"media": (path.name, f, mime(path))})

    def upload_permanent_image(self, path: Path) -> str:
        """永久图片素材（封面用），返回 media_id。"""
        return self._add_image_material(path)["media_id"]

    def upload_content_gif(self, path: Path) -> str:
        """正文 GIF：正文图接口不收 gif，改传永久素材，用它返回的微信 CDN 地址。"""
        return self._add_image_material(path)["url"]

    def upload_content_image(self, path: Path) -> str:
        """正文图（jpg/png ≤1MB），返回微信 CDN 地址。"""
        with open(path, "rb") as f:
            return self._post("/cgi-bin/media/uploadimg",
                              files={"media": (path.name, f, mime(path))})["url"]

    def add_draft(self, article: dict) -> str:
        """创建草稿，返回 media_id。字段超长时按错误码截断后重试一次。"""
        try:
            return self._post("/cgi-bin/draft/add", json_body={"articles": [article]})["media_id"]
        except WeChatError as e:
            # 45003=title 45110=author 45004=digest，只在服务端按转义长度校验时才会出现
            field = {45003: "title", 45110: "author", 45004: "digest"}.get(e.errcode)
            if field is None or field not in article:
                raise
            limit = {"title": 128, "author": 16, "digest": 120}[field]
            article[field] = truncate_units(str(article[field]), limit)
            print(f"  [警告] {field} 超长，已截断后重试")
            return self._post("/cgi-bin/draft/add", json_body={"articles": [article]})["media_id"]


def mime(path: Path) -> str:
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".bmp": "image/bmp", ".webp": "image/webp",
    }.get(Path(path).suffix.lower(), "application/octet-stream")


def wx_units(text: str) -> int:
    """按转义后的长度计数：汉字=6（\\uXXXX），ASCII=1，增补平面字符=12。"""
    n = 0
    for c in text:
        cp = ord(c)
        n += 12 if cp > 0xFFFF else 6 if cp > 127 else 1
    return n


def truncate_units(text: str, max_units: int) -> str:
    """按转义单位截断。正常发 UTF-8 明文时用不到，只在服务端仍报超长时兜底。"""
    while text and wx_units(text) > max_units:
        text = text[:-1]
    return text
