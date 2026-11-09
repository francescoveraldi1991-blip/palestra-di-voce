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
                      "Una postura rilassata aiuta la nota a restare ferma.",
             "next": "Bene: con il corpo allineato la voce è stabile."},
            {"type": "check", "short": "Allo specchio", "title": "Controllo allo specchio",
             "how": "Ora canta qualche nota guardandoti allo specchio.",
             "items": [
                 {"t": "Mentre canti, spalle e collo restano fermi e rilassati?"},
                 {"t": "Il mento resta dritto anche sulle note più alte? Se si alza, riabbassalo e riprova."},
             ]},
        ],
    },
    {
        "id": "riscaldamento", "title": "Riscaldamento",
        "intro": "Cinque-dieci minuti prima di cantare proteggono la voce e la rendono più agile.",
        "acts": [
            {"type": "siren", "short": "Sirena", "title": "Trillo di labbra a sirena", "secs": 8,
             "how": "Chiudi le labbra morbide e soffia facendole vibrare («brrr»), come un motorino. Mentre vibrano, "
                    "aggiungi la voce: parti da una nota bassa, sali piano più in alto che puoi senza sforzo, "
                    "poi torna giù. Come una sirena. Hai 8 secondi.",
             "check": "L'app disegna la tua sirena: più ampia è la curva, più note hai scaldato. Superi l'esercizio "
                      "se copri almeno 7 semitoni. Se il trillo non parte, va bene anche «vvv» o «mmm».",
             "next": "Bene, voce scaldata! Ora l'humming."},
            {"type": "sustain", "short": "Humming «mmm»", "title": "Humming su «mmm»", "secs": 6, "syll": "mmm",
             "how": "A bocca chiusa, con i denti leggermente separati, fai «mmm» su una nota comoda per 6 secondi. "
                    "Devi sentire vibrare labbra e naso.",
             "check": "L'app controlla che la nota resti ferma dentro la fascia verde per tutti i 6 secondi.",
             "next": "Perfetto. Ultimo passo: la scala."},
            {"type": "check", "short": "Scala", "title": "Scala a cinque note",
             "how": "Per finire il riscaldamento, usa il percorso guidato degli esercizi.",
             "items": [
                 {"t": "Apri la scheda Esercizi e scegli «Scala a cinque note»."},
                 {"t": "Segui il percorso guidato: ascolta, canta con la guida, canta da solo."},
                 {"t": "Quando lo superi, sali di mezzo tono una o due volte e poi torna alle note centrali."},
             ]},
        ],
    },
    {
        "id": "intonazione", "title": "Intonazione",
        "intro": "Intonare vuol dire ascoltare prima di cantare: l'orecchio si allena come un muscolo.",
        "acts": [
            {"type": "echo", "short": "Gioco dell'eco", "title": "Gioco dell'eco", "rounds": 5, "low": 52,
             "how": "L'app suona una nota. Ascoltala, immaginala in testa, poi cantala su «la» quando leggi "
                    "«Tocca a te». Puoi cantarla anche un'ottava sopra o sotto: va bene lo stesso. Sono 5 note.",
             "check": "Dopo ogni nota il quadratino diventa verde ✓ se eri giusto, arancione se eri sotto (↑) o "
                      "sopra (↓). «Giusto» vuol dire entro 35 cents (100 cents sono mezzo tono). "
                      "Superi il gioco con almeno 4 note su 5.",
             "next": "Ottimo orecchio! Ora tieni ferma una nota."},
            {"type": "sustain", "short": "Nota ferma", "title": "Tieni la nota ferma", "secs": 6, "syll": "a",
             "how": "Scegli una nota comoda e cantala su «a» per 6 secondi, cercando di non farla salire né scendere.",
             "check": "La linea della tua voce deve restare dentro la fascia verde: vuol dire che resti sulla stessa nota.",
             "next": "Bene! Ora passa all'«Arpeggio maggiore» negli Esercizi."},
            {"type": "check", "short": "Prossimo passo", "title": "Prossimo passo",
             "how": "Continua con gli esercizi guidati.",
             "items": [
                 {"t": "Nella scheda Esercizi prova l'«Arpeggio maggiore» con il percorso guidato."},
                 {"t": "Rigioca al gioco dell'eco ogni giorno: è il modo più veloce per allenare l'orecchio."},
             ]},
        ],
    },
    {
        "id": "canzone", "title": "Imparare una canzone",
        "intro": "Una canzone si impara a pezzi, non tutta insieme.",
        "acts": [
            {"type": "check", "short": "Prepara la canzone", "title": "Prepara la canzone",
             "how": "Metti nell'app la canzone che vuoi imparare.",
             "items": [
                 {"t": "Nel Karaoke premi «Nuova canzone»: incolla il link di un video karaoke oppure carica un file .kar."},
                 {"t": "Se hai solo la base, crea la melodia in «Le mie canzoni» con «Crea la melodia cantandola»."},
                 {"t": "Controlla in «Le mie canzoni» che la canzone rientri nella tua estensione; se no, usa la trasposizione."},
             ]},
            {"type": "check", "short": "Frase per frase", "title": "Studia una frase alla volta",
             "how": "In «Le mie canzoni» scegli una frase sola e lavora così:",
             "items": [
                 {"t": "Ascoltala con «Solo ascolto» due volte."},
                 {"t": "Cantala con la guida, a velocità 70%, con «Ripeti» attivo, finché arrivi all'80%."},
                 {"t": "Togli la guida e cantala da sola."},
                 {"t": "Passa alla frase successiva, poi unisci due frasi insieme."},
             ]},
            {"type": "check", "short": "Canta tutto", "title": "Canta tutta la canzone",
             "how": "Quando le frasi vengono bene, mettile insieme.",
             "items": [
                 {"t": "Canta tutta la canzone con la guida a velocità 100%."},
                 {"t": "Cantala nel Karaoke sulla base vera, in cuffia."},
                 {"t": "Guarda nella scheda Progressi se il punteggio sale giorno dopo giorno."},
             ]},
        ],
    },
    {
        "id": "salute", "title": "Salute della voce",
        "intro": "Una voce allenata è una voce che non si sforza.",
        "acts": [
            {"type": "check", "short": "Abitudini", "title": "Le buone abitudini",
             "how": "Spunta le abitudini che hai già. Le altre sono il tuo prossimo obiettivo.",
             "items": [
                 {"t": "Bevo acqua durante la giornata, non solo mentre canto."},
                 {"t": "Mi alleno poco ma spesso: 15-20 minuti al giorno."},
                 {"t": "Mi riscaldo sempre prima di cantare (lezione «Riscaldamento»)."},
                 {"t": "Non urlo e non canto quando la voce è stanca o rauca."},
             ]},
            {"type": "check", "short": "Segnali", "title": "I segnali per fermarsi",
             "how": "Leggi questi segnali e spunta quando li hai capiti.",
             "items": [
                 {"t": "Se senti dolore, bruciore o la voce si «graffia», fermati e riposa."},
                 {"t": "Se la raucedine dura più di due settimane, parlane con un medico."},
             ]},
        ],
    },
]
