"""CSS y helpers de presentación para acercar la app a los mockups de referencia."""

import html
import re

import streamlit as st
import streamlit.components.v1 as components

COLOR_ESTADO = {"green": "#16A34A", "blue": "#0E2F4E", "red": "#DC2626", "orange": "#D97706", "gray": "#64748B"}
BG_ESTADO = {"green": "#DCFCE7", "blue": "#DBEAFE", "red": "#FEE2E2", "orange": "#FEF3C7", "gray": "#F1F5F9"}
TXT_ESTADO = {"green": "#166534", "blue": "#1E40AF", "red": "#991B1B", "orange": "#92400E", "gray": "#475569"}

BADGE_COLORS = {
    "purple": ("#EDE9FE", "#7C3AED"),
    "teal": ("#CCFBF1", "#0D9488"),
    "blue": ("#DBEAFE", "#2563EB"),
    "green": ("#DCFCE7", "#16A34A"),
}

CSS_GLOBAL = """
<style>
div[class*="st-key-card_"] {
    background: #FFFFFF;
    border-radius: 14px !important;
    border: 1px solid #E7EAF0 !important;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    padding: 6px 4px;
    height: 100%;
    box-sizing: border-box;
}
/* Tarjetas en la misma fila estiran a la misma altura, para que no se vean desordenadas. */
[data-testid="stColumn"]:has(div[class*="st-key-card_"]) {
    display: flex;
}
[data-testid="stColumn"] > [data-testid="stVerticalBlock"]:has(div[class*="st-key-card_"]),
[data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:has(div[class*="st-key-card_"]),
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"]:has(div[class*="st-key-card_"]) {
    height: 100%;
}
[data-testid="stMainBlockContainer"] {
    padding-top: 4rem;
    max-width: 1500px;
    margin: 0 auto;
}
.cp-topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 4px 0 14px 0; border-bottom: 1px solid #E7EAF0; margin-bottom: 18px;
}
.cp-brand { display: flex; align-items: center; gap: 10px; }
.cp-brand-logo { font-weight: 700; font-size: 1.05rem; color: #1C1A1A; }
.cp-brand-logo-img { height: 48px; width: auto; }
.cp-brand-sep { color: #C7CDD9; }
.cp-brand-label { font-size: 0.72rem; letter-spacing: 0.06em; font-weight: 600; color: #64748B; }
.cp-breadcrumb { color: #64748B; font-size: 1.1rem; margin: 2px 0 14px 0; }

/* Texto de contenido (st.caption y párrafos de st.markdown) — +3pt sobre el
   tamaño por defecto de Streamlit, que se veía demasiado pequeño. No toca
   títulos/encabezados ni los valores grandes de las tarjetas. */
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
    font-size: 1.05rem !important;
    line-height: 1.5 !important;
}
[data-testid="stMarkdownContainer"] p {
    font-size: 1.05rem;
    line-height: 1.55;
}
.cp-breadcrumb b { color: #1C1A1A; }

.cp-kpi-row { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 6px; }
.cp-kpi-card {
    background: #FFFFFF; border: 1px solid #E7EAF0; border-radius: 14px;
    padding: 16px 18px; box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}
.cp-kpi-label { font-size: 1.1rem; color: #64748B; display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.cp-kpi-value { font-size: 2.1rem; font-weight: 700; color: #1C1A1A; line-height: 1.1; }
.cp-kpi-delta { font-size: 1.05rem; font-weight: 600; margin-top: 5px; display: inline-block; }

.cp-pill {
    display: inline-block; padding: 3px 12px; border-radius: 999px;
    font-size: 1.02rem; font-weight: 700; letter-spacing: 0.02em;
}
.cp-delta {
    display: inline-flex; align-items: center; gap: 3px;
    font-size: 1.05rem; font-weight: 600;
}

.cp-metric-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; height: 100%; }
.cp-metric-card {
    background: #FFFFFF; border: 1px solid #E7EAF0; border-radius: 12px;
    padding: 14px 16px; box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    display: flex; flex-direction: column; justify-content: center;
}
.cp-metric-label { font-size: 1.05rem; color: #64748B; margin-bottom: 7px; line-height: 1.3; }
.cp-metric-value { font-size: 1.75rem; font-weight: 700; color: #1C1A1A; line-height: 1.15; }
.cp-metric-delta { font-size: 1.05rem; font-weight: 600; margin-top: 5px; }

.cp-icon-badge {
    width: 34px; height: 34px; border-radius: 9px; flex-shrink: 0;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 1.05rem; margin-bottom: 8px;
}
.cp-avatar-badge {
    width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 700; color: #FFFFFF; background: #334155;
}

.cp-card-title { font-size: 1.1rem; color: #64748B; margin-bottom: 6px; }
.cp-card-value { font-size: 1.9rem; font-weight: 700; color: #1C1A1A; line-height: 1.15; }
.cp-header-beat { font-size: 1.15rem; color: #334155; margin-top: 4px; font-weight: 500; }
.cp-card-desc { font-size: 1.05rem; color: #64748B; line-height: 1.4; margin-top: 2px; }

.cp-avatar-perfil {
    width: 112px !important; height: 112px !important; min-width: 112px !important;
    max-width: 112px !important; max-height: 112px !important;
    border-radius: 50% !important; object-fit: cover !important; flex-shrink: 0;
    border: 4px solid #FFFFFF; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.18);
    display: block;
}

.cp-nota-list { display: flex; flex-direction: column; }
.cp-nota-row {
    display: flex; align-items: center; gap: 16px;
    padding: 12px 4px; border-bottom: 1px solid #F1F3F7;
}
.cp-nota-row:last-child { border-bottom: none; }
.cp-nota-rank {
    width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
    background: #F1F5F9; color: #64748B; font-weight: 700; font-size: 0.9rem;
    display: flex; align-items: center; justify-content: center;
}
.cp-nota-rank.top { background: #DCFCE7; color: #166534; }
.cp-nota-info { flex: 1; min-width: 0; }
.cp-nota-titulo {
    font-weight: 600; color: #1C1A1A; font-size: 1rem;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.cp-nota-meta { font-size: 1rem; color: #64748B; margin-top: 2px; }
.cp-nota-bar-track { background: #F1F5F9; border-radius: 6px; height: 6px; margin-top: 7px; overflow: hidden; }
.cp-nota-bar-fill { height: 100%; border-radius: 6px; }
.cp-nota-trafico { text-align: right; flex-shrink: 0; min-width: 90px; }
.cp-nota-clics { font-weight: 700; color: #1C1A1A; font-size: 1.1rem; }
.cp-nota-pct { font-size: 0.95rem; color: #64748B; margin-top: 2px; }

@media (prefers-color-scheme: dark) {
    div[class*="st-key-card_"],
    .cp-kpi-card, .cp-metric-card { background: #10182B; border-color: #223052 !important; }
    .cp-kpi-value, .cp-metric-value, .cp-card-value { color: #E4E9F2; }
    .cp-topbar { border-color: #223052; }
    .cp-brand-logo { color: #E4E9F2; }
    .cp-breadcrumb b { color: #E4E9F2; }
    .cp-nota-row { border-color: #223052; }
    .cp-nota-titulo { color: #E4E9F2; }
    .cp-nota-clics { color: #E4E9F2; }
    .cp-nota-bar-track { background: #223052; }
    .cp-nota-rank { background: #223052; color: #94A3B8; }
}

/* Tarjetas del perfil (.perfil-sec). Ojo: dentro de esta hoja no puede ir nada con forma de etiqueta HTML,
   ni siquiera en un comentario, porque st.html() descartaría la hoja entera sin avisar. */
.perfil-sec h3.card-h { margin: 0 0 6px 0; font-size: 1.3rem; color: #1C1A1A; }
.perfil-sec p, .perfil-sec .cap { font-size: 1.05rem; line-height: 1.5; color: #64748B; margin: 4px 0; }
.perfil-sec img.chart { max-width: 100%; height: auto; display: block; margin: 10px 0; }
.perfil-sec details.exp { margin-top: 10px; }
.perfil-sec details.exp summary { cursor: pointer; font-weight: 600; color: #334155; padding: 6px 0; }
.perfil-sec table.seo-tabla { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 1rem; }
.perfil-sec table.seo-tabla th { text-align: left; color: #64748B; font-size: 0.9rem; padding: 8px 10px; border-bottom: 2px solid #E7EAF0; }
.perfil-sec table.seo-tabla td { padding: 10px; border-bottom: 1px solid #F1F3F6; vertical-align: top; color: #1C1A1A; }
.perfil-sec table.seo-tabla tr:last-child td { border-bottom: none; }
.perfil-sec .table-wrap { overflow-x: auto; }
@media (prefers-color-scheme: dark) {
    .perfil-sec h3.card-h { color: #E4E9F2; }
    .perfil-sec table.seo-tabla td { color: #E4E9F2; }
}
</style>
"""


