#!/usr/bin/env python3
"""Draw entry.png: a one-page newspaper front page summing up 24 Nov 2026.

Tuesday 24 November 2026. 35 stories across 7 regions (EUROPE 9,
AMERICAS 9, ASIA 7, AFRICA 4, MIDDLE EAST 3, OCEANIA 2, WORLD 1),
3 hero + 10 secondary original flat illustrations, a THE DAY IN UTC
timeline strip, a numbers strip of six separate cells where every
number tells a complete mini-story, verification tags on every
illustrated story, a pinned dotted world map whose legend carries the
region counts, a 22-story numbered list, a DATE CHECK box with dated
exclusions plus a "Not yet" tail, and a sources footer. Counts
reconcile: 3 + 10 + 22 = 35; region counts sum to 35; 15 fields.

Every story was verified as having happened, or first been reported,
on Tuesday 24 November 2026, from Reuters, AP, AFP, BBC, Al Jazeera,
Yonhap, Xinhua, UN News, the Kyiv Independent and ChessBase.
Disputed figures are shown as claims, never as fact. Near-misses are
named in the DATE CHECK box, not shown as news. Drawn with Pillow
only; no photos, no copied art. Layout follows the winning newspaper
pattern (date header, timeline, region strip, numbers strip, 3 heroes,
map, numbered list, date check); all content, headlines and drawings
are original to this day.
"""
from PIL import Image, ImageDraw, ImageFont
import math
import os

W = H = 1024
PAPER = (248, 245, 238)
INK = (20, 20, 20)
MUTED = (90, 86, 78)
RED = (166, 27, 27)
NAVY = (18, 34, 64)
RULE = (180, 174, 162)
CARD = (255, 255, 255)
MAPDOT = (158, 168, 180)
GREEN = (46, 134, 74)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def F(path, size):
    return ImageFont.truetype(path, size)


