"""Ahsap oyma ASMR denemesi: Tofas Sahin, 5 asama karesi.
Once 1. kare (ham kalas + eller) uretilir, sonraki asamalar ayni kare
duzenlenerek uretilir ki tezgah, eller ve isik sabit kalsin."""
import os, shutil, pathlib, traceback
if os.environ.get("ANONIM"):
    os.environ.pop("HF_TOKEN", None)  # kutuphane bu degiskeni kendiliginden okuyor
from gradio_client import Client, handle_file

T = os.environ.get("HF_TOKEN") or None
OUT = pathlib.Path("deneme/ahsap/cikti"); OUT.mkdir(parents=True, exist_ok=True)
LOG = open(OUT / "log.txt", "a")
def log(m): print(m, flush=True); LOG.write(m + "\n"); LOG.flush()

def yol(r):
    if isinstance(r, (list, tuple)): r = r[0]
    if isinstance(r, dict): r = r.get("path") or r.get("url") or r.get("image")
    return r

SAHNE = ("Overhead close-up photo, only a craftsman's two hands visible on an old dark wooden workbench, "
         "warm soft window light from the left, dark moody background, no face, photorealistic macro woodworking ASMR still, "
         "natural skin texture, five fingers on each hand. ")
AHSAP = ("carved entirely from one solid piece of light natural walnut wood, visible wood grain everywhere, "
         "wooden wheels, wooden windows with no glass, no paint, no chrome, no metal, no logos")
SON = (SAHNE + "Both hands gently hold a finished hand-carved wooden scale model car, 15 cm long, of a classic 1980s "
       "Turkish family sedan inspired by the Fiat 131: boxy three-box four-door body, wide horizontal-bar grille "
       "between rectangular headlights, thick straight bumpers, " + AHSAP + ", smooth satin oiled finish. "
       "A carving knife and curly wood shavings lie on the bench.")

# Geriye dogru: bitmis arabadan kalasa
ASAMALAR = [
    ("kare4", "Keep the same workbench, lighting, camera angle and the same wooden car shape. The left hand holds the car "
              "and the right hand rubs a folded piece of beige sandpaper along its side, the surface slightly less glossy, "
              "fine pale wood dust on the bench. The car stays raw natural walnut wood, no paint."),
    ("kare3", "Keep the same workbench, lighting, camera angle and the same car shape. Make the wooden car look unfinished: "
              "rough raw surface covered with small knife facets, edges less refined, no oil finish. The left hand holds it, "
              "the right hand holds a small carving knife cutting a curl from the hood. More wood shavings on the bench."),
    ("kare2", "Keep the same workbench, lighting, camera angle and hands. Make the wood much less finished: only a coarse "
              "boxy rough-out of the car's basic silhouette, no wheels, windows or grille details yet, big angular knife cuts, "
              "the right hand holds the carving knife. Many wood shavings."),
    ("kare1", "Keep the same workbench, lighting, camera angle and hands. Replace the carved piece with a plain uncut "
              "rectangular block of light walnut wood, 15 cm long, sharp square edges, the right hand touches its corner "
              "with the carving knife. Just a few shavings on the bench."),
]

k5 = OUT / "kare5.png"
if not k5.exists():
    g = Client("mcp-tools/Z-Image-Turbo", token=T)
    r = g.predict(prompt=SON, resolution="864x1536 ( 9:16 )", seed=5131, random_seed=False,
                  steps=9, shift=3, api_name="/generate")
    shutil.copy(yol(r), k5); log("kare5 tamam")

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

onceki = k5
for i, (ad, p) in enumerate(ASAMALAR, 2):
    k = OUT / f"{ad}.png"
    if k.exists():
        onceki = k; continue
    try:
        # Her asama bir oncekinden duzenlenir: asamalar arasi tutarlilik
        r = duzenle(onceki, p, 5131 + i)
        shutil.copy(yol(r), k); log(ad + " tamam"); onceki = k
    except Exception as e:
        log("HATA " + ad + " " + repr(e)[:400]); traceback.print_exc(); break
