"""Palestra di Voce - app Streamlit per imparare a cantare.

Avvio in locale:  streamlit run app.py
"""
import io
import json
import re
import wave

import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Palestra di Voce", page_icon="🎤", layout="wide")

SR = 22050          # frequenza di campionamento dell'audio di guida
LEAD = 4            # colpi di metronomo prima di iniziare
ACCENT = "#2B45D4"
GOOD = "#1C9764"
WARM = "#D9702A"

# --------------------------------------------------------------------------
# Note e notazione
# --------------------------------------------------------------------------
NAMES = ["Do", "Do♯", "Re", "Re♯", "Mi", "Fa", "Fa♯", "Sol", "Sol♯", "La", "La♯", "Si"]
PC = {"do": 0, "re": 2, "mi": 4, "fa": 5, "sol": 7, "la": 9, "si": 11,
      "c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
NOTE_RE = re.compile(r"^(do|re|mi|fa|sol|la|si|[a-g])([#♯b♭]?)(-?\d)?$", re.I)


def name_of(m: float) -> str:
    m = int(round(m))
    return f"{NAMES[m % 12]}{m // 12 - 1}"


def f2m(f: float) -> float:
    return 69 + 12 * np.log2(f / 440.0)


def m2f(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def parse_note(s: str):
    r = NOTE_RE.match(s)
    if not r:
        return None
    acc = 0
    if r.group(2):
        acc = 1 if r.group(2) in "#♯" else -1
    octave = int(r.group(3)) if r.group(3) is not None else 4
    return (octave + 1) * 12 + PC[r.group(1).lower()] + acc


def parse_melody(text: str):
    """Restituisce (note, n_frasi). Ogni nota: dict(midi, beat, dur, phrase)."""
    notes, beat = [], 0.0
    phrases = text.split("|")
    for i, ph in enumerate(phrases):
        for tok in ph.split():
            parts = tok.split(":")
            n = parts[0]
            try:
                dur = float(parts[1].replace(",", ".")) if len(parts) > 1 else 1.0
            except ValueError:
                dur = -1
            if dur <= 0:
                raise ValueError(f'Durata non valida in "{tok}"')
            if re.fullmatch(r"p|-|r|pausa", n, re.I):
                beat += dur
                continue
            midi = parse_note(n)
            if midi is None:
                raise ValueError(f'Nota non riconosciuta: "{n}"')
            notes.append({"midi": midi, "beat": beat, "dur": dur, "phrase": i})
            beat += dur
    if not notes:
        raise ValueError("Scrivi almeno una nota.")
    return notes, len(phrases)


# --------------------------------------------------------------------------
# Audio: sintesi della guida e lettura delle registrazioni
# --------------------------------------------------------------------------
def to_wav(y: np.ndarray, sr: int = SR) -> bytes:
    peak = np.max(np.abs(y)) or 1.0
    data = (y / peak * 0.8 * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())
    return buf.getvalue()


def tone_samples(midi: float, dur: float) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    f = m2f(midi)
    y = 0.7 * np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t) + 0.08 * np.sin(6 * np.pi * f * t)
    env = np.minimum(1, t / 0.025) * np.minimum(1, np.maximum(0, (dur - 0.04 - t)) / 0.06)
    env *= 0.75 + 0.25 * np.exp(-t / 0.2)
    return y * env


def render_plan(plan, guide=True, clicks=True) -> bytes:
    n = int((plan["total"] + 0.6) * SR)
    y = np.zeros(n)
    spb = 60 / plan["bpm"]
    if clicks:
        tc = np.arange(int(0.06 * SR)) / SR
        for i in range(LEAD):
            f = 1500 if i == 0 else 1000
            c = 0.5 * np.sin(2 * np.pi * f * tc) * np.exp(-tc / 0.012)
            s = int(i * spb * SR)
            y[s:s + len(c)] += c[: max(0, n - s)]
    if guide:
        for nt in plan["notes"]:
            s = int(nt["start"] * SR)
            tn = tone_samples(nt["midi"], nt["dur"])
            e = min(n, s + len(tn))
            y[s:e] += tn[: e - s]
    return to_wav(y)


def read_wav(data: bytes):
    with wave.open(io.BytesIO(data), "rb") as w:
        ch, width, sr, frames = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.readframes(w.getnframes())
    if width == 2:
        x = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768
    elif width == 4:
        x = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2 ** 31
    elif width == 1:
        x = (np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128) / 128
    else:
        raise ValueError("Formato audio non supportato")
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, sr


# --------------------------------------------------------------------------
# Riconoscimento dell'altezza (autocorrelazione via FFT)
# --------------------------------------------------------------------------
def detect(frame: np.ndarray, sr: int):
    x = frame - frame.mean()
    if np.sqrt(np.mean(x ** 2)) < 0.012:
        return None
    n = len(x)
    r = np.fft.irfft(np.abs(np.fft.rfft(x, 2 * n)) ** 2)[:n]
    max_lag = min(n - 2, int(sr / 65))
    rising = np.nonzero(np.diff(r[: max_lag + 1]) > 0)[0]
    if len(rising) == 0:
        return None
    d = rising[0]
    pos = d + int(np.argmax(r[d:max_lag]))
    if pos <= 0 or r[pos] < 0.35 * r[0]:
        return None
    x1, x2, x3 = r[pos - 1], r[pos], r[pos + 1]
    a, b = (x1 + x3 - 2 * x2) / 2, (x3 - x1) / 2
    T = pos - b / (2 * a) if a else pos
    f = sr / T
    return f if 65 < f < 1200 else None


def track(x: np.ndarray, sr: int, n=2048, hop=512):
    out = []
    for i in range(0, len(x) - n, hop):
        f = detect(x[i:i + n], sr)
        out.append((i / sr, f2m(f) if f else None))
    return out


def fold(v, t):
    """Differenza in semitoni ignorando l'ottava (-6..+6)."""
    return ((v - t) % 12 + 18) % 12 - 6


# --------------------------------------------------------------------------
# Punteggio e grafico
# --------------------------------------------------------------------------
def align(voice, plan):
    for i in range(len(voice) - 2):
        if voice[i][1] is not None and voice[i + 1][1] is not None and voice[i + 2][1] is not None:
            off = plan["notes"][0]["start"] - voice[i][0]
            return [(t + off, m) for t, m in voice]
    return None


def score(plan, voice):
    per = []
    for nt in plan["notes"]:
        a = nt["start"] + min(0.12, nt["dur"] * 0.25)
        b = nt["start"] + nt["dur"]
        fr = [m for t, m in voice if a <= t < b]
        voiced = [m for m in fr if m is not None]
        ok = sum(1 for m in voiced if abs(fold(m, nt["midi"])) < 0.5)
        avg = float(np.mean([fold(m, nt["midi"]) for m in voiced])) if voiced else None
        per.append({"note": nt, "pct": ok / len(fr) if fr else 0.0, "avg": avg})
    tot = sum(p["note"]["dur"] for p in per)
    overall = sum(p["pct"] * p["note"]["dur"] for p in per) / tot
    return per, overall


def lane_figure(plan, voice=None):
    notes = plan["notes"]
    lo = min(n["midi"] for n in notes) - 2
    hi = max(n["midi"] for n in notes) + 2
    if hi - lo < 12:
        pad = 12 - (hi - lo)
        lo -= pad // 2
        hi += pad - pad // 2
    fig = go.Figure()
    for n in notes:
        fig.add_trace(go.Scatter(
            x=[n["start"], n["start"] + n["dur"] * 0.96], y=[n["midi"], n["midi"]], mode="lines",
            line=dict(color=ACCENT, width=14), opacity=0.35, hoverinfo="text",
            text=name_of(n["midi"]), showlegend=False))
    if voice:
        xs, ys, cs = [], [], []
        for t, m in voice:
            if m is None:
                continue
            tg = next((n for n in notes if n["start"] <= t < n["start"] + n["dur"]), None)
            if tg:
                mm = tg["midi"] + fold(m, tg["midi"])
                ok = abs(mm - tg["midi"]) < 0.5
            else:
                mm = m
                while mm > hi + 1:
                    mm -= 12
                while mm < lo - 1:
                    mm += 12
                ok = False
            xs.append(t)
            ys.append(mm)
            cs.append(GOOD if ok else WARM)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", marker=dict(color=cs, size=5),
                                 name="La tua voce", hovertemplate="%{x:.2f}s<extra></extra>"))
    ticks = [m for m in range(int(lo), int(hi) + 1) if m % 12 in (0, 2, 4, 5, 7, 9, 11)]
    fig.update_yaxes(tickvals=ticks, ticktext=[name_of(m) for m in ticks], range=[lo - 0.5, hi + 0.5],
                     gridcolor="rgba(128,128,128,0.2)")
    fig.update_xaxes(title="secondi", range=[max(0, plan["lead"] - 0.5), plan["total"] + 0.3],
                     gridcolor="rgba(128,128,128,0.12)")
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
                      plot_bgcolor="rgba(0,0,0,0)")
    return fig


