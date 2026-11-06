"""Lettura dei file MIDI karaoke (.kar / .mid con testo).

Ricava dal file:
- tutte le note, per suonare la base nel browser;
- il testo, sillaba per sillaba, con il suo tempo;
- la traccia della melodia cantata, con la sillaba abbinata a ogni nota.
Nessuna libreria esterna: il formato MIDI è letto qui sotto.
"""
import struct

DRUM_CH = 9


class MidiError(ValueError):
    pass


def _varlen(data, i):
    v = 0
    while True:
        if i >= len(data):
            raise MidiError("File MIDI troncato.")
        b = data[i]
        i += 1
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            return v, i


def _decode(raw: bytes) -> str:
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def read_midi(data: bytes):
    """Restituisce (division, tracce). Ogni traccia: lista di (tick, tipo, valori)."""
    if data[:4] != b"MThd":
        raise MidiError("Non è un file MIDI (manca l'intestazione MThd).")
    hlen = struct.unpack(">I", data[4:8])[0]
    _fmt, ntracks, division = struct.unpack(">HHH", data[8:14])
    i = 8 + hlen
    tracks = []
    for _ in range(ntracks):
        while i + 8 <= len(data) and data[i:i + 4] != b"MTrk":   # salta blocchi sconosciuti
            i += 8 + struct.unpack(">I", data[i + 4:i + 8])[0]
        if i + 8 > len(data):
            break
        tlen = struct.unpack(">I", data[i + 4:i + 8])[0]
        tr = data[i + 8: i + 8 + tlen]
        i += 8 + tlen
        events, j, tick, status = [], 0, 0, None
        while j < len(tr):
            delta, j = _varlen(tr, j)
            tick += delta
            if j >= len(tr):
                break
            b = tr[j]
            if b == 0xFF:                       # meta
                mtype = tr[j + 1]
                ln, j = _varlen(tr, j + 2)
                events.append((tick, "meta", (mtype, tr[j:j + ln])))
                j += ln
                if mtype == 0x2F:
                    break
                continue
            if b in (0xF0, 0xF7):               # sysex
                ln, j = _varlen(tr, j + 1)
                j += ln
                continue
            if b & 0x80:
                status = b
                j += 1
            elif status is None:
                raise MidiError("File MIDI non valido (running status senza stato).")
            kind, ch = status & 0xF0, status & 0x0F
            nbytes = 1 if kind in (0xC0, 0xD0) else 2
            vals = tr[j:j + nbytes]
            j += nbytes
            events.append((tick, kind, (ch, *vals)))
        tracks.append(events)
    return division, tracks


def _tick_to_sec_fn(division, tracks):
    if division & 0x8000:                       # SMPTE
        fps = 256 - (division >> 8)
        tpf = division & 0xFF
        return lambda t: t / (fps * tpf)
    tempos = sorted((tk, int.from_bytes(v[1], "big")) for tr in tracks for tk, k, v in tr
                    if k == "meta" and v[0] == 0x51 and len(v[1]) == 3)
    marks = [(0, 0.0, 500000)]                  # (tick, secondi, microsecondi per semiminima)
    for tk, us in tempos:
        t0, s0, us0 = marks[-1]
        marks.append((tk, s0 + (tk - t0) * us0 / 1e6 / division, us))

    def conv(t):
        k = len(marks) - 1
        while k > 0 and marks[k][0] > t:
            k -= 1
        t0, s0, us0 = marks[k]
        return s0 + (t - t0) * us0 / 1e6 / division
    first_bpm = 60e6 / (tempos[0][1] if tempos else 500000)
    conv.first_bpm = first_bpm
    return conv


def _lyric_events(tracks, sec):
    """Sceglie gli eventi di testo: prima i «lyric» (0x05), poi i «text» (0x01) dei .kar."""
    best = []
    for mtype in (0x05, 0x01):
        for tr in tracks:
            evs = []
            for tk, k, v in tr:
                if k == "meta" and v[0] == mtype:
                    txt = _decode(v[1])
                    if txt.startswith("@") or txt.startswith("%"):
                        continue
                    evs.append((sec(tk), txt))
            if len(evs) > len(best):
                best = evs
        if len(best) >= 8:
            break
    return best


