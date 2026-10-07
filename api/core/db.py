
import json
import math
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

import numpy as np


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR = os.environ.get("APP_DATA_DIR") or os.path.join(ROOT_DIR, "storage")

DB_PATH = os.path.join(DATA_DIR, "app.db")


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash      TEXT    PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at      TEXT    NOT NULL,
    expires_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'draft',
    columns_json    TEXT    NOT NULL,
    analysis_json   TEXT,
    config_json     TEXT,
    draft_json      TEXT,
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS versions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version_no      INTEGER NOT NULL,
    filename        TEXT    NOT NULL,
    file_path       TEXT    NOT NULL,
    rows_added      INTEGER NOT NULL,
    total_rows      INTEGER NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'pending',
    result_json     TEXT,
    characteristics_json TEXT,
    error           TEXT,
    created_at      TEXT    NOT NULL,
    completed_at    TEXT,
    UNIQUE(project_id, version_no)
);

CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_versions_project ON versions(project_id);
"""


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def init_db():

    os.makedirs(DATA_DIR, exist_ok=True)

    with connect() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def connect():

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def project_dir(project_id):

    path = os.path.join(DATA_DIR, "projects", str(project_id))
    os.makedirs(path, exist_ok=True)

    return path


def _default(value):

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        value = float(value)
        return None if math.isnan(value) or math.isinf(value) else value

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, np.ndarray):
        return value.tolist()

    if hasattr(value, "isoformat"):
        return value.isoformat()

    if hasattr(value, "__dict__"):
        return value.__dict__

    return str(value)


def _clean_floats(value):

    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None

    if isinstance(value, dict):
        return {key: _clean_floats(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [_clean_floats(item) for item in value]

    return value


def to_json(value):

    if value is None:
        return None


    text = json.dumps(value, default=_default, ensure_ascii=False)

    return json.dumps(_clean_floats(json.loads(text)), ensure_ascii=False)


def from_json(text):

    if not text:
        return None

    return json.loads(text)
