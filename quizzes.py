"""Manual multiple-choice quizzes: build, take, score on the server, history.

There is no AI here: you write the questions yourself.
The score is always calculated on the server from the database, never trusted from the browser.
"""
import re

from flask import (Blueprint, abort, flash, g, redirect, render_template,
                   request, url_for)

from auth import login_required
from database import get_db
from notifications import add_notification

bp = Blueprint("quizzes", __name__, url_prefix="/quizzes")

MAX_QUESTIONS = 20
OPTIONS_PER_QUESTION = 4
TITLE_MAX = 100
DESCRIPTION_MAX = 300
PROMPT_MAX = 300
OPTION_MAX = 150
EXPLANATION_MAX = 300

# Form fields are named like q-0-prompt, q-0-opt-2, q-0-correct, q-0-explanation.
QUESTION_KEY = re.compile(r"q-(\d{1,3})-prompt")


# ---------- helpers ----------

def blank_question(index):
    return {"index": index, "prompt": "", "explanation": "",
            "options": [""] * OPTIONS_PER_QUESTION, "correct": None, "errors": []}


def read_quiz_form():
    """Parse the quiz builder form. Returns (title, description, questions, errors)."""
    form = request.form
    title = form.get("title", "").strip()
    description = form.get("description", "").strip()

    errors = {}
    if not title:
        errors["title"] = "Please give your quiz a title."
    elif len(title) > TITLE_MAX:
        errors["title"] = f"Titles can be at most {TITLE_MAX} characters."
    if len(description) > DESCRIPTION_MAX:
        errors["description"] = f"Descriptions can be at most {DESCRIPTION_MAX} characters."

    indexes = sorted({int(m.group(1)) for key in form.keys()
                      if (m := QUESTION_KEY.fullmatch(key))})
    if not indexes:
        errors["questions"] = "Add at least one question."
    elif len(indexes) > MAX_QUESTIONS:
        errors["questions"] = f"A quiz can have at most {MAX_QUESTIONS} questions."
        indexes = indexes[:MAX_QUESTIONS]

    questions = []
    valid_correct = {str(i) for i in range(OPTIONS_PER_QUESTION)}
    for n in indexes:
        options = [form.get(f"q-{n}-opt-{m}", "").strip() for m in range(OPTIONS_PER_QUESTION)]
        raw_correct = form.get(f"q-{n}-correct", "")
        question = {
            "index": n,
            "prompt": form.get(f"q-{n}-prompt", "").strip(),
            "explanation": form.get(f"q-{n}-explanation", "").strip(),
            "options": options,
            "correct": int(raw_correct) if raw_correct in valid_correct else None,
            "errors": [],
        }
        problems = question["errors"]
        if not question["prompt"]:
            problems.append("Write the question.")
        elif len(question["prompt"]) > PROMPT_MAX:
            problems.append(f"Questions can be at most {PROMPT_MAX} characters.")
        if sum(1 for text in options if text) < 2:
            problems.append("Add at least two answers.")
        if any(len(text) > OPTION_MAX for text in options):
            problems.append(f"Answers can be at most {OPTION_MAX} characters.")
        if question["correct"] is None:
            problems.append("Select which answer is correct.")
        elif not options[question["correct"]]:
            problems.append("The answer marked correct can't be empty.")
        if len(question["explanation"]) > EXPLANATION_MAX:
            problems.append(f"Explanations can be at most {EXPLANATION_MAX} characters.")
        questions.append(question)

    if any(q["errors"] for q in questions):
        errors["questions"] = errors.get("questions") or "Please fix the highlighted questions."
    return title, description, questions, errors


def get_quiz_or_404(quiz_id):
    quiz = get_db().execute(
        "SELECT * FROM quizzes WHERE id = ? AND user_id = ?", (quiz_id, g.user["id"])
    ).fetchone()
    if quiz is None:
        abort(404)
    return quiz


def load_questions(quiz_id):
    """Return the quiz's questions as dicts, each with a 'choices' list, in order."""
    db = get_db()
    questions = [dict(row) for row in db.execute(
        "SELECT * FROM questions WHERE quiz_id = ? ORDER BY position, id", (quiz_id,)
    ).fetchall()]
    by_id = {q["id"]: q for q in questions}
    for q in questions:
        q["choices"] = []
    rows = db.execute(
        "SELECT c.* FROM choices c JOIN questions q ON q.id = c.question_id "
        "WHERE q.quiz_id = ? ORDER BY c.position, c.id", (quiz_id,)
    ).fetchall()
    for row in rows:
        by_id[row["question_id"]]["choices"].append(dict(row))
    return questions


# ---------- routes ----------

@bp.route("")
@login_required
def index():
    db = get_db()
    quizzes = db.execute(
        "SELECT qz.id, qz.title, qz.description, qz.created_at, "
        "  (SELECT COUNT(*) FROM questions WHERE quiz_id = qz.id) AS question_count, "
        "  (SELECT COUNT(*) FROM attempts WHERE quiz_id = qz.id) AS attempt_count "
        "FROM quizzes qz WHERE qz.user_id = ? ORDER BY qz.created_at DESC, qz.id DESC",
        (g.user["id"],),
    ).fetchall()
    history = db.execute(
        "SELECT a.id, a.score, a.total, a.created_at, qz.title "
        "FROM attempts a JOIN quizzes qz ON qz.id = a.quiz_id "
        "WHERE a.user_id = ? ORDER BY a.created_at DESC, a.id DESC LIMIT 50",
        (g.user["id"],),
    ).fetchall()
    return render_template("quizzes/index.html", quizzes=quizzes, history=history)