def _syllables(events):
    """Da eventi grezzi a sillabe: [{t, syl, we, nl}] (nl = inizia una nuova riga)."""
    out, new_line = [], True
    for t, raw in events:
        r = raw.replace("\r\n", "\n").replace("\r", "\n")
        starts_nl = r[:1] in "/\\\n"
        ends_nl = r.endswith("\n")
        text = r.strip("/\\\n")
        if not text.strip():
            if starts_nl or ends_nl:
                new_line = True
            elif out and text != "":
                out[-1]["we"] = True            # evento di solo spazio = fine parola
            continue
        if text.startswith(" ") and out:
            out[-1]["we"] = True
        out.append({"t": t, "syl": text.strip(), "we": text.endswith(" ") or ends_nl,
                    "nl": new_line or starts_nl})
        new_line = ends_nl
    if out:
        out[-1]["we"] = True
    for k, s in enumerate(out):                 # una parola finisce dove inizia una riga
        if k + 1 < len(out) and out[k + 1]["nl"]:
            s["we"] = True
    return out


def parse_kar(data: bytes):
    division, tracks = read_midi(data)
    sec = _tick_to_sec_fn(division, tracks)

    # titolo dal file (.kar: @T...), altrimenti nome della prima traccia
    title, program = "", {}
    for tr in tracks:
        for tk, k, v in tr:
            if k == "meta" and v[0] == 0x01 and v[1][:2] == b"@T" and not title:
                title = _decode(v[1][2:]).strip()
    # note di tutte le tracce
    notes, open_ = [], {}
    for ti, tr in enumerate(tracks):
        for tk, k, v in tr:
            if k == 0xC0:
                program[v[0]] = v[1]
            elif k in (0x80, 0x90):
                ch, n, vel = v[0], v[1], v[2] if len(v) > 2 else 0
                key = (ti, ch, n)
                if k == 0x90 and vel > 0:
                    open_.setdefault(key, []).append((tk, vel, program.get(ch, 0)))
                elif open_.get(key):
                    t0, v0, prg = open_[key].pop(0)
                    notes.append({"tr": ti, "ch": ch, "midi": n, "vel": v0, "prg": prg,
                                  "start": sec(t0), "end": sec(tk)})
    if not notes:
        raise MidiError("Il file non contiene note.")
    notes.sort(key=lambda n: n["start"])
    duration = max(n["end"] for n in notes)

    syl = _syllables(_lyric_events(tracks, sec))

    # traccia della melodia: quella le cui note partono insieme alle sillabe
    melody_key, best = None, 0.0
    if syl:
        groups = {}
        for n in notes:
            if n["ch"] != DRUM_CH:
                groups.setdefault((n["tr"], n["ch"]), []).append(n["start"])
        t_first, t_last = syl[0]["t"] - 0.5, syl[-1]["t"] + 2.0
        pitch = {}
        for n in notes:
            pitch.setdefault((n["tr"], n["ch"]), []).append(n["midi"])
        for key, starts in groups.items():
            starts.sort()
            hit, j = 0, 0
            for s in syl:
                while j < len(starts) and starts[j] < s["t"] - 0.08:
                    j += 1
                if j < len(starts) and abs(starts[j] - s["t"]) <= 0.08:
                    hit += 1
            # richiamo: sillabe con una nota; precisione: note che hanno una sillaba
            in_range = sum(1 for x in starts if t_first <= x <= t_last) or 1
            rec, prec = hit / len(syl), min(1.0, hit / in_range)
            score = 2 * rec * prec / (rec + prec) if rec + prec else 0
            score += sum(pitch[key]) / len(pitch[key]) / 10000   # a parità, la traccia più acuta
            if score > best:
                best, melody_key = score, key
    if best < 0.3:
        melody_key = None

    # righe di testo
    lines = []
    for s in syl:
        if s["nl"] or not lines:
            lines.append({"t": round(s["t"], 2), "syls": []})
        lines[-1]["syls"].append(s)

    # melodia con sillabe abbinate
    mel = []
    if melody_key:
        mel = [n for n in notes if (n["tr"], n["ch"]) == melody_key]
        # tieni una sola nota per attacco (la più acuta), così la melodia è monofonica
        mono = []
        for n in mel:
            if mono and abs(mono[-1]["start"] - n["start"]) < 0.02:
                if n["midi"] > mono[-1]["midi"]:
                    mono[-1] = n
                continue
            mono.append(n)
        mel = mono
        used = set()
        for li, line in enumerate(lines):
            for s in line["syls"]:
                cand = min((k for k in range(len(mel)) if k not in used),
                           key=lambda k: abs(mel[k]["start"] - s["t"]), default=None)
                if cand is not None and abs(mel[cand]["start"] - s["t"]) <= 0.15:
                    used.add(cand)
                    mel[cand]["syl"], mel[cand]["we"] = s["syl"], s["we"]
        li = 0
        for n in mel:
            while li + 1 < len(lines) and lines[li + 1]["t"] <= n["start"] + 0.05:
                li += 1
            n["phrase"] = li
            n.setdefault("syl", "")
            n.setdefault("we", False)

    melody_ids = {id(n) for n in mel}
    events = [[round(n["start"], 3), round(max(0.05, n["end"] - n["start"]), 3), n["midi"], n["vel"],
               n["ch"], n["prg"], 1 if id(n) in melody_ids or (melody_key and (n["tr"], n["ch"]) == melody_key) else 0]
              for n in notes]
    return {
        "title": title,
        "duration": round(duration, 2),
        "bpm": round(sec.first_bpm),
        "events": events,
        "lines": [{"t": l["t"], "syls": [(s["syl"], s["we"]) for s in l["syls"]]} for l in lines],
        "notes": [{"midi": n["midi"], "start": round(n["start"], 3), "dur": round(n["end"] - n["start"], 3),
                   "syl": n["syl"], "we": n["we"], "phrase": n["phrase"]} for n in mel],
    }


