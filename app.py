"""Interfaccia Streamlit sopra il modello. Si avvia con:  streamlit run app.py"""
import dataclasses
import math
import streamlit as st
from modello import risolvi, G, fattore_attrito, area_cerchio
from dati import PRESE, impianto
from schema import disegna_rete, disegna_intrappolamento, grafici_occlusione, n

# --- tabelle colorate: intestazione in alto beige, colonna delle etichette azzurra, colonne alternate bianco/grigio
BEIGE, AZZURRO, GRIGIO, ROSSO, BORDO, TESTO = "#F3E7CF", "#DCEBF7", "#F1F2F4", "#B42318", "#D0D5DB", "#1F2933"


def tabella(intestazioni, righe, allinea="center"):
    """intestazioni: titoli delle colonne (il primo e' quello della colonna delle etichette).
    righe: lista di (etichetta, [celle]); una cella e' un testo, oppure (testo, True) per evidenziarla in rosso."""
    cella = f"padding: 8px 10px; border: 1px solid {BORDO}; color: {TESTO}; vertical-align: middle;"
    html = '<table style="border-collapse: collapse; width: 100%; font-size: 14px; line-height: 1.4; margin-bottom: 8px">'
    html += "<tr>" + "".join(f'<th style="{cella} background: {BEIGE}; text-align: center">{h}</th>' for h in intestazioni) + "</tr>"
    for etichetta, celle in righe:
        html += f'<tr><th style="{cella} background: {AZZURRO}; text-align: left; font-weight: 600">{etichetta}</th>'
        for j, c in enumerate(celle):
            testo, rosso = c if isinstance(c, tuple) else (c, False)
            sfondo = "#FFFFFF" if j % 2 == 0 else GRIGIO
            extra = f" color: {ROSSO}; font-weight: 700;" if rosso else ""
            html += f'<td style="{cella} background: {sfondo}; text-align: {allinea};{extra}">{testo}</td>'
        html += "</tr>"
    st.markdown(html + "</table>", unsafe_allow_html=True)


st.set_page_config(page_title="Pompa con due prese", layout="wide")
st.title("Pompa con due prese di aspirazione")
st.markdown(
    "Il modello mostra il funzionamento di una pompa di aspirazione: il sistema presenta **due prese di fondo**, collegate in parallelo "
    "a un **collettore** (il tubo in cui i due rami si uniscono prima della pompa), che aspirano l'acqua della vasca. "
    "Ciascuna presa è formata dagli elementi descritti nel Capitolo 3: griglia, pozzetto, tubazione di ramo con le sue curve, "
    "valvola di intercettazione e innesto nel collettore.\n\n"
    "Il calcolo descrive l'impianto **a regime**, cioè quando portate e pressioni non cambiano nel tempo, e tratta "
    "ogni elemento come un ostacolo che fa perdere all'acqua un po' di pressione; non calcola il moto dell'acqua punto "
    "per punto. I dati sono **di esempio**: la griglia 250 × 250 mm viene dalla scheda generica di un rivenditore, mentre "
    "i limiti di velocità sono stati trascritti dalle bozze delle norme e vanno confermati sul testo.\n\n"
    "**Sezioni:** 1 condizioni di verifica · 2 caso scelto con i controlli · 3 intrappolamento · "
    "4 dimensioni e dati dell'impianto · 5 formule usate."
)

# --- stato del filtro: da appena lavato (0) a da lavare (incremento massimo prima del controlavaggio)
st.subheader("Stato del filtro")
incr_max = float(impianto.dp_filtro_incremento)
incremento = st.slider("Intasamento del filtro: perdita di pressione aggiuntiva [kPa]", 0.0, incr_max, 0.0, 1.0)
st.caption(
    "Trattenendo le impurità il filtro si intasa: i suoi passaggi si restringono e la perdita di pressione attraverso di esso aumenta. "
    "Di conseguenza, a parità di pompa, il circuito lavora a una portata minore e con essa diminuiscono le velocità attraverso le griglie "
    "e nei tubi di aspirazione (la piscina però viene filtrata di meno, per questo il filtro va lavato). "
    "Il cursore va quindi da 0 kPa, filtro appena lavato, con portata massima e dunque caso peggiore per le velocità alla griglia e per la "
    f"depressione, fino a {n(incr_max, 0)} kPa, filtro da lavare, cioè l'aumento massimo della perdita di pressione prima del controlavaggio "
    "(bozza §3.6, da verificare sul testo della norma); i valori intermedi rappresentano un filtro più o meno intasato."
)
imp = dataclasses.replace(impianto, dp_filtro_incremento=incremento)