def wrap_text(d, text, fnt, width):
    """Greedy word wrap; returns list of lines that fit width."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if d.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def put_text(d, xy, text, fnt, width, fill, leading=2, limit=None):
    """Draw wrapped text; returns y after last line. Warns on overflow."""
    x, y = xy
    lines = wrap_text(d, text, fnt, width)
    if limit is not None and len(lines) > limit:
        print(f"OVERFLOW: {text[:48]!r} -> {len(lines)} lines (max {limit})")
        lines = lines[:limit]
    for line in lines:
        d.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + leading
    return y


# ---------- small flat-drawing primitives ----------
def sky(d, box, top, mid, bot):
    x0, y0, x1, y1 = box
    for i, c in enumerate((top, mid, bot)):
        d.rectangle([x0, y0 + (y1 - y0) * i // 3,
                     x1, y0 + (y1 - y0) * (i + 1) // 3], fill=c)


def disc(d, cx, cy, r, color):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def puff(d, x, y, s, color):
    d.ellipse([x, y, x + s, y + s * 0.55], fill=color)
    d.ellipse([x + s * 0.5, y - s * 0.25, x + s * 1.5, y + s * 0.4], fill=color)
    d.ellipse([x + s, y, x + s * 2, y + s * 0.55], fill=color)


def block(d, x, y, w, h, color, lit=(255, 214, 90)):
    d.rectangle([x, y, x + w, y + h], fill=color)
    for wy in range(y + 7, y + h - 7, 13):
        for wx in range(x + 5, x + w - 7, 13):
            d.rectangle([wx, wy, wx + 5, wy + 6], fill=lit)


def spark(d, cx, cy, r, color):
    d.polygon([(cx, cy - r), (cx + r * 0.28, cy - r * 0.28), (cx + r, cy),
               (cx + r * 0.28, cy + r * 0.28), (cx, cy + r),
               (cx - r * 0.28, cy + r * 0.28), (cx - r, cy),
               (cx - r * 0.28, cy - r * 0.28)], fill=color)


def fire(d, x, y, s):
    """Flame with base at (x, y), height s."""
    d.polygon([(x - s * 0.4, y), (x, y - s), (x + s * 0.4, y)], fill=(255, 140, 40))
    d.polygon([(x - s * 0.2, y), (x, y - s * 0.55), (x + s * 0.2, y)],
              fill=(255, 220, 120))


def figure(d, x, y, s, skin=(232, 190, 160), shirt=(30, 90, 160)):
    """Small standing person: head, torso, legs."""
    d.ellipse([x - s * 0.28, y, x + s * 0.28, y + s * 0.55], fill=skin)
    d.rectangle([x - s * 0.3, y + s * 0.55, x + s * 0.3, y + s * 1.15], fill=shirt)
    d.rectangle([x - s * 0.22, y + s * 1.15, x - s * 0.02, y + s * 1.7],
                fill=(30, 30, 34))
    d.rectangle([x + s * 0.02, y + s * 1.15, x + s * 0.22, y + s * 1.7],
                fill=(30, 30, 34))


def banner(d, box, text):
    """Red key-number banner across the bottom of a hero picture."""
    x0, y0, x1, y1 = box
    d.rectangle([x0, y1 - 18, x1, y1], fill=RED)
    f = F(SANS_B, 13)
    d.text((x0 + (x1 - x0 - d.textlength(text, font=f)) / 2, y1 - 16),
           text, font=f, fill=(255, 255, 255))


# ---------- hero pictures (310 x 124) ----------
def pic_cikande(d, box):
    """Hero 1: Cikande in daylight — the three-storey candy plant with
    flames from the roof, smoke, a fire truck and a stretcher team."""
    x0, y0, x1, y1 = box
    sky(d, box, (240, 190, 150), (232, 176, 138), (222, 160, 124))
    # three-storey plant
    fx, fy = x0 + 14, y1 - 82
    d.rectangle([fx, fy, fx + 168, y1 - 18], fill=(150, 110, 80))
    d.rectangle([fx, fy - 7, fx + 168, fy], fill=(120, 86, 60))
    for row in range(3):
        for wx in range(fx + 10, fx + 158, 24):
            d.rectangle([wx, fy + 8 + row * 18, wx + 12, fy + 18 + row * 18],
                        fill=(255, 214, 90))
    fire(d, fx + 44, fy - 4, 30)
    fire(d, fx + 128, fy - 4, 24)
    puff(d, fx + 20, y0 + 2, 20, (110, 110, 116))
    puff(d, fx + 84, y0 + 12, 16, (130, 130, 134))
    puff(d, fx + 130, y0 + 0, 14, (120, 120, 124))
    # fire truck at the right
    tx, ty = x0 + 200, y1 - 44
    d.rectangle([tx, ty, tx + 96, ty + 18], fill=(178, 34, 34))
    d.rectangle([tx + 70, ty - 12, tx + 96, ty], fill=(178, 34, 34))
    d.rectangle([tx + 74, ty - 9, tx + 92, ty - 2], fill=(180, 220, 240))
    disc(d, tx + 18, ty + 18, 7, (20, 20, 20))
    disc(d, tx + 78, ty + 18, 7, (20, 20, 20))
    d.rectangle([tx + 8, ty + 4, tx + 58, ty + 10], fill=(240, 240, 238))
    # ladder from the truck to the plant roof
    d.line([tx + 4, ty + 2, fx + 168, fy + 6], fill=(220, 200, 90), width=3)
    # stretcher team at the gate
    figure(d, x0 + 30, y1 - 62, 13, shirt=(220, 180, 60))
    figure(d, x0 + 56, y1 - 62, 13, shirt=(60, 140, 90))
    d.rectangle([x0 + 38, y1 - 44, x0 + 56, y1 - 40], fill=(200, 200, 196))
    d.rectangle([x0, y1 - 18, x1, y1], fill=(110, 88, 66))
    banner(d, box, "26 DEAD, DOZENS MISSING")


def pic_cas(d, box):
    """Hero 2: the AFCON verdict — a floodlit stadium, a gold trophy,
    a ball, and Senegal's green-yellow-red flag."""
    x0, y0, x1, y1 = box
    sky(d, box, (16, 60, 34), (22, 78, 44), (30, 96, 54))
    # floodlit stands: crowd dots in two tiers
    for row, yy in enumerate((y0 + 6, y0 + 20)):
        for cx in range(x0 + 8, x1 - 8, 9):
            col = [(240, 240, 238), (255, 214, 90), (220, 90, 80),
                   (90, 160, 220)][(cx // 9 + row) % 4]
            disc(d, cx, yy, 2, col)
    # pitch with centre circle
    d.rectangle([x0, y1 - 34, x1, y1], fill=(52, 140, 70))
    d.ellipse([x0 + 118, y1 - 66, x0 + 192, y1 - 8], outline=(255, 255, 255),
              width=1)
    d.line([x0 + 155, y1 - 66, x0 + 155, y1 - 8], fill=(255, 255, 255), width=1)
    # gold trophy, centre-left
    tx, ty = x0 + 118, y0 + 34
    d.polygon([(tx, ty), (tx + 34, ty), (tx + 28, ty + 26), (tx + 6, ty + 26)],
              fill=(255, 214, 90))
    d.ellipse([tx - 6, ty + 4, tx + 2, ty + 16], outline=(255, 214, 90), width=2)
    d.ellipse([tx + 32, ty + 4, tx + 40, ty + 16], outline=(255, 214, 90),
              width=2)
    d.rectangle([tx + 13, ty + 26, tx + 21, ty + 38], fill=(255, 214, 90))
    d.rectangle([tx + 6, ty + 38, tx + 28, ty + 44], fill=(255, 214, 90))
    # ball on the pitch
    disc(d, x0 + 216, y1 - 30, 8, (255, 255, 255))
    d.polygon([(x0 + 216, y1 - 35), (x0 + 220, y1 - 30), (x0 + 216, y1 - 25),
               (x0 + 212, y1 - 30)], fill=(30, 30, 30))
    # Senegal flag on a pole at the right
    fx, fy = x0 + 262, y0 + 30
    d.line([fx, fy, fx, y1 - 18], fill=(220, 220, 220), width=2)
    for i, col in enumerate([(0, 136, 70), (255, 214, 0), (200, 40, 40)]):
        d.rectangle([fx + 1 + i * 13, fy, fx + 14 + i * 13, fy + 22], fill=col)
    spark(d, fx + 20, fy + 11, 4, (0, 100, 50))
    # confetti
    for cx, cy, col in [(x0 + 40, y0 + 44, (255, 214, 90)),
                        (x0 + 84, y0 + 58, (240, 240, 238)),
                        (x0 + 250, y0 + 62, (255, 214, 90)),
                        (x0 + 60, y0 + 30, (220, 90, 80))]:
        spark(d, cx, cy, 3, col)
    d.rectangle([x0, y1 - 18, x1, y1], fill=(20, 70, 38))
    banner(d, box, "SENEGAL CHAMPIONS AGAIN")


def pic_dow(d, box):
    """Hero 3: the market board — four ticker rows: name, close level
    and change, green up / red down. No bars: the moves differ by an
    order of magnitude, so bars would lie about the small ones."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(244, 240, 228))
    d.rectangle([x0, y1 - 18, x1, y1], fill=(232, 224, 204))
    rows = [("DOW", "50,019", "+0.85%", GREEN, True),
            ("S&P 500", "7,201", "-0.50%", RED, False),
            ("NASDAQ", "23,734", "-1.48%", RED, False),
            ("CHIPS", "PHLX", "-7.88%", RED, False)]
    for i, (name, lvl, chg, col, up) in enumerate(rows):
        ry = y0 + 8 + i * 24
        d.text((x0 + 14, ry), name, font=F(SANS_B, 13), fill=INK)
        d.text((x0 + 118, ry - 1), lvl, font=F(SERIF_B, 16), fill=INK)
        # small up/down triangle before the change
        tx, ty = x0 + 238, ry + 8
        if up:
            d.polygon([(tx, ty + 5), (tx + 5, ty - 4), (tx + 10, ty + 5)],
                      fill=col)
        else:
            d.polygon([(tx, ty - 4), (tx + 5, ty + 5), (tx + 10, ty - 4)],
                      fill=col)
        d.text((x0 + 252, ry), chg, font=F(SANS_B, 13), fill=col)
        if i < 3:
            d.line([x0 + 12, ry + 20, x1 - 12, ry + 20], fill=(210, 204, 190),
                   width=1)
    banner(d, box, "DOW 50,019 · FIRST CLOSE OVER 50,000")

# ---------- secondary pictures (185 x 58) ----------
def pic_uae(d, box):
    """4: Ras Al Khaimah — a highway, a yellow bus tipped into a grey
    parked truck, debris on the road."""
    x0, y0, x1, y1 = box
    sky(d, box, (214, 200, 170), (200, 186, 158), (186, 170, 144))
    disc(d, x0 + 18, y0 + 10, 8, (255, 214, 90))
    d.rectangle([x0, y1 - 22, x1, y1], fill=(70, 70, 74))
    for wx in range(x0 + 6, x1 - 6, 22):
        d.line([wx, y1 - 11, wx + 10, y1 - 11], fill=(240, 240, 238), width=2)
    # parked grey truck, right
    tx, ty = x0 + 128, y1 - 40
    d.rectangle([tx, ty, tx + 48, ty + 16], fill=(150, 150, 154))
    d.rectangle([tx + 36, ty - 8, tx + 48, ty], fill=(120, 120, 124))
    d.rectangle([tx + 38, ty - 6, tx + 46, ty - 1], fill=(180, 220, 240))
    disc(d, tx + 10, ty + 16, 4, (20, 20, 20))
    disc(d, tx + 38, ty + 16, 4, (20, 20, 20))
    # yellow bus, tipped against the truck
    bx, by = x0 + 52, y1 - 38
    d.polygon([(bx, by + 14), (bx + 66, by + 14), (bx + 72, by + 2),
               (bx + 6, by + 2)], fill=(230, 180, 40))
    for wx in range(bx + 8, bx + 62, 12):
        d.rectangle([wx, by + 5, wx + 7, by + 11], fill=(180, 220, 240))
    disc(d, bx + 14, by + 14, 4, (20, 20, 20))
    disc(d, bx + 58, by + 14, 4, (20, 20, 20))
    # debris and a warning triangle
    for dx, dy in [(x0 + 30, y1 - 26), (x0 + 118, y1 - 26), (x0 + 100, y1 - 30)]:
        disc(d, dx, dy, 2, (200, 60, 40))
    d.polygon([(x0 + 20, y1 - 30), (x0 + 26, y1 - 40), (x0 + 32, y1 - 30)],
              fill=(255, 214, 90))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(52, 52, 56))


def pic_hanoi(d, box):
    """5: Dong Da Street — a hot-pot eatery with a striped awning,
    flames from the doorway, smoke, a parked scooter."""
    x0, y0, x1, y1 = box
    sky(d, box, (232, 196, 150), (224, 182, 138), (212, 166, 124))
    # shopfront with a striped awning
    sx, sy = x0 + 34, y1 - 44
    d.rectangle([sx, sy, sx + 96, y1 - 8], fill=(196, 150, 100))
    for i, col in enumerate([(178, 44, 44), (248, 245, 238)] * 3):
        d.rectangle([sx + i * 16, sy - 8, sx + (i + 1) * 16, sy], fill=col)
    d.rectangle([sx + 34, sy + 12, sx + 62, y1 - 8], fill=(60, 44, 36))
    fire(d, sx + 48, sy + 12, 18)
    fire(d, sx + 84, sy + 20, 12)
    puff(d, sx + 16, y0 + 2, 14, (110, 110, 116))
    puff(d, sx + 60, y0 + 10, 12, (130, 130, 134))
    # a second shop and a scooter
    d.rectangle([x0 + 138, y1 - 34, x0 + 176, y1 - 8], fill=(150, 130, 104))
    d.rectangle([x0 + 144, y1 - 28, x0 + 156, y1 - 18], fill=(180, 220, 240))
    d.line([x0 + 12, y1 - 14, x0 + 26, y1 - 14], fill=(40, 40, 44), width=2)
    disc(d, x0 + 12, y1 - 12, 3, (20, 20, 20))
    disc(d, x0 + 28, y1 - 12, 3, (20, 20, 20))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(120, 104, 84))


def pic_gaza(d, box):
    """6: Gaza at dusk — low blocks, a smoke plume and a burst where
    the strike fell."""
    x0, y0, x1, y1 = box
    sky(d, box, (232, 176, 130), (222, 162, 122), (208, 146, 112))
    disc(d, x0 + 20, y0 + 10, 8, (255, 214, 90))
    for bx, bw, bh in [(x0 + 8, 36, 22), (x0 + 48, 32, 28), (x0 + 140, 38, 20)]:
        d.rectangle([bx, y1 - bh, bx + bw, y1 - 8], fill=(176, 158, 128))
        d.rectangle([bx + 4, y1 - bh - 5, bx + bw - 4, y1 - bh],
                    fill=(146, 128, 100))
    # smoke plume and burst over the middle block
    puff(d, x0 + 84, y0 + 2, 16, (110, 110, 116))
    puff(d, x0 + 104, y0 + 12, 12, (130, 130, 134))
    spark(d, x0 + 96, y0 + 30, 9, (255, 140, 40))
    fire(d, x0 + 96, y1 - 28, 14)
    # a figure carrying a stretcher at the foot of the rubble
    figure(d, x0 + 122, y1 - 40, 12, shirt=(220, 180, 60))
    figure(d, x0 + 142, y1 - 40, 12, shirt=(60, 140, 90))
    d.rectangle([x0 + 128, y1 - 26, x0 + 142, y1 - 22], fill=(200, 200, 196))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(110, 94, 74))


def pic_zap(d, box):
    """7: Zaporizhzhia at night — a five-storey block with its windows
    lit, a dark hole and fire where the strike hit, smoke."""
    x0, y0, x1, y1 = box
    sky(d, box, (14, 22, 46), (24, 36, 68), (36, 52, 92))
    spark(d, x0 + 18, y0 + 8, 3, (255, 255, 255))
    spark(d, x0 + 168, y0 + 12, 3, (255, 255, 255))
    # five-storey block
    fx, fy = x0 + 40, y1 - 46
    d.rectangle([fx, fy, fx + 104, y1 - 8], fill=(10, 16, 32))
    for row in range(4):
        for wx in range(fx + 7, fx + 96, 16):
            d.rectangle([wx, fy + 5 + row * 10, wx + 7, fy + 11 + row * 10],
                        fill=(255, 190, 90))
    # dark hole and fire on the top floor
    d.rectangle([fx + 44, fy, fx + 72, fy + 14], fill=(0, 0, 0))
    fire(d, fx + 58, fy + 2, 16)
    puff(d, fx + 30, y0 + 2, 14, (118, 126, 146))
    # searchlight beam
    d.polygon([(x1 - 6, y1 - 8), (x0 + 150, y0 + 6), (x0 + 160, y0 + 6),
               (x1 - 2, y1 - 8)], fill=(255, 236, 160))
    figure(d, x0 + 22, y1 - 34, 12, shirt=(200, 60, 40))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(12, 18, 34))


def pic_shenzhou(d, box):
    """8: Jiuquan — a rocket climbing past the Tiangong station,
    stars, the Earth curving below."""
    x0, y0, x1, y1 = box
    sky(d, box, (8, 12, 30), (14, 22, 48), (22, 34, 66))
    for sx, sy in [(x0 + 16, y0 + 8), (x0 + 52, y0 + 16), (x0 + 96, y0 + 6),
                   (x0 + 140, y0 + 14), (x0 + 172, y0 + 8)]:
        spark(d, sx, sy, 2, (255, 255, 255))
    # Earth curve at the bottom, kept inside the picture box; drawn
    # before the rocket so the exhaust plume stays in front of it
    d.pieslice([x0 - 20, y1 - 14, x1 + 20, y1 + 14], start=180, end=360,
               fill=(40, 110, 180))
    # Tiangong station: core module and two solar wings
    sx, sy = x0 + 108, y0 + 12
    d.rectangle([sx, sy, sx + 40, sy + 10], fill=(200, 200, 204))
    d.rectangle([sx + 14, sy + 10, sx + 26, sy + 16], fill=(180, 180, 184))
    d.rectangle([sx - 26, sy + 2, sx, sy + 8], fill=(40, 90, 180))
    d.rectangle([sx + 40, sy + 2, sx + 66, sy + 8], fill=(40, 90, 180))
    # rocket climbing, flame below
    rx, ry = x0 + 30, y0 + 26
    d.polygon([(rx + 4, ry - 10), (rx + 10, ry - 18), (rx + 16, ry - 10),
               (rx + 16, ry + 10), (rx + 4, ry + 10)], fill=(240, 240, 238))
    d.rectangle([rx, ry + 2, rx + 4, ry + 8], fill=(178, 44, 44))
    d.rectangle([rx + 16, ry + 2, rx + 20, ry + 8], fill=(178, 44, 44))
    fire(d, rx + 10, ry + 12, 12)
    puff(d, rx - 2, ry + 18, 10, (200, 200, 204))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(16, 32, 56))


def pic_tariff(d, box):
    """9: the tariff threat — a container ship at sea, a big red
    percent board, two small flags."""
    x0, y0, x1, y1 = box
    sky(d, box, (150, 196, 220), (178, 212, 232), (206, 226, 240))
    disc(d, x0 + 18, y0 + 10, 8, (255, 214, 90))
    d.rectangle([x0, y1 - 16, x1, y1], fill=(36, 76, 118))
    for wx in range(x0 + 8, x1 - 8, 26):
        d.line([wx, y1 - 10, wx + 12, y1 - 10], fill=(90, 140, 180), width=1)
    # container ship
    hx, hy = x0 + 18, y1 - 30
    d.polygon([(hx, hy + 12), (hx + 104, hy + 12), (hx + 112, hy + 2),
               (hx, hy + 2)], fill=(24, 24, 28))
    for i, c in enumerate([(200, 60, 50), (40, 120, 90), (220, 160, 40),
                           (36, 84, 160)]):
        d.rectangle([hx + 6 + i * 24, hy - 10, hx + 26 + i * 24, hy + 2],
                    fill=c)
    # percent board on the right
    bx, by = x0 + 138, y0 + 8
    d.rectangle([bx, by, bx + 38, by + 26], fill=(255, 255, 255),
                outline=RED, width=2)
    d.text((bx + 6, by + 4), "%", font=F(SANS_B, 20), fill=RED)
    # two small flags above the board
    d.rectangle([bx, by - 10, bx + 16, by - 2], fill=(178, 44, 44))
    spark(d, bx + 5, by - 6, 2, (255, 214, 90))
    d.rectangle([bx + 20, by - 10, bx + 36, by - 2], fill=(240, 240, 238))
    d.line([bx + 20, by - 10, bx + 36, by - 2], fill=(178, 44, 44), width=1)
    d.rectangle([x0, y1 - 8, x1, y1], fill=(24, 56, 92))


def pic_sanofi(d, box):
    """10: the $41bn deal — a lab bench, flasks, pills and a green
    dollar sign."""
    x0, y0, x1, y1 = box
    sky(d, box, (220, 232, 238), (206, 224, 232), (190, 212, 224))
    # bench
    d.rectangle([x0, y1 - 16, x1, y1], fill=(120, 110, 96))
    # flask with blue liquid
    fx, fy = x0 + 30, y1 - 40
    d.polygon([(fx, fy + 8), (fx + 8, fy + 8), (fx + 8, fy), (fx + 18, fy),
               (fx + 18, fy + 8), (fx + 26, fy + 8), (fx + 32, fy + 24),
               (fx - 6, fy + 24)], fill=(220, 230, 238))
    d.polygon([(fx - 2, fy + 16), (fx + 28, fy + 16), (fx + 32, fy + 24),
               (fx - 6, fy + 24)], fill=(60, 140, 220))
    # test tube
    d.rectangle([x0 + 78, y1 - 44, x0 + 88, y1 - 16], fill=(220, 230, 238))
    d.rectangle([x0 + 79, y1 - 26, x0 + 87, y1 - 16], fill=(46, 134, 74))
    # pills
    for px, py in [(x0 + 108, y1 - 28), (x0 + 122, y1 - 24), (x0 + 114, y1 - 36)]:
        disc(d, px, py, 6, (255, 255, 255))
        d.line([px - 6, py, px + 6, py], fill=(200, 200, 204), width=1)
    # big green dollar sign
    d.text((x0 + 140, y0 + 8), "$", font=F(SANS_B, 34), fill=GREEN)
    d.text((x0 + 162, y1 - 30), "41bn", font=F(SANS_B, 13), fill=INK)
    d.rectangle([x0, y1 - 8, x1, y1], fill=(90, 84, 74))


def pic_pope(d, box):
    """11: the Vatican — an open diary, a candle, a dome behind."""
    x0, y0, x1, y1 = box
    sky(d, box, (232, 214, 180), (224, 202, 168), (212, 188, 152))
    # dome silhouette
    dx = x0 + 140
    d.rectangle([dx, y1 - 34, dx + 34, y1 - 8], fill=(150, 130, 104))
    d.pieslice([dx - 2, y1 - 52, dx + 36, y1 - 28], start=180, end=360,
               fill=(150, 130, 104))
    d.rectangle([dx + 15, y1 - 58, dx + 19, y1 - 52], fill=(150, 130, 104))
    # open diary
    bx, by = x0 + 18, y1 - 40
    d.polygon([(bx, by), (bx + 56, by + 6), (bx + 56, by + 30),
               (bx, by + 24)], fill=(252, 250, 244))
    d.polygon([(bx + 56, by + 6), (bx + 112, by), (bx + 112, by + 24),
               (bx + 56, by + 30)], fill=(248, 246, 238))
    for k in range(3):
        d.line([bx + 8, by + 8 + k * 6, bx + 48, by + 13 + k * 6],
               fill=(120, 116, 106), width=1)
        d.line([bx + 64, by + 13 + k * 6, bx + 104, by + 8 + k * 6],
               fill=(120, 116, 106), width=1)
    # candle with flame
    cx, cy = x0 + 158, y1 - 34
    d.rectangle([cx, cy, cx + 6, y1 - 8], fill=(248, 244, 230))
    fire(d, cx + 3, cy, 10)
    d.rectangle([x0, y1 - 8, x1, y1], fill=(110, 96, 78))


def pic_aus(d, box):
    """12: Canberra — a phone with a shield tick, parliament house
    with its flag mast behind."""
    x0, y0, x1, y1 = box
    sky(d, box, (150, 196, 220), (178, 212, 232), (206, 226, 240))
    # parliament: low building and tall flag mast
    px, py = x0 + 96, y1 - 30
    d.rectangle([px, py, px + 76, y1 - 8], fill=(200, 196, 188))
    d.rectangle([px + 30, py - 8, px + 46, py], fill=(200, 196, 188))
    d.line([px + 38, py - 8, px + 38, y0 + 6], fill=(60, 60, 60), width=2)
    d.rectangle([px + 39, y0 + 6, px + 57, y0 + 16], fill=(36, 84, 160))
    for k in range(4):
        d.rectangle([px + 6 + k * 18, py + 6, px + 12 + k * 18, py + 16],
                    fill=(160, 156, 148))
    # phone with a shield
    phx, phy = x0 + 14, y0 + 6
    d.rectangle([phx, phy, phx + 52, phy + 44], fill=(20, 20, 24))
    d.rectangle([phx + 3, phy + 3, phx + 49, phy + 41], fill=(90, 150, 220))
    d.polygon([(phx + 26, phy + 8), (phx + 42, phy + 12), (phx + 42, phy + 26),
               (phx + 26, phy + 38), (phx + 10, phy + 26),
               (phx + 10, phy + 12)], fill=(255, 255, 255))
    d.line([phx + 18, phy + 24, phx + 24, phy + 30, phx + 34, phy + 16],
           fill=GREEN, width=2)
    d.rectangle([x0, y1 - 8, x1, y1], fill=(90, 110, 130))


def pic_rohingya(d, box):
    """13: the return — a ship on the sea, a plane above, a coastline."""
    x0, y0, x1, y1 = box
    sky(d, box, (150, 196, 220), (178, 212, 232), (206, 226, 240))
    disc(d, x0 + 18, y0 + 10, 8, (255, 214, 90))
    # coastline on the right
    d.polygon([(x0 + 148, y1 - 8), (x0 + 185, y1 - 8), (x0 + 185, y1 - 30),
               (x0 + 168, y1 - 22)], fill=(120, 150, 90))
    d.rectangle([x0, y1 - 16, x1, y1], fill=(36, 76, 118))
    for wx in range(x0 + 8, x1 - 8, 26):
        d.line([wx, y1 - 10, wx + 12, y1 - 10], fill=(90, 140, 180), width=1)
    # ship
    hx, hy = x0 + 22, y1 - 30
    d.polygon([(hx, hy + 12), (hx + 88, hy + 12), (hx + 96, hy + 2),
               (hx, hy + 2)], fill=(24, 24, 28))
    d.rectangle([hx + 12, hy - 8, hx + 30, hy + 2], fill=(240, 240, 238))
    d.rectangle([hx + 36, hy - 6, hx + 58, hy + 2], fill=(200, 60, 50))
    d.rectangle([hx + 62, hy - 6, hx + 82, hy + 2], fill=(220, 160, 40))
    # plane above
    cx, cy = x0 + 140, y0 + 12
    d.ellipse([cx - 12, cy - 3, cx + 12, cy + 3], fill=(255, 255, 255))
    d.polygon([(cx - 4, cy), (cx + 2, cy - 8), (cx + 6, cy)], fill=(255, 255, 255))
    d.polygon([(cx - 4, cy), (cx + 2, cy + 8), (cx + 6, cy)], fill=(255, 255, 255))
    d.line([cx + 12, cy, cx + 20, cy + 4], fill=(255, 255, 255), width=2)
    d.rectangle([x0, y1 - 8, x1, y1], fill=(24, 56, 92))


PICS = {1: pic_cikande, 2: pic_cas, 3: pic_dow, 4: pic_uae, 5: pic_hanoi,
        6: pic_gaza, 7: pic_zap, 8: pic_shenzhou, 9: pic_tariff,
        10: pic_sanofi, 11: pic_pope, 12: pic_aus, 13: pic_rohingya}

# ---------- story data ----------
# (num, region, topic, source, tag, headline, summary)
HEROES = [
    (1, "ASIA", "INDONESIA", "XINHUA", "CONFIRMED",
     "Cikande fire toll rises to 26",
     "26 body bags out; dozens still missing after Saturday's blaze."),
    (2, "AFRICA", "SPORT", "AP", "OFFICIAL",
     "CAS restores Senegal's AFCON title",
     "Unanimous ruling: 1–0 win over Morocco stands; CAF's forfeit award cancelled."),
    (3, "AMERICAS", "MARKETS", "REUTERS", "OFFICIAL",
     "Dow tops 50,000 for first time",
     "Tech fell as chips slid; consumer confidence jumped to 103.3."),
]
SECONDARY = [
    (4, "MIDDLE EAST", "UAE", "REUTERS", "CONFIRMED",
     "UAE bus crash kills 13",
     "41 aboard hit a parked truck in Ras Al Khaimah; 14 hurt."),
    (5, "ASIA", "VIETNAM", "REUTERS", "CONFIRMED",
     "Hanoi blast kills 6",
     "Suspected gas leak at 8 a.m.; 10 hurt on Dong Da Street."),
    (6, "MIDDLE EAST", "GAZA", "REUTERS", "CONFIRMED",
     "Hamas chief killed in Gaza",
     "Naeem Abu Nahel and 6 others killed, medics say."),
    (7, "EUROPE", "UKRAINE", "REUTERS", "CONFIRMED",
     "Zaporizhzhia kills 2",
     "Overnight strike on flats; 40 hurt, 4 of them children."),
    (8, "ASIA", "CHINA", "AP", "OFFICIAL",
     "Shenzhou 24 crew named",
     "First foreign astronaut to Tiangong: Pakistan's Zeeshan Ali."),
    (9, "AMERICAS", "USA", "REUTERS", "REPORTED",
     "US plans higher tariffs",
     "Section 301 findings on China imminent; no decision yet."),
    (10, "EUROPE", "BUSINESS", "REUTERS", "CONFIRMED",
     "Sanofi–Insmed $41bn deal",
     "$175 a share, a 17.5% premium; deal agreed."),
    (11, "EUROPE", "VATICAN", "REUTERS", "CONFIRMED",
     "Pope's diary published",
     "Notes 1992–2024; visions of the Devil; a 2-year crisis."),
    (12, "OCEANIA", "AUSTRALIA", "AP", "OFFICIAL",
     "Tech giants face 5% fines",
     "Duty-of-care deal clinched; Senate votes Wednesday."),
    (13, "ASIA", "MALAYSIA", "AL JAZEERA", "OFFICIAL",
     "6,500 Rohingya to return",
     "Returns start in December, by ship and plane."),
]
LISTED = [
    "KADIZ alert: Russian jets off Ulleungdo",
    "Hasina plans return to Bangladesh 16 Dec",
    "German Ifo business climate 90.6",
    "Bank of Japan leans to December rate rise",
    "UK warns of Russian sabotage threat",
    "NATO chief: defend against space threats",
    "Iraq PM orders Kurdistan takeover",
    "Fighting traps Ebola responders in Ituri",
    "DR Congo plane missing; rebels claim kill",
    "Germany first to access Ukraine's Delta",
    "Court clears Army to blast lead azide",
    "Dymer toll rises to 12",
    "Trump pardons turkeys Freedom, Feathers",
    "Giuliani receives Medal of Freedom",
    "Chess title opens with a draw in Geneva",
    "US consumer confidence jumps to 103.3",
    "Vaccine group to buy 1.5m Ebola doses",
    "UN killer-robot talks end without deal",
    "Australia science prize shared by two",
    "Lula backs second fiscal package",
    "Migrant caravan sets out from Mexico",
    "PAHO: Mexico, US, Bolivia lose measles-free status",
]
REGIONS = [("EUROPE", 9, (36, 84, 160)), ("AMERICAS", 9, (14, 128, 128)),
           ("ASIA", 7, (122, 62, 158)), ("AFRICA", 4, (46, 134, 74)),
           ("MIDDLE EAST", 3, (178, 44, 44)), ("OCEANIA", 2, (214, 122, 26)),
           ("WORLD", 1, (96, 96, 100))]
FIELDS = ["DISASTER", "SPORT", "MARKETS", "CONFLICT", "SCIENCE", "BUSINESS",
          "CULTURE", "TECHNOLOGY", "MIGRATION", "DEFENCE", "POLITICS",
          "ECONOMY", "HEALTH", "DIPLOMACY", "LAW"]
# numbers strip: six cells, two rows of three; each a complete mini-story
NUMBERS = [("26", "dead as the Cikande fire toll rises"),
           ("50,019", "Dow's first close above 50,000"),
           ("13", "killed in the UAE bus–truck crash"),
           ("$41bn", "Sanofi's agreed price for Insmed"),
           ("6,500", "Rohingya Malaysia will return"),
           ("1.5m", "Ebola vaccine doses to be bought")]
# timeline strip: seven timed events across the day (UTC)
TIMELINE = [("01:00", "Hanoi blast kills 6"),
            ("02:00", "Zaporizhzhia hit kills 2"),
            ("06:12", "Pope diary published"),
            ("10:07", "DR Congo plane missing"),
            ("12:19", "Migrant caravan sets out"),
            ("13:29", "Cikande toll rises to 26"),
            ("21:00", "Dow closes above 50,000")]
# map pins: (num, x, y); red for 1-3, navy for 4-13
PINS = [(1, 272, 895), (2, 198, 878), (3, 96, 848), (4, 242, 858),
        (5, 278, 878), (6, 224, 872), (7, 212, 845), (8, 282, 853),
        (9, 106, 861), (10, 190, 845), (11, 200, 850), (12, 300, 924),
        (13, 268, 888)]
LAND = [  # ellipses (x0, y0, x1, y1) forming a coarse dotted world map
    (45, 826, 170, 880), (175, 824, 200, 837), (130, 883, 185, 940),
    (185, 837, 235, 862), (190, 865, 250, 929), (235, 830, 310, 880),
    (255, 880, 285, 897), (265, 912, 305, 935), (180, 840, 192, 851),
    (300, 844, 312, 862), (235, 862, 265, 894), (190, 855, 230, 869),
    (165, 840, 195, 858), (205, 865, 235, 887), (185, 826, 205, 844),
    (308, 928, 318, 940),
]


def kicker(d, x, y, num, region, topic, src, tag, width, size=10):
    """Left: 'N · REGION · TOPIC'; right: 'SOURCE · TAG'. Drops topic if tight."""
    f, sf = F(SANS_B, size), F(SANS, size - 1)
    right = f"{src} · {tag}"
    full = f"{num} · {region} · {topic}"
    if d.textlength(full, font=f) + d.textlength(right, font=sf) + 12 > width:
        full = f"{num} · {region}"
    d.text((x, y), full, font=f, fill=RED)
    d.text((x + width - d.textlength(right, font=sf), y), right, font=sf,
           fill=MUTED)


def kicker2(d, x, y, num, region, topic, src, tag, width):
    """Two-line kicker for the narrow secondary cards: line 1 is the
    number/region/topic, line 2 is the source and verification tag."""
    d.text((x, y), f"{num} · {region} · {topic}", font=F(SANS_B, 9), fill=RED)
    d.text((x, y + 11), f"{src} · {tag}", font=F(SANS, 8), fill=MUTED)


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    M = 24
    X1 = W - M

    # ---- header ----
    d.rectangle([M, 14, 116, 136], fill=RED)
    d.text((30, 20), "NOV", font=F(SANS_B, 22), fill=(255, 255, 255))
    d.text((30, 44), "24", font=F(SERIF_B, 52), fill=(255, 255, 255))
    d.text((30, 104), "TUE 2026", font=F(SANS_B, 13), fill=(255, 255, 255))
    d.text((132, 18), "THE DAY IN WORLD NEWS", font=F(SANS_B, 15), fill=RED)
    d.text((132, 38), "Tuesday 24 November 2026", font=F(SERIF_B, 44), fill=INK)
    d.text((132, 98),
           "Everything on this page happened, or was first reported, on Tuesday 24 November 2026.",
           font=F(SANS, 15), fill=MUTED)
    for i, line in enumerate(["35 STORIES", "7 REGIONS", "15 FIELDS"]):
        f = F(SANS_B, 19)
        d.text((X1 - d.textlength(line, font=f), 24 + i * 26), line, font=f, fill=INK)
    d.line([M, 142, X1, 142], fill=INK, width=2)

    # ---- timeline strip: seven timed events across the day ----
    ty = 147
    d.text((M, ty), "THE DAY IN UTC", font=F(SANS_B, 11), fill=RED)
    tw = (X1 - M) / 7
    for i, (t, lab) in enumerate(TIMELINE):
        cx = M + i * tw
        d.text((cx, ty + 13), t, font=F(SANS_B, 12), fill=RED)
        put_text(d, (cx, ty + 26), lab, F(SANS, 9), tw - 8, INK, leading=1,
                 limit=1)
    d.line([M, 182, X1, 182], fill=RULE, width=1)

    # ---- region strip ----
    y0, y1 = 186, 210
    total_w = X1 - M
    widths = [max(64, int(total_w * n / 35)) for _, n, _ in REGIONS]
    scale = total_w / sum(widths)
    widths = [int(w * scale) for w in widths]
    widths[-1] += total_w - sum(widths)
    x = M
    for (name, n, col), w in zip(REGIONS, widths):
        d.rectangle([x, y0, x + w - 1, y1], fill=col)
        label = f"{name} {n}"
        f = F(SANS_B, 13)
        if d.textlength(label, font=f) <= w - 8:
            d.text((x + (w - d.textlength(label, font=f)) / 2, y0 + 6),
                   label, font=f, fill=(255, 255, 255))
        else:
            f2 = F(SANS_B, 10)
            d.text((x + (w - d.textlength(name, font=f2)) / 2, y0 + 2),
                   name, font=f2, fill=(255, 255, 255))
            d.text((x + (w - d.textlength(str(n), font=f2)) / 2, y0 + 13),
                   str(n), font=f2, fill=(255, 255, 255))
        x += w

    # ---- numbers strip: six cells, two rows of three ----
    ny = 216
    for row in range(2):
        for col in range(3):
            num, lab = NUMBERS[row * 3 + col]
            cx = M + col * 325
            cy = ny + row * 23
            f1, f2 = F(SANS_B, 16), F(SANS, 11)
            d.text((cx, cy), num, font=f1, fill=RED)
            lx = cx + d.textlength(num + " ", font=f1)
            d.text((lx, cy + 3), lab, font=f2, fill=INK)
            end = lx + d.textlength(lab, font=f2)
            if end > X1:
                print(f"OVERFLOW: numbers cell {num!r} ends at {end}, edge {X1}")
    d.line([M, 266, X1, 266], fill=RULE, width=1)

    # ---- hero stories ----
    hy, hh = 272, 228
    hw, gap = 312, 20
    for i, (num, region, topic, src, tag, head, summ) in enumerate(HEROES):
        x = M + i * (hw + gap)
        d.rectangle([x, hy, x + hw, hy + hh], fill=CARD, outline=RULE, width=1)
        PICS[num](d, (x + 1, hy + 1, x + hw - 1, hy + 125))
        ky = hy + 132
        kicker(d, x + 10, ky, num, region, topic, src, tag, hw - 20, size=11)
        y2 = put_text(d, (x + 10, ky + 17), head, F(SERIF_B, 21),
                      hw - 20, INK, leading=1, limit=2)
        put_text(d, (x + 10, y2 + 3), summ, F(SANS, 12),
                 hw - 20, MUTED, leading=1, limit=2)

    # ---- secondary stories: 5 columns x 2 rows ----
    sy = 508
    cw, cgap = 187, 10
    ch = 140
    for i, (num, region, topic, src, tag, head, summ) in enumerate(SECONDARY):
        col, row = i % 5, i // 5
        x = M + col * (cw + cgap)
        yy = sy + row * (ch + 8)
        d.rectangle([x, yy, x + cw, yy + ch], fill=CARD, outline=RULE, width=1)
        PICS[num](d, (x + 1, yy + 1, x + cw - 1, yy + 57))
        kicker2(d, x + 8, yy + 61, num, region, topic, src, tag, cw - 16)
        y2 = put_text(d, (x + 8, yy + 86), head, F(SERIF_B, 14),
                      cw - 16, INK, leading=1, limit=2)
        put_text(d, (x + 8, y2 + 2), summ, F(SANS, 10),
                 cw - 16, MUTED, leading=1, limit=2)

    # ---- map + list ----
    my = 804
    d.line([M, my - 4, X1, my - 4], fill=INK, width=2)
    d.text((M, my), "WHERE IT HAPPENED", font=F(SANS_B, 14), fill=INK)
    d.text((330, my), "ALSO ON TUESDAY 24 NOVEMBER — 22 MORE STORIES",
           font=F(SANS_B, 14), fill=INK)
    # dotted map
    mx0, my0, mx1, my1 = M, my + 20, 318, 940
    for gx in range(mx0, mx1, 6):
        for gy in range(my0, my1, 6):
            cx, cy = gx + 3, gy + 3
            if any((cx - (a + c) / 2) ** 2 / (((c - a) / 2) ** 2) +
                   (cy - (b + e) / 2) ** 2 / (((e - b) / 2) ** 2) <= 1
                   for a, b, c, e in LAND):
                d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=MAPDOT)
    for num, px, py in PINS:
        col = RED if num <= 3 else NAVY
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=col,
                  outline=(255, 255, 255), width=1)
        f = F(SANS_B, 9 if num < 10 else 8)
        t = str(num)
        d.text((px - d.textlength(t, font=f) / 2, py - 5), t, font=f,
               fill=(255, 255, 255))
    d.text((M, 944),
           "Europe 9 · Americas 9 · Asia 7 · Africa 4 · Middle East 3 · Oceania 2 · World 1",
           font=F(SANS, 9), fill=MUTED)
    # numbered list, two columns of 11
    lf = F(SANS, 11)
    for i, item in enumerate(LISTED):
        col = i // 11
        row = i % 11
        lx = 330 + col * 336
        ly = my + 22 + row * 10.5
        num = 14 + i
        d.text((lx, ly), f"{num}", font=F(SANS_B, 11), fill=RED)
        d.text((lx + 22, ly), item, font=lf, fill=INK)

    # ---- date check box ----
    by0 = 954
    d.rectangle([M, by0, X1, by0 + 48], outline=RED, width=2)
    d.text((M + 10, by0 + 3), "DATE CHECK", font=F(SANS_B, 12), fill=RED)
    d.text((M + 108, by0 + 3),
           "Left out on purpose — each was first reported before Tuesday:",
           font=F(SANS, 12), fill=INK)
    dc = F(SANS, 9)
    d.text((M + 10, by0 + 16),
           "Nvidia +31.5% · Cikande toll 24 · Dymer toll 11 · Merkury sunk · EU 22nd sanctions · FIFA 2031/2035 · Sparta II docks · Nepal $1.62bn · Ahmadi flogging (all 23 Nov)",
           font=dc, fill=MUTED)
    d.text((M + 10, by0 + 26),
           "Trump halts Iowa blast · Pennsylvania measles 9th death · India rice duty (23 Nov) · COP31 collapse · Kyiv bridges (22 Nov) · 'El Chapo' · Peru quake · EU–Indonesia pact (21 Nov) · Cyclone Akvan (20 Nov)",
           font=dc, fill=MUTED)
    d.text((M + 10, by0 + 36),
           "Not yet: Shenzhou 24 launch (Wed) · Iowa detonation (Wed) · Chess game 2 (Wed) · Australia tech vote (Wed) · Hasina returns 16 Dec · Rohingya returns start (Dec)",
           font=dc, fill=RED)
    # ---- footer ----
    d.text((M, 1006),
           "Tags: CONFIRMED — two or more outlets · OFFICIAL — on the record · REPORTED — one outlet",
           font=F(SANS, 8), fill=MUTED)
    d.text((M, 1015),
           "Sources: Reuters · AP · AFP · BBC · Al Jazeera · Yonhap · Xinhua",
           font=F(SANS, 8), fill=MUTED)
    attr = "Original drawings. Claims are attributed, not stated as fact."
    d.text((X1 - d.textlength(attr, font=F(SANS, 8)), 1015), attr,
           font=F(SANS, 8), fill=MUTED)

    total = len(HEROES) + len(SECONDARY) + len(LISTED)
    rsum = sum(n for _, n, _ in REGIONS)
    print(f"counts: heroes {len(HEROES)} + secondary {len(SECONDARY)} + listed {len(LISTED)} = {total}; regions sum {rsum}; fields {len(FIELDS)}")
    assert total == 35 and rsum == 35, "counts do not reconcile to 35"
    assert len(FIELDS) == 15, "field count wrong"

    img.save("entry.png", optimize=True)
    print("saved entry.png", img.size, "bytes:", os.path.getsize("entry.png"))


if __name__ == "__main__":
    main()