def show_results(plan, voice):
    per, overall = score(plan, voice)
    pct = round(overall * 100)
    flat = sum(1 for p in per if p["avg"] is not None and p["avg"] < -0.3)
    sharp = sum(1 for p in per if p["avg"] is not None and p["avg"] > 0.3)
    if pct >= 80:
        msg = "Ottima intonazione."
    elif pct >= 55:
        msg = "Buona base: lavora sulle note arancioni."
    else:
        msg = "Continua: riascolta la guida e abbassa il tempo."
    if flat > sharp + 1:
        msg += " Tendi a calare: sostieni il fiato fino alla fine della nota."
    elif sharp > flat + 1:
        msg += " Tendi a crescere: rilassa collo e mascella."
    c1, c2 = st.columns([1, 3])
    c1.metric("Tempo intonato", f"{pct}%")
    c2.write(msg)
    c2.caption("Vale anche cantare un'ottava sopra o sotto la guida.")
    st.plotly_chart(lane_figure(plan, voice), use_container_width=True)
    chips = " ".join(
        f":{'green' if p['pct'] >= .7 else 'orange' if p['pct'] >= .35 else 'red'}[{name_of(p['note']['midi'])} {round(p['pct'] * 100)}%]"
        for p in per[:80])
    st.markdown(chips)


