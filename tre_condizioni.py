from modello import risolvi
from dati import PRESE, CONDIZIONI, impianto

for filtro_da_lavare in (False, True):
    print()
    print("FILTRO", "DA LAVARE" if filtro_da_lavare else "APPENA LAVATO")
    for nome, occlusioni, aperte in CONDIZIONI:
        r = risolvi(PRESE, impianto, occlusioni, aperte, filtro_da_lavare)
        p1, p2 = r["prese"]
        print(f"{nome:40s} Q={r['Q_h']:5.1f}  Q1={p1['Q_h']:5.1f}  Q2={p2['Q_h']:5.1f} m3/h"
              f"  v griglia 1={p1['v_griglia']:.3f}  v griglia 2={p2['v_griglia']:.3f} m/s"
              f"  depr. pozzetto 1={p1['depr_pozzetto_kPa']:.2f} kPa")
        if r["limiti_superati"]:
            print(" " * 40, "limiti superati:", ", ".join(r["limiti_superati"]))
            