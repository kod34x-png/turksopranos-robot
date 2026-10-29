"""Hesabın ve her gönderinin istatistiklerini çekip durum/istatistik.json'a ekler.
İzin eksikse elinden geleni çeker ve eksik izni kaydeder. Anahtar hiçbir yere yazdırılmaz.
"""
import json, os, time, urllib.parse, urllib.request, datetime

API = "https://graph.instagram.com/v21.0"
TOKEN = os.environ["IG_TOKEN"]

def get(yol, **p):
    p["access_token"] = TOKEN
    url = f"{API}/{yol}?" + urllib.parse.urlencode(p)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode()).get("error", {}).get("message", "")
        except Exception:
            msg = str(e.code)
        return None, msg.replace(TOKEN, "***")[:200]

simdi = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M+03:00")
kayit = {"zaman": simdi, "hesap": {}, "icerik": [], "eksikler": []}

hesap, h = get("me", fields="user_id,username,followers_count,follows_count,media_count")
if hesap:
    kayit["hesap"] = {k: hesap.get(k) for k in ("followers_count", "follows_count", "media_count")}
    uid = hesap["user_id"]
    gunluk, h2 = get(f"{uid}/insights", metric="reach,views,profile_views,accounts_engaged,total_interactions",
                     period="day", metric_type="total_value")
    if gunluk:
        kayit["hesap"]["son_gun"] = {m["name"]: m.get("total_value", {}).get("value") for m in gunluk.get("data", [])}
    else:
        kayit["eksikler"].append(f"hesap insights: {h2}")
else:
    kayit["eksikler"].append(f"hesap: {h}")

medya, h = get("me/media", fields="id,caption,media_type,media_product_type,timestamp,like_count,comments_count,permalink", limit=30)
for m in (medya or {}).get("data", []):
    tur = m.get("media_product_type") or m.get("media_type")
    satir = {"id": m["id"], "tur": tur, "zaman": m.get("timestamp"), "link": m.get("permalink"),
             "ilk_satir": (m.get("caption") or "").split("\n")[0][:80],
             "begeni": m.get("like_count"), "yorum": m.get("comments_count")}
    metrikler = ["views", "reach", "saved", "shares", "total_interactions"]
    if tur == "REELS":
        metrikler += ["ig_reels_avg_watch_time", "ig_reels_video_view_total_time"]
    ins, h3 = get(f"{m['id']}/insights", metric=",".join(metrikler))
    if ins is None:                      # metrik metrik dene
        ins = {"data": []}
        for mt in metrikler:
            tek, _ = get(f"{m['id']}/insights", metric=mt)
            if tek:
                ins["data"] += tek.get("data", [])
        if not ins["data"]:
            kayit["eksikler"].append(f"medya insights: {h3}")
    for d in ins.get("data", []):
        v = d.get("values", [{}])[0].get("value") if d.get("values") else d.get("total_value", {}).get("value")
        satir[d["name"]] = v
    kayit["icerik"].append(satir)
    time.sleep(0.5)
if medya is None:
    kayit["eksikler"].append(f"medya listesi: {h}")

kayit["eksikler"] = sorted(set(kayit["eksikler"]))
yol = "durum/istatistik.json"
os.makedirs("durum", exist_ok=True)
tum = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else []
tum.append(kayit)
tum = tum[-120:]                         # son ~4 ay
json.dump(tum, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"hesap": kayit["hesap"], "icerik_sayisi": len(kayit["icerik"]), "eksikler": kayit["eksikler"]}, ensure_ascii=False))
