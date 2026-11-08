"""Kabadayi Girseydi: siradaki onayli bolumu uretir. Biten parcalari atlar, kaldigi yerden devam eder.
Kullanim: python robot/kabadayi_uret.py            (uretim ve montaj)
          python robot/kabadayi_uret.py --montaj N  (yalniz N. bolumun montaji)
"""
import asyncio, json, os, re, shutil, subprocess, sys, textwrap
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

KOK = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
YAZI_FONT = str(KOK / "robot/DejaVuSerif-Bold.ttf")
STIL = ("Photorealistic cinematic film still, 1980s Istanbul, tungsten light, drifting smoke, 35mm film grain, "
        "muted colors, crime drama, no text, no letters, no candles. ")
SES_ADI = "tr-TR-AhmetNeural"

def kaydet(m):
    print(m, flush=True)
    with open(KOK / "medya/kabadayi/uretim.log", "a", encoding="utf-8") as f:
        f.write(m + "\n")

def bolumler():
    return json.load(open(KOK / "icerik/kabadayi.json", encoding="utf-8"))

def yayinlanan():
    y = KOK / "durum/kabadayi.json"
    return json.load(open(y, encoding="utf-8")) if y.exists() else []

def sure(yol):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(yol)]).decode())

def tek_yol(s):
    while isinstance(s, (list, tuple)):
        s = s[0]
    if isinstance(s, dict):
        s = s.get("video") or s.get("image") or s.get("path")
    if isinstance(s, dict):
        s = s.get("path")
    return s

def uret(b, klasor):
    from gradio_client import Client, handle_file
    T = os.environ.get("HF_TOKEN") or None
    klasor.mkdir(parents=True, exist_ok=True)
    ses = klasor / "ses.mp3"
    if not ses.exists():
        import edge_tts
        asyncio.run(edge_tts.Communicate(b["ses"], SES_ADI, rate="-18%", pitch="-12Hz").save(str(ses)))
    g = Client("mcp-tools/Z-Image-Turbo", token=T)
    for i, s in enumerate(b["sahneler"], 1):
        k = klasor / f"kare{i}.png"
        if k.exists() or (klasor / f"sahne{i}.mp4").exists():
            continue
        try:
            r = g.predict(prompt=b.get("stil", STIL) + s["gorsel"], resolution="864x1536 ( 9:16 )", seed=b["no"] * 100 + i,
                          random_seed=False, steps=9, shift=3, api_name="/generate")
            shutil.copy(tek_yol(r), k); print("kare", i, flush=True)
        except Exception as e:
            kaydet("kare durdu: " + repr(e)[:300]); return
    v = Client("zerogpu-aoti/wan2-2-fp8da-aoti-faster", token=T)
    for i, s in enumerate(b["sahneler"], 1):
        o = klasor / f"sahne{i}.mp4"
        if o.exists():
            continue
        try:
            r = v.predict(input_image=handle_file(str(klasor / f"kare{i}.png")), prompt=s["hareket"],
                          duration_seconds=s.get("sure", 4), steps=6, api_name="/generate_video")
            shutil.copy(tek_yol(r), o); print("sahne", i, flush=True)
        except Exception as e:
            kaydet("video durdu: " + repr(e)[:300]); return

KREM, ALTIN = (245, 235, 215, 255), (222, 178, 84, 255)
HANDLE = "@turksopranos"
ANLATI_Y, KONUSMA_Y = 300, 1250        # anlatı yazısı üstte (altın), konuşma altyazısı ortanın altında (krem)

def yazi_katmani(metin, boyut, y, yol, renk=KREM, kontur=7):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(YAZI_FONT, boyut)
    for s in textwrap.wrap(metin, width=int(1600 / boyut)):
        d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=renk,
               stroke_width=kontur, stroke_fill=(0, 0, 0, 235))
        y += int(boyut * 1.3)
    im.save(yol); return yol

def konusmalar(ses, cumleler):
    """Cumleleri sesteki sessizliklere oturtur; sayi tutmazsa harf sayisina gore boler."""
    c = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(ses), "-af", "silencedetect=n=-35dB:d=0.25", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    bas = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", c)]
    son = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", c)]
    T = sure(ses)
    p = [(son[i], bas[i + 1] if i + 1 < len(bas) else T) for i in range(len(son))]
    p = [x for x in p if x[1] - x[0] > 0.1]
    if len(p) == len(cumleler):
        return p
    top = sum(map(len, cumleler)); t = 0.3; r = []
    for m in cumleler:
        e = (T - 0.6) * len(m) / top; r.append((t, t + e)); t += e
    return r

