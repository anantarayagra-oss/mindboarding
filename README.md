# Mindboarding

An interactive note-taking and learning web app styled like a colorful school bulletin board.
Built as a CS50x Final Project with Flask, SQLite, HTML, CSS and vanilla JavaScript.

## What works today

- **Accounts:** register, log in, log out, change username and password (hashed passwords, CSRF protection).
- **My Notes:** create, view, edit, delete (with a confirmation page), search titles and content, favorite, mark complete, filter by All / Favorites / Completed. Every new account starts with nine editable sample notes.
- **Quizzes:** write your own multiple-choice quizzes, take them, get a server-calculated score with explanations, and review your quiz history.
- **Dashboard:** your most recent notes, your latest real quiz results, and the motivational note.
- **Notifications:** a real bell panel. Notifications are created only by real events (finishing a quiz, changing your username or password).

## Coming soon (placeholders only)

AI Learning, Quick AI Actions and Insights are visible but clearly marked "Coming soon". No AI is called and no analytics are calculated.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # then edit .env and set SECRET_KEY
flask --app app init-db             # optional: the app also creates tables on startup
flask --app app run --debug
```

Open http://127.0.0.1:5000 and create an account.

Generate a secret key with: `python -c "import secrets; print(secrets.token_hex(32))"`.
If `SECRET_KEY` is missing, the app uses a temporary random key for development (sessions reset on every restart).

## Tests

```bash
python -m unittest discover -v
```

The tests use Python's built-in `unittest` and a temporary database, so they never touch your real data.

## Project structure

```text
mindboarding/
├── app.py              application factory, security headers, error pages
├── auth.py             register, login, logout, login_required
├── notes.py            notes CRUD, search, favorites, completion
├── quizzes.py          quiz builder, taking, scoring, history
├── pages.py            dashboard, account, placeholder pages
├── notifications.py    real notifications
├── database.py         SQLite connection helpers and init-db command
├── schema.sql          tables, constraints, indexes
├── security.py         CSRF protection and safe redirects
├── validators.py       username / password rules
├── starter_notes.py    the nine sample notes
├── templates/          Jinja2 pages and reusable parts
├── static/css/         style.css (design system)
├── static/js/          app.js (menus, drawer, quiz builder)
├── tests/              automated tests
└── docs/PRD.md         product requirements
```

## Security notes

- Passwords are hashed with Werkzeug (`generate_password_hash`); plain passwords are never stored.
- Every form carries a CSRF token; state-changing requests without it are rejected.
- All SQL uses `?` placeholders (no string-built queries) and every user-owned query filters by `user_id`.
- Jinja2 escapes all user text; a Content-Security-Policy blocks inline scripts.
- Session cookies are `HttpOnly` and `SameSite=Lax` (set `SESSION_COOKIE_SECURE=1` behind HTTPS).
- Login errors are generic and use a dummy hash check so timing does not reveal which usernames exist.

## Known limitations

- No login rate limiting or account lockout.
- No password reset, email, or account deletion.
- Times are stored in UTC and shown as dates only.
- Quizzes cannot be edited after creation (they can be deleted).
- Fonts load from Google Fonts (system fonts are used if offline).
- The JavaScript and layout have not been checked in a real browser by the author of this code; see the review checklist.

## AI-assistance attribution

Parts of this project were written with help from Claude (Anthropic). A suggested comment for the top of each file you submit:

```python
# Mindboarding: CS50x Final Project.
# Portions of this file were generated with the assistance of Claude (Anthropic)
# and were reviewed, understood, and tested by me.
```
