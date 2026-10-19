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
# controls pinned to a right edge must anchor the tooltip inward, else it
# centres on the button and runs off screen on the right-most card
check("right-edge tooltips anchor inward",
      ".thumbx[data-tip]:hover::after" in html
      and "#editBtn[data-tip]:hover::after" in html
      and ".vbar .cbtn[data-tip]:hover::after" in html
      and ".exif .mini[data-tip]:hover::after" in html
      and "left:auto;right:0;transform:none" in html)
check("empty viewer placeholder (owner)", 'id="noview"' in html)
check("empty viewer placeholder (public)", 'id="pnoview"' in html)
check("uniform row rhythm", ".wrap .row{margin-bottom:16px}" in html)
check("no dead history.back buttons", "history.back(" not in html)
check("about returns to previous screen", "show(PREV)" in html)
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
check("photo delete controls", "delPhoto(" in html)
check("infinite scroll", "IntersectionObserver" in html)
check("size keys unmangled", "{full:'large'" not in html)
check("fullscreen caption card", "fscap" in html)
check("ios fullscreen fallback", "pseudo-full" in html)
check("inline comment edit", "startEdit(" in html)
check("mini zoom buttons", 'class="mini"' in html)
check("brand mark in header", 'id="logoMark"' in html)
check("brand favicon", 'rel="icon"' in html)
check("no emoji album chrome", "🏖️" not in html and "New memory album 📸" not in html)
check("no decorative emoji", all(e not in html for e in ["💛", "💾", "📷", "👋", "⚙️", "⬆", "✍", "🔗", "🌞", "✓"]))
check("album delete control", "delAlbum(" in html)
check("album delete confirm modal", 'id="delModal"' in html and 'id="dmsg"' in html)
check("danger confirm button", ".btn.danger" in html)
check("compact 32px buttons", "min-height:32px" in html)
check("settings button loads settings", 'onclick="loadSettings()"' in html)
check("settings reachable from album screen", html.count('onclick="loadSettings()"') >= 2)
check("settings saves itself (no Save button)",
      'onclick="saveSettings()">Save' not in html and "alert('Settings saved')" not in html)
check("settings change listener", "$('s-settings').addEventListener('change'" in html)
check("settings theme select", 'id="stheme"' in html and 'value="system"' in html)
check("settings live preview", 'id="setprev"' in html and "loadPreview()" in html)
check("settings back button", 'onclick="show(PREV)"' in html)
check("theme resolved before paint", "prefers-color-scheme" in html and "dataset.anon" in html)
check("theme written through to server", "'/api/settings'" in html and "body:JSON.stringify({theme:next})" in html)

print(f"\n{51 - len(fails)}/51 passed")
sys.exit(1 if fails else 0)
