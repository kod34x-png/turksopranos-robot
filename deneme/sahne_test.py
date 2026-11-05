"""Kabadayi Girseydi 1. bolum: kareler, hareket, Turkce dis ses. Tekrar calisinca bitenleri atlar."""
import json, os, shutil, sys, time, traceback
from pathlib import Path
from gradio_client import Client, handle_file

T = os.environ.get("HF_TOKEN") or None
C = Path("deneme/cikti"); C.mkdir(parents=True, exist_ok=True)
log = open(C / "log.txt", "a")
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.write(s + "\n"); log.flush()

STIL = ("Photorealistic cinematic film still, 1980s Istanbul, dark backroom gambling den, "
        "green felt card table, tungsten light, cigarette smoke, 35mm film grain, muted colors, crime drama. ")
ADAM = ("a broad-shouldered Turkish man in his sixties, thick black moustache, no beard, long black wool "
        "overcoat, black flat cap, his face almost entirely in deep shadow")
SAHNELER = [
 ("Close-up of a trembling young man's hand pushing a folded paper shop deed onto the green card table, "
  "playing cards around it, sweat on his knuckles, a thick-necked older gambler's hand reaching for it.",
  "The young hand slowly slides the paper forward, fingers trembling, smoke drifts, slow push-in", 4),
 ("Wide shot from inside the room: the door at the back bursts open, hard white light from the alley behind, "
  f"silhouette of {ADAM} standing in the doorway, three gamblers at the table in foreground turning their heads.",
  "The door swings open, light floods in, the silhouetted man stands still, the men at the table turn their heads, smoke swirls", 4),
 (f"Low angle shot of {ADAM}, walking slowly toward camera between the card tables, backlit, smoke behind him, "
  "men in the background looking down.",
  "The man walks slowly and heavily toward the camera, overcoat moving, smoke drifting, steady tracking shot", 4),
 ("Extreme close-up of a large weathered male hand with a silver ring placing itself flat on top of a folded paper deed "
  "on green felt, stopping another hand from taking it, face not visible.",
  "The large hand presses down firmly on the paper, the other hand slowly pulls back, subtle motion, shallow focus", 4),
 (f"Back view from inside: a young man in a worn jacket walks out through the open door into dawn light on a wet "
  f"Istanbul alley, {ADAM} stands beside the door seen from behind, folded paper deed in his hand.",
  "The young man walks out slowly into the dawn light, the older man stays still, smoke drifts out of the door, slow pull-back", 4),
]
SES = "Evlat. Babanın alın terini masaya süren, kazansa da kaybeder. Kalk. Eve git."

def yol(s):
    s = s[0] if isinstance(s, (list, tuple)) else s
    if isinstance(s, (list, tuple)): s = s[0]
    if isinstance(s, dict): s = s.get("image") or s.get("video") or s.get("path") or s
    if isinstance(s, dict): s = s.get("path")
    return s

def dene(ad, f, kac=2):
    for i in range(kac):
        try:
            return f()
        except Exception as e:
            p("HATA", ad, i, repr(e)[:400])
            if "quota" in str(e).lower(): return None
            time.sleep(20)

g = Client("mcp-tools/Z-Image-Turbo", token=T)
for i, (prm, _, _) in enumerate(SAHNELER, 1):
    k = C / f"kare{i}.png"
    if k.exists(): continue
    r = dene(f"kare{i}", lambda: g.predict(prompt=STIL + prm, resolution="864x1536 ( 9:16 )", seed=100 + i,
        random_seed=False, steps=9, shift=3, api_name="/generate"))
    if r: shutil.copy(yol(r), k); p("kare", i, "tamam")

v = Client("zerogpu-aoti/wan2-2-fp8da-aoti-faster", token=T)
for i, (_, har, sn) in enumerate(SAHNELER, 1):
    k, o = C / f"kare{i}.png", C / f"sahne{i}.mp4"
    if o.exists() or not k.exists(): continue
    r = dene(f"sahne{i}", lambda: v.predict(input_image=handle_file(str(k)), prompt=har, duration_seconds=sn, steps=6,
        api_name="/generate_video"))
    if r: shutil.copy(yol(r), o); p("sahne", i, "tamam")

try:
    t = Client("ResembleAI/Chatterbox-Multilingual-TTS", token=T)
    api = t.view_api(return_format="dict")["named_endpoints"]
    p(json.dumps({k: [x.get("parameter_name") for x in val["parameters"]] for k, val in api.items()}, ensure_ascii=False))
    ad = next(k for k in api if "generate" in k or "tts" in k)
    for tohum in (11, 22):
        o = C / f"ses{tohum}.wav"
        if o.exists(): continue
        r = dene("ses", lambda: t.predict(text_input=SES, language_id="tr", audio_prompt_path_input=None, exaggeration_input=0.6,
            temperature_input=0.7, seed_num_input=tohum, cfgw_input=0.4, api_name=ad))
        if r: shutil.copy(yol(r), o); p("ses tamam", tohum)
except Exception:
    p(traceback.format_exc()[-800:])
