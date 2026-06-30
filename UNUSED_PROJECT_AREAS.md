# Removed Legacy Project Areas

The production source tree is now centered on:

- `backend/`
- `frontend/`
- `.github/workflows/`
- `docker-compose.yml`
- `README.md`

Removed duplicate or orphaned areas:

- `web/` - alternate Next.js app duplicate.
- `frontend_old/` - old frontend snapshot.
- `api/`, `dashboard/`, `models/`, `usage/` - older top-level app modules not wired into the active FastAPI/Next.js stack.
- `governance/`, `monitoring/`, `infrastructure/`, `scripts/`, `tests/` - orphaned scaffolding not used by the current production app.
- `docs/docs/` nested duplicates were removed with the old docs nesting.
- `backend/create_db.py` - replaced by Alembic migrations.
- `backend/Init.py` - empty placeholder.
- `structure.txt` - generated structure dump.
- `backend/wefindbest.db` - obsolete SQLite local database.

Current backend tests live in `backend/tests/`.
