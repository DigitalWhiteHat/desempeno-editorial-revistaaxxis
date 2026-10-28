"""Registro de updates de algoritmo de Google confirmados en 2026, para cruzar
contra la línea de tráfico y detectar si una caída/subida coincide con un
algoritmo. Fechas verificadas vía búsqueda (no inventadas) — actualizar cuando
Google confirme uno nuevo.

Fuentes: Search Engine Land, Search Engine Journal, Search Engine Roundtable
(agosto 2026).
"""

from datetime import date

UPDATES_2026 = [
    {"nombre": "Discover Core Update", "tipo": "Discover", "inicio": date(2026, 2, 5), "fin": date(2026, 2, 27)},
    {"nombre": "March 2026 Spam Update", "tipo": "Spam", "inicio": date(2026, 3, 1), "fin": date(2026, 3, 2)},
    {"nombre": "March 2026 Core Update", "tipo": "Core", "inicio": date(2026, 3, 27), "fin": date(2026, 4, 8)},
    {"nombre": "May 2026 Core Update", "tipo": "Core", "inicio": date(2026, 5, 21), "fin": date(2026, 6, 2)},
    {"nombre": "June 2026 Spam Update", "tipo": "Spam", "inicio": date(2026, 6, 24), "fin": date(2026, 6, 26)},
    {"nombre": "August 2026 Spam Update", "tipo": "Spam", "inicio": date(2026, 8, 18), "fin": None},
    {"nombre": "August 2026 Core Update", "tipo": "Core", "inicio": date(2026, 8, 26), "fin": None},
    # 04-oct-2026: faltaba. Google lo anunció el 24-sep a las 09:15 PT, global y en todos los
    # idiomas, con rollout de hasta dos semanas. Es el cuarto spam update del año y el más
    # largo: los tres anteriores cerraron en 19h30 (marzo), 2d01h (junio) y 2d16h (agosto).
    # 11-oct-2026: el fin del 8-oct deja de ser estimado -- el Search Status Dashboard marcó
    # "rollout complete as of October 8, 2026" (01:37 PT), 13 días y 16 horas en total.
    # Fuentes: seroundtable.com/google-september-2026-spam-update-done-42235.html,
    # searchenginejournal.com/google-september-2026-spam-update-complete/592283/ y ppc.land.
    {"nombre": "September 2026 Spam Update", "tipo": "Spam", "inicio": date(2026, 9, 24),
     "fin": date(2026, 10, 8)},
]


def updates_en_rango(fecha_ini: date, fecha_fin: date) -> list[dict]:
    """Updates cuyo rango se solapa con [fecha_ini, fecha_fin]."""
    salida = []
    for u in UPDATES_2026:
        fin_u = u["fin"] or u["inicio"]
        if fin_u >= fecha_ini and u["inicio"] <= fecha_fin:
            salida.append(u)
    return salida
