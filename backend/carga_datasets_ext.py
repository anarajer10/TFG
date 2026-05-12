# Se descargan los datasets de LIAR y FakeDeS y se fusionan con el dataset creado a partir de los scrapers
import os
import re
import requests
import pandas as pd
from io import BytesIO
from langdetect import detect # type: ignore

DATASET_CSV = "dataset.csv" # Datos de la BD (scrapers)
DATASET_FUSIONADO = "dataset_completo.csv" # En español e inglés mezclados
DATASET_ES = "dataset_es.csv" # en español solo
DATASET_EN = "dataset_en.csv" # en inglés solo

# LIAR, dataset en inglés con etiquetas de noticias verdaderas y falsas
LIAR_FALSAS = {"pants-fire", "false"}
LIAR_VERDADERAS = {"mostly-true", "true"} # se van a excluir el resto de etiquetas (son + ambiguas)

# FakeDeS, dataset en español de Github
FAKEDES_URLS = {
    "train": "https://raw.githubusercontent.com/jpposadas/FakeNewsCorpusSpanish/master/train.xlsx",
    "development": "https://raw.githubusercontent.com/jpposadas/FakeNewsCorpusSpanish/master/development.xlsx",
    "test": "https://raw.githubusercontent.com/jpposadas/FakeNewsCorpusSpanish/master/test.xlsx",
}

CARPETA_LIAR = "dataset_liar"
CARPETA_FAKENEWS = "dataset_fakenews"

# Para saber si las notcias de la BD son en español o no
def _es_espanol(texto: str) -> bool:
    try:
        return detect(texto[:300]) == "es"
    except:
        return False

def cargar_liar() -> pd.DataFrame:
    # Descarga de LIAR 
    columnas = ["id", "label", "statement", "subject", "speaker", "job", "state", "party", 
                "barely_true", "false_c", "half_true", "mostly_true", "pants_fire", "context"]

    filas = []
    for archivo in ["train.tsv", "valid.tsv", "test.tsv"]:
        ruta = os.path.join(CARPETA_LIAR, archivo)
        if not os.path.exists(ruta):
            print(f"{ruta} no encontrada")
            continue
        df = pd.read_csv(ruta, sep="\t", header=None, names=columnas, on_bad_lines="skip")

        for _, fila in df.iterrows():
            etiqueta = str(fila["label"]).strip()
            texto = str(fila["statement"]).strip()

            if etiqueta in LIAR_FALSAS:
                label = 1
            elif etiqueta in LIAR_VERDADERAS:
                label = 0
            else:
                continue

            if texto:
                filas.append({"texto": texto, "label": label})

    df = pd.DataFrame(filas)
    print(f"{len(df)} muestras en LIAR"
          f"({(df['label'] == 1).sum()} falsas, {(df['label'] == 0).sum()} verdaderas)")
    return df


def cargar_fakenews() -> pd.DataFrame:
    filas = []
    archivos = {
        "Fake.csv": 1,
        "True.csv": 0,
    }

    for archivo, label in archivos.items():
        ruta = os.path.join(CARPETA_FAKENEWS, archivo)
        if not os.path.exists(ruta):
            print(f"{ruta} no encontrada")
            continue
        df = pd.read_csv(ruta)
        for _, fila in df.iterrows():
            titulo = str(fila.get("title", "") or "").strip()
            texto_art = str(fila.get("text", "") or "").strip()
            texto = f"{titulo}. {texto_art}".strip() if texto_art else titulo
            texto = re.sub(r'^[A-Z][A-Z ,./()-]*\([^)]+\)s*[--]\s*', '', texto)
            if len(texto) < 10:
                continue
            filas.append({"texto": texto, "label": label})

    df = pd.DataFrame(filas)
    print(f"{len(df)} muestras en el dataset de Fake news de Kaggle"
          f"({(df['label'] == 1).sum()} falsas, {(df['label'] == 0).sum()} verdaderas)")
    return df


