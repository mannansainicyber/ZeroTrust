# ZeroTrust

A lightweight issue-tracking web app built with Flask and SQLite. Create, filter, and close issues across projects with multiple view modes (list, grid, board, timeline).

---

## Stack

- **Backend** — Python 3.10+, Flask
- **Database** — SQLite via the standard `sqlite3` module
- **Frontend** — Jinja2 templates, vanilla JS, CSS custom properties
- **Auth** — Email + password with scrypt hashing (via `werkzeug.security`)

---

## Prerequisites

- Python 3.10 or higher
- pip
- A terminal

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/mannansainicyber/ZeroTrust.git
cd ZeroTrust
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set environment variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `FLASK_SECRET_KEY` | **Yes** | A long random hex string for signing sessions. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | No | Path to the SQLite file (default: `zerotrust.db`) |
| `FLASK_DEBUG` | No | Set to `true` for debug mode — **never in production** |

> ⚠️ Never commit your `.env` file. It is already in `.gitignore`.

### 5. Run the app

```bash
python app.py
```

The app will be available at `http://localhost:5000`. On first run, the database and tables are created automatically and seeded with a sample issue.

---

## Project Structure

```
ZeroTrust/
├── app.py                  # All routes, DB helpers, auth logic
├── requirements.txt        # Pinned production dependencies
├── requirements-dev.txt    # Dev-only: pytest, black, ruff, mypy
├── .env.example            # Required environment variable template
├── .gitignore
├── zerotrust.db            # Created at runtime — not committed
├── static/
│   └── css/
│       ├── base.css        # Design tokens, shared components
│       └── dashboard.css   # Dashboard-specific layout
└── templates/
    ├── base.html           # HTML shell
    ├── macros.html         # Reusable Jinja2 macros (badges, pills, buttons)
    ├── dashboard.html      # Main issues view (list / grid / board / timeline)
    ├── new_issue.html      # Create issue form
    ├── signin.html         # Auth — sign in
    ├── signup.html         # Auth — sign up
    └── docs.html           # API documentation page
```

---

## Features

- **Authentication** — Sign up, sign in, sign out. Passwords hashed with scrypt + salt.
- **Issues** — Create issues with title, project, and priority (High / Medium / Low).
- **Filtering** — Filter by status (active / closed), priority, and project.
- **Views** — Four view modes: List, Grid, Board (grouped by priority), Timeline (grouped by date).
- **Search** — Client-side search across title, project, and ref in list and grid views.
- **Sorting** — Click any column header in list view to sort ascending / descending.
- **Close issues** — Mark any active issue as closed from any view.

---

## Development

### Run with debug mode

```bash
FLASK_DEBUG=true python app.py
```

### Lint and format

```bash
ruff check .          # linting
black .               # formatting
mypy app.py           # type checking
```

### Run tests

```bash
pytest
pytest --cov=app      # with coverage report
```

---

## Security Notes

- Passwords are hashed with **scrypt via werkzeug** — not MD5, SHA1, or plain SHA256.
- All SQL uses **parameterised queries** — no string interpolation.
- `FLASK_SECRET_KEY` must be set in the environment. The app will warn at startup if it falls back to a random key.
- `FLASK_DEBUG` defaults to `false`. Never set it to `true` in production — it exposes an interactive Python console on error pages.
- Failed logins return a generic "Invalid email or password" message regardless of whether the email exists, to prevent user enumeration.

---

## Known Limitations

- `build_next_ref()` uses `COUNT(*)+1` to generate issue refs — this has a race condition under concurrent writes. For production, replace with a sequence table or SQLite's `RETURNING` clause.
- No CSRF protection on forms. Add Flask-WTF for production use.
- No rate limiting on auth endpoints. Add Flask-Limiter for production use.
- No database migrations. Schema changes require a manual DB reset in development.
- Sessions do not expire. Add a `PERMANENT_SESSION_LIFETIME` config for production.

---

## Contributing

This is a solo project. If you're reading this and want to suggest something, open an issue.

---

## License

MIT — see `LICENSE`.