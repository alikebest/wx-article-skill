"""配置与多账号。密钥只从这里读，任何输出都不包含密钥本身。

配置文件：环境变量 WX_ARTICLE_CONFIG 指定的路径，否则 ~/.config/wx-article/config.json。
放在 skill 目录之外：更新或重装 skill 不会冲掉，也不会跟着 skill 仓库被提交。

文件格式（可以存多个公众号）：
  {
    "default": "main",
    "accounts": {
      "main": {"appid": "...", "secret": "...", "author": "..."},
      "life": {"appid": "...", "secret": "...", "author": "..."}
    }
  }
只有一个公众号时也可以直接写 {"appid": ..., "secret": ..., "author": ...}，视为名叫 main 的账号。

环境变量 WX_APPID + WX_SECRET（可加 WX_AUTHOR）都设置时，构成一个名叫 env 的账号，
没有明确指定账号时优先用它，适合 CI 这类自动化场景。

选择账号的优先级：命令行 --account > 文章头信息 account > 环境变量账号 env > 配置里的 default。

文章根目录（新建、抓取、列出文章都在这里）：顶层字段 articles_dir，用 config --root 设置；
环境变量 WX_ARTICLE_DIR 优先于它。都没有时用当前目录下的 articles/。
"""

import json
import os
import re
import shutil
from pathlib import Path

ENV_PATH = "WX_ARTICLE_CONFIG"
ENV_ROOT = "WX_ARTICLE_DIR"
ROOT_KEY = "articles_dir"
ENV_FIELDS = {"appid": "WX_APPID", "secret": "WX_SECRET", "author": "WX_AUTHOR"}
ENV_ACCOUNT = "env"
FLAT_ACCOUNT = "main"
FIELDS = ("appid", "secret", "author")
PLACEHOLDER = "这里填"
NAME_RE = re.compile(r"^[A-Za-z0-9_\-一-鿿]{1,32}$")
def _find_example() -> Path:
    p = Path(__file__).resolve()
    for parent in [p, *p.parents]:
        cand = parent / "config.example.json"
        if cand.is_file():
            return cand
    file_str = str(p)
    if ".zip" in file_str:
        zip_str = file_str[:file_str.index(".zip") + 4]
        zip_parent = Path(zip_str).parent
        for cand in [zip_parent.parent / "config.example.json", zip_parent / "config.example.json"]:
            if cand.is_file():
                return cand
    return Path(__file__).resolve().parents[2] / "config.example.json"


EXAMPLE = _find_example()
NEW_ACCOUNT_TEMPLATE = {
    "appid": "这里填AppID（公众号后台 设置与开发 → 基本配置）",
    "secret": "这里填AppSecret",
    "author": "这里填默认作者名（可留空）",
}


class ConfigError(Exception):
    pass


def config_path() -> Path:
    p = os.environ.get(ENV_PATH, "").strip()
    return Path(p).expanduser() if p else Path.home() / ".config" / "wx-article" / "config.json"


def _filled(v) -> bool:
    s = str(v or "").strip()
    return bool(s) and PLACEHOLDER not in s


def _read_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        # 只报位置，不带文件内容
        raise ConfigError(f"配置文件不是合法的 JSON：{path}（第 {e.lineno} 行第 {e.colno} 列）") from None
    if not isinstance(data, dict):
        raise ConfigError(f"配置文件内容应该是一个 JSON 对象：{path}")
    return data


def _parse(data: dict):
    """返回 (默认账号名, {账号名: 原始字段})。原始字段不做清洗，写回文件时原样保留。"""
    if isinstance(data.get("accounts"), dict):
        accounts = {str(k): (v if isinstance(v, dict) else {}) for k, v in data["accounts"].items()}
        default = str(data.get("default") or "")
        if default not in accounts:
            default = next(iter(accounts), "")
        return default, accounts
    if any(k in data for k in FIELDS):
        return FLAT_ACCOUNT, {FLAT_ACCOUNT: {k: data[k] for k in FIELDS if k in data}}
    return "", {}


def _clean(acc: dict) -> dict:
    return {k: str(acc.get(k)).strip() if _filled(acc.get(k)) else "" for k in FIELDS}


def accounts():
    """返回 (默认账号名, {账号名: {appid, secret, author}})，包含环境变量账号。"""
    default, accs = _parse(_read_file(config_path()))
    accs = {name: _clean(a) for name, a in accs.items()}
    if _filled(os.environ.get("WX_APPID")) and _filled(os.environ.get("WX_SECRET")):
        accs[ENV_ACCOUNT] = _clean({k: os.environ.get(env) for k, env in ENV_FIELDS.items()})
        default = ENV_ACCOUNT
    return default, accs


