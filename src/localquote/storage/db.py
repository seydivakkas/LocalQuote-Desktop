"""SQLite migration, transaction and integrity helpers."""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA_VERSION = 2
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


MIGRATION_V2 = (
 "CREATE TABLE IF NOT EXISTS service_packages(id INTEGER PRIMARY KEY,name TEXT NOT NULL CHECK(length(trim(name))>0),active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)))",
 "CREATE TABLE IF NOT EXISTS package_items(package_id INTEGER NOT NULL REFERENCES service_packages(id) ON DELETE CASCADE,service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE RESTRICT,quantity TEXT NOT NULL,PRIMARY KEY(package_id,service_id))",
 "CREATE TABLE IF NOT EXISTS request_revisions(id INTEGER PRIMARY KEY,request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE RESTRICT,version INTEGER NOT NULL,event TEXT NOT NULL,snapshot_json TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT (datetime('now')),UNIQUE(request_id,version))",
 "CREATE TABLE IF NOT EXISTS quote_revisions(id INTEGER PRIMARY KEY,quote_id INTEGER NOT NULL REFERENCES quotes(id) ON DELETE RESTRICT,version INTEGER NOT NULL,event TEXT NOT NULL,snapshot_json TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT (datetime('now')),UNIQUE(quote_id,version))",
 "CREATE TRIGGER IF NOT EXISTS lock_line_insert BEFORE INSERT ON quote_lines WHEN (SELECT status FROM quotes WHERE id=NEW.quote_id)!='DRAFT' BEGIN SELECT RAISE(ABORT,'approved line immutable'); END",
 "CREATE TRIGGER IF NOT EXISTS lock_line_update BEFORE UPDATE ON quote_lines WHEN (SELECT status FROM quotes WHERE id=OLD.quote_id)!='DRAFT' OR (SELECT status FROM quotes WHERE id=NEW.quote_id)!='DRAFT' BEGIN SELECT RAISE(ABORT,'approved line immutable'); END",
 "CREATE TRIGGER IF NOT EXISTS lock_line_delete BEFORE DELETE ON quote_lines WHEN (SELECT status FROM quotes WHERE id=OLD.quote_id)!='DRAFT' BEGIN SELECT RAISE(ABORT,'approved line immutable'); END",
 "CREATE TRIGGER IF NOT EXISTS lock_quote_header BEFORE UPDATE OF customer_id,request_id,note ON quotes WHEN OLD.status!='DRAFT' BEGIN SELECT RAISE(ABORT,'approved quote header immutable'); END",
 "CREATE TRIGGER IF NOT EXISTS lock_status_revert BEFORE UPDATE OF status ON quotes WHEN OLD.status!='DRAFT' AND NEW.status='DRAFT' BEGIN SELECT RAISE(ABORT,'approved quote cannot be draft'); END",
 "CREATE TRIGGER IF NOT EXISTS lock_approved_delete BEFORE DELETE ON quotes WHEN OLD.status!='DRAFT' BEGIN SELECT RAISE(ABORT,'approved quote cannot be deleted'); END",
 "CREATE TRIGGER IF NOT EXISTS lock_revision_update BEFORE UPDATE ON quote_revisions BEGIN SELECT RAISE(ABORT,'revision immutable'); END",
 "CREATE TRIGGER IF NOT EXISTS lock_revision_delete BEFORE DELETE ON quote_revisions BEGIN SELECT RAISE(ABORT,'revision immutable'); END",
 "CREATE TRIGGER IF NOT EXISTS lock_request_revision_update BEFORE UPDATE ON request_revisions BEGIN SELECT RAISE(ABORT,'revision immutable'); END",
 "CREATE TRIGGER IF NOT EXISTS lock_request_revision_delete BEFORE DELETE ON request_revisions BEGIN SELECT RAISE(ABORT,'revision immutable'); END"
)

def _migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    import json
    try:
        conn.execute("BEGIN IMMEDIATE")
        for statement in MIGRATION_V2:
            conn.execute(statement)
        # Baseline reflects current state; migration cannot reconstruct older revisions.
        for row in conn.execute("SELECT * FROM requests ORDER BY id").fetchall():
            payload=json.dumps(dict(row),ensure_ascii=False,sort_keys=True)
            conn.execute("INSERT INTO request_revisions(request_id,version,event,snapshot_json) VALUES (?,1,'MIGRATED_BASELINE',?)",(row["id"],payload))
        for row in conn.execute("SELECT * FROM quotes ORDER BY id").fetchall():
            lines=[dict(x) for x in conn.execute("SELECT * FROM quote_lines WHERE quote_id=? ORDER BY id",(row["id"],))]
            customer=conn.execute("SELECT * FROM customers WHERE id=?",(row["customer_id"],)).fetchone()
            payload=json.dumps({"quote":dict(row),"customer":dict(customer),"lines":lines},ensure_ascii=False,sort_keys=True)
            conn.execute("INSERT INTO quote_revisions(quote_id,version,event,snapshot_json) VALUES (?,1,'MIGRATED_BASELINE',?)",(row["id"],payload))
        conn.execute("PRAGMA user_version=2")
        conn.commit()
    except Exception:
        conn.rollback()
        raise

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
            conn.execute("PRAGMA user_version=1")
            conn.commit()
            version = 1
        if version == 1:
            _migrate_v1_to_v2(conn)
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
