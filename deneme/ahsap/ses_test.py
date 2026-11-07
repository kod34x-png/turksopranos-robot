"""Ahsap oyma ASMR: her yavaslatilmis klip icin videoya uygun ses (MMAudio).
Klip basina ayri komut: hareket ile ses birebir eslessin."""
import os, shutil, pathlib, traceback
if os.environ.get("ANONIM"):
    os.environ.pop("HF_TOKEN", None)
from gradio_client import Client, handle_file

D = pathlib.Path("deneme/ahsap/ses"); OUT = D / "cikti"; OUT.mkdir(parents=True, exist_ok=True)
LOG = open(OUT / "log.txt", "a")
def log(m): print(m, flush=True); LOG.write(m + "\n"); LOG.flush()

def yol(r):
    if isinstance(r, (list, tuple)): r = r[0]
    if isinstance(r, dict): r = r.get("video") or r.get("path") or r.get("url")
    return r

ORTAK = ", close-up microphone, crisp high detail ASMR, quiet workshop room, no music, no speech"
NEG = "music, speech, voice, singing, wind, noise hiss, electronic beeps, loud bang"
KOMUT = [
    ("yavas1", "sharp knife carving into a hard wooden block, crisp wood cutting and scraping, small wood shavings crackling and dropping onto a wooden table" + ORTAK),
    ("yavas2", "small carving knife slicing thin curls of wood, delicate crunchy wood shaving sounds, light tapping on wood" + ORTAK),
    ("yavas3", "knife set down on a wooden bench, then sandpaper rubbing back and forth on smooth wood, soft rhythmic scratchy sanding" + ORTAK),
    ("yavas4", "last soft sandpaper strokes on wood, then a small wooden toy car gently placed and lifted on a wooden table, soft wooden knock" + ORTAK),
    ("yavas5", "quiet calm workshop room tone, a few tiny wood shavings settling, faint soft hand movement" + ORTAK),
]

c = Client("hkchengrex/MMAudio")
if not (OUT / "api.txt").exists():
    (OUT / "api.txt").write_text(str(c.view_api(print_info=False, return_format="str")))

for ad, p in KOMUT:
    v = OUT / f"{ad}.mp4"
    if v.exists():
        continue
    try:
        r = c.predict({"video": handle_file(str(D / f"{ad}.mp4"))}, p, NEG, 2026, 25, 4.5, 8, api_name="/video_to_audio")
        shutil.copy(yol(r), v); log(ad + " tamam")
    except Exception as e:
        log("HATA " + ad + " " + repr(e)[:400]); traceback.print_exc(); break
