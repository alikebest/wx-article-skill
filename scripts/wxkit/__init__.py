"""wx-article skill 的脚本包：抓取、检查、预览、推送公众号文章。

各模块职责：
  frontmatter  front matter 的读写
  naming       每一步输出文件的命名规则
  config       配置查找（环境变量 > 用户目录配置文件），不打印密钥
  render       与主题无关的 Markdown → HTML 处理
  themes       排版主题（lime 荧光柠绿 / pink 樱花粉）
  images       图片压缩、转码、SVG 渲染
  check        推送前检查（不联网）
  preview      本地预览页
  wechat       微信接口客户端
  push         推送到草稿箱
  fetch        抓取公众号文章
"""

__version__ = "1.0.0"
