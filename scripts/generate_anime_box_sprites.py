# -*- coding: utf-8 -*-
"""
生成大正雾云杉木箱 360 度连续旋转与探头动漫级分镜图层与纹理
"""
import sys
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = REPO_ROOT / "resources" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# 1. 绘制高清大正雾云杉木箱正面与侧面高保真材质
def draw_wooden_box_face(width=160, height=220, angle_deg=0, door_open_pct=0.0):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 透视计算 (沿Y轴旋转产生的宽度压缩与阴影)
    rad = math.radians(angle_deg)
    cos_val = math.cos(rad)
    face_w = max(20, int(width * abs(cos_val)))
    x_offset = (width - face_w) // 2

    # 木质渐变背景
    # 正面/背面是深栗色，侧面是略深木纹
    for y in range(height):
        ratio = y / height
        # 大正雾云杉木色深浅渐变
        r = int(58 * (1 - ratio * 0.45) * (0.8 + 0.2 * abs(cos_val)))
        g = int(32 * (1 - ratio * 0.45) * (0.8 + 0.2 * abs(cos_val)))
        b = int(22 * (1 - ratio * 0.45) * (0.8 + 0.2 * abs(cos_val)))
        draw.line([(x_offset, y), (x_offset + face_w, y)], fill=(r, g, b, 255))

    # 绘制垂直木纹纹理
    grain_step = max(6, int(18 * abs(cos_val)))
    for gx in range(x_offset + 4, x_offset + face_w - 4, grain_step):
        draw.line([(gx, 4), (gx, height - 4)], fill=(20, 10, 6, 120), width=1)
        # 轻微木质高光条
        draw.line([(gx + 1, 4), (gx + 1, height - 4)], fill=(85, 48, 30, 80), width=1)

    # 黑色精铁强化外框
    border_w = max(2, int(4 * abs(cos_val)))
    draw.rectangle([x_offset, 2, x_offset + face_w, height - 2], outline=(15, 10, 8, 255), width=border_w)

    # 4 条横向黑色铁包边强化条带
    bands_y = [int(height * 0.2), int(height * 0.45), int(height * 0.72), int(height * 0.9)]
    band_h = max(3, int(8 * abs(cos_val)))
    for by in bands_y:
        draw.rectangle([x_offset, by, x_offset + face_w, by + band_h], fill=(24, 24, 26, 255))
        draw.line([(x_offset, by), (x_offset + face_w, by)], fill=(55, 55, 60, 255), width=1)
        draw.line([(x_offset, by + band_h), (x_offset + face_w, by + band_h)], fill=(10, 10, 12, 255), width=1)

    # 4 个精铁加固角码与黄铜铆钉
    bracket_size = max(6, int(18 * abs(cos_val)))
    if bracket_size >= 4:
        # 左上、右上、左下、右下
        corners = [
            (x_offset, 2),
            (x_offset + face_w - bracket_size, 2),
            (x_offset, height - 2 - bracket_size),
            (x_offset + face_w - bracket_size, height - 2 - bracket_size)
        ]
        for cx, cy in corners:
            draw.rectangle([cx, cy, cx + bracket_size, cy + bracket_size], fill=(18, 18, 20, 255), outline=(40, 40, 45, 255))
            # 金色铆钉
            rivet_x = cx + bracket_size // 2
            rivet_y = cy + bracket_size // 2
            draw.ellipse([rivet_x - 1, rivet_y - 1, rivet_x + 1, rivet_y + 1], fill=(212, 175, 55, 255))

    # 如果是侧面 (abs(cos_val) < 0.6)，绘制炭治郎同款白色双肩布背带
    if abs(cos_val) < 0.65:
        strap_w = max(3, int(10 * (1 - abs(cos_val))))
        strap_x = x_offset + face_w // 2 - strap_w // 2
        draw.rectangle([strap_x, 10, strap_x + strap_w, height - 10], fill=(235, 230, 225, 240), outline=(160, 150, 140, 255))

    # 如果是正面且门未开
    if abs(cos_val) >= 0.65 and door_open_pct < 0.1:
        # 黄铜门拉手圆环
        ring_x = x_offset + int(face_w * 0.75)
        ring_y = int(height * 0.52)
        draw.ellipse([ring_x - 7, ring_y - 7, ring_x + 7, ring_y + 7], outline=(205, 160, 45, 255), width=2)
        draw.ellipse([ring_x - 2, ring_y - 8, ring_x + 2, ring_y - 4], fill=(245, 200, 65, 255))

    # 顶盖金属手提把手
    handle_w = max(10, int(46 * abs(cos_val)))
    hx1 = (width - handle_w) // 2
    hx2 = hx1 + handle_w
    draw.line([(hx1, 4), (hx1, 0), (hx2, 0), (hx2, 4)], fill=(30, 30, 35, 255), width=3)
    draw.line([(hx1 + 1, 0), (hx2 - 1, 0)], fill=(70, 70, 80, 255), width=1)

    return img

# 2. 生成木箱 360 度旋转 8 帧分镜大图 (Sprite Sheet: 8 帧平铺)
frame_w, frame_h = 160, 220
num_frames = 8
sheet_w = frame_w * num_frames
sheet_img = Image.new("RGBA", (sheet_w, frame_h), (0, 0, 0, 0))

angles = [0, 45, 90, 135, 180, 225, 270, 315]
for idx, ang in enumerate(angles):
    f_img = draw_wooden_box_face(frame_w, frame_h, ang)
    sheet_img.paste(f_img, (idx * frame_w, 0), f_img)

out_sheet_png = MEDIA_DIR / "nezuko_box_spin_sheet.png"
sheet_img.save(out_sheet_png, format="PNG")

# 转换为 WebP
out_sheet_webp = MEDIA_DIR / "nezuko_box_spin_sheet.webp"
sheet_img.save(out_sheet_webp, format="WEBP", quality=92)
print(f"✅ 成功生成 360 度转木箱 8 帧高清分镜序列帧图: {out_sheet_png} ({sheet_w}x{frame_h})")

# 3. 绘制落地砸地冲击波特效帧
fx_size = 200
fx_img = Image.new("RGBA", (fx_size, fx_size), (0, 0, 0, 0))
fx_draw = ImageDraw.Draw(fx_img)

# 绘制金色水墨环状冲击波与气浪
cx, cy = fx_size // 2, fx_size // 2
for r in range(15, 85, 8):
    alpha = int(220 * (1 - (r / 85)))
    fx_draw.ellipse([cx - r * 1.3, cy - r * 0.45, cx + r * 1.3, cy + r * 0.45], outline=(245, 200, 65, alpha), width=3)
# 边缘羽化
fx_img = fx_img.filter(ImageFilter.GaussianBlur(radius=1.5))
fx_png = MEDIA_DIR / "box_impact_shockwave.webp"
fx_img.save(fx_png, format="WEBP", quality=90)
print(f"✅ 成功生成沉重落地冲击波特效图层: {fx_png}")
