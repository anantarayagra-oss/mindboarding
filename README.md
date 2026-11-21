# Mindboarding

**Organize your notes. Practice what you learn. Track your progress.**

Mindboarding is a web-based learning platform designed to help students organize study materials, practice through quizzes, and monitor their learning progress. Inspired by a colorful school bulletin board, it combines note-taking, interactive quizzes, and AI-powered learning tools in one application.

Built as a CS50x Final Project using Python, Flask, SQLite, HTML, CSS, JavaScript, and Google's Gemini API.

## Features

### 1. User Accounts
- Register, log in, and log out.
- Change username and password.
- Password hashing and session-based authentication.
- CSRF protection for state-changing requests.

### 2. Notes Management
- Create, view, edit, and delete personal notes.
- Search notes by title and content.
- Mark notes as favorites or completed.
- Filter notes by status.
- Access nine editable starter notes when creating an account.

### 3. Quiz System
- Create multiple-choice quizzes manually.
- Generate quizzes from personal notes using Gemini AI.
- Select the number of generated questions.
- Take quizzes with server-calculated scores.
- Review correct answers and explanations.
- View previous quiz attempts and results.
- Delete quizzes.

### 4. AI Learning Tools

Mindboarding integrates Google's Gemini API to provide three learning tools:

- **AI Note Summarizer:** Generates structured summaries containing an overview, key points, important details, and a conclusion.
- **Explain Concept:** Provides step-by-step explanations of study topics with examples and a recap.
- **Brainstorm Ideas:** Helps generate and organize ideas related to a topic.

Long notes are processed in chunks during summarization to support larger study materials.

### 5. Learning Insights
- View personal learning statistics.
- Track average, best, and latest quiz scores.
- Review performance for individual quizzes.
- View recent score progress.
- Filter score history by quiz.
- Review recent learning activity.

All learning insights are scoped to the authenticated user's own data.

### 6. Dashboard and Notifications

The dashboard provides an overview of recent notes and quiz activity, alongside motivational content. The notification panel displays relevant account and learning events and allows users to mark notifications as read.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Flask | Web framework |
| SQLite | Database |
| HTML and Jinja2 | Page structure and templates |
| CSS | Styling and responsive interface |
| JavaScript | Client-side interactions |
| Google Gemini API | AI-powered learning tools |
| `google-genai` | Gemini Python SDK |
| `python-dotenv` | Environment variable loading |
| pytest | Automated testing |

## Project Structure

```text
mindboarding/
├── app.py
├── auth.py
├── base.py
├── database.py
├── notes.py
├── notifications.py
├── pages.py
├── quizzes.py
├── security.py
├── starter_notes.py
├── validators.py
├── schema.sql
├── services/
│   ├── __init__.py
│   ├── ai_tools.py
│   ├── note_summarizer.py
│   └── quiz_generator.py
├── templates/
│   ├── auth/
│   ├── ai/
│   ├── notes/
│   ├── quizzes/
│   └── shared templates
├── static/
│   ├── css/style.css
│   └── js/app.js
├── tests/
├── docs/
│   └── PRD.md
├── requirements.txt
├── .env.example
└── README.md
```

## Requirements

- Python 3.10 or newer.
- pip.
- A Google Gemini API key for AI features.

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd mindboarding
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
```

Activate it:

**Linux / macOS**
```bash
source venv/bin/activate
```

**Windows**
```powershell
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install pytest
```

### 4. Configure environment variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure the following variables in `.env`:

```env
SECRET_KEY=your-long-random-secret-key
GEMINI_API_KEY=your-gemini-api-key
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Never commit `.env` or expose API credentials.

### 5. Run the application

```bash
flask --app app run --debug
```

Open the application at:

```text
http://127.0.0.1:5000
```

Register an account to start using Mindboarding.

## Configuration

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session signing key |
| `GEMINI_API_KEY` | Credential for Gemini-powered features |
| `GEMINI_TIMEOUT_MS` | Optional Gemini request timeout |
| `SESSION_COOKIE_SECURE` | Set to `1` when using HTTPS |

If `SECRET_KEY` is not configured, the application generates a temporary random key. Sessions may not persist across server restarts.

## Running Tests

Run the automated test suite:

```bash
python -m pytest -q
```

The tests use isolated temporary databases and mock AI providers where appropriate. Normal test execution does not require live Gemini API requests.

## Security

Mindboarding includes several security measures:

- Werkzeug password hashing.
- CSRF protection for state-changing requests.
- User-scoped database operations.
- Parameterized SQL queries.
- Jinja2 autoescaping.
- Content Security Policy and additional security headers.
- `HttpOnly` and `SameSite=Lax` session cookies.

For production deployment, configure a persistent secret key, HTTPS, secure cookies, and an appropriate production WSGI server.

## Current Limitations

- No password reset or email verification.
- No account deletion workflow.
- No login rate limiting or account lockout.
- Quizzes cannot currently be edited after creation.
- The application enforces a 1 MB maximum request body size.
- AI features require a valid Gemini API key and an internet connection.
- AI-generated content should be reviewed for accuracy before being used as study material.

## AI Assistance Attribution

AI tools were used during development to assist with brainstorming, code suggestions, debugging, and documentation. The project author reviewed and adapted suggestions, made implementation decisions, and tested the application. The author remains responsible for understanding the submitted code and explaining its functionality.

---

**Mindboarding — Make learning more organized, interactive, and meaningful.**
