"""
Modello 0D stazionario: una pompa che aspira da N prese di fondo collegate in parallelo.
Ogni presa (livello B): griglia -> pozzetto -> imbocco -> tubazione di ramo -> curve -> valvola -> innesto.
Ogni elemento perde un carico h = K * v^2 / (2 g) [m].
"""
import math
from dataclasses import dataclass

G = 9.81  # accelerazione di gravita' [m/s2]


@dataclass
class Presa:
    nome: str
    A_ingombro: float
    A_libera: float
    Q_max_fabbricante_h: float
    L_pozzetto: float
    B_pozzetto: float
    K_imbocco: float
    D_ramo: float
    L_ramo: float
    rugosita: float
    n_curve: int
    K_curva: float
    K_valvola: float
    K_innesto: float


@dataclass
class Impianto:
    rho: float
    mu: float
    D_comune: float
    L_comune: float
    rugosita_comune: float
    K_comune: float
    Q_ref_h: float
    dp_prefiltro: float
    dp_filtro_pulito: float
    dp_filtro_incremento: float
    dp_mandata: float
    H_statica: float
    H0: float
    a_pompa: float
    battente_pompa: float
    v_griglia_max: float
    v_aspirazione_max: float


def area_cerchio(D):
    return math.pi * D ** 2 / 4


def fattore_attrito(Re, rugosita, D):
    if Re <= 0:
        return 0.0
    if Re < 2300:
        return 64 / Re
    return 0.25 / math.log10(rugosita / (3.7 * D) + 5.74 / Re ** 0.9) ** 2


def K_griglia(f):
    return (0.707 * math.sqrt(1 - f) + 1 - f) ** 2 / f ** 2


def bisezione(F, a, b, iterazioni=60):
    for _ in range(iterazioni):
        m = (a + b) / 2
        if F(m) > 0:
            a = m
        else:
            b = m
    return (a + b) / 2


def perdite_presa(presa, Q, occlusione, imp):
    v_tubo = Q / area_cerchio(presa.D_ramo)
    hv = v_tubo ** 2 / (2 * G)
    v_avv = Q / presa.A_ingombro
    f = (presa.A_libera / presa.A_ingombro) * (1 - occlusione)
    Re = imp.rho * v_tubo * presa.D_ramo / imp.mu
    lam = fattore_attrito(Re, presa.rugosita, presa.D_ramo)
    return {
        "griglia": K_griglia(f) * v_avv ** 2 / (2 * G) if f > 0 else 0.0,
        "imbocco": presa.K_imbocco * hv,
        "tubo": lam * presa.L_ramo / presa.D_ramo * hv,
        "curve": presa.n_curve * presa.K_curva * hv,
        "valvola": presa.K_valvola * hv,
        "innesto": presa.K_innesto * hv,
        "v_tubo": v_tubo,
    }


def perdita_totale_presa(presa, Q, occlusione, imp):
    p = perdite_presa(presa, Q, occlusione, imp)
    return p["griglia"] + p["imbocco"] + p["tubo"] + p["curve"] + p["valvola"] + p["innesto"]


def portata_presa(presa, occlusione, aperta, dh_nodo, imp):
    if not aperta or occlusione >= 1 or dh_nodo <= 0:
        return 0.0
    return bisezione(lambda q: dh_nodo - perdita_totale_presa(presa, q, occlusione, imp), 0.0, 1.0)


def perdite_comune(Q, imp, filtro_da_lavare):
    v_c = Q / area_cerchio(imp.D_comune)
    hv = v_c ** 2 / (2 * G)
    Re = imp.rho * v_c * imp.D_comune / imp.mu
    lam = fattore_attrito(Re, imp.rugosita_comune, imp.D_comune)
    scala = (Q / (imp.Q_ref_h / 3600)) ** 2
    da_kPa = lambda kPa: kPa * 1000 * scala / (imp.rho * G)
    aspirazione = lam * imp.L_comune / imp.D_comune * hv + imp.K_comune * hv
    prefiltro = da_kPa(imp.dp_prefiltro)
    filtro = da_kPa(imp.dp_filtro_pulito + (imp.dp_filtro_incremento if filtro_da_lavare else 0))
    mandata = da_kPa(imp.dp_mandata)
    return {"aspirazione": aspirazione, "prefiltro": prefiltro, "filtro": filtro, "mandata": mandata,
            "totale": aspirazione + prefiltro + filtro + mandata + imp.H_statica, "v_comune": v_c}


def prevalenza_pompa(Q, imp):
    return imp.H0 - imp.a_pompa * Q ** 2


def risolvi(prese, imp, occlusioni, aperte, filtro_da_lavare=False):
    n = len(prese)

    def portate(dh):
        return [portata_presa(prese[j], occlusioni[j], aperte[j], dh, imp) for j in range(n)]

    def squilibrio(dh):
        Q = sum(portate(dh))
        return prevalenza_pompa(Q, imp) - (dh + perdite_comune(Q, imp, filtro_da_lavare)["totale"])

    dh = bisezione(squilibrio, 0.0, imp.H0)
    q = portate(dh)
    Q = sum(q)
    com = perdite_comune(Q, imp, filtro_da_lavare)
    ris = {"Q_h": Q * 3600, "dh_nodo": dh, "p_nodo_kPa": -imp.rho * G * dh / 1000,
           "H_pompa": prevalenza_pompa(Q, imp), "v_comune": com["v_comune"], "prese": [], "limiti_superati": []}
    ris["p_asp_pompa_kPa"] = (imp.rho * G * (imp.battente_pompa - dh - com["aspirazione"] - com["prefiltro"])
                              - imp.rho * com["v_comune"] ** 2 / 2) / 1000
    for j, presa in enumerate(prese):
        el = perdite_presa(presa, q[j], occlusioni[j], imp)
        A_aperta = presa.A_libera * (1 - occlusioni[j])
        v_griglia = q[j] / A_aperta if A_aperta > 0 else 0.0
        v_pozzetto = q[j] / (presa.L_pozzetto * presa.B_pozzetto)
        if not aperte[j]:
            depr = 0.0
        elif q[j] == 0:
            depr = dh
        else:
            depr = el["griglia"] + v_pozzetto ** 2 / (2 * G)
        r = {"nome": presa.nome, "Q_h": q[j] * 3600, "quota": 100 * q[j] / Q if Q > 0 else 0.0,
             "v_griglia": v_griglia, "v_tubo": el["v_tubo"], "depr_pozzetto_kPa": imp.rho * G * depr / 1000,
             "perdite": {k: el[k] for k in ("griglia", "imbocco", "tubo", "curve", "valvola", "innesto")}}
        ris["prese"].append(r)
        if v_griglia > imp.v_griglia_max:
            ris["limiti_superati"].append(f"velocita' griglia {presa.nome}")
        if el["v_tubo"] > imp.v_aspirazione_max:
            ris["limiti_superati"].append(f"velocita' tubo {presa.nome}")
        if q[j] * 3600 > presa.Q_max_fabbricante_h:
            ris["limiti_superati"].append(f"portata del fabbricante {presa.nome}")
    if com["v_comune"] > imp.v_aspirazione_max:
        ris["limiti_superati"].append("velocita' tratto comune")
    return ris