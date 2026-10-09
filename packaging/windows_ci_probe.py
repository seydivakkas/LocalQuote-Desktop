"""Windows CI proof: packaged EXE bootstrap + generated DB/PDF and isolated restore.
Only synthetic data. Not a clean offline GUI acceptance replacement.
"""
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path

from localquote import service
from localquote.export.pdf import create_pdf
from localquote.storage.backup import backup_database, restore_database
from localquote.storage.db import open_db, SCHEMA_VERSION


def main(exe: Path, report: Path):
    exe=exe.resolve()
    if not exe.is_file(): raise AssertionError("EXE missing")
    with tempfile.TemporaryDirectory(prefix="lq_ci_profiles_") as directory:
        root=Path(directory)
        original=root/"profile-A"/"db.sqlite3"
        pdf=root/"sample.pdf"
        original.parent.mkdir(parents=True)
        # The packaged .exe, not the Python code, creates the DB and PDF.
        result=subprocess.run([str(exe),"--demo",str(pdf),"--db",str(original)],
                              cwd=str(root),timeout=90,check=False)
        assert result.returncode==0, f"packaged EXE failed: {result.returncode}"
        assert pdf.is_file() and pdf.read_bytes().startswith(b"%PDF-")
        with closing(open_db(original)) as conn:
            assert conn.execute("PRAGMA user_version").fetchone()[0]==SCHEMA_VERSION
            assert conn.execute("SELECT count(*) FROM quotes WHERE status='EXPORTED'").fetchone()[0]==1
            before=[dict(x) for x in service.list_quotes(conn)]
            backup=root/"backup.sqlite3"
            backup_database(conn,backup)
            assert backup.is_file()
            # Unicode + 50 lines: exercise PDF renderer on Windows runtime.
            cid=service.create_customer(conn,"İstanbul Çeşme Şişli")
            sid=service.create_service(conn,"Tasarım","10")
            qid=service.create_quote(conn,customer_id=cid)
            for i in range(50):
                service.add_line(conn,qid,sid,"Şablon örneği "+str(i)+" ÇĞİÖŞÜ", "1","10")
            service.approve_quote(conn,qid)
            long_pdf=root/"multipage.pdf"
            create_pdf(service.quote_detail(conn,qid),long_pdf)
            assert long_pdf.is_file() and long_pdf.stat().st_size>4000
        restored=root/"profile-B"/"db.sqlite3"
        restore_database(backup,restored)
        with closing(open_db(restored)) as conn:
            after=[dict(x) for x in service.list_quotes(conn)]
            assert before==after
            assert conn.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        try:
            restore_database(backup,restored)
            raise AssertionError("restore unexpectedly overwrote database")
        except FileExistsError:
            pass
        proof={
            "status":"PASS","os":platform.platform(),"python":sys.version.split()[0],
            "schema_version":SCHEMA_VERSION,
            "packaged_exe_sha256":hashlib.sha256(exe.read_bytes()).hexdigest(),
            "sample_pdf_sha256":hashlib.sha256(pdf.read_bytes()).hexdigest(),
            "multipage_pdf_sha256":hashlib.sha256(long_pdf.read_bytes()).hexdigest(),
            "backup_sha256":hashlib.sha256(backup.read_bytes()).hexdigest(),
            "validated":["packaged_exe_demo","pdf_header","sqlite_persistence",
                         "50_line_unicode_render","backup_restore_across_directories",
                         "restore_no_overwrite"],
            "limitations":["not a disconnected-network GUI test","not a clean Windows VM without Python",
                           "not an interactive logo selection test"],
        }
        report.parent.mkdir(parents=True,exist_ok=True)
        report.write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps(proof,ensure_ascii=False,indent=2))


if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: windows_ci_probe.py PATH_TO_EXE PATH_TO_JSON")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
