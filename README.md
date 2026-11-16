# wx-article-skill

把公众号文章从素材整理、写稿润色、排版预览，一路处理到公众号草稿箱的 AI Skill。

既可以处理已有的 Markdown 稿件，也可以从公众号文章链接开始。你可以走完整套流程，也可以只用其中一步。

**仅限非商业使用，禁止商用。** 本项目采用 [PolyForm Noncommercial License 1.0.0](LICENSE)。

## 能实现哪些功能

| 功能 | 具体能做什么 | 主要产出 |
|---|---|---|
| 新建文章 | 创建按日期和序号命名的文章文件夹，生成稿件模板 | `article.md` |
| 查看文章 | 列出文章标题、所在文件夹及当前进度 | 空稿、已抓取、已重写、已美化、已排版、已推送等状态 |
| 抓取公众号文章 | 从 `mp.weixin.qq.com` 链接提取正文、来源信息并下载正文图片 | `article.md`、`images/` |
| 重写参考文章 | 先提取事实清单，再重新组织叙事和表达，最后润色、核对 | `article.facts.md`、`article.rewrite.md` |
| 美化自己的稿子 | 保留观点、例子和个人口吻，调整结构、节奏和语言 | `article.polish.md` |
| 排版与本地预览 | 按主题整理 Markdown，生成 HTML 预览页 | `article.layout.md`、`article.layout.html` |
| 浏览排版主题 | 展示各主题的风格、适用内容和同一篇文章的排版效果 | 本地主题展示页 |
| 推送公众号草稿箱 | 检查稿件、处理图片和封面，将文章推送到指定账号 | 公众号草稿、`article.push.md` 推送记录 |
| 管理多个公众号 | 配置命名账号、设置默认账号，为单篇文章指定推送目标 | 账号配置与状态查询 |

提供 **11 套排版主题**，可按文章类型选择：

| 主题 | 风格 | 适合内容 |
|---|---|---|
| `lime`（默认） | 荧光柠绿、粗描边、硬阴影 | AI 工具、科技资讯、独立开发 |
| `pink` | 樱花粉、荧光笔、手账感 | 数码好物、生活、轻松话题 |
| `neu` | 同色浮雕、新拟态 | 硬件评测、参数对比 |
| `flat` | 扁平纯色块 | 日更资讯、简洁图文 |
| `minimal` | 超大字号、大量留白 | 观点、深度解读、年度盘点 |
| `bento` | 便当盒网格、速览卡片 | 周报、发布会总结 |
| `match` | 黑黄对比、计分板 | 电竞、体育、对比评测 |
| `term` | 墨绿终端、代码窗口 | 配置教程、命令行工具 |
| `editorial` | 衬线标题、首字下沉、杂志感 | 长文、人物故事、社论 |
| `blueprint` | 浅蓝网格、工程图纸 | 硬件拆解、原理说明 |
| `pixel` | 像素边框、爱心、血条 | 游戏、轻松内容 |

## 有哪些优势

- **按需使用，随时接着做。** 稿件处理步骤接受 Markdown，不必先抓取才能排版，也不必走完整个流程。已有稿件可以直接润色或预览。
- **原稿与各阶段产物分开保存。** 重写、美化和排版生成带步骤后缀的新文件，不覆盖输入稿件；同一篇文章的稿件、图片、封面和推送记录集中在一个文件夹里。
- **重写和润色有不同策略。** 参考文章先拆解事实再重新成文；自己的稿件侧重保留内容和口吻，避免把两种任务混在一起。
- **写作与执行各有分工。** 当前 harness 的模型负责文字编辑，Python 脚本负责抓取、检查、渲染和推送，技能本身无需额外配置 AI 接口。
- **先预览、检查，再推送。** 可以在本地查看排版；推送前自动检查，有错误就停止。推送只在明确要求时执行，成功后留下记录。
- **可跨 harness 复用。** 工作流以 `SKILL.md`、参考文档和 Python 脚本组织，可接入具备相应能力的 Agent Skills 宿主，Claude Code 是其中一种使用方式。

## 使用许可

本项目采用 **PolyForm Noncommercial License 1.0.0**，SPDX 标识为 `PolyForm-Noncommercial-1.0.0`。

- 允许在许可证规定的范围内进行非商业使用、修改和再分发，例如个人学习、研究实验和非商业兴趣项目。
- **本仓库不授予商业使用权。** 不得以商业目的使用本项目，例如售卖本项目、集成到收费产品，或用它提供收费代写、排版、代运营等服务。
- 再分发时须保留许可证或其链接，以及本项目提供的 `Required Notice:` 声明。
- 许可证对特定非商业机构等情形另有明确规定，具体权利、例外和义务以 [LICENSE](LICENSE) 原文为准。第三方依赖仍遵循各自的许可证。

