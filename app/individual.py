"""Perfil del periodista: qué publicó en el periodo, qué le funcionó, qué no, sobre qué escribir y cómo titular."""

import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import datos as d
import semaforo
import titulares as tit
import ui
from avatares import avatar_data_uri
from calculos import decimal, estado_label, formatear_delta_pct, formatear_numero, miles, puntaje_rendimiento
from estilos import BG_ESTADO, TXT_ESTADO, delta_html, pill
from google_updates import UPDATES_2026

ICONO_ESTADO = {"green": "📈", "blue": "➡️", "red": "🔻"}
DESC_ESTADO = {"SOBRE MEDIANA": "Clics de Google por nota por encima de la mediana del equipo en el periodo.",
               "EN RANGO": "Clics de Google por nota cerca de la mediana del equipo.",
               "EN ALERTA": "Semáforo SEO en rojo o eficiencia por debajo de la mitad de la mediana."}


def _anterior(periodo):
    if periodo == d.ANO or periodo == d.MESES[0]:
        return None
    return d.MESES[d.MESES.index(periodo) - 1]


def _nombre_periodo(periodo):
    return "2026" if periodo == d.ANO else d.MES_LARGO[periodo]


def _header(meta, rk):
    with st.container(border=True, key="card_header"):
        c1, c2 = st.columns([1, 2.4], vertical_alignment="center")
        c1.markdown(f'<img src="{avatar_data_uri(meta["nombre"], "#231815", 160)}" style="width:96px;height:96px;border-radius:50%">',
                    unsafe_allow_html=True)
        tipo = {"persona": "", "redaccion": " · notas sin firma personal", "agencia": " · contenido de agencias",
                "otros": " · créditos externos"}[meta["tipo"]]
        c2.markdown(f'<div style="font-size:1.5rem;font-weight:700;color:#231815">{html.escape(meta["nombre"])}</div>'
                    f'<div style="color:#5F6467;margin:4px 0 8px 0">{meta["seccion"]} · Tema principal: {meta["beat"]}{tipo}</div>'
                    '', unsafe_allow_html=True)


def _trafico(fila, fila_ant):
    with st.container(border=True, key="card_trafico"):
        dlt = delta_html(fila["lectores"], fila_ant["lectores"] if fila_ant is not None else None)
        st.markdown(f'<div class="cp-kpi-label">📊 Lectores del periodo</div>'
                    f'<div class="cp-kpi-value">{formatear_numero(fila["lectores"])}</div>'
                    f'<div class="cp-kpi-delta">{dlt}</div>'
                    f'<div class="cp-metric-label" style="margin-top:8px">{int(fila["notas"])} notas · '
                    f'{decimal(fila["pct_trafico_total"])} % de los lectores de lo publicado en el periodo</div>',
                    unsafe_allow_html=True)


def _estado(fila):
    lbl, k = estado_label(fila["eficiencia"], fila["en_alerta"]) if fila["tipo"] == "persona" else ("REFERENCIA", "gray")
    desc = DESC_ESTADO.get(lbl, "Firma institucional: se muestra como referencia y no entra en la mediana del equipo.")
    with st.container(border=True, key="card_estado"):
        st.markdown(f'<div class="cp-kpi-label">{ICONO_ESTADO.get(k, "•")} ESTADO ACTUAL</div>'
                    f'<div style="font-weight:700;color:{TXT_ESTADO[k]};font-size:1.1rem;margin:4px 0">{lbl}</div>'
                    f'<div class="cp-metric-label">{desc} Eficiencia: {decimal(fila["eficiencia"], 0)}.</div>',
                    unsafe_allow_html=True)


