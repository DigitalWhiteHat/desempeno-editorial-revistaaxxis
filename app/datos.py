"""Capa de datos del panel: lee data/processed/ (armado por data/construir.py y data/semaforo_seo.py) y calcula
cada tabla por periodo. Todo sale de Search Console, GA4 y la lectura en vivo de las notas de revistaaxxis.com.co.

Criterios (los mismos de la calculadora de referencia, adaptados a lo que AXXIS sí tiene):
- El mes de una nota es el mes en que se publicó. La tarjeta de un mes cuenta las notas PUBLICADAS ese mes, con
  el tráfico que hicieron ese mes. "Todo 2026" suma las notas publicadas en el año con su tráfico del año.
- Lectores = usuarios activos de GA4 en la nota (suma por mes). No se usan vistas de página: desde el 8-oct GA4
  cuenta vistas de más en este sitio.
- Eficiencia = clics de Google (Búsqueda + Discover) por nota, contra la mediana de las personas que firman ese
  periodo (100 = mediana). Se mide en Google y no en lectores porque la pauta en redes, que trae la mayoría de
  los lectores, la decide el área comercial y no quien escribe.
- Las firmas institucionales (Revista AXXIS sin firma personal, agencias) aparecen en las tablas del equipo pero no
  entran en la mediana ni en el ranking.
"""

import json
import os
import re
import unicodedata
from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed")
TTL = 300

