#!/usr/bin/env python3
"""Render the ONE DAY news image for 22 November 2026.

1024x1024 PNG, fully drawn in PIL (no downloaded photos): masthead, stat
strip, region tabs, 3 illustrated lead cards, a real-coastline world map
(Natural Earth 110m, TopoJSON) with numbered pins, 8 small story cards, a
date-check box and a sources line. Liberation Serif/Sans only (real glyphs).
"""
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1024, 1024
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
ASSETS = os.path.join(WORK, "assets")

PAPER = (247, 242, 231)
INK = (20, 33, 61)
RED = (180, 35, 24)
GREY = (90, 96, 110)
LIGHT_LINE = (216, 205, 180)
CARD = (255, 255, 255)
OCEAN = (216, 228, 238)
LAND = (220, 207, 169)
LAND_EDGE = (138, 125, 92)

REGION_COLORS = {
    "EUROPE": (31, 78, 121),
    "MIDDLE EAST": (180, 35, 24),
    "AMERICAS": (46, 125, 50),
    "ASIA-PACIFIC": (106, 27, 154),
    "AFRICA": (230, 81, 0),
    "SPORT": (0, 105, 92),
    "WORLD": (69, 90, 100),
}


def font(name, size):
    return ImageFont.truetype(
        "/usr/share/fonts/truetype/liberation/%s" % name, size)


SERIF = lambda s: font("LiberationSerif-Bold.ttf", s)          # noqa: E731
SERIF_R = lambda s: font("LiberationSerif-Regular.ttf", s)     # noqa: E731
SANS = lambda s: font("LiberationSans-Regular.ttf", s)         # noqa: E731
SANS_B = lambda s: font("LiberationSans-Bold.ttf", s)          # noqa: E731