# =============================================================================
# 1. LE CONDIZIONI DI VERIFICA
# =============================================================================
CASI = [
    ("Entrambe le prese libere", [0.0, 0.0], [True, True]),
    ("Presa 1 occlusa al 50 %", [0.5, 0.0], [True, True]),
    ("Presa 1 completamente occlusa", [1.0, 0.0], [True, True]),
    ("Presa 1 esclusa (valvola chiusa)", [0.0, 0.0], [False, True]),
]
ris = [risolvi(PRESE, imp, occl, aperte, True) for _, occl, aperte in CASI]
vg_max, vt_max = imp.v_griglia_max, imp.v_aspirazione_max
r3, r4 = ris[2], ris[3]


def presa(r, j):
    return r["prese"][j]


def limiti(r):
    return "; ".join(r["limiti_superati"]).replace("velocita'", "velocità")


st.header("1. Le condizioni di verifica")
st.markdown(
    "- **Entrambe le prese libere.** Funzionamento normale: la portata si divide fra le due prese in base alla "
    "resistenza di ciascun ramo. Abbiamo supposto due rami di lunghezza diversa, quindi la ripartizione non è uniforme.\n"
    "- **Presa 1 occlusa al 50 %.** Metà della superficie libera della griglia 1 è coperta; la presa 2 resta libera. "
    "L'acqua della presa 1 passa da un'area dimezzata: la velocità attraverso la griglia 1 circa raddoppia, mentre "
    "la portata cambia poco.\n"
    "- **Presa 1 completamente occlusa.** Un corpo copre tutta la griglia 1 e la valvola del ramo 1 resta aperta. "
    "Dalla presa 1 non passa acqua e tutta la portata va sulla presa 2, dove le velocità aumentano. Il pozzetto 1 "
    "resta collegato alla pompa: sotto il corpo la pressione scende (depressione) e il corpo viene premuto sulla "
    "griglia. È la condizione di intrappolamento.\n"
    "- **Presa 1 esclusa (valvola del ramo 1 chiusa).** Ogni ramo ha una valvola di intercettazione che in esercizio "
    "è aperta (condizioni precedenti). Chiudendola, ad esempio per manutenzione, il gestore esclude la presa 1: la griglia "
    "è libera, ma l'acqua non passa. È la verifica della *presa esclusa*: la presa rimasta deve reggere da sola tutta la portata."
)

st.subheader("Risultato delle quattro condizioni")
tabella(
    ["Grandezza"] + [c[0] for c in CASI],
    [
        ("Portata totale della pompa [m³/h]", [n(r["Q_h"], 1) for r in ris]),
        ("Portata presa 1 [m³/h]", [n(presa(r, 0)["Q_h"], 1) for r in ris]),
        ("Portata presa 2 [m³/h]", [n(presa(r, 1)["Q_h"], 1) for r in ris]),
        ("Ripartizione [%]", [f"Presa 1: {n(presa(r, 0)['quota'], 0)} %<br>Presa 2: {n(presa(r, 1)['quota'], 0)} %" for r in ris]),
        ("Velocità attraverso la griglia 1 [m/s]", [(n(presa(r, 0)["v_griglia"]), presa(r, 0)["v_griglia"] > vg_max) for r in ris]),
        ("Velocità attraverso la griglia 2 [m/s]", [(n(presa(r, 1)["v_griglia"]), presa(r, 1)["v_griglia"] > vg_max) for r in ris]),
        ("Velocità nel tubo del ramo 1 [m/s]", [(n(presa(r, 0)["v_tubo"]), presa(r, 0)["v_tubo"] > vt_max) for r in ris]),
        ("Velocità nel tubo del ramo 2 [m/s]", [(n(presa(r, 1)["v_tubo"]), presa(r, 1)["v_tubo"] > vt_max) for r in ris]),
        ("Depressione nel pozzetto 1 [kPa]", [n(presa(r, 0)["depr_pozzetto_kPa"]) for r in ris]),
        ("Depressione nel pozzetto 2 [kPa]", [n(presa(r, 1)["depr_pozzetto_kPa"]) for r in ris]),
        ("Limiti superati", [(limiti(r), True) if r["limiti_superati"] else "nessuno" for r in ris]),
    ],
)
quota_griglia = 100 * presa(ris[0], 0)["perdite"]["griglia"] / ris[0]["dh_nodo"]
st.markdown(
    f"**Come leggere la tabella.** Ogni colonna è una condizione e ogni riga una grandezza; in rosso compaiono i valori oltre "
    f"i limiti inseriti ({n(vg_max)} m/s attraverso la griglia, {n(vt_max, 1)} m/s nel tubo di aspirazione). "
    "Le due velocità si calcolano in modo diverso: quella *attraverso la griglia* divide la portata della presa per la superficie "
    "libera rimasta aperta, mentre quella *nel tubo* dipende solo dalla portata del ramo e dal suo diametro. Per questo, passando "
    "dalla condizione 1 alla 2, la velocità alla griglia aumenta molto e quella nel tubo poco: la griglia pesa soltanto per circa il "
    f"{n(quota_griglia, 0)} % sulla resistenza del ramo, quindi coprirne metà riduce la portata solo di qualche punto. "
    "La *depressione nel pozzetto* è invece quanto la pressione sotto la griglia scende rispetto a quella dell'acqua alla "
    "stessa profondità. Infine la *ripartizione* non è un dato del fabbricante, ma è calcolata dal modello perché i due rami, "
    "in parallelo sullo stesso collettore, perdono lo stesso carico; la portata massima del fabbricante serve solo come limite "
    "di confronto. Le formule sono nella sezione 5."
)