def analyze_recording(rec, plan):
    try:
        x, sr = read_wav(rec.getvalue())
    except Exception:
        st.error("Non riesco a leggere la registrazione. Riprova a registrare.")
        return
    voice = align(track(x, sr), plan)
    if voice is None:
        st.warning("Non ho sentito una voce cantata. Avvicinati al microfono e riprova.")
        return
    show_results(plan, voice)


# --------------------------------------------------------------------------
# Stato iniziale
# --------------------------------------------------------------------------
EXAMPLES = [
    {"title": "Fra Martino", "artist": "Canto tradizionale", "bpm": 100,
     "melody": "do4 re4 mi4 do4 | do4 re4 mi4 do4 | mi4 fa4 sol4:2 | mi4 fa4 sol4:2 | sol4:0.5 la4:0.5 sol4:0.5 fa4:0.5 mi4 do4 | sol4:0.5 la4:0.5 sol4:0.5 fa4:0.5 mi4 do4 | do4 sol3 do4:2 | do4 sol3 do4:2",
     "lyrics": "Fra Martino\ncampanaro\ndormi tu?\ndormi tu?\nSuona le campane\nsuona le campane\ndin don dan\ndin don dan"},
    {"title": "Tanti auguri", "artist": "Canto tradizionale", "bpm": 90,
     "melody": "sol3:0.75 sol3:0.25 la3 sol3 do4 si3:2 | sol3:0.75 sol3:0.25 la3 sol3 re4 do4:2 | sol3:0.75 sol3:0.25 sol4 mi4 do4 si3 la3:2 | fa4:0.75 fa4:0.25 mi4 do4 re4 do4:2",
     "lyrics": "Tanti auguri a te\ntanti auguri a te\ntanti auguri a…\ntanti auguri a te"},
    {"title": "Inno alla gioia", "artist": "L. van Beethoven (melodia)", "bpm": 100,
     "melody": "mi4 mi4 fa4 sol4 | sol4 fa4 mi4 re4 | do4 do4 re4 mi4 | mi4:1.5 re4:0.5 re4:2 | mi4 mi4 fa4 sol4 | sol4 fa4 mi4 re4 | do4 do4 re4 mi4 | re4:1.5 do4:0.5 do4:2",
     "lyrics": "(canta su «la»)"},
]
ss = st.session_state
ss.setdefault("songs", [dict(s) for s in EXAMPLES])
ss.setdefault("range", {"lo": None, "hi": None})

