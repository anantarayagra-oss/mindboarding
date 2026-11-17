"""Database helpers: one SQLite connection per request.

CS50x idea: SQL (SELECT / INSERT / UPDATE / DELETE), foreign keys, and
the habit of closing resources when you are done with them.
"""
import sqlite3

import click
from flask import current_app, g


def get_db():
    """Return this request's database connection (opening it the first time)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        # Rows behave like dictionaries: row["title"]
        g.db.row_factory = sqlite3.Row
        # SQLite ignores foreign keys unless we turn them on for each connection.
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    """Close the connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create all tables from schema.sql (safe to run repeatedly)."""
    db = get_db()
    with current_app.open_resource("schema.sql") as schema_file:
        db.executescript(schema_file.read().decode("utf-8"))


@click.command("init-db")
def init_db_command():
    """Command line: flask --app app init-db"""
    init_db()
    click.echo("Database ready.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
