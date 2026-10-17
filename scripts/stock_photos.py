#!/usr/bin/env python3
"""Fetch stock photos for README/demo seeding and stamp plausible EXIF on them.

Picsum (Unsplash-licensed) photos ship stripped of metadata, so the "camera
context" feature would be invisible in the README shots. This downloads each
image, then writes EXIF as a phone camera would: make, model, lens, exposure,
ISO and DateTimeOriginal.

Usage: python scripts/stock_photos.py [outdir]   (default: .scratch/stock)
"""
import io
import sys
import urllib.request
from pathlib import Path

from PIL import Image

# picsum id -> (slug, camera make, camera model, lens, focal, f-number,
#               shutter numerator/denominator, iso, taken "YYYY:MM:DD HH:MM:SS")
SHOTS = [
    ("bay-morning", "Apple", "iPhone 15 Pro", "iPhone 15 Pro back camera", 24, 1.8, 1 / 240, 32, "2025:07:14 07:12:04"),
    ("harbour-cliffs", "Apple", "iPhone 15 Pro", "iPhone 15 Pro back camera", 24, 1.8, 1 / 1200, 25, "2025:07:14 11:38:52"),
    ("summit-lake", "Canon", "EOS R6", "RF24-70mm F2.8 L IS USM", 35, 5.6, 1 / 800, 100, "2025:07:15 14:02:19"),
    ("old-town-evening", "Apple", "iPhone 13", "iPhone 13 back camera", 26, 1.6, 1 / 125, 1250, "2025:07:16 19:47:31"),
    ("night-market", "Google", "Pixel 9 Pro", "Pixel 9 Pro rear camera", 25, 1.7, 1 / 200, 500, "2025:07:17 21:15:08"),
    ("last-morning", "Apple", "iPhone 15 Pro", "iPhone 15 Pro back camera", 24, 1.8, 1 / 500, 40, "2025:07:18 06:53:44"),
]

# supporting photos so the album grid has more than one card
EXTRA = [
    ("birthday-2024", "Apple", "iPhone 13", "iPhone 13 back camera", 26, 1.6, 1 / 640, 200, "2024:11:02 18:04:40"),
    ("road-trip-2023", "Canon", "EOS R6", "RF24-70mm F2.8 L IS USM", 50, 2.8, 1 / 250, 160, "2023:09:03 12:41:57"),
    ("bessie-summer", "Apple", "iPhone 15", "iPhone 15 back camera", 24, 1.6, 1 / 1000, 80, "2023:07:22 15:08:26"),
]

IDS = {
    "bay-morning": 1015,
    "harbour-cliffs": 1016,
    "summit-lake": 1039,
    "old-town-evening": 1044,
    "night-market": 292,
    "last-morning": 1036,
    "birthday-2024": 431,
    "road-trip-2023": 1071,
    "bessie-summer": 237,
}

TAGS = {
    "make": 0x010F, "model": 0x0110, "lens": 0xA434,
    "exposure": 0x829A, "fnumber": 0x829D, "iso": 0x8827,
    "taken": 0x9003, "digitized": 0x9004, "focal": 0x920A,
    "software": 0x0131, "artist": 0x013B,
}


def ratio(v: float):
    from fractions import Fraction
    f = Fraction(v).limit_denominator(1000)
    return int(f.numerator), int(f.denominator)


def stamp(im: Image.Image, meta: dict) -> bytes:
    ex = Image.Exif()
    ex[TAGS["artist"]] = "memorees demo"
    ex[TAGS["software"]] = "17.4"
    ex[TAGS["make"]] = meta["make"]
    ex[TAGS["model"]] = meta["model"]
    ex[TAGS["lens"]] = meta["lens"]
    ex[TAGS["focal"]] = ratio(meta["focal"])
    ex[TAGS["fnumber"]] = ratio(meta["fnumber"])
    ex[TAGS["exposure"]] = ratio(meta["shutter"])
    ex[TAGS["iso"]] = meta["iso"]
    ex[TAGS["taken"]] = meta["taken"]
    ex[TAGS["digitized"]] = meta["taken"]
    return ex.tobytes()


def fetch(pid: int, size=(1600, 1067)) -> bytes:
    url = f"https://picsum.photos/id/{pid}/{size[0]}/{size[1]}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def build(shot, out: Path):
    slug, make, model, lens, focal, fnum, shutter, iso, taken = shot
    pid = IDS[slug]
    raw = fetch(pid)
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    meta = dict(make=make, model=model, lens=lens, focal=focal,
                fnumber=fnum, shutter=shutter, iso=iso, taken=taken)
    dest = out / f"{slug}.jpg"
    im.save(dest, "JPEG", quality=88, exif=stamp(im, meta))
    # sanity: the app must be able to read it back
    back = Image.open(dest)._getexif() or {}
    assert back.get(TAGS["model"]) == model, slug
    assert back.get(TAGS["taken"]) == taken, slug
    print(f"  {dest.name:24} {im.size[0]}x{im.size[1]}  {model}  {taken}")
    return dest


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".scratch/stock")
    out.mkdir(parents=True, exist_ok=True)
    print(f"fetching {len(SHOTS)} + {len(EXTRA)} stock photos into {out}")
    for s in SHOTS:
        build(s, out)
    for s in EXTRA:
        build(s, out)
    print("done")


if __name__ == "__main__":
    main()
