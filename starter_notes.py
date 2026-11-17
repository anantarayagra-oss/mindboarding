"""The nine editable starter notes every new account receives.

They are ordinary notes (no levels, no categories). Users can edit or delete them.
"""

STARTER_NOTES = [
    ("Daily Journal", "Reflect on today's progress.", "yellow"),
    ("Math Basics", "Review fractions and decimals.", "pink"),
    ("Healthy Habits", "Drink more water and exercise.", "lavender"),
    ("Study Plan", "Finish chapter 4.", "lavender"),
    ("Python Practice", "Try 5 more exercises.", "yellow"),
    ("Project Ideas", "Build a study app.", "green"),
    ("Data Science", "Explore datasets.", "pink"),
    ("Reading List", "Read Clean Code.", "lavender"),
    ("Career Goals", "Become a data scientist.", "yellow"),
]


def create_starter_notes(db, user_id):
    """Insert the starter notes (the caller commits).

    The notes board sorts newest first, so we insert in reverse order:
    "Daily Journal" is saved last and therefore appears first.
    """
    for title, content, color in reversed(STARTER_NOTES):
        db.execute(
            "INSERT INTO notes (user_id, title, content, color) VALUES (?, ?, ?, ?)",
            (user_id, title, content, color),
        )