# =============================================================================
# 2. CASO SCELTO CON I CONTROLLI
# =============================================================================
st.header("2. Caso scelto con i controlli")
st.markdown("Qui si può esplorare una situazione intermedia, occludendo anche la seconda presa.")
c1, c2, c3 = st.columns(3)
occl_1 = c1.slider("Occlusione della griglia della presa 1 (%)", 0.0, 100.0, 50.0, 0.5)
occl_2 = c2.slider("Occlusione della griglia della presa 2 (%)", 0.0, 100.0, 0.0, 0.5)
esclusa_1 = c3.checkbox("Presa 1 esclusa (valvola del ramo 1 chiusa)")

occlusioni = [occl_1 / 100, occl_2 / 100]
aperte = [not esclusa_1, True]
r = risolvi(PRESE, imp, occlusioni, aperte, True)
p1, p2 = r["prese"]

st.subheader("Schema della rete")
st.pyplot(disegna_rete(r, occlusioni, aperte, incremento > 0, imp, PRESE))
st.caption("I numeri nei cerchi identificano gli elementi elencati nella legenda. Lo spessore dell'acqua nei tubi è proporzionale alla portata; "
           "la parte tratteggiata della griglia è libera, quella grigia è occlusa; la valvola nera è chiusa.")

m = st.columns(4)
m[0].metric("Portata totale", f"{n(r['Q_h'], 1)} m³/h")
m[1].metric("Portata presa 1", f"{n(p1['Q_h'], 1)} m³/h", f"{n(p1['quota'], 1)} % del totale", delta_color="off")
m[2].metric("Portata presa 2", f"{n(p2['Q_h'], 1)} m³/h", f"{n(p2['quota'], 1)} % del totale", delta_color="off")
m[3].metric("Differenza presa 2 − presa 1", f"{n(p2['Q_h'] - p1['Q_h'], 1)} m³/h")
m = st.columns(4)
m[0].metric("Velocità griglia 1", f"{n(p1['v_griglia'])} m/s")
m[1].metric("Velocità griglia 2", f"{n(p2['v_griglia'])} m/s")
m[2].metric("Depressione pozzetto 1", f"{n(p1['depr_pozzetto_kPa'])} kPa")
m[3].metric("Depressione pozzetto 2", f"{n(p2['depr_pozzetto_kPa'])} kPa")
if r["limiti_superati"]:
    st.error("Limiti superati: " + limiti(r))
else:
    st.success("Tutte le velocità e le portate sono entro i limiti inseriti.")
if max(p1["depr_pozzetto_kPa"], p2["depr_pozzetto_kPa"]) > 100:
    st.warning("Con entrambe le prese occluse la pompa lavora a portata nulla e il modello dà una depressione che non è fisicamente "
               "raggiungibile (oltre circa 100 kPa si arriva al vuoto). Il modello non include il limite del vuoto né la cavitazione: "
               "questo valore va letto solo come \"depressione massima teorica\".")


