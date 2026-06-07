import json
import re
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
import spacy
import nltk
from nltk.stem import SnowballStemmer
from nltk.corpus import stopwords
from pysentimiento import create_analyzer

nltk.download("stopwords", quiet=True)

nlp_es = spacy.load("es_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")

sentiment_es = create_analyzer(task="sentiment", lang="es")
sentiment_en = create_analyzer(task="sentiment", lang="en")

# Umbrales predefinidos
DEF_UMBRAL_OBJ = 0.4
DEF_UMBRAL_SENT = -0.3
DEF_AJUSTE = 0.05
DEF_PESO_NEU = 0.6

def _preproc(texto, lang):
    if lang == "es":
        return texto
    stemmer = SnowballStemmer("english")
    stop_words = set(stopwords.words("english"))
    tokens = re.findall(r"\b\w+\b", texto.lower())
    tokens = [stemmer.stem(t) for t in tokens if t not in stop_words and len(t)>1]
    return " ".join(tokens)

def _objetividad_heu(texto, doc):
    penalizacion = 0.0
    palabras = texto.split()
    total = max(len(palabras), 1)
    intensificadores = [t for t in doc if t.pos_ in ("ADV", "ADJ") and len(t.text)>3]
    penalizacion += min(len(intensificadores)/total*2, 0.3)
    mayusc = [p for p in palabras if p.isupper() and len(p)>3]
    penalizacion += min(len(mayusc)/total*3, 0.2)
    signos = texto.count("!")+texto.count("?")
    penalizacion += min(signos*0.02, 0.15)
    if texto[:100].isupper():
        penalizacion += 0.2
    return max(0.0, round(1.0 - penalizacion, 4))


def analizar_muestra(texto, lang):
    analyzer = sentiment_es if lang == "es" else sentiment_en
    nlp = nlp_es if lang == "es" else nlp_en
    texto_trunc = texto[:1000]
    result = analyzer.predict(texto_trunc)
    probas = result.probas
    punt_sent = round(probas.get("POS", 0) - probas.get("NEG", 0), 4)
    prob_neu = probas.get("NEU", 0.5)
    doc = nlp(texto_trunc)
    punt_heu = _objetividad_heu(texto_trunc, doc)
    return punt_sent, prob_neu, punt_heu

def cargar_datos(dataset_csv, lang, modelo_plk, vectorizer_plk):
    with open(modelo_plk, "rb") as f:
        modelo = pickle.load(f)
    with open(vectorizer_plk, "rb") as f:
        vectorizer = pickle.load(f)
    if not hasattr(modelo, "multi_class"):
        modelo.multi_class = "auto"

    df = pd.read_csv(dataset_csv)
    X_all = df["texto"].fillna("")
    y_all = df["label"]

    _, X_test, _, y_test = train_test_split(X_all, y_all, test_size=0.2, random_state=42, stratify=y_all)

    X_test_proc = [_preproc(t, lang) for t in X_test]
    X_vec = vectorizer.transform(X_test_proc)
    probs_base = modelo.predict_proba(X_vec)[:, 1]

    return list(X_test), np.array(y_test), probs_base


def analizar_test(X_test, lang):
    print(f"Análisis de {len(X_test)} muestras con pysentimiento")
    sent_arr, neu_arr, heu_arr = [], [], []
    for texto in X_test:
        punt_sent_val, prob_neu_val, punt_heu_val = analizar_muestra(texto, lang)
        sent_arr.append(punt_sent_val)
        neu_arr.append(prob_neu_val)
        heu_arr.append(punt_heu_val)
    return np.array(sent_arr), np.array(neu_arr), np.array(heu_arr)

