"""Shared helpers for the test suite (standard-library unittest, no extra packages)."""
import os
import re
import sqlite3
import tempfile
import unittest

from app import create_app


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret", "DATABASE": self.db_path})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    # ----- request helpers (every POST carries a valid CSRF token) -----
    def post(self, url, data=None, client=None, **kwargs):
        client = client or self.client
        with client.session_transaction() as session:
            session.setdefault("csrf_token", "test-token")
            token = session["csrf_token"]
        payload = dict(data or {})
        payload["csrf_token"] = token
        return client.post(url, data=payload, **kwargs)

    def register(self, username="alice", password="password123", client=None):
        return self.post("/register", {"username": username, "password": password,
                                       "confirm_password": password}, client=client)

    def login(self, username="alice", password="password123", client=None, **extra):
        return self.post("/login", {"username": username, "password": password, **extra}, client=client)

    def new_client(self, username):
        """A second, independent browser with its own registered user."""
        other = self.app.test_client()
        self.register(username, client=other)
        return other

    # ----- database helpers -----
    def query(self, sql, params=()):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            return connection.execute(sql, params).fetchall()
        finally:
            connection.close()

    def execute(self, sql, params=()):
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute(sql, params)
            connection.commit()
        finally:
            connection.close()

    def user_id(self, username="alice"):
        return self.query("SELECT id FROM users WHERE username = ?", (username,))[0]["id"]

    def note_id(self, title, username="alice"):
        rows = self.query("SELECT id FROM notes WHERE title = ? AND user_id = ?",
                          (title, self.user_id(username)))
        return rows[0]["id"]

    # ----- content helpers -----
    def text(self, response):
        return response.get_data(as_text=True)

    def make_quiz(self, client=None, title="Python Basics"):
        """Create a 2-question quiz; the correct answers are 'B' (q1) and 'A' (q2)."""
        return self.post("/quizzes/new", {
            "title": title, "description": "Practice",
            "q-0-prompt": "Which keyword defines a function?",
            "q-0-opt-0": "func", "q-0-opt-1": "def", "q-0-opt-2": "lambda", "q-0-opt-3": "",
            "q-0-correct": "1", "q-0-explanation": "def starts a function definition.",
            "q-1-prompt": "What does len('abc') return?",
            "q-1-opt-0": "3", "q-1-opt-1": "2", "q-1-opt-2": "", "q-1-opt-3": "",
            "q-1-correct": "0", "q-1-explanation": "",
        }, client=client)

    def quiz_answers(self, quiz_id, picks):
        """Build form data choosing the answer at each position in `picks` (e.g. [1, 0])."""
        questions = self.query("SELECT id FROM questions WHERE quiz_id = ? ORDER BY position", (quiz_id,))
        data = {}
        for question, pick in zip(questions, picks):
            choices = self.query("SELECT id FROM choices WHERE question_id = ? ORDER BY position",
                                 (question["id"],))
            data[f"question-{question['id']}"] = str(choices[pick]["id"])
        return data


def csrf_token_in(html):
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return match.group(1) if match else None
