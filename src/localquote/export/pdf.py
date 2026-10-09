"""Unicode Turkish PDF output using font preinstalled on the customer's OS."""
from __future__ import annotations
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image, KeepTogether
from ..domain.money import money
from ..domain.pricing import PriceLine, calculate_line

FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
]


def resolve_font() -> Path:
    for item in FONT_CANDIDATES:
        if item.is_file(): return item
    raise RuntimeError("Unicode font bulunamadı: Windows Arial/Segoe UI veya DejaVu Sans yükleyin")


def create_pdf(detail: dict, output_path: Path | str, *, logo_path: Path | str | None = None):
    quote, customer, lines = detail["quote"],detail["customer"],detail["lines"]
    if quote["status"] not in ("APPROVED","EXPORTED"):
        raise ValueError("Nihai PDF için onaylı teklif gerekir")
    if not lines: raise ValueError("Boş teklif")
    if "LQUnicode" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("LQUnicode",str(resolve_font())))
    output_path=Path(output_path)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    styles=getSampleStyleSheet()
    base=ParagraphStyle("LQBase",fontName="LQUnicode",fontSize=9,leading=14,spaceAfter=6)
    small=ParagraphStyle("LQSmall",parent=base,fontSize=8,leading=12)
    title=ParagraphStyle("LQTitle",parent=base,fontSize=19,leading=24,spaceAfter=18,textColor=colors.HexColor("#173651"))
    right=ParagraphStyle("LQRight",parent=small,alignment=TA_RIGHT)
    doc=SimpleDocTemplate(str(output_path),pagesize=A4,rightMargin=17*mm,leftMargin=17*mm,
       topMargin=19*mm,bottomMargin=19*mm,title=f"Teklif #{quote['id']}")
    story=[]
    if logo_path:
        logo=Path(logo_path)
        if logo.suffix.lower() not in (".png",".jpg",".jpeg") or logo.stat().st_size>4_000_000:
            raise ValueError("Logo PNG/JPG ve en fazla 4 MB olmalı")
        pic=Image(str(logo))
        factor=min(1, 40*mm/pic.drawWidth,17*mm/pic.drawHeight)
        pic.drawWidth*=factor;pic.drawHeight*=factor
        story.append(pic)
    story.extend([
      Paragraph("HİZMET TEKLİFİ",title),
      Paragraph(f"<b>Teklif No:</b> {quote['id']} &nbsp;&nbsp; <b>Tarih:</b> {escape(quote['created_at'])}",base),
      Paragraph(f"<b>Müşteri:</b> {escape(customer['name'])}",base),
      Paragraph(f"<b>İletişim:</b> {escape(customer['email'] or customer['phone'] or '-')}",base),
      Spacer(1,12),
    ])
    head=[Paragraph(x,small) for x in ("Açıklama","Miktar","Birim Fiyat","İnd. %","KDV %","Toplam")]
    data=[head]
    for row in lines:
        item=PriceLine(row["description"],row["quantity"],row["unit_price_cents"],row["discount_percent"],row["vat_percent"])
        calc=calculate_line(item)
        data.append([
            Paragraph(escape(item.description).replace("\n","<br/>"),small),
            Paragraph(escape(item.quantity),right),Paragraph(money(item.unit_price_cents),right),
            Paragraph(escape(item.discount_percent),right),Paragraph(escape(item.vat_percent),right),
            Paragraph(money(calc.total_cents),right)
        ])
    table=Table(data,colWidths=[67*mm,18*mm,26*mm,19*mm,18*mm,26*mm],repeatRows=1,hAlign="LEFT")
    table.setStyle(TableStyle([
       ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E8EFF4")),
       ("LINEBELOW",(0,0),(-1,0),0.7,colors.HexColor("#90A3B4")),
       ("VALIGN",(0,0),(-1,-1),"TOP"),
       ("BOTTOMPADDING",(0,0),(-1,-1),7),
       ("TOPPADDING",(0,0),(-1,-1),7),
       ("LINEBELOW",(0,1),(-1,-1),0.25,colors.HexColor("#DDE3E8")),
     ]))
    story.extend([table,Spacer(1,13)])
    totals=detail["totals"]
    summary=[
        ["Ara Toplam",money(totals["gross_cents"]) + " TL"],
        ["İndirim",money(totals["discount_cents"]) + " TL"],
        ["Vergi Matrahı",money(totals["net_cents"]) + " TL"],
        ["KDV",money(totals["vat_cents"]) + " TL"],
        ["GENEL TOPLAM",money(totals["total_cents"]) + " TL"]
    ]
    t=Table([[Paragraph(escape(a),small),Paragraph(escape(b),right)] for a,b in summary],colWidths=[45*mm,36*mm],hAlign="RIGHT")
    t.setStyle(TableStyle([("LINEABOVE",(0,-1),(-1,-1),1,colors.HexColor("#173651")),("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story.append(t)
    if quote["note"]:
        story.extend([Spacer(1,12),Paragraph("<b>Not:</b> " + escape(quote["note"]).replace("\n","<br/>"),base)])
    def footer(canvas,doc):
        canvas.setFont("LQUnicode",7)
        canvas.setFillColor(colors.grey)
        canvas.drawString(17*mm,10*mm,"LocalQuote • Yetkili onayından sonra oluşturuldu")
        canvas.drawRightString(A4[0]-17*mm,10*mm,f"Sayfa {doc.page}")
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return output_path
