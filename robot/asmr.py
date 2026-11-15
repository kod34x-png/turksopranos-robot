"""ASMR katmanı: yağmur yatağı, zippo çakmak, ince belli çay bardağı, tespih, ayak sesi.
Tamamen sentez (telif yok). Yalnız numpy. 15 Kasım 2026 kararı: gün aşırı test (tek numaralı Reel'ler).
"""
import numpy as np

SR = 44100

def _bant(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))

def _zarf(n, atak, sonum):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(atak, 1e-4)) * np.exp(-t / sonum)

def _koy(buf, t, x, g):
    i = int(t * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(x)); buf[i:j] += g * x[:j - i]

def katman(sure, olaylar, tohum=7):
    """olaylar: [("cakmak", t), ("bardak", t), ("tespih", t), ("adim", t)] -> mono numpy dizisi"""
    rng = np.random.default_rng(tohum)
    n = int(sure * SR); out = np.zeros(n)
    yagmur = _bant(rng.standard_normal(n), 400, 5000) * 0.05
    for _ in range(int(sure * 35)):
        m = int(0.012 * SR)
        _koy(yagmur, rng.uniform(0, max(0.01, sure - 0.02)),
             _bant(rng.standard_normal(m), 2000, 8000) * _zarf(m, 0.0005, 0.003), rng.uniform(0.02, 0.08))
    out += yagmur * np.minimum(1, np.arange(n) / SR / 0.3)
    for tur, t in olaylar:
        if tur == "cakmak":
            m = int(.03 * SR); _koy(out, t, _bant(rng.standard_normal(m), 1500, 6000) * _zarf(m, .0005, .006), 0.9)
            m = int(.06 * SR); _koy(out, t + .12, _bant(rng.standard_normal(m), 2500, 9000) * _zarf(m, .001, .015), 0.7)
            m = int(.6 * SR); _koy(out, t + .14, _bant(rng.standard_normal(m), 40, 900) * _zarf(m, .05, .25), 0.6)
        elif tur == "bardak":
            m = int(.9 * SR); tt = np.arange(m) / SR
            x = sum(a * np.sin(2 * np.pi * fq * tt) * np.exp(-tt / dc)
                    for fq, a, dc in ((2960, 1, .35), (4410, .6, .22), (6120, .35, .15), (7850, .2, .1)))
            x *= np.minimum(1, tt / .0008); _koy(out, t, x, 0.12); _koy(out, t + .18, x * 0.6, 0.07)
        elif tur == "tespih":
            for k in range(4):
                m = int(.02 * SR)
                _koy(out, t + k * rng.uniform(.13, .2), _bant(rng.standard_normal(m), 1800, 5000) * _zarf(m, .0003, .004), 0.5)
        elif tur == "adim":
            for k in range(3):
                m = int(.12 * SR); _koy(out, t + k * .55, _bant(rng.standard_normal(m), 30, 400) * _zarf(m, .003, .03), 1.2)
    return out * 0.35
