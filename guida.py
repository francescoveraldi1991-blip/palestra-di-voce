"""Guida interattiva di Palestra di Voce (finestra passo per passo)."""
import streamlit as st

STEPS = [
    {
        "titolo": "Benvenuto in Palestra di Voce",
        "icona": ":material/waving_hand:",
        "intro": "In pochi minuti al giorno alleni l'orecchio e la voce. L'app ti ascolta mentre canti "
                 "e ti mostra se sei sulla nota giusta.",
        "fare": [
            "**Accordatore**: vedi che nota stai cantando e misuri la tua estensione.",
            "**Esercizi**: scale e salti guidati, con punteggio di intonazione.",
            "**Le mie canzoni**: impari le canzoni che scegli tu, una frase alla volta.",
            "**Lezioni**: le basi su fiato, postura e salute della voce.",
        ],
        "vedi": "Le schede sono in alto, sotto l'intestazione. Questa guida ti accompagna nell'ordine giusto.",
    },
    {
        "titolo": "1 · Attiva il microfono",
        "icona": ":material/mic:",
        "intro": "Tutto parte dall'accordatore. Serve una sola volta per sessione.",
        "fare": [
            "Apri la scheda **Accordatore**.",
            "Premi il pulsante blu **Attiva microfono**.",
            "Quando il browser lo chiede, scegli **Consenti**.",
            "Canta una «a» lunga e ferma, a volume normale.",
        ],
        "vedi": "Compare la nota che canti (per esempio *La3*) e una lancetta. "
                "Se la lancetta resta nella **fascia verde** sei intonato. A sinistra sei calante, a destra crescente.",
        "extra": "audio",
    },
    {
        "titolo": "2 · Misura la tua estensione",
        "icona": ":material/straighten:",
        "intro": "L'estensione è la distanza tra la nota più bassa e la più alta che canti comodamente. "
                 "Serve all'app per scegliere esercizi e tonalità adatti a te.",
        "fare": [
            "Sempre nella scheda **Accordatore**, guarda a destra: «La tua estensione vocale».",
            "Premi **Nota più bassa**, canta la nota più grave che tieni senza sforzo per 2-3 secondi, poi ferma.",
            "Fai lo stesso con **Nota più alta**.",
        ],
        "vedi": "L'app mostra le due note, quanti semitoni copri e a che tipo di voce somigli "
                "(basso, tenore, soprano…). Non forzare: deve essere una nota comoda, non un urlo.",
    },
    {
        "titolo": "3 · Fai un esercizio",
        "icona": ":material/piano:",
        "intro": "Il cuore dell'allenamento. Ogni esercizio è una piccola melodia da seguire.",
        "fare": [
            "Apri **Esercizi** e scegli **Scala a cinque note** (è il riscaldamento classico).",
            "Lascia la nota di partenza proposta e un tempo lento, 70-80 bpm.",
            "Nel riquadro **Live** premi **Canta**: senti 4 colpi di metronomo, al quarto inizia.",
            "Segui le barre blu che scorrono: canta la nota della barra che passa sotto la linea verticale.",
        ],
        "vedi": "La tua voce appare come una linea: **verde** se sei intonato, **arancione** se sei fuori nota. "
                "Alla fine ricevi un punteggio e i consigli (per esempio «tendi a calare»).",
        "extra": "lane",
    },
    {
        "titolo": "4 · Trucchi per un punteggio affidabile",
        "icona": ":material/headphones:",
        "intro": "Il microfono sente tutto quello che esce dalle casse.",
        "fare": [
            "Usa le **cuffie**: così il microfono sente solo te.",
            "Senza cuffie, togli la spunta a **Suona la guida** e canta da solo dopo aver ascoltato (**Solo ascolto**).",
            "Se il punteggio è basso, abbassa il **tempo** e riprova.",
            "Ce la fai sopra l'80%? Alza la **nota di partenza** di mezzo tono e ripeti.",
        ],
        "vedi": "Vale anche cantare un'ottava sopra o sotto la guida: l'app lo riconosce.",
    },
    {
        "titolo": "5 · Aggiungi una canzone",
        "icona": ":material/library_music:",
        "intro": "In **Le mie canzoni** trovi tre esempi. Per aggiungerne una tua, apri «Aggiungi una canzone» "
                 "e scrivi la melodia con questa notazione semplice.",
        "fare": [
            "Note separate da spazi: `do4 re4 mi4`. Il numero è l'ottava: **do4 è il do centrale** del pianoforte.",
            "Durata in tempi dopo i due punti: `sol4:2` dura due tempi, `mi4:0.5` mezzo tempo. Senza numero vale 1.",
            "Diesis e bemolli: `fa#4`, `sib3`. Pausa: `p:1`.",
            "Separa le frasi con `|` e scrivi il testo con **una riga per frase**.",
        ],
        "vedi": "Prova qui sotto: scrivi qualche nota e guarda come l'app la legge.",
        "extra": "notazione",
    },
    {
        "titolo": "6 · Studia la canzone",
        "icona": ":material/repeat:",
        "intro": "Una canzone si impara a pezzi.",
        "fare": [
            "**Trasposizione**: se il brano è troppo alto o basso, spostalo di qualche semitono. "
            "L'app ti dice se rientra nella tua estensione.",
            "**Frase**: scegli una frase sola e attiva **Ripeti** finché la sai.",
            "**Velocità**: parti al 70% e sali piano fino al 100%.",
            "**Traccia originale**: carica l'mp3 della canzone e ripeti in loop un pezzo, indicando inizio e fine.",
        ],
        "vedi": "Le canzoni che aggiungi restano solo finché la pagina è aperta. "
                "Prima di chiudere usa **Salva o carica la tua raccolta → Scarica le mie canzoni**, "
                "e la volta dopo ricarica il file.",
    },
    {
        "titolo": "Il tuo allenamento di 20 minuti",
        "icona": ":material/fitness_center:",
        "intro": "Meglio poco ogni giorno che tanto una volta a settimana.",
        "fare": [
            "**2 min** · Respirazione (scheda Lezioni, lezione 1).",
            "**5 min** · Scala a cinque note, salendo di mezzo tono a ogni ripetizione.",
            "**5 min** · Un esercizio a scelta finché superi l'80%.",
            "**8 min** · Una canzone, una frase alla volta.",
        ],
        "vedi": "Se senti dolore o raucedine, fermati. Puoi riaprire questa guida quando vuoi "
                "dal pulsante **Guida** in alto.",
    },
]


