# Windows P0 kabul protokolü (Issue #2 ve #4)

**Durum:** HOLD — GitHub Actions testleri gerçek kullanıcı bilgisayarında internetsiz GUI kabulünün yerine geçmez.

## Test düzeneği

Windows 10/11 x64 temiz VM veya yeni Windows hesabı, Python kurulu değil, internet bağlantısı kapalı. GitHub Actions artifact'ından **tüm** `LocalQuote-Desktop` klasörünü kopyalayın (EXE tek başına yeterli değil). Gerçek müşteri verisi kullanmayın.

Kayıt edilecek çevre: tarih, OS derlemesi (`winver`), RAM, CPU, artifact adı, test edilen commit SHA ve EXE SHA-256 (`Get-FileHash .\LocalQuote-Desktop.exe -Algorithm SHA256`). İzin verilmeyen müşteri verilerini kanıt dosyasına koymayın.

## Issue #2 — Tamamen çevrimdışı GUI kabulü

1. Ağ adaptörünü devre dışı bırakın. Python ve internet olmadan EXE'yi Dosya Gezgini üzerinden açın. **PASS:** GUI açılır, hiçbir servis giriş/abonelik penceresi yok.
2. Müşteri ekleyin, güncelleyin ve arşivleyin. Hizmet ekleyin, güncelleyin; hizmet paketi oluşturun ve içine iki hizmet koyun.
3. Talep oluşturun ve metnini güncelleyin. Talebe bağlı teklif oluşturun. Paketi ekleyin ve TL/KDV/indirim toplamlarını elle hesaplayarak doğrulayın.
4. Teklif notunu güncelleyin; sürüm geçmişini görüntüleyin. Teklifi onaylayın; onay sonrası satır/not düzenleme girişimleri reddedilmeli.
5. GUI'den PDF üretin ve CSV dışa aktarın. Programı kapatıp tekrar açın. Müşteri, talep, teklif ve revizyonlar korunmalı.
6. EXE'yi yeniden açıp hiçbir ağ erişimi gerektirmediğini teyit edin. Ekran görüntüleri sentetik veriyle alınmalı.

**FAIL:** Python kurulumu istiyor, ağ erişimi olmadan açılmıyor, kapanıp açılınca veri kaybı, yanlış fiyat veya kilit ihlali.

## Issue #4 — PDF ve geri yükleme kabulü

1. Sentetik Türkçe müşteri/ürün adları: `ÇĞİÖŞÜ çğıöşü`; 50+ satırlı PDF üretin. Sayfa sayısı, fontlar, Türkçe metin, footer ve sayfa taşmalarını gözle kontrol edin.
2. PDF oluştururken PNG/JPEG logo seçin; logonun doğru ölçekte ve bozulmadan göründüğünü doğrulayın. Logo iptalinde yanlış PDF oluşturmamalı.
3. Yedeği GUI'den oluşturun. Uygulamayı kapatın; yedeği farklı bir Windows kullanıcı profilinde **yeni** bir konuma geri yükleyin ve DB kayıt/satır sayılarıyla orijinali karşılaştırın.
4. Var olan bir DB'nin üzerine geri yükleme denemesi engellenmeli. Bozuk DB yedeği reddedilmeli. Veritabanı bütünlüğünü `PRAGMA integrity_check` ile doğrulayın.
5. Tarih/para biçimleri ve çok sayfalı PDF görsel yerleşimini karşılaştırın; yalnızca PDF başlığını görmek yeterli kanıt değil.

## Kanıt formatı

- `evidence/windows-p0/acceptance.md`: ortam, commit, adım bazında PASS/FAIL, test eden kişi, tarih.
- `evidence/windows-p0/exe.sha256`: paket hash'i.
- `evidence/windows-p0/screenshots/`: sentetik verili, müşteri bilgisi içermeyen ekran görüntüleri.
- `evidence/windows-p0/README.md`: kaynak, tekrarlanabilir komutlar, kalan açık durumlar.

Paket için otomatik kanıt: Windows CI `LocalQuote-Windows-CI-Evidence` artifact'ı; bu yalnızca paketli EXE demo, PDF, SQLite ve yedekleme alt testleri için kanıttır.

**Kabul eşiği:** Issue #2 ve #4 yalnızca bu adımların tamamı gerçek Windows makinesinde PASS olduğunda kapatılabilir; aksi halde HOLD.
