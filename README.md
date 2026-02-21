
# ╔══════════════════════════════════════════════════════════╗
# ║                                                          ║
# ║   ░▒▓█  ZEROTRUST  █▓▒░                                  ║
# ║   issue tracking. brutally simple.                       ║
# ║                                                          ║
# ╚══════════════════════════════════════════════════════════╝

<div align="center">

![Python](https://img.shields.io/badge/python-3.8+-black?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/flask-3.x-black?style=flat-square&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-embedded-black?style=flat-square&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-black?style=flat-square)

**A minimal Flask issue tracker. Ships fast. Zero config. Zero fluff.**

</div>

---

## ⚡ Quickstart

```bash
# clone & enter
git clone https://github.com/mannansainicyber/ZeroTrust && cd ZeroTrust

# install deps (one line)
pip install -r requirements.txt

# launch
python app.py
```

Open **http://localhost:5000** — sign up, and you're tracking issues in under 60 seconds.

> The SQLite database (`zerotrust.db`) is created automatically on first run, pre-seeded with 1 demo issues across 1 projects.

---

## 🗂 Views

ZeroTrust has four ways to look at your work:

| View | Description |
|------|-------------|
| **List** | Dense table with sortable columns and inline close actions |
| **Grid** | Card layout — good for skimming titles at a glance |
| **Board** | Kanban columns split by priority: High · Medium · Low |
| **Timeline** | Issues grouped chronologically by date |

Switch between them with the toggle in the toolbar, or via the sidebar nav.

---

## 🔍 Filtering

```
/dashboard?status=active&priority=High&project=Acme+GTM&view=grid
```

Every combination of filters is URL-addressable — bookmark a filtered view, share a link, or hit Back and land exactly where you were.

| Param | Values |
|-------|--------|
| `status` | `active` · `closed` |
| `priority` | `High` · `Medium` · `Low` |
| `project` | any project name |
| `view` | `list` · `grid` · `board` · `timeline` |

The four stat cards at the top of the dashboard are also clickable priority filters.

---

## 🗺 Routes

```
GET  /                        → redirect to dashboard or signin
GET  /signin                  → sign in page
POST /signin                  → authenticate
GET  /signup                  → create account page
POST /signup                  → register + auto-login
GET  /signout                 → clear session, redirect to signin
GET  /dashboard               → issue tracker (auth required)
GET  /issues/new              → new issue form (auth required)
POST /issues/new              → create issue, redirect to dashboard
POST /issues/<id>/close       → mark issue closed, redirect back
```

---

## 🏗 Project Structure

```
zerotrust/
├── app.py                  # all routes, DB setup, helpers
├── requirements.txt
├── zerotrust.db            # auto-created on first run
│
├── static/
│   └── css/
│       ├── base.css        # design tokens + shared components
│       └── dashboard.css   # layout, views, table, board, timeline
│
└── templates/
    ├── base.html           # HTML shell, loads base.css
    ├── macros.html         # DRY Jinja2 macros (badges, pills, avatars)
    ├── dashboard.html      # main issue tracker, all four views
    ├── new_issue.html      # create issue form
    ├── signin.html         # sign in
    └── signup.html         # sign up
```

---

## 🧱 Architecture notes

**Single-file backend** — `app.py` stays intentionally small. All DB logic, route handlers, and helpers live in one file. If it grows beyond ~300 lines, split it.

**CSS design tokens** — Every colour, shadow, and spacing value is defined once in `base.css` as a CSS custom property. Neither templates nor components hardcode values.

**Jinja2 macros** — Shared UI components (`priority_pill`, `project_badge`, `close_btn`, etc.) live in `macros.html` and are imported where needed. No copy-pasted HTML blocks.

**URL-first filtering** — All filter/view state lives in the URL. No session state, no JS-only state, no surprises.

---

## 🔐 Auth notes

Passwords are SHA-256 hashed. For production, replace with `bcrypt` or `argon2`:

```python
# swap this:
hashlib.sha256(pw.encode()).hexdigest()

# for this:
import bcrypt
bcrypt.hashpw(pw.encode(), bcrypt.gensalt())
```

The `secret_key` regenerates on every restart (sessions invalidated on redeploy). Pin it to an env var for persistent sessions:

```python
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
```

---

## 🛠 Extending

**Add a new field to issues** — add a column to the `CREATE TABLE` statement in `init_db()`, update the `INSERT` in `new_issue`, add it to `new_issue.html`, and render it in `dashboard.html`.

**Add a new view** — add it to `VALID_VIEWS` in `app.py`, add a sidebar link in `dashboard.html`, and add an `{% elif current_view == 'yourview' %}` block in the main content section.

**Multi-user issue ownership** — the `owner_id` foreign key is already in the schema. Wire up the avatar column in the dashboard and filter by `owner_id = session['user_id']` to scope views per user.

---

<div align="center">

```
built with Flask · SQLite · Geist · zero dependencies worth mentioning
```

</div>
