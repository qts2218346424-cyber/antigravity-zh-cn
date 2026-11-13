#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成内置示例材质包的图片资源与预览图 (build_skin_assets.py)

用法：
    python scripts/build_skin_assets.py            # 重新生成全部内置包资源
    python scripts/build_skin_assets.py --preview  # 只为 resources/skins/* 重新渲染 preview.png

预览图是根据 skin.json 的配色与背景合成的“迷你工作台”示意图，
自制材质包也可以用 --preview --dir <包目录> 生成预览。
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

REPO_ROOT = Path(__file__).resolve().parent.parent
SKINS = REPO_ROOT / "resources" / "skins"
MEDIA = REPO_ROOT / "resources" / "media"


def _hex(c: str, default=(30, 30, 30)) -> tuple:
    try:
        c = c.strip().lstrip("#")
        if len(c) in (3, 4):
            c = "".join(ch * 2 for ch in c[:3])
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return default


def make_starfield(path: Path, size=(1280, 800)):
    rnd = random.Random(7)
    w, h = size
    im = Image.new("RGB", size)
    px = im.load()
    for y in range(h):
        t = y / h
        for x in range(0, w):
            px[x, y] = (int(8 + 20 * t), int(12 + 18 * t), int(32 + 50 * (1 - t)))
    d = ImageDraw.Draw(im)
    for _ in range(420):
        x, y = rnd.randrange(w), rnd.randrange(h)
        r = rnd.choice((1, 1, 1, 2))
        b = rnd.randint(150, 255)
        d.ellipse((x, y, x + r, y + r), fill=(b, b, min(255, b + 20)))
    glow = Image.new("RGB", size, (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((w * 0.55, h * 0.1, w * 1.1, h * 0.75), fill=(40, 90, 160))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    im = ImageChops.add(im, glow)
    im.save(path, "WEBP", quality=80)


def _petal(d: ImageDraw.ImageDraw, cx, cy, r, ang, color):
    pts = []
    for i in range(24):
        t = i / 24 * 2 * math.pi
        rr = r * (0.55 + 0.45 * math.cos(t)) if math.cos(t) > 0 else r * 0.55
        x = cx + rr * math.cos(t + ang) * 1.0
        y = cy + rr * 0.6 * math.sin(t + ang)
        pts.append((x, y))
    d.polygon(pts, fill=color)


def make_sakura(path: Path, size=(1280, 800)):
    rnd = random.Random(11)
    w, h = size
    im = Image.new("RGB", size, (255, 246, 249))
    d = ImageDraw.Draw(im, "RGBA")
    for _ in range(140):
        cx, cy = rnd.randrange(w), rnd.randrange(h)
        r = rnd.randint(8, 26)
        pink = rnd.choice([(248, 187, 208, 170), (244, 143, 177, 150), (252, 228, 236, 200)])
        _petal(d, cx, cy, r, rnd.random() * math.pi, pink)
    branch = (120, 80, 90, 160)
    d.line([(0, 90), (260, 140), (420, 120), (560, 200)], fill=branch, width=9)
    d.line([(260, 140), (330, 60)], fill=branch, width=6)
    for _ in range(18):
        cx, cy = rnd.randint(200, 600), rnd.randint(40, 230)
        for k in range(5):
            _petal(d, cx, cy, 14, k * 2 * math.pi / 5, (246, 160, 190, 220))
        d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(200, 60, 100, 255))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    im.save(path, "WEBP", quality=80)


def make_asanoha(path: Path, size=(640, 640), fg=(236, 120, 160), bg=(58, 18, 34)):
    """麻叶纹（祢豆子和服纹样）平铺图"""
    w, h = size
    im = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(im)
    s = 80
    hh = s * math.sqrt(3) / 2
    rows = int(h / hh) + 2
    cols = int(w / s) + 2
    for r in range(rows):
        for c in range(cols):
            ox = c * s + (s / 2 if r % 2 else 0)
            oy = r * hh
            tri = [(ox, oy), (ox + s, oy), (ox + s / 2, oy + hh)]
            cx = sum(p[0] for p in tri) / 3
            cy = sum(p[1] for p in tri) / 3
            for p in tri:
                d.line([p, (cx, cy)], fill=fg, width=2)
            d.polygon(tri, outline=fg)
    im.save(path, "WEBP", quality=85)


def make_sakura_svg(path: Path):
    petals = []
    for k in range(5):
        ang = k * 72
        petals.append(f'<ellipse cx="8" cy="4.2" rx="2.6" ry="3.8" transform="rotate({ang} 8 8)"/>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
           f'<g fill="#e86a92">{"".join(petals)}</g><circle cx="8" cy="8" r="1.6" fill="#fff3f7"/></svg>')
    path.write_text(svg, encoding="utf-8")


def render_preview(pack_dir: Path, out: Path | None = None, size=(360, 220)):
    m = json.loads((pack_dir / "skin.json").read_text(encoding="utf-8"))
    c = m.get("colors", {})
    bg = _hex(c.get("background", "#1e1e1e"))
    fg = _hex(c.get("foreground", "#d4d4d4"))
    accent = _hex(c.get("accent", "#3794ff"))
    side = _hex(c.get("sidebar", c.get("background", "#252526")))
    act = _hex(c.get("activityBar", c.get("sidebar", "#333333")))
    title = _hex(c.get("titleBar", c.get("sidebar", "#333333")))
    status = _hex(c.get("statusBar", c.get("accent", "#007acc")))
    w, h = size
    im = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 18), fill=title)
    for i, col in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((8 + i * 14, 5, 16 + i * 14, 13), fill=col)
    d.rectangle((0, 18, 26, h - 14), fill=act)
    for i in range(4):
        d.rounded_rectangle((7, 28 + i * 24, 19, 40 + i * 24), 3, fill=accent if i == 0 else fg)
    d.rectangle((26, 18, 110, h - 14), fill=side)
    for i in range(8):
        d.rectangle((36, 30 + i * 16, 36 + 40 + (i * 13) % 30, 36 + i * 16), fill=fg if i != 2 else accent)
    rnd = random.Random(3)
    for i in range(11):
        x = 124 + (i % 3) * 10
        ln = rnd.randint(60, 190)
        col = [accent, fg, _hex(c.get("muted", "#888888"))][i % 3]
        d.rectangle((x, 30 + i * 15, min(w - 12, x + ln), 36 + i * 15), fill=col)
    d.rectangle((0, h - 14, w, h), fill=status)
    bgs = m.get("background")
    bgs = bgs if isinstance(bgs, list) else ([bgs] if bgs else [])
    for b in bgs:
        p = pack_dir / b.get("image", "")
        if not p.is_file():
            continue
        tex = Image.open(p).convert("RGB")
        target = b.get("target", "window")
        box = {"window": (0, 0, w, h), "editor": (110, 18, w, h - 14), "sidebar": (26, 18, 110, h - 14)}.get(target, (0, 0, w, h))
        bw, bh = box[2] - box[0], box[3] - box[1]
        tex = tex.resize((bw, bh))
        if b.get("blur"):
            tex = tex.filter(ImageFilter.GaussianBlur(b["blur"] / 3))
        region = im.crop(box)
        alpha = min(1.0, float(b.get("opacity", 0.15)) * 1.6)
        im.paste(Image.blend(region, tex, alpha), box[:2])
    pet = m.get("pet") or {}
    sprite = pet.get("sprite")
    char = pet.get("character")
    src = pack_dir / sprite if sprite else (MEDIA / "nezuko_chibi_pet.png" if char == "nezuko" else
                                             MEDIA / "little_prince_pet.png" if char == "prince" else None)
    if src and src.is_file():
        pim = Image.open(src).convert("RGBA")
        pim.thumbnail((70, 90))
        im.paste(pim, (w - pim.width - 8, h - 14 - pim.height), pim)
    (out or pack_dir / "preview.png").parent.mkdir(parents=True, exist_ok=True)
    im.save(out or pack_dir / "preview.png", "PNG", optimize=True)


