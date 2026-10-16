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

print(f"\n{5 - len(fails)}/5 passed")
sys.exit(1 if fails else 0)