def _lead(fila, fila_ant, periodo):
    tot = fila["lectores"] or 1
    gan = (fila["lect_google"] + fila["lect_directo"]) / tot * 100
    pau = fila["lect_pauta"] / tot * 100
    news = fila["lect_newsletter"] / tot * 100
    if fila_ant is not None:
        frase = (f"Con {int(fila['notas'])} notas publicadas en {_nombre_periodo(periodo)} frente a {int(fila_ant['notas'])} "
                 f"en {_nombre_periodo(_anterior(periodo))}: {miles(fila['lectores'])} lectores contra {miles(fila_ant['lectores'])} "
                 f"y {miles(fila['clics'])} clics de Google contra {miles(fila_ant['clics'])}.")
    else:
        frase = (f"Con {int(fila['notas'])} notas publicadas en {_nombre_periodo(periodo)}: {miles(fila['lectores'])} lectores "
                 f"y {miles(fila['clics'])} clics de Google.")
    reparto = (f" De lo que leyeron, el {decimal(gan, 0)} % llegó solo, por Google y entradas directas; el {decimal(pau, 0)} % "
               f"por la pauta en redes y el {decimal(news, 0)} % por el newsletter.")
    st.markdown(f'<p class="lead-ax">{frase}{reparto}</p>', unsafe_allow_html=True)


def _todas_sus_notas(firma, periodo):
    n = d.notas()
    rutas = set(n[n["firma"] == firma]["ruta"])
    t = d.notas_mes()
    t = t[t["ruta"].isin(rutas)]
    return t if periodo == d.ANO else t[t["mes"] == periodo]


def _tabla_periodo(firma, fila, fila_ant, periodo):
    if periodo == d.ANO:
        return
    ant = _anterior(periodo)
    todas = _todas_sus_notas(firma, periodo)
    filas = [["Notas publicadas", miles(fila["notas"])], ["Lectores de esas notas", miles(fila["lectores"])],
             ["Clics de Google de esas notas", miles(fila["clics"])],
             ["Lectores de todas tus notas de 2026", miles(todas["lectores"].sum())],
             ["Clics de Google de todas tus notas de 2026", miles(todas["clics_web"].sum() + todas["clics_disc"].sum())]]
    cab = ["", _nombre_periodo(periodo).capitalize()]
    if ant:
        todas_a = _todas_sus_notas(firma, ant)
        va = [fila_ant["notas"] if fila_ant is not None else 0, fila_ant["lectores"] if fila_ant is not None else 0,
              fila_ant["clics"] if fila_ant is not None else 0, todas_a["lectores"].sum(),
              todas_a["clics_web"].sum() + todas_a["clics_disc"].sum()]
        actuales = [fila["notas"], fila["lectores"], fila["clics"], todas["lectores"].sum(),
                    todas["clics_web"].sum() + todas["clics_disc"].sum()]
        for f, a, b in zip(filas, va, actuales):
            f.insert(1, miles(a))
            f.append(formatear_delta_pct(b, a) or "—")
        cab = ["", d.MES_LARGO[ant].capitalize(), d.MES_LARGO[periodo].capitalize(), "Cambio"]
    nota = ("" if periodo != "2026-10" else
            f'<p class="cap">Octubre va hasta el {d.corte()["ga4"].day} (Search Console hasta el {d.corte()["gsc"].day}): '
            "el mes todavía no está completo.</p>")
    ui.seccion('<h3 class="card-h">El periodo en una tabla</h3><p>"Todas tus notas de 2026" incluye las que publicaste '
               "antes y siguen recibiendo lectores: es la diferencia entre lo que publicaste y lo que te leyeron.</p>"
               + ui.tabla(cab, filas, set(range(1, len(cab)))) + nota, "card_tabla_periodo")


