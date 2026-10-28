"""Rasgos del titular (H1) y su relación con los clics de Google, medidos en las notas de AXXIS.

Se compara la MEDIANA de clics de Google por nota con el rasgo contra la mediana sin el rasgo. Solo entran notas
publicadas antes del mes en curso, para que todas hayan tenido al menos un mes de vida. Una regla se enuncia solo
si hay al menos 8 notas con el rasgo y 8 sin él."""

import re
import unicodedata

import numpy as np
import pandas as pd

MIN_N = 8


def _plano(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


COLOMBIA = ["colombia", "colombiano", "colombiana", "bogota", "medellin", "cali", "barranquilla", "cartagena",
            "bucaramanga", "manizales", "pereira", "armenia", "santa marta", "villa de leyva", "anapoima", "chia",
            "cundinamarca", "antioquia", "boyaca", "caribe colombiano", "llanogrande", "rionegro", "girardot",
            "melgar", "tunja", "cucuta", "ibague", "neiva", "pasto", "popayan", "villavicencio", "monteria",
            "sincelejo", "valledupar", "riohacha", "la guajira", "san andres", "eje cafetero", "quindio", "caldas",
            "santander", "tolima", "huila", "nariño", "narino", "cauca", "choco", "meta", "casanare", "la calera",
            "sopo", "cajica", "zipaquira", "guatape", "raquira", "nocaima", "villeta", "tibasosa", "cienaga",
            "mompox", "barichara", "salento", "filandia", "envigado", "sabaneta", "itagui", "la mesa", "tabio",
            "tenjo", "subachoque", "guaduas", "honda", "santa fe de antioquia", "jardin", "chapinero", "usaquen"]
EXTERIOR = ["mexico", "españa", "espana", "japon", "chile", "brasil", "argentina", "peru", "estados unidos", "ee. uu",
            "eeuu", "nueva york", "miami", "londres", "paris", "italia", "francia", "portugal", "lisboa", "canada",
            "australia", "india", "china", "dubai", "praga", "republica checa", "berlin", "alemania", "suiza",
            "suecia", "noruega", "dinamarca", "paises bajos", "amsterdam", "belgica", "grecia", "turquia",
            "marruecos", "indonesia", "bali", "tailandia", "vietnam", "corea", "uruguay", "ecuador", "costa rica",
            "panama", "guatemala", "polonia", "austria", "viena", "milan", "roma", "barcelona", "madrid", "toronto",
            "washington", "guadalajara", "tulum", "oaxaca", "california", "texas", "florida", "chicago",
            "los angeles", "finlandia", "islandia", "irlanda", "escocia", "inglaterra", "reino unido", "sudafrica",
            "kenia", "egipto", "singapur", "hong kong", "taiwan", "filipinas", "nueva zelanda", "venecia",
            "florencia", "estambul", "cdmx", "ciudad de mexico", "monterrey", "quito", "lima", "santiago de chile",
            "buenos aires", "sao paulo", "rio de janeiro", "montevideo", "canada", "vancouver", "montreal"]
_COMUNES = {"Revista", "AXXIS", "Axxis", "Así", "Asi", "Esta", "Este", "Estos", "Estas", "Una", "Un", "La", "El", "Los",
            "Las", "Qué", "Cómo", "Por", "Para", "Con", "En", "De", "Del", "Al"}


def _tiene(t: str, lista) -> bool:
    p = " " + re.sub(r"[^a-z0-9ñ ]", " ", _plano(t)) + " "
    return any(f" {x} " in p for x in lista)


def _nombre_propio(t: str) -> bool:
    palabras = re.findall(r"[A-ZÁÉÍÓÚÑ][\wáéíóúñ\-]+", t)
    primera = t.split()[0] if t.split() else ""
    resto = [w for w in palabras if w != primera.strip("¿¡\"'“") and w not in _COMUNES]
    resto = [w for w in resto if not _tiene(w, COLOMBIA + EXTERIOR)]
    return len(resto) > 0


RASGOS = [
    ("lugar_col", "Lugar de Colombia en el titular (ciudad, región o el país)", lambda t: _tiene(t, COLOMBIA)),
    ("lugar_ext", "Lugar fuera de Colombia en el titular", lambda t: _tiene(t, EXTERIOR)),
    ("nombre", "Nombre propio de persona, firma, obra o marca", _nombre_propio),
    ("cifra", "Cifra o número", lambda t: bool(re.search(r"\d", t))),
    ("dos_puntos", "Dos puntos (\"tema: gancho\")", lambda t: ":" in t),
    ("pregunta", "Signo de pregunta", lambda t: "?" in t),
    ("asi", "Empieza con \"Así\" (así es, así se ve...)", lambda t: _plano(t).startswith("asi ")),
]


def marcar(df: pd.DataFrame, col: str = "titular") -> pd.DataFrame:
    df = df.copy()
    for k, _, f in RASGOS:
        df[k] = df[col].fillna("").apply(f)
    df["largo"] = df[col].fillna("").str.len()
    return df


def medir(df: pd.DataFrame, metrica: str = "clics") -> list[dict]:
    """Con vs. sin cada rasgo, en mediana de la métrica por nota. Ordenado por diferencia."""
    out = []
    for k, etiqueta, _ in RASGOS:
        con, sin = df[df[k]][metrica], df[~df[k]][metrica]
        if len(con) < MIN_N or len(sin) < MIN_N:
            continue
        mc, ms = float(con.median()), float(sin.median())
        out.append({"rasgo": k, "etiqueta": etiqueta, "n_con": len(con), "med_con": mc, "n_sin": len(sin), "med_sin": ms,
                    "dif": (mc - ms)})
    return sorted(out, key=lambda r: -r["dif"])


def por_largo(df: pd.DataFrame, metrica: str = "clics") -> list[dict]:
    tramos = [("Corto (menos de 60 caracteres)", df["largo"] < 60), ("Medio (60 a 90)", (df["largo"] >= 60) & (df["largo"] <= 90)),
              ("Largo (más de 90)", df["largo"] > 90)]
    return [{"tramo": n, "n": int(m.sum()), "mediana": float(df[m][metrica].median()) if m.sum() else np.nan} for n, m in tramos]
