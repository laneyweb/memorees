"""Memorees UI regression checks — static, stdlib only.

Covers what the API smoke test cannot: no blocking system dialogs for
input, tooltips not clipped by card overflow. Run: python scripts/check_ui.py
"""
import pathlib
import re
import sys

HTML = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "index.html"
html = HTML.read_text(encoding="utf-8")
fails = []


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


check("no system prompt() dialogs", "prompt(" not in html)
check("album modal form exists", 'id="albumModal"' in html
      and "submitAlbum" in html and 'id="aname"' in html)
m = re.search(r"\.card\{[^}]*\}", html)
check("cards do not clip (overflow visible)", bool(m) and "overflow:visible" in m.group(0))
check("card images keep rounded tops", "border-radius:15px 15px 0 0" in html)
check("tooltip rule present", "[data-tip]:hover::after" in html)
check("header tooltips open downward", "header [data-tip]:hover::after" in html)
check("empty viewer placeholder (owner)", 'id="noview"' in html)
check("empty viewer placeholder (public)", 'id="pnoview"' in html)
check("uniform row rhythm", ".wrap .row{margin-bottom:16px}" in html)
check("no dead history.back buttons", "history.back(" not in html)
check("about returns to previous screen", "show(PREV)" in html)
check("comment box survives autoplay", "paint._i" in html)
check("public view sizes", "psize(" in html)
check("readable exif tags", ".pill{font-size:calc(14px * var(--capz,1))" in html)
check("toolbar tooltips open downward", "#s-albums [data-tip]:hover::after" in html)
check("paused by default (owner)", 'onclick="toggleP()">▶<' in html)
check("paused by default (public)", 'onclick="ptoggle()">▶<' in html)
check("size memory (owner)", "localStorage.vsize" in html)
check("size memory (public)", "localStorage.psize" in html)
check("whole image shown", "object-fit:contain" in html)
check("fullscreen fills screen", ":fullscreen" in html)
check("viewer blends with theme", ".viewer{background:transparent" in html)
check("about links github", "github.com/laneyweb/memorees" in html)
check("public sizes in control dock", "dockseg" in html)
check("owner sizes in control dock", "#ovseg" in html)
check("bars auto-hide on idle", ".viewer.idle" in html)
check("comment zoom controls", "capZoom(" in html)
check("photo delete controls", "delPhotoBtn" in html)
check("mini zoom buttons", 'class="mini"' in html)

print(f"\n{29 - len(fails)}/29 passed")
sys.exit(1 if fails else 0)
