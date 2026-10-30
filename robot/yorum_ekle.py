"""icerik/yorum_kuyrugu.json içindeki her {medya_id, metin} için ilk yorumu ekler, sonra kuyruğu boşaltır."""
import json, os, urllib.parse, urllib.request
TOKEN = os.environ["IG_TOKEN"]
yol = "icerik/yorum_kuyrugu.json"
kuyruk = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else []
kalan = []
for is_ in kuyruk:
    data = urllib.parse.urlencode({"message": is_["metin"], "access_token": TOKEN}).encode()
    try:
        with urllib.request.urlopen(f"https://graph.instagram.com/v21.0/{is_['medya_id']}/comments", data=data, timeout=60) as r:
            print("Yorum eklendi:", is_["medya_id"], json.loads(r.read()).get("id"))
    except urllib.error.HTTPError as e:
        print("HATA:", is_["medya_id"], e.read().decode().replace(TOKEN, "***")[:300]); kalan.append(is_)
json.dump(kalan, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