def select(cli=None, article=None) -> str:
    """按优先级选出账号名，不检查密钥。一个账号都没配置时返回空字符串。"""
    default, accs = accounts()
    for name, source in ((cli, "命令行 --account"), (article, "文章头信息 account")):
        if name:
            if name not in accs:
                raise ConfigError(f"{source} 指定的账号 {name} 不存在，"
                                  f"可选：{' / '.join(accs) or '（还没有配置任何账号）'}")
            return name
    return default


def load(account=None) -> dict:
    """返回 {name, appid, secret, author}，未填写的字段为空字符串。没有任何账号时 name 为空。"""
    default, accs = accounts()
    if not accs:
        return {"name": "", "appid": "", "secret": "", "author": ""}
    name = account or default
    if name not in accs:
        raise ConfigError(f"账号 {name} 不存在，可选：{' / '.join(accs)}")
    return {"name": name, **accs[name]}


def require_credentials(account=None) -> dict:
    _, accs = accounts()
    if not accs:
        raise ConfigError(
            "还没有配置公众号账号。\n"
            "  1. 运行 python wxflow.py config --init 生成配置文件\n"
            f"  2. 用编辑器打开 {config_path()} 自己填写（不要把密钥发到对话里）"
        )
    cfg = load(account)
    missing = [k for k in ("appid", "secret") if not cfg[k]]
    if missing:
        where = "环境变量" if cfg["name"] == ENV_ACCOUNT else str(config_path())
        raise ConfigError(f"账号 {cfg['name']} 的 {' / '.join(missing)} 未填写。"
                          f"请用编辑器打开 {where} 自己填写（不要把密钥发到对话里）")
    return cfg


def status() -> dict:
    """配置状态：只报"填了没有"，不返回 appid 和 secret。作者名不是密钥，可以显示。"""
    path = config_path()
    default, accs = accounts()
    rows = [{
        "name": name,
        "default": name == default,
        "source": "环境变量" if name == ENV_ACCOUNT else "配置文件",
        "appid": "已填写" if a["appid"] else "未填写",
        "secret": "已填写" if a["secret"] else "未填写",
        "author": a["author"],
    } for name, a in accs.items()]
    root, root_source = articles_dir()
    return {"path": str(path), "exists": path.exists(), "default": default, "accounts": rows,
            "articles_dir": str(root) if root else "", "articles_dir_source": root_source}


def articles_dir():
    """返回 (文章根目录, 来源)。环境变量 WX_ARTICLE_DIR > 配置文件 articles_dir；都没有返回 (None, "")。"""
    for value, source in ((os.environ.get(ENV_ROOT), "环境变量"),
                          (_read_file(config_path()).get(ROOT_KEY), "配置文件")):
        if _filled(value):
            p = Path(str(value).strip()).expanduser()
            if not p.is_absolute():
                raise ConfigError(f"{source}里的文章根目录要写绝对路径：{p}。"
                                  "用 python wxflow.py config --root <路径> 重新设置")
            return p, source
    return None, ""


def set_articles_dir(value: str) -> Path:
    """设置文章根目录，存成绝对路径。配置文件还不存在时先从模板生成，免得之后 config --init 不生效。"""
    root = Path(value).expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise ConfigError(f"不是文件夹：{root}")
    path, _ = init()
    data = _read_file(path)
    data[ROOT_KEY] = str(root)
    _write(path, data)
    return root


def init():
    """从 config.example.json 生成配置文件；已存在则不动。返回 (path, created)。"""
    path = config_path()
    if path.exists():
        return path, False
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(EXAMPLE, path)
    return path, True


def _write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _to_multi(data: dict, default: str, accs: dict) -> dict:
    """转成多账号格式。顶层其他字段（如别的工具的配置）原样保留。"""
    rest = {k: v for k, v in data.items() if k not in FIELDS and k not in ("default", "accounts")}
    return {**rest, "default": default, "accounts": accs}


def add_account(name: str) -> Path:
    """新增一个账号，字段先填占位文字，由用户自己用编辑器填写。只有一个账号的旧格式会自动转成多账号格式。"""
    if not NAME_RE.match(name or ""):
        raise ConfigError("账号名只能用字母、数字、下划线、连字符或汉字，最长 32 个字符")
    if name == ENV_ACCOUNT:
        raise ConfigError(f"{ENV_ACCOUNT} 是保留名字，代表环境变量里的账号")
    path = config_path()
    data = _read_file(path)
    default, accs = _parse(data)
    if name in accs:
        raise ConfigError(f"账号 {name} 已经存在")
    accs[name] = dict(NEW_ACCOUNT_TEMPLATE)
    _write(path, _to_multi(data, default or name, accs))
    return path


def set_default(name: str) -> Path:
    path = config_path()
    data = _read_file(path)
    default, accs = _parse(data)
    if name not in accs:
        raise ConfigError(f"账号 {name} 不存在，可选：{' / '.join(accs) or '（还没有配置任何账号）'}")
    _write(path, _to_multi(data, name, accs))
    return path
