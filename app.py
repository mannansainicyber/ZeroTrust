from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os, hashlib, secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
DB = 'zerotrust.db'

# ── Constants ──────────────────────────────────────────────
VALID_STATUSES  = {'active', 'closed'}
VALID_VIEWS     = {'list', 'grid', 'board', 'timeline'}
VALID_PRIORITIES = {'High', 'Medium', 'Low'}

SEED_ISSUES = [
    ('FIG-123', 'Task 1','Project 1','High','Dec 5'),
]

# ── DB helpers ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript('''
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
        ''')
        if db.execute('SELECT COUNT(*) FROM issues').fetchone()[0] == 0:
            db.executemany(
                'INSERT INTO issues (ref,title,project,priority,date) VALUES (?,?,?,?,?)',
                SEED_ISSUES
            )
        db.commit()

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def next_ref(db) -> str:
    count = db.execute('SELECT COUNT(*) FROM issues').fetchone()[0]
    return f'FIG-{100 + count + 1}'

def require_login():
    """Returns redirect if not logged in, else None."""
    if 'user_id' not in session:
        return redirect(url_for('signin'))

def build_issue_query(status, priority, project):
    """Build a parameterised issues query from filter args. Returns (sql, params)."""
    sql    = 'SELECT * FROM issues WHERE status=?'
    params = [status]
    if priority and priority in VALID_PRIORITIES:
        sql += ' AND priority=?'
        params.append(priority)
    if project:
        sql += ' AND project=?'
        params.append(project)
    return sql + ' ORDER BY id DESC', params

# ── Routes ─────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('signin'))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('signin.html')
        with get_db() as db:
            user = db.execute(
                'SELECT * FROM users WHERE email=? AND password=?',
                (email, hash_pw(password))
            ).fetchone()
        if user:
            session['user_id']    = user['id']
            session['user_email'] = user['email']
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('signin.html')

@app.route('/docs')
def docs():
    redir = require_login()
    if redir:
        return redir
    return render_template('docs.html')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('signup.html')
        try:
            with get_db() as db:
                db.execute(
                    'INSERT INTO users (email,password) VALUES (?,?)',
                    (email, hash_pw(password))
                )
                db.commit()
                user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
                session['user_id']    = user['id']
                session['user_email'] = email
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'error')
    return render_template('signup.html')

@app.route('/signout')
def signout():
    session.clear()
    return redirect(url_for('signin'))

@app.route('/dashboard')
def dashboard():
    redir = require_login()
    if redir:
        return redir

    # Validated query params
    status   = request.args.get('status',   'active')
    view     = request.args.get('view',     'list')
    priority = request.args.get('priority', '')
    project  = request.args.get('project',  '')

    if status not in VALID_STATUSES: status = 'active'
    if view   not in VALID_VIEWS:    view   = 'list'

    with get_db() as db:
        sql, params = build_issue_query(status, priority, project)
        issues   = db.execute(sql, params).fetchall()
        projects = [r['project'] for r in db.execute(
            'SELECT DISTINCT project FROM issues ORDER BY project'
        ).fetchall()]

        # Counts for stat cards (always over active issues, unfiltered by priority)
        active_all = db.execute(
            "SELECT priority, COUNT(*) as c FROM issues WHERE status='active' GROUP BY priority"
        ).fetchall()

    counts = {r['priority']: r['c'] for r in active_all}

    return render_template(
        'dashboard.html',
        issues          = issues,
        projects        = projects,
        current_status  = status,
        current_view    = view,
        priority_filter = priority,
        project_filter  = project,
        email           = session.get('user_email', ''),
        total_active    = sum(counts.values()),
        high_count      = counts.get('High', 0),
        medium_count    = counts.get('Medium', 0),
        low_count       = counts.get('Low', 0),
    )

@app.route('/issues/new', methods=['GET', 'POST'])
def new_issue():
    redir = require_login()
    if redir:
        return redir

    with get_db() as db:
        projects = [r['project'] for r in db.execute(
            'SELECT DISTINCT project FROM issues ORDER BY project'
        ).fetchall()]

    if request.method == 'POST':
        title    = request.form.get('title',    '').strip()
        project  = request.form.get('project',  '').strip()
        priority = request.form.get('priority', 'Medium')
        if priority not in VALID_PRIORITIES:
            priority = 'Medium'

        if title and project:
            with get_db() as db:
                db.execute(
                    'INSERT INTO issues (ref,title,project,priority,date,owner_id) VALUES (?,?,?,?,?,?)',
                    (next_ref(db), title, project, priority,
                     datetime.now().strftime('%b %-d'), session['user_id'])
                )
                db.commit()
            flash('Issue created.', 'success')
            return redirect(url_for('dashboard'))
        flash('Title and project are required.', 'error')

    return render_template('new_issue.html',
                           email=session.get('user_email', ''),
                           projects=projects)

@app.route('/issues/<int:issue_id>/close', methods=['POST'])
def close_issue(issue_id):
    redir = require_login()
    if redir:
        return redir
    with get_db() as db:
        db.execute("UPDATE issues SET status='closed' WHERE id=?", (issue_id,))
        db.commit()
    # Redirect back to wherever the user came from
    return redirect(request.referrer or url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000, host='0.0.0.0')
