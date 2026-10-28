"""Notas más vistas del periodo, con filtros por firma, sección, tema y canal."""

import pandas as pd
import streamlit as st

import datos as d
from calculos import formatear_numero, miles


def render(periodo):
    df = d.notas_periodo(periodo).copy()
    st.info(f"**{d.label_periodo(periodo)}** — notas publicadas en el periodo con sus lectores (GA4) y clics de Google "
            "(Search Console) dentro del periodo. El semáforo SEO de cada nota sale de la lectura en vivo del sitio.", icon="📊")
    st.caption(f"{len(df)} notas. Filtra por firma, sección, tema o canal principal, o busca una palabra del titular.")
    c1, c2, c3, c4, c5 = st.columns([2, 1.3, 1, 1.3, 1])
    q = c1.text_input("Buscar en el titular", placeholder="ej. Bogotá, casa, Salmona")
    firma = c2.selectbox("Firma", ["Todas"] + sorted(df["firma"].unique()))
    sec = c3.selectbox("Sección", ["Todas"] + sorted(df["seccion"].unique()))
    tema = c4.selectbox("Tema", ["Todos"] + sorted(df["tema_label"].unique()))
    canal = c5.selectbox("Canal principal", ["Todos"] + [n for _, n in d.CANALES])
    if q:
        df = df[df["titular"].str.contains(q, case=False, na=False)]
    if firma != "Todas":
        df = df[df["firma"] == firma]
    if sec != "Todas":
        df = df[df["seccion"] == sec]
    if tema != "Todos":
        df = df[df["tema_label"] == tema]
    if canal != "Todos":
        df = df[df["canal_principal"] == canal]
    orden = st.radio("Ordenar por", ["Lectores", "Clics de Google"], horizontal=True)
    df = df.sort_values("lectores" if orden == "Lectores" else "clics", ascending=False)
    st.caption(f"{len(df)} notas encontradas · {miles(df['lectores'].sum())} lectores · {miles(df['clics'].sum())} clics de Google")
    df["pauta_pct"] = (df["lect_pauta"] / df["lectores"].replace(0, pd.NA) * 100)
    df["seo"] = df.get("pct_seo", pd.Series(index=df.index, dtype=float)).apply(
        lambda x: "⚪" if pd.isna(x) else f"{'🟢' if x >= 80 else '🟡' if x >= 60 else '🔴'} {x:.0f} %")
    v = df[["titular", "link", "firma", "fecha", "seccion", "tema_label", "lectores", "pauta_pct", "clics", "posicion",
            "canal_principal", "seo"]]
    st.dataframe(v, hide_index=True, width="stretch", height=640, column_config={
        "titular": st.column_config.TextColumn("Titular", width="large"),
        "link": st.column_config.LinkColumn("Enlace", display_text="abrir", width="small"),
        "firma": st.column_config.TextColumn("Firma"), "fecha": st.column_config.TextColumn("Publicada"),
        "seccion": st.column_config.TextColumn("Sección"), "tema_label": st.column_config.TextColumn("Tema"),
        "lectores": st.column_config.NumberColumn("Lectores", format="localized"),
        "pauta_pct": st.column_config.NumberColumn("% por pauta", format="%.0f %%"),
        "clics": st.column_config.NumberColumn("Clics Google", format="localized"),
        "posicion": st.column_config.NumberColumn("Posición", format="%.1f"),
        "canal_principal": st.column_config.TextColumn("Canal principal"),
        "seo": st.column_config.TextColumn("Semáforo SEO")})
