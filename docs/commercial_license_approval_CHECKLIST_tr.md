# LocalQuote — ticari kullanım hakkı kesinleştirme kontrolü

**DURUM: HUKUKİ/KULLANICI ONAYI BEKLEYEN TASLAK.**
Bu belge bir yazılım lisansı yayımlamaz ve müşteriye fiilen hak vermez.
Kaynak kod GitHub'da herkese açık olabilir, ancak mevcut depoda proje sahibinin
verdiği bir açık kaynak lisansı bulunmamaktadır.

## Önerilen iş modeli (henüz onaylanmadı)

- Bedel: tek seferlik geliştirme/kurulum bedeli; tutar, kapsam ve ödeme
  takvimi teklif/sözleşmede yazılacak. Zorunlu yıllık/saatlik abonelik yok.
- Kullanım: yalnız adı yazılı müşteri şirketinin kurum içi işleri için,
  ödenmesi ve teslimin kabulü şartıyla, münhasır olmayan, devredilemeyen,
  süresiz yerel çalıştırma izni. Cihaz/sunucu sayısı ayrıca yazılı.
- Teslim: belirli sürüm/commit, kurulum paketi SHA-256, lisans bildirimleri,
  işletim sistemi gereksinimleri ve çalıştırma/yedekleme yönergesi.
- Kaynak kod: teslim/yeniden dağıtım/alt lisans verme varsayılan hak değildir.
  Bunlar ayrıca yazılı kararlaştırılmadıkça verilmez.
- Güncelleme/destek: ayıplı ifa/kusur giderme süresi, kapsamı, azami müdahale
  süresi ve isteğe bağlı ücretli yeni özellikler ayrı madde olmalı; otomatik
  yenilenen gizli abonelik olmamalı.
- Veriler: müşteri cihazı/sunucusunda; kendi yedeklerini yönetmesi, yetki,
  KVKK rolleri, gerektiğinde hizmet sağlayıcı erişimi ayrıca düzenlenmeli.
- Kullanım sınırları: üçüncü tarafa yeniden satış, hizmet olarak sunum,
  başkasına devretme veya kaynak kodu açıkça izin verilmeden yayımlama yok.
  Bunlar hukuken geçerli ve taraflarca kabul edilmiş koşullarla sınırlıdır.
- Üçüncü taraflar: ReportLab/Pillow/charset-normalizer, CPython, Tcl/Tk,
  SQLite, OpenSSL, libffi, zlib, Microsoft runtime, PyInstaller ve varsa
  içe gömülü codec bildirimleri kendi lisansları kapsamında kalır;
  özel sözleşme bu hakları sınırlandıramaz.
- İade/fesih, garanti, sorumluluk sınırları, geçerli hukuk ve yetkili merci
  ile ticari/tüketici mevzuatı uzman hukukçu denetimiyle doldurulmalı.

## İmza öncesi açık sorular (kesinleştirilmesi gerekir)

1. Müşteri başına izin verilen cihaz/sunucu sayısı?
2. Devir veya grup şirketleri için özel hüküm olacak mı?
3. Kaynak kodu teslim/escrow veya özel geliştirme hakkı var mı?
4. Hata düzeltme, teslim-kabul ve destek süreleri ne olacak?
5. Üçüncü taraf DLL ve codec lisanslarının son REDIST/NOTICE denetimi geçildi mi?
6. Gerçek Windows offline kurulum, PDF ve yedekleme kabulü (#2 ve #4) geçti mi?
7. Yazılım sahibi, mali/hukuk danışmanı ve müşteri bu sürümü yazılı onayladı mı?

## Mühendislik kapısı

Şu an #5 = OPEN, ticari dağıtım = HOLD. DRAFT dosyası ve teknik CI PASS
bir araya gelse bile kullanıcı hakları otomatik oluşmaz; son müşteriye
imzalı teklif/sözleşme ve kabul kanıtları gerekir.
