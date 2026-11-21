#primo calcolo: velocità dell'acqua attraverso la griglia, v=Q\A
# Le righe che iniziano con # sono commenti: Python le ignora, servono a noi.
Q_h = 30.0          # portata della presa [m³/h]
A_libera = 0.030    # superficie libera della griglia [m²]
Q = Q_h /3600 #da m³/h a m³/s (un'ora = 3600 secondi)
v = Q / A_libera    # velocità attraverso la griglia [m/s]
print("Portata:", Q, "m³/s")
print("Velocità attraverso la griglia:", round(v, 3), "m/s")