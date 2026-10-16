"""Memorees remote smoke test — stdlib only, no installs.

Usage (PowerShell):
  python scripts/smoke.py --base https://memorees.darrenlane.com --user darren --password <pw>

Checks tickets 01-05 end to end: version, auth lifecycle, album lifecycle
with link regen, photo upload + multiline comment round-trip, public
readonly contract incl. EXIF/GPS privacy. Leaves no residue (test album
deleted). Exits non-zero on any FAIL.
"""
import argparse
import base64
import io
import json
import sys
import urllib.parse
import pathlib
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
EXPECTED_VERSION = (pathlib.Path(__file__).resolve().parent.parent / "VERSION").read_text().strip()

# 1x1 PNG payload (no imaging libs needed)
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

results = []


def check(name, ok, detail=""):
    detail = str(detail)[:160].encode("ascii", "backslashreplace").decode("ascii")
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f" - {detail}" if detail else ""))


class Client:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(CookieJar()))

    def _req(self, method, path, data=None, headers=None, ctype=None):
        r = urllib.request.Request(self.base + path, data=data, method=method)
        if ctype:
            r.add_header("Content-Type", ctype)
        for k, v in (headers or {}).items():
            r.add_header(k, v)
        try:
            with self.opener.open(r) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def get(self, path, headers=None):
        return self._req("GET", path, headers=headers)

    def form(self, path, fields):
        return self._req("POST", path,
                         urllib.parse.urlencode(fields).encode(), ctype="application/x-www-form-urlencoded")

    def json(self, method, path, obj):
        return self._req(method, path, json.dumps(obj).encode(), ctype="application/json")

    def upload(self, path, filename, payload):
        boundary = "smokeboundary123"
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"{filename}\"\r\n"
                f"Content-Type: image/png\r\n\r\n").encode() + payload + f"\r\n--{boundary}--\r\n".encode()
        return self._req("POST", path, body, ctype=f"multipart/form-data; boundary={boundary}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    a = ap.parse_args()
    c = Client(a.base)

    # 01: version + landing
    s, b = c.get("/api/version")
    try:
        v = json.loads(b)
        check("01 version endpoint", s == 200 and v.get("version") == EXPECTED_VERSION, f"{v}")
        check("01 build provenance", v.get("build") not in ("", "dev", None), f"build={v.get('build')}")
    except Exception as e:
        check("01 version endpoint", False, e)
    s, b = c.get("/")
    check("01 landing serves", s == 200 and b"Memorees" in b, f"http={s}")

    # 02: auth lifecycle (bad pw -> login -> me -> logout)
    s, _ = c.form("/api/login", {"username": a.user, "password": "wrong-" + a.password})
    check("02 bad password rejected", s == 401, f"http={s}")
    s, b = c.form("/api/login", {"username": a.user, "password": a.password})
    check("02 login", s == 200, f"http={s}")
    s, b = c.get("/api/me")
    try:
        me = json.loads(b)
        check("02 who-am-i", s == 200 and me.get("user") == a.user, f"{b[:120]}")
        st = me.get("settings", {})
        check("02 defaults (gps off)", st.get("show_gps") is False and st.get("show_camera") is True, f"{st}")
    except Exception as e:
        check("02 who-am-i", False, e)

    # 03: album lifecycle
    s, b = c.json("POST", "/api/albums", {"title": "smoke-probe"})
    alb = json.loads(b) if s == 200 else {}
    aid = alb.get("id")
    check("03 album create", s == 200 and aid, f"http={s}")
    link1 = None
    if aid:
        s, b = c.get("/api/albums")
        names = [x.get("title") for x in json.loads(b)] if s == 200 else []
        check("03 album listed", "smoke-probe" in names, f"{names}")
        s, b = c.json("PUT", f"/api/albums/{aid}",
                      {"font": "serif", "transition": "zoom", "regen": True})
        link1 = (json.loads(b) or {}).get("public_uuid") if s == 200 else None
        check("03 regen link", s == 200 and link1, f"http={s}")
        s, b = c.get(f"/api/albums/{aid}/photos")
        check("03 photo list empty", s == 200 and json.loads(b)["photos"] == [], f"http={s}")

        # 04: upload + comment
        s, b = c.upload(f"/api/albums/{aid}/photos", "probe.png", PNG_1PX)
        try:
            up = json.loads(b)
            check("04 png upload", s == 200 and up.get("uploaded") == 1, f"{b[:120]}")
        except Exception as e:
            check("04 png upload", False, f"http={s} {e}")
        s, b = c.get(f"/api/albums/{aid}/photos")
        photos = (json.loads(b) or {}).get("photos", []) if s == 200 else []
        pid = photos[0]["id"] if photos else None
        src = photos[0]["src"] if photos else None
        check("04 photo listed", bool(pid), f"http={s}")
        if src:
            s2, img = c.get(src)
            check("04 preview serves", s2 == 200 and len(img) > 100, f"http={s2} bytes={len(img)}")
        comment = "line one\nline two\nline three 🐚"
        if pid:
            s, _ = c.json("PUT", f"/api/photos/{pid}", {"comment": comment})
            check("04 comment save", s == 200, f"http={s}")
            s, b = c.get(f"/api/albums/{aid}/photos")
            back = ((json.loads(b) or {}).get("photos") or [{}])[0].get("comment")
            check("04 comment round-trip", back == comment, f"{back!r}"[:120])

        # 05: public contract
        s, b = c.get(f"/api/p/{link1}")
        try:
            pub = json.loads(b)
            check("05 public loads anon-shape", s == 200 and pub.get("album") == "smoke-probe", f"{b[:120]}")
            p0 = (pub.get("photos") or [{}])[0]
            check("05 public comment present", p0.get("comment") == comment, f"{p0.get('comment')!r}"[:120])
            check("05 gps hidden by default", "gps" not in (p0.get("exif") or {}), f"{p0.get('exif')}")
        except Exception as e:
            check("05 public loads anon-shape", False, f"http={s} {e}")

        anon = Client(a.base)
        s, _ = anon._req("DELETE", "/api/photos/999999")
        check("05 anon delete refused", s == 401, f"http={s}")
        if pid:
            s, _ = c._req("DELETE", f"/api/photos/{pid}")
            check("08 photo delete", s == 200, f"http={s}")
            s, b = c.get(f"/api/albums/{aid}/photos")
            check("08 photo gone", s == 200 and json.loads(b)["photos"] == [], f"http={s}")
        # cleanup
        s, _ = c._req("DELETE", f"/api/albums/{aid}")
        check("03 album delete (cleanup)", s == 200, f"http={s}")
        if link1:
            s, _ = c.get(f"/api/p/{link1}")
            check("03 link dead after delete", s == 404, f"http={s}")

    # logout last
    c2 = Client(a.base)
    c2.form("/api/login", {"username": a.user, "password": a.password})
    s, _ = c2._req("POST", "/api/logout")
    s, b = c2.get("/api/me")
    try:
        check("02 logout destroys session", (json.loads(b) or {}).get("user") is None, f"{b[:120]}")
    except Exception as e:
        check("02 logout destroys session", False, e)

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    import urllib.error
    main()
