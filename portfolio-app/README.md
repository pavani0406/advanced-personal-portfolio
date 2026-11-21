# Advanced Personal Portfolio (full stack)

**Stack:** FastAPI + SQLite backend, vanilla JS single-page frontend (served by the same app).

## Run
```bash
pip install -r requirements.txt
ADMIN_PASSWORD=choose-a-strong-one uvicorn backend.main:app --reload
```
Open http://localhost:8000. Admin panel: http://localhost:8000/#admin (add/delete projects, read contact messages).

## Customize
Edit the seed `profile` dict and projects in `backend/main.py` (before first run), or delete `portfolio.db` and rerun to reseed.

## API
GET /api/profile · GET /api/projects?tag= · POST /api/contact · POST /api/login · POST/DELETE /api/projects (admin) · GET /api/messages (admin)

## Deploy
Any host that runs Python (Render, Railway, Fly.io). Set `ADMIN_PASSWORD` and `DB_PATH` (on a persistent disk).
