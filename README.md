# wx-article：公众号文章工作流 skill

给 Claude Code 用的 skill：抓取公众号文章 → 重写或美化 → 排版预览 → 推送到草稿箱。
每一步都可以单独用，输入任意 Markdown，输出写在输入旁边，不改原文件。

| 操作 | 怎么说 | 产出 |
|---|---|---|
| 抓取 | "抓取 https://mp.weixin.qq.com/s/xxx" | `articles/<日期_标题>/article.md` + `images/` |
| 重写 | "把 article.md 重写一下"（别人的文章） | `article.facts.md` + `article.rewrite.md` |
| 美化 | "帮我润色 我的稿子.md"（自己的稿子） | `我的稿子.polish.md` |
| 排版 | "用粉色主题排版 xxx.md" | `xxx.layout.md` + `xxx.layout.html`（预览） |
| 推送 | "把 xxx.layout.md 推送到草稿箱" | 公众号草稿 + `xxx.push.md`（推送记录） |

重写、美化、排版由 Claude 完成，用的是你当前对话里的模型，不需要额外的 AI 接口。

## 安装

```bash
# 1. 放到个人 skill 目录（目录名就是 skill 名）
git clone <本仓库地址> ~/.claude/skills/wx-article

# 2. 安装依赖
pip install -r ~/.claude/skills/wx-article/requirements.txt

# 3. 生成配置文件，然后用编辑器打开它，自己填 appid / secret / author
python ~/.claude/skills/wx-article/scripts/wxflow.py config --init
```

Windows 下 `~` 是 `C:\Users\<你的用户名>`。重开一个 Claude Code 会话，输入 `/` 能看到 `wx-article` 就装好了。

只想在某个项目里用，就放到 `<项目>/.claude/skills/wx-article/`。

## 配置与密钥

配置文件在 **`~/.config/wx-article/config.json`**，不在 skill 目录里：更新、重装 skill 不会冲掉配置，配置也不会跟着 skill 仓库被提交。

```json
{
  "default": "main",
  "accounts": {
    "main": { "appid": "公众号后台 设置与开发 → 基本配置", "secret": "同上", "author": "默认作者名，可留空" },
    "life": { "appid": "...", "secret": "...", "author": "..." }
  }
}
```

只有一个公众号时，也可以直接写 `{"appid": ..., "secret": ..., "author": ...}`，视为名叫 `main` 的账号。

**多个公众号怎么切换：**

- 新增账号：`python scripts/wxflow.py config --add life`，再用编辑器打开配置文件，在 `accounts.life` 里填写
- 改默认账号：`config --default life`
- 推送时指定：`push xxx.md --account life`，或者在文章头信息里写 `account: life`
- 选择顺序：`--account` > 文章头信息 `account` > 环境变量账号 > 默认账号
- 推送记录会写明推到了哪个账号；`thumb_media_id` 只在上传它的账号里有效，用错了 `check` 会报错

环境变量：`WX_APPID` + `WX_SECRET`（可加 `WX_AUTHOR`）都设置时，构成一个名叫 `env` 的账号，没明确指定账号时优先用它，适合 CI；`WX_ARTICLE_CONFIG` 可以换配置文件的位置。

安全上做了这些：

- **自己填，别发给 Claude。** 对话内容会发给模型并存进本地会话记录。skill 里也规定了 Claude 只能用 `config` 命令查看"填没填"，不读配置文件。
- 网络出错时报错信息不带请求地址（地址里有 secret 和 access_token），调试堆栈里也没有。
- 推送前先做本地检查，检查不过不调用任何接口。
- 还要去公众号后台 **基本配置 → IP 白名单** 加入本机公网 IP，否则报 40164。白名单也是一道保护：密钥万一泄露，别人不在白名单里也调不了接口。泄露后去后台重置 AppSecret。

## 不通过 Claude，直接用命令行