SCRIPT_NO_TRANSLATE = """
<script>
(function() {
    // Streamlit Cloud renderiza la app dentro de un iframe -- el documento que Chrome
    // ofrece traducir es el EXTERIOR, no este. st.html() además filtra <script> y nunca
    // lo ejecuta -- por eso este script se llama vía components.html(), no st.html().
    function marcarNoTraducir(doc) {
        if (!doc) return;
        doc.documentElement.setAttribute('translate', 'no');
        if (!doc.querySelector('meta[name="google"]')) {
            const meta = doc.createElement('meta');
            meta.name = 'google';
            meta.content = 'notranslate';
            doc.head.appendChild(meta);
        }
    }
    marcarNoTraducir(document);
    try {
        if (window.top && window.top !== window) {
            marcarNoTraducir(window.top.document);
        }
    } catch (e) {
        // Cross-origin (no debería pasar en Streamlit Cloud, mismo origen) -- no hacer nada.
    }
})();
</script>
"""


SCRIPT_NOINDEX = """
<script>
(function() {
    // Mismo motivo que SCRIPT_NO_TRANSLATE: hay que llegar al documento exterior real
    // (Streamlit Cloud renderiza en iframe) y ejecutarse de verdad (via components.html).
    function marcarNoindex(doc) {
        if (doc && !doc.querySelector('meta[name="robots"]')) {
            const meta = doc.createElement('meta');
            meta.name = 'robots';
            meta.content = 'noindex, nofollow';
            doc.head.appendChild(meta);
        }
    }
    marcarNoindex(document);
    try {
        if (window.top && window.top !== window) {
            marcarNoindex(window.top.document);
        }
    } catch (e) {
        // Cross-origin (no debería pasar en Streamlit Cloud, mismo origen) -- no hacer nada.
    }
})();
</script>
"""