def _sirvio(firma, periodo):
    n = d.notas()
    suyas = n[n["firma"] == firma].set_index("ruta")
    t = _todas_sus_notas(firma, periodo).groupby("ruta").sum(numeric_only=True)
    t = t[t["lectores"] > 0].sort_values("lectores", ascending=False).head(6)
    if t.empty:
        return
    filas = []
    for ruta, r in t.iterrows():
        s = suyas.loc[ruta]
        filas.append([f'{ui.enlace_nota(s["titular"], s["link"])}<div class="mini-ax">{s["seccion"]} · {s["fecha"]} · '
                      f'{s["tema_label"]}</div>{ui.barra_canales(r)}', miles(r["lectores"]),
                      miles(r["clics_web"] + r["clics_disc"]), ui.desglose_canales(r)])
    top = t.index[0]
    ui.seccion(f'<h3 class="card-h">Qué te sirvió</h3><p><b>{html.escape(suyas.loc[top, "titular"])}</b> es lo que más te '
               f'leyeron en {_nombre_periodo(periodo)}: {miles(t.iloc[0]["lectores"])} lectores. Tus notas más leídas del periodo, '
               "sin importar cuándo las publicaste, y de dónde llegó cada lector.</p>" + ui.leyenda_canales()
               + ui.tabla(["Nota", "Lectores", "Clics Google", "De dónde llegaron"], filas, {1, 2}), "card_sirvio")


def _no_sirvio(firma, periodo):
    df = d.notas_periodo(periodo)
    df = df[(df["firma"] == firma)]
    # Una nota necesita tiempo para encontrar lectores en Google: en el mes en curso, al menos una semana de vida;
    # en todo el año, al menos un mes.
    if periodo == "2026-10":
        df = df[df["fecha"] <= "2026-10-20"]
    elif periodo == d.ANO:
        df = df[df["fecha"] <= "2026-09-27"]
    if len(df) < 2:
        return
    df = df.sort_values(["clics", "ganado"]).head(4)
    filas = [[f'{ui.enlace_nota(r["titular"], r["link"])}<div class="mini-ax">{r["seccion"]} · {r["fecha"]} · {r["tema_label"]}</div>',
              miles(r["clics"]), miles(r["lectores"]), f'{r["lect_pauta"] / r["lectores"] * 100:.0f} %' if r["lectores"] else "—"]
             for _, r in df.iterrows()]
    ui.seccion('<h3 class="card-h">Qué no te sirvió</h3><p>Lo que publicaste en el periodo y casi no encontró lectores en '
               "Google. Si los lectores llegaron, fue sobre todo por la pauta.</p>"
               + ui.tabla(["Nota", "Clics Google", "Lectores", "% por pauta"], filas, {1, 2, 3}), "card_no_sirvio")


def _recomendamos(firma):
    df = d.notas_periodo(d.ANO)
    df = df[df["mes_pub"] < "2026-10"]
    suyas = df[df["firma"] == firma]
    if len(suyas) < 3:
        return
    sitio = df.groupby("tema")["clics"].median()
    filas = []
    for tema, g in suyas.groupby("tema"):
        filas.append([d.TEMAS[tema], len(g), decimal(g["clics"].median()), decimal(sitio.get(tema, np.nan)),
                      g["clics"].median()])
    filas.sort(key=lambda x: -x[4])
    mejor, peor = filas[0], filas[-1]
    frase = (f"Tus notas de <b>{html.escape(mejor[0][0].lower() + mejor[0][1:])}</b> hacen {mejor[2]} clics de Google la nota típica; las de "
             f"<b>{html.escape(peor[0][0].lower() + peor[0][1:])}</b>, {peor[2]}.") if len(filas) > 1 else ""
    ui.seccion(f'<h3 class="card-h">Qué te recomendamos</h3><p>Por cada nota que escribes, lo que se gana en Google cambia '
               f"mucho según el tema. {frase} Notas publicadas de enero a septiembre, con sus clics del año; a la derecha, "
               "la nota típica del mismo tema en todo el sitio.</p>"
               + ui.tabla(["Tema", "Tus notas", "Tu nota típica (clics)", "Nota típica del sitio"], [f[:4] for f in filas], {1, 2, 3}),
               "card_recomendamos")