@st.cache_data(show_spinner=False)
def andamento(occl_2_pct, incremento_kpa):
    """Portate, velocita' alla griglia 1 e 2 e depressione del pozzetto 1 al crescere dell'occlusione della presa 1."""
    imp_a = dataclasses.replace(impianto, dp_filtro_incremento=incremento_kpa)
    xs = [float(o) for o in range(0, 100, 5)] + [97.0, 98.0, 99.0, 99.5, 99.9, 100.0]
    d = {"x": xs, "q1": [], "q2": [], "vg1": [], "vg2": [], "dp1": []}
    for x in xs:
        ro = risolvi(PRESE, imp_a, [x / 100, occl_2_pct / 100], [True, True], True)
        a, b = ro["prese"]
        d["q1"].append(a["Q_h"])
        d["q2"].append(b["Q_h"])
        d["dp1"].append(a["depr_pozzetto_kPa"])
        d["vg1"].append(a["v_griglia"] if x < 100 else float("nan"))   # a 100 % non resta nessuna apertura
        d["vg2"].append(b["v_griglia"] if occl_2_pct < 100 else float("nan"))
    return d


st.subheader("Andamento di portata, velocità e depressione al crescere dell'occlusione della presa 1")
st.caption("La presa 2 resta all'occlusione scelta con il secondo cursore; il filtro è nello stato scelto in alto. "
           "Su ogni curva i punti segnati riportano (occlusione della griglia 1 in %; valore); la linea tratteggiata verticale è "
           "l'occlusione scelta con il cursore.")
d = andamento(occl_2, incremento)
f_q, f_v, f_d = grafici_occlusione(d, vg_max, occl_1)
g1, g2 = st.columns(2)
g1.pyplot(f_q)
g2.pyplot(f_v)
_, g3, _ = st.columns([1, 2, 1])
g3.pyplot(f_d)

st.subheader("Differenza fra la condizione 3 e la condizione 4")
st.markdown("Le portate sono identiche, perché in entrambe dalla presa 1 non passa acqua: cambia **dove si trova lo sbarramento** "
            "e quindi se il pozzetto 1 è collegato al collettore e alla pompa.")
tabella(
    ["", "Condizione 3: presa 1 completamente occlusa", "Condizione 4: presa 1 esclusa (valvola chiusa)"],
    [
        ("Configurazione", ["Un corpo copre la griglia 1; la valvola del ramo 1 è aperta.",
                            "Il gestore chiude la valvola del ramo 1; la griglia 1 è libera."]),
        ("Portata della presa 1", [f"{n(presa(r3, 0)['Q_h'], 1)} m³/h", f"{n(presa(r4, 0)['Q_h'], 1)} m³/h"]),
        ("Portata della presa 2", [f"{n(presa(r3, 1)['Q_h'], 1)} m³/h", f"{n(presa(r4, 1)['Q_h'], 1)} m³/h"]),
        ("Pozzetto 1 collegato alla pompa?", ["Sì, attraverso il ramo con la valvola aperta.", "No, la valvola chiusa lo isola."]),
        ("Pressione sotto la griglia 1", [f"{n(presa(r3, 0)['depr_pozzetto_kPa'])} kPa più bassa di quella della vasca.",
                                          "Uguale a quella della vasca, a regime (0 kPa)."]),
        ("Un corpo sulla griglia 1 verrebbe trattenuto?", ["Sì: la differenza di pressione lo preme contro la griglia.",
                                                           "No, a regime: non c'è differenza di pressione "
                                                           "(il transitorio di scarica della depressione non è calcolato)."]),
        ("Che cosa si verifica", ["L'intensità della depressione e, da essa, la forza di trattenimento (sezione 3).",
                                  "Che la presa 2 regga da sola tutta la portata (velocità alla griglia 2 e nel tubo 2)."]),
        ("Situazione reale", ["Scenario di incidente.", "Manovra del gestore, ad esempio per manutenzione."]),
    ],
    allinea="left",
)

# =============================================================================
# 3. INTRAPPOLAMENTO
# =============================================================================
st.header("3. Intrappolamento")
dp_libera = presa(ris[0], 0)["depr_pozzetto_kPa"]
dp_50 = presa(ris[1], 0)["depr_pozzetto_kPa"]
dp_90 = risolvi(PRESE, imp, [0.9, 0.0], [True, True], True)["prese"][0]["depr_pozzetto_kPa"]
dp_3 = presa(r3, 0)["depr_pozzetto_kPa"]
dh_3 = r3["dh_nodo"]
A_g = PRESE[0].A_ingombro
forza = dp_3 * 1000 * A_g