# Guarda: una etiqueta HTML dentro de la hoja de estilos hace que st.html() la descarte entera.
# una etiqueta HTML escrita por accidente dentro de la hoja de estilos hace que
# st.html() la descarte ENTERA, sin error -- la app arranca bien y simplemente se ve con
# los estilos de fábrica. Esto lo convierte en un fallo ruidoso al importar el módulo,
# que es cuando todavía se puede arreglar barato.
_RE_ETIQUETA_EN_CSS = re.compile(r"<\s*/?\s*[a-zA-Z]")


def _verificar_css(css: str) -> str:
    if css.count("<style>") != 1 or css.count("</style>") != 1:
        raise ValueError("CSS_GLOBAL debe tener exactamente un par de etiquetas style")
    cuerpo = css[css.index("<style>") + len("<style>"): css.index("</style>")]
    culpables = [ln.strip() for ln in cuerpo.splitlines() if _RE_ETIQUETA_EN_CSS.search(ln)]
    if culpables:
        raise ValueError(
            "CSS_GLOBAL tiene algo con forma de etiqueta HTML adentro; st.html() descartaría "
            "toda la hoja sin avisar. Líneas: " + " | ".join(culpables[:3]))
    return css


CSS_GLOBAL = _verificar_css(CSS_GLOBAL)


def inyectar_css():
    st.html(CSS_GLOBAL)
    # Evita que el traductor automático del navegador traduzca nombres de canales de Google
    # (Search, Discover, News) que deben quedarse tal cual.
    components.html(SCRIPT_NO_TRANSLATE, height=0, width=0)
    # Datos de desempeño por periodista con nombre propio -- nunca debe indexarse en
    # buscadores, sin importar en qué dominio/hosting termine viviendo esta app.
    components.html(SCRIPT_NOINDEX, height=0, width=0)


def pill(texto: str, color_key: str) -> str:
    return (f'<span class="cp-pill" style="background:{BG_ESTADO[color_key]};'
            f'color:{TXT_ESTADO[color_key]}">{html.escape(texto)}</span>')


