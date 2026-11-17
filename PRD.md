# Mindboarding: Product Requirements (v1)

## 1. Overview
Mindboarding is a web app that turns ordinary notes into an interactive learning space, presented as a colorful school bulletin board (warm cork, cream paper, pastel sticky notes, pushpins, and a yellow sticky-note mascot with nerd glasses).

## 2. Goals
- Make note-taking enjoyable and visually engaging.
- Let learners test themselves with their own quizzes.
- Keep the code understandable for a CS50x student.

## 3. Navigation
Home · My Notes · AI Learning (coming soon) · Quizzes · Insights (coming soon) · Account · Log Out

## 4. Features in scope
- **Accounts:** username and password registration, login, logout, change username, change password.
- **Notes:** create, view, edit, delete, search (title and content), favorite, mark complete, preset sticky colors. Nine editable starter notes per new account. Notes have **no levels, categories, or tags**.
- **Quizzes:** manual multiple-choice builder (2–4 answers per question, one correct answer, optional explanation), quiz taking, server-side scoring, answer explanations, quiz history, quiz deletion.
- **Dashboard:** recent notes, Quick AI Actions (placeholder), latest real quiz results, the motivational note "Small steps lead to big progress!"
- **Notifications:** real, created by real events only.

## 5. Placeholders (UI only)
AI Learning, Quick AI Actions and Insights are labeled "Coming soon". No AI calls, fake answers, fake scores, or analytics.

## 6. Technical decisions
Flask, SQLite (plain `sqlite3`), Jinja2, HTML, CSS, vanilla JavaScript. Flat project layout. CSRF protection, hashed passwords, parameterized SQL, input validation, `unittest` tests.

## 7. Out of scope for v1
AI processing, analytics, password reset, email, quiz editing, note categories/levels/tags, sharing, settings beyond Account.

## 8. Decisions made when the brief was silent
Favorite icon is a star; quizzes are not linked to notes; quizzes can be deleted but not edited; notifications come from quiz completion and account changes; CSRF is a small hand-written helper; tests use the standard-library `unittest`.
