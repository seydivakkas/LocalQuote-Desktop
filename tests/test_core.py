"""Standard library regression suite; no paid API or network needed."""
import csv
import os
from pathlib import Path
from contextlib import closing
import sqlite3
import tempfile
import unittest
from decimal import Decimal

from localquote import service
from localquote.domain.money import InputError, cents, money
from localquote.domain.pricing import PriceLine, calculate_line, calculate_quote
from localquote.storage.db import DatabaseError, open_db
from localquote.storage.backup import backup_database, restore_database
from localquote.export.csv_export import export_quotes, safe_cell
from localquote.export.pdf import create_pdf, resolve_font


class MoneyTests(unittest.TestCase):
    def test_decimal_precision(self):
        a=PriceLine("A","1",10,"0","0")
        b=PriceLine("B","1",20,"0","0")
        self.assertEqual(calculate_quote([a,b])["total_cents"],30)

    def test_discount_before_vat(self):
        x=calculate_line(PriceLine("Web","2","" if False else 10000,"10","20"))
        self.assertEqual((x.gross_cents,x.discount_cents,x.net_cents,x.vat_cents,x.total_cents),
                         (20000,2000,18000,3600,21600))

    def test_mixed_vat(self):
        a=PriceLine("A","1",10000,"0","10")
        b=PriceLine("B","1",10000,"0","20")
        self.assertEqual(calculate_quote([a,b])["total_cents"],23000)

    def test_round_half_up(self):
        x=calculate_line(PriceLine("Fraction","0.5",1,"0","0"))
        self.assertEqual(x.total_cents,1)

    def test_reject_negative_nan_and_float(self):
        for price in ["-1","NaN","Infinity",float("nan"),True,"1.234"]:
            with self.subTest(price=price),self.assertRaises(InputError):cents(price)
        for q in ["-2","0","NaN"]:
            with self.subTest(q=q),self.assertRaises(InputError):
                calculate_line(PriceLine("invalid",q,100,"0","20"))

    def test_locale(self):
        self.assertEqual(cents("12,50"),1250)
        self.assertEqual(money(1250),"12.50")

    def test_over_100_percent(self):
        with self.assertRaises(InputError):calculate_line(PriceLine("item","1",100,"101","20"))

    def test_missing_description(self):
        with self.assertRaises(InputError):calculate_line(PriceLine("","1",100,"0","0"))


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"main.db"
        self.conn=open_db(self.path)
        self.addCleanup(self.conn.close)
        self.cid=service.create_customer(self.conn,"Çeşme Ajans", "merhaba@example.test")
        self.sid=service.create_service(self.conn,"Web Sitesi","5000.00",vat="20")

    def make_quote(self):
        rid=service.create_request(self.conn,self.cid,"Kampanya sitesi + SEO","2026-12-01")
        qid=service.create_quote(self.conn,request_id=rid)
        service.add_line(self.conn,qid,self.sid,"Web Sitesi","1","5000.00",discount="10",vat="20")
        return qid

    def test_fk_enabled(self):
        self.assertEqual(self.conn.execute("PRAGMA foreign_keys").fetchone()[0],1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO requests(customer_id,message) VALUES(?,?)",(999,"test"))

    def test_customer_crud_and_archive(self):
        service.update_customer(self.conn,self.cid,"Güncel Firma",phone="123")
        self.assertEqual(self.conn.execute("SELECT name FROM customers WHERE id=?",(self.cid,)).fetchone()[0],"Güncel Firma")
        service.archive_customer(self.conn,self.cid)
        self.assertEqual(len(service.list_customers(self.conn)),0)
        self.assertEqual(len(service.list_customers(self.conn,include_archived=True)),1)

    def test_invalid_due_date(self):
        with self.assertRaises(InputError):service.create_request(self.conn,self.cid,"Talep","2026-14-99")

    def test_sql_injection(self):
        dangerous="' OR 1=1 --"
        service.create_customer(self.conn,dangerous)
        self.assertEqual(len(service.list_customers(self.conn,dangerous)),1)
        self.assertEqual(len(service.list_customers(self.conn,"missing")),0)

    def test_literal_wildcard_search(self):
        service.create_customer(self.conn,"Acme % Firması")
        self.assertEqual(len(service.list_customers(self.conn,"%")),1)

    def test_snapshot_unaffected_by_catalog_edit(self):
        qid=self.make_quote()
        old=service.quote_detail(self.conn,qid)
        service.update_service(self.conn,self.sid,"Web Sitesi","9999.00")
        new=service.quote_detail(self.conn,qid)
        self.assertEqual(old["totals"],new["totals"])
        self.assertEqual(old["lines"],new["lines"])

    def test_only_own_request(self):
        other=service.create_customer(self.conn,"Başka Firma")
        request=service.create_request(self.conn,self.cid,"Talep")
        with self.assertRaises(InputError):service.create_quote(self.conn,other,request)

    def test_approve_transition_and_mutation_lock(self):
        qid=self.make_quote()
        service.approve_quote(self.conn,qid)
        with self.assertRaises(service.StateError):service.approve_quote(self.conn,qid)
        with self.assertRaises(service.StateError):
            service.add_line(self.conn,qid,self.sid,"hizmet","1","2")
        with self.assertRaises(service.StateError):service.remove_line(self.conn,qid,1)
        service.mark_exported(self.conn,qid)
        self.assertEqual(service.quote_detail(self.conn,qid)["quote"]["status"],"EXPORTED")
        events=self.conn.execute("SELECT event FROM quote_events WHERE quote_id=? ORDER BY id",(qid,)).fetchall()
        self.assertEqual([x[0] for x in events].count("APPROVED"),1)

    def test_empty_quote_not_approved(self):
        qid=service.create_quote(self.conn,customer_id=self.cid)
        with self.assertRaises(service.StateError):service.approve_quote(self.conn,qid)

    def test_bad_schema_rejected_without_overwriting(self):
        p=Path(self.temp.name)/"bad.sqlite3"
        p.write_bytes(b"not-sqlite")
        before=p.read_bytes()
        with self.assertRaises(DatabaseError):open_db(p)
        self.assertEqual(p.read_bytes(),before)

    def test_old_schema_is_rejected(self):
        p=Path(self.temp.name)/"legacy.db"
        with closing(sqlite3.connect(p)) as db:
            db.execute("CREATE TABLE legacy (id INTEGER)")
        with self.assertRaises(DatabaseError):open_db(p)

    def test_csv_injection(self):
        service.create_customer(self.conn,"=HYPERLINK(\"evil\")")
        self.assertEqual(safe_cell("  =2+2"),"'  =2+2")
        qid=service.create_quote(self.conn,customer_id=2)
        p=Path(self.temp.name)/"records.csv"
        export_quotes(self.conn,p)
        with open(p,"r",encoding="utf-8-sig",newline="") as f:
            data=list(csv.reader(f))
        self.assertTrue(any(x[1].startswith("'=") for x in data[1:]))
        self.assertTrue(p.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_backup_restore(self):
        qid=self.make_quote()
        original=service.quote_detail(self.conn,qid)
        target=Path(self.temp.name)/"backup.sqlite3"
        backup_database(self.conn,target)
        restored=Path(self.temp.name)/"restored.db"
        restore_database(target,restored)
        with closing(open_db(restored)) as copied:
            self.assertEqual(original,service.quote_detail(copied,qid))
        with self.assertRaises(FileExistsError):restore_database(target,restored)
        with self.assertRaises(FileExistsError):backup_database(self.conn,target)

    def test_corrupt_backup_refused(self):
        source=Path(self.temp.name)/"broken.sqlite3"
        source.write_bytes(b"garbage")
        destination=Path(self.temp.name)/"fresh.db"
        with self.assertRaises((DatabaseError,sqlite3.DatabaseError)):
            restore_database(source,destination)
        self.assertFalse(destination.exists())

    def test_pdf_unicode_text(self):
        qid=self.make_quote()
        service.approve_quote(self.conn,qid)
        path=Path(self.temp.name)/"quote.pdf"
        create_pdf(service.quote_detail(self.conn,qid),path)
        self.assertTrue(path.read_bytes().startswith(b"%PDF"))
        self.assertGreater(path.stat().st_size,2000)
        try:
            from pypdf import PdfReader
            text="\n".join(x.extract_text() or "" for x in PdfReader(path).pages)
            self.assertIn("Çeşme Ajans",text)
        except ImportError:
            pass

    def test_pdf_draft_refused(self):
        qid=self.make_quote()
        with self.assertRaises(ValueError):create_pdf(service.quote_detail(self.conn,qid),Path(self.temp.name)/"draft.pdf")

    def test_pdf_pagination(self):
        qid=service.create_quote(self.conn,customer_id=self.cid)
        for i in range(50):
            service.add_line(self.conn,qid,self.sid,f"Tasarım {i} " + "Lorem ipsum dolor sit amet "*3,"1","10.00")
        service.approve_quote(self.conn,qid)
        p=Path(self.temp.name)/"long.pdf"
        create_pdf(service.quote_detail(self.conn,qid),p)
        try:
            from pypdf import PdfReader
            self.assertGreater(len(PdfReader(p).pages),1)
        except ImportError:
            self.assertGreater(p.stat().st_size,4000)


if __name__=="__main__": unittest.main()