def icon_badge(icono: str, color_key: str = "blue") -> str:
    bg, fg = BADGE_COLORS.get(color_key, BADGE_COLORS["blue"])
    return f'<div class="cp-icon-badge" style="background:{bg};color:{fg}">{icono}</div>'


def seccion_dificultad_row(label: str, dificultad: str, icono_canal: str, canal: str,
                            pct_canal: float, trafico_txt: str) -> str:
    color_key = {"Fácil": "green", "Media": "blue", "Difícil": "red"}.get(dificultad, "blue")
    bg, fg = BG_ESTADO[color_key], TXT_ESTADO[color_key]
    return (
        f'<div style="display:flex;align-items:center;justify-content:space-between;gap:14px;'
        f'background:{bg};border-radius:12px;padding:12px 16px;margin-bottom:8px">'
        f'<div style="min-width:0">'
        f'<div style="font-weight:700;font-size:1.05rem;color:#1C1A1A">{html.escape(label)}</div>'
        f'<div style="font-size:0.95rem;color:#475569;margin-top:2px">'
        f'{icono_canal} <span translate="no">{html.escape(canal)}</span> · {pct_canal:.0f}% de sus clics</div>'
        f'</div>'
        f'<div style="text-align:right;flex-shrink:0">'
        f'<div style="font-weight:700;color:{fg};font-size:0.95rem;letter-spacing:0.02em">{dificultad.upper()}</div>'
        f'<div style="font-size:0.9rem;color:#64748B;margin-top:2px">{html.escape(trafico_txt)} tráfico</div>'
        f'</div></div>'
    )


def avatar_badge(nombre: str) -> str:
    partes = nombre.split()
    iniciales = (partes[0][0] + partes[-1][0]).upper() if len(partes) > 1 else partes[0][:2].upper()
    return f'<div class="cp-avatar-badge">{html.escape(iniciales)}</div>'


def delta_html(actual: float, anterior, decimales: int = 0, es_bueno_si_sube: bool = True) -> str:
    if anterior in (0, None) or (hasattr(anterior, "__len__") is False and anterior != anterior):
        return '<span class="cp-delta" style="color:#94A3B8">— sin dato previo</span>'
    delta = (actual - anterior) / abs(anterior) * 100
    sube = delta >= 0
    bueno = sube if es_bueno_si_sube else not sube
    color = "#16A34A" if bueno else "#DC2626"
    flecha = "▲" if sube else "▼"
    signo = "+" if delta >= 0 else ""
    return f'<span class="cp-delta" style="color:{color}">{flecha} {signo}{delta:.{decimales}f}%</span>'


def card_value(titulo: str, valor: str) -> str:
    return (f'<div class="cp-card-title">{html.escape(titulo)}</div>'
            f'<div class="cp-card-value">{html.escape(valor)}</div>')


def trafico_card(valor: str, delta_html_str: str, secundario: str) -> str:
    delta_block = delta_html_str or '<span class="cp-delta" style="color:#94A3B8">—</span>'
    return (f'<div class="cp-kpi-card" style="height:100%">'
            f'<div class="cp-kpi-label">📊 Tráfico del periodo</div>'
            f'<div class="cp-kpi-value">{html.escape(valor)}</div>'
            f'<div class="cp-kpi-delta">{delta_block}</div>'
            f'<div class="cp-metric-label" style="margin-top:8px;margin-bottom:0">{html.escape(secundario)}</div>'
            f'</div>')


def metrica_card(label: str, valor: str, delta_html_str: str = "", icono: str = "", color_key: str = "blue") -> str:
    delta_block = delta_html_str or '<span class="cp-delta" style="color:#94A3B8">—</span>'
    badge = icon_badge(icono, color_key) if icono else ""
    return (f'<div class="cp-metric-card">'
            f'{badge}'
            f'<div class="cp-metric-label">{html.escape(label)}</div>'
            f'<div class="cp-metric-value">{html.escape(valor)}</div>'
            f'<div class="cp-metric-delta">{delta_block}</div>'
            f'</div>')


SEMAFORO_COLOR = {"🟢": "#16A34A", "🟡": "#F59E0B", "🔴": "#DC2626"}


