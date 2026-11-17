"""Registration, login, logout and the login_required decorator.

CS50x ideas: sessions and cookies, hashing (never store plaintext passwords),
parameterized SQL (the ? placeholders) to prevent SQL injection.
"""
import functools
import sqlite3

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db
from security import is_safe_next
from starter_notes import create_starter_notes
from validators import validate_password, validate_username

bp = Blueprint("auth", __name__)

# Checking a password against this dummy hash when the username does not exist makes
# "unknown user" take about as long as "wrong password" (stops username guessing by timing).
DUMMY_HASH = generate_password_hash("not-a-real-password")


@bp.before_app_request
def load_logged_in_user():
    """Before every request: look up the logged-in user (if any) and put it in g.user."""
    g.user = None
    if request.endpoint == "static":
        return
    user_id = session.get("user_id")
    if user_id is not None:
        g.user = get_db().execute(
            "SELECT id, username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if g.user is None:  # the account no longer exists
            session.clear()


def login_required(view):
    """Decorator: send visitors who are not logged in to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            next_url = request.full_path.rstrip("?") if request.method == "GET" else None
            return redirect(url_for("auth.login", next=next_url))
        return view(**kwargs)
    return wrapped_view


@bp.route("/register", methods=("GET", "POST"))
def register():
    if g.user:
        return redirect(url_for("pages.home"))

    errors = {}
    username = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        message = validate_username(username)
        if message:
            errors["username"] = message
        message = validate_password(password)
        if message:
            errors["password"] = message
        elif password != confirm:
            errors["confirm_password"] = "The two passwords do not match."

        if not errors:
            db = get_db()
            try:
                cursor = db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                user_id = cursor.lastrowid
                create_starter_notes(db, user_id)
                db.commit()  # the user and their starter notes are saved together
            except sqlite3.IntegrityError:
                db.rollback()
                errors["username"] = "That username is already taken."
            else:
                session.clear()  # start a fresh session (prevents session fixation)
                session["user_id"] = user_id
                flash("Welcome to Mindboarding! We pinned a few sample notes to get you started.", "success")
                return redirect(url_for("pages.home"))

        return render_template("auth/register.html", errors=errors, username=username), 400

    return render_template("auth/register.html", errors=errors, username=username)


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user:
        return redirect(url_for("pages.home"))

    error = None
    username = ""
    next_url = request.args.get("next", "")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        next_url = request.form.get("next", "")

        user = get_db().execute(
            "SELECT id, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
        stored_hash = user["password_hash"] if user else DUMMY_HASH
        password_ok = check_password_hash(stored_hash, password)

        if user is None or not password_ok:
            # One generic message: never reveal which half was wrong.
            error = "That username and password don't match. Please try again."
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(next_url if is_safe_next(next_url) else url_for("pages.home"))

        return render_template("auth/login.html", error=error, username=username, next_url=next_url), 400

    return render_template("auth/login.html", error=error, username=username, next_url=next_url)


@bp.post("/logout")
def logout():
    session.clear()
    flash("You have been logged out. See you soon!", "success")
    return redirect(url_for("auth.login"))
