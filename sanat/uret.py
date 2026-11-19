"""Tek seferlik sanat üretimi (20 Kasım 2026): urfaliozgurkamaci için sürrealist tablo "Söndü sandılar".
Ücretsiz ZeroGPU kotasıyla birkaç versiyon üretir, sanat/ klasörüne koyar. Paylaşım yapmaz."""
import os, shutil, traceback
from pathlib import Path
from gradio_client import Client
KOK = Path(__file__).resolve().parent
T = os.environ.get("HF_TOKEN") or None
ISTEM = ("Surrealist oil painting in the manner of Rene Magritte, smooth matte brushwork, museum quality. "
 "A vast empty grey plain at dusk, pale violet sky. In the center, charred logs of a campfire with deep red embers; "
 "rising from the logs, tall tongues of flame sculpted entirely from clear transparent water, flame-shaped, no container, "
 "no glass, no orange fire anywhere above the logs. Small orange carp swim upward inside the water flames. "
 "In the foreground, a pair of worn black men's shoes seen from behind, toes pointing toward the fire. "
 "On a distant hill, two tall slender stone columns side by side. No people, no text, no signature. Silent, lonely.")

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
    for s in (101, 202, 303):
        dene(f"v2_{s}.png", lambda s=s: k.predict(prompt=ISTEM, seed=s, randomize_seed=False, width=896, height=1120,
             guidance_scale=5, num_inference_steps=28, api_name="/infer"))
except Exception:
    log("Krea HATA: " + traceback.format_exc()[-600:])
