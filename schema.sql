-- Mindboarding database schema (SQLite).
-- Safe to run more than once: every statement uses IF NOT EXISTS.
-- Timestamps are stored as UTC text ("YYYY-MM-DD HH:MM:SS") by datetime('now').

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    -- COLLATE NOCASE makes "Alice" and "alice" the same username.
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE
                  CHECK (length(username) BETWEEN 3 AND 20),
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- All notes are peers: there are no levels, categories, or tags.
CREATE TABLE IF NOT EXISTS notes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title        TEXT NOT NULL CHECK (length(trim(title)) > 0 AND length(title) <= 100),
    content      TEXT NOT NULL DEFAULT '' CHECK (length(content) <= 5000),
    color        TEXT NOT NULL DEFAULT 'yellow'
                 CHECK (color IN ('yellow', 'pink', 'lavender', 'green')),
    is_favorite  INTEGER NOT NULL DEFAULT 0 CHECK (is_favorite IN (0, 1)),
    is_completed INTEGER NOT NULL DEFAULT 0 CHECK (is_completed IN (0, 1)),
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_notes_user_updated ON notes (user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS quizzes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title       TEXT NOT NULL CHECK (length(trim(title)) > 0 AND length(title) <= 100),
    description TEXT NOT NULL DEFAULT '' CHECK (length(description) <= 300),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_quizzes_user ON quizzes (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS questions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id     INTEGER NOT NULL REFERENCES quizzes (id) ON DELETE CASCADE,
    prompt      TEXT NOT NULL CHECK (length(trim(prompt)) > 0 AND length(prompt) <= 300),
    explanation TEXT NOT NULL DEFAULT '' CHECK (length(explanation) <= 300),
    position    INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_questions_quiz ON questions (quiz_id, position);

CREATE TABLE IF NOT EXISTS choices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
    text        TEXT NOT NULL CHECK (length(trim(text)) > 0 AND length(text) <= 150),
    is_correct  INTEGER NOT NULL DEFAULT 0 CHECK (is_correct IN (0, 1)),
    position    INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_choices_question ON choices (question_id, position);
-- At most ONE correct choice per question (the app also requires at least one).
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_correct_choice
    ON choices (question_id) WHERE is_correct = 1;

CREATE TABLE IF NOT EXISTS attempts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    quiz_id    INTEGER NOT NULL REFERENCES quizzes (id) ON DELETE CASCADE,
    score      INTEGER NOT NULL CHECK (score >= 0),
    total      INTEGER NOT NULL CHECK (total > 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (score <= total)
);
CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS attempt_answers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id  INTEGER NOT NULL REFERENCES attempts (id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
    choice_id   INTEGER NOT NULL REFERENCES choices (id) ON DELETE CASCADE,
    UNIQUE (attempt_id, question_id)
);

-- Real notifications only. They are created by real events (see notifications.py).
CREATE TABLE IF NOT EXISTS notifications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    message    TEXT NOT NULL,
    is_read    INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications (user_id, is_read, created_at DESC);
