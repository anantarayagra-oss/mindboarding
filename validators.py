"""Shared validation rules for usernames and passwords.

Each function returns an error message (a string) or None when the value is fine.
"""
import re

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_]{3,20}")
PASSWORD_MIN = 8
PASSWORD_MAX = 128


def validate_username(username):
    if not username:
        return "Please choose a username."
    if not USERNAME_PATTERN.fullmatch(username):
        return "Use 3 to 20 characters: letters, numbers, or underscores."
    return None


def validate_password(password):
    if len(password) < PASSWORD_MIN:
        return f"Your password needs at least {PASSWORD_MIN} characters."
    if len(password) > PASSWORD_MAX:
        return f"Your password can be at most {PASSWORD_MAX} characters."
    return None