def wrap(text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if fnt.getlength(trial) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_text_block(d, xy, lines, fnt, fill, leading=None):
    x, y = xy
    lh = leading if leading is not None else int(fnt.size * 1.22)
    for ln in lines:
        d.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


# ---------------------------------------------------------------- map data
def load_land():
    """Decode Natural Earth 110m land polygons from TopoJSON."""
    with open(os.path.join(ASSETS, "countries-110m.json")) as fh:
        topo = json.load(fh)
    arcs = topo["arcs"]
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    pts = []
    for arc in arcs:
        x, y = 0, 0
        out = []
        for dx, dy in arc:
            x += dx
            y += dy
            out.append((x * sx + tx, y * sy + ty))
        pts.append(out)
    polys = []
    land = topo["objects"]["land"]
    geoms = land["geometries"] if land["type"] == "GeometryCollection" else [land]
    for geom in geoms:
        if geom["type"] == "Polygon":
            polygons = [geom["arcs"]]
        else:  # MultiPolygon
            polygons = geom["arcs"]
        for poly in polygons:
            for ring in poly:
                ring_pts = []
                for ai in ring:
                    seg = pts[ai] if ai >= 0 else list(reversed(pts[~ai]))
                    if ring_pts and ring_pts[-1] == seg[0]:
                        seg = seg[1:]
                    ring_pts.extend(seg)
                if len(ring_pts) > 2:
                    polys.append(ring_pts)
    return polys


def lonlat_to_xy(lon, lat, box):
    """Equirectangular: lon -180..180, lat -60..85 -> box (x, y, w, h)."""
    x0, y0, w, h = box
    scale = w / 360.0
    cx = x0 + (lon + 180.0) * scale
    cy = y0 + (85.0 - lat) * scale
    return cx, cy


# ---------------------------------------------------------------- lead art
def art_cop31(d, x, y, w, h):
    # sky bands
    for i in range(h):
        t = i / h
        r = int(191 + (232 - 191) * t)
        g = int(227 + (243 - 227) * t)
        b = int(224 + (238 - 224) * t)
        d.line([(x, y + i), (x + w, y + i)], fill=(r, g, b))
    # sun + rays
    sx, sy = x + w - 62, y + 42
    for k in range(8):
        a = math.pi * k / 4
        d.line([(sx + 34 * math.cos(a), sy + 34 * math.sin(a)),
                (sx + 46 * math.cos(a), sy + 46 * math.sin(a))],
               fill=(232, 131, 58), width=3)
    d.ellipse([sx - 26, sy - 26, sx + 26, sy + 26], fill=(232, 131, 58))
    # mountains
    d.polygon([(x, y + h), (x + 70, y + 62), (x + 140, y + h)], fill=(47, 110, 110))
    d.polygon([(x + 90, y + h), (x + 190, y + 48), (x + w, y + h)], fill=(31, 84, 92))
    # sea
    d.rectangle([x, y + h - 34, x + w, y + h], fill=(46, 125, 140))
    for wy in (y + h - 26, y + h - 14):
        for wx in range(0, w, 26):
            d.arc([x + wx, wy - 5, x + wx + 24, wy + 7], 180, 360,
                  fill=(255, 255, 255), width=2)
    # conference hall + flags
    d.rectangle([x + 18, y + h - 78, x + 108, y + h - 34], fill=(255, 255, 255))
    d.polygon([(x + 18, y + h - 78), (x + 63, y + h - 96), (x + 108, y + h - 78)],
              fill=(180, 35, 24))
    for i, c in enumerate([(31, 78, 121), (46, 125, 50), (232, 131, 58)]):
        fx = x + 122 + i * 16
        d.line([(fx, y + h - 66), (fx, y + h - 34)], fill=INK, width=2)
        d.polygon([(fx, y + h - 66), (fx + 12, y + h - 62), (fx, y + h - 58)],
                  fill=c)


def art_ukraine(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(16, 30, 51))
    import random
    rnd = random.Random(7)
    for _ in range(46):
        px, py = x + rnd.randint(4, w - 4), y + rnd.randint(4, h - 60)
        r = rnd.choice([1, 1, 2])
        d.ellipse([px - r, py - r, px + r, py + r],
                  fill=(255, 255, 255) if rnd.random() > 0.3 else (200, 210, 230))
    # low fire band behind the skyline + small bursts at building bases
    d.rectangle([x, y + h - 10, x + w, y + h], fill=(200, 90, 40))
    # skyline
    for bx, bw, bh in [(8, 34, 52), (48, 26, 70), (80, 40, 44), (126, 28, 64),
                       (160, 36, 50), (202, 30, 72), (238, 34, 46), (278, 26, 58)]:
        d.rectangle([x + bx, y + h - bh, x + bx + bw, y + h], fill=(8, 14, 26))
        for wy in range(y + h - bh + 8, y + h - 6, 12):
            for wx in range(x + bx + 6, x + bx + bw - 5, 11):
                if rnd.random() > 0.45:
                    d.rectangle([wx, wy, wx + 4, wy + 6], fill=(255, 200, 80))
    # drones + tracer arcs (all boxes kept inside the panel)
    for dx, dy, s in [(150, 34, 1.0), (210, 58, 0.8), (96, 62, 0.7)]:
        cx, cy = x + dx, y + dy
        d.ellipse([cx - 9 * s, cy - 3 * s, cx + 9 * s, cy + 3 * s], fill=(10, 10, 14))
        d.line([(cx - 14 * s, cy), (cx + 14 * s, cy)], fill=(10, 10, 14), width=2)
        d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(255, 60, 40))
    d.arc([x + 60, y + 10, x + 260, y + 130], 200, 340, fill=(255, 120, 60), width=2)
    d.arc([x + 120, y + 0, x + 300, y + 120], 210, 330, fill=(255, 200, 80), width=2)


