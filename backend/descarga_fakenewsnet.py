import os
import time
import pandas as pd
from newspaper import Article

CARPETA = "dataset_fakenewsnet"
SALIDA = os.path.join(CARPETA, "politifact_content.csv")

def _descargar(url: str, titulo: str) -> str:
    try:
        article = Article(url)
        article.download()
        article.parse()
        texto = article.text or ""
        if len(texto) > 50:
            return f"{titulo}. {texto}".strip()
    except Exception:
        pass
    return titulo if len(titulo) > 20 else ""

def descargar():
    resultados = []
    archivos = [
        (os.path.join(CARPETA, "politifact_fake.csv"), 1),
        (os.path.join(CARPETA, "politifact_real.csv"), 0),
    ]

    for ruta, label in archivos:
        df = pd.read_csv(ruta)
        nombre = "fake" if label == 1 else "real"
        print(f"Descarga de {len(df)} articulos {nombre}")
        ok = 0
        for i, row in df.iterrows():
            url = str(row.get("news_url", "") or "").strip()
            titulo = str(row.get("title", "") or "").strip()
            if not url and not titulo:
                continue
            texto = _descargar(url, titulo) if url else titulo
            if texto:
                resultados.append({"texto": texto, "label": label})
                ok += 1
            if (i+1)%25 == 0:
                print(f"{ok} ok de {i+1}/{len(df)}")
            time.sleep(0.3)

    df_out = pd.DataFrame(resultados)
    df_out.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"\nGuardado en {SALIDA}")
    print(f"Total de {len(df_out)}"
          f"({(df_out['label']==1).sum()} falsas,  { (df_out['label']==0).sum()} verdaderas)")
    
if __name__ == "__main__":
    descargar()
