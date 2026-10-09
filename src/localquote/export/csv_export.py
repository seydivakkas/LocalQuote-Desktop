"""UTF-8-BOM CSV for spreadsheet safety; user strings never interpreted as formulae."""
import csv
from pathlib import Path


def safe_cell(value):
    if value is None: return ""
    value=str(value)
    if value.lstrip().startswith(("=","+","-","@")) or value.startswith(("\t","\r","\n")):
        return "'"+value
    return value


def export_quotes(conn, path: Path | str):
    rows=conn.execute("SELECT q.id,c.name,q.status,q.created_at,q.approved_at FROM quotes q "
        "JOIN customers c ON c.id=q.customer_id ORDER BY q.id").fetchall()
    with open(path,"w",encoding="utf-8-sig",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(["Teklif No","Müşteri","Durum","Oluşturulma","Onay Tarihi"])
        writer.writerows([[safe_cell(v) for v in row] for row in rows])
    return len(rows)
