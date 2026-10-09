"""P0-02: immutable quote revisions, editable requests and catalog packages."""
from __future__ import annotations
import json
from datetime import date
from .domain.money import InputError, decimal_value
from .domain.pricing import PriceLine, calculate_line
from .storage.db import transaction


def _services():
    from . import service
    return service


def _due(value):
    value=_services()._optional(value,10)
    if value:
        try:
            if date.fromisoformat(value).isoformat()!=value: raise ValueError()
        except ValueError: raise InputError("Tarih YYYY-MM-DD biçiminde olmalı") from None
    return value


def record_request_revision(conn, rid, event):
    item=dict(_services()._id(conn,"requests",rid))
    v=conn.execute("SELECT COALESCE(MAX(version),0)+1 FROM request_revisions WHERE request_id=?",(rid,)).fetchone()[0]
    conn.execute("INSERT INTO request_revisions(request_id,version,event,snapshot_json) VALUES(?,?,?,?)",
                 (rid,v,event,json.dumps(item,ensure_ascii=False,sort_keys=True)))


def request_history(conn,rid):
    _services()._id(conn,"requests",rid)
    return [dict(x) for x in conn.execute("SELECT version,event,snapshot_json,created_at FROM request_revisions WHERE request_id=? ORDER BY version",(rid,))]


def record_quote_revision(conn,qid,event):
    detail=_services().quote_detail(conn,qid)
    v=conn.execute("SELECT COALESCE(MAX(version),0)+1 FROM quote_revisions WHERE quote_id=?",(qid,)).fetchone()[0]
    snapshot={"quote":detail["quote"],"customer":detail["customer"],"lines":detail["lines"],"totals":detail["totals"]}
    conn.execute("INSERT INTO quote_revisions(quote_id,version,event,snapshot_json) VALUES(?,?,?,?)",
                 (qid,v,event,json.dumps(snapshot,ensure_ascii=False,sort_keys=True)))


def quote_history(conn,qid):
    _services()._id(conn,"quotes",qid)
    return [dict(x) for x in conn.execute("SELECT version,event,snapshot_json,created_at FROM quote_revisions WHERE quote_id=? ORDER BY version",(qid,))]


def update_request(conn,rid,customer_id,message,due_date=""):
    svc=_services()
    prior=svc._id(conn,"requests",rid)
    customer=svc._id(conn,"customers",customer_id)
    if customer["archived"]: raise InputError("Arşivlenmiş müşteri seçilemez")
    if prior["customer_id"]!=customer_id and conn.execute("SELECT 1 FROM quotes WHERE request_id=? LIMIT 1",(rid,)).fetchone():
        raise svc.StateError("Teklife bağlı talebin müşterisi değiştirilemez")
    message=svc._required(message,"Talep",20000)
    due_date=_due(due_date)
    with transaction(conn):
        conn.execute("UPDATE requests SET customer_id=?,message=?,due_date=? WHERE id=?",(customer_id,message,due_date,rid))
        record_request_revision(conn,rid,"UPDATED")


def update_quote_note(conn,qid,note):
    svc=_services()
    svc._draft(conn,qid)
    note=svc._optional(note,2000)
    with transaction(conn):
        conn.execute("UPDATE quotes SET note=? WHERE id=?",(note,qid))
        conn.execute("INSERT INTO quote_events(quote_id,event) VALUES(?,?)",(qid,"NOTE_UPDATED"))
        record_quote_revision(conn,qid,"NOTE_UPDATED")


def _package(conn,pid):
    x=conn.execute("SELECT * FROM service_packages WHERE id=?",(pid,)).fetchone()
    if x is None: raise InputError("Paket bulunamadı")
    return x


def _items(conn,items):
    if not isinstance(items,list) or not 1<=len(items)<=100: raise InputError("Paket en az 1, en fazla 100 hizmet içerir")
    result=[];seen=set()
    for sid,qty in items:
        service=_services()._id(conn,"services",sid)
        if not service["active"]: raise InputError("Pasif hizmet kullanılamaz")
        if sid in seen: raise InputError("Tekrarlanan hizmet")
        seen.add(sid)
        result.append((sid,str(decimal_value(qty,positive=True))))
    return result


def create_service_package(conn,name,items):
    name=_services()._required(name,"Paket adı",300)
    items=_items(conn,items)
    with transaction(conn):
        cur=conn.execute("INSERT INTO service_packages(name) VALUES(?)",(name,))
        for sid,qty in items:
            conn.execute("INSERT INTO package_items(package_id,service_id,quantity) VALUES(?,?,?)",(cur.lastrowid,sid,qty))
        return cur.lastrowid


def update_service_package(conn,pid,name,items):
    _package(conn,pid)
    name=_services()._required(name,"Paket adı",300)
    items=_items(conn,items)
    with transaction(conn):
        conn.execute("UPDATE service_packages SET name=? WHERE id=?",(name,pid))
        conn.execute("DELETE FROM package_items WHERE package_id=?",(pid,))
        for sid,qty in items:
            conn.execute("INSERT INTO package_items(package_id,service_id,quantity) VALUES(?,?,?)",(pid,sid,qty))


def deactivate_service_package(conn,pid):
    _package(conn,pid)
    with transaction(conn): conn.execute("UPDATE service_packages SET active=0 WHERE id=?",(pid,))


def list_service_packages(conn,active_only=True):
    return conn.execute("SELECT * FROM service_packages WHERE (?=0 OR active=1) ORDER BY name,id",(int(active_only),)).fetchall()


def package_detail(conn,pid):
    pkg=_package(conn,pid)
    rows=conn.execute("SELECT pi.service_id,pi.quantity,s.name,s.unit_price_cents,s.vat_percent,s.active FROM package_items pi JOIN services s ON s.id=pi.service_id WHERE pi.package_id=? ORDER BY pi.service_id",(pid,)).fetchall()
    return {"package":dict(pkg),"items":[dict(x) for x in rows]}


def add_package_to_quote(conn,qid,pid):
    svc=_services()
    svc._draft(conn,qid)
    data=package_detail(conn,pid)
    if not data["package"]["active"] or not data["items"]: raise InputError("Paket boş veya pasif")
    validated=[]
    for item in data["items"]:
        if not item["active"]: raise InputError("Pasif hizmet pakette yer alıyor")
        line=PriceLine(item["name"],item["quantity"],item["unit_price_cents"],"0",item["vat_percent"])
        calculate_line(line)
        validated.append((item["service_id"],line))
    with transaction(conn):
        for sid,line in validated:
            conn.execute("INSERT INTO quote_lines(quote_id,service_id,description,quantity,unit_price_cents,discount_percent,vat_percent) VALUES(?,?,?,?,?,?,?)",
                       (qid,sid,line.description,line.quantity,line.unit_price_cents,line.discount_percent,line.vat_percent))
        conn.execute("INSERT INTO quote_events(quote_id,event) VALUES(?,?)",(qid,f"PACKAGE_ADDED:{pid}"))
        record_quote_revision(conn,qid,f"PACKAGE_ADDED:{pid}")
    return len(validated)
