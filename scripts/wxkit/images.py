"""图片处理：压缩、转 PNG、SVG 渲染成 PNG/GIF。

正文图按格式分流（见 push.upload_body_image）：
  jpg/png         → 正文图接口（超过 1MB 压成 JPEG）
  gif             → 永久素材接口（正文图接口不收 gif，走素材库才能保留动画，≤10MB）
  svg             → 用本机 Edge/Chrome 渲染：带动画的转 GIF，静态的转 PNG（需要 playwright）
  其他（webp 等）  → 转 PNG（需要 Pillow）
"""

import math
from functools import reduce
from io import BytesIO
from pathlib import Path

MAX_IMAGE_BYTES = 10 * 1024 * 1024           # 永久素材（封面、正文 GIF）上限
CONTENT_SUFFIXES = {".jpg", ".jpeg", ".png"}  # 正文图接口只收这两种
CONTENT_MAX_BYTES = 1 * 1024 * 1024           # 正文图接口上限
COVER_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}  # 永久素材接受的格式，webp 会被拒

# SVG 动画转 GIF 的循环时长：各动画周期的最小公倍数 ≤ GIF_MAX_MS 时取它（无缝循环）；
# 否则在 GIF_MIN_MS～GIF_FALLBACK_MS 内挑一个让短周期动画接缝最平滑的时长，
# 周期更长的背景漂移会在接缝处跳一下，这是换取体积的折中。
GIF_FRAME_MS = 60                            # 帧间隔（≈16fps）
GIF_MAX_FRAMES = 300
GIF_MAX_MS = GIF_FRAME_MS * GIF_MAX_FRAMES   # 18s
GIF_MIN_MS = 3000
GIF_FALLBACK_MS = 8000
SVG_MIN_WIDTH = 600                          # 过小的 SVG（图标等）放大到此宽度再渲染


def has_pillow() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def has_playwright() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def compress_image(src: Path, max_bytes: int, out_dir: Path) -> Path:
    """超过 max_bytes 的图片转 JPEG 压缩（有损），返回处理后的路径（没超就是原路径）。"""
    if src.stat().st_size <= max_bytes:
        return src
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError(f"图片 {src.name} 超过 {max_bytes // 1024 // 1024}MB，压缩需要先 pip install Pillow")
    out = out_dir / f"{src.stem}.compressed.jpg"
    img = Image.open(src)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    for q in (85, 75, 65, 50):
        img.save(out, "JPEG", quality=q)
        if out.stat().st_size <= max_bytes:
            return out
    raise RuntimeError(f"图片 {src.name} 压缩后仍超过 {max_bytes // 1024 // 1024}MB")


def convert_to_png(src: Path, out_dir: Path) -> Path:
    """webp/bmp 等正文图接口不收的格式转 PNG。"""
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError(f"图片 {src.name} 要转成 PNG 才能上传，请先 pip install Pillow")
    out = out_dir / f"{src.stem}.png"
    Image.open(src).save(out, "PNG")
    return out


# 在页面里读出 SVG 的显示尺寸和所有动画周期（ms）。
# 周期同时覆盖 SMIL（<animate> 等）和 CSS 动画；alternate 方向的周期按两倍算。
_SVG_PROBE_JS = """() => {
  const root = document.documentElement;
  const len = l => l.baseVal.unitType === SVGLength.SVG_LENGTHTYPE_PERCENTAGE ? 0 : l.baseVal.value;
  let w = len(root.width), h = len(root.height);
  const vb = root.viewBox.baseVal;
  if (vb && vb.width && vb.height) {
    if (!w && !h) { w = vb.width; h = vb.height; }
    else if (!w) w = h * vb.width / vb.height;
    else if (!h) h = w * vb.height / vb.width;
  }
  const durs = [];
  for (const a of document.querySelectorAll('animate, animateTransform, animateMotion, set')) {
    try { durs.push(a.getSimpleDuration() * 1000); } catch (e) {}  // indefinite 会抛异常
  }
  for (const a of document.getAnimations()) {
    const t = a.effect.getComputedTiming();
    durs.push(String(t.direction).startsWith('alternate') ? t.duration * 2 : t.duration);
  }
  return {w: w || 800, h: h || 600, durs: durs.filter(d => isFinite(d) && d > 0)};
}"""

