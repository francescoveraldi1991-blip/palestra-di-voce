"""Le lezioni interattive: ogni lezione è una sequenza di attività guidate.

Tipi di attività (li esegue il riquadro _LESSON in live.py):
- check:   lista di passi da spuntare, con timer facoltativo (secs)
- breath:  inspira per N tempi, poi «sss» per M tempi; l'app ascolta il soffio
- sustain: nota tenuta (vocale o «mmm»); l'app misura quanto resta ferma
- siren:   sirena con trillo di labbra; l'app disegna la curva e misura l'ampiezza
- echo:    l'app suona una nota, l'utente la ripete; l'app misura lo scarto
"""

TEMPO = ("Un «tempo» è un battito regolare, come il tic-tac di un orologio: qui ogni tempo dura "
         "1 secondo e lo senti con un clic, mentre sullo schermo vedi il numero. ")

LESSONS = [
    {
        "id": "respiro", "title": "Respirazione",
        "intro": "Il fiato è il motore della voce: impari a prendere aria in basso e a farla uscire in modo costante.",
        "acts": [
            {"type": "check", "short": "Preparati", "title": "Preparati",
             "how": "Mettiti comodo e prepara il corpo. Spunta ogni passo quando l'hai fatto.",
             "items": [
                 {"t": "Stai in piedi (o seduto sul bordo della sedia) con la schiena dritta e le spalle rilassate."},
                 {"t": "Appoggia una mano sull'addome, appena sotto le costole, e l'altra su un fianco."},
                 {"t": "Mettiti a circa 30 cm dal microfono, in una stanza silenziosa."},
             ]},
            {"type": "check", "short": "Respiro basso", "title": "Trova il respiro basso",
             "how": "Inspira lentamente dal naso: la mano sull'addome deve spostarsi in fuori e i fianchi "
                    "allargarsi. Le spalle invece restano ferme, non salgono. Poi lascia uscire l'aria dalla bocca.",
             "items": [
                 {"t": "Fai 3 respiri così, con calma. Premi Avvia e respira finché finisce il tempo.", "secs": 20},
                 {"t": "Hai sentito la mano muoversi in fuori mentre inspiravi? Se sì, spunta. Se si alzavano le "
                       "spalle, rifallo pensando di «riempire la pancia»."},
             ]},
            {"type": "breath", "short": "«sss» 8 tempi", "title": "Espira su «sss» per 8 tempi",
             "beats": 8, "inhale": 4,
             "how": TEMPO + "Prima inspiri dal naso per 4 tempi (4 secondi). Poi fai uscire l'aria tra i denti "
                    "facendo «sss», come uno pneumatico che si sgonfia piano, per 8 tempi (8 secondi). "
                    "«Flusso costante» vuol dire che l'«sss» resta uguale dall'inizio alla fine: "
                    "né più forte né più debole, e senza pause.",
             "check": "L'app ascolta il tuo «sss»: ogni tempo in cui lo sente diventa un quadratino verde "
                      "(arancione se è debole o a tratti). La barra mostra la forza del flusso: deve restare "
                      "ferma dentro la fascia verde. Superi l'esercizio se arrivi in fondo con un flusso regolare.",
             "next": "Superato! Ora prova con 12 tempi."},
            {"type": "breath", "short": "«sss» 12 tempi", "title": "Espira su «sss» per 12 tempi",
             "beats": 12, "inhale": 4,
             "how": "Come prima, ma più lungo: 4 tempi per inspirare e 12 tempi (12 secondi) di «sss». "
                    "Il trucco è far uscire meno aria all'inizio, così ne resta per la fine.",
             "check": "Stessi quadratini e stessa barra: tutti verdi e barra ferma vuol dire che dosi bene il fiato.",
             "next": "Superato! Ultimo livello: 16 tempi."},
            {"type": "breath", "short": "«sss» 16 tempi", "title": "Espira su «sss» per 16 tempi",
             "beats": 16, "inhale": 4,
             "how": "Il livello più difficile: 16 secondi di «sss» costante. Inspira bene in basso e parti piano. "
                    "Se non ci arrivi subito è normale: con qualche giorno di allenamento il fiato si allunga.",
             "check": "Arrivare a 16 tempi con un flusso regolare vuol dire avere un buon controllo del fiato "
                      "per frasi lunghe.",
             "next": "Ottimo controllo del fiato! Ripeti questo esercizio ogni giorno prima di cantare."},
        ],
    },
    {
        "id": "postura", "title": "Postura",
        "intro": "Il corpo è lo strumento: una postura rilassata lascia passare il suono.",
        "acts": [
            {"type": "check", "short": "Allinea il corpo", "title": "Allinea il corpo",
             "how": "Segui i passi uno alla volta, davanti a uno specchio se puoi.",
             "items": [
                 {"t": "Piedi alla larghezza delle spalle, peso su entrambi i piedi, ginocchia morbide (non bloccate)."},
                 {"t": "Alza le spalle verso le orecchie, tienile su 3 secondi, poi lasciale cadere giù e indietro.", "secs": 3},
                 {"t": "Collo lungo e mento parallelo al pavimento: immagina un filo che ti tira su dalla testa."},
                 {"t": "Mascella sciolta: apri piano la bocca come all'inizio di uno sbadiglio e resta così.", "secs": 5},
             ]},
            {"type": "sustain", "short": "Nota ferma", "title": "Prova: una nota ferma", "secs": 5, "syll": "a",
             "how": "Con questa postura, canta una «a» su una nota comoda (né alta né bassa) e tienila per 5 secondi.",
             "check": "L'app disegna la tua nota come una linea: se resta dentro la fascia verde, la voce è stabile. "
                      "Una postura rilassata
