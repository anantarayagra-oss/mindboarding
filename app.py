"""Mindboarding: application factory.

Run it with:   flask --app app run --debug
"""
import os
import secrets
from datetime import datetime

from flask import Flask, render_template

import auth
import database
import notes
import notifications
import pages
import quizzes
import security

ERROR_MESSAGES = {
    400: ("That didn't work", "Your page may have expired. Go back, refresh it, and try again."),
    403: ("Not allowed", "You don't have access to that page."),
    404: ("Page not found", "We couldn't find that page. It may have been moved or deleted."),
    405: ("That isn't allowed here", "Please use the buttons and links on the page."),
    413: ("That was too big", "Please send something smaller."),
    500: ("Something went wrong on our side", "Your notes are safe. Please try again in a moment."),
}


def pretty_date(value):
    """'2026-11-16 08:30:00' -> 'Nov 16, 2026' (stored times are UTC)."""
    try:
        moment = datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value or ""
    return f"{moment:%b} {moment.day}, {moment.year}"


def percent(score, total):
    return round(100 * score / total) if total else 0


def score_label(pct):
    if pct >= 90:
        return "Excellent!"
    if pct >= 70:
        return "Great job!"
    if pct >= 50:
        return "Good effort"
    return "Keep practicing"


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key and not (test_config and test_config.get("SECRET_KEY")):
        # Safe fallback for local development: random, never stored in the code.
        # Sessions reset whenever the server restarts. Set SECRET_KEY in .env to keep them.
        secret_key = secrets.token_hex(32)
        app.logger.warning("SECRET_KEY is not set; using a temporary random key. See .env.example.")

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        DATABASE=os.path.join(app.instance_path, "mindboarding.db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE") == "1",
        MAX_CONTENT_LENGTH=1024 * 1024,  # reject requests larger than 1 MB
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    database.init_app(app)
    with app.app_context():
        database.init_db()  # creates the tables the first time

    app.before_request(security.csrf_protect)
    for module in (auth, pages, notes, quizzes, notifications):
        app.register_blueprint(module.bp)

    app.jinja_env.globals["csrf_token"] = security.generate_csrf_token
    app.jinja_env.filters.update(pretty_date=pretty_date, percent=percent, score_label=score_label)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; "
            "style-src 'self' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; img-src 'self' data:; "
            "form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        return response

    def show_error(error):
        code = getattr(error, "code", 500)
        title, message = ERROR_MESSAGES.get(code, ERROR_MESSAGES[500])
        return render_template("error.html", code=code, title=title, message=message), code

    for code in ERROR_MESSAGES:
        app.register_error_handler(code, show_error)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
