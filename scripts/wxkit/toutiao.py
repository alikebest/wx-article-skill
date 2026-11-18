"""从 Markdown 导出今日头条排版预览和可复制的正文片段。"""

import base64
import html
import json
import mimetypes
import re
from pathlib import Path
from string import Template
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup, NavigableString

from . import frontmatter, naming, render


MARKER = '<!-- 由 wx-article 生成的今日头条导出 -->'
PAGE = Template('''<!doctype html>
$marker
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>今日头条排版 · $title</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; background: #eee; color: #202020;
           font-family: -apple-system, BlinkMacSystemFont, "Microsoft YaHei", sans-serif; }
    .tools { max-width: 780px; margin: 28px auto; padding: 20px 24px; background: #fff;
             border: 2px solid #111; box-shadow: 5px 5px 0 #111; font-size: 14px; line-height: 1.8; }
    .tools p { margin: 0 0 10px; }
    .actions { display: flex; gap: 10px; flex-wrap: wrap; }
    button { font: inherit; font-weight: 700; cursor: pointer; background: #111;
             color: #fff; border: 2px solid #111; padding: 9px 16px; }
    button.secondary { background: #fff; color: #111; }
    #status:not(:empty) { margin-top: 8px; color: #555; }
    .paper { max-width: 740px; margin: 34px auto 48px; padding: 38px 44px 50px; background: #fff; }
    .title { font-size: 24px; line-height: 1.5; margin: 0 0 14px; font-weight: 800; }
    .byline { font-size: 14px; color: #666; margin-bottom: 34px; }
    #article-body { font-size: 16px; line-height: 1.8; overflow-wrap: anywhere; }
    #article-body p { margin: 0 0 20px; }
    #article-body h1 { position: relative; font-size: 18px; line-height: 1.55;
                       font-weight: 800; margin: 30px 0 23px; padding-left: 17px; }
    #article-body h1::before { content: ""; position: absolute; left: 2px; top: 8px;
                               width: 4px; height: 14px; background: #f35151; transform: skew(-20deg); }
    #article-body strong { font-weight: 800; color: #111; }
    #article-body blockquote { border-left: 4px solid #ccc; margin: 24px 0; padding: 0 0 0 18px; }
    #article-body blockquote p { margin: 0; }
    #article-body hr { border: 0; border-top: 1px solid #ddd; margin: 30px 0; }
    #article-body ul, #article-body ol { padding-left: 1.3em; margin: 0 0 22px; }
    #article-body li { padding-left: 3px; margin-bottom: 12px; }
    #article-body img { max-width: 100%; height: auto; }
    #article-body pre { overflow-x: auto; }
    #article-body .pgc-img { margin: 24px 0; }
    #article-body .pgc-img img { display: block; margin: 0 auto 8px; }
    #article-body .pgc-img-caption { margin: 0; color: #666; text-align: center; font-size: 13px; }
    @media (max-width: 800px) {
      .tools { margin: 16px; }
      .paper { margin: 28px auto 0; padding: 25px 22px 40px; }
      .title { font-size: 22px; }
      #article-body h1 { font-size: 17px; }
    }
  </style>
</head>
<body>
  <aside class="tools" aria-label="复制到今日头条">
    <p>将标题和正文分别粘贴到头条文章编辑器。若图片未随正文导入，请从原稿目录补传，再核对图片描述。</p>
    <div class="actions">
      <button type="button" id="copy-body">复制正文</button>
      <button type="button" class="secondary" id="copy-title">复制标题</button>
    </div>
    <div id="status" role="status" aria-live="polite"></div>
  </aside>
  <main class="paper">
    <h1 class="title">$title</h1>
    $byline
    <section id="article-body">$body</section>
  </main>
  <script>
    const assets = $assets;
    const article = document.getElementById('article-body');
    const title = document.querySelector('.title');
    const status = document.getElementById('status');

    function selectContents(element) {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(element);
      selection.removeAllRanges();
      selection.addRange(range);
    }

    document.getElementById('copy-body').addEventListener('click', async () => {
      const fragment = article.cloneNode(true);
      for (const img of fragment.querySelectorAll('img')) {
        const src = img.getAttribute('src');
        if (Object.prototype.hasOwnProperty.call(assets, src)) img.src = assets[src];
      }
      try {
        const markup = '<!--StartFragment-->' + fragment.innerHTML + '<!--EndFragment-->';
        const item = new ClipboardItem({
          'text/html': new Blob([markup], {type: 'text/html'}),
          'text/plain': new Blob([article.innerText], {type: 'text/plain'}),
        });
        await navigator.clipboard.write([item]);
        status.textContent = '正文已复制。粘贴后请核对配图和图片描述。';
      } catch (error) {
        selectContents(article);
        status.textContent = '已选中正文，请手动复制。';
      }
    });

    document.getElementById('copy-title').addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(title.textContent);
        status.textContent = '标题已复制。';
      } catch (error) {
        selectContents(title);
        status.textContent = '已选中标题，请手动复制。';
      }
    });
  </script>
</body>
</html>
''')


