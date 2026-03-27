import os
import sqlite3
from datetime import datetime, timedelta, timezone
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, flash, redirect, render_template, request, session, url_for
from Helpers import *

# ------------------------------------------------------------------
app = Flask(__name__)

_secret_key = os.environ.get("FLASK_SECRET_KEY")
if not _secret_key:
    import secrets as _secrets
    _secret_key = _secrets.token_hex(32)
    print("use secret key bruh i aint joking.")
app.secret_key = _secret_key
# -------------------------------------------------------------------
DEBUG: bool = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["SESSION_COOKIE_SECURE"]      = False
app.config["SESSION_COOKIE_HTTPONLY"]    = True

VALID_STATUSES: frozenset[str] = frozenset({"active", "closed"})
VALID_VIEWS: frozenset[str]    = frozenset({"list", "grid", "board", "timeline"})


limiter = Limiter(
    get_remote_address,  
    app=app,             
    default_limits=["40 per minute"],
    storage_uri="memory://"
)
# ------------------------------------------------------------------

@app.template_filter("fmtdate")
def fmtdate(val):
    return datetime.strptime(val, "%Y-%m-%d").strftime("%b %d")


@app.route("/")
def index():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("signin"))


@app.route("/signin", methods=["GET", "POST"])
@limiter.limit("10 per minute")
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

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email=?", (email,)
            ).fetchone()

        if user and verify_password(raw_password, user["password"]):
            session.permanent     = True
            session["user_id"]    = user["id"]
            session["user_email"] = user["email"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("signin.html")


@app.route("/docs")
def docs():
    return render_template("docs.html")


@app.route("/signup", methods=["GET", "POST"])
@limiter.limit("10 per minute")
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
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (email, password) VALUES (?, ?)",
                    (email, hash_password(password)),
                )
                conn.commit()
                user = conn.execute(
                    "SELECT * FROM users WHERE email=?", (email,)
                ).fetchone()
                session["user_id"]    = user["id"]
                session["user_email"] = email
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("An account with this email already exists.", "error")

    return render_template("signup.html")


@app.route("/signout")
def signout():
    session.clear()
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

    if status not in VALID_STATUSES:
        status = "active"
    if view not in VALID_VIEWS:
        view = "list"

    user_id = session["user_id"]

    with get_db() as conn:
        sql, params = build_issue_query(status, priority, project, user_id)
        issues     = conn.execute(sql, params).fetchall()
        projects   = [
            r["project"]
            for r in conn.execute(
                "SELECT DISTINCT project FROM issues WHERE owner_id=? ORDER BY project",
                (user_id,),
            ).fetchall()
        ]
        active_all = conn.execute(
            "SELECT priority, COUNT(*) as c FROM issues WHERE status='active' AND owner_id=? GROUP BY priority",
            (user_id,),
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

    with get_db() as conn:
        projects = [
            r["project"]
            for r in conn.execute(
                "SELECT DISTINCT project FROM issues WHERE owner_id=? ORDER BY project",
                (session["user_id"],),
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
            iso_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            with get_db() as conn:
                ref = build_next_ref(conn)
                conn.execute(
                    "INSERT INTO issues (ref, title, project, priority, date, owner_id) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (ref, title, project, priority, iso_date, session["user_id"]),
                )
                conn.commit()
            flash("Issue created.", "success")
            return redirect(url_for("dashboard"))

    return render_template(
        "new_issue.html",
        email    = session.get("user_email", ""),
        projects = projects,
    )

@app.route("/issues/<int:issue_id>/close", methods=["GET", "POST"])
def close_issue(issue_id: int):
    redir = require_login()
    if redir:
        return redir

    if request.method == "POST":
        
        with get_db() as conn:
            conn.execute(
                "UPDATE issues SET status='closed' WHERE id=? AND owner_id=?",
                (issue_id, session["user_id"]),
            )
            conn.commit()
        return redirect(url_for("dashboard"))

    
    return render_template("close_confirm.html", issue_id=issue_id)
    

if __name__ == "__main__":
    init_db()
    app.run(debug=DEBUG, port=5000, host="0.0.0.0")