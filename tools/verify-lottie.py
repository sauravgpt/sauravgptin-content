#!/usr/bin/env python3
"""Check an exported .lottie against the AGENTS.md section 12 quality gate.

Reads the animation JSON straight out of the dotLottie container, so it works on the
committed asset and does not depend on the Creator MCP bridge being alive. Checks are
derived from the layer naming convention (`packet-*`, `line-*`, `box-*`, `container-*`,
`branding-*`), so it works on any animation in this repo without configuration.

What it catches that the eye tends not to:
  - a state colour that never returns to base, so the loop jumps
  - a state colour that drifts back over hundreds of frames through off-palette mud
  - a packet still visible at the loop boundary
  - an edge line left highlighted
  - a layer accidentally named NaN (see the createTextLayer bug in AGENTS.md)
  - a missing or buried branding watermark

Usage:
  tools/verify-lottie.py assets/lottie/system-design/*.lottie
  tools/verify-lottie.py --quiet assets/lottie/**/*.lottie   # only report failures
"""

import argparse
import glob
import json
import sys
import zipfile

PALETTE = {
    "#6366f1": "accent", "#f97316": "packet", "#64748b": "line/muted",
    "#cbd5e1": "border", "#f4f4f5": "panel", "#1e1b4b": "text",
    "#ffffff": "white", "#16a34a": "success", "#dc2626": "error",
}
LINE_BASE = "#64748b"
MAX_TRANSITION_FRAMES = 30  # a state colour change; observed good values are 12-24
CANVAS_PRESETS = {(1200, 500): "wide", (1200, 675): "standard", (800, 1000): "tall", (600, 600): "square"}


def load(path):
    with zipfile.ZipFile(path) as zf:
        name = next(n for n in zf.namelist() if n.startswith("a/") and n.endswith(".json"))
        return json.loads(zf.read(name))


def hexof(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c * 255))) for c in rgb[:3])


def sample(prop, frame):
    if prop.get("a", 0) == 0:
        return prop["k"]
    keys = prop["k"]
    if frame <= keys[0]["t"]:
        return keys[0]["s"]
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if a["t"] <= frame <= b["t"]:
            span = b["t"] - a["t"]
            t = 0 if span == 0 else (frame - a["t"]) / span
            sa, sb = a["s"], b.get("s", a["s"])
            return [sa[j] + (sb[j] - sa[j]) * t for j in range(len(sa))]
    return keys[-1].get("s", keys[-1].get("e"))


def paint(layer, frame):
    for shape in layer.get("shapes", []):
        if shape["ty"] in ("fl", "st"):
            return hexof(sample(shape["c"], frame))
    return None


def opacity(layer, frame):
    return round(sample(layer["ks"]["o"], frame)[0])


def check(path, quiet=False):
    anim = load(path)
    layers = anim["layers"]
    names = [l.get("nm", "") for l in layers]
    by_prefix = lambda p: [l for l in layers if l.get("nm", "").startswith(p)]
    end = anim["op"]
    failures = []

    def fail(msg):
        failures.append(msg)

    preset = CANVAS_PRESETS.get((anim["w"], anim["h"]))
    if not preset:
        fail("canvas %dx%d is not one of the four presets" % (anim["w"], anim["h"]))
    if anim["fr"] != 60:
        fail("framerate %s, expected 60" % anim["fr"])

    if "NaN" in names:
        fail("%d layer(s) named NaN" % names.count("NaN"))

    brand = [n for n in names if n.startswith("branding-")]
    if not brand:
        fail("no branding watermark")
    elif names[0] != brand[0]:
        fail("branding is not the topmost layer (topmost is %s)" % names[0])

    for l in by_prefix("packet-"):
        if opacity(l, 0) != 0 or opacity(l, end) != 0:
            fail("%s visible at a loop boundary (f0=%d%%, f%d=%d%%)"
                 % (l["nm"], opacity(l, 0), end, opacity(l, end)))

    for l in by_prefix("line-") + by_prefix("lifeline-"):
        for f in (0, end):
            c = paint(l, f)
            if l["nm"].startswith("line-") and c not in (LINE_BASE, None):
                fail("%s not at base colour at f%d (%s)" % (l["nm"], f, c))

    for l in by_prefix("box-"):
        a, b = paint(l, 0), paint(l, end)
        if a != b:
            fail("%s does not return to its f0 colour (f0=%s, f%d=%s)" % (l["nm"], a, end, b))
        # A state change should read as a change, not a slow desaturation. Measure the span of
        # each keyframe pair whose colour actually differs: legitimate transitions are 12-24
        # frames, so anything much longer is the box drifting through off-palette mud.
        for shape in l.get("shapes", []):
            if shape["ty"] != "fl" or shape["c"].get("a", 0) != 1:
                continue
            keys = shape["c"]["k"]
            for i in range(len(keys) - 1):
                lo, hi = keys[i], keys[i + 1]
                if hexof(lo["s"]) == hexof(hi.get("s", lo["s"])):
                    continue
                span = hi["t"] - lo["t"]
                if span > MAX_TRANSITION_FRAMES:
                    fail("%s eases %s -> %s over %d frames (f%d-f%d); a state change should "
                         "take <=%d, longer reads as unexplained drift through off-palette colours"
                         % (l["nm"], hexof(lo["s"]), hexof(hi["s"]), span, lo["t"], hi["t"],
                            MAX_TRANSITION_FRAMES))

    for l in by_prefix("container-"):
        if opacity(l, end) != 100:
            fail("%s ambient cycle does not land on 100%% at f%d (%d%%)"
                 % (l["nm"], end, opacity(l, end)))

    status = "FAIL" if failures else "PASS"
    if failures or not quiet:
        print("%-4s %s" % (status, path.split("/")[-1]))
        if not quiet:
            print("       %dx%d (%s) @%dfps  frames %d..%d  %d layers"
                  % (anim["w"], anim["h"], preset or "?", anim["fr"], anim["ip"], end, len(layers)))
            counts = {}
            for n in names:
                counts[n.split("-")[0]] = counts.get(n.split("-")[0], 0) + 1
            print("       " + "  ".join("%s:%d" % kv for kv in sorted(counts.items())))
    for f in failures:
        print("       - %s" % f)
    return not failures


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+", help=".lottie files (globs are expanded)")
    ap.add_argument("--quiet", action="store_true", help="only print failures")
    args = ap.parse_args(argv)

    paths = []
    for p in args.paths:
        paths.extend(sorted(glob.glob(p, recursive=True)) or [p])

    ok = True
    for p in paths:
        try:
            ok &= check(p, args.quiet)
        except Exception as exc:  # noqa: BLE001 - report and keep going
            print("FAIL %s\n       - could not read: %s" % (p.split("/")[-1], exc))
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
