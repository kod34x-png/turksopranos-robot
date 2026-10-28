"""Günün Reel videosunu ve alıntı kartını üretir.
Kullanım: python robot/uret.py <gün_json_dosyası> <çıktı_klasörü>
"""
import json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BURASI = os.path.dirname(os.path.abspath(__file__))
SANS = os.path.join(BURASI, "DejaVuSans-Bold.ttf")
SERIF = os.path.join(BURASI, "DejaVuSerif-Bold.ttf")
GOLD = (212, 168, 76)
WHITE = (240, 236, 228)
HANDLE = "@turksopranos"

gun = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ arka plan
def arka_plan(W, H, seed=7):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(seed)
    def f(t):
        cx = W * (0.5 + 0.18 * math.sin(t * 0.25))
        cy = H * (0.42 + 0.08 * math.cos(t * 0.2))
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (H * 0.75)
        g = np.clip(1 - d, 0, 1) ** 2.2
        base = np.stack([12 + 38 * g, 10 + 26 * g, 8 + 14 * g], -1)
        vign = np.clip(1 - (np.sqrt((xx - W/2)**2 + (yy - H/2)**2) / (H * 0.7)) ** 2 * 0.55, 0.3, 1)
        return base * vign[..., None]
    noise = [rng.normal(0, 4, (H, W, 1)).astype(np.float32) for _ in range(6)]
    return f, noise

def yazi_katmani(W, H, metin, vurgu, boyut, font=SANS, y_merkez=None):
    fnt = ImageFont.truetype(font, boyut)
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    satirlar = metin.split("\n")
    lh = int(boyut * 1.22)
    y = (H - lh * len(satirlar)) // 2 if y_merkez is None else int(y_merkez - lh * len(satirlar) / 2)
    hv = vurgu.strip(".?!,…")
    for s in satirlar:
        kel = s.split(" ")
        gen = [d.textlength(k, font=fnt) for k in kel]
        bos = d.textlength(" ", font=fnt)
        x = (W - (sum(gen) + bos * (len(kel) - 1))) / 2
        for k, g in zip(kel, gen):
            renk = GOLD if k.strip(".?!,…") == hv else WHITE
            d.text((x, y), k, font=fnt, fill=renk + (255,))
            x += g + bos
        y += lh
    golge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    golge.putalpha(L.filter(ImageFilter.GaussianBlur(14)).split()[3].point(lambda a: int(a * 0.8)))
    return Image.alpha_composite(golge, L)

def boyut_sec(metin, W):
    en_uzun = max(len(s) for s in metin.split("\n"))
    return 118 if en_uzun <= 12 else 100 if en_uzun <= 16 else 86 if en_uzun <= 20 else 74