def montaj(b, klasor, cikti, kapak, gecici):
    gecici.mkdir(parents=True, exist_ok=True)
    kod = open(KOK / "robot/uret.py", encoding="utf-8").read()
    a = kod.index("# ------------------------------------------------------------------ müzik")
    z = kod.index("# ------------------------------------------------------------------ reel")
    ns = {"np": np, "os": os}; exec("import wave, struct, subprocess", ns); exec(kod[a:z], ns)
    os.environ["MUZIK_STIL"] = "gerilim"
    sahneler = [klasor / f"sahne{i}.mp4" for i in range(1, len(b["sahneler"]) + 1)]
    sureler = [sure(s) for s in sahneler]
    baslar = [sum(sureler[:i]) for i in range(len(sureler))]
    ses = klasor / "ses.mp3"
    cumleler = [x.strip() for x in re.findall(r"[^.!?]+[.!?]", b["ses"])]
    parca = konusmalar(ses, cumleler)
    gecik = max(0.0, baslar[b["ses_sahne"] - 1] - parca[0][0] + 0.2)
    ses_son = gecik + sure(ses)
    govde = sum(sureler); uzat = max(0.0, ses_son - govde + 0.3)
    KART = 2.5; govde += uzat; TOPLAM = round(govde + KART, 2)
    ns["muzik"](TOPLAM, [*baslar], str(gecici / "muzik.wav"), ns["muzik_secimi"]("2026-11-07", b["no"]))
    gir = []; fc = ""
    for i, s in enumerate(sahneler):
        gir += ["-i", str(s)]
        ek = f",tpad=stop_mode=clone:stop_duration={uzat + KART:.2f}" if i == len(sahneler) - 1 else ""
        fc += (f"[{i}:v]scale=-2:{H}:flags=lanczos,crop={W}:{H},unsharp=5:5:0.7,"
               f"minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1{ek},setsar=1[s{i}];")
    n = len(sahneler)
    fc += "".join(f"[s{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,format=yuv420p[t0];"
    son = "t0"; yazilar = []
    for i, s in enumerate(b["sahneler"]):
        if s.get("yazi"):
            yazilar.append((s["yazi"], baslar[i] + (0.0 if i == 0 else 0.2), baslar[i] + sureler[i] - 0.2, "anlati"))
    for j, (m, (p0, p1)) in enumerate(zip(cumleler, parca)):
        bitis = (parca[j + 1][0] + gecik - 0.1) if j + 1 < len(parca) else min(govde - 0.1, p1 + gecik + 1.2)
        yazilar.append((m, max(0.0, p0 + gecik - 0.1), bitis, "konusma"))
    for j, (m, x0, x1, tur) in enumerate(yazilar):
        if tur == "anlati":
            k = yazi_katmani(m, 62 if len(m) > 24 else 74, ANLATI_Y, str(gecici / f"y{j}.png"), ALTIN, 6)
        else:
            k = yazi_katmani(m, 70 if len(m) > 20 else 92, KONUSMA_Y, str(gecici / f"y{j}.png"))
        gir += ["-i", k]
        fc += f"[{son}][{n}:v]overlay=enable='between(t,{x0:.2f},{x1:.2f})'[u{j}];"; son = f"u{j}"; n += 1
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)   # köşede kimlik
    hf = ImageFont.truetype(YAZI_FONT, 34)
    d.text((W - 60 - d.textlength(HANDLE, font=hf), 170), HANDLE, font=hf, fill=(245, 235, 215, 190),
           stroke_width=3, stroke_fill=(0, 0, 0, 160))
    im.save(gecici / "imza.png"); gir += ["-i", str(gecici / "imza.png")]
    fc += f"[{son}][{n}:v]overlay=enable='lt(t,{govde:.2f})'[im];"; son = "im"; n += 1
    Image.new("RGBA", (W, H), (0, 0, 0, 175)).save(gecici / "karart.png")  # kapanış: son sahne kararır
    gir += ["-i", str(gecici / "karart.png")]
    fc += f"[{son}][{n}:v]overlay=enable='gte(t,{govde:.2f})'[ka0];"; son = "ka0"; n += 1
    gir += ["-i", yazi_katmani("KABADAYI GİRSEYDİ", 84, 760, str(gecici / "k1.png"), ALTIN)]
    fc += f"[{son}][{n}:v]overlay=enable='gte(t,{govde + .1:.2f})'[k0];"; n += 1
    gir += ["-i", yazi_katmani("Her Cumartesi · " + HANDLE, 54, 890, str(gecici / "k1b.png"))]
    fc += f"[k0][{n}:v]overlay=enable='gte(t,{govde + .1:.2f})'[k1];"; n += 1
    gir += ["-i", yazi_katmani("Takip et. Kapı yine açılacak.", 50, 990, str(gecici / "k2.png"))]
    fc += f"[k1][{n}:v]overlay=enable='gte(t,{govde + .1:.2f})'[k2];"; n += 1
    if b.get("not"):
        gir += ["-i", yazi_katmani(b["not"], 36, 1120, str(gecici / "k3.png"))]
        fc += f"[k2][{n}:v]overlay=enable='gte(t,{govde + .1:.2f})'[v];"; n += 1
    else:
        fc += "[k2]null[v];"
    gir += ["-i", str(ses)]; sv = n; n += 1
    gir += ["-i", str(gecici / "muzik.wav")]; mz = n; n += 1
    ms = int(gecik * 1000)
    fc += (f"[{sv}:a]aresample=44100,asetrate=44100*0.91,aresample=44100,atempo=1.0989,lowpass=f=6500,highpass=f=70,"
           f"aformat=channel_layouts=stereo,aecho=0.8:0.5:45:0.18,acompressor=threshold=-18dB:ratio=3,volume=1.6,"
           f"adelay={ms}|{ms},apad,asplit=2[se][ka];[{mz}:a]aresample=44100,aformat=channel_layouts=stereo,volume=0.32[mu];"
           f"[mu][ka]sidechaincompress=threshold=0.02:ratio=10:attack=5:release=350[md];"
           f"[md][se]amix=inputs=2:duration=first:normalize=0,afade=t=out:st={TOPLAM - 1:.2f}:d=1,alimiter=limit=0.95[a]")
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + gir + ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-t", str(TOPLAM), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(cikti)], check=True)
    ky = gecici / "kapak.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1.5", "-i", str(sahneler[1]), "-frames:v", "1",
                    "-vf", f"scale=-2:{H}:flags=lanczos,crop={W}:{H}", str(ky)], check=True)
    im = Image.open(ky).convert("RGBA")
    im = Image.alpha_composite(im, Image.open(yazi_katmani(f"KABADAYI GİRSEYDİ #{b['no']}", 84, 1300, str(gecici / "kk.png"))))
    im = Image.alpha_composite(im, Image.open(yazi_katmani(HANDLE, 46, 1530, str(gecici / "kh.png"), ALTIN, 5)))
    im.convert("RGB").save(kapak, quality=92)
    print("montaj tamam", cikti, TOPLAM, flush=True)