```bash
python scripts/wxflow.py fetch <链接> [-o 根目录]   # 抓取，默认存到 ./articles
python scripts/wxflow.py check <文章.md>             # 推送前检查（不联网）
python scripts/wxflow.py preview <文章.md> --open    # 本地预览（不联网）
python scripts/wxflow.py push <文章.md>              # 推送到草稿箱（--account 指定账号）
python scripts/wxflow.py config                      # 所有账号的配置状态（不显示密钥）
python scripts/wxflow.py config --add <账号名>        # 新增账号
python scripts/wxflow.py config --default <账号名>    # 设置默认账号
python scripts/wxflow.py themes                      # 排版主题
```

## front matter

```yaml
---
title: 标题（≤64 字，留空取正文第一个 # 标题）
author: 作者（≤16 字，留空用配置里的 author）
digest: 摘要（≤120 字，留空自动取正文开头）
cover: cover.jpg            # 必填，路径相对本 md。排版时固定写成 cover.jpg，封面图就用这个名字放在 md 旁边
thumb_media_id: MEDIA_ID    # 可选，复用已上传的封面，优先于 cover
theme: lime                 # lime（默认）/ pink / neu / clay / flat / minimal / bento，见下方「排版主题」
account: life               # 可选，推送到哪个公众号；不写用默认账号
---
```

## 排版主题

在 front matter 里写 `theme: <主题>`，或者对 Claude 说"用夸张极简排版"。

| 主题 | 风格 | 适合 |
|---|---|---|
| `lime`（默认） | 荧光柠绿 · 新粗野主义：黑白高对比、粗描边硬阴影 | AI 工具、独立开发、科技资讯 |
| `pink` | 樱花粉 · 荧光笔：柔和手账风 | 数码好物、轻松话题、生活类 |
| `neu` | 新拟态：同色浮雕，只靠阴影做凸起凹陷 | 硬件评测、参数对比（深色模式下浮雕感会消失） |
| `clay` | 黏土拟态：马卡龙色、超大圆角、三层阴影 | 科普小报、数码入门 |
| `flat` | 扁平化：纯色块，零阴影零渐变 | 日更资讯，深色模式最稳 |
| `minimal` | 夸张极简：超大字号、大量留白、一个强调色 | 观点、深度解读、年度盘点 |
| `bento` | 便当盒网格：开头自动生成"本期速览"格子盒 | 周报、发布会总结 |

后五个主题额外认一种**数据列表**：无序列表 1~3 项，每项都是 `**数值** 简短说明`，会排成各主题的数据组件（数据圆盘、数据卡、数据磁贴、超大数字、便当数据格）：

```markdown
- **35dB** 降噪深度
- **30h** 综合续航
```

想保持普通列表，在加粗后面加冒号（`- **30h**：续航`）。各主题对每种写法的具体效果见 [references/layout.md](references/layout.md)。

## 注意事项

- **个人主体订阅号只能推到草稿箱**（2025 年 7 月起发布接口被回收），发表要去后台手动点。
- 接口有日配额，`draft` 相关接口一天几十次后报 45009，第二天再试。
- 每推送一次会把封面存成一张新的永久素材。想复用，把推送记录里的 `thumb_media_id` 写进 front matter。
- 正文图片必须是本地图，外链图发出去显示不出来。
- 正文里有 SVG 图片时需要额外 `pip install playwright`（用本机 Edge/Chrome 渲染）。
- 重写别人的文章发布前，请确认有转载或改写的授权。来源链接会保留在 front matter 的 `source_url` 里。

## 目录结构

```
SKILL.md               skill 入口：给 Claude 的总说明
references/            各步骤的详细规范，Claude 用到时才读
  rewrite.md           重写：事实清单 → 子代理成文 → 去 AI 味
  polish.md            美化：保留原稿内容，只调结构和节奏
  layout.md            排版：front matter、主题写法、允许的格式调整
  titles.md            标题与摘要规则
scripts/wxflow.py      统一入口
scripts/wxkit/         实现：抓取、主题、检查、预览、推送、配置
tests/test_wxkit.py    本地回归测试（不调用接口）：python tests/test_wxkit.py
```
