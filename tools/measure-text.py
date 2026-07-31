#!/usr/bin/env python3
"""Measure exact text widths in the font embedded in a .lottie file.

Used when laying out Lottie animations (see AGENTS.md section 12): node labels must fit
their boxes and edge labels must fit the gap between nodes. Guessing leads to overflow
that only shows up visually in Creator; this reports the real pixel width.

Pure stdlib -- parses the TrueType `cmap` (format 4), `hmtx`, `head` and `hhea` tables
directly. Widths are the sum of glyph advances and ignore kerning, which for these fonts
makes the result a hair conservative: a string reported as fitting will fit.

Examples
--------
  # widths at 15px
  tools/measure-text.py --size 15 "Message Queue (Kafka/Redis)" "Send Update"

  # check they fit a 160px node box (needs >=10px padding each side)
  tools/measure-text.py --size 17 --box 160 "Client Device" "Load Balancer"

  # check an edge label fits the 190px gap between two nodes
  tools/measure-text.py --size 15 --box 190 "Throughput: RPS"

  # try several sizes to find one that fits
  tools/measure-text.py --size 17 --size 16 --size 15 --box 160 "WebSocket Server"

  # centre-anchor x for a right-aligned item (e.g. the branding watermark)
  tools/measure-text.py --size 14 --canvas 1200 --margin 40 "learn.sauravgpt.in"

  # use a different font source
  tools/measure-text.py --lottie assets/lottie/system-design/caching-cache-layers.lottie ...
  tools/measure-text.py --font "/path/to/Some Font.ttf" ...
"""

import argparse
import glob
import os
import struct
import sys
import zipfile

DEFAULT_LOTTIE_GLOB = "assets/lottie/**/*.lottie"
MIN_PADDING = 10  # per AGENTS.md: labels need >=10px clearance each side


class Font:
    """Minimal TrueType metrics reader: advance widths by unicode codepoint."""

    def __init__(self, data, name="<font>"):
        self.data = data
        self.name = name
        self._tables = self._read_table_directory()
        for required in ("head", "hhea", "hmtx", "cmap"):
            if required not in self._tables:
                raise ValueError("%s: missing required '%s' table" % (name, required))
        self.units_per_em = self._u16(self._tables["head"] + 18)
        self._num_h_metrics = self._u16(self._tables["hhea"] + 34)
        self._hmtx = self._tables["hmtx"]
        self._cmap = self._read_cmap4()

    def _u16(self, o):
        return struct.unpack(">H", self.data[o:o + 2])[0]

    def _s16(self, o):
        return struct.unpack(">h", self.data[o:o + 2])[0]

    def _u32(self, o):
        return struct.unpack(">I", self.data[o:o + 4])[0]

    def _read_table_directory(self):
        tables = {}
        for i in range(self._u16(4)):
            o = 12 + i * 16
            tag = self.data[o:o + 4].decode("latin-1")
            tables[tag] = self._u32(o + 8)
        return tables

    def _read_cmap4(self):
        base = self._tables["cmap"]
        sub = None
        for i in range(self._u16(base + 2)):
            o = base + 4 + i * 8
            platform, encoding = self._u16(o), self._u16(o + 2)
            if (platform, encoding) in ((3, 1), (3, 10), (0, 3), (0, 4), (0, 6)):
                sub = base + self._u32(o + 4)
                break
        if sub is None:
            raise ValueError("%s: no unicode cmap subtable" % self.name)
        fmt = self._u16(sub)
        if fmt != 4:
            raise ValueError("%s: unsupported cmap format %d (only 4)" % (self.name, fmt))
        seg_x2 = self._u16(sub + 6)
        return {
            "segments": seg_x2 // 2,
            "end": sub + 14,
            "start": sub + 14 + seg_x2 + 2,
            "delta": sub + 14 + seg_x2 * 2 + 2,
            "range": sub + 14 + seg_x2 * 3 + 2,
        }

    def _glyph_id(self, char):
        c = ord(char)
        cm = self._cmap
        for i in range(cm["segments"]):
            if self._u16(cm["end"] + i * 2) >= c:
                start = self._u16(cm["start"] + i * 2)
                if start > c:
                    return 0
                range_offset = self._u16(cm["range"] + i * 2)
                delta = self._s16(cm["delta"] + i * 2)
                if range_offset == 0:
                    return (c + delta) & 0xFFFF
                gid = self._u16(cm["range"] + i * 2 + range_offset + (c - start) * 2)
                return 0 if gid == 0 else (gid + delta) & 0xFFFF
        return 0

    def _advance(self, gid):
        index = min(gid, self._num_h_metrics - 1)
        return self._u16(self._hmtx + index * 4)

    def width(self, text, size_px):
        units = sum(self._advance(self._glyph_id(ch)) for ch in text)
        return units / self.units_per_em * size_px

    def missing(self, text):
        return sorted({ch for ch in text if self._glyph_id(ch) == 0 and ch != " "})


