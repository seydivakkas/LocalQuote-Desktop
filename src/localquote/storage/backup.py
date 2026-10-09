"""Consistent SQLite backup and cautious restore, intended while app is closed."""
from __future__ import annotations
from pathlib import Path
from contextlib import closing
import os
import sqlite3
import tempfile
from .db import SCHEMA_VERSION, DatabaseError


def backup_database(conn: sqlite3.Connection, target: Path | str):
    target=Path(target).resolve()
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        raise FileExistsError("Mevcut yedeğin üzerine yazılmıyor")
    with tempfile.NamedTemporaryFile(dir=target.parent,suffix=".sqlite3",delete=False) as temp:
        temp_path=Path(temp.name)
    try:
        with closing(sqlite3.connect(str(temp_path))) as copy:
            conn.backup(copy)
            if copy.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise DatabaseError("Yedek bütünlüğü bozuk")
        os.replace(temp_path,target)
    finally:
        temp_path.unlink(missing_ok=True)


def restore_database(source: Path | str, target: Path | str):
    """Restore only when no active connections are open. Refuse to overwrite existing DB."""
    source=Path(source).resolve()
    target=Path(target).resolve()
    if source == target or not source.is_file() or source.stat().st_size > 2_000_000_000:
        raise DatabaseError("Geçersiz yedek")
    if target.exists():
        raise FileExistsError("Güvenlik gereği mevcut veritabanı üzerine geri yükleme yapılmaz; boş bir veri dizini kullanın")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent,suffix=".sqlite3",delete=False) as temp:
        tmp=Path(temp.name)
    try:
        with closing(sqlite3.connect(f"file:{source.as_posix()}?mode=ro",uri=True)) as incoming:
            if incoming.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                raise DatabaseError("Yedek bütünlüğü hatalı")
            if incoming.execute("PRAGMA user_version").fetchone()[0]!=SCHEMA_VERSION:
                raise DatabaseError("Yedek şema sürümü desteklenmiyor")
            with closing(sqlite3.connect(str(tmp))) as restored:
                incoming.backup(restored)
                if restored.execute("PRAGMA foreign_key_check").fetchall():
                    raise DatabaseError("Yedekte ilişki hatası")
        os.replace(tmp,target)
    except (sqlite3.DatabaseError, OSError) as e:
        raise DatabaseError(f"Geri yükleme hatası: {e}") from e
    finally:
        tmp.unlink(missing_ok=True)
