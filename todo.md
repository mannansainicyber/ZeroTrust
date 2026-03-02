# TODO — ZeroTrust

Priority order within each section: items at the top are most urgent.

---

## 🔴 Critical — Do Before Any Public Use

- [ ] Create `requirements.txt` with pinned versions (`pip freeze > requirements.txt`)
- [ ] Create `requirements-dev.txt` for dev-only tools (pytest, black, ruff, mypy)
- [ ] Create `.env.example` listing all required env vars with descriptions
- [ ] Add `.env`, `*.db`, and `__pycache__/` to `.gitignore`
- [ ] Add CSRF protection to all forms — install Flask-WTF
- [ ] Add rate limiting to `/signin` and `/signup` — install Flask-Limiter
- [ ] Set up HTTPS — use a reverse proxy (nginx / Caddy) or deploy to a platform that provides TLS
- [ ] Set `SESSION_COOKIE_SECURE = True` and `SESSION_COOKIE_HTTPONLY = True` in app config

---

## 🟠 High Priority — Correctness & Reliability

- [ ] Fix `build_next_ref()` race condition — replace `COUNT(*)+1` with a sequence table or SQLite `RETURNING` clause
- [ ] Fix `close_issue` redirect — `request.referrer` can be spoofed; use an explicit `next` param instead
- [ ] Add `PERMANENT_SESSION_LIFETIME` config so sessions expire (e.g. 7 days)
- [ ] Validate that `issue_id` in `close_issue` belongs to the current user before closing it (authorisation check, not just authentication)
- [ ] Dates currently stored as ISO strings (`2024-12-05`) but displayed raw — add a Jinja2 filter to format them for display (e.g. "Dec 5")
- [ ] Handle `IntegrityError` on issue creation (duplicate refs) gracefully

---

## 🟡 Testing — Currently Zero Coverage

- [ ] Set up pytest with a test Flask app and in-memory SQLite DB (`conftest.py`)
- [ ] `test_auth.py`
  - [ ] Sign up with valid credentials creates a user and redirects to dashboard
  - [ ] Sign up with duplicate email shows an error
  - [ ] Sign up with short password shows a validation error
  - [ ] Sign in with correct credentials sets session
  - [ ] Sign in with wrong password returns generic error (does not reveal if email exists)
  - [ ] Sign out clears session and redirects to sign in
- [ ] `test_issues.py`
  - [ ] Creating an issue with valid data saves to DB and redirects
  - [ ] Creating an issue with missing title shows an error
  - [ ] Creating an issue with invalid priority falls back to Medium
  - [ ] Closing an issue sets status to 'closed'
  - [ ] Dashboard filters by status, priority, and project correctly
  - [ ] Unauthenticated requests to protected routes redirect to sign in
- [ ] `test_db.py`
  - [ ] `init_db()` creates tables and seeds data
  - [ ] `build_issue_query()` returns correct SQL for all filter combinations
  - [ ] `hash_password()` / `verify_password()` round-trip correctly
- [ ] Set up coverage reporting (`pytest --cov=app`) and aim for 80%+ on `app.py`

---

## 🔵 Code Quality

- [ ] Split `app.py` into modules as it grows:
  - `db.py` — connection, init, helpers
  - `auth.py` — sign in, sign up, sign out, session helpers
  - `issues.py` — dashboard, new issue, close issue
  - `validators.py` — `validate_email`, `validate_password`, etc.
- [ ] Add `mypy` type checking to CI — fix any remaining `Any` types
- [ ] Set up `pre-commit` hooks: black + ruff + mypy run automatically before each commit
- [ ] Audit all Jinja2 templates for inline styles — move to CSS classes
- [ ] Remove unused `btn-danger` class (defined in CSS but never used in templates)

---

## 🟢 Features — Backlog

- [ ] **Schema migrations** — add Alembic or Flask-Migrate so schema changes don't require wiping the DB
- [ ] **Edit issues** — allow updating title, project, or priority after creation
- [ ] **Delete issues** — hard delete with a confirmation step (or soft-delete with a `deleted_at` column)
- [ ] **Multi-user** — issues are currently shown to all users; scope them per user or per workspace
- [ ] **Pagination** — the issues list loads all rows; add cursor-based pagination for large datasets
- [ ] **Keyboard shortcuts** — `n` to open new issue, `/` to focus search (already common in issue trackers)
- [ ] **Dark mode** — CSS variables are already set up; just needs a media query or toggle
- [ ] **Export** — download issues as CSV

---

## ⚙️ Infrastructure & DevOps

- [ ] Write a `Dockerfile` for reproducible local and production builds
- [ ] Write a `Makefile` with targets: `make dev`, `make test`, `make lint`, `make format`
- [ ] Set up a GitHub Actions CI pipeline:
  - Runs `ruff`, `black --check`, `mypy`, and `pytest` on every push and PR
- [ ] Add a production deployment guide to README (e.g. Fly.io, Railway, or a VPS with nginx + gunicorn)
- [ ] Switch from SQLite to PostgreSQL for any multi-user / production deployment

---

## ✅ Done

- [x] Basic Flask app with SQLite
- [x] User authentication (sign up / sign in / sign out)
- [x] Issue creation with priority and project
- [x] Issue filtering by status, priority, and project
- [x] Four view modes: list, grid, board, timeline
- [x] Client-side search and column sorting
- [x] Replaced `hashlib.sha256` with `werkzeug.security` scrypt hashing
- [x] `secret_key` now loaded from `FLASK_SECRET_KEY` env var
- [x] `debug=True` replaced with `FLASK_DEBUG` env var
- [x] DB path now loaded from `DATABASE_URL` env var
- [x] Dates now stored as ISO 8601 (`YYYY-MM-DD`)
- [x] Login fixed to use constant-time `check_password_hash()` comparison
- [x] Added `logging` module throughout `app.py`
- [x] Added `validate_email()` and `validate_password()` with typed `ValidationError`
- [x] Added `ValidationError` custom exception class
- [x] API documentation page