"""Entry points: GUI by default, headless demo/smoke/restore for verification."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from contextlib import closing
from .config import database_path
from .storage.db import open_db, SCHEMA_VERSION
from .storage.backup import restore_database
from . import service
from .export.pdf import create_pdf


def _announce(*parts):
    if sys.stdout is not None:
        print(*parts)


def main(argv=None):
    parser=argparse.ArgumentParser(description="LocalQuote Offline Desktop")
    parser.add_argument("--db",type=Path,default=database_path())
    group=parser.add_mutually_exclusive_group()
    group.add_argument("--gui",action="store_true")
    group.add_argument("--smoke",action="store_true")
    group.add_argument("--demo",type=Path,metavar="PDF_PATH")
    group.add_argument("--restore",type=Path,metavar="BACKUP_PATH")
    args=parser.parse_args(argv)
    if args.restore:
        restore_database(args.restore,args.db)
        _announce("Yedek yeni veritabanı konumuna geri yüklendi:",args.db)
        return 0
    if args.smoke:
        with closing(open_db(args.db)) as conn:
            _announce(f"PASS: SQLite schema, integrity, local bootstrap; schema version {SCHEMA_VERSION}")
        return 0
    if args.demo:
        with closing(open_db(args.db)) as conn:
            cust=service.create_customer(conn,"Örnek Ajans Müşterisi","ornek@example.test")
            svc=service.create_service(conn,"Kurumsal Web Sitesi","12500.00")
            req=service.create_request(conn,cust,"Türkçe web sitesi ve SEO hizmeti istiyoruz.","2026-12-01")
            quote=service.create_quote(conn,request_id=req,note="Bu belge sentetik demo verileriyle üretilmiştir.")
            service.add_line(conn,quote,svc,"Kurumsal Web Sitesi","1","12500.00","10","20")
            service.approve_quote(conn,quote)
            create_pdf(service.quote_detail(conn,quote),args.demo)
            service.mark_exported(conn,quote)
            _announce(f"PASS: PDF oluşturuldu: {args.demo}, teklif #{quote}")
        return 0
    from .ui.app import run
    run(args.db)
    return 0

if __name__=="__main__":
    sys.exit(main())
