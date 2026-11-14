#!/usr/bin/env python3
"""Makes the button-icon sets that replace the game's PlayStation icons (port/src/gs/gs_padicons.c).

    port/tools/pad_icons.py build [xbox|nintendo ...]   port/assets/pad_icons/src/<set>/<label>.png
                                                          -> port/assets/pad_icons/<set>/<PCSX2 name>.png
    port/tools/pad_icons.py placeholder                  writes simple pictures into src/<set>/ (letters on round
                                                          buttons) to try the sets before the real ones are drawn

A picture is named by its button's label in port/assets/pad_icons/names.tsv (cross.png, circle.png, square.png,
triangle.png, triangle_hold.png, circle_prompt.png, l2.png) and has the shape of the game's texture, at any whole
scale: 32 x 32 (or 64, 128 ...) for one icon, 64 x 64 (or 128, 256 ...) for circle_prompt, whose two frames sit side
by side in its top half. Draw inside the game's own area: a face button within x 0..19 and y 4..28 of its 32 x 32
cell (scaled), L2 within x 0..28, y 6..26; what lies to the right of that is overlapped by the next letter.

The icon follows the button's place, not its letter: the bottom button (the game's cross) is A on an Xbox controller
and B on a Nintendo one; right (circle) B / A; left (square) X / Y; top (triangle) Y / X; L2 is LT / ZL.

PNG in, 8-bit RGBA or RGB, not interlaced; the alpha is written as the GS reads it (0x80 = opaque), as every texture
pack has it. No library is needed beyond Python 3.
"""
import os, struct, sys, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ICONS = os.path.join(ROOT, "port", "assets", "pad_icons")
SETS = ("xbox", "nintendo")


