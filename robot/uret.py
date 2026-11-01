"""Günün Reel videosunu, Reel kapağını ve (kapalı) alıntı kartını üretir.
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

# ------------------------------------------------------------------ müzik (her gün farklı)
# Tamamen kendi sentezimiz (telif yok). Tarih+numara tohumlu: aynı gün hep aynı müzik,
# her gün farklı stil / tempo / ton / akor dizisi / davul deseni.
STILLER = ["trap", "orkestral", "boombap", "gerilim"]
TEMPO = {"trap": (68, 80), "orkestral": (70, 84), "boombap": (80, 90), "gerilim": (72, 88)}
DIZILER = [[0, 8, 3, 10], [0, 5, 8, 7], [0, 10, 8, 7], [0, 3, 8, 7], [0, 8, 5, 7], [0, 1, 0, 8]]

def _lowpass(x, fc, SR):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / fc) ** 4), len(x))

def _highpass(x, fc, SR):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    r = (f / fc) ** 2; return np.fft.irfft(X * r / np.sqrt(1 + r ** 2), len(x))

def muzik_secimi(tarih, no):
    tohum = int(tarih.replace("-", "")) * 100 + int(no)
    rng = np.random.default_rng(tohum)
    stil = STILLER[int(no) % len(STILLER)]          # ardışık günler hep farklı stil
    if os.environ.get("MUZIK_STIL"):
        stil = os.environ["MUZIK_STIL"]
    lo, hi = TEMPO[stil]
    return {"stil": stil, "bpm": int(rng.integers(lo, hi + 1)), "kok": int(rng.integers(0, 12)),
            "dizi": DIZILER[int(rng.integers(len(DIZILER)))], "rng": rng}

def muzik(sure, satir_baslari, yol, secim, SR=44100):
    n = int(sure * SR); t = np.arange(n) / SR
    rng, stil, bpm = secim["rng"], secim["stil"], secim["bpm"]
    vurus = 60 / bpm; olcu = 4 * vurus
    kok = 36.71 * 2 ** (secim["kok"] / 12)            # D1 .. C#2 arası bas kökü
    hz = lambda yarim: kok * 2 ** (yarim / 12)
    m = np.zeros(n); pad = np.zeros(n)
    def ekle(hedef, i0, sig):
        if i0 < 0: sig = sig[-i0:]; i0 = 0
        e = min(n, i0 + len(sig))
        if i0 < n: hedef[i0:e] += sig[:e - i0]
    def zarf(L, atak, birak):
        tt = np.arange(L) / SR
        return np.clip(tt / max(atak, 1e-3), 0, 1) * np.exp(-tt * birak)
    def kick(guc=0.9, uzun=0.9, kayma=None):
        L = int(uzun * SR); tt = np.arange(L) / SR
        f = (kayma or 45) + 95 * np.exp(-tt * 32)
        return np.tanh(np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-tt * 3.0) * 2.4) * 0.55 * guc
    def snare(guc=0.35, parlak=True):
        L = int(0.28 * SR); tt = np.arange(L) / SR
        nz = rng.normal(0, 1, L)
        if parlak: nz = nz - np.convolve(nz, np.ones(8)/8, mode="same")
        return nz * np.exp(-tt * 16) * guc + np.sin(2*np.pi*185*tt) * np.exp(-tt*22) * 0.22
    def hat(guc=0.1):
        L = int(0.045 * SR); tt = np.arange(L) / SR
        h = rng.normal(0, 1, L); h = h - np.convolve(h, np.ones(3)/3, mode="same")
        return h * np.exp(-tt * 95) * guc
    def akor_tonlari(derece):
        minor = derece in (0, 5)                      # i ve iv minör, diğerleri majör
        return [derece, derece + (3 if minor else 4), derece + 7]
    dizi = secim["dizi"]
    akor_suresi = olcu if stil != "boombap" else olcu / 2 * 2
    # --- armoni katmanı (stile göre tını)
    k = 0
    while k * akor_suresi < sure:
        i0 = int(k * akor_suresi * SR); L = int(akor_suresi * SR) + int(0.3 * SR)
        tt = np.arange(L) / SR; der = dizi[k % len(dizi)]
        tonlar = akor_tonlari(der)
        if stil == "orkestral":                      # yaylılar: dedüne testere, yavaş atak
            s = sum(sum(np.sign(np.sin(2*np.pi*hz(y + 24)*(1 + d)*tt)) * 0.5 + np.sin(2*np.pi*hz(y+24)*(1+d)*tt)
                    for d in (-0.004, 0, 0.005)) for y in tonlar)
            ekle(pad, i0, s * np.clip(tt / 0.6, 0, 1) * np.clip((L/SR - tt) / 0.4, 0, 1) * 0.035)
        elif stil == "boombap":                      # piyano benzeri akor vuruşu
            for vur in (0, 1.5, 2.5) if k % 2 == 0 else (0, 2):
                j = i0 + int(vur * vurus * SR); LL = int(1.4 * SR); t2 = np.arange(LL) / SR
                s = sum(sum(np.sin(2*np.pi*hz(y+36)*h*t2) / h**1.6 for h in (1, 2, 3, 4)) for y in tonlar)
                ekle(pad, j, s * np.exp(-t2 * 3.2) * 0.06)
        elif stil == "gerilim":                      # braam: alçak testere, akor değişiminde
            s = sum(np.sign(np.sin(2*np.pi*hz(y + 12)*tt)) + np.sin(2*np.pi*hz(y+12)*1.003*tt) for y in tonlar[:2])
            ekle(pad, i0, s * zarf(L, 0.05, 1.1) * 0.06)
        else:                                        # trap: karanlık sinüs pad + tek nota melodi
            s = sum(np.sin(2*np.pi*hz(y + 24)*tt) + 0.3*np.sin(2*np.pi*hz(y+36)*tt) for y in tonlar)
            ekle(pad, i0, s * np.clip(tt / 0.3, 0, 1) * np.clip((L/SR - tt) / 0.3, 0, 1) * 0.04)
            for j, y in enumerate(rng.choice([tonlar[0]+36, tonlar[1]+36, tonlar[2]+36, tonlar[0]+48], 3)):
                LL = int(0.5 * SR); t2 = np.arange(LL) / SR
                ekle(pad, i0 + int((j * 1.5 + rng.integers(0, 2)) * vurus * SR),
                     (np.sin(2*np.pi*hz(y)*t2) + 0.4*np.sin(4*np.pi*hz(y)*t2)) * np.exp(-t2 * 5) * 0.05)
        k += 1
    pad = _lowpass(pad, {"orkestral": 2200, "boombap": 2600, "gerilim": 900, "trap": 1800}[stil], SR)
    m += pad
    # --- davul / ritim (her gün farklı desen)
    adim_s = vurus / 4; adim_say = int(sure / adim_s) + 1
    desen_kick = sorted(set([0] + list(rng.choice(range(1, 16), int(rng.integers(2, 4)), replace=False))))
    salinim = 0.0 if stil != "boombap" else adim_s * float(rng.uniform(0.12, 0.22))
    for a in range(adim_say):
        zaman = a * adim_s + (salinim if a % 2 else 0)
        i0 = int(zaman * SR); p = a % 16; der = dizi[int(zaman // akor_suresi) % len(dizi)]
        if stil == "trap":
            if p in desen_kick:
                ekle(m, i0, kick(0.95, 1.1, kayma=hz(der) * 1.0))
            if p in (8,): ekle(m, i0, snare(0.33))
            if p % 2 == 0 or rng.random() < 0.18:    # hi-hat + ara ara rulolar
                ekle(m, i0, hat(0.09 if p % 4 else 0.13))
                if rng.random() < 0.12:
                    for r in range(1, 3): ekle(m, i0 + int(r * adim_s / 3 * SR), hat(0.07))
        elif stil == "boombap":
            if p in (0, 10) or (p in desen_kick and p not in (4, 12)): ekle(m, i0, kick(0.8, 0.5, 55))
            if p in (4, 12): ekle(m, i0, snare(0.42, parlak=False))
            if p % 2 == 0: ekle(m, i0, hat(0.08 if p % 4 else 0.11))
            if p in (0, 6) :                          # bas
                LL = int(adim_s * 5 * SR); t2 = np.arange(LL) / SR
                ekle(m, i0, np.sin(2*np.pi*hz(der+12)*t2) * zarf(LL, 0.01, 2.5) * 0.28)
        elif stil == "orkestral":
            if p in (0, 8) or (p in desen_kick and rng.random() < 0.5):  # taiko
                LL = int(0.8 * SR); t2 = np.arange(LL) / SR
                ekle(m, i0, (np.sin(2*np.pi*(60 + 60*np.exp(-t2*20))*t2) + rng.normal(0, .25, LL)*np.exp(-t2*30))
                     * np.exp(-t2 * 5) * 0.5)
            if p % 2 == 0:                            # alçak yaylı ostinato (8'lik)
                LL = int(adim_s * 1.8 * SR); t2 = np.arange(LL) / SR
                f = hz(der + 12)
                s = sum(np.sign(np.sin(2*np.pi*f*h*t2)) / h for h in (1, 2))
                ekle(m, i0, s * zarf(LL, 0.01, 9) * 0.07)
        else:  # gerilim
            LL = int(adim_s * 0.9 * SR); t2 = np.arange(LL) / SR   # 16'lık nabız synth
            ekle(m, i0, np.sign(np.sin(2*np.pi*hz(der+12)*t2)) * zarf(LL, 0.005, 14) * (0.09 if p % 4 == 0 else 0.05))
            if p in desen_kick or p == 0: ekle(m, i0, kick(0.75, 0.7, 40))
            if p % 4 == 2: ekle(m, i0, hat(0.06))            # saat tıkırtısı
    # --- satır geçişlerinde vuruş (ilk satırda 0. saniyede sert giriş)
    for s in satir_baslari:
        L = int(1.4 * SR); tt = np.arange(L) / SR
        ekle(m, int(s * SR), np.sin(2*np.pi*(38 + 52*np.exp(-tt*8))*tt) * np.exp(-tt*2.4) * 0.45)
    if stil in ("gerilim", "orkestral"):            # satır öncesi yükselen gerilim (riser)
        for s in satir_baslari[1:]:
            L = int(0.7 * SR); tt = np.arange(L) / SR
            nz = _highpass(rng.normal(0, 1, L), 3000, SR)
            ekle(m, int((s - 0.7) * SR), nz * (tt / tt[-1]) ** 2 * 0.06)
    m *= np.clip(t / 0.02, 0, 1) * np.clip((sure - t) / 1.0, 0, 1)   # 0. saniyede tam ses
    m = np.tanh(m * 1.6); m = m / (np.abs(m).max() + 1e-9) * 0.85
    # hafif stereo genişlik
    gec = int(0.012 * SR); sag = np.concatenate([np.zeros(gec), pad[:-gec]]) * 0.25
    sol_k, sag_k = m, np.clip(m - pad * 0.25 + sag, -1, 1)
    with wave.open(yol, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        st = np.stack([(sol_k * 32767).astype(np.int16), (sag_k * 32767).astype(np.int16)], 1)
        w.writeframes(st.tobytes())

# ------------------------------------------------------------------ kapak (profil ızgarası için)
def kapak():
    """1080x1920 kapak. Yazı, profil ızgarasının kırptığı orta 1080x1350 alanda kalır."""
    W, H = 1080, 1920
    bg, noise = arka_plan(W, H, seed=5)
    im = Image.fromarray(np.clip(bg(0) + noise[0], 0, 255).astype(np.uint8)).convert("RGBA")
    ust, alt = (H - 1350) // 2, (H + 1350) // 2           # 285 .. 1635
    d = ImageDraw.Draw(im)
    d.rectangle((70, ust + 70, W - 70, alt - 70), outline=GOLD + (170,), width=4)
    etiket_f = ImageFont.truetype(SANS, 64)
    etiket = f"SOKAK DERSİ #{gun['no']}"
    d.text(((W - d.textlength(etiket, font=etiket_f)) / 2, ust + 150), etiket, font=etiket_f, fill=GOLD + (255,))
    d.line((W/2 - 120, ust + 250, W/2 + 120, ust + 250), fill=GOLD + (200,), width=3)
    metin, vurgu, _ = gun["reel"][0]
    en_uzun = max(len(s) for s in metin.split("\n"))
    boyut = 132 if en_uzun <= 12 else 112 if en_uzun <= 15 else 96 if en_uzun <= 18 else 82
    im = Image.alpha_composite(im, yazi_katmani(W, H, metin, vurgu, boyut, y_merkez=H * 0.52))
    d = ImageDraw.Draw(im)
    hf = ImageFont.truetype(SANS, 40)
    d.text(((W - d.textlength(HANDLE, font=hf)) / 2, alt - 190), HANDLE, font=hf, fill=(220, 210, 190, 210))
    yol = os.path.join(OUT, "kapak.jpg")
    im.convert("RGB").save(yol, quality=92)
    return yol

# ------------------------------------------------------------------ reel
def reel():
    W, H, FPS = 1080, 1920, 30
    satirlar = [list(s) for s in gun["reel"]]
    satirlar[-1][2] += 1.2                      # son soru ekranda daha uzun kalsın (yorum için)
    katmanlar, zamanlar, t0 = [], [], 0.0
    for metin, vurgu, sure in satirlar:
        katmanlar.append(yazi_katmani(W, H, metin, vurgu, boyut_sec(metin, W)))
        zamanlar.append((t0, sure)); t0 += sure
    # kapanış: takip çağrısı
    cta = Image.alpha_composite(
        yazi_katmani(W, H, f"Yarın\nSokak Dersi #{gun['no'] + 1}", "Yarın", 104, y_merkez=H * 0.45),
        yazi_katmani(W, H, "Takip et, kaçırma.", "Takip", 72, y_merkez=H * 0.60))
    katmanlar.append(cta); zamanlar.append((t0, 2.8)); t0 += 2.8
    toplam = t0 + 0.5
    bg, noise = arka_plan(W, H)
    hf = ImageFont.truetype(SANS, 38)
    seri = ImageFont.truetype(SANS, 34)
    wav = os.path.join(OUT, "muzik.wav")
    secim = muzik_secimi(gun["tarih"], gun["no"]); print("Müzik:", secim["stil"], secim["bpm"], "BPM")
    muzik(toplam, [s for s, _ in zamanlar], wav, secim)
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
                a = (1 if s == 0 else min(1, (t - s) / 0.3)) * min(1, (s + sure - t) / 0.25)
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
    print(kapak())
    print(reel())