def load_font(font_path=None, lottie_path=None, repo_root="."):
    if font_path:
        with open(font_path, "rb") as fh:
            return Font(fh.read(), os.path.basename(font_path))

    if not lottie_path:
        pattern = os.path.join(repo_root, DEFAULT_LOTTIE_GLOB)
        candidates = sorted(glob.glob(pattern, recursive=True))
        if not candidates:
            raise SystemExit(
                "no .lottie found under %s -- pass --font or --lottie" % DEFAULT_LOTTIE_GLOB)
        lottie_path = candidates[0]

    with zipfile.ZipFile(lottie_path) as zf:
        fonts = [n for n in zf.namelist() if n.lower().endswith((".ttf", ".otf"))]
        if not fonts:
            raise SystemExit("%s embeds no font -- pass --font" % lottie_path)
        return Font(zf.read(fonts[0]), "%s :: %s" % (os.path.basename(lottie_path), fonts[0]))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Measure text widths in the font embedded in a .lottie.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Examples\n--------\n")[1])
    ap.add_argument("strings", nargs="+", help="text to measure")
    ap.add_argument("--size", type=float, action="append", metavar="PX",
                    help="font size in px (repeatable to compare sizes; default 15)")
    ap.add_argument("--box", type=float, metavar="PX",
                    help="available width to check against (node box or inter-node gap)")
    ap.add_argument("--canvas", type=float, metavar="PX",
                    help="canvas width, for computing a right-aligned centre anchor")
    ap.add_argument("--margin", type=float, default=40.0, metavar="PX",
                    help="right margin used with --canvas (default 40)")
    ap.add_argument("--font", metavar="PATH", help="use this .ttf/.otf directly")
    ap.add_argument("--lottie", metavar="PATH", help="take the font from this .lottie")
    ap.add_argument("--repo-root", default=os.path.join(os.path.dirname(__file__), ".."),
                    help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    sizes = args.size or [15.0]
    font = load_font(args.font, args.lottie, args.repo_root)
    print("font: %s (unitsPerEm=%d)" % (font.name, font.units_per_em))
    if args.box:
        print("fit target: %gpx, needs >=%gpx padding each side" % (args.box, MIN_PADDING))
    print("")

    worst_verdict = "OK"
    for text in args.strings:
        gaps = font.missing(text)
        if gaps:
            print("  WARNING: no glyph for %s in '%s'" % (gaps, text))
        for size in sizes:
            w = font.width(text, size)
            line = "  %7.1fpx @%-5g" % (w, size)
            if args.box:
                pad = (args.box - w) / 2
                verdict = "OK" if pad >= MIN_PADDING else ("TIGHT" if pad >= 0 else "OVERFLOW")
                if verdict == "OVERFLOW" or (verdict == "TIGHT" and worst_verdict == "OK"):
                    worst_verdict = verdict
                line += "  pad %6.1f  %-8s" % (pad, verdict)
            if args.canvas:
                anchor = args.canvas - args.margin - w / 2
                line += "  anchor-x %7.1f  spans %.1f..%.1f" % (
                    anchor, anchor - w / 2, anchor + w / 2)
            print("%s  '%s'" % (line, text))
        if len(sizes) > 1:
            print("")

    if args.box and worst_verdict == "OVERFLOW":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
