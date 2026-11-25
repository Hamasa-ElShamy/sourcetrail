"""Local SQLite library of passages with full-text search. Nothing leaves your machine."""
import hashlib
import os
import sqlite3
from pathlib import Path

from .extract import extract, SUPPORTED


def default_db_path():
    return os.environ.get("SOURCETRAIL_DB", str(Path.home() / ".sourcetrail.db"))


class Library:
    def __init__(self, path=None):
        self.path = path or default_db_path()
        self.db = sqlite3.connect(self.path)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, sha TEXT);
            CREATE TABLE IF NOT EXISTS passages(id INTEGER PRIMARY KEY, path TEXT, loc TEXT, text TEXT);
            CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(text, content='passages', content_rowid='id');
        """)

    @staticmethod
    def _sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()

    def add_file(self, path):
        """Index one file. Returns number of passages, or None if unchanged."""
        path = str(Path(path).resolve())
        sha = self._sha(path)
        row = self.db.execute("SELECT sha FROM files WHERE path=?", (path,)).fetchone()
        if row and row[0] == sha:
            return None
        self.remove_file(path)
        passages = extract(path)
        cur = self.db.cursor()
        for loc, text in passages:
            cur.execute("INSERT INTO passages(path, loc, text) VALUES (?,?,?)", (path, loc, text))
            cur.execute("INSERT INTO fts(rowid, text) VALUES (?,?)", (cur.lastrowid, text))
        cur.execute("INSERT OR REPLACE INTO files(path, sha) VALUES (?,?)", (path, sha))
        self.db.commit()
        return len(passages)

    def remove_file(self, path):
        path = str(Path(path).resolve())
        ids = [r[0] for r in self.db.execute("SELECT id, text FROM passages WHERE path=?", (path,))]
        for i in ids:
            t = self.db.execute("SELECT text FROM passages WHERE id=?", (i,)).fetchone()[0]
            self.db.execute("INSERT INTO fts(fts, rowid, text) VALUES ('delete', ?, ?)", (i, t))
        self.db.execute("DELETE FROM passages WHERE path=?", (path,))
        self.db.execute("DELETE FROM files WHERE path=?", (path,))
        self.db.commit()

    def add_folder(self, folder):
        """Index every supported file under a folder. Returns {path: passages or None, errors}."""
        res, errors = {}, {}
        for p in sorted(Path(folder).rglob("*")):
            if p.is_file() and p.suffix.lower() in SUPPORTED:
                try:
                    res[str(p)] = self.add_file(p)
                except Exception as e:
                    errors[str(p)] = f"{type(e).__name__}: {e}"
        return res, errors

    def files(self):
        return [r[0] for r in self.db.execute("SELECT path FROM files ORDER BY path")]

    def search(self, match_query, limit=200):
        return self.db.execute(
            "SELECT p.path, p.loc, p.text FROM fts JOIN passages p ON p.id=fts.rowid "
            "WHERE fts MATCH ? ORDER BY rank LIMIT ?", (match_query, limit)).fetchall()
