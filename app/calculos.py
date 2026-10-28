"""Formatos y puntaje de rendimiento. Mismo criterio que la calculadora de referencia (sub-puntajes en
escala 0-10), sin el componente de producción: AXXIS no tiene una meta de notas por persona."""

import numpy as np
import pandas as pd

MESES_ABREV = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def formatear_numero(n: float) -> str:
    n = float(n)
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.2f}M".replace(".", ",")
    if abs(n) >= 10_000:
        return f"{n / 1_000:.0f}K"
    return f"{n:,.0f}".replace(",", ".")


def miles(n) -> str:
    """Cifra completa con punto de miles, como se escribe en español."""
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "—"
    return f"{float(n):,.0f}".replace(",", ".")


def decimal(n, d: int = 1) -> str:
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "—"
    return f"{float(n):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatear_tiempo(segundos: float) -> str:
    segundos = max(0, int(round(segundos)))
    return f"{segundos // 60}:{segundos % 60:02d} min"


def formatear_delta_pct(actual: float, anterior: float, decimales: int = 0) -> str | None:
    if anterior in (0, None) or pd.isna(anterior):
        return None
    delta = (actual - anterior) / abs(anterior) * 100
    signo = "+" if delta >= 0 else ""
    return f"{signo}{delta:.{decimales}f}%".replace(".", ",")


def estado_label(eficiencia: float, en_alerta: bool) -> tuple[str, str]:
    if en_alerta:
        return "EN ALERTA", "red"
    if eficiencia is not None and not pd.isna(eficiencia) and eficiencia >= 120:
        return "SOBRE MEDIANA", "green"
    return "EN RANGO", "blue"


PESOS_RENDIMIENTO = {"eficiencia": 4, "ctr": 2, "posicion": 2, "seo": 2}


def _vacio(v) -> bool:
    return v is None or (isinstance(v, float) and np.isnan(v))


def sub_eficiencia(e):
    """100 = mediana del equipo -> 5,0. Escala logarítmica: el índice no tiene techo."""
    if _vacio(e):
        return None
    return float(np.clip(5.0 + 3.0 * np.log10(max(float(e), 1.0) / 100.0), 0.0, 10.0))


def sub_ctr(indice):
    """1,0 = CTR igual al esperado por la posición (curva del propio sitio) -> 5,0."""
    if _vacio(indice):
        return None
    return float(np.clip(5.0 + 5.0 * (float(indice) - 1.0), 0.0, 10.0))


def sub_posicion(pos):
    """Posición 1 -> 10; posición 20 o peor -> 0."""
    if _vacio(pos):
        return None
    return float(np.clip(10.0 - (float(pos) - 1.0) * (10.0 / 19.0), 0.0, 10.0))


def sub_seo(pct):
    if _vacio(pct):
        return None
    return float(np.clip(float(pct) / 10.0, 0.0, 10.0))


def puntaje_rendimiento(fila) -> dict:
    """Promedio ponderado de los sub-puntajes que existen (si falta uno, se reparte su peso)."""
    subs = {"eficiencia": sub_eficiencia(fila.get("eficiencia")), "ctr": sub_ctr(fila.get("ctr_indice")),
            "posicion": sub_posicion(fila.get("posicion")), "seo": sub_seo(fila.get("pct_seo"))}
    validos = {k: v for k, v in subs.items() if v is not None}
    if not validos:
        return {"total": None, "subs": subs}
    peso = sum(PESOS_RENDIMIENTO[k] for k in validos)
    total = sum(v * PESOS_RENDIMIENTO[k] for k, v in validos.items()) / peso
    return {"total": round(total, 1), "subs": subs}
