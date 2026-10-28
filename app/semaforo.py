"""Semáforo SEO por nota y por periodista (los ítems se evalúan en data/semaforo_seo.py)."""

import html

import pandas as pd

import ui
from calculos import decimal

ITEMS = {
    "title_70": ("Title de hasta 70 caracteres",
                 "Que el título que se ve en Google no pase de 70 caracteres: si el titular es más largo, el title lo resume "
                 "con el nombre del proyecto y el lugar."),
    "meta_120_160": ("Meta descripción de 120 a 160 caracteres",
                     "Escribe la meta descripción con 120 a 160 caracteres: más corta, Google la reemplaza; más larga, la corta."),
    "meta_no_repite": ("Meta descripción distinta del titular",
                       "La meta descripción suma información nueva (lugar, firma, qué tiene de especial); no repite el titular."),
    "h2_2": ("Al menos 2 subtítulos H2 (notas de 400 palabras o más)",
             "Divide la nota en partes con al menos 2 subtítulos H2 que digan de qué trata cada parte."),
    "enlaces_3": ("3 o más enlaces internos",
                  "Enlaza de 3 a 5 notas de AXXIS del mismo tema, la misma firma o el mismo lugar."),
    "enlace_temprano": ("Un enlace interno en los 3 primeros párrafos",
                        "Pon el primer enlace interno en los primeros 3 párrafos, no al final."),
    "ancla_descriptiva": ("Texto del enlace descriptivo (2 a 8 palabras)",
                          "El texto del enlace dice adónde lleva (\"la casa de Simón Vélez en Anapoima\"), no una palabra suelta."),
    "extension_400": ("400 palabras o más", "La nota se queda corta: cuenta el proyecto con al menos 400 palabras."),
    "imagenes_alt": ("Todas las imágenes con texto alternativo",
                     "Escribe en el texto alternativo de cada imagen qué se ve: espacio, material, lugar."),
}


def color(pct):
    if pd.isna(pct):
        return "⚪"
    return "🟢" if pct >= 80 else "🟡" if pct >= 60 else "🔴"


def cumplimiento_items(df: pd.DataFrame) -> list[dict]:
    out = []
    for k, (lbl, accion) in ITEMS.items():
        col = f"seo_{k}"
        if col not in df:
            continue
        v = df[col].dropna()
        if len(v) == 0:
            continue
        out.append({"item": k, "etiqueta": lbl, "accion": accion, "cumplen": int(v.astype(bool).sum()), "aplica": len(v),
                    "pct": v.astype(bool).mean() * 100})
    return out


def bloque_periodista(df: pd.DataFrame, nombre_periodo: str) -> str:
    ev = df[df["pct_seo"].notna()]
    pct = ev["pct_seo"].mean()
    items = cumplimiento_items(ev)
    filas = [[f'{color(i["pct"])} {html.escape(i["etiqueta"])}', f'{i["cumplen"]} de {i["aplica"]}', f'{decimal(i["pct"], 0)} %']
             for i in sorted(items, key=lambda x: x["pct"])]
    fallas = [i for i in sorted(items, key=lambda x: x["pct"]) if i["pct"] < 80]
    que_hacer = "".join(f"<li>{html.escape(i['accion'])} <span class='mini-ax'>(hoy lo cumplen {i['cumplen']} de {i['aplica']} notas)</span></li>"
                        for i in fallas[:4])
    return (f'<h3 class="card-h">¿En qué está fallando el SEO? — desglose por ítem</h3>'
            f'<p>{color(pct)} <b>{decimal(pct, 0)} %</b> de cumplimiento promedio en {len(ev)} notas de {nombre_periodo}, leídas '
            "en vivo en el sitio. 🟢 80 % o más · 🟡 60 a 79 % · 🔴 menos de 60 %. Es higiene de cada nota: ayuda a que Google "
            "la entienda, pero por sí sola no garantiza clics.</p>"
            + ui.tabla(["Ítem", "Notas que cumplen", "%"], filas, {1, 2})
            + (f"<p style='margin-top:10px'><b>Qué hacer en las próximas notas:</b></p><ul>{que_hacer}</ul>" if que_hacer else ""))