def _go(delta):
    st.session_state.guide_step = max(0, min(len(STEPS) - 1, st.session_state.get("guide_step", 0) + delta))


def _extra(kind, tools):
    if kind == "audio":
        st.caption("Prova: ascolta un La3, poi cantalo nell'accordatore.")
        st.audio(tools["tone"](57, 1.8), format="audio/wav")
    elif kind == "lane":
        st.caption("Ecco come appare un esercizio: le barre sono le note da cantare.")
        st.plotly_chart(tools["lane"](), use_container_width=True, key="guide_lane")
    elif kind == "notazione":
        txt = st.text_input("Prova la notazione", "do4 re4 mi4:2 | sol4:0.5 fa#4:0.5 p:1 do5:2",
                            key="guide_notation")
        try:
            notes, phrases = tools["parse"](txt)
            st.success(f"Letta correttamente: {len(notes)} note in {phrases} frasi.")
            st.markdown(" ".join(
                f"`{tools['name'](n['midi'])} · {n['dur']:g} {'tempo' if n['dur'] == 1 else 'tempi'}`" for n in notes[:24]))
        except ValueError as e:
            st.error(f"{e}. Controlla gli esempi qui sopra.")


@st.dialog("Guida rapida", width="large")
def show(tools):
    """tools: dict con 'tone', 'lane', 'parse', 'name' (funzioni dell'app)."""
    i = st.session_state.get("guide_step", 0)
    step = STEPS[i]
    st.progress((i + 1) / len(STEPS), text=f"Passo {i + 1} di {len(STEPS)}")
    st.subheader(f"{step['icona']} {step['titolo']}")
    st.write(step["intro"])
    st.markdown("**Cosa fare**")
    st.markdown("\n".join(f"{n + 1}. {t}" for n, t in enumerate(step["fare"])))
    st.info(step["vedi"], icon=":material/visibility:")
    if step.get("extra"):
        _extra(step["extra"], tools)

    c1, c2, c3 = st.columns([1, 1, 1])
    c1.button("Indietro", icon=":material/arrow_back:", disabled=i == 0, on_click=_go, args=(-1,),
              use_container_width=True, key="g_back")
    if c2.button("Chiudi la guida", use_container_width=True, key="g_close"):
        st.rerun()
    if i < len(STEPS) - 1:
        c3.button("Avanti", icon=":material/arrow_forward:", type="primary", on_click=_go, args=(1,),
                  use_container_width=True, key="g_next")
    elif c3.button("Iniziamo!", icon=":material/check:", type="primary", use_container_width=True, key="g_done"):
        st.session_state.guide_step = 0
        st.rerun()
