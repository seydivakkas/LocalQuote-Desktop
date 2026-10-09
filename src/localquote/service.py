"""Business operations; all SQL parameters are bound, no raw text interpolation."""
from __future__ import annotations
from datetime import date
import sqlite3
from typing import Any
from .domain.money import InputError, cents, percent, decimal_value
from .domain.pricing import PriceLine, calculate_quote, calculate_line
from .storage.db import transaction

class StateError(ValueError):
    pass


def _required(s: str, field: str, max_len: int) -> str:
    if not isinstance(s, str) or not s.strip() or len(s) > max_len:
        raise InputError(f"{field} boş veya çok uzun")
    return s.strip()


def _optional(s: str, max_len: int) -> str:
    if not isinstance(s, str) or len(s) > max_len:
        raise InputError("Alan çok uzun")
    return s.strip()


def _id(conn, table: str, identifier: int):
    # No free-form table input. All callers use hard-coded internal names.
    if table not in {"customers", "services", "requests", "quotes"}:
        raise ValueError("Invalid table")
    row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (identifier,)).fetchone()
    if row is None:
        raise InputError(f"Kayıt bulunamadı: {table} #{identifier}")
    return row


def create_customer(conn: sqlite3.Connection, name: str, email="", phone="", notes="") -> int:
    with transaction(conn):
        cur = conn.execute("INSERT INTO customers(name,email,phone,notes) VALUES (?,?,?,?)",
            (_required(name,"Müşteri adı",200),_optional(email,200),_optional(phone,80),_optional(notes,1000)))
        return cur.lastrowid


def update_customer(conn, customer_id: int, name: str, email="", phone="", notes="") -> None:
    _id(conn,"customers",customer_id)
    with transaction(conn):
        conn.execute("UPDATE customers SET name=?,email=?,phone=?,notes=? WHERE id=?",
             (_required(name,"Müşteri adı",200), _optional(email,200),_optional(phone,80),_optional(notes,1000),customer_id))


def archive_customer(conn, customer_id: int):
    _id(conn,"customers", customer_id)
    with transaction(conn):
        conn.execute("UPDATE customers SET archived=1 WHERE id=?",(customer_id,))


def list_customers(conn, query="", include_archived=False):
    escaped = query.replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%" if query else "%"
    return conn.execute("SELECT * FROM customers WHERE (name LIKE ? ESCAPE '\\' OR email LIKE ? ESCAPE '\\') "
       "AND (?=1 OR archived=0) ORDER BY name", (pattern,pattern,int(include_archived))).fetchall()


def create_service(conn, name: str, price: str, unit="adet", vat="20") -> int:
    price_cents = cents(price)
    vat_rate = str(percent(vat))
    with transaction(conn):
        cur=conn.execute("INSERT INTO services(name,unit,unit_price_cents,vat_percent) VALUES (?,?,?,?)",
            (_required(name,"Hizmet adı",300),_required(unit,"Birim",40), price_cents,vat_rate))
        return cur.lastrowid


def update_service(conn, service_id, name, price, unit="adet", vat="20"):
    _id(conn,"services",service_id)
    with transaction(conn):
        conn.execute("UPDATE services SET name=?,unit=?,unit_price_cents=?,vat_percent=? WHERE id=?",
            (_required(name,"Hizmet adı",300),_required(unit,"Birim",40),cents(price),str(percent(vat)),service_id))


def deactivate_service(conn, service_id):
    _id(conn,"services",service_id)
    with transaction(conn):
        conn.execute("UPDATE services SET active=0 WHERE id=?",(service_id,))


def list_services(conn, active_only=True):
    return conn.execute("SELECT * FROM services WHERE (?=0 OR active=1) ORDER BY name",(int(active_only),)).fetchall()


def create_request(conn, customer_id, message, due_date=""):
    _id(conn,"customers",customer_id)
    message = _required(message,"Talep",20000)
    due_date = _optional(due_date,10)
    if due_date:
        try:
            if date.fromisoformat(due_date).isoformat()!=due_date: raise ValueError()
        except ValueError:
            raise InputError("Tarih YYYY-MM-DD biçiminde olmalı") from None
    with transaction(conn):
        cur=conn.execute("INSERT INTO requests(customer_id,message,due_date) VALUES(?,?,?)", (customer_id,message,due_date))
        return cur.lastrowid


def list_requests(conn, customer_id=None):
    return conn.execute("SELECT r.*,c.name customer_name FROM requests r JOIN customers c ON c.id=r.customer_id "
      "WHERE (? IS NULL OR customer_id=?) ORDER BY r.id DESC",(customer_id,customer_id)).fetchall()


