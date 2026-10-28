"""Avatares: foto real si existe en assets/fotos_periodistas/<slug>.(jpg|jpeg|png),
si no, placeholder (iniciales sobre círculo de color)."""

import base64
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps

# Constante local (no importar la de datos_reales.py -- ese archivo puede importar
# avatares.py, así que importar en sentido contrario arriesgaría un ciclo). Mismo
# motivo que en datos_reales.py: Streamlit Cloud recarga en caliente sin reiniciar
# el proceso, así que sin ttl un avatar viejo puede quedar cacheado indefinidamente.
_CACHE_TTL_AVATARES = 300

FOTOS_DIR = Path("assets/fotos_periodistas")


def _iniciales(nombre: str) -> str:
    partes = nombre.split()
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[-1][0]).upper()


def _mascara_circular(tamano: int) -> Image.Image:
    """Máscara circular antialiaseada (canal alfa) -- se dibuja el círculo 4x más grande
    y se reduce con LANCZOS, si no el borde queda dentado incluso a tamaños chicos (~96px).
    Se aplica tanto a fotos reales como a los avatares de iniciales para que se vean
    consistentes -- sin esto, si el cuadrante usa marcadores circulares de Plotly
    (add_layout_image sobre un go.Scatter), las esquinas del recorte cuadrado quedan
    visibles fuera del círculo del marcador."""
    escala = 4
    grande = Image.new("L", (tamano * escala, tamano * escala), 0)
    ImageDraw.Draw(grande).ellipse((0, 0, tamano * escala - 1, tamano * escala - 1), fill=255)
    return grande.resize((tamano, tamano), Image.LANCZOS)


@st.cache_data(ttl=_CACHE_TTL_AVATARES)
def _slug_por_nombre_display() -> dict:
    import datos
    return {m["nombre"]: m["slug"] for m in datos.periodistas_meta()}


def _foto_real_path(nombre: str):
    slug = _slug_por_nombre_display().get(nombre)
    if not slug:
        return None
    for ext in ("jpg", "jpeg", "png"):
        p = FOTOS_DIR / f"{slug}.{ext}"
        if p.exists():
            return p
    return None


@st.cache_data(ttl=_CACHE_TTL_AVATARES)
def avatar_png_bytes(nombre: str, color: str, tamano: int = 160) -> bytes:
    img = Image.new("RGB", (tamano, tamano), color)
    draw = ImageDraw.Draw(img)
    texto = _iniciales(nombre)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(tamano * 0.4))
    except OSError:
        try:
            font = ImageFont.load_default(size=int(tamano * 0.4))  # en el navegador (sin fuentes del sistema)
        except TypeError:
            font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), texto, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((tamano - w) / 2 - bbox[0], (tamano - h) / 2 - bbox[1]), texto, fill="white", font=font)
    img.putalpha(_mascara_circular(tamano))
    buf = BytesIO()
    img.save(buf, format="PNG")  # PNG, no JPEG -- necesita canal alfa para la máscara
    return buf.getvalue()


@st.cache_data(ttl=_CACHE_TTL_AVATARES)
def avatar_data_uri(nombre: str, color: str, tamano: int = 160) -> str:
    foto = _foto_real_path(nombre)
    if foto is not None:
        img = Image.open(foto).convert("RGB")
        # centering sesgado hacia arriba (no 0.5,0.5) para que el recorte cuadrado
        # no corte la cara en fotos tipo retrato — prioriza cabeza/rostro sobre hombros.
        img = ImageOps.fit(img, (tamano, tamano), centering=(0.5, 0.22))
        img.putalpha(_mascara_circular(tamano))
        buf = BytesIO()
        img.save(buf, format="PNG")  # PNG, no JPEG -- necesita canal alfa para la máscara
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    b64 = base64.b64encode(avatar_png_bytes(nombre, color, tamano)).decode("ascii")
    return f"data:image/png;base64,{b64}"


@st.cache_data(ttl=_CACHE_TTL_AVATARES)
def logo_axxis_data_uri(color: str = "negro") -> str:
    """Logo real de Revista AXXIS (SVG del encabezado del sitio, assets/axxis_<color>.svg)."""
    with open(f"assets/axxis_{color}.svg", "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"
