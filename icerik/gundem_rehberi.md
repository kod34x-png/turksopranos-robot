# Gündem videosu rehberi (20 Kasım 2026, Özgür'ün kararı)

Her gün o günün Türkiye gündeminden **tek** olay seçilir; Sokak Dersi'nin satırları bu olaydan **ince bir mesajla** yazılır.
Olay açıkça anlatılmaz, adı konmaz; ama o gün haberi gören herkes "bu o mevzu" diye anlar. Ses: Özgür'ün kendi klonu.

## Seçim
- O gün gerçekten çok konuşulan, sokağın da konuştuğu bir olay (fırtına, ekonomi, maç, ihanet, bir tartışma, bir dönüş...).
- **Yasak:** ölüm/cenaze/kaza/afet acısından mesaj çıkarmak; suçu veya şiddeti özendirmek; gerçek kişiyi karalamak, isim vermek;
  parti/siyasetçi tarafı tutmak; çocuklar. Emin değilsen o olayı seçme, bir sonrakine geç.

## Yazım
- 4–6 satır, her satır ekranda 2–3 kısa kısım (`\n`), Türkçe, emekli kabadayı ağzı: sakin, tok, bedel ödemiş.
- Kalıp: 1) olaya gizli gönderme ("Bugün lodos esti.") 2) çift anlamlı ikinci satır 3) "Ben gençken..." itirafı 4) ders 5) kısa kapanış.
- Her satırın vurgu kelimesi satırın içinde aynen geçmeli (2. eleman). 3. eleman 2.4.
- Açıklamanın ilk satırı videonun en güçlü iki satırı + 🎩; sonra "Sokak Dersi #N", bir "gönder" çağrısı, "Yarın #N+1 — takip et, kaçırma.",
  olayla ilgili 1–2 etiket + #sokakdersi #hayatdersleri #türksopranos.

## Ses
- Seslendirilecek metinde â/î/û yerine a/i/u yaz; virgül ve nokta koy; çok kısa cümle kur.
- `araclar/ozgur_ses.py <ses-klonu/referans> <klasör> "satır1" ...` — benzerlik 0.9 altındaki satırı yeniden yaz/üret.
- Çıktılar 44.1 kHz'e çevrilip `medya/ses/<TARİH>/s0.wav ...` olarak konur; takvim girdisine `"hazir_ses": true` ve `"gundem": "..."` eklenir.
- Özgür'ün referansları/modeli bu depoya **asla** konmaz (depo herkese açık). Sadece bitmiş satır sesleri konur.

## Elle hazırlanmış günler
- Takvimde `"bicim": "hazir_video"` olan güne dokunma: videosu `medya/<TARİH>-reel.mp4` olarak Özgür'ün onayıyla hazır konmuştur
  (ilki 21 Kasım 2026, Sokak Dersi #25 "FON / DİP"). Gündem videosu o gün üretilmez; sonraki günden devam edilir.