st.markdown(
    "L'intrappolamento da aspirazione può verificarsi quando una persona ostruisce con il proprio corpo una griglia di aspirazione "
    "della piscina, impedendo il normale passaggio dell'acqua. Per comprendere come si sviluppa questo fenomeno, occorre partire dal "
    "funzionamento dell'impianto. Durante il normale esercizio, la pompa mantiene nel circuito di aspirazione una pressione inferiore "
    "a quella presente nella vasca. Questa differenza di pressione consente all'acqua di attraversare le griglie e raggiungere la pompa, "
    "per essere successivamente trattata e reimmessa in piscina."
)
st.markdown(
    "Quando la griglia è completamente libera, l'acqua riesce a entrare senza incontrare ostacoli rilevanti e la differenza di pressione "
    "necessaria a mantenerne il movimento è relativamente contenuta. Nell'esempio considerato, con il filtro nello stato scelto in alto, "
    f"tale differenza è pari a circa {n(dp_libera)} kPa. La situazione cambia quando una persona si avvicina alla griglia e comincia a "
    "coprirne le aperture con il proprio corpo. La superficie disponibile per il passaggio dell'acqua si riduce progressivamente e, di "
    "conseguenza, aumenta la resistenza all'aspirazione. La pressione all'interno del pozzetto può quindi diminuire rispetto a quella "
    "della vasca, mentre la pompa continua a funzionare."
)
st.markdown(
    "Il fenomeno diventa particolarmente pericoloso quando il corpo copre completamente la griglia, creando una tenuta che impedisce "
    "all'acqua di attraversarla. In questa condizione, rappresentata nello schema qui sotto come condizione 3, la portata attraverso la "
    "presa ostruita si annulla. Tuttavia, poiché il ramo rimane collegato al collettore di aspirazione attraverso una valvola aperta, la "
    "pressione ridotta presente nel circuito può continuare a trasmettersi fino al pozzetto, anche in assenza di movimento dell'acqua "
    "attraverso la griglia. La pompa, nel frattempo, continua a ricevere acqua dalla seconda presa, che rimane libera."
)
st.markdown(
    "Si crea così una differenza di pressione tra le due facce del corpo. La superficie rivolta verso la piscina è sottoposta alla "
    "pressione dell'acqua della vasca, mentre quella a contatto con la griglia risente della pressione inferiore presente nel pozzetto. "
    "Questa differenza genera una forza che spinge il corpo contro la griglia e può impedirne il distacco, producendo un effetto simile "
    "a quello di una ventosa."
)
st.pyplot(disegna_intrappolamento(r3, r4, A_g))
st.caption("Schema non in scala. Arancione = pressione più bassa di quella della vasca (più scuro = differenza maggiore); azzurro = pressione "
           "uguale a quella della vasca. Frecce blu: pressione dell'acqua sul corpo; frecce verdi: acqua aspirata dalla presa 2.")
st.markdown(
    f"Nell'esempio analizzato il modello dà una differenza di pressione di {n(dp_3, 1)} kPa, corrispondente a circa {n(dh_3, 2)} metri di "
    "colonna d'acqua: è la perdita di carico che l'acqua subisce, nel ramo della presa 2 rimasta libera, per arrivare dalla vasca al "
    f"collettore. Supponendo che il corpo ostruisca una superficie di {n(A_g * 1e4, 0)} cm², pari a {n(A_g, 4)} m², la forza di "
    "trattenimento può essere stimata moltiplicando la differenza di pressione per l'area interessata:"
)
dp_Pa_tex = format(round(dp_3 * 1000), ",").replace(",", r"\,")   # 14490 -> 14\,490
A_tex = n(A_g, 4).replace(",", "{,}")                              # 0,0625 -> 0{,}0625
st.latex(rf"F = \Delta p \cdot A = {dp_Pa_tex} \cdot {A_tex} \approx {round(forza)}\ \text{{N}}")
st.markdown(
    f"Il risultato corrisponde a circa {n(forza / 1000, 1)} kN, equivalenti al peso di una massa di {n(forza / G, 0)} kg. Si tratta di un "
    "ordine di grandezza, ricavato nell'ipotesi di tenuta perfetta (il modello non calcola questa forza, che dipende anche dall'area di "
    "contatto, dalla tenuta e dalla deformabilità del corpo), ma comunque di una forza considerevole, che può rendere estremamente "
    "difficile per una persona liberarsi autonomamente dalla griglia."
)
st.markdown(
    "È importante osservare che questa situazione non si manifesta necessariamente all'improvviso, ma può svilupparsi progressivamente "
    "man mano che la superficie della griglia viene ostruita. Nello scenario considerato, la differenza di pressione passa da "
    f"{n(dp_libera)} kPa con la griglia libera a {n(dp_50, 1)} kPa quando è coperta per metà, raggiunge {n(dp_90, 1)} kPa con "
    f"un'occlusione del 90 % e arriva a {n(dp_3, 1)} kPa con l'occlusione completa. Questi valori descrivono il comportamento ipotizzato "
    "per l'impianto esaminato e non devono essere considerati validi per qualsiasi piscina."
)
st.markdown(
    "Per liberare la persona intrappolata è necessario eliminare, o ridurre sufficientemente, la differenza di pressione che la trattiene "
    "contro la griglia. La condizione 4 dello schema rappresenta la chiusura della valvola del ramo, che interrompe il collegamento con il "
    "collettore di aspirazione: se la pressione nel pozzetto riesce a riequilibrarsi con quella della vasca, la forza di trattenimento si "
    "annulla e il corpo può staccarsi dalla griglia. La sola chiusura della valvola, tuttavia, non garantisce necessariamente questo "
    "risultato, perché una depressione già presente potrebbe rimanere intrappolata nel tratto isolato. Per questo motivo, i sistemi di "
    "sicurezza devono essere progettati in modo da consentire un effettivo e tempestivo rilascio della depressione. Il modello descrive "
    "solo la situazione a regime, a pressione già riequilibrata, e non il transitorio durante il quale la depressione si scarica: è un "
    "aspetto da sviluppare."
)

