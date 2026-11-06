"""Grafica di Palestra di Voce: colori, caratteri e intestazione.

Solo aspetto: nessuna funzionalità dell'app dipende da questo file.
"""
import streamlit as st

LIGHT = {
    "bg": "#F3F5F9", "surface": "#FFFFFF", "ink": "#141B26", "muted": "#5A6577",
    "line": "#D8DEE7", "accent": "#2B45D4", "soft": "#E6EAFB", "warm": "#D9702A", "good": "#1C9764",
}
DARK = {
    "bg": "#0E131B", "surface": "#161D28", "ink": "#E7EBF1", "muted": "#95A1B4",
    "line": "#273244", "accent": "#7D90FF", "soft": "#1E2747", "warm": "#F09B5C", "good": "#3CC48A",
}
FONTS = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800"
         "&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap")


def theme_type():
    """'light', 'dark' oppure None se Streamlit non lo sa ancora."""
    try:
        return st.context.theme.type
    except Exception:
        return None


def palette():
    return DARK if theme_type() == "dark" else LIGHT


def _vars(p):
    return ";".join(f"--pdv-{k}:{v}" for k, v in p.items())


def inject():
    t = theme_type()
    if t == "dark":
        tokens = f":root{{{_vars(DARK)}}}"
    elif t == "light":
        tokens = f":root{{{_vars(LIGHT)}}}"
    else:
        tokens = f":root{{{_vars(LIGHT)}}} @media (prefers-color-scheme: dark){{:root{{{_vars(DARK)}}}}}"
    st.html(f"""<style>
@import url('{FONTS}');
{tokens}
[data-testid="stMainBlockContainer"]{{padding-top:2.2rem;padding-bottom:4rem;max-width:1240px}}

/* Intestazione */
.pdv-hero{{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:2rem;align-items:center;
  background:var(--pdv-surface);border:1px solid var(--pdv-line);border-radius:18px;padding:1.9rem 2.2rem;
  margin-bottom:.4rem;position:relative;overflow:hidden}}
.pdv-hero::before{{content:"";position:absolute;inset:0 auto 0 0;width:6px;background:var(--pdv-accent)}}
.pdv-eyebrow{{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:.72rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--pdv-muted);margin:0 0 .6rem}}
.pdv-hero h1{{font-family:"Bricolage Grotesque","Avenir Next",system-ui,sans-serif;font-weight:800;
  font-size:clamp(2.2rem,4.6vw,3.4rem);line-height:1;letter-spacing:-.035em;margin:0;padding:0;color:var(--pdv-ink)}}
.pdv-hero h1 span{{color:var(--pdv-accent)}}
.pdv-hero p.pdv-lead{{font-size:1.05rem;line-height:1.55;color:var(--pdv-muted);margin:.9rem 0 0;max-width:46ch}}
.pdv-facts{{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:1.2rem}}
.pdv-facts span{{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:.75rem;color:var(--pdv-ink);
  border:1px solid var(--pdv-line);border-radius:999px;padding:.3rem .75rem;background:var(--pdv-bg)}}
.pdv-facts span b{{color:var(--pdv-accent);font-weight:500}}
.pdv-staff{{width:100%;height:auto;display:block}}
.pdv-sl line{{stroke:var(--pdv-line);stroke-width:1.5}}
.pdv-sn rect{{fill:var(--pdv-soft);stroke:var(--pdv-accent);stroke-width:1.5}}
.pdv-sn rect.pdv-on{{fill:var(--pdv-accent)}}
.pdv-sv{{fill:none;stroke:var(--pdv-good);stroke-width:3.5;stroke-linecap:round}}
.pdv-sd{{fill:var(--pdv-good)}}
@media (max-width:760px){{.pdv-hero{{grid-template-columns:minmax(0,1fr);padding:1.5rem 1.4rem}} .pdv-staff{{max-height:130px}}}}

/* Schede principali */
[data-testid="stTabs"] [role="tablist"]{{gap:.35rem;border-bottom:1px solid var(--pdv-line)}}
[data-testid="stTabs"] button[role="tab"]{{padding:.55rem .9rem}}
[data-testid="stTabs"] button[role="tab"] p{{font-weight:600;font-size:.98rem}}

/* Numeri e riquadri */
[data-testid="stMetric"]{{background:var(--pdv-surface);border:1px solid var(--pdv-line);border-radius:12px;padding:.8rem 1rem}}
[data-testid="stMetricLabel"] p{{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--pdv-muted)}}
[data-testid="stMetricValue"]{{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-weight:800;letter-spacing:-.02em}}
[data-testid="stExpander"] details{{border-radius:12px}}
[data-testid="stVerticalBlockBorderWrapper"]{{border-radius:14px}}
blockquote{{border-left:3px solid var(--pdv-accent)!important;font-size:1.1rem}}

.pdv-foot{{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--pdv-line);color:var(--pdv-muted);
  font-size:.82rem;display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem}}
</style>""")


# Pentagramma con note e la linea di una voce che le insegue
_STAFF = """<svg class="pdv-staff" viewBox="0 0 420 170" role="img" aria-label="Pentagramma con una melodia e la linea della voce">
  <g class="pdv-sl">
    <line x1="0" y1="35" x2="420" y2="35"/><line x1="0" y1="60" x2="420" y2="60"/><line x1="0" y1="85" x2="420" y2="85"/>
    <line x1="0" y1="110" x2="420" y2="110"/><line x1="0" y1="135" x2="420" y2="135"/>
  </g>
  <g class="pdv-sn">
    <rect x="18" y="116" width="62" height="13" rx="4"/><rect x="92" y="91" width="62" height="13" rx="4"/>
    <rect x="166" y="66" width="62" height="13" rx="4"/><rect x="240" y="41" width="104" height="13" rx="4" class="pdv-on"/>
    <rect x="356" y="78" width="56" height="13" rx="4"/>
  </g>
  <path d="M20 128 C40 124 60 122 78 123 C90 124 94 100 104 98 C124 95 140 97 152 98 C164 99 170 74 182 73
           C200 71 214 72 226 72 C236 72 244 48 256 47 C280 45 310 48 340 47 C350 47 356 84 366 85 C384 86 398 84 410 85"
        class="pdv-sv"/>
  <circle cx="340" cy="47" r="6" class="pdv-sd"/>
</svg>"""


def hero():
    st.html(f"""<div class="pdv-hero">
  <div>
    <p class="pdv-eyebrow">Allenamento vocale · La4 = 440 Hz</p>
    <h1>Palestra di <span>Voce</span></h1>
    <p class="pdv-lead">Allena l'intonazione con la tua voce in diretta, scopri la tua estensione
    impara le canzoni che scegli tu e cantale in karaoke.</p>
    <div class="pdv-facts"><span><b>●</b> Karaoke con YouTube</span><span><b>●</b> Accordatore live</span><span><b>6</b> esercizi guidati</span><span><b>6</b> lezioni</span></div>
  </div>
  {_STAFF}
</div>""")


def footer():
    st.html('<div class="pdv-foot"><span>Palestra di Voce</span>'
            '<span>Consiglio: canta in cuffia, così il microfono sente solo te.</span></div>')