def cargar_fakedes() -> pd.DataFrame:
    filas = []

    for split, url in FAKEDES_URLS.items():
        try:
            respuesta = requests.get(url, timeout=30)
            respuesta.raise_for_status()
            df = pd.read_excel(BytesIO(respuesta.content))

            for _, fila in df.iterrows():
                categoria = str(fila.get("Category", "")).strip().lower()
                if categoria == "fake":
                    label = 1
                elif categoria == "true":
                    label = 0
                else:
                    continue

                headline = str(fila.get("Headline", "") or "").strip()
                text = str(fila.get("Text", "") or "").strip()
                texto = f"{headline}. {text}".strip() if text else headline

                if len(texto) < 10:
                    continue

                filas.append({"texto": texto, "label": label})

        except Exception as e:
            print(f"Error cargando FakeDeS ({split}): {e}")
        
    
    df = pd.DataFrame(filas)
    print(f"{len(df)} muestras en FakeDeS"
          f"({(df['label'] == 1).sum()} falsas, {(df['label'] == 0).sum()} verdaderas)")
    return df


def _resumen(nombre: str, df: pd.DataFrame):
    falsas = int((df["label"] == 1).sum())
    verdaderas = int((df["label"] == 0).sum())
    print(f"\nHay un total de {len(df)} muestras")
    print(f"Número de noticias falsas: {falsas} ({round(falsas/len(df)*100, 1)}%)")
    print(f"Número de noticias verdaderas: {verdaderas} ({round(verdaderas/len(df)*100, 1)}%)")


def fusionar():
    df_liar = cargar_liar()
    df_fakedes = cargar_fakedes()
    df_fakenews_en = cargar_fakenews()

    df_propio = pd.DataFrame()
    if os.path.exists(DATASET_CSV):
        df_propio = pd.read_csv(DATASET_CSV)[["texto", "label"]]
        print(f"{len(df_propio)} del dataset propio (BD)")
    else:
        print("No se ha podido encontrar el dataset.csv, por lo que solo se usarán los externos")

   # Dataset solo en español con FakeDeS y datos de los scrapers
    dfs_es = [df_fakedes]
    if not df_propio.empty:
        df_propio_es = df_propio[df_propio["texto"].apply(_es_espanol)]
        print(f"{len(df_propio_es)} muestras en el dataset de la BD filtrando por aquellas en español")
        dfs_es.append(df_propio_es)
    df_es = pd.concat(dfs_es, ignore_index=True).drop_duplicates(subset="texto")
    _resumen("Dataset en espalol (dataset_es.csv)", df_es)
    df_es.to_csv(DATASET_ES, index=False, encoding="utf-8")

    # Dataset solo en inglés con LIAR y datos de los scrapers
    dfs_en = [df_fakenews_en] # Cambiar LIAR por Fake news
    if not df_propio.empty:
        df_propio_en = df_propio[~df_propio["texto"].apply(_es_espanol)]
        print(f"{len(df_propio_en)} muestras en el dataset de la BD filtrando por aquellas en inglés")
        dfs_en.append(df_propio_en)
    df_en = pd.concat(dfs_en, ignore_index=True).drop_duplicates(subset="texto")
    _resumen("Dataset en inglés (dataset_en.csv)", df_en)
    df_en.to_csv(DATASET_EN, index=False, encoding="utf-8")

    # Dataset con LIAR, FakeDeS y datos de los scrapers
    dfs_final = [df_fakenews_en, df_fakedes]
    if not df_propio.empty:
        dfs_final.append(df_propio)
    df_completo = pd.concat(dfs_final, ignore_index=True).drop_duplicates(subset="texto")
    _resumen("Dataset mixto (dataset_completo.csv)", df_completo)
    df_completo.to_csv(DATASET_FUSIONADO, index=False, encoding="utf-8")
    

if __name__ == "__main__":
    fusionar()