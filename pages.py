"""Home dashboard, Account page, and the coming-soon placeholder pages."""
import sqlite3

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from auth import login_required
from database import get_db
from notifications import add_notification
from validators import validate_password, validate_username

bp = Blueprint("pages", __name__)


@bp.route("/")
@login_required
def home():
    db = get_db()
    notes = db.execute(
        "SELECT * FROM notes WHERE user_id = ? ORDER BY updated_at DESC, id DESC LIMIT 9",
        (g.user["id"],),
    ).fetchall()
    note_total = db.execute(
        "SELECT COUNT(*) FROM notes WHERE user_id = ?", (g.user["id"],)
    ).fetchone()[0]
    # Only real, saved attempts are ever shown here.
    recent_attempts = db.execute(
        "SELECT a.id, a.score, a.total, a.created_at, qz.title "
        "FROM attempts a JOIN quizzes qz ON qz.id = a.quiz_id "
        "WHERE a.user_id = ? ORDER BY a.created_at DESC, a.id DESC LIMIT 3",
        (g.user["id"],),
    ).fetchall()
    return render_template("dashboard.html", notes=notes, note_total=note_total,
                           recent_attempts=recent_attempts)


@bp.route("/ai-learning")
@login_required
def ai_learning():
    """UI-only placeholder. No AI is called and nothing is analyzed."""
    note_titles = get_db().execute(
        "SELECT title FROM notes WHERE user_id = ? ORDER BY updated_at DESC, id DESC LIMIT 20",
        (g.user["id"],),
    ).fetchall()
    return render_template("ai_learning.html", note_titles=note_titles)


@bp.route("/insights")
@login_required
def insights():
    """UI-only placeholder. No analytics are calculated."""
    return render_template("insights.html")


# ---------- Account ----------

def render_account(username_errors=None, password_errors=None, username_value=None, status=200):
    return render_template(
        "account.html",
        username_errors=username_errors or {},
        password_errors=password_errors or {},
        username_value=g.user["username"] if username_value is None else username_value,
    ), status


@bp.route("/account")
@login_required
def account():
    return render_account()


@bp.post("/account/username")
@login_required
def account_username():
    new_username = request.form.get("username", "").strip()
    errors = {}
    message = validate_username(new_username)
    if message:
        errors["username"] = message
    elif new_username == g.user["username"]:
        errors["username"] = "That is already your username."

    if not errors:
        db = get_db()
        try:
            db.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, g.user["id"]))
            add_notification(db, g.user["id"], f"Your username was changed to {new_username}.")
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            errors["username"] = "That username is already taken."
        else:
            flash("Username updated.", "success")
            return redirect(url_for("pages.account"))
    return render_account(username_errors=errors, username_value=new_username, status=400)


@bp.post("/account/password")
@login_required
def account_password():
    current = request.form.get("current_password", "")
    new = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")

    db = get_db()
    row = db.execute("SELECT password_hash FROM users WHERE id = ?", (g.user["id"],)).fetchone()

    errors = {}
    if not check_password_hash(row["password_hash"], current):
        errors["current_password"] = "That isn't your current password."
    message = validate_password(new)
    if message:
        errors["new_password"] = message
    elif new != confirm:
        errors["confirm_password"] = "The two new passwords do not match."

    if not errors:
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                   (generate_password_hash(new), g.user["id"]))
        add_notification(db, g.user["id"], "Your password was changed.")
        db.commit()
        flash("Password updated.", "success")
        return redirect(url_for("pages.account"))
    return render_account(password_errors=errors, status=400)
