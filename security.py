"""Small security helpers: CSRF tokens and safe redirects.

CSRF (cross-site request forgery): a malicious site could try to make your
browser submit a form to Mindboarding while you are logged in. Defence: every
form carries a secret random token that only our own pages know.
"""
import secrets
from urllib.parse import urlparse

from flask import abort, current_app, redirect, request, session, url_for


def generate_csrf_token():
    """Return this session's CSRF token, creating it on first use."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def csrf_protect():
    """Run before every request: reject state-changing requests without a valid token."""
    if not current_app.config.get("CSRF_ENABLED", True):
        return
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        sent = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        # compare_digest avoids leaking information through timing differences.
        if not expected or not secrets.compare_digest(sent.encode(), expected.encode()):
            abort(400)


def is_safe_next(target):
    """Allow only same-site paths like '/notes' (blocks 'https://evil.com' and '//evil.com')."""
    if not target or not target.startswith("/") or target.startswith("//"):
        return False
    if "\\" in target:
        return False
    return urlparse(target).netloc == ""


def redirect_back(default_endpoint, **values):
    """Go back to the page the form was submitted from (if it is on our site)."""
    referrer = request.referrer
    if referrer and urlparse(referrer).netloc == request.host:
        return redirect(referrer)
    return redirect(url_for(default_endpoint, **values))