def create_quote(conn, customer_id=None, request_id=None, note=""):
    if request_id is not None:
        request = _id(conn,"requests",request_id)
        if customer_id is not None and request["customer_id"]!=customer_id:
            raise InputError("Talep farklı müşteriye ait")
        customer_id = request["customer_id"]
    if customer_id is None: raise InputError("Müşteri seçiniz")
    _id(conn,"customers",customer_id)
    note=_optional(note,2000)
    with transaction(conn):
        cur=conn.execute("INSERT INTO quotes(customer_id,request_id,note) VALUES (?,?,?)",(customer_id,request_id,note))
        conn.execute("INSERT INTO quote_events(quote_id,event) VALUES (?,?)",(cur.lastrowid,"CREATED"))
        return cur.lastrowid


def _draft(conn, quote_id):
    quote=_id(conn,"quotes",quote_id)
    if quote["status"] != "DRAFT":
        raise StateError("Onaylı teklif değiştirilemez")
    return quote


def add_line(conn, quote_id: int, service_id: int | None, description: str, quantity: str, price: str,
             discount="0", vat="20") -> int:
    _draft(conn,quote_id)
    if service_id is not None: _id(conn,"services",service_id)
    line=PriceLine(_required(description,"Satır açıklaması",2000),str(decimal_value(quantity,positive=True)),
        cents(price),str(percent(discount)),str(percent(vat)))
    calculate_line(line)
    with transaction(conn):
        cur=conn.execute("INSERT INTO quote_lines (quote_id,service_id,description,quantity,unit_price_cents,discount_percent,vat_percent) "
            "VALUES (?,?,?,?,?,?,?)", (quote_id,service_id,line.description,line.quantity,line.unit_price_cents,line.discount_percent,line.vat_percent))
        conn.execute("INSERT INTO quote_events(quote_id,event) VALUES (?,?)",(quote_id,"LINE_ADDED"))
        return cur.lastrowid


def remove_line(conn, quote_id: int, line_id: int):
    _draft(conn,quote_id)
    if not conn.execute("SELECT 1 FROM quote_lines WHERE id=? AND quote_id=?",(line_id,quote_id)).fetchone():
        raise InputError("Satır bulunamadı")
    with transaction(conn):
        conn.execute("DELETE FROM quote_lines WHERE id=? AND quote_id=?",(line_id,quote_id))
        conn.execute("INSERT INTO quote_events(quote_id,event) VALUES (?,?)",(quote_id,"LINE_REMOVED"))


def quote_detail(conn,quote_id):
    quote=_id(conn,"quotes",quote_id)
    customer=_id(conn,"customers",quote["customer_id"])
    lines=conn.execute("SELECT * FROM quote_lines WHERE quote_id=? ORDER BY id",(quote_id,)).fetchall()
    data=[PriceLine(row["description"],row["quantity"],row["unit_price_cents"],row["discount_percent"],row["vat_percent"]) for row in lines]
    return {"quote":dict(quote),"customer":dict(customer),"lines":[dict(x) for x in lines], "totals":calculate_quote(data)}


def approve_quote(conn,quote_id):
    _draft(conn,quote_id)
    detail=quote_detail(conn,quote_id)
    if not detail["lines"]: raise StateError("Boş teklif onaylanamaz")
    with transaction(conn):
        conn.execute("UPDATE quotes SET status='APPROVED',approved_at=datetime('now') WHERE id=? AND status='DRAFT'",(quote_id,))
        conn.execute("INSERT INTO quote_events(quote_id,event) VALUES (?,?)",(quote_id,"APPROVED"))


def mark_exported(conn,quote_id):
    quote=_id(conn,"quotes",quote_id)
    if quote["status"] not in ("APPROVED","EXPORTED"):
        raise StateError("Nihai PDF için teklif onayı gerekli")
    with transaction(conn):
        conn.execute("UPDATE quotes SET status='EXPORTED' WHERE id=?",(quote_id,))
        conn.execute("INSERT INTO quote_events(quote_id,event) VALUES (?,?)",(quote_id,"EXPORTED"))


def list_quotes(conn,query=""):
    escaped = query.replace("%", "\\%").replace("_", "\\_")
    pattern=f"%{escaped}%" if query else "%"
    return conn.execute("SELECT q.*,c.name customer_name FROM quotes q JOIN customers c ON c.id=q.customer_id "
      "WHERE c.name LIKE ? ESCAPE '\\' ORDER BY q.id DESC",(pattern,)).fetchall()
