"""Figure e blocchi dell'app: schema della rete, intrappolamento, grafici dell'occlusione, percorso dell'acqua.
Usa i risultati di modello.risolvi(); nessuna di queste funzioni fa calcoli idraulici nuovi:
mostra i numeri del modello (o ne ricava le quantita' intermedie con le stesse funzioni di modello.py)."""
import math
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, Circle, Polygon, FancyArrow, FancyBboxPatch
from modello import G, area_cerchio, fattore_attrito, K_griglia, perdite_comune

COLORI = ["#2563eb", "#ea580c", "#16a34a"]   # presa 1, presa 2, parte comune
TESTO, TESTO_CHIARO, BORDO = "#1F2933", "#6B7280", "#E5E7EB"
BASSA, ALTA = "#fb923c", "#7dd3fc"           # pressione piu' bassa della vasca / uguale a quella della vasca


def n(x, dec=2):
    """Numero in formato italiano (virgola decimale)."""
    if x != x:  # nan
        return "-"
    return f"{x:.{dec}f}".replace(".", ",")


# =============================================================================
# 1. SCHEMA DELLA RETE (con i numeri degli elementi)
# =============================================================================
def _tubo(ax, xs, ys, Q_h, Q_ref_h, colore):
    """Un tubo: bordo scuro, interno chiaro e, se c'e' portata, acqua di spessore proporzionale a Q."""
    ax.plot(xs, ys, color="#334155", lw=11, solid_capstyle="butt", solid_joinstyle="round", zorder=2)
    ax.plot(xs, ys, color="white", lw=8, solid_capstyle="butt", solid_joinstyle="round", zorder=3)
    if Q_h > 0:
        ax.plot(xs, ys, color=colore, lw=1.5 + 6.5 * min(1.3, Q_h / Q_ref_h), alpha=0.8,
                solid_capstyle="butt", solid_joinstyle="round", zorder=4)


def _badge(ax, x, y, num, col="#0f172a"):
    """Pallino numerato: lo stesso numero compare nei blocchi del percorso dell'acqua."""
    ax.add_patch(Circle((x, y), 9, facecolor=col, edgecolor="white", lw=1.2, zorder=20))
    ax.text(x, y, str(num), color="white", ha="center", va="center", fontsize=8.5, fontweight="bold", zorder=21)


