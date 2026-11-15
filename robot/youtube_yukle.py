"""Günün Reel'ini YouTube Shorts olarak da yükler (15 Kasım 2026 kararı).
Kullanım: python robot/youtube_yukle.py <gün_json> <video> <çıktı_klasörü>
Anahtarlar (YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN) GitHub gizli kasasından gelir; yoksa sessizce çıkar.
Hiçbir anahtar yazdırılmaz. Instagram Reel'i bugün yayınlanmadıysa yüklemez; aynı gün iki kez yüklemez.
"""
import json, os, sys, urllib.parse, urllib.request

ID, SIR, YEN = (os.environ.get(k, "") for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))
if not (ID and SIR and YEN):
    print("YouTube anahtarları yok; atlanıyor."); sys.exit(0)
gun = json.load(open(sys.argv[1], encoding="utf-8")); video = sys.argv[2]; out = sys.argv[3]
sy = os.path.join(out, "sonuc.json")
sonuc = json.load(open(sy, encoding="utf-8")) if os.path.exists(sy) else {}
onceki = {}
if os.path.exists("durum/yayinlanan.json"):
    onceki = next((k for k in json.load(open("durum/yayinlanan.json")) if k.get("tarih") == gun["tarih"]), {})
if onceki.get("youtube_id") or sonuc.get("youtube_id"):
    print("Bugün YouTube'a zaten yüklendi."); sys.exit(0)
if not (sonuc.get("reel_id") or onceki.get("reel_id")):
    print("Instagram Reel'i henüz yok; YouTube bekliyor."); sys.exit(0)

def gizle(m):
    for s in (ID, SIR, YEN):
        m = m.replace(s, "***")
    return m

try:
    t = urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=urllib.parse.urlencode(
        {"client_id": ID, "client_secret": SIR, "refresh_token": YEN, "grant_type": "refresh_token"}).encode()), timeout=60)
    erisim = json.loads(t.read())["access_token"]
    ilk = gun["reel_aciklama"].split("\n")[0].replace("🎩", "").strip()
    baslik = (ilk[:80] + " #Shorts")[:100]
    aciklama = gun["reel_aciklama"].replace("Yarın #", "Yarın Sokak Dersi #") + "\n\nInstagram: @turksopranos"
    govde = {"snippet": {"title": baslik, "description": aciklama[:4900], "categoryId": "22", "defaultLanguage": "tr"},
             "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}
    boy = os.path.getsize(video)
    r = urllib.request.urlopen(urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(govde).encode(), method="POST",
        headers={"Authorization": f"Bearer {erisim}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(boy)}), timeout=60)
    yer = r.headers["Location"]
    r = urllib.request.urlopen(urllib.request.Request(yer, data=open(video, "rb").read(), method="PUT",
        headers={"Authorization": f"Bearer {erisim}", "Content-Type": "video/mp4"}), timeout=600)
    sonuc["youtube_id"] = json.loads(r.read())["id"]
    print("YouTube'a yüklendi:", sonuc["youtube_id"])
except urllib.error.HTTPError as e:
    sonuc["youtube_hata"] = gizle(f"{e.code} {e.read().decode()[:300]}"); print("YouTube HATA:", sonuc["youtube_hata"])
except Exception as e:
    sonuc["youtube_hata"] = gizle(repr(e)[:300]); print("YouTube HATA:", sonuc["youtube_hata"])
if sonuc:
    sonuc.setdefault("tarih", gun["tarih"]); sonuc.setdefault("no", gun["no"])
    json.dump(sonuc, open(sy, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
