"""Generate a polished multi-layer PNGTuber showcase character ('SproutBot Pro')."""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

SIZE = 600
SCALE = 4
W = H = SIZE * SCALE

OUT_DIR = Path(__file__).parent / "test_character"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def new_layer() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def save_layer(img: Image.Image, filename: str) -> Image.Image:
    resized = img.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    resized.save(OUT_DIR / filename, "PNG")
    return resized


def s(val: float) -> int:
    return int(round(val * SCALE))


def main() -> None:
    outline = (34, 38, 56, 255)
    stroke = s(7)

    # 1. Body
    body_img, d = new_layer()
    d.rounded_rectangle(
        [s(210), s(365), s(390), s(545)],
        radius=s(78),
        fill=(95, 168, 255, 255),
        outline=outline,
        width=stroke,
    )
    # Shading stripe on bottom-right of body
    d.arc([s(218), s(375), s(382), s(536)], start=15, end=120, fill=(68, 136, 224, 255), width=s(12))
    # Chest panel
    d.rounded_rectangle(
        [s(255), s(405), s(345), s(478)],
        radius=s(22),
        fill=(228, 242, 255, 255),
        outline=outline,
        width=s(5),
    )
    d.ellipse([s(284), s(425), s(316), s(457)], fill=(116, 224, 146, 255), outline=outline, width=s(4))
    body_final = save_layer(body_img, "01_body.png")

    # 2. Left Arm
    arm_l_img, d = new_layer()
    d.rounded_rectangle(
        [s(154), s(398), s(212), s(492)],
        radius=s(28),
        fill=(95, 168, 255, 255),
        outline=outline,
        width=stroke,
    )
    d.ellipse([s(158), s(454), s(208), s(494)], fill=(228, 242, 255, 255), outline=outline, width=s(5))
    arm_l_final = save_layer(arm_l_img, "02_arm_left.png")

    # 3. Right Arm
    arm_r_img, d = new_layer()
    d.rounded_rectangle(
        [s(388), s(398), s(446), s(492)],
        radius=s(28),
        fill=(95, 168, 255, 255),
        outline=outline,
        width=stroke,
    )
    d.ellipse([s(392), s(454), s(442), s(494)], fill=(228, 242, 255, 255), outline=outline, width=s(5))
    arm_r_final = save_layer(arm_r_img, "03_arm_right.png")

    # 4. Head
    head_img, d = new_layer()
    # Side ear pods
    d.rounded_rectangle([s(124), s(255), s(156), s(320)], radius=s(14), fill=(116, 224, 146, 255), outline=outline, width=s(5))
    d.rounded_rectangle([s(444), s(255), s(476), s(320)], radius=s(14), fill=(116, 224, 146, 255), outline=outline, width=s(5))
    # Main head shell
    d.rounded_rectangle(
        [s(145), s(165), s(455), s(405)],
        radius=s(110),
        fill=(245, 248, 255, 255),
        outline=outline,
        width=stroke,
    )
    # Dark visor screen
    d.rounded_rectangle(
        [s(175), s(198), s(425), s(376)],
        radius=s(76),
        fill=(44, 52, 80, 255),
        outline=outline,
        width=s(5),
    )
    head_final = save_layer(head_img, "04_head.png")

    # 5. Antenna / Sprout (seamless stem + Bezier leaves)
    def bezier(p0, p1, p2, p3, steps=28):
        pts = []
        for i in range(steps + 1):
            t = i / steps
            u = 1.0 - t
            x = (u**3) * p0[0] + 3 * (u**2) * t * p1[0] + 3 * u * (t**2) * p2[0] + (t**3) * p3[0]
            y = (u**3) * p0[1] + 3 * (u**2) * t * p1[1] + 3 * u * (t**2) * p2[1] + (t**3) * p3[1]
            pts.append((s(x), s(y)))
        return pts

    ant_img, d = new_layer()
    # Stem extending slightly inside head top (y=174) up to leaf junction (y=98)
    d.line([s(300), s(174), s(300), s(98)], fill=outline, width=s(12))
    d.line([s(300), s(174), s(300), s(98)], fill=(120, 224, 143, 255), width=s(5))

    left_leaf = bezier((300, 100), (288, 66), (250, 68), (242, 98)) + bezier((242, 98), (262, 114), (286, 110), (300, 100))[1:]
    right_leaf = bezier((300, 100), (312, 62), (352, 64), (360, 94)) + bezier((360, 94), (340, 112), (314, 108), (300, 100))[1:]

    d.polygon(left_leaf, fill=(120, 224, 143, 255))
    d.line(left_leaf, fill=outline, width=s(5), joint="curve")

    d.polygon(right_leaf, fill=(88, 200, 116, 255))
    d.line(right_leaf, fill=outline, width=s(5), joint="curve")

    # Small junction node so stem green and leaf bases join seamlessly
    d.ellipse([s(296), s(96), s(304), s(104)], fill=(120, 224, 143, 255), outline=outline, width=s(3))
    ant_final = save_layer(ant_img, "05_antenna.png")

    # 6. Eyes Open
    eyes_open_img, d = new_layer()
    for cx in (245, 355):
        d.ellipse([s(cx - 24), s(242), s(cx + 24), s(298)], fill=(115, 240, 255, 255))
        d.ellipse([s(cx - 12), s(250), s(cx + 4), s(266)], fill=(255, 255, 255, 255))
        d.ellipse([s(cx + 6), s(274), s(cx + 15), s(283)], fill=(255, 255, 255, 220))
    eyes_open_final = save_layer(eyes_open_img, "06_eyes_open.png")

    # 7. Eyes Closed (happy blink arc)
    eyes_closed_img, d = new_layer()
    for cx in (245, 355):
        d.arc([s(cx - 24), s(256), s(cx + 24), s(292)], start=190, end=350, fill=(115, 240, 255, 255), width=s(8))
    save_layer(eyes_closed_img, "07_eyes_closed.png")

    # 8. Mouth Closed (smile)
    mouth_closed_img, d = new_layer()
    d.arc([s(272), s(304), s(328), s(340)], start=15, end=165, fill=(255, 255, 255, 255), width=s(7))
    mouth_closed_final = save_layer(mouth_closed_img, "08_mouth_closed.png")

    # 9. Mouth Open (talking, tongue clipped cleanly inside mouth cavity)
    mouth_open_img, d = new_layer()
    mouth_box = [s(268), s(284), s(332), s(352)]
    mouth_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mouth_mask).chord(mouth_box, start=0, end=180, fill=255)

    cavity = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dc = ImageDraw.Draw(cavity)
    dc.chord(mouth_box, start=0, end=180, fill=(132, 44, 72, 255))
    dc.ellipse([s(276), s(332), s(324), s(366)], fill=(255, 138, 166, 255))

    mouth_open_img.paste(cavity, (0, 0), mouth_mask)
    d = ImageDraw.Draw(mouth_open_img)
    d.chord(mouth_box, start=0, end=180, fill=None, outline=(255, 255, 255, 255), width=s(5))
    save_layer(mouth_open_img, "09_mouth_open.png")

    # 10. Blush
    blush_img, d = new_layer()
    for cx in (212, 388):
        d.ellipse([s(cx - 22), s(298), s(cx + 22), s(318)], fill=(255, 120, 165, 195))
    blush_final = save_layer(blush_img, "10_blush.png")

    # 11. Cool Sunglasses Visor
    glasses_img, d = new_layer()
    d.line([s(176), s(262), s(424), s(262)], fill=(24, 26, 36, 255), width=s(10))
    for lx1, lx2 in ((198, 286), (314, 402)):
        d.rounded_rectangle([s(lx1), s(238), s(lx2), s(296)], radius=s(14), fill=(20, 22, 32, 245), outline=(255, 210, 80, 255), width=s(5))
        d.line([s(lx1 + 16), s(250), s(lx1 + 36), s(282)], fill=(255, 255, 255, 180), width=s(6))
    save_layer(glasses_img, "11_glasses.png")

    # 12. Angry Brows + Anger Vein Mark
    angry_img, d = new_layer()
    d.line([s(215), s(226), s(270), s(246)], fill=(255, 110, 110, 255), width=s(9))
    d.line([s(385), s(226), s(330), s(246)], fill=(255, 110, 110, 255), width=s(9))
    # Comic anger mark on forehead
    d.arc([s(376), s(196), s(396), s(216)], start=0, end=90, fill=(255, 95, 95, 255), width=s(5))
    d.arc([s(402), s(196), s(422), s(216)], start=90, end=180, fill=(255, 95, 95, 255), width=s(5))
    d.arc([s(376), s(222), s(396), s(242)], start=270, end=360, fill=(255, 95, 95, 255), width=s(5))
    d.arc([s(402), s(222), s(422), s(242)], start=180, end=270, fill=(255, 95, 95, 255), width=s(5))
    save_layer(angry_img, "12_angry_brows.png")

    # Combined preview
    preview = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for layer in (arm_l_final, arm_r_final, body_final, ant_final, head_final, blush_final, eyes_open_final, mouth_closed_final):
        preview.alpha_composite(layer)
    preview.save(OUT_DIR / "preview_assembled.png", "PNG")
    print(f"Generated 13 PNG files in {OUT_DIR}")


if __name__ == "__main__":
    main()
