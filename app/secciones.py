"""Secciones y temas: dónde está el tráfico del sitio y qué tema rinde, sin importar quién firma."""

import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import datos as d
import ui
from calculos import decimal, formatear_numero, miles
from estilos import kpi_card

NOMBRES = {"arquitectura": "Arquitectura", "diseno": "Diseño", "decoracion": "Decoración", "especiales": "Especiales",
           "(portada)": "Portada", "revistaaxxis": "Revista AXXIS"}


def _base(periodo):
    df = d.notas_periodo(periodo)
    if periodo == d.ANO:
        df = df[df["mes_pub"] < "2026-10"]
    return df


def _panorama(periodo):
    st.subheader(f"Panorama del sitio — {d.label_periodo(periodo)}")
    sm = d.sitio_mes()
    sm = sm[sm["mes"] >= "2026-01"] if periodo == d.ANO else sm[sm["mes"] == periodo]
    df = d.notas_periodo(periodo)
    tarjetas = [kpi_card("🌐", "Sesiones del sitio", formatear_numero(sm["sesiones"].sum())),
                kpi_card("🔍", "Sesiones desde Google", formatear_numero(sm["ses_google"].sum())),
                kpi_card("📣", "Sesiones por pauta", formatear_numero(sm["ses_pauta"].sum())),
                kpi_card("📝", "Notas publicadas", miles(len(df))),
                kpi_card("🗂️", "Temas con notas", str(df["tema"].nunique())),
                kpi_card("✍️", "Firmas con notas", str(df["firma"].nunique()))]
    st.markdown(f'<div class="cp-kpi-row">{"".join(tarjetas)}</div>', unsafe_allow_html=True)


def _por_seccion(periodo):
    st.subheader("Lectores por sección y por dónde llegan")
    st.caption("Lectores de GA4 de todas las páginas de cada sección (notas nuevas y viejas) en el periodo, partidos por canal.")
    s = d.secciones_mes()
    s = s[s["mes"] >= "2026-01"] if periodo == d.ANO else s[s["mes"] == periodo]
    s = s[s["seccion"].isin(NOMBRES)]
    g = s.groupby(["seccion", "canal"])["lectores"].sum().unstack(fill_value=0)
    g["total"] = g.sum(axis=1)
    g = g.sort_values("total")
    fig = go.Figure()
    for k, n in d.CANALES:
        if k in g:
            fig.add_trace(go.Bar(y=[NOMBRES[x] for x in g.index], x=g[k], name=n, orientation="h",
                                 marker_color=ui.COLOR_CANAL[n], hovertemplate=f"{n}: %{{x:,.0f}}<extra></extra>"))
    fig.update_layout(barmode="stack", height=300, margin=dict(l=0, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis=dict(gridcolor="#E4E4E4"))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    arq = g.loc["arquitectura", "total"] / g["total"].sum() * 100 if "arquitectura" in g.index else 0
    ui.idea(f"Arquitectura reúne <mark>{decimal(arq, 0)} % de los lectores</mark> de las secciones en el periodo.")


def _por_tema(periodo):
    df = _base(periodo)
    st.subheader("Qué tema rinde")
    st.caption("Cuenta toda nota del periodo, tenga o no firma personal. Clics de Google = Búsqueda y Discover de Search Console. "
               + ("En \"Todo 2026\" se usan las notas de enero a septiembre, para que todas hayan tenido al menos un mes de vida."
                  if periodo == d.ANO else ""))
    if df.empty:
        return
    med_sitio = df["clics"].median()
    filas = []
    for tema, g in df.groupby("tema"):
        filas.append({"tema": d.TEMAS[tema], "notas": len(g), "pct": len(g) / len(df) * 100, "med": g["clics"].median(),
                      "diez": (g["clics"] >= 10).mean() * 100, "lect": g["lectores"].median(),
                      "pauta": g["lect_pauta"].sum() / max(1, g["lectores"].sum()) * 100})
    filas.sort(key=lambda f: -f["med"])
    rows = [[html.escape(f["tema"]), f["notas"], f"{decimal(f['pct'], 0)} %", decimal(f["med"]), f"{decimal(f['diez'], 0)} %",
             miles(f["lect"]), f"{decimal(f['pauta'], 0)} %"] for f in filas]
    ui.seccion(ui.tabla(["Tema", "Notas", "% de lo publicado", "Clics Google (nota típica)", "Notas con 10+ clics",
                         "Lectores (nota típica)", "% por pauta"], rows, {1, 2, 3, 4, 5, 6}), "card_temas")
    st.caption(f"Nota típica del sitio en el periodo: {decimal(med_sitio)} clics de Google.")
    reforzar = [f for f in filas if f["med"] >= 2 * med_sitio and f["pct"] < 15 and f["notas"] >= 5][:3]
    reducir = [f for f in filas if f["med"] <= 0.5 * med_sitio and f["pct"] >= 20]
    st.subheader("Propuesta de redistribución editorial")
    st.caption("Cruce de lo que rinde cada tema en Google con cuánto se publica de él. Es un punto de partida con datos: la decisión "
               "es de la dirección editorial.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🟢 Temas para reforzar** (los 3 que más rinden entre los que doblan la nota típica, tienen 5 notas o más y son menos del 15 % de lo publicado)")
        for f in reforzar:
            st.markdown(f"- **{f['tema']}** — {decimal(f['med'])} clics la nota típica · {f['notas']} notas ({decimal(f['pct'], 0)} %)")
        if not reforzar:
            st.caption("Ningún tema cumple las dos condiciones en este periodo.")
    with c2:
        st.markdown("**🔴 Temas para reducir** (rinden la mitad de la nota típica o menos y son 20 % o más de lo publicado)")
        for f in reducir:
            st.markdown(f"- **{f['tema']}** — {decimal(f['med'])} clics la nota típica · {f['notas']} notas ({decimal(f['pct'], 0)} %)")
        if not reducir:
            st.caption("Ningún tema cumple las dos condiciones en este periodo.")


def _especializacion(periodo):
    df = _base(d.ANO)
    st.subheader("Especialización: en qué tema le rinde escribir a cada persona")
    st.caption("Cruce persona × tema con las notas de enero a septiembre de 2026 (no cambia con el periodo de arriba: es para "
               "decidir). Confianza según cuántas notas hay: 🟢 alta (10 o más) · 🟡 media (3 a 9) · ⚪ baja (menos de 3, solo indicativo).")
    for firma, g in df[df["tipo_firma"] == "persona"].groupby("firma"):
        with st.expander(f"{firma} — {g['tema'].nunique()} tema(s) en {len(g)} notas"):
            rows = []
            for tema, gg in g.groupby("tema"):
                conf = "🟢" if len(gg) >= 10 else "🟡" if len(gg) >= 3 else "⚪"
                rows.append([d.TEMAS[tema], len(gg), decimal(gg["clics"].median()), miles(gg["lectores"].median()), conf,
                             gg["clics"].median()])
            rows.sort(key=lambda r: -r[5])
            st.markdown('<div class="perfil-sec">' + ui.tabla(["Tema", "Notas", "Clics Google (nota típica)",
                                                                "Lectores (nota típica)", "Confianza"], [r[:5] for r in rows], {1, 2, 3})
                        + "</div>", unsafe_allow_html=True)


def render(periodo):
    _panorama(periodo)
    st.write("")
    _por_seccion(periodo)
    st.write("")
    _por_tema(periodo)
    st.write("")
    _especializacion(periodo)
