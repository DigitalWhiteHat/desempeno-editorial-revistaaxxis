"""Piezas de presentación compartidas por las vistas (tarjetas HTML con el mismo CSS .perfil-sec)."""

import html

import streamlit as st

import datos as d
from calculos import miles

COLOR_CANAL = {"Google": "#1E6B3A", "Directo": "#7CB38E", "Pauta en redes": "#B07A1E", "Newsletter": "#3C5A78",
               "Redes sin pauta": "#9DB8D6", "Otros": "#B9B6B3"}
CSS_EXTRA = """
<style>
.lead-ax { background:#F2F4F3; border:1px solid #E4E4E4; border-radius:12px; padding:14px 18px; font-size:1.08rem;
  line-height:1.55; color:#231815; margin:0; }
.idea-ax { border:2px solid #0E2F4E; border-radius:12px; padding:12px 16px; margin:4px 0 10px 0; background:#FFFFFF; }
.idea-ax span.et { display:block; font-size:0.75rem; letter-spacing:0.08em; text-transform:uppercase; font-weight:700;
  color:#0E2F4E; margin-bottom:4px; }
.idea-ax p { margin:0; font-size:1.05rem; color:#231815; }
.idea-ax mark { background:#E8EDF3; color:#0E2F4E; font-weight:700; padding:0 3px; border-radius:3px; }
.chip-ax { display:inline-block; padding:3px 10px; border-radius:999px; font-size:0.9rem; margin:2px 4px 2px 0; }
.mini-ax { color:#5F6467; font-size:0.92rem; }
.barra-ax { display:flex; height:10px; border-radius:6px; overflow:hidden; background:#ECECEC; margin-top:4px; }
.leyenda-ax span { display:inline-flex; align-items:center; gap:5px; margin-right:12px; font-size:0.9rem; color:#5F6467; }
.leyenda-ax i { width:10px; height:10px; border-radius:2px; display:inline-block; }
</style>
"""


def css_extra():
    st.html(CSS_EXTRA)


def seccion(html_seccion: str, key: str) -> None:
    if not html_seccion or not html_seccion.strip():
        return
    with st.container(border=True, key=key):
        st.markdown(f'<div class="perfil-sec">{html_seccion}</div>', unsafe_allow_html=True)


def tabla(cabeceras: list, filas: list, alinear_der: set | None = None) -> str:
    alinear_der = alinear_der or set()
    th = "".join(f'<th style="text-align:{"right" if i in alinear_der else "left"}">{html.escape(h)}</th>'
                 for i, h in enumerate(cabeceras))
    tr = "".join("<tr>" + "".join(
        f'<td style="text-align:{"right" if i in alinear_der else "left"}">{c}</td>' for i, c in enumerate(f)) + "</tr>"
        for f in filas)
    return f'<div class="table-wrap"><table class="seo-tabla"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def idea(texto_html: str) -> None:
    st.markdown(f'<div class="idea-ax"><span class="et">Idea destacada</span><p>{texto_html}</p></div>',
                unsafe_allow_html=True)


def barra_canales(fila, total=None) -> str:
    """Barra partida por origen de los lectores (Google, directo, pauta, newsletter, redes, otros)."""
    total = total or sum(fila.get(f"lect_{k}", 0) for k, _ in d.CANALES) or 1
    partes = "".join(
        f'<div title="{n}: {miles(fila.get(f"lect_{k}", 0))}" style="width:{fila.get(f"lect_{k}", 0) / total * 100:.1f}%;'
        f'background:{COLOR_CANAL[n]}"></div>' for k, n in d.CANALES if fila.get(f"lect_{k}", 0) > 0)
    return f'<div class="barra-ax">{partes}</div>'


def leyenda_canales() -> str:
    return '<div class="leyenda-ax">' + "".join(
        f'<span><i style="background:{c}"></i>{n}</span>' for n, c in COLOR_CANAL.items()) + "</div>"


def desglose_canales(fila) -> str:
    partes = [f"{n} {miles(fila.get(f'lect_{k}', 0))}" for k, n in d.CANALES if fila.get(f"lect_{k}", 0) >= 1]
    return " · ".join(partes) if partes else "sin lectores medidos"


def enlace_nota(titulo: str, link: str) -> str:
    return f'<a href="{html.escape(link)}" target="_blank" style="color:#231815;text-decoration:none">{html.escape(titulo)}</a>'
