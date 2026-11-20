"""FON / DİP tek seferlik video için görseller (FLUX Krea, ücretsiz ZeroGPU)."""
import shutil, sys, traceback, time
from pathlib import Path
from gradio_client import Client

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
FON = ("Cinematic film still, warm golden light, rich saturated colors, shallow depth of field, luxury, opulence, 35mm film grain. "
       "No text, no logos, no recognizable famous people. ")
DIP = ("Cinematic film still, cold blue-grey desaturated light, harsh winter, gritty realism, documentary feel, 35mm film grain, Turkey. "
       "No text, no logos, no children. ")
SAHNE = {
 "fon1": FON + "Night party on the deck of a huge private yacht on the Bosphorus in Istanbul, people in suits seen from behind raising champagne glasses, city lights.",
 "dip1": DIP + "An elderly Turkish pensioner man in a worn coat and flat cap waiting in a long queue of old people for cheap bread at a small municipal bread kiosk at dawn, breath visible in the cold.",
 "fon2": FON + "Close-up of hands opening a black leather briefcase filled with stacks of banknotes and gold bars on a polished mahogany desk.",
 "dip2": DIP + "An elderly Turkish woman in a headscarf bending down to pick up discarded tomatoes and vegetables from the wet ground at the end of an empty open-air street market, evening.",
 "fon3": FON + "A huge banquet table overflowing with lavish untouched food, whole roasted lamb, fruits, desserts, gold cutlery, crystal glasses, waiters scraping full plates into a trash bin.",
 "dip3": DIP + "A tired young university student in a hoodie studying with a laptop and textbooks on a bench in a cold park at night under a single street lamp, backpack beside him.",
 "fon4": FON + "A row of black luxury cars with tinted windows parked in front of a palatial marble mansion with fountains at dusk.",
 "dip4": DIP + "An old retired Turkish man sitting alone at a small kitchen table holding an electricity bill, an empty plate and a glass of tea, single bare bulb, peeling wall.",
 "son":  ("Cinematic film still, dark moody low-key lighting, heavy shadows, 35mm film grain. An old Turkish street boss, a retired kabadayi in his late sixties, "
          "grey mustache, black fedora hat and long dark coat, standing in a dark Istanbul back street at night, looking straight into the camera with a tired stern gaze. No text."),
}
import os
k = Client("mcp-tools/FLUX.1-Krea-dev", token=os.environ.get("HF_TOKEN") or None)
for ad, istem in SAHNE.items():
    if (OUT / f"{ad}.png").exists(): continue
    for deneme in range(2):
        try:
            r = k.predict(prompt=istem, seed=77 + deneme, randomize_seed=False, width=768, height=1344,
                          guidance_scale=4.5, num_inference_steps=28, api_name="/infer")
            while isinstance(r, (list, tuple)): r = r[0]
            if isinstance(r, dict): r = r.get("path") or r.get("url")
            shutil.copy(r, OUT / f"{ad}.png"); print(ad, "tamam", flush=True); break
        except Exception:
            print(ad, "HATA", traceback.format_exc()[-400:], flush=True); time.sleep(20)
