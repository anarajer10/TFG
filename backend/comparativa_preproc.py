import json
import re
import pandas as pd
import numpy as np
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
from sklearn.utils.class_weight import compute_class_weight
import spacy
import nltk
from nltk.stem import SnowballStemmer
from nltk.corpus import stopwords

nltk.download("stopwords", quiet=True)

nlp_es = spacy.load("es_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")

# Vectorización TF-IDF
TFIDF_PARAMS = dict(
    max_features=10000,          # 10000 términos más relevantes
    ngram_range=(1, 2),         # Unigramas y bigramas
    min_df=2,                   # Ignorar términos que aparezcan menos de 2 veces
    sublinear_tf=True,          # Para suavizar frecuencias altas
    strip_accents="unicode",
)

def preprocess_raw(texts, lang):
    return texts.tolist()

def preprocess_lemma(texts, lang):
    nlp = nlp_es if lang == "es" else nlp_en
    result = []
    for doc in nlp.pipe(texts.tolist(), batch_size=64, disable=["ner", "parser"]):
        tokens = [
            t.lemma_.lower()
            for t in doc
            if not t.is_stop and not t.is_punct and not t.is_space and len(t.text) > 1
        ]
        result.append(" ".join(tokens))
    return result

def preprocess_stem(texts, lang):
    lang_nltk = "spanish" if lang == "es" else "english"
    stemmer = SnowballStemmer(lang_nltk)
    stop_words = set(stopwords.words(lang_nltk))
    result = []
    for text in texts:
        tokens = re.findall(r"\b\w+\b", text.lower())
        tokens = [stemmer.stem(t) for t in tokens if t not in stop_words and len(t) > 1]
        result.append(" ".join(tokens))
    return result

PREPROCESSORS = {
    "Sin preprocesamiento": preprocess_raw,
    "Lematizacion + stopwords": preprocess_lemma,
    "Stemming + stopwords": preprocess_stem,
}

def evaluar(dataset_csv, lang):
    df = pd.read_csv(dataset_csv)
    X_raw = df["texto"].fillna("")
    y = df["label"]

    clases = np.unique(y)
    pesos = compute_class_weight("balanced", classes=clases, y=y)
    pesos_dict = dict(zip(clases, pesos))

    resultados = []
    for nombre, preprocesador in PREPROCESSORS.items():
        print(f" [{lang.upper()}] {nombre}")
        X = preprocesador(X_raw, lang)
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", CalibratedClassifierCV(
                LinearSVC(max_iter=2000, class_weight=pesos_dict), cv=3
            )),
        ])
        cv = min(5, len(X) // 5)
        f1 = cross_val_score(pipeline, X, y, cv=cv, scoring="f1")
        acc = cross_val_score(pipeline, X, y, cv=cv, scoring="accuracy")
        resultados.append({
            "preprocesamiento": nombre,
            "f1_media": round(float(f1.mean()), 4),
            "f1_std": round(float(f1.std()), 4),
            "acc_media": round(float(acc.mean()), 4),
        })
        print(f"F1={f1.mean():.4f} ± {f1.std():.4f} Acc={acc.mean():.4f}")
    return resultados


if __name__ == "__main__":
    print("Comparativa de preprocesamiento")
    resultados_es = evaluar("dataset_es.csv", "es")
    resultados_en = evaluar("dataset_en.csv", "en")

    resultados_json = {"es": resultados_es, "en": resultados_en}
    with open("comparativa_preprocesamiento.json", "w", encoding="utf-8") as f:
        json.dump(resultados_json, f, ensure_ascii=False, indent=2)

    print("Tabla de resultados")
    cabecera = f"{'Preprocesamiento':<30} {'F1 ES':>8} {'±':>8} {'Acc ES':>8} {'F1 EN':>8} {'±':>8} {'Acc EN':>8}"
    print(cabecera)
    for r_es, r_en in zip(resultados_es, resultados_en):
        print(
            f"{r_es['preprocesamiento']:<30}"
            f"{r_es['f1_media']:>8.4f} {r_es['f1_std']:>6.4f} {r_es['acc_media']:>9.4f} "
            f"{r_en['f1_media']:>8.4f} {r_en['f1_std']:>6.4f} {r_en['acc_media']:>9.4f} "
        )