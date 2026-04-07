"""
Creates the orgs and contacts tables that are managed=False in Django
(owned by the pipeline's db.py). On Railway these tables don't exist
until the pipeline runs, so we create them here via RunSQL.
Uses CREATE TABLE IF NOT EXISTS so it's safe to run multiple times.
"""
from django.db import migrations


CREATE_ORGS = """
CREATE TABLE IF NOT EXISTS orgs (
    ein             TEXT PRIMARY KEY,
    name            TEXT,
    city            TEXT,
    state           TEXT,
    zipcode         TEXT,
    revenue         INTEGER DEFAULT 0,
    assets          INTEGER DEFAULT 0,
    ntee_code       TEXT,
    website         TEXT,
    mission         TEXT,
    has_property    INTEGER DEFAULT 0,
    fiscal_year_end TEXT,
    source          TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
"""

CREATE_CONTACTS = """
CREATE TABLE IF NOT EXISTS contacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ein             TEXT REFERENCES orgs(ein),
    full_name       TEXT,
    first_name      TEXT,
    last_name       TEXT,
    title           TEXT,
    compensation    INTEGER DEFAULT 0,
    email           TEXT,
    email_status    TEXT,
    email_source    TEXT,
    priority        INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now'))
);
"""

CREATE_CONTACT_UNIQUE_IDX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_contact_unique
ON contacts(ein, full_name);
"""


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(CREATE_ORGS,        reverse_sql="DROP TABLE IF EXISTS orgs;"),
        migrations.RunSQL(CREATE_CONTACTS,    reverse_sql="DROP TABLE IF EXISTS contacts;"),
        migrations.RunSQL(CREATE_CONTACT_UNIQUE_IDX, reverse_sql="DROP INDEX IF EXISTS idx_contact_unique;"),
    ]