IT = ["do", "do#", "re", "re#", "mi", "fa", "fa#", "sol", "sol#", "la", "la#", "si"]


def to_app_song(parsed, fallback_title):
    """Converte in una canzone dell'app: testo con trattini, melodia nella notazione, tempi delle righe."""
    lines = parsed["lines"]
    notes = parsed["notes"]
    bpm = max(40, min(200, parsed["bpm"] or 90))
    beat = 60 / bpm
    q = lambda s: max(0.25, round(s / beat * 4) / 4)

    # testo: sillabe unite con «-»; «_» = nota senza sillaba (vocalizzo)
    if notes:
        by_p = {}
        for n in notes:
            by_p.setdefault(n["phrase"], []).append(n)
        text_lines, mel_phr = [], []
        for p in range(len(lines)):
            group = by_p.get(p, [])
            words, toks = "", []
            for k, n in enumerate(group):
                if n["syl"]:
                    words += n["syl"] + (" " if n["we"] else "-")
                else:
                    words += " _ "
                nxt = group[k + 1]["start"] if k + 1 < len(group) else None
                gap = (nxt - (n["start"] + n["dur"])) if nxt is not None else 0
                legato = nxt is not None and gap < beat / 4
                toks.append(f"{IT[n['midi'] % 12]}{n['midi'] // 12 - 1}:{q((nxt - n['start']) if legato else n['dur']):g}")
                if nxt is not None and not legato:
                    toks.append(f"p:{q(gap):g}")
            # le sillabe del file che non hanno trovato una nota restano nel testo
            if not group:
                words = "".join(s + (" " if we else "-") for s, we in lines[p]["syls"])
                toks = ["p:1"]
            text_lines.append(" ".join(words.split()))
            mel_phr.append(" ".join(toks))
        melody = " | ".join(mel_phr)
    else:
        text_lines = ["".join(s + (" " if we else "") for s, we in l["syls"]).strip() for l in lines]
        melody = ""
    return {
        "title": parsed["title"] or fallback_title,
        "artist": "",
        "bpm": int(bpm),
        "melody": melody,
        "lyrics": "\n".join(text_lines),
        "youtube": "",
        "sync": [l["t"] for l in lines],
        "midi": {"events": parsed["events"], "duration": parsed["duration"], "notes": parsed["notes"]},
    }