# =============================================================================
# 4. DIMENSIONI E DATI DELL'IMPIANTO
# =============================================================================
st.header("4. Dimensioni e dati dell'impianto")
a, b = PRESE
lato = lambda p: n(math.sqrt(p.A_ingombro) * 1000, 0)
st.markdown("**Le due prese**")
tabella(
    ["Grandezza", "Presa 1", "Presa 2", "Significato e contesto"],
    [
        ("Griglia: dimensioni esterne", [f"{lato(a)} × {lato(a)} mm", f"{lato(b)} × {lato(b)} mm",
                                         "Ingombro della griglia (griglia quadrata). Scheda generica di un rivenditore."]),
        ("Griglia: superficie libera", [f"{n(a.A_libera, 4)} m²", f"{n(b.A_libera, 4)} m²",
                                        "Somma delle aperture da cui passa l'acqua. Ricavata dalla portata massima divisa "
                                        "per 0,5 m/s: da verificare sulla scheda tecnica."]),
        ("Griglia: portata massima ammessa", [f"{n(a.Q_max_fabbricante_h, 1)} m³/h", f"{n(b.Q_max_fabbricante_h, 1)} m³/h",
                                              "Portata più alta che il fabbricante dichiara per la griglia, cioè quella "
                                              "per cui la velocità nelle aperture resta entro il limite."]),
        ("Pozzetto: lunghezza × larghezza", [f"{n(a.L_pozzetto)} × {n(a.B_pozzetto)} m", f"{n(b.L_pozzetto)} × {n(b.B_pozzetto)} m",
                                             "Vasca sotto la griglia. Esempio."]),
        ("Tubo del ramo: diametro interno", [f"{n(a.D_ramo * 1000, 0)} mm", f"{n(b.D_ramo * 1000, 0)} mm", "Esempio, uguale per i due rami."]),
        ("Tubo del ramo: lunghezza fino al collettore", [f"{n(a.L_ramo, 0)} m", f"{n(b.L_ramo, 0)} m",
                                                         "Esempio: la diversa lunghezza spiega la diversa ripartizione."]),
        ("Tubo del ramo: rugosità della parete", [f"{n(a.rugosita * 1000, 4)} mm", f"{n(b.rugosita * 1000, 4)} mm",
                                                  "PVC, valore di letteratura."]),
        ("Curve a 90° lungo il tubo del ramo", [str(a.n_curve), str(b.n_curve), "Numero di cambi di direzione. Esempio."]),
    ],
    allinea="left",
)

st.markdown(
    "**Perdite localizzate lungo il ramo.** Ogni raccordo fa perdere all'acqua una parte della sua energia pari a "
    "*K* volte l'altezza cinetica *v²/2g*. *K* è un numero puro che dipende dalla forma del raccordo; "
    "i valori sono indicativi, presi dai manuali di idraulica."
)
tabella(
    ["Elemento", "K", "Significato"],
    [
        ("Imbocco dal pozzetto nel tubo", [n(a.K_imbocco, 1), "L'acqua entra bruscamente nel tubo (imbocco a spigolo vivo)."]),
        ("Curva a 90° (ciascuna)", [n(a.K_curva, 1), "Cambio di direzione del tubo."]),
        ("Valvola di intercettazione aperta", [n(a.K_valvola, 1), "Ostacolo della valvola anche quando è tutta aperta."]),
        ("Innesto del ramo nel collettore", [n(a.K_innesto, 1), "Raccordo a T in cui la corrente del ramo si unisce alle altre."]),
    ],
    allinea="left",
)

