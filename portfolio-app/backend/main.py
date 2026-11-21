"""Portfolio API: FastAPI + SQLite. Serves the frontend too.
Run: ADMIN_PASSWORD=yourpass uvicorn backend.main:app --reload
"""
import os, sqlite3, secrets, json, time
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
DB = os.getenv("DB_PATH", str(ROOT / "portfolio.db"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")
TOKENS: dict[str, float] = {}  # token -> expiry
app = FastAPI(title="Portfolio API")

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def init():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS profile(k TEXT PRIMARY KEY, v TEXT);
    CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT, summary TEXT, tags TEXT, link TEXT, year INTEGER);
    CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT, email TEXT, body TEXT, created REAL);
    """)
    if not c.execute("SELECT 1 FROM profile").fetchone():
        profile = {
            "name": "pavani sri", "role": "Full-stack developer",
            "tagline": "I build fast, accessible web products from database to pixel.",
            "about": "I'm a fuull stack developer who works with Python,c,and java,I enjoy solving problems with data structures and algorithms.",
            "email": "you@example.com", "github": "https://github.com/", "linkedin": "https://linkedin.com/",
            "skills": json.dumps({"Frontend": ["React", "TypeScript", "CSS"],
                "Backend": ["Python", "FastAPI", "PostgreSQL"], "Ops": ["Docker", "CI/CD", "AWS"]}),
            "timeline": json.dumps([
                {"when": "2025 – now", "what": "Software Engineer, Company A"},
                {"when": "2023 – 2025", "what": "Developer, Company B"},
                {"when": "2019 – 2023", "what": "B.Tech, Your University"}]),
        }
        c.executemany("INSERT INTO profile VALUES(?,?)", profile.items())
        c.executemany("INSERT INTO projects(title,summary,tags,link,year) VALUES(?,?,?,?,?)", [
            ("Project One", "What it does, who it is for, and the result it produced.", "React,FastAPI", "#", 2026),
            ("Project Two", "A tool you built to solve a specific, measurable problem.", "Python,ML", "#", 2025),
            ("Project Three", "An open-source contribution or side project.", "TypeScript", "#", 2024)])
    c.commit(); c.close()
init()

def admin(authorization: str | None):
    t = (authorization or "").removeprefix("Bearer ")
    if TOKENS.get(t, 0) < time.time(): raise HTTPException(401, "Sign in required")

class Login(BaseModel): password: str
class Contact(BaseModel): name: str; email: str; body: str
class Project(BaseModel):
    title: str; summary: str; tags: str = ""; link: str = "#"; year: int = 2026

@app.get("/api/profile")
def profile():
    c = db(); d = {r["k"]: r["v"] for r in c.execute("SELECT * FROM profile")}; c.close()
    for k in ("skills", "timeline"): d[k] = json.loads(d[k])
    return d

@app.get("/api/projects")
def projects(tag: str | None = Query(None)):
    c = db(); rows = [dict(r) for r in c.execute("SELECT * FROM projects ORDER BY year DESC, id DESC")]; c.close()
    for r in rows: r["tags"] = [t for t in r["tags"].split(",") if t]
    return [r for r in rows if not tag or tag in r["tags"]]

@app.post("/api/contact", status_code=201)
def contact(m: Contact):
    if not (m.name.strip() and "@" in m.email and len(m.body.strip()) >= 10):
        raise HTTPException(422, "Add your name, a valid email, and a message of at least 10 characters.")
    c = db(); c.execute("INSERT INTO messages(name,email,body,created) VALUES(?,?,?,?)",
        (m.name[:100], m.email[:200], m.body[:4000], time.time())); c.commit(); c.close()
    return {"ok": True}

@app.post("/api/login")
def login(l: Login):
    if not secrets.compare_digest(l.password, ADMIN_PASSWORD): raise HTTPException(401, "Wrong password")
    t = secrets.token_urlsafe(24); TOKENS[t] = time.time() + 3600; return {"token": t}

@app.post("/api/projects", status_code=201)
def add_project(p: Project, authorization: str | None = Header(None)):
    admin(authorization); c = db()
    c.execute("INSERT INTO projects(title,summary,tags,link,year) VALUES(?,?,?,?,?)",
        (p.title, p.summary, p.tags, p.link, p.year)); c.commit(); c.close(); return {"ok": True}

@app.delete("/api/projects/{pid}")
def del_project(pid: int, authorization: str | None = Header(None)):
    admin(authorization); c = db(); c.execute("DELETE FROM projects WHERE id=?", (pid,)); c.commit(); c.close(); return {"ok": True}

@app.get("/api/messages")
def messages(authorization: str | None = Header(None)):
    admin(authorization); c = db()
    rows = [dict(r) for r in c.execute("SELECT * FROM messages ORDER BY created DESC")]; c.close(); return rows

app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="static")