def experimento(dataset_csv, lang, modelo_plk, vectorizer_plk):
    print(f"\n[{lang.upper()}]")
    X_test, y_test, probs_base = cargar_datos(dataset_csv, lang, modelo_plk, vectorizer_plk)
    punt_sent, prob_neu, prob_heu = analizar_test(X_test, lang)

    punt_obj = prob_neu*DEF_PESO_NEU + prob_heu*(1-DEF_PESO_NEU)

    resultado = {}

    def calcular_f1(probs):
        return round(f1_score(y_test, (np.clip(probs, 0.0, 0.99) >= 0.5).astype(int)), 4)
    
    print("Umbral de objetividad:")
    barrido_obj = {}
    for umbral in [0.3, 0.35, 0.4, 0.45, 0.5]:
        probs = probs_base + np.where(punt_obj < umbral, DEF_AJUSTE, 0.0) + np.where(punt_sent < DEF_UMBRAL_SENT, DEF_AJUSTE, 0.0)
        barrido_obj[umbral] = calcular_f1(probs)
        marca = "Actual" if umbral == DEF_UMBRAL_OBJ else ""
        print(f"{umbral:.2f} -> F1={barrido_obj[umbral]:.4f}{marca}")

    print("Umbral de sentimiento:")
    barrido_sent = {}
    for umbral in [-0.2, -0.25, -0.3, -0.35, -0.4]:
        probs = probs_base + np.where(punt_obj < DEF_UMBRAL_OBJ, DEF_AJUSTE, 0.0) + np.where(punt_sent < umbral, DEF_AJUSTE, 0.0)
        barrido_sent[umbral] = calcular_f1(probs)
        marca = "Actual" if umbral == DEF_UMBRAL_SENT else ""
        print(f"{umbral:.2f} -> F1={barrido_sent[umbral]:.4f}{marca}")

    print("Tamaño de ajuste:")
    barrido_ajuste= {}
    for ajuste in [0.03, 0.05, 0.07, 0.1]:
        probs = probs_base + np.where(punt_obj < DEF_UMBRAL_OBJ, ajuste, 0.0) + np.where(punt_sent < DEF_UMBRAL_SENT, ajuste, 0.0)
        barrido_ajuste[ajuste] = calcular_f1(probs)
        marca = "Actual" if ajuste == DEF_AJUSTE else ""
        print(f"{ajuste:.2f} -> F1={barrido_ajuste[ajuste]:.4f}{marca}")

    print("Peso prob_NEU en la fórmula de objetividad:")
    barrido_peso = {}
    for peso_neu in [0.4, 0.5, 0.6, 0.7, 0.8]:
        punt_obj_peso = prob_neu*peso_neu + prob_heu*(1-peso_neu)
        probs = probs_base + np.where(punt_obj_peso < DEF_UMBRAL_OBJ, DEF_AJUSTE, 0.0) + np.where(punt_sent < DEF_UMBRAL_SENT, DEF_AJUSTE, 0.0)
        barrido_peso[peso_neu] = calcular_f1(probs)
        marca = "Actual" if peso_neu == DEF_PESO_NEU else ""
        print(f"{peso_neu:.2f} -> F1={barrido_peso[peso_neu]:.4f}{marca}")

    resultado["barrido"] = {
        "umbral_obj": barrido_obj,
        "umbral_sent": barrido_sent,
        "umbral_ajuste": barrido_ajuste,
        "peso_neu": barrido_peso,
    }

    borderline = (probs_base >= 0.45) & (probs_base < 0.50)
    n_borderline = int(np.sum(borderline))
    print(f"\nDiagnóstico borderline ({n_borderline} muestras con probs_base en [0.45, 0.50)):")
    if n_borderline > 0:
        prob_neu_border = prob_neu[borderline]
        prob_heu_border = prob_heu[borderline]
        print(f"  prob_neu (p_NEU): media={prob_neu_border.mean():.4f}")
        print(f"  prob_heu (heurística): media={prob_heu_border.mean():.4f}")


    return resultado

if __name__ == "__main__":
    print("Comparativa de heurísticas")

    res_es = experimento("dataset_es.csv", "es", "modelo_es.pkl", "vectorizer_es.pkl")
    res_en = experimento("dataset_en.csv", "en", "modelo_en.pkl", "vectorizer_en.pkl")

    with open("comparativas_heu.json", "w", encoding="utf-8") as f:
        json.dump({"es": res_es, "en": res_en}, f, ensure_ascii=False, indent=2)

