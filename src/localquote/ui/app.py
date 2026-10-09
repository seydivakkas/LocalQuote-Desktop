"""Small fully offline Tkinter client. Business rules reside in service.py."""
from __future__ import annotations
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from .. import service
from ..config import database_path
from ..domain.money import money
from ..storage.db import open_db
from ..storage.backup import backup_database, restore_database
from ..export.csv_export import export_quotes
from ..export.pdf import create_pdf


def _field(parent, label, row, *, width=34):
    ttk.Label(parent,text=label).grid(row=row,column=0,sticky="w",padx=8,pady=4)
    entry=ttk.Entry(parent,width=width)
    entry.grid(row=row,column=1,sticky="ew",padx=8,pady=4)
    return entry


class LocalQuoteApp(tk.Tk):
    def __init__(self, path=None):
        super().__init__()
        self.title("LocalQuote • Çevrimdışı Teklif Yönetimi [P0 önizleme]")
        self.geometry("1080x760")
        self.minsize(850,650)
        self.db_path=Path(path) if path else database_path()
        self.conn=open_db(self.db_path)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.tabs=ttk.Notebook(self); self.tabs.pack(fill="both",expand=True,padx=10,pady=10)
        for label,builder in (("Müşteriler",self.customers_tab),("Hizmetler",self.services_tab),
                               ("Talepler",self.requests_tab),("Teklifler",self.quotes_tab)):
            page=ttk.Frame(self.tabs,padding=8)
            self.tabs.add(page,text=label)
            builder(page)
        self.status=tk.StringVar(value=f"Yerel veritabanı: {self.db_path}")
        ttk.Label(self,textvariable=self.status,anchor="w").pack(fill="x",padx=12,pady=4)
        self.refresh_all()

    def close(self):
        self.conn.close(); self.destroy()

    def action(self, fn):
        try:
            result=fn()
            self.refresh_all()
            self.status.set("İşlem tamamlandı. Veriler yerel diskte kaydedildi.")
            return result
        except Exception as exc:
            # Sensitive user content is never logged or included in stack traces.
            messagebox.showerror("İşlem gerçekleştirilemedi",str(exc),parent=self)

    def tree(self,parent,columns,headings,height=13):
        frame=ttk.Frame(parent)
        frame.pack(fill="both",expand=True,pady=8)
        tree=ttk.Treeview(frame,columns=columns,show="headings",height=height,selectmode="browse")
        for c,h in zip(columns,headings):
            tree.heading(c,text=h)
            tree.column(c,width=115 if c=="id" else 185,stretch=True)
        scroll=ttk.Scrollbar(frame,orient="vertical",command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        return tree

    def customers_tab(self,parent):
        form=ttk.LabelFrame(parent,text="Müşteri Bilgileri",padding=6)
        form.pack(fill="x")
        self.c_fields={name:_field(form,label,i) for i,(name,label) in enumerate([
            ("name","Ad / Firma"),("email","E-posta"),("phone","Telefon"),("notes","Not")])}
        form.columnconfigure(1,weight=1)
        buttons=ttk.Frame(form);buttons.grid(row=4,column=0,columnspan=2,sticky="e")
        ttk.Button(buttons,text="Ekle",command=lambda:self.action(self.customer_add)).pack(side="left",padx=3)
        ttk.Button(buttons,text="Seçileni Güncelle",command=lambda:self.action(self.customer_update)).pack(side="left",padx=3)
        ttk.Button(buttons,text="Arşivle",command=lambda:self.action(self.customer_archive)).pack(side="left",padx=3)
        self.customer_search=ttk.Entry(parent)
        self.customer_search.pack(fill="x",pady=4)
        self.customer_search.bind("<KeyRelease>",lambda _:self.refresh_customers())
        self.customers=self.tree(parent,("id","name","email","phone"),("ID","Firma","E-posta","Telefon"))
        self.customers.bind("<<TreeviewSelect>>",self.customer_select)

    def customer_add(self):
        service.create_customer(self.conn,**{k:v.get() for k,v in self.c_fields.items()})

    def customer_id(self):
        selected=self.customers.selection()
        if not selected: raise ValueError("Önce müşteri seçin")
        return int(selected[0])

    def customer_update(self):
        service.update_customer(self.conn,self.customer_id(),**{k:v.get() for k,v in self.c_fields.items()})

    def customer_archive(self):
        if messagebox.askyesno("Arşivleme","Müşteri aktif listeden çıkarılsın?",parent=self):
            service.archive_customer(self.conn,self.customer_id())

    def customer_select(self,_):
        selection=self.customers.selection()
        if not selection: return
        row=self.conn.execute("SELECT * FROM customers WHERE id=?",(int(selection[0]),)).fetchone()
        if not row: return
        for k,v in self.c_fields.items():
            v.delete(0,"end");v.insert(0,row[k])

    def services_tab(self,parent):
        form=ttk.LabelFrame(parent,text="Hizmet Kataloğu",padding=6);form.pack(fill="x")
        self.s_fields={name:_field(form,label,i) for i,(name,label) in enumerate([
            ("name","Hizmet"),("price","Birim fiyat (TL)"),("unit","Birim"),("vat","KDV (%)")])}
        self.s_fields["unit"].insert(0,"adet");self.s_fields["vat"].insert(0,"20")
        form.columnconfigure(1,weight=1)
        buttons=ttk.Frame(form);buttons.grid(row=4,column=0,columnspan=2,sticky="e")
        ttk.Button(buttons,text="Hizmet Ekle",command=lambda:self.action(self.service_add)).pack(side="left",padx=3)
        ttk.Button(buttons,text="Güncelle",command=lambda:self.action(self.service_update)).pack(side="left",padx=3)
        ttk.Button(buttons,text="Pasife Al",command=lambda:self.action(self.service_deactivate)).pack(side="left",padx=3)
        self.services=self.tree(parent,("id","name","unit","price","vat"),("ID","Hizmet","Birim","Fiyat TL","KDV %"))
        self.services.bind("<<TreeviewSelect>>",self.service_select)
        pack=ttk.LabelFrame(parent,text="Hizmet Paketleri — örnek: 1:2, 3:1",padding=6);pack.pack(fill="x")
        ttk.Label(pack,text="Paket adı").pack(side="left",padx=3)
        self.package_name=ttk.Entry(pack,width=20);self.package_name.pack(side="left",padx=3)
        ttk.Label(pack,text="HizmetID:Miktar").pack(side="left",padx=3)
        self.package_items=ttk.Entry(pack,width=23);self.package_items.pack(side="left",padx=3)
        ttk.Button(pack,text="Ekle",command=lambda:self.action(self.package_add)).pack(side="left")
        ttk.Button(pack,text="Güncelle",command=lambda:self.action(self.package_update)).pack(side="left")
        ttk.Button(pack,text="Pasif",command=lambda:self.action(self.package_deactivate)).pack(side="left")
        self.packages=self.tree(parent,("id","name","content"),("ID","Paket","İçerik"),height=4)
        self.packages.bind("<<TreeviewSelect>>",self.package_select)

    def package_id(self):
        selection=self.packages.selection()
        if not selection:raise ValueError("Önce paket seçiniz")
        return int(selection[0])

    def parsed_package_items(self):
        output=[]
        for token in self.package_items.get().split(","):
            if not token.strip():continue
            tokens=token.strip().split(":")
            if len(tokens)!=2:raise ValueError("Paket biçimi: 1:2, 3:1")
            output.append((int(tokens[0].strip()),tokens[1].strip()))
        return output

    def package_add(self):
        service.create_service_package(self.conn,self.package_name.get(),self.parsed_package_items())

    def package_update(self):
        service.update_service_package(self.conn,self.package_id(),self.package_name.get(),self.parsed_package_items())

    def package_deactivate(self):
        service.deactivate_service_package(self.conn,self.package_id())

    def package_select(self,_):
        if not self.packages.selection():return
        data=service.package_detail(self.conn,self.package_id())
        self.package_name.delete(0,"end");self.package_name.insert(0,data["package"]["name"])
        self.package_items.delete(0,"end")
        self.package_items.insert(0,", ".join(str(x["service_id"])+":"+str(x["quantity"]) for x in data["items"]))

    def service_id(self):
        selected=self.services.selection()
        if not selected: raise ValueError("Önce hizmet seçin")
        return int(selected[0])

    def service_add(self):
        service.create_service(self.conn,**{k:v.get() for k,v in self.s_fields.items()})

    def service_update(self):
        service.update_service(self.conn,self.service_id(),**{k:v.get() for k,v in self.s_fields.items()})

    def service_deactivate(self):
        service.deactivate_service(self.conn,self.service_id())

    def service_select(self,_):
        selection=self.services.selection()
        if not selection: return
        row=self.conn.execute("SELECT * FROM services WHERE id=?",(int(selection[0]),)).fetchone()
        if row:
            for k,v in self.s_fields.items():
                val=money(row["unit_price_cents"]) if k=="price" else row["vat_percent"] if k=="vat" else row[k]
                v.delete(0,"end");v.insert(0,val)

    def requests_tab(self,parent):
        form=ttk.LabelFrame(parent,text="Yeni Müşteri Talebi",padding=6);form.pack(fill="x")
        ttk.Label(form,text="Müşteri").grid(row=0,column=0,sticky="w",padx=8)
        self.r_customer=ttk.Combobox(form,state="readonly",width=60)
        self.r_customer.grid(row=0,column=1,sticky="ew",padx=8,pady=4)
        self.r_due=_field(form,"Teslim tarihi YYYY-MM-DD (isteğe bağlı)",1)
        ttk.Label(form,text="Talep metni").grid(row=2,column=0,sticky="nw",padx=8)
        self.r_text=tk.Text(form,height=5,width=65,wrap="word")
        self.r_text.grid(row=2,column=1,sticky="ew",padx=8,pady=4)
        form.columnconfigure(1,weight=1)
        buttons=ttk.Frame(form);buttons.grid(row=3,column=1,sticky="e",padx=8,pady=4)
        ttk.Button(buttons,text="Talep Ekle",command=lambda:self.action(self.request_add)).pack(side="left",padx=4)
        ttk.Button(buttons,text="Seçileni Güncelle",command=lambda:self.action(self.request_update)).pack(side="left",padx=4)
        self.requests=self.tree(parent,("id","customer","due","message"),("ID","Firma","Termin","Talep (özet)"),height=11)
        self.requests.bind("<<TreeviewSelect>>",self.request_select)

    @staticmethod
    def combo_id(c):
        value=c.get()
        if not value: raise ValueError("Listeden seçim yapın")
        return int(value.split(" • ",1)[0])

    def request_add(self):
        service.create_request(self.conn,self.combo_id(self.r_customer),self.r_text.get("1.0","end").strip(),self.r_due.get())

    def request_select(self,_):
        if not self.requests.selection():return
        row=self.conn.execute("SELECT * FROM requests WHERE id=?",(int(self.requests.selection()[0]),)).fetchone()
        if row is None:return
        self.r_due.delete(0,"end");self.r_due.insert(0,row["due_date"])
        self.r_text.delete("1.0","end");self.r_text.insert("1.0",row["message"])
        for value in self.r_customer["values"]:
            if value.startswith(str(row["customer_id"])+" • "):self.r_customer.set(value);break

    def request_update(self):
        if not self.requests.selection():raise ValueError("Talep seçiniz")
        service.update_request(self.conn,int(self.requests.selection()[0]),self.combo_id(self.r_customer),
                               self.r_text.get("1.0","end").strip(),self.r_due.get())

    def quotes_tab(self,parent):
        tool=ttk.Frame(parent);tool.pack(fill="x",pady=4)
        ttk.Label(tool,text="Talep").pack(side="left",padx=4)
        self.q_request=ttk.Combobox(tool,state="readonly",width=53);self.q_request.pack(side="left",padx=4)
        ttk.Button(tool,text="Talepten Teklif",command=lambda:self.action(self.quote_add)).pack(side="left",padx=5)
        ttk.Label(tool,text="Ara").pack(side="left",padx=4)
        self.q_search=ttk.Entry(tool,width=16);self.q_search.pack(side="left")
        self.q_search.bind("<KeyRelease>",lambda _:self.refresh_quotes())
        self.quotes=self.tree(parent,("id","customer","status","date"),("ID","Müşteri","Durum","Oluşturulma"),height=8)
        self.quotes.bind("<<TreeviewSelect>>",self.quote_select)
        note_bar=ttk.Frame(parent);note_bar.pack(fill="x",pady=2)
        ttk.Label(note_bar,text="Teklif notu").pack(side="left")
        self.q_note=ttk.Entry(note_bar,width=60);self.q_note.pack(side="left",fill="x",expand=True,padx=4)
        ttk.Button(note_bar,text="Notu Kaydet",command=lambda:self.action(self.quote_note_update)).pack(side="left")
        panel=ttk.LabelFrame(parent,text="Seçili Teklife Satır Ekle",padding=6);panel.pack(fill="x")
        ttk.Label(panel,text="Katalog hizmeti").grid(row=0,column=0,sticky="w",padx=5)
        self.q_service=ttk.Combobox(panel,state="readonly",width=48)
        self.q_service.grid(row=0,column=1,columnspan=4,sticky="ew",padx=5,pady=4)
        self.q_service.bind("<<ComboboxSelected>>",self.quote_service_select)
        self.q_package=ttk.Combobox(panel,state="readonly",width=22)
        self.q_package.grid(row=0,column=5,padx=3)
        ttk.Button(panel,text="Paketi Teklife Ekle",command=lambda:self.action(self.quote_package_add)).grid(row=0,column=6,padx=3)
        entries=[("Açıklama","description"),("Miktar","quantity"),("Fiyat TL","price"),
                 ("İndirim %","discount"),("KDV %","vat")]
        self.q_fields={}
        for i,(label,key) in enumerate(entries):
            ttk.Label(panel,text=label).grid(row=1,column=i,sticky="w",padx=3)
            e=ttk.Entry(panel,width=24 if key=="description" else 12);e.grid(row=2,column=i,sticky="ew",padx=3,pady=4)
            self.q_fields[key]=e
        for k,v in {"quantity":"1","discount":"0","vat":"20"}.items():self.q_fields[k].insert(0,v)
        buttons=ttk.Frame(panel);buttons.grid(row=3,column=0,columnspan=5,sticky="w",pady=5)
        for title,fn in [
          ("Satır Ekle",self.quote_line_add),("Seçili Satırı Sil",self.quote_line_remove),
          ("Teklifi Onayla",self.quote_approve),("Onaylı PDF",self.quote_pdf),
          ("CSV Dışa Aktar",self.quote_csv),("Veritabanı Yedeği",self.quote_backup),("Sürüm Geçmişi",self.quote_history)]:
            ttk.Button(buttons,text=title,command=lambda f=fn:self.action(f)).pack(side="left",padx=3)
        self.lines=self.tree(parent,("id","description","quantity","price","discount","vat"),
           ("ID","Açıklama","Miktar","Fiyat TL","İnd.%","KDV%"),height=6)
        self.quote_total=tk.StringVar(value="Toplam: 0,00 TL")
        ttk.Label(parent,textvariable=self.quote_total,font=("Segoe UI",12,"bold")).pack(anchor="e",padx=12,pady=5)

    def quote_id(self):
        selection=self.quotes.selection()
        if not selection: raise ValueError("Önce teklif seçin")
        return int(selection[0])

    def quote_add(self):
        req_id=self.combo_id(self.q_request)
        service.create_quote(self.conn,request_id=req_id)

    def quote_select(self,_=None):
        for key in self.lines.get_children(): self.lines.delete(key)
        selection=self.quotes.selection()
        if not selection:return
        detail=service.quote_detail(self.conn,int(selection[0]))
        self.q_note.delete(0,"end");self.q_note.insert(0,detail["quote"]["note"])
        for row in detail["lines"]:
            self.lines.insert("", "end", iid=str(row["id"]),values=(row["id"],row["description"][:95],
                row["quantity"],money(row["unit_price_cents"]),row["discount_percent"],row["vat_percent"]))
        self.quote_total.set(f"Toplam: {money(detail['totals']['total_cents'])} TL  •  Durum: {detail['quote']['status']}")

    def quote_service_select(self,_):
        s=self.combo_id(self.q_service)
        row=self.conn.execute("SELECT * FROM services WHERE id=?",(s,)).fetchone()
        if row:
            for key,value in (("description",row["name"]),("price",money(row["unit_price_cents"])),("vat",row["vat_percent"])):
                entry=self.q_fields[key];entry.delete(0,"end");entry.insert(0,value)

    def quote_line_add(self):
        svc_id=self.combo_id(self.q_service) if self.q_service.get() else None
        service.add_line(self.conn,self.quote_id(),svc_id,**{k:v.get() for k,v in self.q_fields.items()})
        self.quote_select()

    def quote_note_update(self):
        service.update_quote_note(self.conn,self.quote_id(),self.q_note.get())
        self.quote_select()

    def quote_package_add(self):
        service.add_package_to_quote(self.conn,self.quote_id(),self.combo_id(self.q_package))
        self.quote_select()

    def quote_history(self):
        win=tk.Toplevel(self);win.title("Sürüm Geçmişi — Salt Okunur");win.geometry("690x400")
        view=tk.Text(win,wrap="word");view.pack(fill="both",expand=True)
        for rev in service.quote_history(self.conn,self.quote_id()):
            snapshot=json.loads(rev["snapshot_json"])
            total=snapshot.get("totals",{}).get("total_cents","v1 baseline")
            view.insert("end","Sürüm "+str(rev["version"])+": "+rev["event"]+"; toplam kuruş: "+str(total)+"\n")
        view.configure(state="disabled")

    def quote_line_remove(self):
        selection=self.lines.selection()
        if not selection:raise ValueError("Önce teklif satırı seçin")
        service.remove_line(self.conn,self.quote_id(),int(selection[0]));self.quote_select()

    def quote_approve(self):
        if messagebox.askyesno("Nihai onay","Teklif onaylandıktan sonra fiyat satırları değiştirilemez. Onaylıyor musunuz?",parent=self):
            service.approve_quote(self.conn,self.quote_id());self.quote_select()

    def quote_pdf(self):
        qid=self.quote_id()
        target=filedialog.asksaveasfilename(parent=self,defaultextension=".pdf",filetypes=[("PDF","*.pdf")],initialfile=f"Teklif-{qid}.pdf")
        if not target:return
        if Path(target).exists() and not messagebox.askyesno("Dosya var","PDF dosyası üzerine yazılsın mı?",parent=self):return
        create_pdf(service.quote_detail(self.conn,qid),target)
        service.mark_exported(self.conn,qid)
        self.quote_select()
        messagebox.showinfo("PDF oluşturuldu",target,parent=self)

    def quote_csv(self):
        target=filedialog.asksaveasfilename(parent=self,defaultextension=".csv",filetypes=[("CSV","*.csv")])
        if target:export_quotes(self.conn,target)

    def quote_backup(self):
        target=filedialog.asksaveasfilename(parent=self,defaultextension=".sqlite3",filetypes=[("SQLite yedeği","*.sqlite3")])
        if target:backup_database(self.conn,target)

    def refresh_customers(self):
        selected=self.customers.selection()
        for item in self.customers.get_children():self.customers.delete(item)
        for row in service.list_customers(self.conn,self.customer_search.get()):
            self.customers.insert("","end",iid=str(row["id"]),values=(row["id"],row["name"],row["email"],row["phone"]))
        if selected and self.customers.exists(selected[0]):self.customers.selection_set(selected[0])

    def refresh_all(self):
        self.refresh_customers()
        for item in self.services.get_children(): self.services.delete(item)
        svcs=service.list_services(self.conn)
        for item in self.packages.get_children(): self.packages.delete(item)
        pkgs=service.list_service_packages(self.conn)
        for pkg in pkgs:
            data=service.package_detail(self.conn,pkg["id"])
            items=", ".join(str(x["name"])+ " x "+str(x["quantity"]) for x in data["items"])
            self.packages.insert("","end",iid=str(pkg["id"]),values=(pkg["id"],pkg["name"],items))
        self.q_package["values"]=[str(pkg["id"])+" • "+pkg["name"] for pkg in pkgs]
        for row in svcs:self.services.insert("","end",iid=str(row["id"]),values=(row["id"],row["name"],row["unit"],money(row["unit_price_cents"]),row["vat_percent"]))
        cust=service.list_customers(self.conn)
        self.r_customer["values"]=[f"{r['id']} • {r['name']}" for r in cust]
        requests=service.list_requests(self.conn)
        self.q_request["values"]=[f"{r['id']} • {r['customer_name']} • {r['message'][:35]}" for r in requests]
        for item in self.requests.get_children():self.requests.delete(item)
        for r in requests:self.requests.insert("","end",iid=str(r["id"]),values=(r["id"],r["customer_name"],r["due_date"],r["message"][:110]))
        self.q_service["values"]=[f"{r['id']} • {r['name']}" for r in svcs]
        self.refresh_quotes()

    def refresh_quotes(self):
        selected=self.quotes.selection()
        for item in self.quotes.get_children():self.quotes.delete(item)
        for r in service.list_quotes(self.conn,self.q_search.get()):
            self.quotes.insert("","end",iid=str(r["id"]),values=(r["id"],r["customer_name"],r["status"],r["created_at"]))
        if selected and self.quotes.exists(selected[0]):
            self.quotes.selection_set(selected[0]);self.quote_select()
        else:self.quote_total.set("Teklif seçiniz")


def run(path=None):
    app=LocalQuoteApp(path)
    app.mainloop()
