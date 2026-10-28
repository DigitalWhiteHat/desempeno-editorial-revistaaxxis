"""Dashboard: desempeño editorial de todo el equipo en el periodo elegido."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import datos as d
import titulares as tit
import ui
from avatares import avatar_data_uri
from calculos import decimal, estado_label, formatear_numero, miles
from estilos import BG_ESTADO, TXT_ESTADO, kpi_card
from google_updates import UPDATES_2026
from graficos import agregar_proyeccion, texto_metodologia_proyeccion

COLOR_ESTADO = {"green": "#16A34A", "blue": "#0E2F4E", "red": "#DC2626"}
ESTADO_STYLE = {lbl: f"background-color:{BG_ESTADO[k]};color:{TXT_ESTADO[k]};font-weight:600;border-radius:6px"
                for lbl, k in [("SOBRE MEDIANA", "green"), ("EN RANGO", "blue"), ("EN ALERTA", "red")]}
ARTICULO_CANAL = {"Google": "Google", "Directo": "entrada directa", "Pauta en redes": "la pauta en redes",
                  "Newsletter": "el newsletter", "Redes sin pauta": "redes sin pauta", "Otros": "otros canales"}
COLOR_UPDATE = {"Core": "#B07A1E", "Spam": "#DC2626", "Discover": "#64748B"}


def _banner(periodo):
    if periodo == d.ANO:
        txt = (f"**{d.label_periodo(periodo)}** — cada nota publicada en 2026 con todo su tráfico del año. Es la "
               "lectura principal: en AXXIS cada persona publica pocas notas al mes y un solo mes deja poco para comparar.")
    else:
        txt = (f"**{d.label_periodo(periodo)}** — las notas PUBLICADAS ese mes, con el tráfico que hicieron dentro de "
               "ese mes. Una nota publicada al final del mes todavía no muestra todo lo que va a rendir.")
    st.info(txt, icon="📊")


def _kpis(t):
    personas = t[t["tipo"] == "persona"]
    canal = {n: t[f"lect_{k}"].sum() for k, n in d.CANALES}
    canal_top = max(canal, key=canal.get) if t["lectores"].sum() else "—"
    tarjetas = [
        kpi_card("👥", "Periodistas activos", f"{len(personas)}", help_text="Personas con al menos una nota publicada en el periodo. "
                 "Revista AXXIS sin firma personal y las agencias aparecen aparte."),
        kpi_card("⚠️", "En alerta", f"{int(personas['en_alerta'].sum())}", help_text="Semáforo SEO en rojo (con 3 notas leídas o más), o eficiencia "
                 "por debajo de la mitad de la mediana con 3 notas o más. El detalle está en el perfil de cada persona."),
        kpi_card("📈", "Eficiencia mediana", "100", help_text="Índice: 100 = clics de Google por nota de la persona del medio. "
                 f"Este periodo, la mediana es {decimal(t['mediana_equipo'].iloc[0])} clics por nota."),
        kpi_card("📝", "Notas publicadas", miles(t["notas"].sum())),
        kpi_card("👀", "Lectores de esas notas", formatear_numero(t["lectores"].sum())),
        kpi_card("📡", "Canal dominante", canal_top),
    ]
    st.markdown(f'<div class="cp-kpi-row">{"".join(tarjetas)}</div>', unsafe_allow_html=True)


def _tendencia():
    s = d.sitio_mes()
    s = s[s["mes"] >= "2026-01"].copy()
    s["x"] = s["mes"].map(d.MES_CORTO)
    st.subheader(f"Tendencia del sitio — {len(s)} meses (enero-octubre 2026)")
    st.caption("Sesiones reales de GA4 de todo revistaaxxis.com.co cada mes, y cuántas llegaron desde Google y desde la "
               "pauta en redes. Las marcas de color son actualizaciones de Google: pasa el mouse para ver cuál.")
    fig = go.Figure()
    for col, nombre, color, ancho in (("sesiones", "Sesiones totales", "#231815", 3), ("ses_pauta", "Desde la pauta en redes", "#B07A1E", 2),
                                      ("ses_google", "Desde Google", "#1E6B3A", 2)):
        fig.add_trace(go.Scatter(x=s["x"], y=s[col], mode="lines+markers+text", name=nombre,
                                 line=dict(color=color, width=ancho), marker=dict(size=7),
                                 text=[formatear_numero(v) if col == "sesiones" else "" for v in s[col]], textposition="top center",
                                 hovertemplate=f"{nombre}<br>%{{x}}: %{{y:,.0f}}<extra></extra>"))
    proy = d.proyeccion_mes(float(s.iloc[-1]["sesiones"]))
    if proy:
        agregar_proyeccion(fig, proy, s.iloc[-1]["x"], "Oct (proy.)", color="#231815")
    for u in UPDATES_2026:
        m = f"2026-{u['inicio'].month:02d}"
        if m in set(s["mes"]):
            y = float(s.loc[s["mes"] == m, "sesiones"].iloc[0])
            fig.add_trace(go.Scatter(x=[d.MES_CORTO[m]], y=[y], mode="markers", showlegend=False,
                                     marker=dict(size=15, color="rgba(0,0,0,0)", line=dict(color=COLOR_UPDATE[u["tipo"]], width=2)),
                                     hovertemplate=f"{u['nombre']}<br>desde el {u['inicio'].day}-{u['inicio'].month}<extra></extra>"))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=-0.15),
                      yaxis=dict(gridcolor="#E4E4E4", tickformat=",.0f"), xaxis=dict(showgrid=False))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    if proy:
        st.caption(texto_metodologia_proyeccion(proy))
    pauta = s["ses_pauta"].sum() / s["sesiones"].sum() * 100
    google = s["ses_google"].sum() / s["sesiones"].sum() * 100
    ui.idea(f"En 2026, <mark>{decimal(pauta, 0)} % de las sesiones llegó por la pauta en redes</mark> y {decimal(google, 0)} % "
            "desde Google. La línea total sube y baja con la pauta; la de Google se mueve poco mes a mes.")
    with st.expander("Ver las cifras de la gráfica"):
        tabla = s[["mes", "sesiones", "lectores", "ses_pauta", "ses_google", "ses_directo", "ses_newsletter", "clics_web", "clics_disc"]].copy()
        tabla["mes"] = tabla["mes"].map(lambda m: d.MES_LARGO[m].capitalize())
        tabla.columns = ["Mes", "Sesiones", "Lectores", "Pauta", "Google", "Directo", "Newsletter", "Clics Búsqueda (SC)", "Clics Discover (SC)"]
        st.dataframe(tabla, hide_index=True, width="stretch")
        st.caption(f"Clics de Search Console hasta el {d.corte()['gsc'].day}-oct (último día con dato final). "
                   "Sesiones y lectores de GA4 hasta el " f"{d.corte()['ga4'].day}-oct.")


def _que_cambia(periodo):
    """Qué está bajando y qué está subiendo: ritmo diario del mes contra el mes anterior."""
    mes = periodo if periodo != d.ANO else "2026-10"
    i = d.MESES.index(mes)
    if i == 0:
        return
    ant = d.MESES[i - 1]
    c = d.corte()["ga4"]
    import calendar
    dias = {m: (c.day if m == f"{c.year}-{c.month:02d}" else calendar.monthrange(2026, int(m[5:]))[1]) for m in (mes, ant)}
    sec = d.secciones_mes()
    nombres = {"arquitectura": "Arquitectura", "diseno": "Diseño", "decoracion": "Decoración", "especiales": "Especiales",
               "(portada)": "Portada", "revistaaxxis": "Revista AXXIS"}
    sec = sec[sec["seccion"].isin(nombres)]
    g = sec.groupby(["seccion", "mes"])["lectores"].sum().unstack(fill_value=0)
    filas = []
    for s_, r in g.iterrows():
        a, b = r.get(mes, 0) / dias[mes], r.get(ant, 0) / dias[ant]
        if b >= 20:
            filas.append((nombres[s_], a, b, (a / b - 1) * 100))
    sm = d.sitio_mes().set_index("mes")
    canales = []
    for k, n in (("pauta", "Pauta en redes"), ("google", "Google"), ("directo", "Directo"), ("newsletter", "Newsletter"), ("redes", "Redes sin pauta")):
        a, b = sm.loc[mes, f"ses_{k}"] / dias[mes], sm.loc[ant, f"ses_{k}"] / dias[ant]
        if b >= 20:
            canales.append((n, a, b, (a / b - 1) * 100))
    tab_baja, tab_sube = st.tabs(["⚠️ Qué está bajando", "📈 Qué está subiendo"])
    for tab, signo in ((tab_baja, -1), (tab_sube, 1)):
        with tab:
            st.caption(f"Ritmo diario, {d.MES_LARGO[mes]} ({dias[mes]} días) contra {d.MES_LARGO[ant]} ({dias[ant]} días), "
                       "para que un mes parcial no se vea peor solo por tener menos días.")
            hubo = False
            st.markdown("**Por sección** (lectores por día):")
            for n, a, b, p in sorted(filas, key=lambda x: signo * -x[3]):
                if signo * p > 3:
                    hubo = True
                    st.markdown(f"{'🔻' if signo < 0 else '🔺'} **{n}** — {miles(a)}/día en {d.MES_LARGO[mes]} contra "
                                f"{miles(b)}/día en {d.MES_LARGO[ant]} ({'+' if p >= 0 else ''}{decimal(p, 0)} %)")
            st.markdown("**Por canal** (sesiones por día, todo el sitio):")
            for n, a, b, p in sorted(canales, key=lambda x: signo * -x[3]):
                if signo * p > 3:
                    hubo = True
                    st.markdown(f"{'🔻' if signo < 0 else '🔺'} **{n}** — {miles(a)}/día contra {miles(b)}/día "
                                f"({'+' if p >= 0 else ''}{decimal(p, 0)} %)")
            if not hubo:
                st.caption("Nada se mueve más de 3 % en este sentido.")


def _barras(t, col, titulo, cap, fmt):
    st.subheader(titulo)
    st.caption(cap)
    o = t.sort_values(col, ascending=True)
    colores = [COLOR_ESTADO[estado_label(r.eficiencia, r.en_alerta)[1]] if r.tipo == "persona" else "#B9B6B3"
               for r in o.itertuples()]
    fig = go.Figure(go.Bar(x=o[col], y=o["periodista"], orientation="h", marker_color=colores,
                           text=[fmt(v, r) for v, r in zip(o[col], o.itertuples())], textposition="outside",
                           hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>"))
    fig.update_layout(height=max(280, 32 * len(o)), margin=dict(l=0, r=70, t=10, b=10), showlegend=False,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(showgrid=True, gridcolor="#E4E4E4"), yaxis=dict(automargin=True))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def _nombre_corto(nombre):
    """Nombre y primer apellido: cabe en la gráfica y no se confunde (dos personas tienen las iniciales MB)."""
    p = nombre.split()
    return " ".join(p[:2]) if len(p) > 2 else nombre


def _ubicar_etiquetas(px, py, textos, ancho, alto, radio=14):
    """Coloca cada nombre junto a su punto sin pisar otros nombres ni otros puntos ni salirse del área.
    Trabaja en píxeles: prueba posiciones alrededor del punto (arriba, abajo, a la derecha y a la izquierda, cada vez
    más lejos) y se queda con la primera libre; si ninguna está libre, con la que menos se cruza."""
    def cruce(a, b):
        return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))

    puestas, salida = [], []
    for k in np.argsort(py):  # de arriba hacia abajo
        w, h = len(textos[k]) * 7.2 + 12, 18
        lado = w / 2 + radio + 4
        candidatos = [(0, -26), (0, 26), (lado, 0), (-lado, 0), (lado, -20), (lado, 20), (-lado, -20), (-lado, 20),
                      (0, -44), (0, 44), (lado, -38), (lado, 38), (-lado, -38), (-lado, 38), (0, -62), (0, 62),
                      (lado + 30, -56), (lado + 30, 56), (-lado - 30, -56), (-lado - 30, 56), (0, -80), (0, 80)]
        mejor = None
        for dx, dy in candidatos:
            cx, cy = px[k] + dx, py[k] + dy
            caja = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            castigo = sum(cruce(caja, b) for b in puestas)
            castigo += sum(cruce(caja, (qx - radio, qy - radio, qx + radio, qy + radio)) for qx, qy in zip(px, py))
            fuera = max(0, 2 - caja[0]) + max(0, caja[2] - ancho + 2) + max(0, 2 - caja[1]) + max(0, caja[3] - alto + 2)
            castigo += fuera * 1000
            if mejor is None or castigo < mejor[0]:
                mejor = (castigo, dx, dy, caja)
            if castigo == 0:
                break
        puestas.append(mejor[3])
        salida.append((k, mejor[1], mejor[2]))
    return salida


def _cuadrante(t):
    st.subheader("Volumen de notas vs. eficiencia")
    st.caption("Cada punto es una persona que firma, con sus iniciales y su nombre. Haz clic en un punto para abrir su perfil. "
               "Quien no tuvo ningún clic de Google en el periodo aparece en la línea de abajo (\"0\").")
    p = t[t["tipo"] == "persona"].copy().reset_index(drop=True)
    if p.empty:
        return None
    notas = p["notas"].to_numpy(float)
    # Escala logarítmica también en X: la mayoría firma de 1 a 10 notas y unas pocas personas, más de 40; en escala
    # lineal los puntos de la izquierda quedan amontonados y los nombres se pisan.
    x = np.log10(notas)
    y_real = p["eficiencia"].fillna(0).to_numpy(float)
    piso = 3.0  # quien tiene eficiencia 0 se dibuja en el piso, rotulado "0"
    y = np.log10(np.clip(y_real, piso, None))
    x_mid, y_mid = float(np.log10(np.median(notas))), 2.0
    xr = (-0.12, max(x.max(), np.log10(20)) + 0.12)
    yr = (np.log10(piso) - 0.25, max(y.max(), np.log10(300)) + 0.35)
    xticks = [v for v in [1, 2, 3, 5, 10, 20, 30, 50, 100] if xr[0] <= np.log10(v) <= xr[1]]
    ticks = [v for v in [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000] if yr[0] <= np.log10(v) <= yr[1]]
    tickvals = [np.log10(piso)] + [np.log10(v) for v in ticks]
    ticktext = ["0"] + [miles(v) for v in ticks]
    alto, m = 520, dict(l=70, r=20, t=20, b=50)
    ancho_area, alto_area = 780, alto - m["t"] - m["b"]  # ancho conservador: en pantallas más angostas no se pisan
    fig = go.Figure()
    zonas = [(xr[0], x_mid, y_mid, yr[1], "#FEF3C7", "ALTA EFICIENCIA · POCAS NOTAS", "left", "top"),
             (x_mid, xr[1], y_mid, yr[1], "#DCFCE7", "ZONA IDEAL · EFICIENCIA Y VOLUMEN", "right", "top"),
             (xr[0], x_mid, yr[0], y_mid, "#F1F5F9", "BAJA EFICIENCIA · POCAS NOTAS", "left", "bottom"),
             (x_mid, xr[1], yr[0], y_mid, "#FEE2E2", "ZONA DE REVISIÓN · MUCHAS NOTAS, BAJA EFICIENCIA", "right", "bottom")]
    for x0, x1, y0, y1, c, lbl, ha, va in zonas:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1, fillcolor=c, opacity=0.5, line_width=0, layer="below")
        fig.add_annotation(x=x0 if ha == "left" else x1, y=y1 if va == "top" else y0, text=lbl, showarrow=False,
                           xanchor=ha, yanchor=va, xshift=6 if ha == "left" else -6, yshift=-4 if va == "top" else 4,
                           font=dict(size=10, color="#64748B"))
    fig.add_shape(type="line", x0=x_mid, x1=x_mid, y0=yr[0], y1=yr[1], line=dict(color="#94A3B8", dash="dash", width=1))
    fig.add_shape(type="line", x0=xr[0], x1=xr[1], y0=y_mid, y1=y_mid, line=dict(color="#94A3B8", dash="dash", width=1))
    # Dos personas con las mismas notas y una eficiencia parecida quedarían una encima de la otra: se corre la segunda
    # unos píxeles a un lado (el valor exacto sigue en el recuadro que aparece al pasar el mouse).
    paso = 30 / ancho_area * (xr[1] - xr[0])
    puestos = []
    for k in np.argsort(-y):
        for desplazo in (0, 1, -1, 2, -2, 3, -3):
            xk = x[k] + desplazo * paso
            pxk, pyk = (xk - xr[0]) / (xr[1] - xr[0]) * ancho_area, (yr[1] - y[k]) / (yr[1] - yr[0]) * alto_area
            if all((pxk - a) ** 2 + (pyk - b) ** 2 >= 30 ** 2 for a, b in puestos):
                break
        x[k] = xk
        puestos.append((pxk, pyk))
    iniciales = ["".join(w[0] for w in _nombre_corto(n).split()[:2]).upper() for n in p["periodista"]]
    fig.add_trace(go.Scatter(x=x, y=y, mode="markers+text", text=iniciales, textposition="middle center",
                             textfont=dict(color="#FFFFFF", size=10, family="Rubik, Arial"),
                             marker=dict(size=28, color="#231815", line=dict(color="#FFFFFF", width=2)),
                             customdata=np.stack([p["slug"], y_real, p["periodista"], notas], axis=-1),
                             hovertemplate="%{customdata[2]}<br>Notas: %{customdata[3]}<br>Eficiencia: %{customdata[1]:.0f}<extra></extra>"))
    px = (x - xr[0]) / (xr[1] - xr[0]) * ancho_area
    py = (yr[1] - y) / (yr[1] - yr[0]) * alto_area
    nombres = [_nombre_corto(n) for n in p["periodista"]]
    for k, dx, dy in _ubicar_etiquetas(px, py, nombres, ancho_area, alto_area):
        lejos = abs(dx) > 40 or abs(dy) > 30
        fig.add_annotation(x=x[k], y=y[k], text=nombres[k], ax=dx, ay=dy, showarrow=True, arrowhead=0,
                           arrowwidth=1 if lejos else 0.1, arrowcolor="#94A3B8" if lejos else "rgba(0,0,0,0)", standoff=15,
                           font=dict(size=11, color="#231815"), bgcolor="rgba(255,255,255,0.85)", borderpad=1)
    fig.update_layout(height=alto, margin=m, showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(title="Notas publicadas en el periodo (escala log)", range=xr, tickvals=[np.log10(v) for v in xticks],
                                 ticktext=[str(v) for v in xticks], gridcolor="#E4E4E4", zeroline=False),
                      yaxis=dict(title="Eficiencia (índice, escala log)", range=yr, tickvals=tickvals, ticktext=ticktext,
                                 gridcolor="#E4E4E4", zeroline=False))
    ev = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key="cuadrante",
                         config={"displayModeBar": False})
    pts = ev.get("selection", {}).get("points", []) if ev else []
    if pts and "customdata" in pts[0]:
        return pts[0]["customdata"][0]
    return None


def _selector(t):
    o = t.sort_values("lectores", ascending=False)
    c1, c2, c3 = st.columns([2, 2, 1])
    c1.subheader("Detalle por periodista")
    nombre = c2.selectbox("Ver perfil", o["periodista"], label_visibility="collapsed")
    if c3.button("Ver perfil →", width="stretch"):
        return o.loc[o["periodista"] == nombre, "slug"].iloc[0]
    return None


def _tabla(t, periodo):
    st.subheader("Desempeño por periodista" + ("" if periodo == d.ANO else " este mes"))
    st.caption("Haz clic en una fila para abrir el perfil. **Semáforo SEO** = % promedio de cumplimiento del checklist "
               "de cada nota (title, meta descripción, subtítulos, enlaces internos, extensión, imágenes): "
               "🟢 80 % o más · 🟡 60 a 79 % · 🔴 menos de 60 %.")
    v = t.copy().reset_index(drop=True)
    v["foto"] = [avatar_data_uri(n, "#231815", 64) for n in v["periodista"]]
    v["firma"] = v["tipo"].map({"persona": "Persona", "redaccion": "Sin firma personal", "agencia": "Agencias", "otros": "Otros créditos"})
    v["seccion_beat"] = v["seccion"] + " · " + v["beat"]
    v["pct_txt"] = v["pct_trafico_total"].map(lambda x: f"{decimal(x)} %")
    v["pauta_txt"] = (v["lect_pauta"] / v["lectores"].replace(0, np.nan) * 100).map(lambda x: "—" if pd.isna(x) else f"{x:.0f} %")
    v["semaforo"] = v["pct_seo"].apply(lambda x: "⚪ s/e" if pd.isna(x) else f"{'🟢' if x >= 80 else '🟡' if x >= 60 else '🔴'} {x:.0f} %")
    v["estado_txt"] = [estado_label(r.eficiencia, r.en_alerta)[0] if r.tipo == "persona" else "—" for r in v.itertuples()]
    cols = ["foto", "periodista", "firma", "seccion_beat", "notas", "lectores", "pct_txt", "pauta_txt", "clics",
            "clics_por_nota", "eficiencia", "posicion", "puntaje", "semaforo", "estado_txt"]
    styled = v[cols].style.map(lambda x: ESTADO_STYLE.get(x, ""), subset=["estado_txt"])
    ev = st.dataframe(styled, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row", key="tabla_p",
                      column_config={
                          "foto": st.column_config.ImageColumn("", width="small"),
                          "periodista": st.column_config.TextColumn("Periodista", width="medium"),
                          "firma": st.column_config.TextColumn("Firma", width="small"),
                          "seccion_beat": st.column_config.TextColumn("Sección · tema principal", width="medium"),
                          "notas": st.column_config.NumberColumn("Notas", width="small"),
                          "lectores": st.column_config.NumberColumn("Lectores", format="localized", width="small"),
                          "pct_txt": st.column_config.TextColumn("% del total", width="small"),
                          "pauta_txt": st.column_config.TextColumn("% por pauta", width="small",
                                                                   help="Parte de los lectores que llegó por la pauta en redes"),
                          "clics": st.column_config.NumberColumn("Clics Google", format="localized", width="small"),
                          "clics_por_nota": st.column_config.NumberColumn("Clics por nota", format="%.1f", width="small"),
                          "eficiencia": st.column_config.NumberColumn("Eficiencia", format="%.0f", width="small",
                                                                     help="100 = clics de Google por nota de la persona del medio"),
                          "posicion": st.column_config.NumberColumn("Posición Google", format="%.1f", width="small"),
                          "puntaje": st.column_config.NumberColumn("Puntaje (0-10)", format="%.1f", width="small"),
                          "semaforo": st.column_config.TextColumn("Semáforo SEO", width="small"),
                          "estado_txt": st.column_config.TextColumn("Estado", width="medium")})
    filas = ev.get("selection", {}).get("rows", []) if ev else []
    if filas:
        return v.iloc[filas[0]]["slug"]
    return None


def _explicacion(t):
    p = t[(t["tipo"] == "persona") & t["eficiencia"].notna()]
    if p.empty:
        return
    med = t["mediana_equipo"].iloc[0]
    ref = p.iloc[(p["clics_por_nota"] - med).abs().argsort()[:1]].iloc[0]
    top = p.sort_values("eficiencia", ascending=False).iloc[0]
    with st.expander("ℹ️ ¿Qué significa \"eficiencia\"? (no es el número de notas)", expanded=False):
        st.markdown(
            "Es un **índice comparativo**: los clics de Google (Búsqueda y Discover) que hace cada nota, contra la "
            "**mediana de las personas que firmaron en el periodo**.\n\n"
            "- **100** = clics por nota iguales a la mediana\n- **200** = el doble\n- **50** = la mitad\n\n"
            f"**Con los datos de este periodo:** la mediana es **{decimal(med)} clics por nota**. {ref['periodista']} "
            f"hizo {decimal(ref['clics_por_nota'])}, por eso su índice es {decimal(ref['eficiencia'], 0)}. "
            f"{top['periodista']} hizo {decimal(top['clics_por_nota'])} por nota: índice {decimal(top['eficiencia'], 0)}.\n\n"
            "Se mide en Google y no en lectores porque la mayoría de los lectores llega por la pauta en redes, y qué nota se "
            "pauta lo decide el área comercial, no quien escribe. Revista AXXIS sin firma personal y las agencias se muestran "
            "con el mismo índice como referencia, pero no entran en la mediana ni en el ranking.")


def _secciones(periodo):
    st.subheader("Dificultad y canal por sección")
    df = d.notas_periodo(d.ANO)
    df = df[df["mes_pub"] < "2026-10"]
    st.caption("Qué tan fácil es que una nota de cada sección gane lectores en Google (mediana de clics por nota publicada "
               "de enero a septiembre de 2026: 🟢 Fácil 10 o más · 🔵 Media 3 a 9 · 🔴 Difícil menos de 3) y por dónde "
               "llegan sus lectores.")
    for sec, g in df.groupby("seccion"):
        if len(g) < 5:
            continue
        med = g["clics"].median()
        dif = "Fácil" if med >= 10 else "Media" if med >= 3 else "Difícil"
        canal = {n: g[f"lect_{k}"].sum() for k, n in d.CANALES}
        top = max(canal, key=canal.get)
        pct = canal[top] / max(1, sum(canal.values())) * 100
        k_dif = {"Fácil": "green", "Media": "blue", "Difícil": "red"}[dif]
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;gap:14px;background:{BG_ESTADO[k_dif]};'
            f'border-radius:12px;padding:12px 16px;margin-bottom:8px"><div style="min-width:0">'
            f'<div style="font-weight:700;font-size:1.05rem;color:#1C1A1A">{sec} · {len(g)} notas</div>'
            f'<div style="font-size:0.95rem;color:#475569;margin-top:2px">Sus lectores llegan sobre todo por {ARTICULO_CANAL.get(top, top)} '
            f'({pct:.0f} %)</div></div><div style="text-align:right;flex-shrink:0">'
            f'<div style="font-weight:700;color:{TXT_ESTADO[k_dif]};font-size:0.95rem;letter-spacing:0.02em">{dif.upper()}</div>'
            f'<div style="font-size:0.9rem;color:#64748B;margin-top:2px">{decimal(med)} clics de Google la nota típica</div>'
            f'</div></div>', unsafe_allow_html=True)


def _titulares():
    st.subheader("🧮 Qué tipo de titular funciona en Google")
    df = d.notas_periodo(d.ANO)
    df = tit.marcar(df[df["mes_pub"] < "2026-10"])
    filas = tit.medir(df)
    st.caption(f"Medido sobre los titulares (H1) de las {len(df)} notas publicadas de enero a septiembre de 2026 y sus "
               "clics de Google en el año. Se compara la nota típica (mediana) con el rasgo contra la nota típica sin él. "
               "Es una relación medida, no una causa: sirve para decidir qué probar.")
    rows = []
    for r in filas:
        flecha = "▲" if r["dif"] > 0 else "▼" if r["dif"] < 0 else "="
        rows.append([r["etiqueta"], f"{decimal(r['med_con'])} clics (n={r['n_con']})", f"{decimal(r['med_sin'])} clics (n={r['n_sin']})",
                     f"{flecha} {decimal(r['dif'])}"])
    ui.seccion(ui.tabla(["Rasgo del titular", "Con el rasgo", "Sin el rasgo", "Diferencia"], rows, {1, 2, 3}), "card_titulares")
    lar = tit.por_largo(df)
    st.markdown("**Por largo del titular:** " + " · ".join(f"{x['tramo']}: {decimal(x['mediana'])} clics ({x['n']} notas)" for x in lar))
    mejor = filas[0] if filas else None
    if mejor:
        ui.idea(f"La diferencia más grande: <mark>{mejor['etiqueta']}</mark> — {decimal(mejor['med_con'])} clics la nota "
                f"típica con el rasgo, contra {decimal(mejor['med_sin'])} sin él.")


def render(periodo):
    t = d.tabla_periodistas(periodo)
    _banner(periodo)
    if t.empty:
        st.warning("No hay notas publicadas en este periodo.")
        return None
    _kpis(t)
    st.write("")
    _tendencia()
    _que_cambia(periodo)
    st.write("")
    elegido = None
    c1, c2 = st.columns(2)
    with c1:
        _barras(t, "lectores", "Aporte de lectores por periodista",
                "Lectores de las notas publicadas en el periodo, por firma. En gris, las firmas que no son personas.",
                lambda v, r: f"{formatear_numero(v)} · {decimal(r.pct_trafico_total)} %")
    with c2:
        _barras(t, "notas", "Notas publicadas por periodista", "Cuántas notas publicó cada firma: dato bruto, sin ajustar.",
                lambda v, r: f"{int(v)}")
    elegido = _cuadrante(t) or elegido
    elegido = _selector(t) or elegido
    elegido = _tabla(t, periodo) or elegido
    _explicacion(t)
    st.write("")
    _secciones(periodo)
    st.write("")
    _titulares()
    return elegido
