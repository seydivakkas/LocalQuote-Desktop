"""P0-02 migration, package, CRUD and immutability regressions."""
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from localquote import service
from localquote.domain.money import InputError
from localquote.storage.db import SCHEMA, open_db


class P002Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.conn=open_db(Path(self.tmp.name)/"p0-02.db")
        self.addCleanup(self.conn.close)
        self.customer=service.create_customer(self.conn,"Çeşme Ajans")
        self.web=service.create_service(self.conn,"Web","1000",vat="20")
        self.seo=service.create_service(self.conn,"SEO","250",vat="10")

    def test_schema_and_request_versions(self):
        self.assertEqual(self.conn.execute("PRAGMA user_version").fetchone()[0],2)
        rid=service.create_request(self.conn,self.customer,"İlk istek")
        service.update_request(self.conn,rid,self.customer,"Yeni istek","2027-01-01")
        history=service.request_history(self.conn,rid)
        self.assertEqual([h["event"] for h in history],["CREATED","UPDATED"])
        self.assertEqual(json.loads(history[0]["snapshot_json"])["message"],"İlk istek")

    def test_package_price_snapshot_and_lock(self):
        pkg=service.create_service_package(self.conn,"Paket",[(self.web,"2"),(self.seo,"3")])
        q=service.create_quote(self.conn,customer_id=self.customer)
        self.assertEqual(service.add_package_to_quote(self.conn,q,pkg),2)
        before=service.quote_detail(self.conn,q)
        self.assertEqual(before["totals"]["total_cents"],322500)
        service.update_service(self.conn,self.web,"Web","9999")
        service.update_service_package(self.conn,pkg,"Yeni",[(self.seo,"1")])
        self.assertEqual(service.quote_detail(self.conn,q)["lines"],before["lines"])
        service.approve_quote(self.conn,q)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("UPDATE quote_lines SET unit_price_cents=1 WHERE quote_id=?",(q,))
        self.conn.rollback()
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("UPDATE quotes SET status='DRAFT' WHERE id=?",(q,))
        self.conn.rollback()
        self.assertEqual(before["totals"],service.quote_detail(self.conn,q)["totals"])

    def test_approval_history_is_immutable(self):
        q=service.create_quote(self.conn,customer_id=self.customer)
        service.add_line(self.conn,q,self.web,"Web","1","1000")
        service.update_quote_note(self.conn,q,"Birinci teklif")
        service.approve_quote(self.conn,q)
        h=service.quote_history(self.conn,q)
        self.assertEqual([r["event"] for r in h],["CREATED","LINE_ADDED","NOTE_UPDATED","APPROVED"])
        baseline=json.loads(h[-1]["snapshot_json"])
        service.update_customer(self.conn,self.customer,"Yeni Firma")
        self.assertEqual(baseline["customer"]["name"],"Çeşme Ajans")
        with self.assertRaises(service.StateError):service.update_quote_note(self.conn,q,"Hata")
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("DELETE FROM quote_revisions WHERE quote_id=?",(q,))
        self.conn.rollback()

    def test_package_invalid_atomic(self):
        with self.assertRaises(InputError):
            service.create_service_package(self.conn,"X",[(self.web,"1"),(self.web,"2")])
        self.assertEqual(len(service.list_service_packages(self.conn)),0)
        pkg=service.create_service_package(self.conn,"Paket",[(self.web,"1")])
        q=service.create_quote(self.conn,customer_id=self.customer)
        service.deactivate_service(self.conn,self.web)
        with self.assertRaises(InputError):service.add_package_to_quote(self.conn,q,pkg)
        self.assertEqual(len(service.quote_detail(self.conn,q)["lines"]),0)

    def test_customer_reassignment_for_linked_request_denied(self):
        rid=service.create_request(self.conn,self.customer,"Talep")
        service.create_quote(self.conn,request_id=rid)
        other=service.create_customer(self.conn,"İkinci Firma")
        with self.assertRaises(service.StateError):
            service.update_request(self.conn,rid,other,"Bilinmeyen")

    def test_v1_upgrade_preserves_approved_quotes(self):
        path=Path(self.tmp.name)/"v1.db"
        with closing(sqlite3.connect(path)) as old:
            old.executescript(SCHEMA)
            old.execute("INSERT INTO customers(name) VALUES('Eski Firma')")
            old.execute("INSERT INTO quotes(customer_id,status) VALUES(1,'APPROVED')")
            old.execute("INSERT INTO quote_lines(quote_id,description,quantity,unit_price_cents,discount_percent,vat_percent) VALUES(1,'Web','1',10000,'0','20')")
            old.execute("PRAGMA user_version=1")
            old.commit()
        with closing(open_db(path)) as migrated:
            self.assertEqual(migrated.execute("PRAGMA user_version").fetchone()[0],2)
            self.assertEqual(service.quote_detail(migrated,1)["totals"]["total_cents"],12000)
            self.assertEqual(service.quote_history(migrated,1)[0]["event"],"MIGRATED_BASELINE")
        with closing(open_db(path)) as again:
            self.assertEqual(len(service.quote_history(again,1)),1)


if __name__=="__main__":unittest.main()
