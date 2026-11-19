"""Tek seferlik sanat üretimi (20 Kasım 2026): urfaliozgurkamaci için sürrealist tablo "Söndü sandılar".
Ücretsiz ZeroGPU kotasıyla birkaç versiyon üretir, sanat/ klasörüne koyar. Paylaşım yapmaz."""
import os, shutil, traceback
from pathlib import Path
from gradio_client import Client
KOK = Path(__file__).resolve().parent
T = os.environ.get("HF_TOKEN") or None
ISTEM = ("Surrealist oil painting in the manner of Rene Magritte, smooth matte brushwork, museum quality. "
 "A vast empty plain at dusk under a pale quiet violet sky. In the center a tall bonfire whose flames are made "
 "entirely of clear rippling water, orange carp fish swimming slowly upward inside the water flames. At the very "
 "bottom, beneath the water, a bed of embers still glowing deep red. On the sand in front, a pair of worn black men's "
 "leather shoes placed neatly side by side, toes pointing toward the fire. Far away on a low hill, two faint ancient "
 "stone columns. No people, no figures, no text, no signature. Silent, solemn, lonely, eerie.")

def yol(s):
    while isinstance(s, (list, tuple)): s = s[0]
    if isinstance(s, dict): s = s.get("image") or s.get("path") or s.get("url")
    if isinstance(s, dict): s = s.get("path")
    return s

def log(m):
    print(m, flush=True)
    with open(KOK / "uretim.log", "a", encoding="utf-8") as f: f.write(m + "\n")

def dene(ad, fn):
    try:
        shutil.copy(yol(fn()), KOK / ad); log(f"{ad} tamam")
    except Exception:
        log(f"{ad} HATA: " + traceback.format_exc()[-600:])

try:
    k = Client("mcp-tools/FLUX.1-Krea-dev", token=T)
    log(str(k.view_api(print_info=False, return_format="dict"))[:1500])
    for s in (11, 27, 45, 63):
        dene(f"krea_{s}.png", lambda s=s: k.predict(prompt=ISTEM, seed=s, randomize_seed=False, width=896, height=1120,
             guidance_scale=4.5, num_inference_steps=28, api_name="/infer"))
except Exception:
    log("Krea HATA: " + traceback.format_exc()[-600:])
try:
    z = Client("mcp-tools/Z-Image-Turbo", token=T)
    for s in (7, 19):
        dene(f"zimage_{s}.png", lambda s=s: z.predict(prompt=ISTEM, resolution="1024x1280 ( 4:5 )", seed=s,
             random_seed=False, steps=9, shift=3, api_name="/generate"))
except Exception:
    log("Z HATA: " + traceback.format_exc()[-600:])
