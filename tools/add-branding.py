#!/usr/bin/env python3
"""Splice the branding watermark into a .lottie that was authored before the rule existed.

Rebuilding those scenes in Creator and re-exporting would work too, but this is
deterministic and leaves the rest of the animation byte-identical: it copies the
`branding-learn-sauravgpt-in` text layer out of a reference asset and inserts it as the
topmost layer, then repacks the container with every other entry untouched.

Safe because the layer is self-contained: its anchor/position give an effective translation
of (1102.8, 46) -- the documented 40px right margin on a 1200px canvas -- and it references
`Cal Sans Regular`, which every asset in this repo already embeds.

Usage:
  tools/add-branding.py --check  assets/lottie/**/*.lottie      # report what needs it
  tools/add-branding.py assets/lottie/system-design/foo.lottie  # splice it in
"""

import argparse
import copy
import glob
import json
import shutil
import sys
import zipfile

REFERENCE = "assets/lottie/system-design/dns-recursive-resolution.lottie"
BRAND_NAME = "branding-learn-sauravgpt-in"
BRAND_FONT = "Cal Sans Regular"
EXPECTED_TRANSLATION = (1102.8, 46.0)


def anim_entry(zf):
    return next(n for n in zf.namelist() if n.startswith("a/") and n.endswith(".json"))


def read(path):
    with zipfile.ZipFile(path) as zf:
        name = anim_entry(zf)
        return name, json.loads(zf.read(name))


def brand_layer(reference):
    _, anim = read(reference)
    for l in anim["layers"]:
        if l.get("nm") == BRAND_NAME:
            return copy.deepcopy(l)
    raise SystemExit("reference %s has no %s layer" % (reference, BRAND_NAME))


def translation(layer):
    a, p = layer["ks"]["a"]["k"], layer["ks"]["p"]["k"]
    return (round(p[0] - a[0], 1), round(p[1] - a[1], 1))


def splice(path, brand, dry_run=False):
    name, anim = read(path)
    names = [l.get("nm", "") for l in anim["layers"]]

    if any(n.startswith("branding-") for n in names):
        return "already branded"
    if anim["w"] != 1200:
        return "SKIP: canvas is %dpx wide, the reference anchor assumes 1200" % anim["w"]
    fonts = [f["fName"] for f in anim.get("fonts", {}).get("list", [])]
    if BRAND_FONT not in fonts:
        return "SKIP: does not embed %s (has %s)" % (BRAND_FONT, fonts or "no fonts")

    layer = copy.deepcopy(brand)
    layer["ind"] = max([l.get("ind", 0) for l in anim["layers"]]) + 1
    layer["op"] = anim["op"]
    layer["ip"] = anim["ip"]
    anim["layers"].insert(0, layer)

    if dry_run:
        return "would add as topmost layer (ind=%d, op=%d)" % (layer["ind"], layer["op"])

    # repack: rewrite the animation entry, copy everything else through untouched
    shutil.copy2(path, path + ".bak")
    with zipfile.ZipFile(path + ".bak") as src:
        entries = [(i, src.read(i.filename)) for i in src.infolist()]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
        for info, data in entries:
            if info.filename == name:
                data = json.dumps(anim, separators=(",", ":")).encode()
            out.writestr(info.filename, data)

    # confirm the round trip
    _, check = read(path)
    if check["layers"][0].get("nm") != BRAND_NAME:
        shutil.move(path + ".bak", path)
        return "FAILED: branding not topmost after repack, restored original"
    if len(check["layers"]) != len(names) + 1:
        shutil.move(path + ".bak", path)
        return "FAILED: layer count %d != %d, restored original" % (len(check["layers"]), len(names) + 1)
    return "added (%d -> %d layers)" % (len(names), len(check["layers"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--check", action="store_true", help="report only, change nothing")
    ap.add_argument("--reference", default=REFERENCE)
    ap.add_argument("--keep-backups", action="store_true")
    args = ap.parse_args(argv)

    brand = brand_layer(args.reference)
    got = translation(brand)
    if got != EXPECTED_TRANSLATION:
        raise SystemExit("reference watermark sits at %s, expected %s -- refusing to copy it"
                         % (got, EXPECTED_TRANSLATION))
    print("reference: %s (watermark at x=%.1f y=%.1f)\n" % (args.reference.split("/")[-1], *got))

    paths = []
    for p in args.paths:
        paths.extend(sorted(glob.glob(p, recursive=True)) or [p])

    for p in paths:
        print("  %-52s %s" % (p.split("/")[-1], splice(p, brand, args.check)))

    if not args.check and not args.keep_backups:
        for p in paths:
            try:
                import os
                os.remove(p + ".bak")
            except OSError:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
