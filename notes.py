"""Notes: create, read, edit, delete, search, favorite and complete.

Every query includes "user_id = ?" so people only ever see their own notes.
"""
from flask import (Blueprint, abort, flash, g, redirect, render_template,
                   request, url_for)

from auth import login_required
from database import get_db
from security import redirect_back

bp = Blueprint("notes", __name__, url_prefix="/notes")

COLORS = ("yellow", "pink", "lavender", "green")
FILTERS = ("all", "favorites", "completed")
TITLE_MAX = 100
CONTENT_MAX = 5000
SEARCH_MAX = 100


def escape_like(text):
    """Make %, _ and \\ literal so searching for '%' does not match everything."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_note_or_404(note_id):
    """Fetch one of the current user's notes, or answer 404 (also for other people's notes)."""
    note = get_db().execute(
        "SELECT * FROM notes WHERE id = ? AND user_id = ?", (note_id, g.user["id"])
    ).fetchone()
    if note is None:
        abort(404)
    return note


def read_note_form():
    """Read and validate the note form. Returns (values, errors)."""
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").replace("\r\n", "\n").strip()
    color = request.form.get("color", "yellow")

    errors = {}
    if not title:
        errors["title"] = "Please give your note a title."
    elif len(title) > TITLE_MAX:
        errors["title"] = f"Titles can be at most {TITLE_MAX} characters."
    if len(content) > CONTENT_MAX:
        errors["content"] = f"Notes can be at most {CONTENT_MAX} characters."
    if color not in COLORS:
        errors["color"] = "Please pick one of the colors shown."
    return {"title": title, "content": content, "color": color}, errors


@bp.route("")
@login_required
def index():
    query = request.args.get("q", "").strip()[:SEARCH_MAX]
    active = request.args.get("filter", "all")
    if active not in FILTERS:
        active = "all"

    sql = "SELECT * FROM notes WHERE user_id = ?"
    params = [g.user["id"]]
    if query:
        sql += " AND (title LIKE ? ESCAPE '\\' OR content LIKE ? ESCAPE '\\')"
        pattern = f"%{escape_like(query)}%"
        params += [pattern, pattern]
    if active == "favorites":
        sql += " AND is_favorite = 1"
    elif active == "completed":
        sql += " AND is_completed = 1"
    sql += " ORDER BY updated_at DESC, id DESC"

    db = get_db()
    notes = db.execute(sql, params).fetchall()
    counts = db.execute(
        "SELECT COUNT(*) AS total, "
        "COALESCE(SUM(is_favorite), 0) AS favorites, "
        "COALESCE(SUM(is_completed), 0) AS completed "
        "FROM notes WHERE user_id = ?",
        (g.user["id"],),
    ).fetchone()
    return render_template("notes/index.html", notes=notes, counts=counts, q=query, active=active)


@bp.route("/new", methods=("GET", "POST"))
@login_required
def new():
    form = {"title": "", "content": "", "color": "yellow"}
    errors = {}
    if request.method == "POST":
        form, errors = read_note_form()
        if not errors:
            db = get_db()
            cursor = db.execute(
                "INSERT INTO notes (user_id, title, content, color) VALUES (?, ?, ?, ?)",
                (g.user["id"], form["title"], form["content"], form["color"]),
            )
            db.commit()
            flash("Note pinned to your board.", "success")
            return redirect(url_for("notes.view", note_id=cursor.lastrowid))
        return render_template("notes/form.html", form=form, errors=errors, colors=COLORS, editing=False), 400
    return render_template("notes/form.html", form=form, errors=errors, colors=COLORS, editing=False)


@bp.route("/<int:note_id>")
@login_required
def view(note_id):
    return render_template("notes/view.html", note=get_note_or_404(note_id))


@bp.route("/<int:note_id>/edit", methods=("GET", "POST"))
@login_required
def edit(note_id):
    note = get_note_or_404(note_id)
    form = {"title": note["title"], "content": note["content"], "color": note["color"]}
    errors = {}
    if request.method == "POST":
        form, errors = read_note_form()
        if not errors:
            db = get_db()
            db.execute(
                "UPDATE notes SET title = ?, content = ?, color = ?, updated_at = datetime('now') "
                "WHERE id = ? AND user_id = ?",
                (form["title"], form["content"], form["color"], note_id, g.user["id"]),
            )
            db.commit()
            flash("Changes saved.", "success")
            return redirect(url_for("notes.view", note_id=note_id))
        return render_template("notes/form.html", form=form, errors=errors, colors=COLORS,
                               editing=True, note=note), 400
    return render_template("notes/form.html", form=form, errors=errors, colors=COLORS,
                           editing=True, note=note)


@bp.route("/<int:note_id>/delete", methods=("GET", "POST"))
@login_required
def delete(note_id):
    note = get_note_or_404(note_id)
    if request.method == "POST":
        db = get_db()
        db.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, g.user["id"]))
        db.commit()
        flash(f"Deleted “{note['title']}”.", "success")
        return redirect(url_for("notes.index"))
    # GET shows a confirmation page, so nothing is deleted by accident.
    return render_template(
        "confirm.html",
        heading="Delete this note?",
        message=f"“{note['title']}” will be permanently deleted. This cannot be undone.",
        action=url_for("notes.delete", note_id=note_id),
        cancel_url=url_for("notes.view", note_id=note_id),
        button_label="Delete note",
    )


@bp.post("/<int:note_id>/favorite")
@login_required
def toggle_favorite(note_id):
    get_note_or_404(note_id)
    db = get_db()
    # 1 - 0 = 1 and 1 - 1 = 0, so this flips the value. updated_at is NOT changed,
    # so favoriting does not reshuffle your board.
    db.execute(
        "UPDATE notes SET is_favorite = 1 - is_favorite WHERE id = ? AND user_id = ?",
        (note_id, g.user["id"]),
    )
    db.commit()
    return redirect_back("notes.index")


@bp.post("/<int:note_id>/complete")
@login_required
def toggle_complete(note_id):
    get_note_or_404(note_id)
    db = get_db()
    db.execute(
        "UPDATE notes SET is_completed = 1 - is_completed WHERE id = ? AND user_id = ?",
        (note_id, g.user["id"]),
    )
    db.commit()
    return redirect_back("notes.index")
