# Entrenamiento para la clasificación de fake news
# Uso de TF-IDF y la Regresión Logística

import json
import pickle
import sys
import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.utils.class_weight import compute_class_weight

DATASET_CSV = "dataset.csv"
MODELO_PATH = "modelo_fake_news.pkl"
VECTORIZER_PATH = "vectorizer.pkl"
METRICAS_PATH = "metricas.json"

# Entrena el modelo y devuelve las métricas
def entrenar() -> dict:
    # Primero se carga el dataset
    if not os.path.exists(DATASET_CSV):
        print(f"Error: no se encontró el {DATASET_CSV}")
        sys.exit(1)

    df = pd.read_csv(DATASET_CSV)
    print(f"Número de muestras: {len(df)}")
    print(f"Falsas: {(df['label'] == 1).sum()}")
    print(f"Verdaderas: {(df['label'] == 0).sum()}")

    if len(df) < 20:
        print("Error, dataset demasiado pequeño")
        sys.exit(1)

    X = df["texto"].fillna("")
    y = df["label"]

    # Vectorización TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=5000,      # 5000 términos más relevantes
        ngram_range=(1,2),      # Unigramas y bigramas
        min_df=2,               # Ignorar términos que aparezcan menos de 2 veces
        sublinear_tf=True,      # Para suavizar frecuencias altas
        strip_accents="unicode",
    )

    X_vec = vectorizer.fit_transform(X)

    # Separación del dataset en entrenamiento (train) y prueba (test)
    test_size = 0.3 if len(df) < 100 else 0.2

    X_train, X_test, y_train, y_test = train_test_split(
        X_vec, y,
        test_size=test_size,
        random_state=42,
        stratify=y,
    )

    print(f"\n Entrenamiento: {X_train.shape[0]} muestras")
    print(f"\n Prueba: {X_test.shape[0]} muestras")
    clases = np.unique(y_train)
    pesos = compute_class_weight("balanced", classes=clases, y=y_train) 
    pesos_dict = dict(zip(clases, pesos)) # En caso de tener un dataset desbalanceado

    # Entrenamiento
    modelo = LogisticRegression(
        max_iter=1000,
        class_weight=pesos_dict, # Para compensar el desbalance en caso de que haya
        C=1.0, 
        solver="lbfgs",
    )
    modelo.fit(X_train, y_train)

    # Predicción
    y_pred = modelo.predict(X_test)
    y_pred_prob = modelo.predict_proba(X_test)[:, 1]
    report = classification_report(y_test, y_pred, output_dict=True)
    matriz = confusion_matrix(y_test, y_pred).tolist()

    try:
        auc = round(roc_auc_score(y_test, y_pred_prob), 4) # Curva ROC
    except Exception as e:
        print(f"Error ROC-AUC: {e}")
        auc = -1.0

    # Validación cruzada (cross-validation)
    cv_scores = cross_val_score(
        LogisticRegression(max_iter=1000, class_weight=pesos_dict, solver="lbfgs"),
        X_vec, y, cv=min(5, len(df) // 5), scoring="f1" # F1-score
    )

    metricas = {
        "total_muestras": len(df),
        "falsas": int((df["label"] == 1).sum()),
        "verdaderas": int((df["label"] == 0).sum()),
        "test_size": test_size,
        "accuracy": round(report["accuracy"], 4),
        "precision_falsa": round(report.get("1", {}).get("precision", 0), 4),
        "recall_falsa": round(report.get("1", {}).get("recall", 0), 4),
        "f1_falsa": round(report.get("1", {}).get("f1-score", 0), 4),
        "precision_real": round(report.get("0", {}).get("precision", 0), 4),
        "recall_real": round(report.get("0", {}).get("recall", 0), 4),
        "f1_real": round(report.get("0", {}).get("f1-score", 0), 4),
        "roc_auc": auc,
        "cv_f1_media": round(float(cv_scores.mean()), 4),
        "cv_f1_std": round(float(cv_scores.std()), 4),
        "matriz_confusion": matriz,
        "modelo": "LogisticRegression",
        "vectorizador": "TfidfVectorizer(max_features=5000, ngram_range=(1,2))"
    }

    # Resultados
    print("\n Métricas del modelo")
    print(f"Accuracy: {metricas['accuracy']}")
    print(f"ROC-AUC: {metricas['roc_auc']}")
    print(f"F1 (falsa): {metricas['f1_falsa']}")
    print(f"F1 (real): {metricas['f1_real']}")
    print(f"F1 media: {metricas['cv_f1_media']} ± {metricas['cv_f1_std']}")
    print(f"Matriz de confusión: {matriz}")

    # Por último, se guarda el modelo y el vectorizador
    with open(MODELO_PATH, "wb") as f:
        pickle.dump(modelo, f)
    print(f"\nModelo guardado en: {MODELO_PATH}")

    with open(VECTORIZER_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    print(f"\nVectorizador guardado en: {VECTORIZER_PATH}")

    with open(METRICAS_PATH, "w", encoding="utf-8") as f:
        json.dump(metricas, f, ensure_ascii=False, indent=2)
    print(f"\nMétricas guardadas en: {METRICAS_PATH}")

    return metricas

if __name__ == "__main__":
    entrenar()