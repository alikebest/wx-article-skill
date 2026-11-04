# -*- coding: utf-8 -*-
"""wx-article 统一入口：公众号文章的抓取、检查、预览、推送。

每个命令都只接一个 md（或链接），彼此独立，可以单独使用：
  python wxflow.py fetch <公众号文章链接> [-o 根目录]          抓取 → <根目录>/<日期_标题>/article.md
  python wxflow.py check <文章.md> [--account 账号]            推送前检查，不联网
  python wxflow.py preview <文章.md> [--open] [--account 账号] 生成本地预览页 <文章>.html，不联网
  python wxflow.py push <文章.md> [更多.md ...] [--account 账号] 推送到草稿箱，记录写入 <文章>.push.md
  python wxflow.py config                                     查看所有账号的配置状态（不显示密钥）
  python wxflow.py config --init                              生成配置文件
  python wxflow.py config --add <账号名>                       新增一个账号（之后自己用编辑器填写）
  python wxflow.py config --default <账号名>                   设置默认账号
  python wxflow.py themes                                     列出排版主题

多个公众号：推送用哪个账号，按 --account > 文章头信息 account > 环境变量账号 > 默认账号 选择。
重写、美化、排版由 Claude 按 skill 里的 references/*.md 完成，不在这里。

调试：设置环境变量 WXFLOW_DEBUG=1 会在出错时打印堆栈（堆栈里同样不含密钥）。
"""

import argparse
import os
import sys
import traceback
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# 控制台编码不是 UTF-8 时（如部分 Windows 终端），无法编码的字符用 ? 代替，不至于报错退出
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(errors="replace")


def cmd_fetch(args):
    from wxkit import fetch
    root = Path(args.out) if args.out else Path.cwd() / "articles"
    d = fetch.fetch(args.url, root)
    print(f"已保存：{d['path']}" + ("（覆盖了之前抓取的版本）" if d["overwritten"] else ""))
    print(f"标题：{d['title']}")
    print(f"来源：{d['author'] or '（未知）'}  发布时间：{d['publish_time'] or '（未知）'}")
    print(f"图片：{d['images_ok']}/{d['images_unique']} 张已下载到 images/（正文共 {d['images_total']} 处）")
    print(f"正文：{d['chars']} 字符")
    return 0


def cmd_check(args):
    from wxkit import check
    r = check.inspect(_existing(args.md), args.account)
    print(check.format_report(r))
    return 0 if r.ok else 1


def cmd_preview(args):
    from wxkit import check, preview
    r = check.inspect(_existing(args.md), args.account)
    out = preview.build(r)
    print(check.format_report(r))
    print(f"\n预览页：{out}")
    if args.open:
        webbrowser.open(out.resolve().as_uri())
    return 0


def cmd_push(args):
    from wxkit import config, frontmatter, push
    from wxkit.wechat import WeChat
    files = [_existing(f) for f in args.md]
    clients = {}  # 每个账号一个客户端，同一账号的多篇共用 access_token
    ok = 0
    for f in files:
        try:
            meta, _ = frontmatter.split(f.read_text(encoding="utf-8"))
            cfg = config.require_credentials(config.select(args.account, meta.get("account")))
            if cfg["name"] not in clients:
                clients[cfg["name"]] = WeChat(cfg["appid"], cfg["secret"])
            if push.push_one(f, clients[cfg["name"]], cfg["name"]):
                ok += 1
        except Exception as e:
            print(f"  [错误] {f.name} 推送失败：{e}")
            if os.environ.get("WXFLOW_DEBUG"):
                traceback.print_exc()
    if len(files) > 1:
        print(f"\n完成：{ok}/{len(files)} 篇推送成功")
    return 0 if ok == len(files) else 1


def cmd_config(args):
    from wxkit import config
    if args.init:
        path, created = config.init()
        if created:
            print(f"已生成配置文件：{path}")
            print("请用编辑器打开它，自己填写 appid / secret / author（不要把密钥发到对话里）")
        else:
            print(f"配置文件已存在，没有改动：{path}")
    if args.add:
        path = config.add_account(args.add)
        print(f"已新增账号 {args.add}：请用编辑器打开 {path}，在 accounts.{args.add} 里自己填写"
              f" appid / secret / author（不要把密钥发到对话里）")
    if args.default:
        config.set_default(args.default)
        print(f"默认账号已改为 {args.default}")

    st = config.status()
    print(f"\n配置文件：{st['path']}（{'存在' if st['exists'] else '不存在'}）")
    if not st["accounts"]:
        print("还没有任何账号，运行 config --init 生成配置文件")
        return 0
    for a in st["accounts"]:
        mark = "（默认）" if a["default"] else ""
        print(f"  {a['name']}{mark}  appid：{a['appid']}  secret：{a['secret']}  "
              f"作者：{a['author'] or '（空）'}  来源：{a['source']}")
    return 0


def cmd_themes(args):
    from wxkit.themes import DEFAULT_THEME, THEMES
    for k, (name, desc) in THEMES.items():
        print(f"{k:9s}{name}{'（默认）' if k == DEFAULT_THEME else ''}\n         {desc}")
    return 0


def _existing(p) -> Path:
    p = Path(p)
    if not p.is_file():
        raise FileNotFoundError(f"文件不存在：{p}")
    return p


def main(argv=None):
    parser = argparse.ArgumentParser(prog="wxflow.py", description="公众号文章：抓取 / 检查 / 预览 / 推送",
                                     formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="命令")
    account_help = "用哪个公众号账号（配置里的账号名），优先于文章头信息里的 account"

    p = sub.add_parser("fetch", help="抓取公众号文章")
    p.add_argument("url", help="公众号文章链接")
    p.add_argument("-o", "--out", help="输出根目录（默认 ./articles）")
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("check", help="推送前检查（不联网）")
    p.add_argument("md")
    p.add_argument("--account", help=account_help)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("preview", help="生成本地预览页（不联网）")
    p.add_argument("md")
    p.add_argument("--open", action="store_true", help="生成后用浏览器打开")
    p.add_argument("--account", help=account_help)
    p.set_defaults(func=cmd_preview)

    p = sub.add_parser("push", help="推送到草稿箱")
    p.add_argument("md", nargs="+")
    p.add_argument("--account", help=account_help)
    p.set_defaults(func=cmd_push)

    p = sub.add_parser("config", help="查看配置状态 / 生成配置文件 / 管理账号")
    p.add_argument("--init", action="store_true", help="从模板生成配置文件（已存在则不动）")
    p.add_argument("--add", metavar="账号名", help="新增一个账号，之后自己用编辑器填写")
    p.add_argument("--default", metavar="账号名", help="设置默认账号")
    p.set_defaults(func=cmd_config)

    p = sub.add_parser("themes", help="列出排版主题")
    p.set_defaults(func=cmd_themes)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n已中断")
        return 130
    except Exception as e:
        print(f"[错误] {e}")
        if os.environ.get("WXFLOW_DEBUG"):
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