def art_bahrain(d, x, y, w, h):
    for i in range(h):
        t = i / h
        r = int(232 + (217 - 232) * t)
        g = int(201 + (168 - 201) * t)
        b = int(143 + (108 - 143) * t)
        d.line([(x, y + i), (x + w, y + i)], fill=(r, g, b))
    sx, sy = x + w - 56, y + 36
    d.ellipse([sx - 22, sy - 22, sx + 22, sy + 22], fill=(245, 222, 160))
    # dunes
    d.polygon([(x, y + h), (x + 90, y + 92), (x + 200, y + h)], fill=(200, 155, 94))
    d.polygon([(x + 120, y + h), (x + 230, y + 84), (x + w, y + h)], fill=(180, 132, 74))
    # base: buildings + radar dome
    d.rectangle([x + 16, y + h - 52, x + 66, y + h - 18], fill=(74, 62, 48))
    d.rectangle([x + 74, y + h - 44, x + 108, y + h - 18], fill=(96, 82, 62))
    d.pieslice([x + 118, y + h - 58, x + 158, y + h - 18], 180, 360, fill=(120, 104, 80))
    d.line([(x + 138, y + h - 58), (x + 138, y + h - 70)], fill=(120, 104, 80), width=2)
    for wx in range(x + 22, x + 62, 12):
        d.rectangle([wx, y + h - 44, wx + 5, y + h - 36], fill=(255, 200, 80))
    # missile arcs + smoke (all boxes kept inside the panel)
    d.arc([x + 150, y + 10, x + 310, y + 120], 200, 320, fill=(255, 255, 255), width=3)
    d.arc([x + 190, y + 0, x + 310, y + 100], 210, 330, fill=(255, 255, 255), width=2)
    for px, py, r in [(238, 44, 4), (252, 58, 3), (214, 30, 3)]:
        d.ellipse([x + px - r, y + py - r, x + px + r, y + py + r], fill=(255, 255, 255))
    # impact puffs
    for px, py in [(40, 118), (250, 128)]:
        d.ellipse([x + px - 12, y + py - 8, x + px + 12, y + py + 8], fill=(232, 120, 50))
        d.ellipse([x + px - 6, y + py - 12, x + px + 6, y + py + 2], fill=(255, 200, 80))


LEADS = [
    ("COP31 — ANTALYA", "COP31 ends with no fossil fuels in the deal",
     "Nearly 200 nations approve a 10-page pact that never mentions oil, coal "
     "or gas — and admits the 1.5°C goal is out of reach.",
     "REUTERS", art_cop31),
    ("UKRAINE — KYIV", "186 drones in one night over Ukraine",
     "Russia launches 186 drones from six bases; Ukraine downs 161, but strikes "
     "still hit 18 sites. The raid runs into Sunday morning.",
     "UKRAINIAN AIR FORCE", art_ukraine),
    ("BAHRAIN", "Iran's missiles hit US bases in Bahrain",
     "Two waves of drones and missiles strike four American bases; air defences "
     "intercept most of them. One industrial site burns; no one hurt.",
     "BAHRAIN GOVERNMENT", art_bahrain),
]

SMALL = [
    ("SINALOA, MEXICO", "AMERICAS", "'El Chapo Isidro' captured",
     "Troops seize FBI most-wanted cartel boss Fausto Isidro Meza Flores; "
     "11 die in the raid."),
    ("NIGERIA", "AFRICA", "Boat of mourners capsizes; 24 dead",
     "A boat carrying funeral mourners goes down in southern Nigeria."),
    ("HONG KONG", "ASIA-PACIFIC", "Hong Kong votes for its next leader's electors",
     "856 candidates contest 723 seats on the Election Committee; turnout hits "
     "95.6% by 3pm."),
    ("WASHINGTON", "AMERICAS", "FBI crime database breached",
     "Hackers breach the FBI crime database; Trump calls it \"not good\". "
     "Gun checks paused."),
    ("MARKETS", "WORLD", "AI sell-off shakes markets",
     "S&P 500 falls 3.7%, Nikkei 5.06%; Nvidia drops 14% as the SEC probes its "
     "accounting."),
    ("GULF OF FINLAND", "EUROPE", "Russian ship still burning after drone strike",
     "Sanctioned ship Sparta II is hit by two drones off Finland; "
     "16 crew evacuated."),
    ("GAZA", "MIDDLE EAST", "Strikes continue; aid vehicle hit",
     "Three Palestinians die as an aid vehicle is struck; food aid trickles in."),
    ("TEHRAN", "MIDDLE EAST", "Power cuts begin as war hits the grid",
     "Iran starts rolling blackouts today, up to two hours a day, "
     "as strikes damage its grid."),
]

