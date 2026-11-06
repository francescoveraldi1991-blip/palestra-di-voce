"""Karaoke: video YouTube, testo che scorre a tempo e voce misurata dal vivo."""
import re
from pathlib import Path

import streamlit.components.v1 as components

from testo import clean_line

_component = components.declare_component(
    "karaoke", path=str(Path(__file__).parent / "karaoke_frontend"))

_ID_RE = re.compile(r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([A-Za-z0-9_-]{11})")
_LRC_TIME = re.compile(r"\[(\d{1,3}):(\d{1,2}(?:[.,]\d{1,3})?)\]")


def video_id(url: str):
    """Estrae l'identificativo di 11 caratteri da un link YouTube."""
    m = _ID_RE.search(url or "")
    return m.group(1) if m else None


def lyric_lines(song):
    """Righe di testo non vuote, ciascuna con il suo tempo (o None)."""
    texts = [l.strip() for l in (song.get("lyrics") or "").split("\n") if l.strip()]
    times = song.get("sync") or []
    if len(times) != len(texts):
        times = [None] * len(texts)
    return [{"text": t, "t": s} for t, s in zip(texts, times)]


def parse_lrc(text: str):
    """Legge un file .lrc: restituisce (testo, tempi)."""
    items = []
    for raw in text.splitlines():
        stamps = _LRC_TIME.findall(raw)
        if not stamps:
            continue
        words = _LRC_TIME.sub("", raw).strip()
        if not words:
            continue
        for mm, ss in stamps:
            items.append((int(mm) * 60 + float(ss.replace(",", ".")), words))
    if not items:
        raise ValueError("Nel file non ho trovato righe con il tempo, come [00:12.50] testo.")
    items.sort()
    return "\n".join(w for _, w in items), [round(t, 2) for t, _ in items]


def to_lrc(song) -> str:
    out = [f"[ti:{song.get('title', '')}]", f"[ar:{song.get('artist', '')}]"]
    for line in lyric_lines(song):
        if line["t"] is None:
            continue
        m, s = divmod(line["t"], 60)
        out.append(f"[{int(m):02d}:{s:05.2f}]{line['text']}")
    return "\n".join(out) + "\n"


def karaoke(song, song_key, theme=None, notes=None, midi=None):
    """Mostra il karaoke. Restituisce l'ultimo messaggio inviato dal riquadro (o None).

    notes: note della melodia già messe a tempo sul video, con la sillaba ('syl').
    """
    shown = [{"text": clean_line(l["text"]), "t": l["t"]} for l in lyric_lines(song)]
    return _component(video_id=video_id(song.get("youtube", "")), lines=shown, notes=notes or [], midi=midi,
                      title=song.get("title", ""), song_key=song_key, theme=theme,
                      key="karaoke_main", default=None)