def disegna_rete(r, occlusioni, aperte, filtro_da_lavare, imp, prese=None):
    """Schema della rete. r: risultato di risolvi(); occlusioni e aperte: liste per presa (due prese).
    Se si passa anche 'prese' compaiono le dimensioni degli elementi e la legenda numerata."""
    fig = Figure(figsize=(10, 6.4))
    ax = fig.subplots()
    ax.set_xlim(0, 720)
    ax.set_ylim(462, 0)          # asse y verso il basso, come in un disegno
    ax.set_aspect("equal")
    ax.axis("off")

    fondo, xs_prese, larg = 122, [130, 370], 92
    y_rami, nodo, xs_valvola = [330, 250], (500, 290), [250, 440]

    # vasca
    ax.add_patch(Rectangle((10, 22), 700, fondo - 22, color="#38bdf8", alpha=0.15, zorder=0))
    ax.plot([10, 10, 710, 710], [14, fondo, fondo, 14], color="#0f172a", lw=2, zorder=5)
    ax.plot([10, 710], [22, 22], color="#0284c7", lw=1.2, zorder=1)
    ax.text(16, 17, "pelo libero", fontsize=8, color="#0284c7")

    for j in range(2):
        p, cx, col, yr, vx = r["prese"][j], xs_prese[j], COLORI[j], y_rami[j], xs_valvola[j]
        # ramo dal pozzetto al collettore
        _tubo(ax, [cx, cx, nodo[0]], [fondo + 40, yr, yr], p["Q_h"] if aperte[j] else 0, imp.Q_ref_h, col)
        # pozzetto
        ax.add_patch(Rectangle((cx - larg / 2, fondo), larg, 40, facecolor="white", edgecolor="#0f172a", lw=2, zorder=5))
        if p["Q_h"] > 0 or p["depr_pozzetto_kPa"] > 0:
            ax.add_patch(Rectangle((cx - larg / 2 + 2, fondo + 1), larg - 4, 37, color=col, alpha=0.18, zorder=6))
        # griglia (tratteggio) e parte ostruita
        ax.plot([cx - larg / 2, cx + larg / 2], [fondo, fondo], color="#0f172a", lw=4, ls=(0, (2, 1.5)), zorder=7)
        if aperte[j] and occlusioni[j] > 0:
            ax.add_patch(Rectangle((cx - larg / 2, fondo - 8), larg * occlusioni[j], 11, facecolor="#94a3b8",
                                   edgecolor="#0f172a", hatch="////", zorder=8))
        # valvola di ramo (piena = chiusa)
        ax.add_patch(Polygon([(vx - 10, yr - 9), (vx + 10, yr + 9), (vx + 10, yr - 9), (vx - 10, yr + 9)],
                             closed=True, facecolor="#0f172a" if not aperte[j] else "white",
                             edgecolor="#0f172a", lw=1.5, zorder=9))
        if not aperte[j]:
            ax.text(vx, yr - 19, "valvola chiusa", ha="center", fontsize=8.5, fontweight="bold")
        # etichette nella vasca
        oltre = p["v_griglia"] > imp.v_griglia_max
        ax.text(cx, 40, p["nome"].capitalize(), ha="center", fontsize=11, fontweight="bold", color=col, zorder=9)
        ax.text(cx, 61, f"{n(p['Q_h'], 1)} m³/h · {n(p['quota'], 1)} %", ha="center", fontsize=9.5, zorder=9)
        ax.text(cx, 81, f"v griglia {n(p['v_griglia'])} m/s", ha="center", fontsize=9.5,
                color="#dc2626" if oltre else "#475569", fontweight="bold" if oltre else "normal", zorder=9)
        if occlusioni[j] > 0 and aperte[j]:
            ax.text(cx, 100, f"griglia occlusa al {n(100 * occlusioni[j], 0)} %", ha="center", fontsize=8.5, color="#475569", zorder=9)
        # numeri degli elementi
        _badge(ax, cx - larg / 2 - 14, fondo - 4, 1)
        _badge(ax, cx - larg / 2 - 14, fondo + 22, 2)
        _badge(ax, cx - 17, fondo + 52, 3)
        _badge(ax, cx - 17, (fondo + 40 + yr) / 2 + 6, 4)
        _badge(ax, cx + 18, yr + 20, 5)
        _badge(ax, vx, yr + 24, 6)
        _badge(ax, nodo[0] - 19, yr - 17, 7)
        # dati accanto al tubo
        tx = cx + 17
        ax.text(tx, fondo + 56, f"Δp pozzetto {n(p['depr_pozzetto_kPa'])} kPa", fontsize=8.5, color="#475569", va="center")
        if prese:
            pr = prese[j]
            ax.text(tx, fondo + 71, f"tubo Ø {n(pr.D_ramo * 1000, 0)} mm, L = {n(pr.L_ramo, 0)} m", fontsize=8.5, color="#475569", va="center")
            ax.text(tx, fondo + 86, f"{pr.n_curve} curve a 90°", fontsize=8.5, color="#475569", va="center")

    # collettore, tratto comune e ritorno in vasca
    ax.plot([nodo[0], nodo[0]], [y_rami[1], y_rami[0]], color="#334155", lw=11, solid_capstyle="butt", zorder=2)
    ax.plot([nodo[0], nodo[0]], [y_rami[1], y_rami[0]], color="white", lw=8, solid_capstyle="butt", zorder=3)
    _tubo(ax, [nodo[0], 690, 690], [nodo[1], nodo[1], fondo + 4], r["Q_h"], imp.Q_ref_h, COLORI[2])
    ax.add_patch(FancyArrow(690, fondo + 18, 0, -14, width=4, head_width=12, head_length=8, color="#0f172a", zorder=10))
    ax.add_patch(Circle(nodo, 5, color="#0f172a", zorder=10))
    ax.text(nodo[0] - 12, nodo[1] + 2, f"collettore\n{n(r['p_nodo_kPa'])} kPa", ha="right", va="center", fontsize=8.5, color="#475569")
    # prefiltro, pompa, filtro
    ax.add_patch(Rectangle((525, nodo[1] - 13), 26, 26, facecolor="white", edgecolor="#0f172a", lw=2, zorder=10))
    ax.text(538, nodo[1] + 27, "prefiltro", ha="center", fontsize=8.5, color="#475569")
    ax.add_patch(Circle((590, nodo[1]), 19, facecolor="white", edgecolor="#0f172a", lw=2.5, zorder=10))
    ax.add_patch(Polygon([(580, nodo[1] + 8), (602, nodo[1]), (580, nodo[1] - 8)], closed=False, fill=False,
                         edgecolor="#0f172a", lw=2, zorder=11))
    ax.add_patch(Rectangle((628, nodo[1] - 22), 30, 44, facecolor="#cbd5e1" if filtro_da_lavare else "white",
                           edgecolor="#0f172a", lw=2, hatch="xx" if filtro_da_lavare else None, zorder=10))
    ax.text(643, nodo[1] + 36, "filtro", ha="center", fontsize=8.5, color="#475569")
    ax.text(590, nodo[1] + 34, "pompa", ha="center", fontsize=9.5, fontweight="bold")
    ax.text(590, nodo[1] + 50, f"{n(r['Q_h'], 1)} m³/h", ha="center", fontsize=9, fontweight="bold")
    ax.text(590, nodo[1] + 64, f"H = {n(r['H_pompa'], 1)} m", ha="center", fontsize=8.5, color="#475569")
    _badge(ax, 512, nodo[1] - 24, 8)
    _badge(ax, 538, nodo[1] - 27, 9)
    _badge(ax, 590, nodo[1] - 34, 10)
    _badge(ax, 643, nodo[1] - 38, 11)
    _badge(ax, 706, 205, 12)
    ax.text(676, 222, "mandata e\nimmissione", ha="right", fontsize=8.5, color="#475569", va="top")

    # legenda numerata
    if prese:
        a, b = prese
        lato = lambda p: n(math.sqrt(p.A_ingombro) * 1000, 0)
        sin = [
            f"1  Griglia {lato(a)} × {lato(a)} mm, aperture {n(a.A_libera * 1e4, 0)} cm²",
            f"2  Pozzetto {n(a.L_pozzetto * 100, 0)} × {n(a.B_pozzetto * 100, 0)} cm",
            f"3  Imbocco dal pozzetto nel tubo (K = {n(a.K_imbocco, 1)})",
            f"4  Tubo del ramo Ø {n(a.D_ramo * 1000, 0)} mm, lungo {n(a.L_ramo, 0)} m (presa 1) e {n(b.L_ramo, 0)} m (presa 2)",
            f"5  Curve a 90° ({a.n_curve} sulla presa 1, {b.n_curve} sulla presa 2), K = {n(a.K_curva, 1)} ciascuna",
            f"6  Valvola di intercettazione (K = {n(a.K_valvola, 1)})",
            f"7  Innesto a T nel collettore (K = {n(a.K_innesto, 1)})",
        ]
        des = [
            f"8  Collettore e tubo fino alla pompa, Ø {n(imp.D_comune * 1000, 0)} mm, L = {n(imp.L_comune, 0)} m",
            "9  Prefiltro (cestello)",
            "10  Pompa",
            "11  Filtro" + (" (da lavare)" if filtro_da_lavare else ""),
            "12  Mandata e immissione in vasca",
        ]
        ax.text(10, 384, "\n".join(sin), fontsize=8.8, va="top", linespacing=1.5, color=TESTO)
        ax.text(430, 384, "\n".join(des), fontsize=8.8, va="top", linespacing=1.5, color=TESTO)

    fig.tight_layout(pad=0.2)
    return fig


