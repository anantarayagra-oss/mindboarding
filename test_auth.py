from tests.base import AppTestCase, csrf_token_in


class AuthTests(AppTestCase):
    def test_register_logs_in_and_creates_nine_starter_notes(self):
        response = self.register()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        notes = self.query("SELECT title FROM notes WHERE user_id = ?", (self.user_id(),))
        self.assertEqual(len(notes), 9)
        self.assertIn("Welcome", self.text(self.client.get("/")))

    def test_password_is_hashed_not_stored_in_plain_text(self):
        self.register(password="password123")
        stored = self.query("SELECT password_hash FROM users")[0]["password_hash"]
        self.assertNotIn("password123", stored)
        self.assertGreater(len(stored), 30)

    def test_duplicate_username_is_rejected_case_insensitively(self):
        self.register("alice")
        other = self.app.test_client()
        response = self.register("ALICE", client=other)
        self.assertEqual(response.status_code, 400)
        self.assertIn("already taken", self.text(response))
        self.assertEqual(len(self.query("SELECT id FROM users")), 1)

    def test_register_validation(self):
        cases = [
            ({"username": "ab", "password": "password123", "confirm_password": "password123"}, "3 to 20"),
            ({"username": "bad name!", "password": "password123", "confirm_password": "password123"}, "3 to 20"),
            ({"username": "carol", "password": "short", "confirm_password": "short"}, "at least 8"),
            ({"username": "carol", "password": "password123", "confirm_password": "different1"}, "do not match"),
        ]
        for data, expected in cases:
            with self.subTest(data=data):
                response = self.post("/register", data)
                self.assertEqual(response.status_code, 400)
                self.assertIn(expected, self.text(response))
        self.assertEqual(len(self.query("SELECT id FROM users")), 0)

    def test_login_success_and_failure_use_a_generic_message(self):
        self.register()
        self.client.post("/logout", data={"csrf_token": "x"})  # rejected (bad token), still logged in
        bad_user = self.post("/login", {"username": "nobody", "password": "password123"},
                             client=self.app.test_client())
        other = self.app.test_client()
        self.register("bob", client=other)
        wrong_pw = self.post("/login", {"username": "bob", "password": "wrong-password"},
                             client=self.app.test_client())
        self.assertEqual(bad_user.status_code, 400)
        self.assertEqual(wrong_pw.status_code, 400)
        self.assertIn("Please try again", self.text(bad_user))
        self.assertIn("Please try again", self.text(wrong_pw))

    def test_login_then_redirects_to_safe_next_only(self):
        self.register()
        fresh = self.app.test_client()
        ok = self.login(client=fresh, next="/notes")
        self.assertEqual(ok.headers["Location"], "/notes")
        for bad in ("https://evil.example", "//evil.example", "/\\evil"):
            with self.subTest(next=bad):
                other = self.app.test_client()
                response = self.login(client=other, next=bad)
                self.assertEqual(response.headers["Location"], "/")

    def test_protected_pages_redirect_to_login(self):
        for url in ("/", "/notes", "/notes/new", "/quizzes", "/quizzes/new", "/account",
                    "/ai-learning", "/insights"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/login", response.headers["Location"])

    def test_logout_requires_post_and_clears_session(self):
        self.register()
        self.assertEqual(self.client.get("/logout").status_code, 405)
        response = self.post("/logout")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", self.client.get("/").headers["Location"])

    def test_post_without_csrf_token_is_rejected(self):
        response = self.client.post("/register", data={"username": "eve", "password": "password123",
                                                        "confirm_password": "password123"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(self.query("SELECT id FROM users")), 0)

    def test_forms_contain_a_csrf_token(self):
        self.assertTrue(csrf_token_in(self.text(self.client.get("/login"))))

    def test_security_headers_are_set(self):
        response = self.client.get("/login")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])


class AccountTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.register()

    def test_change_password(self):
        bad = self.post("/account/password", {"current_password": "nope-nope1", "new_password": "newpassword1",
                                               "confirm_password": "newpassword1"})
        self.assertEqual(bad.status_code, 400)
        self.assertIn("your current password", self.text(bad))

        mismatch = self.post("/account/password", {"current_password": "password123", "new_password": "newpassword1",
                                                    "confirm_password": "other-pass1"})
        self.assertEqual(mismatch.status_code, 400)

        good = self.post("/account/password", {"current_password": "password123", "new_password": "newpassword1",
                                                "confirm_password": "newpassword1"})
        self.assertEqual(good.status_code, 302)

        old_login = self.login(password="password123", client=self.app.test_client())
        new_login = self.login(password="newpassword1", client=self.app.test_client())
        self.assertEqual(old_login.status_code, 400)
        self.assertEqual(new_login.status_code, 302)

    def test_change_username(self):
        self.new_client("bob")
        taken = self.post("/account/username", {"username": "BOB"})
        self.assertEqual(taken.status_code, 400)
        self.assertIn("already taken", self.text(taken))

        invalid = self.post("/account/username", {"username": "x"})
        self.assertEqual(invalid.status_code, 400)

        ok = self.post("/account/username", {"username": "alice_2"})
        self.assertEqual(ok.status_code, 302)
        self.assertEqual(self.query("SELECT username FROM users WHERE id = ?", (self.user_id("alice_2"),))[0][0], "alice_2")

    def test_account_changes_create_real_notifications(self):
        self.post("/account/username", {"username": "alice_2"})
        self.post("/account/password", {"current_password": "password123", "new_password": "newpassword1",
                                         "confirm_password": "newpassword1"})
        messages = [r["message"] for r in self.query("SELECT message FROM notifications")]
        self.assertEqual(len(messages), 2)
        self.assertTrue(any("username" in m for m in messages))
        self.assertTrue(any("password" in m for m in messages))

    def test_account_page_says_account_not_settings(self):
        html = self.text(self.client.get("/account"))
        self.assertIn("Account", html)
        self.assertNotIn("Settings", html)
