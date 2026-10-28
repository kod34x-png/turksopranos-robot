"""Instagram'a Reel + hikâye + alıntı kartı gönderisi yayınlar.
Kullanım: python robot/yayinla.py <gün_json> <çıktı_klasörü> <kart_public_url|"">
Anahtar IG_TOKEN ortam değişkeninden okunur; hiçbir yere yazdırılmaz.
"""
import json, os, sys, time, urllib.parse, urllib.request

API = "https://graph.instagram.com/v21.0"
TOKEN = os.environ["IG_TOKEN"]
gun = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]
KART_URL = sys.argv[3] if len(sys.argv) > 3 else ""
VIDEO_URL = sys.argv[4] if len(sys.argv) > 4 else ""
sonuc = {"tarih": gun["tarih"], "no": gun["no"]}
# Bugün daha önce yapılanları atla (tekrar paylaşım olmasın)
onceki = {}
if os.path.exists("durum/yayinlanan.json"):
    for k in json.load(open("durum/yayinlanan.json", encoding="utf-8")):
        if k.get("tarih") == gun["tarih"]:
            for a in ("reel_id", "hikaye_id", "gonderi_id"):
                if k.get(a): onceki[a] = k[a]
sonuc.update(onceki)

def istek(method, url, params=None, data=None, headers=None):
    params = dict(params or {}); params["access_token"] = TOKEN
    if method == "GET":
        url = url + "?" + urllib.parse.urlencode(params); body = None
    else:
        body = data if data is not None else urllib.parse.urlencode(params).encode()
        if data is not None:
            url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        hata = e.read().decode()
        raise RuntimeError(f"{e.code} {hata}".replace(TOKEN, "***"))

me = istek("GET", f"{API}/me", {"fields": "user_id,username"})
IG = me["user_id"]

def bekle(cid, ad):
    for _ in range(60):
        st = istek("GET", f"{API}/{cid}", {"fields": "status_code,status"})
        if st.get("status_code") == "FINISHED":
            return
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"{ad} işlenemedi: {st}")
        time.sleep(10)
    raise RuntimeError(f"{ad} zaman aşımı")

def video_yukle(media_type, caption=None):
    params = {"media_type": media_type, "video_url": VIDEO_URL}
    if caption:
        params["caption"] = caption
    if media_type == "REELS":
        params["share_to_feed"] = "true"
    kap = istek("POST", f"{API}/{IG}/media", params)
    bekle(kap["id"], media_type)
    return istek("POST", f"{API}/{IG}/media_publish", {"creation_id": kap["id"]})["id"]

# 1) Reel
if "reel_id" not in sonuc:
  try:
    sonuc["reel_id"] = video_yukle("REELS", gun["reel_aciklama"])
    print("Reel yayınlandı")
  except Exception as e:
    sonuc["reel_hata"] = str(e)[:500]; print("Reel HATA:", sonuc["reel_hata"])

# 2) Hikâye (aynı video)
if "hikaye_id" not in sonuc:
  try:
    sonuc["hikaye_id"] = video_yukle("STORIES")
    print("Hikâye yayınlandı")
  except Exception as e:
    sonuc["hikaye_hata"] = str(e)[:500]; print("Hikâye HATA:", sonuc["hikaye_hata"])

# 3) Alıntı kartı gönderisi
if "gonderi_id" in sonuc:
    pass
elif KART_URL:
    try:
        kap = istek("POST", f"{API}/{IG}/media", {"image_url": KART_URL, "caption": gun["kart_aciklama"]})
        bekle(kap["id"], "Gönderi")
        sonuc["gonderi_id"] = istek("POST", f"{API}/{IG}/media_publish", {"creation_id": kap["id"]})["id"]
        print("Gönderi yayınlandı")
    except Exception as e:
        sonuc["gonderi_hata"] = str(e)[:500]; print("Gönderi HATA:", sonuc["gonderi_hata"])
else:
    sonuc["gonderi_hata"] = "Kart için herkese açık link yok (depo gizli)"

sonuc["zaman"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
json.dump(sonuc, open(os.path.join(OUT, "sonuc.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
