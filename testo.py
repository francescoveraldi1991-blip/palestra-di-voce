"""Divide il testo in sillabe e abbina ogni sillaba alla sua nota.

Regola semplice: la riga N del testo va con la frase N della melodia (le frasi
sono separate da | nella melodia). Ogni nota prende una sillaba, in ordine.
Chi vuole decidere le sillabe a mano può scriverle con il trattino:
«Fra Mar-ti-no» → Fra · Mar · ti · no.
"""
import re

VOWELS = set("aeiouàèéìíòóùúAEIOUÀÈÉÌÍÒÓÙÚyY")
LIQUID_NASAL = set("lmnrLMNR")


def _is_vowel(word, i):
    c = word[i]
    if c not in VOWELS:
        return False
    # la «u» di «qu» e «gu» davanti a vocale non fa sillaba
    if c in "uU" and i > 0 and word[i - 1] in "qQgG" and i + 1 < len(word) and word[i + 1] in VOWELS:
        return False
    # la «i» di «ci», «gi», «sci», «gli» davanti a vocale è solo grafica
    if c in "iI" and i > 0 and word[i - 1] in "cCgG" and i + 1 < len(word) and word[i + 1] in VOWELS:
        return False
    return True


def syllabify_word(word: str):
    """Sillabazione approssimata per l'italiano (va bene anche per molte parole straniere)."""
    letters = [i for i, c in enumerate(word) if c.isalpha()]
    if not letters:
        return [word]
    nuclei = []  # gruppi di vocali consecutive
    i = 0
    while i < len(word):
        if word[i].isalpha() and _is_vowel(word, i):
            j = i
            while j + 1 < len(word) and word[j + 1].isalpha() and _is_vowel(word, j + 1):
                j += 1
            nuclei.append((i, j))
            i = j + 1
        else:
            i += 1
    if len(nuclei) <= 1:
        return [word]
    cuts = []
    for (_, end), (start, _) in zip(nuclei, nuclei[1:]):
        cons = [k for k in range(end + 1, start) if word[k].isalpha()]
        if len(cons) <= 1:
            cut = end + 1                       # ca-sa
        else:
            a, b = word[cons[0]].lower(), word[cons[1]].lower()
            if a == b or (a == "c" and b == "q"):
                cut = cons[1]                   # gat-to, ac-qua
            elif a == "s":
                cut = cons[0]                   # ca-sta
            elif word[cons[0]] in LIQUID_NASAL:
                cut = cons[1]                   # can-to, ar-te
            else:
                cut = cons[0]                   # ca-pra, ma-gro
        cuts.append(cut)
    parts, prev = [], 0
    for c in cuts:
        parts.append(word[prev:c])
        prev = c
    parts.append(word[prev:])
    return [p for p in parts if p]


def syllables(line: str):
    """Restituisce [(sillaba, fine_parola)] per una riga di testo."""
    out = []
    for word in line.split():
        if "-" in word.strip("-"):
            parts = [p for p in word.split("-") if p]
        else:
            parts = syllabify_word(word)
        for k, p in enumerate(parts):
            out.append((p, k == len(parts) - 1))
    return out


def clean_line(line: str) -> str:
    """La riga come va mostrata (senza i trattini usati per dividere le sillabe)."""
    return " ".join("".join(p for p, _ in syllables(w)) for w in line.split()) if "-" in line else line


def attach(notes, lyric_lines):
    """Aggiunge a ogni nota 'syl' (sillaba) e 'we' (fine parola).

    notes: lista di dict con 'phrase'; lyric_lines: righe non vuote del testo.
    Note in più rispetto alle sillabe restano senza sillaba (vocalizzo);
    sillabe in più vengono unite all'ultima nota della frase.
    """
    by_phrase = {}
    for n in notes:
        by_phrase.setdefault(n["phrase"], []).append(n)
    for p, group in by_phrase.items():
        syl = syllables(lyric_lines[p]) if p < len(lyric_lines) else []
        for n in group:
            n["syl"], n["we"] = "", False
        for k, n in enumerate(group):
            if k < len(syl):
                n["syl"], n["we"] = syl[k]
        if len(syl) > len(group) and group:
            extra = syl[len(group) - 1:]
            text = ""
            for s, we in extra:
                text += s + (" " if we else "")
            group[-1]["syl"], group[-1]["we"] = text.rstrip(), True
    return notes


def lyric_list(text: str):
    return [l.strip() for l in (text or "").split("\n") if l.strip()]
