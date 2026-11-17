from tests.base import AppTestCase


class NotesTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.register()

    def test_starter_notes_appear_in_order_without_levels(self):
        html = self.text(self.client.get("/notes"))
        self.assertLess(html.index("Daily Journal"), html.index("Career Goals"))
        for word in ("Level 1", "Level 2", "Level 3"):
            self.assertNotIn(word, html)
        self.assertNotIn("Level 1", self.text(self.client.get("/")))

    def test_create_view_edit_delete(self):
        created = self.post("/notes/new", {"title": "Biology", "content": "Cells\r\nare small", "color": "green"})
        self.assertEqual(created.status_code, 302)
        note_id = self.note_id("Biology")
        self.assertIn("Cells", self.text(self.client.get(f"/notes/{note_id}")))

        self.execute("UPDATE notes SET updated_at = '2020-01-01 00:00:00' WHERE id = ?", (note_id,))
        edited = self.post(f"/notes/{note_id}/edit", {"title": "Biology 101", "content": "Updated", "color": "pink"})
        self.assertEqual(edited.status_code, 302)
        row = self.query("SELECT * FROM notes WHERE id = ?", (note_id,))[0]
        self.assertEqual((row["title"], row["color"]), ("Biology 101", "pink"))
        self.assertNotEqual(row["updated_at"], "2020-01-01 00:00:00")

        self.assertIn("permanently deleted", self.text(self.client.get(f"/notes/{note_id}/delete")))
        self.assertEqual(len(self.query("SELECT id FROM notes WHERE id = ?", (note_id,))), 1)  # GET deletes nothing
        self.post(f"/notes/{note_id}/delete")
        self.assertEqual(len(self.query("SELECT id FROM notes WHERE id = ?", (note_id,))), 0)

    def test_note_validation(self):
        cases = [
            ({"title": "", "content": "x", "color": "yellow"}, "title"),
            ({"title": "t" * 101, "content": "x", "color": "yellow"}, "at most 100"),
            ({"title": "ok", "content": "c" * 5001, "color": "yellow"}, "at most 5000"),
            ({"title": "ok", "content": "x", "color": "red"}, "pick one"),
        ]
        for data, expected in cases:
            with self.subTest(expected=expected):
                response = self.post("/notes/new", data)
                self.assertEqual(response.status_code, 400)
                self.assertIn(expected, self.text(response))
        self.assertEqual(len(self.query("SELECT id FROM notes")), 9)

    def test_html_in_notes_is_escaped(self):
        self.post("/notes/new", {"title": "<script>alert(1)</script>", "content": "<b>x</b>", "color": "yellow"})
        html = self.text(self.client.get("/notes"))
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_favorite_and_complete_toggles_persist(self):
        note_id = self.note_id("Math Basics")
        self.post(f"/notes/{note_id}/favorite")
        self.post(f"/notes/{note_id}/complete")
        row = self.query("SELECT is_favorite, is_completed FROM notes WHERE id = ?", (note_id,))[0]
        self.assertEqual((row[0], row[1]), (1, 1))
        favorites = self.text(self.client.get("/notes?filter=favorites"))
        completed = self.text(self.client.get("/notes?filter=completed"))
        self.assertIn("Math Basics", favorites)
        self.assertNotIn("Daily Journal", favorites)
        self.assertIn("Math Basics", completed)
        self.post(f"/notes/{note_id}/favorite")
        self.assertEqual(self.query("SELECT is_favorite FROM notes WHERE id = ?", (note_id,))[0][0], 0)

    def test_toggles_do_not_change_updated_at(self):
        note_id = self.note_id("Math Basics")
        self.execute("UPDATE notes SET updated_at = '2020-01-01 00:00:00' WHERE id = ?", (note_id,))
        self.post(f"/notes/{note_id}/favorite")
        self.assertEqual(self.query("SELECT updated_at FROM notes WHERE id = ?", (note_id,))[0][0], "2020-01-01 00:00:00")

    def test_search_title_content_and_case(self):
        by_title = self.text(self.client.get("/notes?q=python"))
        self.assertIn("Python Practice", by_title)
        self.assertNotIn("Daily Journal", by_title)
        by_content = self.text(self.client.get("/notes?q=FRACTIONS"))
        self.assertIn("Math Basics", by_content)
        self.assertIn("No notes match", self.text(self.client.get("/notes?q=zzzzzz")))

    def test_search_treats_percent_and_underscore_literally(self):
        self.assertIn("No notes match", self.text(self.client.get("/notes?q=%25")))
        self.assertIn("No notes match", self.text(self.client.get("/notes?q=_")))

    def test_invalid_filter_falls_back_to_all(self):
        self.assertIn("Daily Journal", self.text(self.client.get("/notes?filter=nonsense")))

    def test_users_cannot_touch_each_others_notes(self):
        self.post("/notes/new", {"title": "Private Plan", "content": "secret", "color": "pink"})
        other = self.new_client("bob")
        note_id = self.note_id("Private Plan", "alice")
        for method, url in (("get", f"/notes/{note_id}"), ("get", f"/notes/{note_id}/edit"),
                            ("get", f"/notes/{note_id}/delete")):
            self.assertEqual(getattr(other, method)(url).status_code, 404, url)
        for url in (f"/notes/{note_id}/edit", f"/notes/{note_id}/delete",
                    f"/notes/{note_id}/favorite", f"/notes/{note_id}/complete"):
            self.assertEqual(self.post(url, {"title": "hacked", "content": "", "color": "pink"}, client=other).status_code, 404, url)
        row = self.query("SELECT title, is_favorite FROM notes WHERE id = ?", (note_id,))[0]
        self.assertEqual((row[0], row[1]), ("Private Plan", 0))
        self.assertNotIn("Private Plan", self.text(other.get("/notes?q=Private")))

    def test_dashboard_shows_nine_notes_and_new_button(self):
        for i in range(3):
            self.post("/notes/new", {"title": f"Extra {i}", "content": "", "color": "yellow"})
        html = self.text(self.client.get("/"))
        self.assertIn("Showing your 9 most recent notes of 12", html)
        self.assertIn("New note", html)
