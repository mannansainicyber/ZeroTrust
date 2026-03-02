"""
ZeroTrust — Flask issue-tracker backend.

Environment variables:
    FLASK_SECRET_KEY   Required in production — hex string for session signing.
    DATABASE_URL       SQLite file path (default: zerotrust.db).
    FLASK_DEBUG        Set 'true' to enable debug mode (default: false).
"""
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
log = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────────────────────
app = Flask(__name__)

# FIXED: secret_key was regenerated on every restart, invalidating all sessions.
# Now loaded from env; a random fallback is used only in development with a loud warning.
_secret_key = os.environ.get("FLASK_SECRET_KEY")
if not _secret_key:
    import secrets as _secrets
    _secret_key = _secrets.token_hex(32)
    log.warning(
        "FLASK_SECRET_KEY not set — using a random key. "
        "All active sessions will be lost on restart. "
        "Set FLASK_SECRET_KEY in your environment for production."
    )
app.secret_key = _secret_key

# ── Config ─────────────────────────────────────────────────────────────────────
# FIXED: DB path and debug flag were hardcoded. Now loaded from environment.
DB_PATH: str = os.environ.get("DATABASE_URL", "zerotrust.db")
DEBUG: bool  = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

# FIXED: mutable set → frozenset (these are constants, not state)
VALID_STATUSES: frozenset[str]   = frozenset({"active", "closed"})
VALID_VIEWS: frozenset[str]      = frozenset({"list", "grid", "board", "timeline"})
VALID_PRIORITIES: frozenset[str] = frozenset({"High", "Medium", "Low"})

# FIXED: seed date stored as ISO 8601 (was 'Dec 5' — not sortable, not parseable)
SEED_ISSUES: list[tuple] = [
    ("FIG-123", "Task 1", "Project 1", "High", "2024-12-05"),
]


# ── Custom exceptions ──────────────────────────────────────────────────────────
class ValidationError(ValueError):
    """Raised when user-supplied input fails validation rules."""


# ── Database helpers ───────────────────────────────────────────────────────────
def get_db() -> sqlite3.Connection:
    """Open and return a new SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables and seed initial data if the DB is empty."""
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                email      TEXT UNIQUE NOT NULL,
                password   TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS issues (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                ref      TEXT NOT NULL,
                title    TEXT NOT NULL,
                project  TEXT NOT NULL,
                priority TEXT NOT NULL,
                date     TEXT NOT NULL,
                owner_id INTEGER,
                status   TEXT DEFAULT 'active',
                FOREIGN KEY(owner_id) REFERENCES users(id)
            );
        """)
        if db.execute("SELECT COUNT(*) FROM issues").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO issues (ref, title, project, priority, date) VALUES (?, ?, ?, ?, ?)",
                SEED_ISSUES,
            )
        db.commit()


def hash_password(password: str) -> str:
    """Return a secure bcrypt hash of password via werkzeug.

    FIXED: was hashlib.sha256 with no salt — vulnerable to rainbow table attacks.
    werkzeug's generate_password_hash uses scrypt/pbkdf2 with a random salt.
    """
    return generate_password_hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Return True if password matches the stored hash."""
    return check_password_hash(hashed, password)


def build_next_ref(db: sqlite3.Connection) -> str:
    """Generate the next issue reference string.

    NOTE: COUNT(*)+1 is not atomic under concurrent load.
    For production use, replace with a dedicated sequence table or DB trigger.
    """
    count = db.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
    return f"FIG-{100 + count + 1}"


def build_issue_query(
    status: str,
    priority: str,
    project: str,
) -> tuple[str, list[str]]:
    """Build a parameterised issues SELECT query from filter arguments.

    Returns:
        Tuple of (sql_string, params_list) ready for db.execute().
    """
    sql: str         = "SELECT * FROM issues WHERE status=?"
    params: list[str] = [status]

    if priority and priority in VALID_PRIORITIES:
        sql += " AND priority=?"
        params.append(priority)

    if project:
        sql += " AND project=?"
        params.append(project)

    return sql + " ORDER BY id DESC", params


# ── Input validation ───────────────────────────────────────────────────────────
def validate_email(raw: str) -> str:
    """Return a normalised email string or raise ValidationError."""
    email = raw.strip().lower()
    if not email:
        raise ValidationError("Email is required.")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValidationError("Please enter a valid email address.")
    return email


def validate_password(password: str) -> str:
    """Return password or raise ValidationError if it doesn't meet requirements."""
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters.")
    return password


