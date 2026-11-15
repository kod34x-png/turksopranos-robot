"""Takip ölçer (15 Kasım 2026): takipçi sayısını ve son Reel'in izlenmesini saat başı kaydeder.
Amaç: hangi Reel'in takip getirdiğini görmek. Yalnız okuma yapar. Anahtar yazdırılmaz.
"""
import json, os, urllib.parse, urllib.request, datetime

API = "https://graph.instagram.com/v21.0"; TOKEN = os.environ["IG_TOKEN"]
def get(yol, **p):
    p["access_token"] = TOKEN
    with urllib.request.urlopen(f"{API}/{yol}?" + urllib.parse.urlencode(p), timeout=60) as r:
        return json.loads(r.read().decode())
yol = "durum/takip_saatlik.json"
kayitlar = json.load(open(yol)) if os.path.exists(yol) else []
k = {"zaman": (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M+03:00")}
try:
    me = get("me", fields="user_id,followers_count,media_count")
    k["takipci"] = me.get("followers_count"); k["medya"] = me.get("media_count")
    son = get(f"{me['user_id']}/media", fields="id,timestamp,media_product_type", limit=3).get("data", [])
    for m in son:
        if m.get("media_product_type") == "REELS":
            k["son_reel"] = m["id"]; k["son_reel_zaman"] = m["timestamp"]
            try:
                d = get(f"{m['id']}/insights", metric="reach,views").get("data", [])
                k.update({x["name"]: x["values"][0]["value"] for x in d})
            except Exception as e:
                k["insights_hata"] = str(e)[:80]
            break
except Exception as e:
    k["hata"] = str(e).replace(TOKEN, "***")[:150]
kayitlar.append(k); json.dump(kayitlar, open(yol, "w"), ensure_ascii=False, indent=1); print(k)