# ------------------------------------------------------------------ sert müzik
def muzik(sure, satir_baslari, yol, SR=44100):
    n = int(sure * SR); t = np.arange(n) / SR
    m = np.zeros(n)
    bpm = 72; vurus = 60 / bpm
    # karanlık drone (minör)
    for f, a in [(36.71, .10), (55.0, .07), (73.42, .05), (87.31, .04)]:
        m += a * np.sin(2*np.pi*f*t) * (0.7 + 0.3*np.sin(2*np.pi*0.1*t))
    rng = np.random.default_rng(3)
    def ekle(i0, sig):
        e = min(n, i0 + len(sig))
        if i0 < n: m[i0:e] += sig[:e - i0]
    davul_basla = 1.2
    k = 0
    while davul_basla + k * vurus / 2 < sure:
        zaman = davul_basla + k * vurus / 2
        i0 = int(zaman * SR)
        adim = k % 8
        if adim in (0, 3, 5):                     # 808 kick + uzun bas
            L = int(0.9 * SR); tt = np.arange(L) / SR
            f = 42 + 90 * np.exp(-tt * 30)
            sig = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-tt * 3.2) * 0.9
            ekle(i0, np.tanh(sig * 2.5) * 0.55)
        if adim in (2, 6):                        # clap/snare
            L = int(0.25 * SR); tt = np.arange(L) / SR
            nz = rng.normal(0, 1, L)
            nz = nz - np.convolve(nz, np.ones(8)/8, mode="same")
            ekle(i0, nz * np.exp(-tt * 18) * 0.35 + np.sin(2*np.pi*190*tt) * np.exp(-tt*25) * 0.2)
        L = int(0.04 * SR); tt = np.arange(L) / SR  # hi-hat
        hh = rng.normal(0, 1, L); hh = hh - np.convolve(hh, np.ones(3)/3, mode="same")
        ekle(i0, hh * np.exp(-tt * 90) * (0.12 if adim % 2 else 0.07))
        k += 1
    for s in satir_baslari:                         # satır geçişinde derin vuruş
        L = int(1.4 * SR); tt = np.arange(L) / SR
        ekle(int(s * SR), np.sin(2*np.pi*(40 + 50*np.exp(-tt*8))*tt) * np.exp(-tt*2.4) * 0.45)
    m *= np.clip(t / 0.4, 0, 1) * np.clip((sure - t) / 1.0, 0, 1)
    m = np.tanh(m * 1.6) * 0.85
    with wave.open(yol, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        st = np.repeat((m * 32767).astype(np.int16)[:, None], 2, axis=1)
        w.writeframes(st.tobytes())

# ------------------------------------------------------------------ reel
def reel():
    W, H, FPS = 1080, 1920, 30
    satirlar = gun["reel"]
    toplam = sum(s[2] for s in satirlar) + 0.8
    katmanlar, zamanlar, t0 = [], [], 0.3
    for metin, vurgu, sure in satirlar:
        katmanlar.append(yazi_katmani(W, H, metin, vurgu, boyut_sec(metin, W)))
        zamanlar.append((t0, sure)); t0 += sure
    bg, noise = arka_plan(W, H)
    hf = ImageFont.truetype(SANS, 38)
    seri = ImageFont.truetype(SANS, 34)
    wav = os.path.join(OUT, "muzik.wav")
    muzik(toplam, [s for s, _ in zamanlar], wav)
    mp4 = os.path.join(OUT, "reel.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
        "-vf", "hqdn3d=3:3:6:6", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    base_cache = {}
    for i in range(int(toplam * FPS)):
        t = i / FPS
        key = i // 3                                  # arka planı 3 karede bir hesapla
        if key not in base_cache:
            base_cache.clear(); base_cache[key] = bg(t)
        arr = np.clip(base_cache[key] + noise[i % 6], 0, 255).astype(np.uint8)
        im = Image.fromarray(arr).convert("RGBA")
        for L, (s, sure) in zip(katmanlar, zamanlar):
            if s <= t < s + sure:
                p_ = (t - s) / sure
                a = min(1, (t - s) / 0.3) * min(1, (s + sure - t) / 0.25)
                sc = 1.0 + 0.04 * p_
                Ls = L.resize((int(W * sc), int(H * sc)), Image.BILINEAR)
                ox, oy = (Ls.width - W) // 2, (Ls.height - H) // 2
                Ls = Ls.crop((ox, oy, ox + W, oy + H))
                Ls.putalpha(Ls.split()[3].point(lambda v: int(v * a)))
                im = Image.alpha_composite(im, Ls)
        d = ImageDraw.Draw(im)
        etiket = f"SOKAK DERSİ #{gun['no']}"
        d.text(((W - d.textlength(etiket, font=seri)) / 2, 230), etiket, font=seri, fill=GOLD + (200,))
        d.text(((W - d.textlength(HANDLE, font=hf)) / 2, H - 300), HANDLE, font=hf, fill=(200, 190, 170, 150))
        p.stdin.write(im.convert("RGB").tobytes())
    p.stdin.close(); p.wait()
    os.remove(wav)
    return mp4

# ------------------------------------------------------------------ kart
def kart():
    W, H = 1080, 1350
    bg, noise = arka_plan(W, H, seed=11)
    arr = np.clip(bg(0) + noise[0], 0, 255).astype(np.uint8)
    im = Image.fromarray(arr).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle((60, 60, W - 60, H - 60), outline=GOLD + (160,), width=3)
    tirnak = ImageFont.truetype(SERIF, 220)
    d.text(((W - d.textlength("“", font=tirnak)) / 2, 170), "“", font=tirnak, fill=GOLD + (230,))
    metin = gun["kart"]
    en_uzun = max(len(s) for s in metin.split("\n"))
    boyut = 92 if en_uzun <= 14 else 78 if en_uzun <= 20 else 64
    im = Image.alpha_composite(im, yazi_katmani(W, H, metin, gun["kart_vurgu"], boyut, SERIF, y_merkez=H * 0.52))
    d = ImageDraw.Draw(im)
    imza = ImageFont.truetype(SANS, 36)
    s = "— EMEKLİ KABADAYI"
    d.text(((W - d.textlength(s, font=imza)) / 2, H - 290), s, font=imza, fill=GOLD + (220,))
    h = ImageFont.truetype(SANS, 32)
    d.text(((W - d.textlength(HANDLE, font=h)) / 2, H - 200), HANDLE, font=h, fill=(200, 190, 170, 170))
    yol = os.path.join(OUT, "kart.jpg")
    im.convert("RGB").save(yol, quality=92)
    return yol

if __name__ == "__main__":
    print(kart())
    print(reel())