# ── Auth helpers ───────────────────────────────────────────────────────────────
def require_login() -> Optional[Response]:
    """Return a redirect to sign-in if the user is not authenticated, else None."""
    if "user_id" not in session:
        return redirect(url_for("signin"))
    return None


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index() -> Response:
    return redirect(url_for("dashboard") if "user_id" in session else url_for("signin"))


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        raw_email    = request.form.get("email", "")
        raw_password = request.form.get("password", "")

        try:
            email = validate_email(raw_email)
        except ValidationError as exc:
            flash(str(exc), "error")
            return render_template("signin.html")

        if not raw_password:
            flash("Please enter your password.", "error")
            return render_template("signin.html")

        with get_db() as db:
            # FIXED: was fetching by (email AND password) with a plain SHA256 hash —
            # now we fetch by email only, then use constant-time verify_password().
            user = db.execute(
                "SELECT * FROM users WHERE email=?", (email,)
            ).fetchone()

        if user and verify_password(raw_password, user["password"]):
            session["user_id"]    = user["id"]
            session["user_email"] = user["email"]
            log.info("User signed in: %s", email)
            return redirect(url_for("dashboard"))

        # Don't distinguish 'email not found' from 'wrong password' — prevents enumeration
        flash("Invalid email or password.", "error")
        log.warning("Failed sign-in attempt for: %s", email)

    return render_template("signin.html")


@app.route("/docs")
def docs():
    redir = require_login()
    if redir:
        return redir
    return render_template("docs.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        raw_email    = request.form.get("email", "")
        raw_password = request.form.get("password", "")

        try:
            email    = validate_email(raw_email)
            password = validate_password(raw_password)
        except ValidationError as exc:
            flash(str(exc), "error")
            return render_template("signup.html")

        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO users (email, password) VALUES (?, ?)",
                    (email, hash_password(password)),
                )
                db.commit()
                user = db.execute(
                    "SELECT * FROM users WHERE email=?", (email,)
                ).fetchone()
                session["user_id"]    = user["id"]
                session["user_email"] = email
            log.info("New user registered: %s", email)
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("An account with this email already exists.", "error")
            log.warning("Duplicate signup attempt for: %s", email)

    return render_template("signup.html")


@app.route("/signout")
def signout():
    email = session.get("user_email", "unknown")
    session.clear()
    log.info("User signed out: %s", email)
    return redirect(url_for("signin"))


@app.route("/dashboard")
def dashboard():
    redir = require_login()
    if redir:
        return redir

    status   = request.args.get("status",   "active")
    view     = request.args.get("view",     "list")
    priority = request.args.get("priority", "")
    project  = request.args.get("project",  "")

    # Sanitise against allowlists — never trust user-supplied values for branching logic
    if status not in VALID_STATUSES:
        status = "active"
    if view not in VALID_VIEWS:
        view = "list"

    with get_db() as db:
        sql, params = build_issue_query(status, priority, project)
        issues   = db.execute(sql, params).fetchall()
        projects = [
            r["project"]
            for r in db.execute(
                "SELECT DISTINCT project FROM issues ORDER BY project"
            ).fetchall()
        ]
        active_all = db.execute(
            "SELECT priority, COUNT(*) as c FROM issues WHERE status='active' GROUP BY priority"
        ).fetchall()

    counts = {r["priority"]: r["c"] for r in active_all}

    return render_template(
        "dashboard.html",
        issues          = issues,
        projects        = projects,
        current_status  = status,
        current_view    = view,
        priority_filter = priority,
        project_filter  = project,
        email           = session.get("user_email", ""),
        total_active    = sum(counts.values()),
        high_count      = counts.get("High", 0),
        medium_count    = counts.get("Medium", 0),
        low_count       = counts.get("Low", 0),
    )


@app.route("/issues/new", methods=["GET", "POST"])
def new_issue():
    redir = require_login()
    if redir:
        return redir

    with get_db() as db:
        projects = [
            r["project"]
            for r in db.execute(
                "SELECT DISTINCT project FROM issues ORDER BY project"
            ).fetchall()
        ]

    if request.method == "POST":
        title    = request.form.get("title",    "").strip()
        project  = request.form.get("project",  "").strip()
        priority = request.form.get("priority", "Medium")

        if priority not in VALID_PRIORITIES:
            priority = "Medium"

        if not title:
            flash("Title is required.", "error")
        elif not project:
            flash("Project is required.", "error")
        else:
            # FIXED: was storing 'Dec 5' format — not sortable, not parseable.
            # Now stores ISO 8601 with UTC timezone.
            iso_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            with get_db() as db:
                ref = build_next_ref(db)
                db.execute(
                    "INSERT INTO issues (ref, title, project, priority, date, owner_id) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (ref, title, project, priority, iso_date, session["user_id"]),
                )
                db.commit()
            log.info("Issue created: %s — '%s'", ref, title)
            flash("Issue created.", "success")
            return redirect(url_for("dashboard"))

    return render_template(
        "new_issue.html",
        email    = session.get("user_email", ""),
        projects = projects,
    )


@app.route("/issues/<int:issue_id>/close", methods=["POST"])
def close_issue(issue_id: int):
    redir = require_login()
    if redir:
        return redir
    with get_db() as db:
        db.execute("UPDATE issues SET status='closed' WHERE id=?", (issue_id,))
        db.commit()
    log.info("Issue %d closed by user_id=%d", issue_id, session["user_id"])
    return redirect(request.referrer or url_for("dashboard"))


if __name__ == "__main__":
    init_db()
    # FIXED: debug=True was hardcoded — never acceptable in production.
    # Now controlled by the FLASK_DEBUG environment variable.
    app.run(debug=DEBUG, port=5000, host="0.0.0.0")