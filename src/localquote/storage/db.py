"""SQLite migration, transaction and integrity helpers."""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA_VERSION = 1
SCHEMA = '''
CREATE TABLE customers (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL CHECK(length(trim(name)) > 0),
 email TEXT NOT NULL DEFAULT '', phone TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
 archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1)),
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE services (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL CHECK(length(trim(name)) > 0),
 unit TEXT NOT NULL DEFAULT 'adet', unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents >= 0),
 vat_percent TEXT NOT NULL DEFAULT '20', active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
);
CREATE TABLE requests (
 id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
 message TEXT NOT NULL CHECK(length(trim(message)) > 0),
 due_date TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE quotes (
 id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
 request_id INTEGER REFERENCES requests(id) ON DELETE RESTRICT,
 status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(status IN ('DRAFT','APPROVED','EXPORTED')),
 note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT (datetime('now')),
 approved_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE quote_lines (
 id INTEGER PRIMARY KEY, quote_id INTEGER NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
 service_id INTEGER REFERENCES services(id) ON DELETE SET NULL,
 description TEXT NOT NULL, quantity TEXT NOT NULL, unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents >= 0),
 discount_percent TEXT NOT NULL, vat_percent TEXT NOT NULL
);
CREATE TABLE quote_events (
 id INTEGER PRIMARY KEY, quote_id INTEGER NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
 event TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_customers_name ON customers(name);
CREATE INDEX idx_requests_customer ON requests(customer_id);
CREATE INDEX idx_quotes_customer ON quotes(customer_id);
CREATE INDEX idx_quote_lines_quote ON quote_lines(quote_id);
'''

class DatabaseError(RuntimeError):
    pass


def open_db(path: Path | str) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            if any(conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()):
                raise DatabaseError("Bilinmeyen eski veritabanı: üzerine yazılmadı")
            conn.executescript(SCHEMA)
            conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            conn.commit()
        elif version != SCHEMA_VERSION:
            raise DatabaseError(f"Desteklenmeyen şema sürümü: {version}")
        result = conn.execute("PRAGMA quick_check").fetchone()[0]
        if result != "ok":
            raise DatabaseError("Veritabanı bütünlüğü hatalı")
        return conn
    except (sqlite3.DatabaseError, DatabaseError) as e:
        conn.close()
        raise DatabaseError(f"Veritabanı açılamadı: {e}") from e

@contextmanager
def transaction(conn: sqlite3.Connection):
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
