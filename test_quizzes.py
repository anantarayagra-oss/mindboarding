from tests.base import AppTestCase


class QuizTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.register()

    def test_create_quiz_saves_questions_and_one_correct_choice_each(self):
        response = self.make_quiz()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(self.query("SELECT id FROM questions")), 2)
        self.assertEqual(len(self.query("SELECT id FROM choices")), 5)  # empty answer boxes are skipped
        for question in self.query("SELECT id FROM questions"):
            correct = self.query("SELECT id FROM choices WHERE question_id = ? AND is_correct = 1", (question["id"],))
            self.assertEqual(len(correct), 1)

    def test_quiz_builder_validation(self):
        base = {"title": "T", "q-0-prompt": "Q?", "q-0-opt-0": "a", "q-0-opt-1": "b", "q-0-correct": "0"}
        cases = {
            "no title": ({**base, "title": ""}, "give your quiz a title"),
            "no question": ({"title": "T"}, "at least one question"),
            "one answer": ({**base, "q-0-opt-1": ""}, "at least two answers"),
            "no correct": ({k: v for k, v in base.items() if k != "q-0-correct"}, "Select which answer"),
            "empty correct": ({**base, "q-0-correct": "2"}, "marked correct"),
            "no prompt": ({**base, "q-0-prompt": ""}, "Write the question"),
        }
        for name, (data, expected) in cases.items():
            with self.subTest(name):
                response = self.post("/quizzes/new", data)
                self.assertEqual(response.status_code, 400)
                self.assertIn(expected, self.text(response))
        self.assertEqual(len(self.query("SELECT id FROM quizzes")), 0)

    def test_failed_form_keeps_what_you_typed(self):
        response = self.post("/quizzes/new", {"title": "Keep me", "q-3-prompt": "Typed question", "q-3-opt-0": "x"})
        html = self.text(response)
        self.assertIn("Keep me", html)
        self.assertIn("Typed question", html)

    def test_take_quiz_scores_on_the_server_and_saves_history(self):
        self.make_quiz()
        quiz_id = self.query("SELECT id FROM quizzes")[0]["id"]
        self.assertEqual(self.client.get(f"/quizzes/{quiz_id}/take").status_code, 200)

        response = self.post(f"/quizzes/{quiz_id}/take", self.quiz_answers(quiz_id, [1, 1]))  # one right, one wrong
        self.assertEqual(response.status_code, 302)
        attempt = self.query("SELECT * FROM attempts")[0]
        self.assertEqual((attempt["score"], attempt["total"]), (1, 2))
        self.assertEqual(len(self.query("SELECT id FROM attempt_answers")), 2)

        result = self.text(self.client.get(response.headers["Location"]))
        self.assertIn("1 of 2 correct", result)
        self.assertIn("def starts a function definition.", result)
        self.assertIn("50%", result)
        self.assertIn("Python Basics", self.text(self.client.get("/quizzes")))

    def test_perfect_score(self):
        self.make_quiz()
        quiz_id = self.query("SELECT id FROM quizzes")[0]["id"]
        self.post(f"/quizzes/{quiz_id}/take", self.quiz_answers(quiz_id, [1, 0]))
        self.assertEqual(self.query("SELECT score, total FROM attempts")[0][0], 2)

    def test_unanswered_or_tampered_submissions_are_rejected(self):
        self.make_quiz()
        self.make_quiz(title="Second quiz")
        first, second = [r["id"] for r in self.query("SELECT id FROM quizzes ORDER BY id")]
        partial = self.quiz_answers(first, [1, 0])
        partial.pop(next(iter(partial)))
        response = self.post(f"/quizzes/{first}/take", partial)
        self.assertEqual(response.status_code, 400)
        self.assertIn("answer every question", self.text(response))

        # Choice ids that belong to a different quiz must not count.
        foreign = self.quiz_answers(second, [1, 0])
        questions = self.query("SELECT id FROM questions WHERE quiz_id = ? ORDER BY position", (first,))
        tampered = {f"question-{q['id']}": list(foreign.values())[i] for i, q in enumerate(questions)}
        self.assertEqual(self.post(f"/quizzes/{first}/take", tampered).status_code, 400)
        self.assertEqual(len(self.query("SELECT id FROM attempts")), 0)

    def test_attempt_creates_notification_and_it_can_be_marked_read(self):
        self.make_quiz()
        quiz_id = self.query("SELECT id FROM quizzes")[0]["id"]
        self.post(f"/quizzes/{quiz_id}/take", self.quiz_answers(quiz_id, [1, 0]))
        html = self.text(self.client.get("/"))
        self.assertIn("You scored 2/2", html)
        self.assertIn('class="badge"', html)
        notification_id = self.query("SELECT id FROM notifications")[0]["id"]
        self.post(f"/notifications/{notification_id}/read")
        self.assertNotIn('class="badge"', self.text(self.client.get("/")))

    def test_dashboard_empty_then_real_result(self):
        self.assertIn("No quiz attempts yet", self.text(self.client.get("/")))
        self.make_quiz()
        quiz_id = self.query("SELECT id FROM quizzes")[0]["id"]
        self.post(f"/quizzes/{quiz_id}/take", self.quiz_answers(quiz_id, [1, 0]))
        html = self.text(self.client.get("/"))
        self.assertIn("100%", html)
        self.assertIn("Excellent!", html)
        self.assertNotIn("No quiz attempts yet", html)

    def test_delete_quiz_cascades(self):
        self.make_quiz()
        quiz_id = self.query("SELECT id FROM quizzes")[0]["id"]
        self.post(f"/quizzes/{quiz_id}/take", self.quiz_answers(quiz_id, [1, 0]))
        self.assertIn("attempt history", self.text(self.client.get(f"/quizzes/{quiz_id}/delete")))
        self.post(f"/quizzes/{quiz_id}/delete")
        for table in ("quizzes", "questions", "choices", "attempts", "attempt_answers"):
            self.assertEqual(len(self.query(f"SELECT id FROM {table}")), 0, table)

    def test_users_cannot_access_each_others_quizzes_or_attempts(self):
        self.make_quiz()
        quiz_id = self.query("SELECT id FROM quizzes")[0]["id"]
        self.post(f"/quizzes/{quiz_id}/take", self.quiz_answers(quiz_id, [1, 0]))
        attempt_id = self.query("SELECT id FROM attempts")[0]["id"]
        other = self.new_client("bob")
        self.assertEqual(other.get(f"/quizzes/{quiz_id}/take").status_code, 404)
        self.assertEqual(other.get(f"/quizzes/attempts/{attempt_id}").status_code, 404)
        self.assertEqual(other.get(f"/quizzes/{quiz_id}/delete").status_code, 404)
        self.assertEqual(self.post(f"/quizzes/{quiz_id}/delete", client=other).status_code, 404)
        self.assertNotIn("Python Basics", self.text(other.get("/quizzes")))
        self.assertEqual(len(self.query("SELECT id FROM quizzes")), 1)

    def test_database_allows_only_one_correct_choice_per_question(self):
        import sqlite3
        self.make_quiz()
        question_id = self.query("SELECT id FROM questions")[0]["id"]
        with self.assertRaises(sqlite3.IntegrityError):
            self.execute("INSERT INTO choices (question_id, text, is_correct, position) VALUES (?, 'dup', 1, 9)",
                         (question_id,))