def _sobre_que_escribir(firma):
    n = d.notas()
    suyas = n[n["firma"] == firma].set_index("ruta")
    rec = d.consultas()["rec"]
    ventana = d.consultas()["rec_ventana"]
    agg = {}
    for ruta in suyas.index:
        for q, c, i, p in rec.get(ruta, []):
            a = agg.setdefault(q, {"imp": 0, "clics": 0, "pos": [], "notas": set()})
            a["imp"] += i
            a["clics"] += c
            a["pos"].append(p)
            a["notas"].add(ruta)
    if not agg:
        return
    top = sorted(agg.items(), key=lambda kv: -kv[1]["imp"])[:8]
    filas = []
    for q, a in top:
        nota = suyas.loc[sorted(a["notas"])[0]]
        filas.append([f"<b>{html.escape(q)}</b>", miles(a["imp"]), miles(a["clics"]), decimal(np.mean(a["pos"])),
                      ui.enlace_nota(nota["titular"], nota["link"])])
    ui.seccion(f'<h3 class="card-h">Sobre qué escribir las próximas semanas</h3><p>No es una lista de ideas: son las '
               f"búsquedas que HOY traen gente a tus notas en Google ({ventana[0][8:]}-{ventana[0][5:7]} al {ventana[1][8:]}-"
               f"{ventana[1][5:7]}). Si la posición es mayor que 10, la nota sale en la segunda página: una nota nueva sobre "
               "esa búsqueda, enlazada a la anterior, tiene espacio.</p>"
               + ui.tabla(["Búsqueda", "Impresiones", "Clics", "Posición", "Tu nota que aparece"], filas, {1, 2, 3}),
               "card_que_escribir")


def _no_dejar(firma):
    df = d.notas_periodo(d.ANO)
    suyas = df[(df["firma"] == firma) & (df["mes_pub"] < "2026-10")]
    if len(suyas) < 4:
        return
    med_mes = df.groupby("mes_pub")["clics"].median()
    filas = []
    for tema, g in suyas.groupby("tema"):
        meses = sorted({m for m, gg in g.groupby("mes_pub") if gg["clics"].median() >= med_mes.get(m, np.inf)})
        if len(meses) >= 2:
            filas.append([d.TEMAS[tema], f"{len(meses)} de {g['mes_pub'].nunique()} meses en que lo publicaste",
                          len(g), decimal(g["clics"].median())])
    if not filas:
        return
    filas.sort(key=lambda f: -float(f[3].replace(".", "").replace(",", ".")))
    ui.seccion('<h3 class="card-h">Lo que no deberías dejar de escribir</h3><p>Los temas que te funcionaron mes tras mes: '
               "en esos meses, tus notas del tema hicieron al menos la mediana de clics de Google de todo lo que publicó el "
               "sitio ese mes. Se miden en meses, no en días, para que no se cuele un pico de una sola nota.</p>"
               + ui.tabla(["Tema", "Meses en que te rindió", "Notas", "Nota típica (clics)"], filas, {2, 3}), "card_no_dejar")


def _como_titular(firma):
    df = tit.marcar(d.notas_periodo(d.ANO))
    df = df[df["mes_pub"] < "2026-10"]
    suyas = df[df["firma"] == firma]
    propias = tit.medir(suyas)
    if propias:
        filas = [[("✅ " if r["dif"] > 0 else "➖ ") + html.escape(r["etiqueta"]),
                  f"{decimal(r['med_con'])} clics la nota típica con el rasgo, contra {decimal(r['med_sin'])} sin él "
                  f"({r['n_con']} y {r['n_sin']} notas)"] for r in propias]
        cuerpo = ("<p>Medido sobre TUS titulares y TUS clics de Google. Solo aparece un rasgo cuando hay al menos 8 notas tuyas "
                  "con él y 8 sin él: con menos, un titular con suerte parece un método.</p>"
                  + ui.tabla(["Rasgo", "Lo que se midió"], filas))
    else:
        sitio = tit.medir(df)
        filas = [[("✅ " if r["dif"] > 0 else "➖ ") + html.escape(r["etiqueta"]),
                  f"{decimal(r['med_con'])} contra {decimal(r['med_sin'])} clics la nota típica",
                  f"{int(suyas[r['rasgo']].sum())} de {len(suyas)}"] for r in sitio]
        cuerpo = (f"<p>Con {len(suyas)} notas tuyas no alcanza para una regla propia (pedimos 8 con el rasgo y 8 sin él). "
                  "Esto es lo que mide todo el sitio, y cuántos de tus titulares ya lo tienen:</p>"
                  + ui.tabla(["Rasgo del titular", "En todo el sitio", "Tus titulares con el rasgo"], filas, {2}))
    ui.seccion('<h3 class="card-h">Cómo titular</h3>' + cuerpo, "card_titular")


