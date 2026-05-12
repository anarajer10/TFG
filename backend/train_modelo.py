# Entrenamiento y comparación de modelos para la clasificación de fake news
# Se usan (de momento) Logistic Regression, Random Forest y Gradient Boosting
# Se entrena por un lado con el dataset en español y por otro con el dataset completo, mixto.

import json
import pickle
import sys
import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.utils.class_weight import compute_class_weight

RUTAS_MODELO = {
    "es": ("modelo_es.pkl", "vectorizer_es.pkl"),
    "en": ("modelo_en.pkl", "vectorizer_en.pkl"),
}

# Vectorización TF-IDF
TFIDF_PARAMS = dict(
    max_features=10000,          # 10000 términos más relevantes
    ngram_range=(1, 2),         # Unigramas y bigramas
    min_df=2,                   # Ignorar términos que aparezcan menos de 2 veces
    sublinear_tf=True,          # Para suavizar frecuencias altas
    strip_accents="unicode",
)

# Para las métricas del cross-validation (cv)
def _metricas_cv(nombre: str, pipeline: Pipeline, X: pd.Series, y: pd.Series) -> dict:
    cv = min(5, len(X) // 5)
    scores_f1 = cross_val_score(pipeline, X, y, cv=cv, scoring="f1")
    scores_acc = cross_val_score(pipeline, X, y, cv=cv, scoring="accuracy")
    result = {
        "modelo": nombre,
        "cv_f1_media": round(float(scores_f1.mean()), 4), # media
        "cv_f1_std": round(float(scores_f1.std()), 4), # desviación típica
        "cv_acc_media": round(float(scores_acc.mean()), 4), # media
    }
    print(f"{nombre:30s} F1={result['cv_f1_media']:.3f} ± {result['cv_f1_std']:.3f} "
          f"Accuracy={result['cv_acc_media']:.3f}")
    return result


# Entrena el modelo y devuelve las métricas
def entrenar(dataset_csv: str, sufijo: str) -> dict:
    metricas_path = f"metricas_{sufijo}.json"
    comparativa_path = f"comparativa_{sufijo}.json"

    # Primero se carga el dataset
    if not os.path.exists(dataset_csv):
        print(f"Error: no se encontró el {dataset_csv}")
        return {}

    df = pd.read_csv(dataset_csv)
    print(f"El dataset es {dataset_csv}")
    print(f"El número de muestras es de {len(df)}")
    print(f"Falsas: {(df['label'] == 1).sum()}")
    print(f"Verdaderas: {(df['label'] == 0).sum()}")

    if len(df) < 20:
        print("Error, dataset demasiado pequeño")
        return {}

    X = df["texto"].fillna("")
    y = df["label"]

    clases = np.unique(y)
    pesos = compute_class_weight("balanced", classes=clases, y=y) 
    pesos_dict = dict(zip(clases, pesos)) # En caso de tener un dataset desbalanceado


    pipelines = {
        "LogisticRegression": Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", LogisticRegression(max_iter=1000, class_weight=pesos_dict, C=1.0, solver="lbfgs")),
        ]),
        "RandomForest": Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", RandomForestClassifier(n_estimators=100, class_weight=pesos_dict, random_state=42, n_jobs=-1))
        ]),
        "LinearSVC": Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", CalibratedClassifierCV(LinearSVC(max_iter=2000, class_weight=pesos_dict), cv=3)),
        ]),
    }

    # Comparación con la validación cruzada (cv)
    print("\n Comparación de los algoritmos con validación cruzada")
    comparativa = []
    for nombre, pipeline in pipelines.items():
        print(f"Entrenamiento del modelo {nombre}")
        comparativa.append(_metricas_cv(nombre, pipeline, X, y))

    mejor = max(comparativa, key=lambda x: x["cv_f1_media"])
    print(f"\n El mejor modelo es {mejor['modelo']} con un F1 de {mejor['cv_f1_media']:.3f}")
    
    # Evaluación final del mejor modelo
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    print(f"\n Entrenamiento: {len(X_train)} muestras")
    print(f"\n Prueba: {len(X_test)} muestras")
    
    pipeline_final = pipelines[mejor["modelo"]]
    pipeline_final.fit(X_train, y_train)

    # Predicción
    y_pred = pipeline_final.predict(X_test)
    y_pred_prob = pipeline_final.predict_proba(X_test)[:, 1]
    report = classification_report(y_test, y_pred, output_dict=True)
    matriz = confusion_matrix(y_test, y_pred).tolist()

    try:
        auc = round(roc_auc_score(y_test, y_pred_prob), 4) # Curva ROC
    except Exception as e:
        print(f"Error ROC-AUC: {e}")
        auc = -1.0


    metricas = {
        "dataset": dataset_csv,
        "total_muestras": len(df),
        "falsas": int((df["label"] == 1).sum()),
        "verdaderas": int((df["label"] == 0).sum()),
        "modelo": mejor["modelo"],
        "test_size": 0.2,
        "accuracy": round(report["accuracy"], 4),
        "precision_falsa": round(report.get("1", {}).get("precision", 0), 4),
        "recall_falsa": round(report.get("1", {}).get("recall", 0), 4),
        "f1_falsa": round(report.get("1", {}).get("f1-score", 0), 4),
        "precision_real": round(report.get("0", {}).get("precision", 0), 4),
        "recall_real": round(report.get("0", {}).get("recall", 0), 4),
        "f1_real": round(report.get("0", {}).get("f1-score", 0), 4),
        "roc_auc": auc,
        "cv_f1_media": mejor["cv_f1_media"],
        "cv_f1_std": mejor["cv_f1_std"],
        "matriz_confusion": matriz,
        "vectorizador": "TfidfVectorizer(max_features=10000, ngram_range=(1,2))",
        "comparativa": comparativa,
    }

    # Resultados
    print("\n Métricas del modelo")
    print(f"\nAccuracy: {metricas['accuracy']}")
    print(f"ROC-AUC: {metricas['roc_auc']}")
    print(f"F1 (falsa): {metricas['f1_falsa']}")
    print(f"F1 (real): {metricas['f1_real']}")
    # print(f"F1 media: {metricas['cv_f1_media']} ± {metricas['cv_f1_std']}")
    print(f"Matriz de confusión: {matriz}")

    # Por último, se guarda el modelo y el vectorizador
    if sufijo in RUTAS_MODELO:
        modelo_path, vectorizer_path = RUTAS_MODELO[sufijo]
        with open(modelo_path, "wb") as f:
            pickle.dump(pipeline_final.named_steps["clf"], f)
        with open(vectorizer_path, "wb") as f:
            pickle.dump(pipeline_final.named_steps["tfidf"], f)
        print(f"\nModelo de producción guardado: {modelo_path} / {vectorizer_path}")

    with open(metricas_path, "w", encoding="utf-8") as f:
        json.dump(metricas, f, ensure_ascii=False, indent=2)
    print(f"\nMétricas guardadas en: {metricas_path}")

    with open(comparativa_path, "w", encoding="utf-8") as f:
        json.dump(comparativa, f, ensure_ascii=False, indent=2)
    print(f"\nComparativa guardada en: {comparativa_path}")

    return metricas

if __name__ == "__main__":
    print("Dataset español")
    entrenar("dataset_es.csv", "es")

    print("Dataset inglés")
    entrenar("dataset_en.csv", "en")

    print("Dataset completo")
    entrenar("dataset_completo.csv", "completo")