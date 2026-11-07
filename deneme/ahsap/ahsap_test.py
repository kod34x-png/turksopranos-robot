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
    if isinstance(r, dict): r = r.get("video") or r.get("path") or r.get("url") or r.get("image")
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

# Geriye dogru: zimpara karesinden kalasa. Her karede yalnizca IKI el.
IKI = (" Exactly two human hands in the whole image, no third hand: the left hand at the bottom holds the wood, "
       "the right hand at the top holds the tool. Same camera angle, workbench and window light.")
ASAMALAR = [
    ("kare4", "unused"),
    ("kare3", "Remove the sandpaper. The right hand at the top now holds a small carving knife slicing a thin curl from the roof. "
              "Make the wooden car clearly unfinished: rough raw surface covered with visible flat knife facets, "
              "softer less refined details, wheels only roughly shaped, no polish." + IKI),
    ("kare2", "Make the wood much less finished: only a coarse boxy rough-out of the car's basic silhouette with big angular "
              "knife cuts, no wheels, no windows, no grille details yet, many fresh wood shavings." + IKI),
    ("kare1", "Replace the carved piece with a plain uncut rectangular block of light walnut wood, 15 cm long, sharp square "
              "edges, the knife touching one corner, just a few shavings on the bench." + IKI),
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
        r = duzenle(onceki, p, 6262 + i)
        shutil.copy(yol(r), k); log(ad + " tamam"); onceki = k
    except Exception as e:
        log("HATA " + ad + " " + repr(e)[:400]); traceback.print_exc(); break

# Gecis videolari: her iki kare arasi oyma hareketi
GECIS = [
    ("gecis1", "kare1", "kare2", "Hands carving the wooden block with a small knife, wood shavings curling off and falling, the block slowly taking the shape of a small car, steady overhead camera, realistic woodworking ASMR"),
    ("gecis2", "kare2", "kare3", "The right hand slices thin wood curls from the wooden car roof with a knife, shavings falling, steady camera, realistic slow woodworking"),
    ("gecis3", "kare3", "kare4", "The hand puts the knife away and rubs sandpaper along the side of the wooden car, fine dust, steady camera, realistic slow motion"),
    ("gecis4", "kare4", "kare5", "The hands finish sanding and gently lift and present the finished wooden toy car, steady camera, realistic slow motion"),
]
NEG = "extra hands, third hand, extra fingers, deformed hands, fused fingers, morphing, camera shake, cuts, text, watermark, blurry, static frame"
vc = Client("mcp-tools/wan-2-2-first-last-frame", token=T)
for ad, a_, b_, p in GECIS:
    v = OUT / f"{ad}.mp4"
    if v.exists():
        continue
    try:
        r = vc.predict(start_image_pil=handle_file(str(OUT / f"{a_}.png")), end_image_pil=handle_file(str(OUT / f"{b_}.png")),
                       prompt=p, negative_prompt=NEG, duration_seconds=3.5, steps=8, guidance_scale=1.0,
                       guidance_scale_2=1.0, seed=777, randomize_seed=False, api_name="/generate_video")
        shutil.copy(yol(r), v); log(ad + " tamam")
    except Exception as e:
        log("HATA " + ad + " " + repr(e)[:300]); break
