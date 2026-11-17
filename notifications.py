"""Notifications: small, real messages created by real events.

A notification is created when you finish a quiz or change your username or password.
Nothing is made up: with no events there are no notifications (and no badge).
"""
import sqlite3

from flask import Blueprint, g

from auth import login_required
from database import get_db
from security import redirect_back

bp = Blueprint("notifications", __name__, url_prefix="/notifications")


def add_notification(db, user_id, message):
    """Insert a notification (the caller commits together with its own changes)."""
    db.execute(
        "INSERT INTO notifications (user_id, message) VALUES (?, ?)", (user_id, message)
    )


@bp.app_context_processor
def inject_notifications():
    """Make `unread_count` and `notifications` available to every template."""
    if g.get("user") is None:
        return {}
    try:
        db = get_db()
        unread = db.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
            (g.user["id"],),
        ).fetchone()[0]
        recent = db.execute(
            "SELECT id, message, is_read, created_at FROM notifications "
            "WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT 10",
            (g.user["id"],),
        ).fetchall()
    except sqlite3.Error:
        return {"unread_count": 0, "notifications": []}
    return {"unread_count": unread, "notifications": recent}


@bp.post("/<int:notification_id>/read")
@login_required
def mark_read(notification_id):
    db = get_db()
    # user_id in the WHERE clause means you can only touch your own notifications.
    db.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
        (notification_id, g.user["id"]),
    )
    db.commit()
    return redirect_back("pages.home")


@bp.post("/read-all")
@login_required
def mark_all_read():
    db = get_db()
    db.execute(
        "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
        (g.user["id"],),
    )
    db.commit()
    return redirect_back("pages.home")