# (number, lon, lat, city, text, nudge dx, dy)
PINS = [
    (12, 4.35, 50.85, "Brussels", "EU and Indonesia sign a trade deal after 10 years of talks.", 2, -28),
    (13, 174.78, -41.29, "Wellington", "Pant's 128 lifts India to 629/6 against New Zealand.", 0, 0),
    (14, 12.57, 55.68, "Copenhagen", "Denmark expels a Russian attaché over a rapper plot.", 28, -24),
    (15, -47.88, -15.79, "Brasília", "Bolsonaro in intensive care with a bowel obstruction.", 0, 0),
    (16, 42.95, 14.80, "Hodeida", "Houthis strike after a Saudi-led coalition operation.", -14, 10),
    (17, 35.50, 33.89, "Beirut", "Lebanon's Aoun blames Israel and Iran for threats.", 24, -12),
    (18, -0.13, 51.51, "London", "UK and EU strike deals; Burnham eyes rejoining.", -32, -18),
    (19, -77.04, 38.91, "Washington", "Trump tells contractors to report Congress.", -16, 14),
    (20, -74.01, 40.71, "New York", "Amazon nears a $7.5B deal for Israeli AI start-up Decart.", 16, -14),
    (21, 7.69, 45.07, "Turin", "Alcaraz to face Zverev for the ATP Finals title.", -14, 28),
    (22, -0.19, 51.48, "London", "Leeds stun Chelsea 4–1 at Stamford Bridge.", -26, 22),
    (23, -118.24, 34.05, "Los Angeles", "GTA 6 sets a $3.79B launch-day record.", 0, 0),
    (24, 6.14, 46.20, "Geneva", "UN nations reach a tentative deal on autonomous weapons.", 18, 28),
    (25, 56.50, 26.60, "Strait of Hormuz", "Pugh braves the strait as a tanker is hit.", 16, -6),
    (26, 144.96, -37.81, "Melbourne", "70 years since the 1956 Olympics opened.", -16, -14),
    (27, 2.35, 48.86, "Paris", "France reach the Nations Championship final.", -42, -2),
    (28, 0.12, 51.50, "London", "England beat New Zealand 37–12, a record win.", 30, -18),
    (29, -9.14, 38.72, "Lisbon", "Thousands march in the rain over living costs.", 0, 0),
    (30, 35.21, 31.77, "Jerusalem", "Eisenkot invites Likud to coalition talks starting today.", 22, 16),
    (31, 149.13, -35.28, "Canberra", "Marles rejects a US report on AUKUS subs.", -18, 14),
    (32, 151.21, -33.87, "Sydney", "Teen gamer, 16, helps the FBI rescue a missing girl.", 18, -12),
    (33, 13.40, 52.52, "Berlin", "IG Metall calls 23,000 car and shipyard workers out.", 36, 0),
]

TABS = [("EUROPE", 8), ("MIDDLE EAST", 6), ("AMERICAS", 5),
        ("ASIA-PACIFIC", 3), ("AFRICA", 1), ("SPORT", 4), ("WORLD", 6)]