@bp.route("/new", methods=("GET", "POST"))
@login_required
def create():
    title, description, errors = "", "", {}
    questions = [blank_question(0)]

    if request.method == "POST":
        title, description, questions, errors = read_quiz_form()
        if not questions:
            questions = [blank_question(0)]
        if not errors:
            db = get_db()
            cursor = db.execute(
                "INSERT INTO quizzes (user_id, title, description) VALUES (?, ?, ?)",
                (g.user["id"], title, description),
            )
            quiz_id = cursor.lastrowid
            for position, q in enumerate(questions):
                cursor = db.execute(
                    "INSERT INTO questions (quiz_id, prompt, explanation, position) VALUES (?, ?, ?, ?)",
                    (quiz_id, q["prompt"], q["explanation"], position),
                )
                question_id = cursor.lastrowid
                choice_position = 0
                for m, text in enumerate(q["options"]):
                    if text:  # skip empty answer boxes
                        db.execute(
                            "INSERT INTO choices (question_id, text, is_correct, position) VALUES (?, ?, ?, ?)",
                            (question_id, text, 1 if m == q["correct"] else 0, choice_position),
                        )
                        choice_position += 1
            db.commit()  # quiz, questions and choices are saved together or not at all
            flash("Quiz created. Ready when you are!", "success")
            return redirect(url_for("quizzes.index"))

    next_index = max((q["index"] for q in questions), default=-1) + 1
    status = 400 if errors else 200
    return render_template("quizzes/create.html", title=title, description=description,
                           questions=questions, errors=errors, next_index=next_index,
                           max_questions=MAX_QUESTIONS, blank=blank_question("__N__")), status


@bp.route("/<int:quiz_id>/take", methods=("GET", "POST"))
@login_required
def take(quiz_id):
    quiz = get_quiz_or_404(quiz_id)
    questions = load_questions(quiz_id)
    if not questions:
        abort(404)

    if request.method == "POST":
        selected, chosen = {}, {}
        for q in questions:
            raw = request.form.get(f"question-{q['id']}", "")
            selected[q["id"]] = raw
            for choice in q["choices"]:  # only accept choices that belong to THIS question
                if str(choice["id"]) == raw:
                    chosen[q["id"]] = choice

        if len(chosen) < len(questions):
            flash("Please answer every question before submitting.", "error")
            return render_template("quizzes/take.html", quiz=quiz, questions=questions,
                                   selected=selected), 400

        score = sum(1 for choice in chosen.values() if choice["is_correct"])
        total = len(questions)
        db = get_db()
        cursor = db.execute(
            "INSERT INTO attempts (user_id, quiz_id, score, total) VALUES (?, ?, ?, ?)",
            (g.user["id"], quiz_id, score, total),
        )
        attempt_id = cursor.lastrowid
        for question_id, choice in chosen.items():
            db.execute(
                "INSERT INTO attempt_answers (attempt_id, question_id, choice_id) VALUES (?, ?, ?)",
                (attempt_id, question_id, choice["id"]),
            )
        add_notification(db, g.user["id"], f"You scored {score}/{total} on “{quiz['title']}”.")
        db.commit()
        return redirect(url_for("quizzes.result", attempt_id=attempt_id))

    return render_template("quizzes/take.html", quiz=quiz, questions=questions, selected={})


@bp.route("/attempts/<int:attempt_id>")
@login_required
def result(attempt_id):
    db = get_db()
    attempt = db.execute(
        "SELECT a.*, qz.title AS quiz_title, qz.id AS quiz_id "
        "FROM attempts a JOIN quizzes qz ON qz.id = a.quiz_id "
        "WHERE a.id = ? AND a.user_id = ?",
        (attempt_id, g.user["id"]),
    ).fetchone()
    if attempt is None:
        abort(404)

    review = [dict(row) for row in db.execute(
        "SELECT q.id AS question_id, q.prompt, q.explanation, aa.choice_id AS chosen_id "
        "FROM attempt_answers aa JOIN questions q ON q.id = aa.question_id "
        "WHERE aa.attempt_id = ? ORDER BY q.position, q.id",
        (attempt_id,),
    ).fetchall()]
    by_id = {item["question_id"]: item for item in review}
    for item in review:
        item["choices"] = []
    choice_rows = db.execute(
        "SELECT c.* FROM choices c WHERE c.question_id IN "
        "(SELECT question_id FROM attempt_answers WHERE attempt_id = ?) "
        "ORDER BY c.position, c.id",
        (attempt_id,),
    ).fetchall()
    for row in choice_rows:
        by_id[row["question_id"]]["choices"].append(dict(row))
    for item in review:
        item["was_correct"] = any(c["id"] == item["chosen_id"] and c["is_correct"]
                                  for c in item["choices"])
    return render_template("quizzes/result.html", attempt=attempt, review=review)


@bp.route("/<int:quiz_id>/delete", methods=("GET", "POST"))
@login_required
def delete(quiz_id):
    quiz = get_quiz_or_404(quiz_id)
    if request.method == "POST":
        db = get_db()
        # ON DELETE CASCADE also removes the quiz's questions, choices and attempts.
        db.execute("DELETE FROM quizzes WHERE id = ? AND user_id = ?", (quiz_id, g.user["id"]))
        db.commit()
        flash(f"Deleted “{quiz['title']}”.", "success")
        return redirect(url_for("quizzes.index"))
    return render_template(
        "confirm.html",
        heading="Delete this quiz?",
        message=f"“{quiz['title']}” and all of its attempt history will be permanently deleted.",
        action=url_for("quizzes.delete", quiz_id=quiz_id),
        cancel_url=url_for("quizzes.index"),
        button_label="Delete quiz",
    )