EXERCISES = {
    "Note tenute": ("Tieni ogni nota per quattro tempi su una «a» aperta, senza far oscillare la voce.",
                    [(0, 4), (4, 4), (7, 4), (4, 4), (0, 4)]),
    "Scala a cinque note": ("Do-re-mi-fa-sol e ritorno su «ma-me-mi-mo-mu». Ripetilo salendo di mezzo tono.",
                            [(s, 1) for s in (0, 2, 4, 5, 7, 5, 4, 2)] + [(0, 2)]),
    "Arpeggio maggiore": ("1-3-5-8 e ritorno sulla sillaba «no», senza scivolare tra le note.",
                          [(0, 1), (4, 1), (7, 1), (12, 2), (7, 1), (4, 1), (0, 2)]),
    "Terze in successione": ("Salti di terza su e giù. Allena l'orecchio.",
                             [(0, 1), (4, 1), (2, 1), (5, 1), (4, 1), (7, 1), (5, 1), (2, 1), (0, 2)]),
    "Scala maggiore": ("L'ottava intera, salendo e scendendo: do re mi fa sol la si do.",
                       [(s, 1) for s in (0, 2, 4, 5, 7, 9, 11, 12, 11, 9, 7, 5, 4, 2)] + [(0, 2)]),
    "Salto di quinta": ("Do-sol tenuto e ritorno su «ah». Allena l'attacco della nota alta.",
                        [(0, 1), (7, 3), (0, 1), (7, 3), (0, 4)]),
}
VOICE_TYPES = [("basso", 40, 64), ("baritono", 45, 67), ("tenore", 48, 72),
               ("contralto", 53, 77), ("mezzosoprano", 57, 81), ("soprano", 60, 84)]
MIDI_CHOICES = list(range(36, 80))


def median_note(rec):
    x, sr = read_wav(rec.getvalue())
    ms = [m for _, m in track(x, sr) if m is not None]
    return float(np.median(ms)) if len(ms) >= 10 else None


# --------------------------------------------------------------------------
# Interfaccia
# --------------------------------------------------------------------------
st.title("Palestra di Voce")
st.caption("Impara a cantare con esercizi di intonazione e con le canzoni che scegli tu. La4 = 440 Hz.")

tab_acc, tab_ex, tab_song, tab_les = st.tabs(["🎯 Accordatore", "🎼 Esercizi", "🎵 Le mie canzoni", "📖 Lezioni"])

# ---------------- Accordatore ----------------
with tab_acc:
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.subheader("Che nota stai cantando?")
        st.write("Registra 2-3 secondi tenendo una nota ferma su «a» o «o».")
        rec = st.audio_input("Registra una nota", key="tuner_rec")
        if rec:
            m = median_note(rec)
            if m is None:
                st.warning("Non ho sentito una nota abbastanza a lungo. Riprova più vicino al microfono.")
            else:
                cents = round((m - round(m)) * 100)
                a, b, c = st.columns(3)
                a.metric("Nota", name_of(m))
                b.metric("Frequenza", f"{m2f(m):.1f} Hz")
                c.metric("Scarto", f"{cents:+d} cents")
                if abs(cents) <= 10:
                    st.success("Intonato!")
                elif cents < 0:
                    st.info("Un po' calante: pensa la nota più in alto e sostieni il fiato.")
                else:
                    st.info("Un po' crescente: rilassa collo e mascella.")
        st.divider()
        st.write("**Nota di riferimento**")
        ref = st.select_slider("Scegli la nota", MIDI_CHOICES, value=60, format_func=name_of, key="ref_note")
        st.audio(to_wav(tone_samples(ref, 1.8)), format="audio/wav")

    with c2:
        st.subheader("La tua estensione vocale")
        st.write("Registra la nota più bassa che tieni senza sforzo, poi la più alta.")
        r_lo = st.audio_input("Nota più bassa", key="range_lo")
        r_hi = st.audio_input("Nota più alta", key="range_hi")
        if r_lo:
            v = median_note(r_lo)
            if v is not None:
                ss.range["lo"] = int(round(v))
        if r_hi:
            v = median_note(r_hi)
            if v is not None:
                ss.range["hi"] = int(round(v))
        lo, hi = ss.range["lo"], ss.range["hi"]
        a, b = st.columns(2)
        a.metric("Più bassa", name_of(lo) if lo is not None else "—")
        b.metric("Più alta", name_of(hi) if hi is not None else "—")
        if lo is not None and hi is not None and hi > lo:
            best = min(VOICE_TYPES, key=lambda v: abs(v[1] - lo) + abs(v[2] - hi))[0]
            st.write(f"**{hi - lo} semitoni** ({(hi - lo) / 12:.1f} ottave). "
                     f"La tua estensione somiglia a quella di un **{best}**. È una stima: con l'allenamento si allarga.")