def _chunks(text: str):
    """沿用原导出脚本的中文断段规则，保留末尾与行内元素之间的空白。"""
    for sentence in re.split(r'(?<=[。！？])', text):
        while len(sentence.strip()) > 92:
            split = sentence.rfind('，', 32, 86)
            if split < 0:
                break
            yield sentence[:split + 1]
            sentence = sentence[split + 1:]
        if sentence.strip():
            yield sentence


def _split_paragraph(document, paragraph):
    # 只拆段首纯文本。最后一段文字和随后的加粗、链接等行内元素留在同一个段落。
    first = paragraph.contents[0] if paragraph.contents else None
    if not isinstance(first, NavigableString):
        return
    parts = list(_chunks(str(first)))
    if len(parts) < 2:
        return
    for chunk in parts[:-1]:
        part = document.new_tag('p')
        part.string = chunk.strip()
        paragraph.insert_before(part)
    first.replace_with(parts[-1].lstrip())


def _format_body(markdown: str):
    document = BeautifulSoup(render.decorate(render.markdown_to_html(markdown)), 'html.parser')
    heading_count = 0
    for node in document.find_all(recursive=False):
        if node.name == 'h2':
            previous = node.find_previous_sibling()
            if heading_count and previous and previous.name != 'hr':
                node.insert_before(document.new_tag('hr'))
            node.name = 'h1'
            number = node.attrs.pop('data-num', None)
            if number:
                node.insert(0, number + ' ')
            heading_count += 1
        elif node.name == 'section' and node.has_attr('data-lead'):
            node.unwrap()
        elif node.name == 'p':
            images = node.find_all('img', recursive=False)
            if images and len(images) == len([child for child in node.contents if str(child).strip()]):
                for image in images:
                    block = document.new_tag('div', attrs={'class': 'pgc-img'})
                    block.append(image.extract())
                    caption = render.caption_of(image.get('alt', ''))
                    if caption:
                        label = document.new_tag('p', attrs={'class': 'pgc-img-caption'})
                        label.string = caption
                        block.append(label)
                    node.insert_before(block)
                node.decompose()
            elif not node.find('img'):
                _split_paragraph(document, node)
    for node in document.select('[data-num], [data-kind]'):
        node.attrs.pop('data-num', None)
        node.attrs.pop('data-kind', None)
    return document


def _clipboard_assets(document, base: Path):
    assets = {}
    warnings = []
    for image in document.find_all('img', src=True):
        src = image['src']
        path = Path(unquote(src))
        if path.is_absolute() and not src.startswith('//'):
            src = image['src'] = path.as_uri()
        else:
            url = urlsplit(src)
            if url.scheme or url.netloc:
                continue
            path = base / unquote(url.path)
        if src in assets:
            continue
        media_type = mimetypes.guess_type(path.name)[0]
        if not path.is_file():
            warnings.append(f'找不到正文图片：{path}')
        elif media_type and media_type.startswith('image/'):
            encoded = base64.b64encode(path.read_bytes()).decode('ascii')
            assets[src] = f'data:{media_type};base64,{encoded}'
        else:
            warnings.append(f'无法识别图片格式，粘贴时请手动上传：{path}')
    return assets, list(dict.fromkeys(warnings))


def build(md_path: Path) -> tuple[Path, Path, list[str]]:
    """在稿件旁生成头条预览和正文 HTML。"""
    md_path = Path(md_path)
    if md_path.suffix.lower() != '.md':
        raise ValueError('头条排版需要 Markdown 稿件，例如 article.layout.md')
    meta, markdown = frontmatter.split(md_path.read_text(encoding='utf-8'))
    title = meta.get('title') or render.infer_title_and_digest(markdown)[0] or naming.base_stem(md_path)
    markdown, _ = render.strip_h1_if_title(markdown, title)
    document = _format_body(markdown)
    if not document.find():
        raise ValueError('稿件没有正文')

    stem = naming.base_stem(md_path)
    preview = md_path.with_name(f'{stem}.toutiao.html')
    fragment = md_path.with_name(f'{stem}.toutiao.body.html')
    for output in (preview, fragment):
        if output.exists():
            with output.open(encoding='utf-8-sig', errors='replace') as previous:
                if MARKER not in previous.read(200):
                    raise FileExistsError(f'{output} 已存在且缺少头条导出标记，已停止覆盖')

    assets, warnings = _clipboard_assets(document, md_path.parent)
    body = document.decode_contents().strip()
    author = meta.get('author')
    page = PAGE.substitute(
        marker=MARKER,
        title=html.escape(title),
        byline=f'<p class="byline">{html.escape(author)}</p>' if author else '',
        body=body,
        assets=json.dumps(assets, ensure_ascii=False).replace('<', '\\u003c'),
    )
    fragment.write_text(f'{MARKER}\n{body}\n', encoding='utf-8')
    preview.write_text(page, encoding='utf-8')
    return preview, fragment, warnings
