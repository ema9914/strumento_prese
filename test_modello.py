"""Test automatici: si lanciano con il comando  pytest  e devono risultare tutti 'passed'."""
import dataclasses
import math
from modello import risolvi, perdita_totale_presa
from dati import PRESE, impianto


def test_velocita_griglia_a_mano():
    # v = Q / A_libera: 30 m3/h su 0,030 m2 -> 0,2778 m/s (calcolo a mano)
    assert math.isclose((30 / 3600) / 0.030, 0.2778, rel_tol=1e-3)


def test_conservazione_della_portata():
    r = risolvi(PRESE, impianto, [0.5, 0.0], [True, True])
    somma = sum(p["Q_h"] for p in r["prese"])
    assert math.isclose(somma, r["Q_h"], rel_tol=1e-9)


def test_rami_in_parallelo_perdono_lo_stesso_carico():
    r = risolvi(PRESE, impianto, [0.0, 0.0], [True, True])
    h1 = perdita_totale_presa(PRESE[0], r["prese"][0]["Q_h"] / 3600, 0.0, impianto)
    h2 = perdita_totale_presa(PRESE[1], r["prese"][1]["Q_h"] / 3600, 0.0, impianto)
    assert math.isclose(h1, r["dh_nodo"], rel_tol=1e-6)
    assert math.isclose(h2, r["dh_nodo"], rel_tol=1e-6)


def test_presa_occlusa_portata_nulla_e_depressione_del_nodo():
    r = risolvi(PRESE, impianto, [1.0, 0.0], [True, True])
    p1 = r["prese"][0]
    assert p1["Q_h"] == 0
    assert math.isclose(p1["depr_pozzetto_kPa"], -r["p_nodo_kPa"], rel_tol=1e-9)


def test_presa_esclusa_nessuna_depressione():
    r = risolvi(PRESE, impianto, [0.0, 0.0], [False, True])
    assert r["prese"][0]["Q_h"] == 0
    assert r["prese"][0]["depr_pozzetto_kPa"] == 0


def test_stessi_numeri_della_dashboard():
    # La dashboard "Pompa con due prese" usa ancora la griglia 300 x 300 mm (superficie libera 0,030 m2).
    # Con quei dati la condizione 1, a filtro appena lavato, deve dare 60,0 / 33,4 / 26,6 m3/h.
    prese = [dataclasses.replace(p, A_ingombro=0.09, A_libera=0.030) for p in PRESE]
    r = risolvi(prese, impianto, [0.0, 0.0], [True, True])
    assert round(r["Q_h"], 1) == 60.0
    assert round(r["prese"][0]["Q_h"], 1) == 33.4
    assert round(r["prese"][1]["Q_h"], 1) == 26.6


def test_griglia_250_condizione_3_verifica_a_mano():
    # Dati attuali (griglia 250 x 250), presa 1 completamente occlusa, filtro appena lavato:
    # la presa 2 porta tutta la portata; la depressione sotto il corpo e' rho * g * (perdita del ramo 2).
    r = risolvi(PRESE, impianto, [1.0, 0.0], [True, True])
    p2 = r["prese"][1]
    h_ramo_2 = sum(p2["perdite"].values())
    assert math.isclose(h_ramo_2, r["dh_nodo"], rel_tol=1e-6)
    assert math.isclose(r["prese"][0]["depr_pozzetto_kPa"], impianto.rho * 9.81 * h_ramo_2 / 1000, rel_tol=1e-6)
    assert round(r["prese"][0]["depr_pozzetto_kPa"], 1) == 14.5