# ---------------- Esercizi ----------------
with tab_ex:
    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        ex_name = st.radio("Esercizio", list(EXERCISES), index=1)
        desc, steps = EXERCISES[ex_name]
        default_root = (ss.range["lo"] + 4) if ss.range["lo"] is not None else 55
        default_root = min(max(default_root, 36), 79)
        root = st.select_slider("Nota di partenza", MIDI_CHOICES, value=default_root, format_func=name_of)
        bpm = st.slider("Tempo (bpm)", 50, 140, 80)
    with c2:
        st.subheader(ex_name)
        st.write(desc)
        spb = 60 / bpm
        lead = LEAD * spb
        beat, notes = 0, []
        for s, d in steps:
            notes.append({"midi": root + s, "start": lead + beat * spb, "dur": d * spb, "phrase": 0})
            beat += d
        plan = {"notes": notes, "bpm": bpm, "lead": lead, "total": lead + beat * spb}
        st.plotly_chart(lane_figure(plan), use_container_width=True)
        st.markdown("**1. Ascolta** (4 colpi di metronomo, poi la melodia)")
        st.audio(render_plan(plan), format="audio/wav")
        st.markdown("**2. Canta e registra.** Canta senza la guida in sottofondo, oppure ascoltala in cuffia: "
                    "l'app allinea da sola la prima nota cantata.")
        rec = st.audio_input("Registra l'esercizio", key=f"ex_rec_{ex_name}_{root}_{bpm}")
        if rec:
            analyze_recording(rec, plan)

