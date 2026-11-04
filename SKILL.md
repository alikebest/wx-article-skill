---
name: wx-article
description: 微信公众号文章工作流：抓取公众号文章（mp.weixin.qq.com 链接）、重写别人的文章、美化润色自己写的稿子、按主题排版并本地预览、推送到公众号草稿箱。用户提到公众号、草稿箱、公众号排版，要把文章改写/润色后发公众号，或者给出 mp.weixin.qq.com 链接时使用。每一步都可以单独用，输入任意 Markdown 文件。
argument-hint: "[抓取|重写|美化|排版|推送] <链接或 md 路径>"
---

# 公众号文章工作流

五个操作彼此独立。每个操作都接受任意 md（抓来的、用户自己写的、上一步的产物都行），输出写在输入文件旁边，**从不修改输入文件**。

| 操作 | 谁来做 | 输入 | 输出 |
|---|---|---|---|
| 抓取 | 脚本 | 公众号文章链接 | `<根目录>/<日期_标题>/article.md` + `images/` |
| 重写 | Claude | 任意 md，通常是别人的文章 | `<名>.facts.md` + `<名>.rewrite.md` |
| 美化 | Claude | 任意 md，通常是用户自己的稿子 | `<名>.polish.md` |
| 排版 | Claude + 脚本 | 任意 md | `<名>.layout.md` + `<名>.layout.html`（预览页） |
| 推送 | 脚本 | 任意 md | 公众号草稿 + `<名>.push.md`（推送记录，追加写） |

## 判断用户要做哪一步

- 给了 mp.weixin.qq.com 链接，或说"抓取""下载这篇" → 抓取
- 要把**别人的**文章"重写""改写""用自己的话写" → 重写
- 要把**自己写的**稿子"润色""美化""整理一下" → 美化。拿不准稿子是谁写的，问一句
- "排版""预览""看看效果""换个主题" → 排版
- "推送""发到草稿箱""发公众号" → 推送

一次要求多步（如"重写后排版"）就按 抓取 → 重写或美化 → 排版 → 推送 的顺序依次做，后一步的输入是前一步的输出。重写已经包含去 AI 味的润色，不用再美化。

**推送只在用户明确要求时执行。** 它会占用接口日配额、往素材库新增封面，前面几步做完了也不要顺手推送。

## 输出文件命名

去掉输入文件名里已有的步骤后缀（`.facts` `.rewrite` `.polish` `.layout` `.push`），再加上本步的后缀：

- `article.md` → `article.rewrite.md` → `article.layout.md` → `article.push.md`
- `我的稿子.md` → `我的稿子.polish.md` → `我的稿子.layout.md`

输出文件已经存在、而用户并没有说要重做这一步时，先确认再覆盖。

## 脚本

统一入口是 skill 目录（也就是这个 SKILL.md 所在的目录）下的 `scripts/wxflow.py`。调用方式：`python "<skill目录>/scripts/wxflow.py" <命令>`。

| 命令 | 作用 |
|---|---|
| `fetch <链接> [-o 根目录]` | 抓取文章，根目录默认是当前目录下的 `articles/` |
| `check <md> [--account 账号]` | 推送前检查，不联网、不耗配额。输出分错误/警告/提示三级 |
| `preview <md> [--open] [--account 账号]` | 生成与 md 同名的 `.html` 预览页，`--open` 用浏览器打开 |
| `push <md> [--account 账号]` | 推送到草稿箱。先自动检查，有错误就拒绝，不调用任何接口 |
| `config` | 列出所有账号：哪个是默认、密钥填没填（不显示密钥）、作者名 |
| `config --init` / `--add <账号名>` / `--default <账号名>` | 生成配置文件 / 新增账号 / 设置默认账号 |
| `themes` | 列出排版主题 |

脚本报缺少依赖时，告诉用户运行 `pip install -r "<skill目录>/requirements.txt"`。

## front matter

所有步骤共用这套字段，未知字段原样保留：

