"""Kabadayi Girseydi: hazir ve yayinlanmamis ilk bolumu Reel olarak atar. Anahtar yazdirilmaz."""
import datetime, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

API = "https://graph.instagram.com/v21.0"
KOK = Path(__file__).resolve().parent.parent
REPO = os.environ["GITHUB_REPOSITORY"]
DURUM = KOK / "durum/kabadayi.json"
yapilan = json.load(open(DURUM, encoding="utf-8")) if DURUM.exists() else []
biten = {k["no"] for k in yapilan if k.get("reel_id")}
simdi = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
bugun = simdi.strftime("%Y-%m-%d")
if (KOK / "robot/DURAKLAT").exists() or (KOK / "robot/KABADAYI_DURDUR").exists():
    sys.exit("Duraklatildi.")
if any(k.get("tarih") == bugun for k in yapilan):
    print("Bugun zaten paylasildi."); sys.exit(0)
if os.environ.get("ELLE") != "evet" and (simdi.weekday() != 5 or simdi.strftime("%H:%M") < "13:00"):
    print("Vakit degil."); sys.exit(0)
b = next((x for x in json.load(open(KOK / "icerik/kabadayi.json", encoding="utf-8"))
          if x["durum"] == "onayli" and x["no"] not in biten and (KOK / f"medya/kabadayi/{x['no']}.mp4").exists()), None)
if not b:
    print("Hazir bolum yok, bu hafta atlandi."); sys.exit(0)
TOKEN = os.environ["IG_TOKEN"]

def istek(method, url, params):
    params = dict(params); params["access_token"] = TOKEN; body = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        body = urllib.parse.urlencode(params).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, method=method), timeout=300) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{e.code} {e.read().decode()}".replace(TOKEN, "***"))

taban = f"https://raw.githubusercontent.com/{REPO}/main/medya/kabadayi/{b['no']}"
sonuc = {"tarih": bugun, "no": b["no"]}
try:
    ig = istek("GET", f"{API}/me", {"fields": "user_id"})["user_id"]
    kap = istek("POST", f"{API}/{ig}/media", {"media_type": "REELS", "video_url": taban + ".mp4", "cover_url": taban + "-kapak.jpg",
                                               "caption": b["aciklama"], "share_to_feed": "true"})
    for _ in range(60):
        st = istek("GET", f"{API}/{kap['id']}", {"fields": "status_code"}).get("status_code")
        if st == "FINISHED":
            break
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"video islenemedi: {st}")
        time.sleep(10)
    else:
        raise RuntimeError("zaman asimi")
    sonuc["reel_id"] = istek("POST", f"{API}/{ig}/media_publish", {"creation_id": kap["id"]})["id"]
    print("Reel yayinlandi", b["no"])
except Exception as e:
    sonuc["hata"] = str(e)[:500]; print("HATA", sonuc["hata"])
sonuc["zaman"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
yapilan = [k for k in yapilan if not (k["no"] == b["no"] and "hata" in k)] + [sonuc]
json.dump(yapilan, open(DURUM, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