def calistir():
    tum = bolumler()
    if len(sys.argv) > 2 and sys.argv[1] == "--montaj":
        b = next(x for x in tum if x["no"] == int(sys.argv[2]))
    else:
        biten = {k["no"] for k in yayinlanan() if k.get("reel_id")}
        sira = sorted(tum, key=lambda x: (x["durum"] != "onayli", x["no"]))   # önce onaylı bölüm
        b = next((x for x in sira if x["durum"] in ("onayli", "uret") and x["no"] not in biten
                  and not (KOK / f"medya/kabadayi/{x['no']}.mp4").exists()), None)
        if not b:
            print("Uretilecek onayli bolum yok."); return
        uret(b, KOK / f"medya/kabadayi/{b['no']}")
    k = KOK / f"medya/kabadayi/{b['no']}"
    if all((k / f"sahne{i}.mp4").exists() for i in range(1, len(b["sahneler"]) + 1)) and (k / "ses.mp3").exists():
        montaj(b, k, KOK / f"medya/kabadayi/{b['no']}.mp4", KOK / f"medya/kabadayi/{b['no']}-kapak.jpg", Path("/tmp/kabadayi"))
    else:
        print("Bolum eksik; sonraki calismada devam edecek.")

if __name__ == "__main__":
    calistir()
