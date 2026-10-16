"""Memorees V1 — single-container FastAPI + SQLite. See README.md."""
import hashlib
import json
import os
import secrets
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

try:
    import pillow_heif  # enables HEIF/HEIC opens in Pillow
    pillow_heif.register_heif_opener()
except Exception:
    pass
from PIL import ExifTags, Image

DATA = Path(os.environ.get("DATA_DIR", "./data"))
DB = DATA / "memorees.db"
ORIG = DATA / "originals"
PREV = DATA / "previews"
ALLOW_SIGNUP = os.environ.get("ALLOW_SIGNUP", "true").lower() == "true"
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
APP_DIR = Path(__file__).resolve().parent.parent
VERSION = (APP_DIR / "VERSION").read_text().strip() if (APP_DIR / "VERSION").exists() else "0.1.0"

for p in (DATA, ORIG, PREV):
    p.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Memorees")

TAGS = {v: k for k, v in ExifTags.TAGS.items()}


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def init():
    c = db()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
          salt TEXT NOT NULL, hash TEXT NOT NULL,
          display TEXT DEFAULT '', created TEXT NOT NULL,
          settings TEXT DEFAULT '{}');
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS albums(
          id INTEGER PRIMARY KEY, owner INTEGER NOT NULL, title TEXT NOT NULL,
          font TEXT DEFAULT 'hand', transition TEXT DEFAULT 'fade',
          public_uuid TEXT UNIQUE NOT NULL, created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS photos(
          id INTEGER PRIMARY KEY, album_id INTEGER NOT NULL,
          fname TEXT NOT NULL, preview TEXT NOT NULL,
          comment TEXT DEFAULT '', taken_at TEXT DEFAULT '',
          uploaded_at TEXT NOT NULL, exif TEXT DEFAULT '{}', pos INTEGER DEFAULT 0);
        """
    )
    c.commit()
    c.close()


init()


def migrate():
    c = db()
    try:
        c.execute("ALTER TABLE photos ADD COLUMN thumb TEXT DEFAULT ''")
    except Exception:
        pass
    c.commit()
    c.close()


migrate()


def make_thumb(preview_name: str) -> str:
    """400px grid thumb stored next to the preview; backfilled on demand."""
    stem = Path(preview_name).stem
    thumb = stem + "_t.jpg"
    if not (PREV / thumb).exists() and (PREV / preview_name).exists():
        try:
            im = Image.open(PREV / preview_name).convert("RGB")
            im.thumbnail((400, 400))
            im.save(PREV / thumb, "JPEG", quality=80)
        except Exception:
            return preview_name
    return thumb if (PREV / thumb).exists() else preview_name


DEFAULT_SETTINGS = {
    "show_camera": True,
    "show_gps": False, "show_taken": True, "show_uploaded": True,
    "font_default": "hand", "theme": "light",
}


def get_settings(username_row) -> dict:
    s = dict(DEFAULT_SETTINGS)
    try:
        s.update(json.loads(username_row["settings"] or "{}"))
    except Exception:
        pass
    return s


def me(session: str | None = Cookie(default=None)):
    if not session:
        return None
    c = db()
    r = c.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=?",
        (session,),
    ).fetchone()
    c.close()
    return r


def need(u):
    if not u:
        raise HTTPException(401, "login required")
    return u


def pbkdf(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()


def frac(v):
    try:
        if hasattr(v, "numerator"):
            return round(float(v.numerator) / float(v.denominator), 2) if v.denominator else float(v)
        return v
    except Exception:
        return str(v)


def read_exif(path: Path) -> dict:
    out: dict = {}
    try:
        im = Image.open(path)
        out["width"], out["height"] = im.size
        ex = im._getexif() or {}
        g = lambda n: ex.get(TAGS.get(n))
        make = g("Make") or ""
        model = g("Model") or ""
        if make or model:
            out["camera"] = f"{make} {model}".strip()
        if g("LensModel"):
            out["lens"] = str(g("LensModel"))
        if g("FocalLength") is not None:
            out["focal"] = str(frac(g("FocalLength"))) + "mm"
        if g("FNumber") is not None:
            out["aperture"] = "f/" + str(frac(g("FNumber")))
        if g("ExposureTime") is not None:
            e = g("ExposureTime")
            out["shutter"] = f"1/{round(float(e.denominator)/float(e.numerator))}" if hasattr(e, "denominator") and e.numerator else str(e)
        if g("ISOSpeedRatings") is not None:
            out["iso"] = "ISO" + str(g("ISOSpeedRatings"))
        if g("DateTimeOriginal"):
            out["taken"] = str(g("DateTimeOriginal"))
        gps = g("GPSInfo")
        if gps:
            out["gps"] = "present"
    except Exception:
        pass
    return out


def fmt_when(s: str) -> str:
    """EXIF/ISO stamp -> '16 Oct 2026, 12:22' for humans."""
    s = (s or "").strip()
    if not s:
        return ""
    d = None
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        try:
            d = datetime.strptime(s, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            return s
    return d.strftime("%d %b %Y, %H:%M")


def filter_exif(full: dict, settings: dict, taken_at: str, uploaded_at: str) -> dict:
    f: dict = {}
    if settings.get("show_uploaded"):
        f["uploaded"] = fmt_when(uploaded_at)
    if settings.get("show_taken") and taken_at:
        f["taken"] = fmt_when(taken_at)
    if settings.get("show_camera") and full.get("camera"):
        f["camera"] = full["camera"]
    if settings.get("show_gps") and full.get("gps"):
        f["gps"] = full["gps"]
    return f


@app.get("/api/version")
def version():
    return {"version": VERSION, "build": os.environ.get("BUILD_HASH", "dev"),
            "date": os.environ.get("BUILD_DATE", "unknown")}


@app.post("/api/register")
def register(username: str = Form(...), password: str = Form(...)):
    if not ALLOW_SIGNUP:
        raise HTTPException(403, "signup disabled")
    username = username.strip()[:32]
    if len(username) < 2 or len(password) < 4:
        raise HTTPException(400, "username/password too short")
    salt = secrets.token_hex(16)
    c = db()
    try:
        c.execute("INSERT INTO users(username,salt,hash,display,created) VALUES(?,?,?,?,?)",
                  (username, salt, pbkdf(password, salt), username, datetime.utcnow().isoformat()))
        c.commit()
    except sqlite3.IntegrityError:
        c.close()
        raise HTTPException(409, "username taken")
    c.close()
    return login(username=username, password=password)


@app.post("/api/login")
def login(username: str = Form(...), password: str = Form(...)):
    c = db()
    u = c.execute("SELECT * FROM users WHERE username=?", (username.strip(),)).fetchone()
    if not u or pbkdf(password, u["salt"]) != u["hash"]:
        c.close()
        raise HTTPException(401, "bad credentials")
    tok = secrets.token_urlsafe(32)
    c.execute("INSERT INTO sessions(token,user_id,created) VALUES(?,?,?)",
              (tok, u["id"], datetime.utcnow().isoformat()))
    c.commit()
    c.close()
    r = JSONResponse({"ok": True, "username": u["username"]})
    r.set_cookie("session", tok, httponly=True, samesite="lax", max_age=30 * 86400)
    return r


@app.post("/api/logout")
def logout(session: str | None = Cookie(default=None)):
    if session:
        c = db()
        c.execute("DELETE FROM sessions WHERE token=?", (session,))
        c.commit()
        c.close()
    r = JSONResponse({"ok": True})
    r.delete_cookie("session")
    return r


@app.get("/api/me")
def me_route(session: str | None = Cookie(default=None)):
    u = me(session)
    if not u:
        return {"user": None}
    return {"user": u["username"], "display": u["display"] or u["username"],
            "settings": get_settings(u)}


@app.get("/api/settings")
def get_set(session: str | None = Cookie(default=None)):
    u = need(me(session))
    return get_settings(u)


@app.put("/api/settings")
async def put_set(body: dict, session: str | None = Cookie(default=None)):
    u = need(me(session))
    cur = get_settings(u)
    for k in DEFAULT_SETTINGS:
        if k in body:
            cur[k] = body[k]
    c = db()
    c.execute("UPDATE users SET settings=? WHERE id=?", (json.dumps(cur), u["id"]))
    c.commit()
    c.close()
    return cur


@app.get("/api/albums")
def albums(session: str | None = Cookie(default=None)):
    u = need(me(session))
    c = db()
    rows = c.execute("SELECT * FROM albums WHERE owner=? ORDER BY id DESC", (u["id"],)).fetchall()
    out = []
    for a in rows:
        n = c.execute("SELECT COUNT(*) n FROM photos WHERE album_id=?", (a["id"],)).fetchone()["n"]
        cov = c.execute("SELECT preview,thumb FROM photos WHERE album_id=? ORDER BY pos,rowid LIMIT 1",
                        (a["id"],)).fetchone()
        cv = None
        if cov:
            th = cov["thumb"] or make_thumb(cov["preview"])
            if not cov["thumb"]:
                c.execute("UPDATE photos SET thumb=? WHERE preview=?", (th, cov["preview"]))
                c.commit()
            cv = f"/previews/{th}"
        out.append({"id": a["id"], "title": a["title"], "font": a["font"],
                    "transition": a["transition"], "public_uuid": a["public_uuid"],
                    "count": n, "cover": cv,
                    "link": f"{BASE_URL}/p/{a['public_uuid']}"})
    c.close()
    return out


@app.post("/api/albums")
async def create_album(body: dict, session: str | None = Cookie(default=None)):
    u = need(me(session))
    title = (body.get("title") or "Untitled").strip()[:80]
    c = db()
    pu = uuid.uuid4().hex[:12]
    cur = c.execute("INSERT INTO albums(owner,title,public_uuid,created) VALUES(?,?,?,?)",
                    (u["id"], title, pu, datetime.utcnow().isoformat()))
    c.commit()
    aid = cur.lastrowid
    c.close()
    return {"id": aid, "public_uuid": pu}


@app.put("/api/albums/{aid}")
async def update_album(aid: int, body: dict, session: str | None = Cookie(default=None)):
    u = need(me(session))
    c = db()
    a = c.execute("SELECT * FROM albums WHERE id=? AND owner=?", (aid, u["id"])).fetchone()
    if not a:
        c.close()
        raise HTTPException(404, "album not found")
    title = body.get("title", a["title"])[:80]
    font = body.get("font", a["font"]) if body.get("font") in ("hand", "sans", "serif") else a["font"]
    trans = body.get("transition", a["transition"]) if body.get("transition") in ("fade", "slide", "zoom", "none") else a["transition"]
    pu = a["public_uuid"]
    if body.get("regen"):
        pu = uuid.uuid4().hex[:12]
    c.execute("UPDATE albums SET title=?,font=?,transition=?,public_uuid=? WHERE id=?",
              (title, font, trans, pu, aid))
    c.commit()
    c.close()
    return {"ok": True, "public_uuid": pu, "link": f"{BASE_URL}/p/{pu}"}


@app.delete("/api/albums/{aid}")
def del_album(aid: int, session: str | None = Cookie(default=None)):
    u = need(me(session))
    c = db()
    c.execute("DELETE FROM photos WHERE album_id IN (SELECT id FROM albums WHERE id=? AND owner=?)", (aid, u["id"]))
    c.execute("DELETE FROM albums WHERE id=? AND owner=?", (aid, u["id"]))
    c.commit()
    c.close()
    return {"ok": True}


@app.get("/api/albums/{aid}/photos")
def photos(aid: int, offset: int = 0, limit: int = 48, session: str | None = Cookie(default=None)):
    u = need(me(session))
    c = db()
    a = c.execute("SELECT * FROM albums WHERE id=? AND owner=?", (aid, u["id"])).fetchone()
    if not a:
        c.close()
        raise HTTPException(404, "album not found")
    total = c.execute("SELECT COUNT(*) n FROM photos WHERE album_id=?", (aid,)).fetchone()["n"]
    rows = c.execute("SELECT * FROM photos WHERE album_id=? ORDER BY pos,rowid LIMIT ? OFFSET ?",
                     (aid, limit, offset)).fetchall()
    st = get_settings(u)
    out = []
    for r in rows:
        th = r["thumb"] or make_thumb(r["preview"])
        if not r["thumb"]:
            c.execute("UPDATE photos SET thumb=? WHERE id=?", (th, r["id"]))
        out.append({"id": r["id"], "thumb": f"/previews/{th}", "src": f"/previews/{r['preview']}",
                    "comment": r["comment"],
                    "exif": filter_exif(json.loads(r["exif"] or "{}"), st, r["taken_at"], r["uploaded_at"]),
                    "taken": r["taken_at"], "uploaded": r["uploaded_at"]})
    c.commit()
    c.close()
    return {"album": {"id": a["id"], "title": a["title"], "font": a["font"],
                      "transition": a["transition"], "link": f"{BASE_URL}/p/{a['public_uuid']}"},
            "photos": out, "total": total}


@app.post("/api/albums/{aid}/photos")
async def upload(aid: int, files: list[UploadFile] = File(...),
                 session: str | None = Cookie(default=None)):
    u = need(me(session))
    c = db()
    a = c.execute("SELECT * FROM albums WHERE id=? AND owner=?", (aid, u["id"])).fetchone()
    if not a:
        c.close()
        raise HTTPException(404, "album not found")
    ext_ok = (".jpg", ".jpeg", ".png", ".heif", ".heic")
    made = []
    for f in files:
        ext = Path(f.filename or "img").suffix.lower()
        if ext not in ext_ok:
            continue
        pid = uuid.uuid4().hex
        raw = ORIG / f"{pid}{ext}"
        raw.write_bytes(await f.read())
        ex = read_exif(raw)
        taken = ex.pop("taken", "") if isinstance(ex, dict) else ""
        # build JPEG preview (this is what browsers display; original kept on disk)
        try:
            im = Image.open(raw).convert("RGB")
            im.thumbnail((1600, 1600))
            pv = f"{pid}.jpg"
            im.save(PREV / pv, "JPEG", quality=85)
        except Exception:
            raw.unlink(missing_ok=True)
            continue
        now = datetime.utcnow().isoformat()
        c.execute("INSERT INTO photos(album_id,fname,preview,thumb,comment,taken_at,uploaded_at,exif) VALUES(?,?,?,?,?,?,?,?)",
                  (aid, f.filename[:120], pv, make_thumb(pv), "", taken, now, json.dumps(ex)))
        made.append({"taken": taken, "name": f.filename})
    c.commit()
    c.close()
    return {"uploaded": len(made), "files": made}


@app.put("/api/photos/{pid}")
async def edit_photo(pid: int, body: dict, session: str | None = Cookie(default=None)):
    u = need(me(session))
    c = db()
    r = c.execute("SELECT p.* FROM photos p JOIN albums a ON a.id=p.album_id WHERE p.id=? AND a.owner=?",
                  (pid, u["id"])).fetchone()
    if not r:
        c.close()
        raise HTTPException(404, "photo not found")
    c.execute("UPDATE photos SET comment=? WHERE id=?", (body.get("comment", "")[:2000], pid))
    c.commit()
    c.close()
    return {"ok": True}


@app.delete("/api/photos/{pid}")
def del_photo(pid: int, session: str | None = Cookie(default=None)):
    u = need(me(session))
    c = db()
    r = c.execute("SELECT p.* FROM photos p JOIN albums a ON a.id=p.album_id WHERE p.id=? AND a.owner=?",
                  (pid, u["id"])).fetchone()
    if not r:
        c.close()
        raise HTTPException(404, "photo not found")
    c.execute("DELETE FROM photos WHERE id=?", (pid,))
    c.commit()
    c.close()
    stem = Path(r["preview"]).stem
    for f in ORIG.glob(stem + ".*"):
        f.unlink(missing_ok=True)
    (PREV / r["preview"]).unlink(missing_ok=True)
    (PREV / (stem + "_t.jpg")).unlink(missing_ok=True)
    return {"ok": True}


@app.get("/api/p/{puuid}")
def public(puuid: str, offset: int = 0, limit: int = 48):
    c = db()
    a = c.execute("SELECT a.*, u.username, u.settings FROM albums a JOIN users u ON u.id=a.owner WHERE a.public_uuid=?",
                  (puuid,)).fetchone()
    if not a:
        c.close()
        raise HTTPException(404, "link not found")
    st = dict(DEFAULT_SETTINGS)
    try:
        st.update(json.loads(a["settings"] or "{}"))
    except Exception:
        pass
    rows = c.execute("SELECT * FROM photos WHERE album_id=? ORDER BY pos,rowid LIMIT ? OFFSET ?",
                     (a["id"], limit, offset)).fetchall()
    total = c.execute("SELECT COUNT(*) n FROM photos WHERE album_id=?", (a["id"],)).fetchone()["n"]
    c.close()
    return {"album": a["title"], "author": a["username"], "font": a["font"],
            "transition": a["transition"],
            "photos": [{"src": f"/previews/{r['preview']}", "comment": r["comment"],
                        "exif": filter_exif(json.loads(r["exif"] or "{}"), st, r["taken_at"], r["uploaded_at"])}
                       for r in rows], "total": total}


app.mount("/previews", StaticFiles(directory=PREV), name="previews")
FRONT = APP_DIR / "frontend" / "index.html"
NOCACHE = {"Cache-Control": "no-store"}


@app.middleware("http")
async def cache_headers(req, call_next):
    resp = await call_next(req)
    if req.url.path.startswith("/previews/"):
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(FRONT, media_type="text/html", headers=NOCACHE)


@app.get("/p/{puuid}", response_class=HTMLResponse)
def pub_page(puuid: str):
    return FileResponse(FRONT, media_type="text/html", headers=NOCACHE)