st.markdown("**Parte comune, pompa e limiti**")
tabella(
    ["Grandezza", "Valore", "Significato e contesto"],
    [
        ("Tubo dal collettore alla pompa: diametro interno", [f"{n(impianto.D_comune * 1000, 0)} mm", "Esempio."]),
        ("Tubo dal collettore alla pompa: lunghezza", [f"{n(impianto.L_comune, 0)} m", "Esempio."]),
        (f"Perdita di pressione nel prefiltro pulito, a {n(impianto.Q_ref_h, 0)} m³/h",
         [f"{n(impianto.dp_prefiltro, 0)} kPa", "Differenza di pressione fra ingresso e uscita del cestello del prefiltro; "
                                                "cresce quando si riempie. Esempio: valore reale dalla scheda del prefiltro."]),
        (f"Perdita di pressione nel filtro appena lavato, a {n(impianto.Q_ref_h, 0)} m³/h",
         [f"{n(impianto.dp_filtro_pulito, 0)} kPa", "Esempio: valore reale dalla scheda del filtro."]),
        ("Aumento massimo della perdita del filtro prima del lavaggio",
         [f"{n(incr_max, 0)} kPa", "Bozza §3.6 (UNI 10637:2024): da verificare sul testo della norma."]),
        (f"Perdita di pressione in mandata, a {n(impianto.Q_ref_h, 0)} m³/h",
         [f"{n(impianto.dp_mandata, 0)} kPa", "Tubi di mandata, scambiatore e bocchette di immissione. Esempio."]),
        ("Pompa: prevalenza a portata nulla", [f"{n(impianto.H0, 1)} m", "Punto di partenza della curva della pompa. Esempio."]),
        ("Pompa: profondità sotto il pelo libero", [f"{n(impianto.battente_pompa, 1)} m", "Pompa sotto battente. Esempio."]),
        ("Limite di velocità attraverso la griglia", [f"{n(vg_max)} m/s", "UNI EN 13451-3 (dalla bozza §3.8): da verificare sul testo."]),
        ("Limite di velocità nel tubo di aspirazione", [f"{n(vt_max, 1)} m/s", "UNI 10637:2024 (dalla bozza §3.5): da verificare sul testo."]),
    ],
    allinea="left",
)
st.caption(f"Le perdite di prefiltro, filtro e mandata sono date alla portata di {n(impianto.Q_ref_h, 0)} m³/h "
           "e nel calcolo crescono con il quadrato della portata.")

# =============================================================================
# 5. FORMULE USATE
# =============================================================================
st.header("5. Formule usate")
st.markdown("**Velocità attraverso la griglia** — portata della presa divisa per la superficie libera rimasta aperta "
            "(β = quota della griglia occlusa, da 0 a 1):")
st.latex(r"v_{griglia} = \frac{Q_{presa}}{A_{libera}\,(1-\beta)} \quad [\mathrm{m/s}]")
st.markdown("**Velocità nel tubo del ramo** — portata del ramo divisa per la sezione del tubo:")
st.latex(r"v_{tubo} = \frac{Q_{presa}}{\pi D^2 / 4} \quad [\mathrm{m/s}]")
st.markdown("**Perdite lungo il ramo** — ogni raccordo e l'attrito del tubo fanno perdere un'altezza di carico "
            "(λ con la formula di Swamee–Jain; la griglia con la formula di Idel'chik per griglie sottili, "
            "riferita alla velocità di avvicinamento *Q/A_ingombro*):")
st.latex(r"h = K \frac{v^2}{2g} \qquad h_{attrito} = \lambda \frac{L}{D} \frac{v^2}{2g} \qquad "
         r"K_{griglia} = \frac{\left(0{,}707\sqrt{1-f} + 1 - f\right)^2}{f^2},\; f = \frac{A_{libera}}{A_{ingombro}}(1-\beta)")
st.markdown("**Ripartizione** — le due prese partono dallo stesso pelo libero e arrivano allo stesso collettore, "
            "quindi perdono lo stesso carico Δh; la pompa fornisce la prevalenza che serve a tutto il circuito:")
st.latex(r"h_1(Q_1) = h_2(Q_2) = \Delta h_N, \qquad Q_1 + Q_2 = Q, \qquad H_0 - a\,Q^2 = \Delta h_N + h_{comune}(Q)")
st.markdown("**Depressione nel pozzetto** — differenza fra la pressione dell'acqua alla stessa profondità e quella "
            "sotto la griglia:")