MES_CORTO = {f"2026-{m:02d}": c for m, c in enumerate(["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct"], 1)}
MES_LARGO = {f"2026-{m:02d}": c for m, c in enumerate(["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                                                         "agosto", "septiembre", "octubre"], 1)}
MESES = list(MES_CORTO)
ANO = "2026"
TEMAS = {"obras": "Obras públicas, educativas y culturales en Colombia", "vivienda": "Casas y apartamentos en Colombia",
         "comercial": "Restaurantes, hoteles, tiendas y oficinas en Colombia",
         "territorio": "Crónicas de pueblos, ciudades y patrimonio de Colombia",
         "perfil": "Perfiles de arquitectos, diseñadores y firmas", "objetos": "Objetos, mobiliario, materiales y marcas",
         "exterior": "Proyectos fuera de Colombia", "agenda": "Ferias, premios, ediciones de la revista y eventos",
         "guias": "Guías, ideas y tendencias", "ensayos": "Columnas y ensayos"}
TEMAS_CORTO = {"obras": "Obras en Colombia", "vivienda": "Casas en Colombia", "comercial": "Comercial en Colombia",
               "territorio": "Territorio y patrimonio", "perfil": "Perfiles", "objetos": "Objetos y marcas",
               "exterior": "Proyectos en el exterior", "agenda": "Ferias y eventos", "guias": "Guías y tendencias",
               "ensayos": "Columnas"}
CANALES = [("google", "Google"), ("directo", "Directo"), ("pauta", "Pauta en redes"), ("newsletter", "Newsletter"),
           ("redes", "Redes sin pauta"), ("otros", "Otros")]
GANADO = ("google", "directo")
MIN_NOTAS_RANKING = 3  # con 1 o 2 notas, una sola nota con suerte decide el puesto  # lo que la nota se gana sola en buscadores y entradas directas


def slug(nombre: str) -> str:
    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


@st.cache_data(ttl=TTL)
def _crudo():
    n = json.load(open(os.path.join(BASE, "notas.json")))
    nm = json.load(open(os.path.join(BASE, "notas_mes.json")))
    sitio = json.load(open(os.path.join(BASE, "sitio.json")))
    cons = json.load(open(os.path.join(BASE, "consultas.json")))
    seo_path = os.path.join(BASE, "seo_notas.json")
    seo = json.load(open(seo_path)) if os.path.exists(seo_path) else None
    return n, nm, sitio, cons, seo


def corte():
    n, _, sitio, _, _ = _crudo()
    return {"ga4": date.fromisoformat(n["corte_ga4"]), "gsc": date.fromisoformat(n["corte_gsc"])}


def periodos():
    c = corte()["ga4"]
    out = [(m, f"{MES_LARGO[m].capitalize()} 2026") for m in MESES]
    out[-1] = ("2026-10", f"Octubre 2026 (parcial, hasta {c.day}-oct)")
    out.append((ANO, f"Todo 2026 (1-ene a {c.day}-oct)"))
    return out


def label_periodo(p):
    return dict(periodos())[p]


@st.cache_data(ttl=TTL)
def notas() -> pd.DataFrame:
    n, nm, _, _, seo = _crudo()
    df = pd.DataFrame(n["notas"])
    df = df[~df["despues_del_corte"]].copy()
    df["tema_label"] = df["tema"].map(TEMAS_CORTO)
    df["slug_firma"] = df["firma"].map(slug)
    df["tiempo_seg"] = df["ruta"].map(nm["tiempo_interaccion_seg"]).fillna(0)
    if seo:
        s = pd.DataFrame(seo["notas"]).set_index("ruta")
        df = df.join(s, on="ruta")
    return df


@st.cache_data(ttl=TTL)
def notas_mes() -> pd.DataFrame:
    _, nm, _, _, _ = _crudo()
    return pd.DataFrame(nm["filas"])


@st.cache_data(ttl=TTL)
def ctr_esperado() -> dict:
    """CTR de Google por tramo de posición, medido en todas las notas de 2026 (la curva propia del sitio)."""
    f = notas_mes()
    f = f[f["imp_web"] > 0].copy()
    f["pos"] = f["pos_x_imp"] / f["imp_web"]
    f["tramo"] = f["pos"].apply(_tramo)
    g = f.groupby("tramo")[["clics_web", "imp_web"]].sum()
    return (g["clics_web"] / g["imp_web"]).to_dict()


def _tramo(p):
    if p < 1.5:
        return 1
    if p <= 10:
        return int(round(p))
    if p <= 20:
        return 15
    if p <= 40:
        return 30
    return 50


def _filtro_periodo(df, periodo, col="mes"):
    return df if periodo == ANO else df[df[col] == periodo]


@st.cache_data(ttl=TTL)
def notas_periodo(periodo) -> pd.DataFrame:
    """Notas PUBLICADAS en el periodo con el tráfico que hicieron dentro del periodo."""
    n = notas()
    n = n if periodo == ANO else n[n["mes_pub"] == periodo]
    t = notas_mes()
    t = t if periodo == ANO else t[t["mes"] == periodo]
    agg = t.groupby("ruta").sum(numeric_only=True)
    df = n.join(agg, on="ruta")
    cols = [c for c in agg.columns]
    df[cols] = df[cols].fillna(0)
    df["clics"] = df["clics_web"] + df["clics_disc"]
    df["ganado"] = df["lect_google"] + df["lect_directo"]
    df["posicion"] = np.where(df["imp_web"] > 0, df["pos_x_imp"] / df["imp_web"].replace(0, np.nan), np.nan)
    exp = ctr_esperado()
    df["clics_esperados"] = [imp * exp.get(_tramo(p), 0) if imp > 0 and not np.isnan(p) else 0
                             for imp, p in zip(df["imp_web"], df["posicion"])]
    canal_cols = [f"lect_{k}" for k, _ in CANALES]
    df["canal_principal"] = df[canal_cols].idxmax(axis=1).str.replace("lect_", "").map(dict(CANALES))
    df.loc[df["lectores"] == 0, "canal_principal"] = "—"
    return df


def _periodistas_base():
    n = notas()
    base = (n.groupby(["firma", "tipo_firma"]).size().reset_index(name="notas_ano"))
    return base


@st.cache_data(ttl=TTL)
def periodistas_meta() -> list:
    """Todas las firmas de 2026 con su beat (tema y sección donde más publican)."""
    n = notas()
    out = []
    for firma, g in n.groupby("firma"):
        tema = g["tema"].value_counts().index[0]
        sec = g["seccion"].value_counts().index[0]
        out.append({"nombre": firma, "slug": slug(firma), "tipo": g["tipo_firma"].iloc[0], "notas_ano": len(g),
                    "seccion": sec, "beat": TEMAS_CORTO[tema], "beat_largo": TEMAS[tema]})
    orden = {"persona": 0, "redaccion": 1, "agencia": 2, "otros": 3}
    return sorted(out, key=lambda m: (orden[m["tipo"]], -m["notas_ano"]))


@st.cache_data(ttl=TTL)
def tabla_periodistas(periodo) -> pd.DataFrame:
    df = notas_periodo(periodo)
    if df.empty:
        return pd.DataFrame()
    meta = {m["nombre"]: m for m in periodistas_meta()}
    filas = []
    for firma, g in df.groupby("firma"):
        lect = g["lectores"].sum()
        canal = {k: g[f"lect_{k}"].sum() for k, _ in CANALES}
        imp = g["imp_web"].sum()
        filas.append({
            "periodista": firma, "slug": slug(firma), "tipo": g["tipo_firma"].iloc[0],
            "seccion": meta[firma]["seccion"], "beat": meta[firma]["beat"],
            "notas": len(g), "lectores": lect, **{f"lect_{k}": v for k, v in canal.items()},
            "ganado": canal["google"] + canal["directo"],
            "clics": g["clics"].sum(), "clics_web": g["clics_web"].sum(), "clics_disc": g["clics_disc"].sum(),
            "imp": imp, "posicion": (g["pos_x_imp"].sum() / imp) if imp else np.nan,
            "ctr": g["clics_web"].sum() / imp * 100 if imp else np.nan,
            "ctr_indice": (g["clics_web"].sum() / g["clics_esperados"].sum()) if g["clics_esperados"].sum() > 0 else np.nan,
            "clics_por_nota": g["clics"].sum() / len(g), "mediana_clics": g["clics"].median(),
            "lectores_por_nota": lect / len(g),
            "canal_dominante": max(canal, key=canal.get) if lect else "—",
            "tiempo_por_lector": (g["tiempo_seg"].sum() / max(1, notas_mes()[notas_mes()["ruta"].isin(g["ruta"])]["lectores"].sum())),
            "pct_seo": g["pct_seo"].mean() if "pct_seo" in g and g["pct_seo"].notna().any() else np.nan,
            "notas_seo": int(g["pct_seo"].notna().sum()) if "pct_seo" in g else 0,
            "sin_impresiones": int(((g["imp_web"] + g["imp_disc"]) == 0).sum()),
        })
    t = pd.DataFrame(filas)
    total_lect = t["lectores"].sum()
    t["pct_trafico_total"] = t["lectores"] / total_lect * 100 if total_lect else 0
    personas = t[t["tipo"] == "persona"]
    med = personas["clics_por_nota"].median() if len(personas) else np.nan
    t["eficiencia"] = np.where(t["tipo"] == "persona", t["clics_por_nota"] / med * 100 if med else np.nan, np.nan)
    t.loc[(t["tipo"] != "persona"), "eficiencia"] = t["clics_por_nota"] / med * 100 if med else np.nan
    t["mediana_equipo"] = med
    t["canal_dominante"] = t["canal_dominante"].map(dict(CANALES)).fillna("—")
    t["semaforo_rojo"] = (t["pct_seo"] < 60) & (t["notas_seo"] >= 3)
    t["en_alerta"] = (t["tipo"] == "persona") & (t["semaforo_rojo"].fillna(False) | ((t["eficiencia"] < 50) & (t["notas"] >= 3)))
    from calculos import puntaje_rendimiento
    t["puntaje"] = [puntaje_rendimiento(r)["total"] if r["tipo"] == "persona" else None for r in t.to_dict("records")]
    return t.sort_values("lectores", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=TTL)
def historial(firma) -> pd.DataFrame:
    """Mes a mes: notas publicadas ese mes, sus lectores y clics de ese mes, y la eficiencia contra el equipo."""
    filas = []
    for m in MESES:
        t = tabla_periodistas(m)
        if t.empty:
            continue
        r = t[t["periodista"] == firma]
        if r.empty:
            filas.append({"mes": m, "notas": 0, "lectores": 0, "clics": 0, "eficiencia": np.nan, "ganado": 0,
                          "lect_pauta": 0, "posicion": np.nan})
        else:
            r = r.iloc[0]
            filas.append({"mes": m, "notas": r["notas"], "lectores": r["lectores"], "clics": r["clics"],
                          "eficiencia": r["eficiencia"], "ganado": r["ganado"], "lect_pauta": r["lect_pauta"],
                          "posicion": r["posicion"]})
    return pd.DataFrame(filas)


def ranking(firma, periodo):
    t = tabla_periodistas(periodo)
    p = t[(t["tipo"] == "persona") & t["puntaje"].notna() & (t["notas"] >= MIN_NOTAS_RANKING)]
    p = p.sort_values(["puntaje", "clics"], ascending=False).reset_index(drop=True)
    pos = p.index[p["periodista"] == firma]
    return (int(pos[0]) + 1, len(p)) if len(pos) else None


# --- Sitio -----------------------------------------------------------------------------------------------------
@st.cache_data(ttl=TTL)
def sitio_mes() -> pd.DataFrame:
    _, _, s, _, _ = _crudo()
    df = pd.DataFrame([{"mes": k, **v} for k, v in s["mes"].items()]).fillna(0)
    web = pd.DataFrame(s["gsc_dia"]["web_dia"], columns=["dia", "clics", "imp"])
    disc = pd.DataFrame(s["gsc_dia"]["disc_dia"], columns=["dia", "clics", "imp"])
    corte_gsc = corte()["gsc"].isoformat()
    for nombre, d in (("clics_web", web), ("clics_disc", disc)):
        d = d[d["dia"] <= corte_gsc]
        g = d.groupby(d["dia"].str[:7])["clics"].sum()
        df[nombre] = df["mes"].map(g).fillna(0)
    return df.sort_values("mes").reset_index(drop=True)


@st.cache_data(ttl=TTL)
def secciones_mes() -> pd.DataFrame:
    _, _, s, _, _ = _crudo()
    return pd.DataFrame(s["seccion_mes"], columns=["seccion", "mes", "canal", "lectores"])


def proyeccion_mes(valor_actual, mes="2026-10"):
    """Regla de tres sobre los días con dato del mes en curso (no es un modelo)."""
    c = corte()["ga4"]
    if mes != f"{c.year}-{c.month:02d}":
        return None
    import calendar
    total = calendar.monthrange(c.year, c.month)[1]
    return {"valor_actual": valor_actual, "valor_proyectado": valor_actual / c.day * total,
            "dias_transcurridos": c.day, "dias_totales": total}


def consultas():
    return _crudo()[3]


def seo_meta():
    seo = _crudo()[4]
    return seo["meta"] if seo else None