# =============================================================================
# 2. INTRAPPOLAMENTO: valvola aperta (condizione 3) e valvola chiusa (condizione 4)
# =============================================================================
INK, VERDE = "#0f172a", "#15803d"


def _pannello_intrappolamento(ax, titolo, aperta, depr1, depr2, Q2_h, forza_N, A_m2):
    """Un pannello: vasca con due prese (la 1 con un corpo sulla griglia, la 2 libera), i due rami che si uniscono nel
    collettore e la pompa. Colori: arancione = pressione piu' bassa di quella della vasca, azzurro = uguale."""
    ax.set_xlim(0, 400)
    ax.set_ylim(376, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    c1 = BASSA if aperta else ALTA                       # pozzetto 1 e ramo 1 fino alla valvola
    # vasca e fondo con le aperture dei due pozzetti
    ax.add_patch(Rectangle((10, 44), 380, 86, facecolor=ALTA, alpha=0.35, edgecolor="none", zorder=0))
    ax.plot([10, 390], [44, 44], color="#0284c7", lw=1.5)
    ax.text(14, 37, "pelo libero della vasca", fontsize=8.5, color="#0284c7")
    for xa, xb in ((10, 30), (150, 250), (370, 390)):
        ax.plot([xa, xb], [130, 130], color=INK, lw=2.5)
    ax.plot([10, 10], [44, 130], color=INK, lw=2.5)
    ax.plot([390, 390], [44, 130], color=INK, lw=2.5)

    def tubo(xs, ys, col):
        ax.plot(xs, ys, color="#334155", lw=13, solid_capstyle="butt", solid_joinstyle="round", zorder=2)
        ax.plot(xs, ys, color=col, lw=10, solid_capstyle="butt", solid_joinstyle="round", zorder=3)

    # rami e collettore
    tubo([90, 90, 172], [205, 285, 285], c1)             # ramo 1, lato pozzetto
    tubo([208, 361], [285, 285], BASSA)                  # collettore (a valle della valvola 1)
    tubo([310, 310], [205, 285], BASSA)                  # ramo 2
    # pozzetti
    ax.add_patch(Rectangle((30, 130), 120, 75, facecolor=to_rgba(c1, 0.85 if aperta else 0.75), edgecolor=INK, lw=2.5, zorder=4))
    ax.add_patch(Rectangle((250, 130), 120, 75, facecolor=to_rgba(BASSA, 0.35), edgecolor=INK, lw=2.5, zorder=4))
    # griglie
    ax.plot([30, 150], [130, 130], color=INK, lw=5, ls=(0, (2, 1.5)), zorder=7)
    ax.plot([250, 370], [130, 130], color=INK, lw=5, ls=(0, (2, 1.5)), zorder=7)
    # corpo sulla griglia 1 (tratteggiato nella condizione 4: la griglia e' libera)
    ax.add_patch(FancyBboxPatch((22, 103), 136, 27, boxstyle="round,pad=0,rounding_size=12",
                                facecolor="#d6d3d1" if aperta else "none", edgecolor=INK, lw=2,
                                ls="-" if aperta else (0, (4, 3)), zorder=8))
    ax.text(90, 117, "corpo sulla griglia" if aperta else "(corpo ipotetico)", ha="center", va="center", fontsize=8.8, zorder=9)
    # pressioni sul corpo: dall'alto (vasca) e dal basso (pozzetto)
    xs_fr = (42, 66, 90, 114, 138)
    for x in xs_fr:
        ax.add_patch(FancyArrow(x, 68, 0, 32, width=3, head_width=10, head_length=8, color="#0369a1", length_includes_head=True, zorder=6))
    ax.text(90, 58, "pressione della vasca", ha="center", fontsize=8.8, color="#0369a1", fontweight="bold")
    lung = 18 if aperta else 36
    for x in xs_fr:
        ax.add_patch(FancyArrow(x, 170, 0, -lung, width=3, head_width=10, head_length=8,
                                color="#c2410c" if aperta else "#0369a1", length_includes_head=True, zorder=6))
    # scritte nei pozzetti
    ax.text(90, 184, "pozzetto 1", ha="center", fontsize=8.8, fontweight="bold", color="#7c2d12" if aperta else "#075985", zorder=9)
    ax.text(90, 197, f"−{n(depr1, 1)} kPa" if depr1 > 0 else "0 kPa", ha="center", fontsize=8.8, fontweight="bold",
            color="#7c2d12" if aperta else "#075985", zorder=9)
    ax.text(310, 184, "pozzetto 2", ha="center", fontsize=8.8, fontweight="bold", color="#7c2d12", zorder=9)
    ax.text(310, 197, f"−{n(depr2, 1)} kPa", ha="center", fontsize=8.8, fontweight="bold", color="#7c2d12", zorder=9)
    # acqua aspirata dalla presa 2 e verso la pompa
    for x in (285, 310, 335):
        ax.add_patch(FancyArrow(x, 80, 0, 62, width=3, head_width=10, head_length=8, color=VERDE, length_includes_head=True, zorder=6))
    ax.text(310, 64, f"presa 2: {n(Q2_h, 1)} m³/h", ha="center", fontsize=8.8, color=VERDE, fontweight="bold")
    ax.annotate("", xy=(310, 262), xytext=(310, 218), arrowprops=dict(arrowstyle="-|>", color=VERDE, lw=2.6, mutation_scale=14), zorder=12)
    ax.annotate("", xy=(352, 285), xytext=(326, 285), arrowprops=dict(arrowstyle="-|>", color=VERDE, lw=2.6, mutation_scale=14), zorder=12)
    # valvola del ramo 1
    vx = 190
    ax.add_patch(Polygon([(vx - 14, 272), (vx + 14, 298), (vx + 14, 272), (vx - 14, 298)], closed=True,
                         facecolor="white" if aperta else INK, edgecolor=INK, lw=2, zorder=9))
    ax.text(vx, 259, "valvola aperta" if aperta else "valvola CHIUSA", ha="center", fontsize=8.8, fontweight="bold")
    # pompa e nomi
    ax.add_patch(Circle((376, 285), 15, facecolor="white", edgecolor=INK, lw=2.5, zorder=10))
    ax.add_patch(Polygon([(369, 292), (383, 285), (369, 278)], closed=False, fill=False, edgecolor=INK, lw=2, zorder=11))
    ax.text(376, 309, "pompa", ha="center", fontsize=8.5, color="#475569")
    ax.text(100, 238, "ramo 1", fontsize=8.5, color="#475569")
    ax.text(320, 238, "ramo 2", fontsize=8.5, color="#475569")
    ax.text(262, 309, "collettore", ha="center", fontsize=8.5, color="#475569")
    # esito
    if aperta:
        esito = [f"Differenza di pressione sul corpo: {n(depr1, 1)} kPa",
                 f"Su {n(A_m2 * 1e4, 0)} cm² ≈ {n(forza_N / 1000, 1)} kN (circa {n(forza_N / G, 0)} kg-forza, ordine di grandezza)",
                 "Il corpo è premuto contro la griglia"]
        colore = "#b42318"
    else:
        esito = ["A regime, differenza di pressione sul corpo: 0 kPa", "Un corpo sulla griglia 1 non sarebbe più trattenuto",
                 "La presa 2 porta da sola tutta la portata"]
        colore = "#166534"
    ax.add_patch(Rectangle((10, 324), 380, 46, facecolor="white", edgecolor=colore, lw=1.8, zorder=5))
    ax.text(200, 347, "\n".join(esito), ha="center", va="center", fontsize=8.4, color=colore, fontweight="bold", linespacing=1.4, zorder=6)
    ax.text(200, 16, titolo, ha="center", fontsize=10.5, fontweight="bold", color=TESTO)


def disegna_intrappolamento(r_aperta, r_chiusa, A_ingombro):
    """Due pannelli affiancati: condizione 3 (valvola aperta) e condizione 4 (valvola chiusa).
    r_aperta, r_chiusa: risultati di risolvi() per le condizioni 3 e 4. Lo schema non e' in scala."""
    fig = Figure(figsize=(11, 5.6))
    a1, a2 = fig.subplots(1, 2)
    p3, p4 = r_aperta["prese"], r_chiusa["prese"]
    forza = p3[0]["depr_pozzetto_kPa"] * 1000 * A_ingombro
    _pannello_intrappolamento(a1, "Condizione 3: presa 1 occlusa, valvola aperta", True,
                              p3[0]["depr_pozzetto_kPa"], p3[1]["depr_pozzetto_kPa"], p3[1]["Q_h"], forza, A_ingombro)
    _pannello_intrappolamento(a2, "Condizione 4: presa 1 esclusa, valvola chiusa", False,
                              p4[0]["depr_pozzetto_kPa"], p4[1]["depr_pozzetto_kPa"], p4[1]["Q_h"], 0.0, A_ingombro)
    fig.tight_layout(pad=0.3, w_pad=1.0)
    return fig


# =============================================================================
# 3. GRAFICI: come cambiano portate, velocita' e depressione al crescere dell'occlusione
# =============================================================================
def _annota(ax, xs, curve, punti, decimali, sinistra=False):
    """Segna sulle curve i punti scelti con i valori (ascissa; ordinata).
    curve: lista di (ys, colore); in ogni punto l'etichetta della curva piu' alta va sopra, l'altra sotto."""
    for xp in punti:
        i = xs.index(xp)
        valori = [c[0][i] for c in curve]
        for k, (ys, col) in enumerate(curve):
            y = ys[i]
            if y != y:
                continue
            alto = len(curve) == 1 or y >= max(v for v in valori if v == v) - 1e-12
            if len(curve) > 1 and len(set(valori)) > 1 and y == min(valori):
                alto = False
            ax.plot(xp, y, "o", color=col, ms=5.5, zorder=6)
            ha = "left" if xp == xs[0] else ("right" if (xp == xs[-1] or sinistra) else "center")
            dx = 4 if ha == "left" else (-6 if ha == "right" else 0)
            ax.annotate(f"({n(xp, 0)} %; {n(y, decimali)})", (xp, y), xytext=(dx, 10 if alto else -12),
                        textcoords="offset points", ha=ha, va="bottom" if alto else "top", fontsize=8.6, color=col,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85), zorder=7)


