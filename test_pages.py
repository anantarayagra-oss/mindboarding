from tests.base import AppTestCase


class PageTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.register()

    def test_dashboard_has_required_content(self):
        html = self.text(self.client.get("/"))
        self.assertIn("Small steps lead to big progress!", html)
        for label in ("Summarize Note", "Explain Concept", "Brainstorm Ideas", "Create Quiz",
                      "Recent Quiz Results", "My Notes"):
            self.assertIn(label, html)
        for nav in ("Home", "My Notes", "AI Learning", "Quizzes", "Insights", "Account", "Log Out"):
            self.assertIn(nav, html)

    def test_quick_ai_actions_are_disabled_placeholders(self):
        html = self.text(self.client.get("/"))
        self.assertEqual(html.count("ai-tile ai-tile--"), 4)
        self.assertEqual(html.count("disabled aria-disabled"), 4)
        self.assertIn("Coming soon", html)

    def test_no_fake_notification_badge_or_quiz_result(self):
        html = self.text(self.client.get("/"))
        self.assertNotIn('class="badge"', html)
        self.assertIn("all caught up", html)
        self.assertNotIn("Python Functions Quiz", html)

    def test_placeholder_pages_load_and_are_clearly_inactive(self):
        ai = self.text(self.client.get("/ai-learning"))
        insights = self.text(self.client.get("/insights"))
        self.assertIn("Coming soon", ai)
        self.assertIn("not active", ai)
        self.assertIn("Coming soon", insights)
        self.assertIn("nothing is being calculated", insights)

    def test_mark_all_notifications_read(self):
        self.post("/account/username", {"username": "alice_2"})
        self.assertIn('class="badge"', self.text(self.client.get("/")))
        self.post("/notifications/read-all")
        self.assertNotIn('class="badge"', self.text(self.client.get("/")))

    def test_notifications_are_private(self):
        self.post("/account/username", {"username": "alice_2"})
        other = self.new_client("bob")
        self.assertNotIn("alice_2", self.text(other.get("/")))
        notification_id = self.query("SELECT id FROM notifications")[0]["id"]
        self.post(f"/notifications/{notification_id}/read", client=other)
        self.assertEqual(self.query("SELECT is_read FROM notifications WHERE id = ?", (notification_id,))[0][0], 0)

    def test_404_page_is_friendly(self):
        response = self.client.get("/definitely-not-here")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Page not found", self.text(response))

    def test_pages_have_one_h1_and_landmarks(self):
        for url in ("/", "/notes", "/quizzes", "/account", "/ai-learning", "/insights"):
            with self.subTest(url=url):
                html = self.text(self.client.get(url))
                self.assertEqual(html.count("<h1"), 1)
                self.assertIn('id="main"', html)
                self.assertIn('class="skip-link"', html)

    def test_database_can_be_initialised_repeatedly(self):
        from database import init_db
        with self.app.app_context():
            init_db()
            init_db()
        self.assertEqual(len(self.query("SELECT id FROM users")), 1)