def names():
    out = {}
    for line in open(os.path.join(ICONS, "names.tsv"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        label, size, name = line.split("\t")[:3]
        w, h = map(int, size.split("x"))
        out[label] = (w, h, name)
    return out


# ---- PNG
def read_png(path):
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    pos, idat, w = 8, b"", 0
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, color, _, _, inter = struct.unpack(">IIBBBBB", body)
            if depth != 8 or color not in (2, 6) or inter:
                raise ValueError(f"{path}: needs 8-bit RGB or RGBA, not interlaced (depth {depth}, colour type {color})")
            bpp = 4 if color == 6 else 3
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    raw, stride = zlib.decompress(idat), w * bpp
    rows, prev = [], bytearray(stride)
    for y in range(h):
        f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b, c = prev[i], prev[i - bpp] if i >= bpp else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    px = bytearray()
    for line in rows:
        if bpp == 4:
            px += line
        else:
            for i in range(0, stride, 3):
                px += line[i:i + 3] + b"\xff"
    return w, h, px


def write_png(path, w, h, px):
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(px[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


# ---- build
def build(sets):
    table = names()
    for s in sets:
        src, dst = os.path.join(ICONS, "src", s), os.path.join(ICONS, s)
        os.makedirs(dst, exist_ok=True)
        for old in os.listdir(dst):
            if old.endswith(".png"):
                os.remove(os.path.join(dst, old))
        done = 0
        for label, (w, h, name) in table.items():
            path = os.path.join(src, label + ".png")
            if not os.path.exists(path):
                print(f"{s}: no {label}.png (the game's own icon stays)")
                continue
            pw, ph, px = read_png(path)
            if pw * h != ph * w or pw % w or ph % h:
                raise SystemExit(f"{path}: {pw} x {ph} is not a whole scale of {w} x {h}")
            for i in range(3, len(px), 4):
                px[i] = (px[i] * 128 + 127) // 255
            write_png(os.path.join(dst, name + ".png"), pw, ph, px)
            done += 1
        print(f"{s}: {done} icons -> {dst}")


# ---- placeholder pictures (drawn here, letters of a 5 x 7 font)
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}
# by the game's button: (letter, colour) for each set; colours of the letters, the button itself is dark
FACES = {
    "xbox": {"cross": ("A", (0x6C, 0xC0, 0x3A)), "circle": ("B", (0xE0, 0x3C, 0x31)),
             "square": ("X", (0x2F, 0x7B, 0xE0)), "triangle": ("Y", (0xF2, 0xC2, 0x1B)), "l2": ("LT", (0xF0, 0xF0, 0xF0))},
    "nintendo": {"cross": ("B", (0xF0, 0xF0, 0xF0)), "circle": ("A", (0xF0, 0xF0, 0xF0)),
                 "square": ("Y", (0xF0, 0xF0, 0xF0)), "triangle": ("X", (0xF0, 0xF0, 0xF0)), "l2": ("ZL", (0xF0, 0xF0, 0xF0))},
}
S = 4  # pixels per texel of the game's texture


class Canvas:
    def __init__(self, w, h):
        self.w, self.h, self.px = w, h, bytearray(w * h * 4)

    def dot(self, x, y, rgb, a=255):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = (y * self.w + x) * 4
            self.px[o:o + 4] = bytes((*rgb, a))

    def disc(self, cx, cy, r, rgb):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    self.dot(x, y, rgb)

    def rect(self, x0, y0, x1, y1, rgb, r=0):
        for y in range(y0, y1):
            for x in range(x0, x1):
                dx = max(x0 + r - x - 0.5, 0, x + 0.5 - (x1 - r))
                dy = max(y0 + r - y - 0.5, 0, y + 0.5 - (y1 - r))
                if dx * dx + dy * dy <= r * r:
                    self.dot(x, y, rgb)

    def text(self, s, cx, cy, scale, rgb):
        w = len(s) * 6 * scale - scale
        x = cx - w // 2
        for ch in s:
            for gy, row in enumerate(FONT[ch]):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        for yy in range(scale):
                            for xx in range(scale):
                                self.dot(x + gx * scale + xx, cy - 7 * scale // 2 + gy * scale + yy, rgb)
            x += 6 * scale


def face(c, ox, oy, letter, rgb, pressed=False, mark=False):
    """A round button in the game's face-button area of a 32 x 32 cell at (ox, oy) texels: x 0..19, y 4..28."""
    cx, cy, r = (ox + 10) * S, (oy + (18 if pressed else 16)) * S, 9.5 * S
    c.disc(cx, cy, r, (0xE8, 0xE8, 0xE8))                 # rim
    c.disc(cx, cy, r - 1.5 * S, (0x26, 0x26, 0x2A) if not pressed else (0x18, 0x18, 0x1B))
    c.text(letter, cx, cy, 2 * S // 2 if len(letter) > 1 else 3 * S // 2, rgb)
    if mark:                                               # the "hold" mark above, as the game's
        for y in range(5 * S // 2):
            half = (5 * S // 2 - y)
            for x in range(-half, half + 1):
                c.dot(cx + x, (oy + 1) * S + y, (0xF2, 0xE0, 0x10))


def placeholder():
    for s in SETS:
        out = os.path.join(ICONS, "src", s)
        os.makedirs(out, exist_ok=True)
        f = FACES[s]
        for label in ("cross", "circle", "square", "triangle"):
            c = Canvas(32 * S, 32 * S)
            face(c, 0, 0, *f[label])
            write_png(os.path.join(out, label + ".png"), c.w, c.h, c.px)
        c = Canvas(32 * S, 32 * S)
        face(c, 0, 0, *f["triangle"], pressed=True, mark=True)
        write_png(os.path.join(out, "triangle_hold.png"), c.w, c.h, c.px)
        c = Canvas(64 * S, 64 * S)
        face(c, 0, 0, *f["circle"])
        face(c, 32, 0, *f["circle"], pressed=True)
        write_png(os.path.join(out, "circle_prompt.png"), c.w, c.h, c.px)
        c = Canvas(32 * S, 32 * S)
        c.rect(0, 6 * S, 29 * S, 27 * S, (0xE8, 0xE8, 0xE8), r=3 * S)
        c.rect(1 * S, 7 * S, 28 * S, 26 * S, (0x26, 0x26, 0x2A), r=2 * S)
        letter, rgb = f["l2"]
        c.text(letter, 14 * S + S // 2, 16 * S + S // 2, 3 * S // 2, rgb)
        write_png(os.path.join(out, "l2.png"), c.w, c.h, c.px)
        print(f"{s}: placeholder pictures -> {out}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        build(sys.argv[2:] or SETS)
    elif cmd == "placeholder":
        placeholder()
    else:
        print(__doc__)