# ---------------- Canzoni ----------------
with tab_song:
    songs = ss.songs
    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        st.subheader("Le mie canzoni")
        if "_next_idx" in ss:
            ss.song_idx = ss.pop("_next_idx")
        if ss.get("song_idx", 0) >= len(songs):
            ss.song_idx = 0
        idx = st.radio("Scegli una canzone", list(range(len(songs))),
                       format_func=lambda i: f"{songs[i]['title']} · {songs[i].get('artist') or '—'}",
                       key="song_idx") if songs else None

        with st.expander("➕ Aggiungi una canzone", expanded=not songs):
            with st.form("new_song", clear_on_submit=True):
                t = st.text_input("Titolo")
                a = st.text_input("Artista")
                b = st.number_input("Tempo (bpm)", 30, 240, 90)
                mel = st.text_area("Melodia", placeholder="do4 re4 mi4 do4 | mi4 fa4 sol4:2")
                lyr = st.text_area("Testo (una riga per frase)")
                if st.form_submit_button("Salva canzone"):
                    try:
                        parse_melody(mel)
                        if not t.strip():
                            raise ValueError("Dai un titolo alla canzone.")
                        songs.append({"title": t.strip(), "artist": a.strip(), "bpm": int(b),
                                      "melody": mel.strip(), "lyrics": lyr})
                        ss["_next_idx"] = len(songs) - 1
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            st.caption(
                "Note separate da spazi: `do4 re4 mi4` (il numero è l'ottava, do4 è il do centrale). "
                "Durata in tempi con i due punti: `sol4:2`, `mi4:0.5`. Alterazioni: `fa#4`, `sib3`. "
                "Pausa: `p:1`. Separa le frasi con `|`. Vanno bene anche `C4 D4 E4`.")

        with st.expander("💾 Salva o carica la tua raccolta"):
            st.write("Le canzoni aggiunte restano solo finché la pagina è aperta. Scarica il file per tenerle.")
            st.download_button("Scarica le mie canzoni", json.dumps(songs, ensure_ascii=False, indent=2),
                               "mie-canzoni.json", "application/json")
            up = st.file_uploader("Carica un file di canzoni", type="json")
            if up and st.button("Sostituisci la raccolta"):
                try:
                    data = json.loads(up.getvalue().decode("utf-8"))
                    for s in data:
                        parse_melody(s["melody"])
                    ss.songs = data
                    ss["_next_idx"] = 0
                    st.rerun()
                except Exception as e:
                    st.error(f"File non valido: {e}")

    with c2:
        if songs and idx is not None:
            song = songs[idx]
            st.subheader(song["title"])
            st.caption(song.get("artist") or "")
            try:
                parsed, n_phr = parse_melody(song["melody"])
            except ValueError as e:
                st.error(f"La melodia contiene un errore: {e}")
                st.stop()
            lines = (song.get("lyrics") or "").split("\n")
            k1, k2, k3 = st.columns(3)
            tr = k1.number_input("Trasposizione (semitoni)", -12, 12, 0, key=f"tr_{idx}")
            speed = k2.slider("Velocità %", 50, 120, 100, 5, key=f"sp_{idx}")
            phrase = k3.selectbox("Frase", [-1] + list(range(n_phr)), key=f"ph_{idx}",
                                  format_func=lambda i: "Tutta la canzone" if i < 0 else
                                  f"{i + 1}. {(lines[i] if i < len(lines) else '')[:30]}")
            sel = [n for n in parsed if phrase < 0 or n["phrase"] == phrase]
            sbpm = song["bpm"] * speed / 100
            spb = 60 / sbpm
            lead = LEAD * spb
            b0 = sel[0]["beat"]
            plan = {"notes": [{"midi": n["midi"] + tr, "start": lead + (n["beat"] - b0) * spb,
                               "dur": n["dur"] * spb, "phrase": n["phrase"]} for n in sel],
                    "bpm": sbpm, "lead": lead,
                    "total": lead + (sel[-1]["beat"] + sel[-1]["dur"] - b0) * spb}

            lo_s = min(n["midi"] for n in plan["notes"])
            hi_s = max(n["midi"] for n in plan["notes"])
            fit = f"Estensione: {name_of(lo_s)} – {name_of(hi_s)}."
            rlo, rhi = ss.range["lo"], ss.range["hi"]
            if rlo is not None and rhi is not None:
                if lo_s < rlo:
                    fit += f" Scende sotto la tua nota più bassa: prova a trasporre di +{rlo - lo_s}."
                elif hi_s > rhi:
                    fit += f" Sale sopra la tua nota più alta: prova a trasporre di −{hi_s - rhi}."
                else:
                    fit += " Rientra nella tua estensione."
            st.caption(fit)

            shown = sorted({n["phrase"] for n in sel})
            lyr_txt = "  \n".join(lines[i] for i in shown if i < len(lines) and lines[i].strip())
            if lyr_txt:
                st.markdown(f"> {lyr_txt}")
            st.plotly_chart(lane_figure(plan), use_container_width=True)
            st.markdown("**1. Ascolta la melodia**")
            st.audio(render_plan(plan), format="audio/wav")
            st.markdown("**2. Canta e registra**")
            rec = st.audio_input("Registra la tua voce", key=f"song_rec_{idx}_{tr}_{speed}_{phrase}")
            if rec:
                analyze_recording(rec, plan)

            with st.expander("🎧 Traccia originale: ripeti un pezzo in loop"):
                up = st.file_uploader("Carica l'mp3 della canzone", type=["mp3", "m4a", "wav", "ogg"], key=f"orig_{idx}")
                if up:
                    a, b = st.columns(2)
                    start = a.number_input("Inizio (secondi)", 0, 3600, 0, key=f"A_{idx}")
                    end = b.number_input("Fine (secondi, 0 = fino alla fine)", 0, 3600, 0, key=f"B_{idx}")
                    loop = st.checkbox("Ripeti in loop", True, key=f"loop_{idx}")
                    st.audio(up, start_time=start, end_time=end if end > start else None, loop=loop)

            with st.expander("✏️ Modifica o elimina"):
                with st.form(f"edit_{idx}"):
                    t = st.text_input("Titolo", song["title"])
                    a = st.text_input("Artista", song.get("artist", ""))
                    b = st.number_input("Tempo (bpm)", 30, 240, int(song["bpm"]))
                    mel = st.text_area("Melodia", song["melody"])
                    lyr = st.text_area("Testo", song.get("lyrics", ""))
                    if st.form_submit_button("Salva modifiche"):
                        try:
                            parse_melody(mel)
                            song.update(title=t.strip() or song["title"], artist=a.strip(), bpm=int(b),
                                        melody=mel.strip(), lyrics=lyr)
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                if st.checkbox("Voglio eliminare questa canzone", key=f"delchk_{idx}"):
                    if st.button("Elimina definitivamente", type="primary", key=f"del_{idx}"):
                        songs.pop(idx)
                        ss["_next_idx"] = 0
                        st.rerun()
        else:
            st.info("Aggiungi la tua prima canzone dal pannello a sinistra.")