STATS = [
    ("≈200", "nations approve the COP31 pact in Antalya"),
    ("161", "of 186 drones downed over Ukraine overnight"),
    ("24", "dead as a boat of mourners capsizes in Nigeria"),
    ("95.6%", "turnout in Hong Kong's Election Committee vote"),
]


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    MX = 28  # side margin

    # ---- masthead
    d.text((MX, 18), "ONE DAY", font=SERIF(58), fill=INK)
    d.text((W - MX, 22), "SUNDAY 22 NOVEMBER 2026", font=SANS_B(19),
           fill=RED, anchor="ra")
    d.text((W - MX, 48), "THE WORLD IN ONE PAGE", font=SANS_B(11),
           fill=GREY, anchor="ra")
    d.rectangle([MX, 82, W - MX, 85], fill=RED)
    d.line([(MX, 88), (W - MX, 88)], fill=INK, width=1)

    # ---- subline
    sub = "33 STORIES  •  7 REGIONS  •  EVERY ONE DATED"
    d.text((W // 2, 96), sub, font=SANS_B(14), fill=INK, anchor="ma")

    # ---- stat strip
    sy, sh = 116, 40
    sw = (W - 2 * MX - 3 * 8) // 4
    for i, (num, cap) in enumerate(STATS):
        x0 = MX + i * (sw + 8)
        d.rectangle([x0, sy, x0 + sw, sy + sh], fill=CARD, outline=LIGHT_LINE)
        d.text((x0 + 10, sy + 4), num, font=SERIF(24), fill=RED)
        tw = SANS(10).getlength(num) if False else SERIF(24).getlength(num)
        cap_lines = wrap(cap, SANS(10), sw - tw - 22)
        draw_text_block(d, (x0 + 14 + tw, sy + 6), cap_lines[:2], SANS(10),
                        INK, leading=12)

    # ---- region tabs
    ty = 164
    x = MX
    for name, count in TABS:
        label = "%s %d" % (name, count)
        fnt = SANS_B(11)
        tw = fnt.getlength(label) + 18
        col = REGION_COLORS[name]
        d.rounded_rectangle([x, ty, x + tw, ty + 20], radius=10,
                            fill=(255, 255, 255), outline=col, width=1)
        d.text((x + 9, ty + 4), label, font=fnt, fill=col)
        x += tw + 6

    # ---- lead cards
    ly, lh = 192, 268
    cw = (W - 2 * MX - 2 * 12) // 3
    for i, (kicker, head, body, src, art) in enumerate(LEADS):
        x0 = MX + i * (cw + 12)
        d.rectangle([x0, ly, x0 + cw, ly + lh], fill=CARD, outline=LIGHT_LINE)
        art(d, x0 + 1, ly + 1, cw - 2, 132)
        d.text((x0 + 10, ly + 140), kicker, font=SANS_B(10), fill=RED)
        hl = wrap(head, SERIF(19), cw - 20)
        y = draw_text_block(d, (x0 + 10, ly + 156), hl[:2], SERIF(19), INK,
                            leading=21)
        bl = wrap(body, SANS(12), cw - 20)
        draw_text_block(d, (x0 + 10, y + 4), bl[:3], SANS(12), INK, leading=14)
        d.text((x0 + 10, ly + lh - 16), "SOURCE: " + src, font=SANS_B(9),
               fill=GREY)

    # ---- map + list
    my, mh = 470, 288
    d.text((MX, my), "THE WORLD ON SUNDAY", font=SERIF(16), fill=INK)
    d.text((MX, my + 20), "Every pin is a story — numbers match the key",
           font=SANS(11), fill=GREY)
    map_box = (MX, my + 42, 520, mh - 42)
    d.rectangle([map_box[0], map_box[1],
                 map_box[0] + map_box[2], map_box[1] + map_box[3]],
                fill=OCEAN, outline=LIGHT_LINE)
    land = load_land()
    for poly in land:
        pts = [lonlat_to_xy(lon, lat, map_box) for lon, lat in poly]
        if len(pts) > 2:
            d.polygon(pts, fill=LAND, outline=LAND_EDGE)
    # graticule
    for lon in range(-150, 181, 30):
        gx, _ = lonlat_to_xy(lon, 85, map_box)
        d.line([(gx, map_box[1]), (gx, map_box[1] + map_box[3])],
               fill=(255, 255, 255), width=1)
    for lat in (-30, 0, 30, 60):
        _, gy = lonlat_to_xy(0, lat, map_box)
        d.line([(map_box[0], gy), (map_box[0] + map_box[2], gy)],
               fill=(255, 255, 255), width=1)
    # pins
    pin_font = SANS_B(9)
    for num, lon, lat, city, text, ndx, ndy in PINS:
        px, py = lonlat_to_xy(lon, lat, map_box)
        cx, cy = px + ndx, py + ndy
        if ndx or ndy:
            d.line([(px, py), (cx, cy)], fill=GREY, width=1)
        r = 8
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED,
                  outline=(255, 255, 255), width=1)
        d.text((cx, cy - 1), str(num), font=pin_font, fill=(255, 255, 255),
               anchor="mm")

    # list (key), two columns
    lx = MX + 520 + 14
    lw = W - MX - lx
    d.text((lx, my), "ALSO ON SUNDAY 22 NOVEMBER", font=SERIF(14), fill=INK)
    col_w = (lw - 12) // 2
    item_font = SANS(10)
    city_font = SANS_B(10)
    num_font = SANS_B(10)
    row_h = 23
    for idx, (num, lon, lat, city, text, ndx, ndy) in enumerate(PINS):
        col = idx // 11
        row = idx % 11
        ix = lx + col * (col_w + 12)
        iy = my + 22 + row * row_h
        d.text((ix, iy), str(num), font=num_font, fill=RED)
        d.text((ix + 20, iy), city + " — ", font=city_font, fill=INK)
        cw2 = city_font.getlength(city + " — ")
        first = wrap(text, item_font, col_w - 20 - cw2)
        d.text((ix + 20 + cw2, iy), first[0], font=item_font, fill=INK)
        rest = text[len(first[0]):].strip()
        if rest:
            second = wrap(rest, item_font, col_w - 20)
            d.text((ix + 20, iy + 11), second[0], font=item_font, fill=INK)

    # ---- small cards
    sy2, sh2 = 770, 88
    scw = (W - 2 * MX - 3 * 10) // 4
    for i, (kicker, region, head, body) in enumerate(SMALL):
        col_i, row_i = i % 4, i // 4
        x0 = MX + col_i * (scw + 10)
        y0 = sy2 + row_i * (sh2 + 8)
        col = REGION_COLORS[region]
        d.rectangle([x0, y0, x0 + scw, y0 + sh2], fill=CARD, outline=LIGHT_LINE)
        d.rectangle([x0, y0, x0 + scw, y0 + 3], fill=col)
        d.text((x0 + 8, y0 + 8), kicker + "  ·  " + region, font=SANS_B(9),
               fill=col)
        hl = wrap(head, SERIF(14), scw - 16)
        y = draw_text_block(d, (x0 + 8, y0 + 22), hl[:2], SERIF(14), INK,
                            leading=16)
        bl = wrap(body, SANS(10), scw - 16)
        draw_text_block(d, (x0 + 8, y + 2), bl[:2], SANS(10), INK, leading=12)

    # ---- date check box
    dy = 956
    d.rectangle([MX, dy, W - MX, dy + 34], outline=RED, width=1)
    d.text((MX + 10, dy + 4),
           "DATE CHECK — Wires read to 00:50 UTC, Sunday 22 November 2026. Every story here was",
           font=SANS_B(10), fill=INK)
    d.text((MX + 10, dy + 18),
           "reported on 22 November, or on Saturday night and confirmed in Sunday's wires. Left out as other days' news: the Shenzhen summit (19 Nov).",
           font=SANS(10), fill=INK)

    # ---- sources + footer
    d.text((W // 2, 996),
           "SOURCES: Reuters · BBC · Al Jazeera · DW · Straits Times · Sky News · CNA · ABC Australia · Times of India · Guardian · Kyiv Independent · IANS · Ukrainian Air Force",
           font=SANS(9), fill=GREY, anchor="ma")
    d.text((W // 2, 1012), "ONE DAY — SUNDAY 22 NOVEMBER 2026  •  ONE PAGE",
           font=SANS_B(9), fill=INK, anchor="ma")

    out = os.path.join(HERE, "entry.png")
    img.save(out, "PNG", optimize=True)
    print("saved", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
