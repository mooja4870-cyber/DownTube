"""DownTube 런처 아이콘 생성 — 빨간 그라데이션 배경 + 흰색 재생▶/다운로드↓ 글리프.

산출물 (android/res/):
  mipmap-*/ic_launcher.png  레거시 아이콘 (둥근 모서리 + 그라데이션 + 글리프)
  mipmap-*/ic_bg.png        어댑티브 아이콘 배경 (그라데이션 정사각형)
  mipmap-*/ic_fg.png        어댑티브 아이콘 전경 (투명 배경 글리프, 중앙 안전영역)
"""

from pathlib import Path

from PIL import Image, ImageDraw

RES = Path(__file__).resolve().parent / "res"
TOP = (255, 105, 92)      # 위쪽 밝은 빨강
BOTTOM = (205, 24, 14)    # 아래쪽 진한 빨강
WHITE = (255, 255, 255, 255)
S = 4                     # 슈퍼샘플 배율 (안티앨리어싱)

LEGACY = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
ADAPTIVE = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}


def gradient(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / max(size - 1, 1)
        c = tuple(round(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))
        d.line([(0, y), (size, y)], fill=c + (255,))
    return img


def draw_glyph(draw: ImageDraw.ImageDraw, cx: float, cy: float, w: float) -> None:
    """중심 (cx, cy), 폭 w 박스 안에 재생 삼각형 + 다운로드 화살표를 그린다."""
    h = w * 1.12
    top, left = cy - h / 2, cx - w / 2
    # 재생 삼각형 (약간 오른쪽으로 시각 보정)
    t_h = h * 0.50
    t_w = w * 0.48
    t_cx = cx + w * 0.015
    draw.polygon(
        [(t_cx - t_w / 2, top), (t_cx - t_w / 2, top + t_h), (t_cx + t_w / 2, top + t_h / 2)],
        fill=WHITE,
    )
    # 다운로드 화살표: 세로 줄기 + 화살촉 + 받침 바
    stem_w = w * 0.13
    stem_top = top + h * 0.58
    head_top = top + h * 0.74
    head_w = w * 0.38
    tip_y = top + h * 0.90
    draw.rectangle([cx - stem_w / 2, stem_top, cx + stem_w / 2, head_top + 2], fill=WHITE)
    draw.polygon([(cx - head_w / 2, head_top), (cx + head_w / 2, head_top), (cx, tip_y)], fill=WHITE)
    bar_h = h * 0.075
    bar_w = w * 0.78
    draw.rounded_rectangle(
        [cx - bar_w / 2, top + h - bar_h, cx + bar_w / 2, top + h], radius=bar_h / 2, fill=WHITE
    )


def legacy_icon(size: int) -> Image.Image:
    big = size * S
    img = gradient(big)
    d = ImageDraw.Draw(img)
    draw_glyph(d, big / 2, big * 0.485, big * 0.46)
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, big - 1, big - 1], radius=big * 0.22, fill=255)
    img.putalpha(mask)
    return img.resize((size, size), Image.LANCZOS)


def fg_icon(size: int) -> Image.Image:
    big = size * S
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_glyph(d, big / 2, big * 0.49, big * 0.34)  # 안전영역(중앙 61%) 안에 배치
    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    for dpi, size in LEGACY.items():
        out = RES / f"mipmap-{dpi}"
        out.mkdir(parents=True, exist_ok=True)
        legacy_icon(size).save(out / "ic_launcher.png")
    for dpi, size in ADAPTIVE.items():
        out = RES / f"mipmap-{dpi}"
        gradient(size).save(out / "ic_bg.png")
        fg_icon(size).save(out / "ic_fg.png")
    anydpi = RES / "mipmap-anydpi-v26"
    anydpi.mkdir(parents=True, exist_ok=True)
    (anydpi / "ic_launcher.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '  <background android:drawable="@mipmap/ic_bg"/>\n'
        '  <foreground android:drawable="@mipmap/ic_fg"/>\n'
        "</adaptive-icon>\n",
        encoding="utf-8",
    )
    print("아이콘 생성 완료:", RES)


if __name__ == "__main__":
    main()