def _base(titolo, etichetta_y, occ_scelta):
    fig = Figure(figsize=(6.4, 4.5))
    ax = fig.subplots()
    ax.set_title(titolo, fontsize=11, fontweight="bold", loc="left", pad=22)
    ax.set_xlabel("Occlusione della griglia 1 [%]", fontsize=10)
    ax.set_ylabel(etichetta_y, fontsize=10)
    ax.set_xlim(-6, 106)
    ax.set_xticks(range(0, 101, 10))
    ax.grid(alpha=0.25)
    ax.axvline(occ_scelta, color="#64748b", lw=1.2, ls="--", zorder=1)
    ax.text(occ_scelta, 1.0, f" scelta: {n(occ_scelta, 0)} %", transform=ax.get_xaxis_transform(), fontsize=8, color="#64748b",
            va="top", ha="left" if occ_scelta < 70 else "right")
    for lato in ("top", "right"):
        ax.spines[lato].set_visible(False)
    return fig, ax


def grafici_occlusione(d, vg_max, occ_scelta):
    """d: dizionario con liste 'x' [%], 'q1', 'q2' [m3/h], 'vg1', 'vg2' [m/s], 'dp1' [kPa] (vg = nan dove non definita).
    Restituisce tre figure: portate, velocita' alla griglia, depressione nel pozzetto 1."""
    x = d["x"]
    # portate
    f1, a = _base("Portate delle due prese", "Portata [m³/h]", occ_scelta)
    a.plot(x, d["q1"], color=COLORI[0], lw=2.4, label="Presa 1 (occlusa)")
    a.plot(x, d["q2"], color=COLORI[1], lw=2.4, label="Presa 2")
    a.set_ylim(-9, max(max(d["q2"]), max(d["q1"])) * 1.18)
    _annota(a, x, [(d["q1"], COLORI[0]), (d["q2"], COLORI[1])], [0, 25, 50, 75, 100], 1)
    a.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=9)
    f1.tight_layout()
    # velocita' alla griglia
    f2, a = _base("Velocità attraverso la griglia", "Velocità [m/s]", occ_scelta)
    a.plot(x, d["vg1"], color=COLORI[0], lw=2.4, label="Griglia 1 (occlusa)")
    a.plot(x, d["vg2"], color=COLORI[1], lw=2.4, label="Griglia 2")
    a.axhline(vg_max, color="#dc2626", lw=1.4, ls="--", label=f"limite {n(vg_max)} m/s")
    vmax = max(v for v in d["vg1"] + d["vg2"] if v == v)
    a.set_ylim(0, vmax * 1.3)
    a.text(104, vmax * 1.27, "a 100 % non resta\nnessuna apertura", ha="right", va="top", fontsize=8.5, color="#475569", style="italic")
    _annota(a, x, [(d["vg1"], COLORI[0]), (d["vg2"], COLORI[1])], [0, 25, 50, 75, 90, 99], 2)
    a.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, frameon=False, fontsize=8.5)
    f2.tight_layout()
    # depressione
    f3, a = _base("Depressione nel pozzetto 1", "Depressione [kPa]", occ_scelta)
    a.plot(x, d["dp1"], color="#b42318", lw=2.4)
    a.set_ylim(-1, max(d["dp1"]) * 1.2)
    _annota(a, x, [(d["dp1"], "#b42318")], [0, 50, 75, 90, 100], 1, sinistra=True)
    f3.tight_layout()
    return f1, f2, f3


