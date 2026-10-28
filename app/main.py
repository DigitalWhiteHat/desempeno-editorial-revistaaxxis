"""Desempeño Editorial — Revista AXXIS
Entrada: streamlit run app/main.py
"""

import streamlit as st

import datos as d
import general
import individual
import notas as vista_notas
import secciones as vista_secciones
import ui
from avatares import logo_axxis_data_uri
from estilos import inyectar_css

st.set_page_config(page_title="Desempeño Editorial — Revista AXXIS", layout="wide", page_icon="📊")
inyectar_css()
ui.css_extra()

meta = d.periodistas_meta()
if "vista" not in st.session_state:
    st.session_state.vista = "general"
if "periodista_slug" not in st.session_state:
    st.session_state.periodista_slug = meta[0]["slug"]
if "periodo" not in st.session_state:
    # Abre en todo 2026: en AXXIS cada persona publica de 0 a 5 notas al mes, y un mes solo deja leer poco.
    # Los meses siguen en el selector, con el mes en curso al final.
    st.session_state.periodo = d.ANO

NAV_ITEMS = [
    ("🏠", "Dashboard", "general"),
    ("🗂️", "Secciones y temas", "secciones"),
    ("📝", "Notas más vistas", "notas"),
]
VISTAS = {v for _, _, v in NAV_ITEMS}

with st.sidebar:
    st.markdown(f'<div style="padding:6px 2px 2px 2px"><img src="{logo_axxis_data_uri("blanco")}" '
                f'style="height:34px;width:auto;display:block"></div>', unsafe_allow_html=True)
    st.caption("Desempeño Editorial")
    st.write("")
    activa = st.session_state.vista if st.session_state.vista in VISTAS else "general"
    for icono, etiqueta, clave in NAV_ITEMS:
        st.button(f"{icono}  {etiqueta}", key=f"nav_{clave}", width="stretch",
                  type="primary" if activa == clave else "secondary",
                  on_click=lambda v=clave: st.session_state.update(vista=v))
    st.write("")
    c = d.corte()
    st.caption(f"Datos reales: GA4 hasta el {c['ga4'].day}-oct, Search Console hasta el {c['gsc'].day}-oct "
               f"y lectura en vivo de cada nota de 2026.")

st.markdown(
    f'<div class="cp-topbar"><div class="cp-brand">'
    f'<img src="{logo_axxis_data_uri("negro")}" class="cp-brand-logo-img" style="height:30px" alt="Revista AXXIS">'
    f'<span class="cp-brand-sep">|</span><span class="cp-brand-label">DESEMPEÑO EDITORIAL</span>'
    f'</div></div>', unsafe_allow_html=True)

_, col_periodo = st.columns([3, 2])
with col_periodo:
    codigos = [p for p, _ in d.periodos()]
    st.selectbox("📅 Periodo", codigos, index=codigos.index(st.session_state.periodo),
                 format_func=d.label_periodo, key="periodo", label_visibility="collapsed")

periodo = st.session_state.periodo

if st.session_state.vista == "individual":
    col_migas, col_sel = st.columns([3, 1])
    with col_migas:
        if st.button("← Volver al dashboard", key="volver"):
            st.session_state.vista = "general"
            st.rerun()
        st.markdown('<div class="cp-breadcrumb">Desempeño Editorial &nbsp;›&nbsp; <b>Perfil del periodista</b></div>',
                    unsafe_allow_html=True)
    nombres = [m["nombre"] for m in meta]
    actual = next((m["nombre"] for m in meta if m["slug"] == st.session_state.periodista_slug), nombres[0])
    with col_sel:
        elegido = st.selectbox("Cambiar periodista", nombres, index=nombres.index(actual), key="sel_periodista")
    slug_elegido = next(m["slug"] for m in meta if m["nombre"] == elegido)
    if slug_elegido != st.session_state.periodista_slug:
        st.session_state.periodista_slug = slug_elegido
        st.rerun()
    individual.render(st.session_state.periodista_slug, periodo)
elif st.session_state.vista == "secciones":
    vista_secciones.render(periodo)
elif st.session_state.vista == "notas":
    vista_notas.render(periodo)
else:
    elegido = general.render(periodo)
    if elegido:
        st.session_state.periodista_slug = elegido
        st.session_state.vista = "individual"
        st.rerun()
