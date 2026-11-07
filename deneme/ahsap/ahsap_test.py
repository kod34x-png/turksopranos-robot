"""Ahsap oyma ASMR denemesi: Tofas Sahin, 5 asama karesi.
Once 1. kare (ham kalas + eller) uretilir, sonraki asamalar ayni kare
duzenlenerek uretilir ki tezgah, eller ve isik sabit kalsin."""
import os, shutil, pathlib, traceback
from gradio_client import Client, handle_file

T = None if os.environ.get("ANONIM") else (os.environ.get("HF_TOKEN") or None)
OUT = pathlib.Path("deneme/ahsap/cikti"); OUT.mkdir(parents=True, exist_ok=True)
LOG = open(OUT / "log.txt", "a")
def log(m): print(m, flush=True); LOG.write(m + "\n"); LOG.flush()

def yol(r):
    if isinstance(r, (list, tuple)): r = r[0]
    if isinstance(r, dict): r = r.get("path") or r.get("url") or r.get("image")
    return r

ARABA = ("a hand-carved wooden scale model of a 1980s boxy four-door sedan, long flat hood, "
         "small rectangular headlights, straight sharp body lines, upright trunk, no logos, no emblems")

ILK = ("Overhead close-up photo, only a craftsman's two hands visible on an old dark wooden workbench, "
       "left hand holding a rectangular raw block of light walnut wood about 20 cm long, "
       "right hand holding a small sharp carving knife touching the block, a few curly wood shavings, "
       "warm soft window light from the left, dark moody background, no face, "
       "photorealistic macro woodworking ASMR still, natural skin texture, five fingers on each hand")

ASAMALAR = [
    ("kare2", "Keep the same hands, workbench, lighting and camera angle. The wooden block is now roughly cut "
              "into the basic silhouette of a boxy 1980s four-door sedan, coarse knife marks, many fresh wood shavings on the bench."),
    ("kare3", "Keep the same hands, workbench, lighting and camera angle. The wood is now clearly carved into " + ARABA +
              ", wheel arches and windows cut in, still rough raw surface with tool marks, wood shavings around."),
    ("kare4", "Keep the same hands, workbench, lighting and camera angle. The hands are now sanding " + ARABA +
              " with a piece of sandpaper, smooth surface, fine wood dust on the bench."),
    ("kare5", "Keep the same hands and workbench. The hands now gently hold the finished polished " + ARABA +
              ", glossy oiled walnut grain, detailed carved wheels, bumpers and grille, shavings in the background."),
]

# 1. kare
k1 = OUT / "kare1.png"
if not k1.exists():
    g = Client("mcp-tools/Z-Image-Turbo", token=T)
    r = g.predict(prompt=ILK, resolution="864x1536 ( 9:16 )", seed=7311, random_seed=False,
                  steps=9, shift=3, api_name="/generate")
    shutil.copy(yol(r), k1); log("kare1 tamam")

# Duzenleme araci: once FLUX Kontext, olmazsa Qwen Image Edit
duz = None
for sp in ["mcp-tools/FLUX.1-Kontext-Dev", "prithivMLmods/Qwen-Image-Edit-2509-LoRAs-Fast"]:
    try:
        c = Client(sp, token=T)
        log("API " + sp + "\n" + str(c.view_api(print_info=False, return_format="str"))[:2500])
        duz = (sp, c); break
    except Exception as e:
        log("acilmadi " + sp + " " + repr(e)[:200])

def duzenle(girdi, prompt, seed):
    sp, c = duz
    if "Kontext" in sp:
        return c.predict(input_image=handle_file(str(girdi)), prompt=prompt, seed=seed,
                         randomize_seed=False, guidance_scale=2.5, steps=24, api_name="/infer")
    return c.predict(images=[handle_file(str(girdi))], prompt=prompt, seed=seed,
                     randomize_seed=False, api_name="/infer")

onceki = k1
for i, (ad, p) in enumerate(ASAMALAR, 2):
    k = OUT / f"{ad}.png"
    if k.exists():
        onceki = k; continue
    try:
        # Her asama bir oncekinden duzenlenir: asamalar arasi tutarlilik
        r = duzenle(onceki, p, 7311 + i)
        shutil.copy(yol(r), k); log(ad + " tamam"); onceki = k
    except Exception as e:
        log("HATA " + ad + " " + repr(e)[:400]); traceback.print_exc(); break