# =============================================================================
# 4. IL PERCORSO DELL'ACQUA, BLOCCO PER BLOCCO (HTML)
# =============================================================================
def _card(num, titolo, righe, formula, col, sfondo="#FFFFFF"):
    h = (f'<div style="flex:1 1 142px;min-width:142px;max-width:200px;background:{sfondo};border:2px solid {col};'
         f'border-radius:10px;padding:8px 9px;box-sizing:border-box;color:{TESTO}">')
    h += '<div style="display:flex;align-items:center;gap:6px;margin-bottom:5px">'
    if num:
        h += (f'<span style="flex:none;width:21px;height:21px;line-height:21px;text-align:center;border-radius:50%;'
              f'background:{col};color:#fff;font-weight:700;font-size:12px">{num}</span>')
    h += f'<span style="font-weight:700;font-size:13px;line-height:1.2">{titolo}</span></div>'
    for etichetta, valore in righe:
        h += (f'<div style="display:flex;justify-content:space-between;gap:6px;border-top:1px solid {BORDO};padding:2px 0;font-size:12px">'
              f'<span style="color:{TESTO_CHIARO}">{etichetta}</span><span style="font-weight:600;text-align:right">{valore}</span></div>')
    if formula:
        h += f'<div style="margin-top:5px;font-size:11px;color:{TESTO_CHIARO};line-height:1.3">{formula}</div>'
    return h + "</div>"