def _trafico_por_mes(firma, meta_todos):
    with st.container(border=True, key="card_trafico_mes"):
        st.subheader("Lectores y clics de Google por mes")
        st.caption("Notas publicadas cada mes, con los lectores y clics de Google que hicieron ese mes. Las marcas de color son "
                   "actualizaciones de Google: si una caída coincide con una, la causa puede ser el algoritmo, no la persona.")
        otros = [m["nombre"] for m in meta_todos if m["nombre"] != firma]
        comparar = st.selectbox("Comparar con", ["(nadie)"] + otros, key=f"cmp_{firma}")
        h = d.historial(firma)
        fig = go.Figure()
        x = h["mes"].map(d.MES_CORTO)
        fig.add_trace(go.Bar(x=x, y=h["lectores"], name="Lectores", marker_color="#B9B6B3",
                             text=[formatear_numero(v) if v else "" for v in h["lectores"]], textposition="outside",
                             hovertemplate="%{x}: %{y:,.0f} lectores<extra></extra>"))
        fig.add_trace(go.Scatter(x=x, y=h["clics"], name="Clics de Google", yaxis="y2", mode="lines+markers",
                                 line=dict(color="#1E6B3A", width=3), hovertemplate="%{x}: %{y:,.0f} clics<extra></extra>"))
        if comparar != "(nadie)":
            h2 = d.historial(comparar)
            fig.add_trace(go.Scatter(x=h2["mes"].map(d.MES_CORTO), y=h2["clics"], name=f"Clics de Google · {comparar}",
                                     yaxis="y2", mode="lines+markers", line=dict(color="#0E2F4E", width=2, dash="dot")))
        for u in UPDATES_2026:
            m = f"2026-{u['inicio'].month:02d}"
            if m in d.MES_CORTO:
                fig.add_vline(x=d.MESES.index(m), line=dict(color={"Core": "#B07A1E", "Spam": "#DC2626", "Discover": "#64748B"}[u["tipo"]],
                                                            width=1, dash="dot"))
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10), legend=dict(orientation="h", y=-0.18),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          yaxis=dict(title="Lectores", gridcolor="#E4E4E4"),
                          yaxis2=dict(title="Clics de Google", overlaying="y", side="right", showgrid=False))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        upd = ", ".join(f"{u['nombre']} ({u['inicio'].day}-{u['inicio'].month})" for u in UPDATES_2026)
        st.caption(f"Actualizaciones de Google de 2026 marcadas: {upd}. Octubre va hasta el {d.corte()['ga4'].day}.")


def _diagnostico_seo(firma, periodo):
    df = d.notas_periodo(periodo)
    df = df[df["firma"] == firma]
    if "pct_seo" not in df or df["pct_seo"].notna().sum() == 0:
        ui.seccion('<h3 class="card-h">¿En qué está fallando el SEO? — desglose por ítem</h3><p>La lectura en vivo de las '
                   "notas todavía no termina: el semáforo aparece cuando se complete.</p>", "card_seo")
        return
    ui.seccion(semaforo.bloque_periodista(df, _nombre_periodo(periodo)), "card_seo")


