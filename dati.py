from modello import Presa, Impianto

presa_1 = Presa(nome="presa 1", A_ingombro=0.0625, A_libera=0.0156, Q_max_fabbricante_h=28.1,
                L_pozzetto=0.30, B_pozzetto=0.30, K_imbocco=0.5,
                D_ramo=0.10, L_ramo=12, rugosita=0.0000015, n_curve=3, K_curva=0.3,
                K_valvola=0.2, K_innesto=0.9)

presa_2 = Presa(nome="presa 2", A_ingombro=0.0625, A_libera=0.0156, Q_max_fabbricante_h=28.1,
                L_pozzetto=0.30, B_pozzetto=0.30, K_imbocco=0.5,
                D_ramo=0.10, L_ramo=25, rugosita=0.0000015, n_curve=4, K_curva=0.3,
                K_valvola=0.2, K_innesto=0.9)

impianto = Impianto(rho=996.5, mu=0.00085,
                    D_comune=0.125, L_comune=8, rugosita_comune=0.0000015, K_comune=1.0,
                    Q_ref_h=60, dp_prefiltro=5, dp_filtro_pulito=30, dp_filtro_incremento=30, dp_mandata=40,
                    H_statica=0, H0=14, a_pompa=21000, battente_pompa=2,
                    v_griglia_max=0.5, v_aspirazione_max=1.7)

PRESE = [presa_1, presa_2]

CONDIZIONI = [
    ("1 - Entrambe libere",                   [0.0, 0.0], [True, True]),
    ("2 - Presa 1 parzialmente occlusa",      [0.5, 0.0], [True, True]),
    ("3 - Presa 1 completamente occlusa",     [1.0, 0.0], [True, True]),
    ("Confronto - Presa 1 esclusa (valvola)", [0.0, 0.0], [False, True]),
]