Required Notice: Copyright (c) 2026 alikebest (https://github.com/alikebest/wx-article-skill)

## 怎么使用

### 1. 准备运行环境

要完成整套工作流，所用 harness（智能体运行环境）需要能读取 `SKILL.md` 及引用文件、读写稿件，并执行 Python 脚本。抓取和推送需要联网；本地排版预览不需要公众号密钥。

在实际执行脚本的本机、容器或远程环境中安装：

```bash
git clone https://github.com/alikebest/wx-article-skill.git
cd wx-article-skill
pip install -r requirements.txt
```

建议设置固定的文章根目录，将下面的示例路径换成自己选定的位置：

```bash
python scripts/wxflow.py config --root D:/公众号文章
```

未设置时，默认使用当前工作目录下的 `articles/`。`new`、`list`、`fetch` 可用 `-o <路径>` 临时指定根目录；根目录优先级为 `-o` > `WX_ARTICLE_DIR` 环境变量 > 配置文件 > 默认目录。

### 2. 将 Skill 接入 harness

仓库及本地开发目录名为 `wx-article-skill`，技能名为 `wx-article`。按宿主支持的方式选择一种接入：

| 接入方式 | 操作 |
|---|---|
| 技能目录或自定义路径 | 将完整目录安装或注册到宿主支持的位置，保留文件的相对结构；若要求目录名与技能名一致，安装目录使用 `wx-article` |
| ZIP 导入 | 运行 `python tools/pack_zip.py`，按平台要求导入 `dist/wx-article.zip` 或 `dist/wx-article-folder.zip` |
| 显式读取入口文件 | 如果宿主不自动发现技能，但有文件和命令工具，直接让智能体读取项目的 `SKILL.md`，再执行任务 |

显式指定入口的示例：

```text
请先读取 <项目绝对路径>/SKILL.md，按其中的公众号文章工作流处理这份稿子：<稿件绝对路径>。
```

不同 harness 的技能目录、导入规则和执行权限不同，需按各自文档配置，尚未逐一验证所有产品。ZIP 打包会移除 `argument-hint` 扩展字段，其余元信息仍需符合目标平台规则。参见 [Agent Skills 概述](https://agentskills.io/home)和[宿主集成说明](https://agentskills.io/client-implementation/adding-skills-support)。

技能正文中的 Claude 可对应为当前 AI 智能体，Agent / Task 对应宿主的子代理工具。子代理是可选能力：没有时，重写流程可以在主对话中依次完成，原文表达与新稿的上下文隔离会弱一些。

**Claude Code 安装示例**：按其[技能文档](https://code.claude.com/docs/en/skills)，可安装到用户技能目录：

```bash
git clone https://github.com/alikebest/wx-article-skill.git ~/.claude/skills/wx-article
pip install -r ~/.claude/skills/wx-article/requirements.txt
```

项目内使用时可放到 `<项目>/.claude/skills/wx-article/`，重新加载后通过 `/wx-article` 调用。其他 harness 使用各自的入口。Windows 命令行若未展开 `~`，请改用用户目录的完整路径。

### 3. 用自然语言处理文章

加载技能后，直接说明要处理的稿件和目标即可。

**从自己的稿子开始：**

```text
帮我润色 D:/公众号文章/我的稿子.md，保留我的观点、例子和口吻。
把生成的润色稿用 editorial 主题排版，并打开预览。
```

**从参考文章开始：**

```text
抓取这篇文章：https://mp.weixin.qq.com/s/文章标识
根据抓取结果提取事实，重新组织成一篇文章，再用 lime 主题排版预览。
```

**其他常用指令：**

| 目标 | 示例 |
|---|---|
| 开始新稿 | 新建一篇文章，标题是「我的工具周报」 |
| 查找已有文章 | 列一下文章，看看哪些已经排版 |
| 选择主题 | 打开模板列表，看看各个主题的效果 |
| 更换排版 | 把这份稿子改成 pink 主题，再生成预览 |
| 推送草稿 | 检查这份排版稿，通过后推送到 life 号的草稿箱 |

重写参考文章前，请确认有相应的转载或改写授权。正文中的图片应使用本地文件；封面由用户准备，统一命名为 `cover.jpg`，放在稿件旁边。缺封面时可以先完成排版，推送前再补齐。

### 4. 配置公众号并推送

只做写稿和本地预览时，可以先跳过账号配置。需要推送时，生成配置模板：

```bash
python scripts/wxflow.py config --init
```

用编辑器打开 `~/.config/wx-article/config.json`，自行填写 `appid`、`secret` 和默认作者，并在公众号后台将执行环境的公网 IP 加入白名单。配置也可通过 `WX_ARTICLE_CONFIG` 指向其他位置。

**密钥只在本地填写，不要发到对话里。** 让智能体运行 `config` 查看配置状态即可，不要让它读取或打印配置文件。

多账号的常用操作：

```bash
# 添加命名账号，再自行打开配置文件填写
python scripts/wxflow.py config --add life

# 设置默认账号、查看配置状态
python scripts/wxflow.py config --default life
python scripts/wxflow.py config

# 检查并推送一份稿件
python scripts/wxflow.py check D:/公众号文章/我的稿子.layout.md --account life
python scripts/wxflow.py push D:/公众号文章/我的稿子.layout.md --account life
```

账号选择优先级为：命令行 `--account` > 稿件头信息 `account` > 环境变量账号 `env` > 默认账号。也可以通过 `WX_APPID`、`WX_SECRET`、`WX_AUTHOR` 提供环境变量账号。

推送后，前往公众号后台草稿箱检查效果，再手动发表。实际可用接口和配额以公众号账号权限及接口返回为准。推送记录中的 `thumb_media_id` 可用于复用封面，且仅对上传它的账号有效。

### 5. 管理稿件与排版信息

一篇文章一个文件夹，由新建或抓取命令生成，名称为 `年-月-日-序号`：

```text
D:/公众号文章/
└── 2026-11-16-01/
    ├── article.md             原稿或抓取结果
    ├── article.facts.md       重写使用的事实清单
    ├── article.rewrite.md     重写稿
    ├── article.polish.md      润色稿
    ├── article.layout.md      排版稿
    ├── article.layout.html    本地预览
    ├── article.push.md        推送记录
    ├── cover.jpg              用户准备的封面
    └── images/                正文图片
```

以上文件按实际使用的步骤生成。已有 Markdown 可以直接在原位置处理，输出写在输入旁边，无需先搬进文章根目录。步骤后缀会统一替换，例如 `article.rewrite.md` 排版后生成 `article.layout.md`。

稿件通过 YAML 头信息设置标题、主题和推送账号，例如：

```yaml
---
title: 我的工具周报
author: 小明
digest: 本周值得关注的工具与实践。
cover: cover.jpg
theme: lime
account: life
---

这里开始写正文。
```

`author` 留空时使用账号默认作者，`digest` 留空时从正文开头提取，`account` 省略时按账号选择规则处理。已有封面素材可用 `thumb_media_id` 复用，其优先级高于 `cover`。

更多排版规则见 [references/layout.md](references/layout.md)，标题规则见 [references/titles.md](references/titles.md)。正文含 SVG 图片时，需要额外安装 `playwright`，脚本使用本机 Edge / Chrome 渲染。

### 6. 直接使用命令行

脚本命令可独立运行。重写、美化及排版中的内容整理由智能体或人工完成，脚本负责抓取、渲染、检查和推送等操作。

| 命令 | 用途 |
|---|---|
| `python scripts/wxflow.py new --title "文章标题"` | 新建文章 |
| `python scripts/wxflow.py list` | 列出文章及进度 |
| `python scripts/wxflow.py fetch <链接>` | 抓取公众号文章；可加 `--into <文件夹>` 使用指定文件夹 |
| `python scripts/wxflow.py themes` | 查看主题名称 |
| `python scripts/wxflow.py gallery` | 打开主题展示页；加 `--no-open` 仅生成页面 |
| `python scripts/wxflow.py preview <稿件.md> --open` | 将已有 Markdown 渲染为 HTML 并打开预览 |
| `python scripts/wxflow.py check <稿件.md>` | 本地推送检查，不调用公众号接口 |
| `python scripts/wxflow.py push <稿件.md>` | 推送至公众号草稿箱 |

以上 `<链接>`、`<稿件.md>` 等为占位符，运行时替换为实际值。`check`、`preview`、`push` 均可加 `--account <账号名>`。

### 7. 测试与打包

在仓库目录中运行：

```bash
python tests/test_wxkit.py
python tools/pack_zip.py
```

打包脚本会先运行测试，再生成并解压自检两种发布包：

- `dist/wx-article.zip`：`SKILL.md` 在 ZIP 根目录。
- `dist/wx-article-folder.zip`：外层包含 `wx-article/` 文件夹。

发布包将模块收在 `scripts/wxkit.zip` 中；本地开发使用 `scripts/wxkit/` 源码目录。文章、个人配置、缓存和 `dist/` 不会提交到仓库。