| 字段 | 说明 |
|---|---|
| `title` | 标题，≤64 字 |
| `author` | 作者，≤16 字；留空则用配置里的默认作者 |
| `digest` | 摘要，≤120 字；留空则自动取正文开头 |
| `cover` | 封面图，路径相对本 md 文件。排版时固定写成 `cover.jpg`（见「封面」） |
| `thumb_media_id` | 已上传过的封面素材 ID，优先于 cover，不会重复上传 |
| `theme` | 排版主题：`lime`（默认）、`pink`、`neu`、`clay`、`flat`、`minimal`、`bento`，怎么选见 [references/layout.md](references/layout.md) |
| `account` | 推送到哪个公众号（配置里的账号名），不写则用默认账号，见「多个公众号」 |
| `source_url` / `source_author` / `source_time` | 来源信息，抓取时写入 |

重写、美化、排版写输出文件时：`title`、`digest` 由这一步重新确定；其余字段**输入里有就原样带过去，没有就不要编**。

## 各步骤怎么做

### 抓取

运行 `fetch`，把输出路径、标题、图片下载情况告诉用户。报"被拦截"时让用户过一会儿再试或换个网络，不要反复重试。

### 重写

读 [references/rewrite.md](references/rewrite.md)，按里面的三遍流程做。标题规则见 [references/titles.md](references/titles.md)。

### 美化

读 [references/polish.md](references/polish.md)。标题规则见 [references/titles.md](references/titles.md)。

### 排版

读 [references/layout.md](references/layout.md)。

### 推送

1. 确定推到哪个账号，规则见下面「多个公众号」。
2. 运行 `check <md>`（指定了账号就加 `--account`）。有错误先解决，缺封面就按下面「封面」处理。
3. 运行 `push <md>`（同上）。
4. 告诉用户：推到了哪个账号、草稿 media_id、推送记录路径，并提醒去 mp.weixin.qq.com → 草稿箱预览后手动点「发表」（个人主体订阅号不能用接口发表）。
5. 推送记录里如果提示"新增了一张封面素材"，告诉用户可以把 `thumb_media_id` 写进 md 复用（只在这个账号里有效），但不要自己去改用户的 md。

报错时把脚本给出的中文提示转告用户（如 40164 是 IP 不在白名单，45009 是当天配额用完）。

## 多个公众号

配置文件里可以存多个命名账号。推送用哪个账号，按这个优先级选：`--account` > 文章头信息 `account` > 环境变量账号 `env` > 默认账号。

- 用户说"推到 life 号""用生活号发"：命令加 `--account life`。不确定账号名时先运行 `config` 看有哪些，对不上就问用户。
- 用户只说"推送"，没提账号，文章头信息里也没有 `account`：只有一个账号就直接推；**有多个账号时，先告诉用户会推到默认账号（账号名和作者），用户确认后再推。**
- 排版时用户说了这篇要发哪个号：在头信息写 `account: 账号名`，以后推送就不用再指定。没说就不写。
- 新增账号：运行 `config --add <账号名>`，再请用户自己用编辑器打开配置文件填写（规则同「密钥」）。改默认账号：`config --default <账号名>`。
- `thumb_media_id` 只在上传它的那个账号里有效，check 会对照推送记录检查，报错时按提示处理。
- 每个公众号都要在各自后台的 IP 白名单里加入本机 IP。

## 封面

封面由用户自己准备，**统一命名为 `cover.jpg`，放在 md 所在的文件夹**。排版时头信息固定写 `cover: cover.jpg`。**不要从原文下载封面，也不要自己生成。**

- `cover.jpg` 还没放：照常完成排版，在回复里提醒用户放进去。check 会报缺封面，放好后重新检查即可。
- 用户手上的封面是 png 等其他格式：征得用户同意后，用 Pillow 转存成 `cover.jpg`。不要只改扩展名，那样文件内容还是 png。

## 密钥

- 配置文件在 `~/.config/wx-article/config.json`（或环境变量 `WX_ARTICLE_CONFIG` 指定的位置），也可以用环境变量 `WX_APPID` / `WX_SECRET` / `WX_AUTHOR`。
- 只用 `config` 命令看配置状态。**不要读取、打印、cat 配置文件，也不要 echo 这几个环境变量**：内容一旦进入对话就离开了本机。
- 未配置时：运行 `config --init` 生成模板，请用户**自己用编辑器打开填写**。不要让用户把 AppID、AppSecret 发到对话里。
- 用户主动在对话里发了 AppSecret：提醒它已经留在对话记录里了，建议去公众号后台重置，再自己把新的填进配置文件。