st.latex(r"\Delta p = \rho g \left(h_{griglia} + \frac{v_{pozzetto}^2}{2g}\right) \;\text{presa che lavora}, \qquad "
         r"\Delta p = \rho g\, \Delta h_N \;\text{griglia coperta}, \qquad \Delta p = 0 \;\text{valvola chiusa}")

p3 = presa(r3, 1)
pp = p3["perdite"]
pr = PRESE[1]
q3 = p3["Q_h"] / 3600
A_t = area_cerchio(pr.D_ramo)
v3 = q3 / A_t
hv3 = v3 ** 2 / (2 * G)
lam3 = fattore_attrito(imp.rho * v3 * pr.D_ramo / imp.mu, pr.rugosita, pr.D_ramo)
sumK = pr.K_imbocco + pr.n_curve * pr.K_curva + pr.K_valvola + pr.K_innesto
h_racc = pp["imbocco"] + pp["curve"] + pp["valvola"] + pp["innesto"]
h_tot = sum(pp.values())
dp_calc = imp.rho * G * h_tot / 1000
st.markdown("**Verifica a mano: presa 1 completamente occlusa (condizione 3).** Si calcola quanto carico perde l'acqua che passa "
            "dalla presa 2, perché quello è anche il carico che sente il pozzetto 1 sotto il corpo.")
tabella(
    ["Passo", "Che cosa calcolo", "Come", "Risultato"],
    [
        ("1", ["Portata nel ramo 2, in m³/s", f"{n(p3['Q_h'], 2)} m³/h ÷ 3600", f"{n(q3, 5)} m³/s"]),
        ("2", ["Velocità nel tubo", f"portata ÷ sezione = {n(q3, 5)} ÷ {n(A_t, 5)} m²", f"{n(v3, 3)} m/s"]),
        ("3", ["Altezza cinetica, v²/2g", f"{n(v3, 3)}² ÷ (2 × 9,81)", f"{n(hv3, 4)} m"]),
        ("4", ["Perdita nei raccordi", f"K totale = {n(pr.K_imbocco, 1)} (imbocco) + {pr.n_curve} × {n(pr.K_curva, 1)} (curve) + "
                                      f"{n(pr.K_valvola, 1)} (valvola) + {n(pr.K_innesto, 1)} (innesto) = {n(sumK, 1)}; "
                                      f"{n(sumK, 1)} × {n(hv3, 4)} m", f"{n(h_racc, 3)} m"]),
        ("5", ["Perdita per attrito nel tubo", f"λ × L/D × v²/2g = {n(lam3, 5)} × {n(pr.L_ramo / pr.D_ramo, 0)} × {n(hv3, 4)} m", f"{n(pp['tubo'], 3)} m"]),
        ("6", ["Perdita nella griglia", "K griglia × (Q/A ingombro)² / 2g, con la formula di Idel'chik", f"{n(pp['griglia'], 3)} m"]),
        ("7", ["Perdita totale del ramo 2 = carico del collettore", "passo 4 + passo 5 + passo 6", f"{n(h_tot, 3)} m"]),
        ("8", ["Da metri a pressione", f"ρ × g × carico = {n(imp.rho, 1)} × 9,81 × {n(h_tot, 3)} m", f"{n(dp_calc, 2)} kPa"]),
    ],
    allinea="left",
)
st.markdown(
    f"Il pozzetto 1, collegato al collettore e senza acqua che scorre, prende quella pressione: **{n(dp_calc, 2)} kPa di depressione**. "
    f"Il modello dà {n(presa(r3, 0)['depr_pozzetto_kPa'], 2)} kPa: i due numeri coincidono."
)

st.markdown(
    "**Approssimazioni.** Regime stazionario (nessun transitorio, ad esempio all'avvio o all'arresto della pompa); "
    "coefficienti K indicativi di letteratura; griglia sottile con aperture distribuite in modo uniforme e occlusione "
    "uniforme; velocità medie sulle sezioni (vicino al raccordo d'uscita la velocità reale nelle aperture è più alta); "
    "λ da Swamee–Jain, che approssima la formula di Colebrook; perdite di prefiltro, filtro e mandata scalate con "
    "(Q/Q_ref)²; curva della pompa parabolica; pelo libero comune alle due prese; pozzetto e collettore alla stessa quota; "
    "nessun limite di vuoto né cavitazione. La forza sul corpo non è calcolata: la stima Δp × area è solo un ordine di grandezza "
    "e dipende da area di contatto, tenuta e deformabilità."
)