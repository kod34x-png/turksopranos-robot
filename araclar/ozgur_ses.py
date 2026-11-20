"""Özgür'ün ses klonu (XTTS v2 + referans/) ile satır satır anlatım üretir.
Her satır için birkaç aday üretir, Whisper ile metne en yakın olanı seçer, sondaki fazlalığı keser.
Kullanım: python ozgur_ses.py <referans_klasoru> <cikti_klasoru> "satır 1" "satır 2" ...
Çıktı: cikti_klasoru/s0.wav, s1.wav ... (24 kHz mono) + rapor.json"""
import os, sys, json, subprocess, difflib, re, numpy as np, torch, soundfile as sf, scipy.signal as ss
os.environ["COQUI_TOS_AGREED"] = "1"
import TTS.tts.models.xtts as X
def _load(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return torch.from_numpy(np.frombuffer(raw, dtype=np.float32).copy()).unsqueeze(0)
X.load_audio = _load
from TTS.api import TTS
from faster_whisper import WhisperModel

def norm(t):
    t = t.lower().replace("i̇", "i")
    return re.sub(r"[^a-zçğıöşü ]", "", re.sub(r"\s+", " ", t)).strip()

ref_dir, out_dir, satirlar = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(out_dir, exist_ok=True)
refs = sorted(os.path.join(ref_dir, f) for f in os.listdir(ref_dir) if f.endswith(".wav"))
m = TTS("tts_models/multilingual/multi-dataset/xtts_v2").synthesizer.tts_model
lat, spk = m.get_conditioning_latents(audio_path=refs)
asr = WhisperModel("small", device="cpu", compute_type="int8")
rapor = []
for i, satir in enumerate(satirlar):
    metin = re.sub(r"\s+", " ", satir.replace("\n", " ")).strip()
    if metin[-1] not in ".!?": metin += "."
    en_iyi = None
    for d, sic in enumerate((0.55, 0.65, 0.75, 0.6)):
        torch.manual_seed(1000 * i + d)
        w = np.array(m.inference(metin, "tr", lat, spk, temperature=sic, repetition_penalty=5.0, speed=0.92)["wav"], dtype=np.float32)
        a16 = ss.resample_poly(w, 16000, 24000).astype(np.float32)
        segs = list(asr.transcribe(a16, language="tr", word_timestamps=True)[0])
        kel = [k for s in segs for k in (s.words or [])]
        duyulan = " ".join(k.word for k in kel)
        # metnin son kelimesine kadar olan kısmı bul, gerisini kes
        hedef = norm(metin).split(); son_t = None; birikim = []
        for k in kel:
            birikim.append(norm(k.word))
            if difflib.SequenceMatcher(None, " ".join(birikim), " ".join(hedef)).ratio() >= 0.9:
                son_t = k.end
        oran = difflib.SequenceMatcher(None, norm(duyulan), norm(metin)).ratio()
        if son_t:
            kes = min(len(w), int((son_t + 0.18) * 24000))
            oran_kes = difflib.SequenceMatcher(None, norm(" ".join(birikim[:[j for j, k in enumerate(kel) if k.end <= son_t][-1] + 1])), norm(metin)).ratio()
            w2, o2 = w[:kes], max(oran, oran_kes)
        else:
            w2, o2 = w, oran
        if en_iyi is None or o2 > en_iyi[0]:
            en_iyi = (o2, w2, duyulan)
        if o2 >= 0.97:
            break
    o, w, duy = en_iyi
    f = np.linspace(1, 0, int(0.04 * 24000)); w[-len(f):] *= f
    sf.write(os.path.join(out_dir, f"s{i}.wav"), w, 24000)
    rapor.append({"satir": metin, "duyulan": duy.strip(), "benzerlik": round(o, 3)})
    print(i, round(o, 3), "|", metin, "|", duy.strip(), flush=True)
json.dump(rapor, open(os.path.join(out_dir, "rapor.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