# ---------------- Lezioni ----------------
LESSONS = [
    ("Respirazione", "Il fiato è il motore della voce.",
     ["Mano sull'addome, appena sotto le costole.",
      "Inspira dal naso per 4 tempi: si allargano pancia e fianchi, non si alzano le spalle.",
      "Espira su «sss» per 8 tempi a flusso costante, poi 12 e 16.",
      "Ripeti 5 volte prima di cantare. Esercizio collegato: **Note tenute**."]),
    ("Postura", "Una postura rilassata lascia passare il suono.",
     ["Piedi alla larghezza delle spalle, ginocchia morbide.",
      "Spalle basse, collo lungo, mento parallelo al pavimento.",
      "Mascella sciolta, come all'inizio di uno sbadiglio.",
      "Controlla allo specchio che collo e spalle non si irrigidiscano."]),
    ("Riscaldamento", "Cinque-dieci minuti proteggono la voce.",
     ["Trillo di labbra («brrr») su e giù come una sirena.",
      "Humming a bocca chiusa su «mmm».",
      "**Scala a cinque note**, salendo di mezzo tono a ogni ripetizione.",
      "Finisci tornando alle note centrali."]),
    ("Intonazione", "Intonare è ascoltare prima di cantare.",
     ["Ascolta la guida, immagina la nota, poi cantala.",
      "Nel grafico, i punti verdi sono entro mezzo semitono dalla nota.",
      "Se sbagli spesso, abbassa il tempo.",
      "Sopra l'80%, passa all'esercizio successivo. Prova l'**Arpeggio maggiore**."]),
    ("Imparare una canzone", "Una canzone si impara a pezzi.",
     ["Ascolta la traccia originale ripetendo una frase in loop.",
      "Scrivi la melodia frase per frase (separate da `|`) e il testo riga per riga.",
      "Trasponi finché il brano rientra nella tua estensione.",
      "Studia una frase alla volta, poi uniscile."]),
    ("Salute della voce", "Una voce allenata non si sforza.",
     ["Bevi acqua durante la giornata.",
      "Meglio 15-20 minuti al giorno che due ore una volta a settimana.",
      "Se senti dolore o raucedine, fermati.",
      "Se la raucedine dura più di due settimane, parlane con un medico."]),
]
with tab_les:
    cols = st.columns(2, gap="large")
    for i, (title, intro, steps) in enumerate(LESSONS):
        with cols[i % 2]:
            with st.container(border=True):
                st.caption(f"Lezione {i + 1} di {len(LESSONS)}")
                st.subheader(title)
                st.write(intro)
                st.markdown("\n".join(f"{j + 1}. {s}" for j, s in enumerate(steps)))