FRECCIA = '<div style="align-self:center;font-size:20px;color:#9CA3AF;flex:none">→</div>'


def _riga(schede, ultimo=None):
    """Una fila di blocchi separati da frecce; 'ultimo' (facoltativo) e' il blocco del totale, preceduto da '='."""
    html = FRECCIA.join(schede)
    if ultimo:
        html += FRECCIA.replace("→", "=") + ultimo
    return '<div style="display:flex;flex-wrap:wrap;align-items:stretch;gap:6px;margin:6px 0 14px 0">' + html + "</div>"


def blocchi_percorso(r, j, occlusione, aperta, prese, imp):
    """HTML dei blocchi che l'acqua attraversa: ramo della presa j e parte comune, con sezione, velocita' e perdita
    di ciascun elemento. r: risultato di risolvi(); j: indice della presa; occlusione: frazione 0..1."""
    p, rr = prese[j], r["prese"][j]
    col, colc = COLORI[j], COLORI[2]
    Q = rr["Q_h"] / 3600                      # portata del ramo [m3/s]
    Qt = r["Q_h"] / 3600                      # portata totale [m3/s]
    kPa = lambda h: h * imp.rho * G / 1000    # carico [m] -> pressione [kPa]
    perd = rr["perdite"]
    A_tubo = area_cerchio(p.D_ramo)
    v_t = rr["v_tubo"]
    hv = v_t ** 2 / (2 * G)
    Re = imp.rho * v_t * p.D_ramo / imp.mu
    lam = fattore_attrito(Re, p.rugosita, p.D_ramo)
    A_ap = p.A_libera * (1 - occlusione)
    f = p.A_libera / p.A_ingombro * (1 - occlusione)
    A_poz = p.L_pozzetto * p.B_pozzetto
    v_p = Q / A_poz
    qm = f"{n(rr['Q_h'], 1)} m³/h"
    perdita = lambda h: ("Perdita", f"{n(h, 3)} m<br><span style='font-weight:400;color:{TESTO_CHIARO}'>= {n(kPa(h), 2)} kPa</span>")

    ramo = [
        _card("", "Vasca", [("Portata", qm), ("Sezione", "molto ampia"), ("Velocità", "≈ 0"), ("Pressione", "di quiete"), ("Perdita", "-")],
              "L'acqua parte ferma, dal pelo libero.", "#38bdf8", "#F0F9FF"),
        _card(1, "Griglia", [("Portata", qm), ("Sezione libera", f"{n(A_ap * 1e4, 0)} cm²"), ("Velocità", f"{n(rr['v_griglia'])} m/s"),
                             ("K griglia", n(K_griglia(f), 1) if f > 0 else "-"), perdita(perd["griglia"])],
              "v = Q / A libera aperta<br>h = K · (Q/A ingombro)² / 2g<br>(K riferito a Q/A ingombro)", col),
        _card(2, "Pozzetto", [("Portata", qm), ("Sezione", f"{n(A_poz * 1e4, 0)} cm²"), ("Velocità", f"{n(v_p, 2)} m/s"),
                              ("v²/2g", f"{n(v_p ** 2 / (2 * G), 4)} m"), ("Perdita", "-")],
              "Nessuna perdita: la sua energia cinetica entra nella depressione.", col),
        _card(3, "Imbocco nel tubo", [("Portata", qm), ("Sezione tubo", f"{n(A_tubo * 1e4, 1)} cm²"), ("Velocità", f"{n(v_t)} m/s"),
                                      ("K", n(p.K_imbocco, 1)), perdita(perd["imbocco"])],
              "h = K · v²/2g", col),
        _card(4, "Tubo del ramo", [("Portata", qm), ("Sezione", f"{n(A_tubo * 1e4, 1)} cm²"), ("Velocità", f"{n(v_t)} m/s"),
                                   ("Ø · L", f"{n(p.D_ramo * 1000, 0)} mm · {n(p.L_ramo, 0)} m"), perdita(perd["tubo"])],
              f"h = λ · (L/D) · v²/2g<br>λ = {n(lam, 4)} (attrito)", col),
        _card(5, "Curve a 90°", [("Portata", qm), ("Sezione", f"{n(A_tubo * 1e4, 1)} cm²"), ("Velocità", f"{n(v_t)} m/s"),
                                 ("K", f"{p.n_curve} × {n(p.K_curva, 1)} = {n(p.n_curve * p.K_curva, 1)}"), perdita(perd["curve"])],
              "h = (n · K) · v²/2g", col),
        _card(6, "Valvola", [("Portata", qm), ("Sezione", f"{n(A_tubo * 1e4, 1)} cm²"), ("Velocità", f"{n(v_t)} m/s"),
                             ("K", f"{n(p.K_valvola, 1)} ({'aperta' if aperta else 'CHIUSA'})"), perdita(perd["valvola"])],
              "h = K · v²/2g", col),
        _card(7, "Innesto a T nel collettore", [("Portata", qm), ("Sezione", f"{n(A_tubo * 1e4, 1)} cm²"), ("Velocità", f"{n(v_t)} m/s"),
                                                ("K", n(p.K_innesto, 1)), perdita(perd["innesto"])],
              "h = K · v²/2g", col),
    ]
    somma = sum(perd.values())
    totale = _card("Σ", "Totale del ramo", [("Perdita", f"{n(somma, 3)} m"), ("Pressione", f"{n(kPa(somma), 2)} kPa"),
                                            ("Carico al collettore", f"{n(r['dh_nodo'], 3)} m")],
                   "Se la presa lavora, la somma delle perdite è uguale al carico che il collettore chiede alla presa (le due prese lo condividono).", col, "#F8FAFC")

    # parte comune
    com = perdite_comune(Qt, imp, True)
    A_c = area_cerchio(imp.D_comune)
    v_c = r["v_comune"]
    Re_c = imp.rho * v_c * imp.D_comune / imp.mu
    lam_c = fattore_attrito(Re_c, imp.rugosita_comune, imp.D_comune)
    qt = f"{n(r['Q_h'], 1)} m³/h"
    dp_filtro = imp.dp_filtro_pulito + imp.dp_filtro_incremento
    comune = [
        _card(8, "Collettore e tubo comune", [("Portata", qt), ("Sezione", f"{n(A_c * 1e4, 1)} cm²"), ("Velocità", f"{n(v_c)} m/s"),
                                              ("Ø · L · K", f"{n(imp.D_comune * 1000, 0)} mm · {n(imp.L_comune, 0)} m · {n(imp.K_comune, 1)}"),
                                              perdita(com["aspirazione"])],
              f"h = (λ · L/D + K) · v²/2g<br>λ = {n(lam_c, 4)}", colc),
        _card(9, "Prefiltro", [("Portata", qt), ("Sezione", "-"), ("Velocità", "-"),
                               (f"Δp a {n(imp.Q_ref_h, 0)} m³/h", f"{n(imp.dp_prefiltro, 0)} kPa"), perdita(com["prefiltro"])],
              "Δp = Δp<sub>rif</sub> · (Q/Q<sub>rif</sub>)²", colc),
        _card(10, "Pompa", [("Portata", qt), ("Sezione", "-"), ("Velocità", "-"),
                            ("Curva", f"H = {n(imp.H0, 0)} − {n(imp.a_pompa, 0)}·Q²"), ("Prevalenza", f"{n(r['H_pompa'], 2)} m<br>"
                                                                                       f"<span style='font-weight:400;color:{TESTO_CHIARO}'>= {n(kPa(r['H_pompa']), 1)} kPa</span>")],
              "È la pompa che dà l'energia: tutte le perdite del circuito sono pagate da lei.", colc),
        _card(11, "Filtro", [("Portata", qt), ("Sezione", "-"), ("Velocità", "-"),
                             (f"Δp a {n(imp.Q_ref_h, 0)} m³/h", f"{n(dp_filtro, 0)} kPa"), perdita(com["filtro"])],
              "Δp = Δp<sub>rif</sub> · (Q/Q<sub>rif</sub>)²<br>cresce se il filtro si sporca", colc),
        _card(12, "Mandata e immissione", [("Portata", qt), ("Sezione", "-"), ("Velocità", "-"),
                                           (f"Δp a {n(imp.Q_ref_h, 0)} m³/h", f"{n(imp.dp_mandata, 0)} kPa"), perdita(com["mandata"])],
              "Tubi di mandata, bocchette: stessa legge del prefiltro", colc),
        _card("", "Ritorno in vasca", [("Portata", qt), ("Sezione", "molto ampia"), ("Velocità", "≈ 0"), ("Pressione", "di quiete"), ("Perdita", "-")],
              "L'acqua rientra: il circuito è chiuso.", "#38bdf8", "#F0F9FF"),
    ]
    perdite_comuni = com["aspirazione"] + com["prefiltro"] + com["filtro"] + com["mandata"] + imp.H_statica
    bilancio = (f'<div style="border:2px dashed {colc};border-radius:10px;padding:9px 12px;font-size:13px;color:{TESTO};background:#F0FDF4">'
                f"<b>Bilancio dell'energia.</b> Prevalenza della pompa {n(r['H_pompa'], 2)} m = "
                f"{n(r['dh_nodo'], 3)} m (perdita dei rami, cioè carico al collettore) + {n(perdite_comuni, 3)} m (parte comune). "
                f"La pompa fornisce esattamente l'energia che l'acqua consuma lungo il percorso.</div>")

    intest = lambda testo, c: f'<div style="font-weight:700;font-size:14px;color:{c};margin-top:4px">{testo}</div>'
    return (intest(f"Ramo di aspirazione della {p.nome}", col) + _riga(ramo, totale)
            + intest("Parte comune: dal collettore alla vasca", colc) + _riga(comune) + bilancio)