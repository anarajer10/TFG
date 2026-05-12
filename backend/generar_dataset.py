# Lee las noticias etiquetadas como 'verdadera' o 'falsa' de la BD
# y genera un csv y un json para entrenar el modelo

import json
import csv
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.database import engine
from app.models.schema import Noticia, EtiquetaEnum

def generar_dataset(salida_csv: str = "dataset.csv", salida_json: str = "dataset.json") -> list[dict]:
    dataset = []

    with Session(engine) as session:
        noticias = session.exec(select(Noticia).where(
            Noticia.etiqueta.in_([EtiquetaEnum.falsa, EtiquetaEnum.verdadera])
        )).all()

    print(f"\nNoticias encontradas en la BD: {len(noticias)}")

    falsas = 0
    verdaderas = 0

    for noticia in noticias:
        # para entrenar son el título y la descripción
        titulo = noticia.titulo or ""
        descripcion = noticia.descripcion or ""

        # Para las noticias de fact-checkers, solo el titulo es el claim, la descripción es donde se desmiente
        if noticia.categoria == "Fact-Check":
            texto = titulo.strip()
        else:
            texto = f"{titulo}. {descripcion}".strip()

        if not texto or len(texto) < 10:
            continue

        label = 1 if noticia.etiqueta == EtiquetaEnum.falsa else 0

        if label == 1:
            falsas += 1
        else:
            verdaderas += 1

        dataset.append({
            "id":           noticia.id,
            "titulo":       titulo,
            "descripcion":  descripcion,
            "texto":        texto,
            "label":        label,
            "etiqueta":     noticia.etiqueta.value,
            "fuente_id":    noticia.fuente_id,
            "categoria":    noticia.categoria or "",
        })

    print(f"Noticias falsas: {falsas}")
    print(f"Noticias verdaderas: {verdaderas}")
    print(f"Total del dataset: {len(dataset)}")

    if not dataset:
        print("Error, no hay noticias etiquetadas en la BD")
        return []
    
    # Para guardar el csv
    with open(salida_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "titulo", "descripcion", 
                                "texto", "label", "etiqueta", "fuente_id", "categoria"])
        writer.writeheader()
        writer.writerows(dataset)
    print(f"\n csv guardado en: {salida_csv}")

    # Para guardar el json
    with open(salida_json, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"\n json guardado en: {salida_json}")

    # Resumen para la memoria
    print(f"Total de muestras: {len(dataset)}")
    print(f"Clase 1 (falsa): {falsas} ({round(falsas/len(dataset)*100, 1)}%)")
    print(f"Clase 0 (real): {verdaderas} ({round(verdaderas/len(dataset)*100, 1)}%)")
    balance = "Balanceado" if abs(falsas - verdaderas)/len(dataset) < 0.15 else "Desbalanceado"
    print(f"Balance: {balance}")

    return dataset

if __name__ == "__main__":
    generar_dataset()