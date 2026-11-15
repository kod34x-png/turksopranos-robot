"""Kabadayı kütüphanesi (15 Kasım 2026): ücretsiz ZeroGPU kotasıyla her gün birkaç kare ve bir kısa klip üretir.
Harman Reel'ler bu kütüphaneden beslenir (robot/uret.py -> kutuphane_sec). Kota bitince sessizce durur.
Görseller: suç/şiddet/silah/kumar yok; sakin, bedel ödemiş bir adam.
"""
import json, os, shutil, sys
from pathlib import Path
KOK = Path(__file__).resolve().parent.parent
STIL = ("Photorealistic cinematic film still, Istanbul, tungsten light, 35mm film grain, muted colors, "
        "no text, no letters, no weapons, no cards, no gambling. ")
KARE_SAYISI = int(os.environ.get("KARE_SAYISI", "3"))
KUT = KOK / "medya/kabadayi/kutuphane"; IDX = KOK / "medya/kabadayi/kutuphane.json"

def tek_yol(s):
    while isinstance(s, (list, tuple)):
        s = s[0]
    if isinstance(s, dict):
        s = s.get("video") or s.get("image") or s.get("path")
    if isinstance(s, dict):
        s = s.get("path")
    return s

def kaydet(m):
    print(m, flush=True)
    with open(KUT / "uretim.log", "a", encoding="utf-8") as f:
        f.write(m + "\n")

def main():
    from gradio_client import Client, handle_file
    KUT.mkdir(parents=True, exist_ok=True)
    T = os.environ.get("HF_TOKEN") or None
    lst = json.load(open(IDX, encoding="utf-8"))
    istem = json.load(open(KOK / "icerik/kutuphane_istem.json", encoding="utf-8"))
    yapilan = {x.get("istem_no") for x in lst if x.get("istem_no")}
    sira = [i for i in istem if i["no"] not in yapilan][:KARE_SAYISI]
    if not sira:
        print("Bütün istemler üretildi; yeni istem eklenmeli."); return
    yeni = []
    g = Client("mcp-tools/Z-Image-Turbo", token=T)
    for i in sira:
        k = KUT / f"k{i['no']:03d}.png"
        try:
            r = g.predict(prompt=STIL + i["gorsel"], resolution="864x1536 ( 9:16 )", seed=1000 + i["no"],
                          random_seed=False, steps=9, shift=3, api_name="/generate")
            shutil.copy(tek_yol(r), k)
            e = {"dosya": str(k.relative_to(KOK)), "tur": "kare", "karakter": True, "istem_no": i["no"], "not": i["gorsel"][-80:]}
            lst.append(e); yeni.append((i, k)); kaydet(f"kare {i['no']} tamam")
        except Exception as ex:
            kaydet("kare durdu: " + repr(ex)[:300]); break
    json.dump(lst, open(IDX, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if not yeni:
        return
    i, k = yeni[0]
    try:
        v = Client("zerogpu-aoti/wan2-2-fp8da-aoti-faster", token=T)
        r = v.predict(input_image=handle_file(str(k)), prompt=i["hareket"], duration_seconds=4, steps=6, api_name="/generate_video")
        o = KUT / f"k{i['no']:03d}.mp4"; shutil.copy(tek_yol(r), o)
        lst.append({"dosya": str(o.relative_to(KOK)), "tur": "klip", "bas": 0.2, "karakter": True, "istem_no_klip": i["no"],
                    "not": "klip: " + i["hareket"][:60]})
        json.dump(lst, open(IDX, "w", encoding="utf-8"), ensure_ascii=False, indent=1); kaydet(f"klip {i['no']} tamam")
    except Exception as ex:
        kaydet("klip durdu: " + repr(ex)[:300])

if __name__ == "__main__":
    main()