def _puntaje(fila):
    if fila["tipo"] != "persona":
        return
    p = puntaje_rendimiento(fila)
    if p["total"] is None:
        return
    s = p["subs"]
    filas = [["Eficiencia (clics de Google por nota contra la mediana)", decimal(fila["eficiencia"], 0), decimal(s["eficiencia"]), "4"],
             ["CTR contra lo esperado por su posición", decimal(fila["ctr_indice"], 2), decimal(s["ctr"]), "2"],
             ["Posición promedio en Google", decimal(fila["posicion"]), decimal(s["posicion"]), "2"],
             ["Cumplimiento del checklist SEO", f"{decimal(fila['pct_seo'], 0)} %" if not pd.isna(fila["pct_seo"]) else "—",
              decimal(s["seo"]), "2"]]
    color = "green" if p["total"] >= 7 else "orange" if p["total"] >= 5 else "red"
    muestra = (f'<p class="cap">Muestra chica: {int(fila["notas"])} nota(s) en el periodo. Léelo como una señal, no como una '
               "calificación.</p>") if fila["notas"] < 3 else ""
    ui.seccion(f'<h3 class="card-h">🎯 Puntaje de rendimiento del periodo: '
               f'<span style="background:{BG_ESTADO[color]};color:{TXT_ESTADO[color]};padding:2px 10px;border-radius:8px">'
               f'{decimal(p["total"])}</span> / 10</h3><p>Combina cuatro señales medidas, cada una llevada a una escala de 0 a 10. '
               "Si falta una (por ejemplo, notas sin impresiones), su peso se reparte entre las demás.</p>"
               + ui.tabla(["Señal", "Valor", "Puntaje (0-10)", "Peso"], filas, {1, 2, 3}) + muestra, "card_puntaje")


def _notas_del_periodo(firma, periodo):
    df = d.notas_periodo(periodo)
    df = df[df["firma"] == firma].sort_values("fecha", ascending=False)
    if df.empty:
        return
    with st.expander(f"Ver las {len(df)} notas publicadas en el periodo"):
        v = df[["fecha", "titular", "seccion", "tema_label", "lectores", "lect_pauta", "clics", "posicion"]].copy()
        v.columns = ["Fecha", "Titular", "Sección", "Tema", "Lectores", "Por pauta", "Clics Google", "Posición"]
        st.dataframe(v, hide_index=True, width="stretch",
                     column_config={"Lectores": st.column_config.NumberColumn(format="localized"),
                                    "Por pauta": st.column_config.NumberColumn(format="localized"),
                                    "Clics Google": st.column_config.NumberColumn(format="localized"),
                                    "Posición": st.column_config.NumberColumn(format="%.1f")})


def render(slug, periodo):
    meta_todos = d.periodistas_meta()
    meta = next(m for m in meta_todos if m["slug"] == slug)
    t = d.tabla_periodistas(periodo)
    fila = t[t["slug"] == slug]
    if fila.empty:
        st.info(f"{meta['nombre']} no publicó notas en el periodo \"{d.label_periodo(periodo)}\". Elige otro periodo arriba o "
                "\"Todo 2026\".")
        _trafico_por_mes(meta["nombre"], meta_todos)
        return
    fila = fila.iloc[0]
    ant = _anterior(periodo)
    fila_ant = None
    if ant:
        ta = d.tabla_periodistas(ant)
        fa = ta[ta["slug"] == slug]
        fila_ant = fa.iloc[0] if not fa.empty else None
    rk = None

    c1, c2, c3 = st.columns([1.8, 1, 1.1], vertical_alignment="top")
    with c1:
        _header(meta, rk)
    with c2:
        _trafico(fila, fila_ant)
    with c3:
        _estado(fila)
    st.write("")
    _lead(fila, fila_ant, periodo)
    st.write("")
    _tabla_periodo(meta["nombre"], fila, fila_ant, periodo)
    st.write("")
    _sirvio(meta["nombre"], periodo)
    st.write("")
    _no_sirvio(meta["nombre"], periodo)
    st.write("")
    _recomendamos(meta["nombre"])
    st.write("")
    _sobre_que_escribir(meta["nombre"])
    st.write("")
    _no_dejar(meta["nombre"])
    st.write("")
    _como_titular(meta["nombre"])
    st.write("")
    _trafico_por_mes(meta["nombre"], meta_todos)
    st.write("")
    _diagnostico_seo(meta["nombre"], periodo)
    st.write("")
    _puntaje(fila)
    st.write("")
    _notas_del_periodo(meta["nombre"], periodo)