# 暂停所有动画并跳到 t 毫秒，等两帧确保画面已更新
_SVG_SEEK_JS = """t => {
  const root = document.documentElement;
  if (root.pauseAnimations) { root.pauseAnimations(); root.setCurrentTime(t / 1000); }
  for (const a of document.getAnimations()) { a.pause(); a.currentTime = t; }
  return new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
}"""


def pick_loop_ms(durs) -> int:
    """根据各动画周期（ms）选 GIF 循环时长，规则见 GIF_* 常量处的说明。"""
    durs = sorted({round(d / 10) * 10 for d in durs if d >= 10})
    full = reduce(math.lcm, durs)
    if full <= GIF_MAX_MS:
        return full
    short = [d for d in durs if d <= GIF_FALLBACK_MS]

    def seam_error(loop):  # 接缝处各动画的相位误差之和（0 = 完全无缝）
        return sum(abs(loop / d - round(loop / d)) for d in short)

    return min(range(GIF_MIN_MS, GIF_FALLBACK_MS + 1, 10),
               key=lambda loop: (round(seam_error(loop), 3), loop))


def _launch_browser(pw):
    """优先用本机已装的 Edge/Chrome，免去 playwright install 下载浏览器。"""
    for channel in ("msedge", "chrome", None):
        try:
            return pw.chromium.launch(channel=channel)
        except Exception:
            continue
    raise RuntimeError("渲染 SVG 找不到可用的浏览器：请安装 Edge/Chrome，"
                       "或运行 python -m playwright install chromium")


def render_svg(src: Path, out_dir: Path) -> Path:
    """用浏览器渲染 SVG：带动画的输出 GIF，静态的输出 PNG。"""
    try:
        from PIL import Image
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(f"SVG 图片 {src.name} 要先渲染，请先 pip install playwright Pillow")

    with sync_playwright() as pw:
        browser = _launch_browser(pw)
        try:
            page = browser.new_page()
            page.goto(src.resolve().as_uri())
            info = page.evaluate(_SVG_PROBE_JS)
            w, h = math.ceil(info["w"]), math.ceil(info["h"])
            page = browser.new_page(viewport={"width": w, "height": h},
                                    device_scale_factor=max(1, SVG_MIN_WIDTH / w))
            page.goto(src.resolve().as_uri())

            if not info["durs"]:
                out = out_dir / f"{src.stem}.png"
                page.screenshot(path=str(out))
                return out

            loop = pick_loop_ms(info["durs"])
            n = min(GIF_MAX_FRAMES, max(1, round(loop / GIF_FRAME_MS)))
            print(f"  渲染 SVG 动画 {src.name}：{loop / 1000:g}s 循环 / {n} 帧 ...")
            shots = []  # 先存 PNG 字节，300 帧的原始位图会占几百 MB 内存
            for i in range(n):
                page.evaluate(_SVG_SEEK_JS, i * loop / n)
                shots.append(page.screenshot())
        finally:
            browser.close()

    # GIF 帧延时以 10ms 为单位，按累计时刻取整分配，总时长严格等于 loop
    ticks = [round(i * loop / n / 10) * 10 for i in range(n + 1)]
    durations = [b - a for a, b in zip(ticks, ticks[1:])]
    out = out_dir / f"{src.stem}.gif"
    size = 0
    for scale in (1, 0.8, 0.64, 0.5):
        frames = []
        for png in shots:
            img = Image.open(BytesIO(png)).convert("RGB")
            if scale != 1:
                img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
            frames.append(img)
        # 全局调色板（从若干帧拼图里取色）：各帧颜色一致不闪烁；不抖动，平涂插画更干净也更小
        sample = frames[::max(1, n // 8)][:8]
        mosaic = Image.new("RGB", (sample[0].width, sample[0].height * len(sample)))
        for k, f in enumerate(sample):
            mosaic.paste(f, (0, f.height * k))
        palette = mosaic.quantize(colors=255)
        frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
        frames[0].save(out, save_all=True, append_images=frames[1:],
                       duration=durations, loop=0, disposal=1)
        size = out.stat().st_size
        if size <= MAX_IMAGE_BYTES:
            if scale != 1:
                print(f"  [警告] {src.name} 的 GIF 超过 {MAX_IMAGE_BYTES // 1024 // 1024}MB，已缩小到 {scale:.0%}")
            return out
    raise RuntimeError(f"SVG 动画 {src.name} 转成 GIF 后仍有 {size / 1024 / 1024:.1f}MB，"
                       f"超过 {MAX_IMAGE_BYTES // 1024 // 1024}MB")