def nota_row(rank: int, titulo: str, meta: str, clics_txt: str, pct_txt: str,
             barra_pct: float, semaforo: str, sufijo_pct: str = "del periodista",
             segmentos: list[tuple[float, str, str]] | None = None, detalle: str = "") -> str:
    """Una fila del ranking de notas.

    `segmentos` (opcional, lista de (porcentaje, color, etiqueta)): parte la barra por
    origen del tráfico. El largo de la barra es el tráfico de la nota y los colores dicen
    de dónde vino.

    `detalle` (opcional, HTML ya armado): una línea extra bajo la meta, para las cifras
    del desglose."""
    rank_cls = "cp-nota-rank top" if rank == 1 else "cp-nota-rank"
    ancho = max(4, min(100, barra_pct))
    if segmentos:
        partes = "".join(
            f'<div style="width:{pct:.1f}%;height:100%;background:{color}" title="{html.escape(etiqueta)}"></div>'
            for pct, color, etiqueta in segmentos if pct > 0
        )
        relleno = (f'<div class="cp-nota-bar-fill" style="width:{ancho}%;display:flex;'
                   f'overflow:hidden">{partes}</div>')
    else:
        relleno = (f'<div class="cp-nota-bar-fill" '
                   f'style="width:{ancho}%;background:{SEMAFORO_COLOR.get(semaforo, "#0E2F4E")}"></div>')
    detalle_html = f'<div class="cp-nota-meta">{detalle}</div>' if detalle else ""
    pct_html = html.escape(pct_txt) + (f" {html.escape(sufijo_pct)}" if sufijo_pct else "")
    return (f'<div class="cp-nota-row">'
            f'<div class="{rank_cls}">{rank}</div>'
            f'<div class="cp-nota-info">'
            f'<div class="cp-nota-titulo">{html.escape(titulo)}</div>'
            f'<div class="cp-nota-meta">{html.escape(meta)} {semaforo}</div>'
            f'{detalle_html}'
            f'<div class="cp-nota-bar-track">{relleno}</div>'
            f'</div>'
            f'<div class="cp-nota-trafico">'
            f'<div class="cp-nota-clics">{html.escape(clics_txt)}</div>'
            f'<div class="cp-nota-pct">{pct_html}</div>'
            f'</div>'
            f'</div>')


def ecuacion_titular_box(etiqueta: str, ecuacion: str, ejemplo: dict | None = None) -> str:
    """Caja destacada para una ecuación de titular, con el mismo estilo en todas las vistas.

    ejemplo (opcional): dict de dr.ejemplo_titular_* -- una nota REAL que ya trae varias de las
    piezas de la ecuación, para que se vea cómo se escribe en la práctica, no solo la fórmula
    abstracta."""
    ejemplo_html = ""
    if ejemplo:
        trafico_fmt = f"{ejemplo['trafico']:,.0f}".replace(",", ".")
        ejemplo_html = (
            f'<div class="cp-nota-meta" style="margin-top:6px;font-style:italic">'
            f'📰 Ejemplo real: “{html.escape(ejemplo["titulo"])}” — {trafico_fmt} de tráfico '
            f'({ejemplo["rasgos_presentes"]}/{ejemplo["rasgos_totales"]} piezas de la ecuación)</div>'
        )
    return (
        f'<div class="cp-nota-row" style="background:#F1F5F9;border-radius:10px;padding:12px 16px">'
        f'<div class="cp-nota-info"><div class="cp-nota-meta" style="font-size:0.95rem">🧮 {html.escape(etiqueta.upper())}</div>'
        f'<div class="cp-nota-titulo" style="white-space:normal">{ecuacion}</div>{ejemplo_html}</div></div>'
    )


def kpi_card(icono: str, label: str, valor: str, delta_html_str: str = "", help_text: str = "") -> str:
    delta_block = delta_html_str or '<span class="cp-delta" style="color:#94A3B8">—</span>'
    label_seguro = html.escape(label)
    valor_seguro = html.escape(valor)
    if help_text:
        titulo = f'<span title="{html.escape(help_text)}">{label_seguro}</span>'
    else:
        titulo = label_seguro
    return (f'<div class="cp-kpi-card">'
            f'<div class="cp-kpi-label">{icono} {titulo}</div>'
            f'<div class="cp-kpi-value">{valor_seguro}</div>'
            f'<div class="cp-kpi-delta">{delta_block}</div>'
            f'</div>')
