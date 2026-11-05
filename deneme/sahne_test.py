"""Tek sahne denemesi: FLUX ile kare, Wan 2.2 ile 5 saniyelik hareket."""
import shutil
from pathlib import Path
from gradio_client import Client, handle_file

CIKTI = Path("deneme/cikti")
CIKTI.mkdir(parents=True, exist_ok=True)

GORSEL = (
    "Cinematic film still, vertical frame. Smoky 1980s Istanbul backroom gambling den, "
    "two tense men at a green card table in foreground, seen from behind. In the open "
    "doorway, a broad silhouetted elderly man in a long black wool overcoat and flat cap, "
    "face hidden in shadow, hard tungsten backlight, volumetric smoke, 35mm anamorphic "
    "lens, Kodak Vision3 grain, moody crime drama"
)
HAREKET = (
    "The silhouetted man in the doorway walks slowly forward into the room, the two men "
    "at the table freeze, smoke drifts, slow cinematic push-in"
)

g = Client("mcp-tools/FLUX.1-Krea-dev")
print(g.view_api(return_format="dict")["named_endpoints"].keys())
sonuc = g.predict(
    prompt=GORSEL, seed=3412, randomize_seed=False, width=720, height=1280,
    guidance_scale=4.5, num_inference_steps=28, api_name="/infer",
)
print("gorsel:", sonuc)
yol = sonuc[0] if isinstance(sonuc, (list, tuple)) else sonuc
yol = yol["path"] if isinstance(yol, dict) else yol
kare = CIKTI / "kare.png"
shutil.copy(yol, kare)

v = Client("zerogpu-aoti/wan2-2-fp8da-aoti-faster")
print(v.view_api(return_format="dict")["named_endpoints"].keys())
sonuc = v.predict(
    input_image=handle_file(str(kare)), prompt=HAREKET, duration_seconds=5, steps=6,
    api_name="/generate_video",
)
print("video:", sonuc)
yol = sonuc[0] if isinstance(sonuc, (list, tuple)) else sonuc
if isinstance(yol, dict):
    yol = yol.get("video") or yol.get("path")
shutil.copy(yol, CIKTI / "sahne.mp4")