def build_all():
    (SKINS / "midnight-dark").mkdir(parents=True, exist_ok=True)
    (SKINS / "sakura-light" / "icons").mkdir(parents=True, exist_ok=True)
    (SKINS / "nezuko-bamboo").mkdir(parents=True, exist_ok=True)
    make_starfield(SKINS / "midnight-dark" / "starfield.webp")
    make_sakura(SKINS / "sakura-light" / "sakura.webp")
    make_sakura_svg(SKINS / "sakura-light" / "icons" / "sakura.svg")
    make_asanoha(SKINS / "nezuko-bamboo" / "asanoha.webp")
    src = MEDIA / "nezuko_basket.webp"
    if src.is_file():
        (SKINS / "nezuko-bamboo" / "nezuko_basket.webp").write_bytes(src.read_bytes())
    for d in sorted(SKINS.iterdir()):
        if (d / "skin.json").is_file():
            render_preview(d)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="只渲染预览图")
    ap.add_argument("--dir", help="指定材质包目录（配合 --preview）")
    a = ap.parse_args()
    if a.preview:
        targets = [Path(a.dir)] if a.dir else [d for d in sorted(SKINS.iterdir()) if (d / "skin.json").is_file()]
        for t in targets:
            render_preview(t)
            print("preview:", t / "preview.png")
    else:
        build_all()
        print("内置材质包资源已生成:", SKINS)
    sys.exit(0)
