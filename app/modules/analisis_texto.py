import re
import os
import logging
from pysentimiento import create_analyzer # type: ignore
import spacy # type: ignore
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

os.environ["HF_TOKEN"] = os.getenv("HUGGINGFACE_API_KEY", "")

# Carga de modelos para el módulo (solo se cargan una vez)
_sentiment_es = None
_sentiment_en = None
_emotion_es = None
_emotion_en = None
_nlp_es = None
_nlp_en = None

def _get_models(lang:str):
    global _sentiment_es, _sentiment_en, _emotion_es, _emotion_en, _nlp_es, _nlp_en

    # Español
    if lang == "es":
        if _sentiment_es is None:
            _sentiment_es = create_analyzer(task="sentiment", lang="es")
            # Modelo que se usa en español
            print(f"Modelo español cargado: {_sentiment_es.model.config._name_or_path}")
        if _emotion_es is None:
            _emotion_es = create_analyzer(task="emotion", lang="es")
        if _nlp_es is None:
            _nlp_es = spacy.load("es_core_news_sm")
        return _sentiment_es, _emotion_es, _nlp_es
    else: # Inglés
        if _sentiment_en is None:
            _sentiment_en = create_analyzer(task="sentiment", lang="en")
            # Lo mismo en inglés
            print(f"Modelo inglés cargado: {_sentiment_en.model.config._name_or_path}")
        if _emotion_en is None:
            _emotion_en = create_analyzer(task="emotion", lang="en")
        if _nlp_en is None:
            _nlp_en = spacy.load("en_core_web_sm")
        return _sentiment_en, _emotion_en, _nlp_en
    
# Palabras que pueden ser subjetivas o denotar emoción
PALABRAS_ES = ["escandaloso", "escándalo", "brutal", "devastador", "catastrófico", "alarmante",
               "terrible", "horrible", "increíble", "impactante", "urgente", "peligroso",
               "secreto", "prohibido", "revelado", "exclusivo", "bomba", "expuesto"]

PALABRAS_EN = ["shocking", "scandal", "brutal", "devastating", "catastrophic", "alarming",
               "terrible", "horrible", "incredible", "impactful", "urgent", "dangerous",
               "secret", "banned", "revealed", "exclusive", "bombshell", "exposed"]


# Preprocesamiento de texto(tokenización, stop words, lematización y NER)
def _preprocesar_texto(texto: str, doc, lang: str) -> dict:
    # Tokens (separacion por espacios y puntos)
    tokens_brutos = [t for t in doc if not t.is_punct and not t.is_space]

    # Eliminación de stop words
    tokens_sin_stopwords = [t for t in tokens_brutos if not t.is_stop]

    # Lematización
    lemas = [t.lemma_.lower() for t in tokens_sin_stopwords]

    # NER (detectadas con spacy)
    entidades = [
        {"texto": ent.text, "tipo": ent.label_}
        for ent in doc.ents
    ]

    # Adjetivos y adverbios intensificadores (ADV/ADJ con + dd 3 caracteres)
    intensificadores = [t for t in doc if t.pos_ in ("ADV", "ADJ") and len(t.text)>3]

    return{
        "tokens": tokens_brutos,
        "tokens_sin_stop_words": tokens_sin_stopwords,
        "lemas": lemas,
        "entidades": entidades,
        "intensificadores": intensificadores,
    }


# Muy subjetivo (0.0) / Objetivo (1.0)
def _calcular_objetividad(texto: str, prep: dict, lang: str) -> float:
    if not texto:
        return -1.0 
    
    penalizacion = 0.0
    palabras = texto.split()
    total_palabras = max(len(palabras), 1)

    # Adverbios y adjetivos intensificadores
    ratio_intensificadores = len(prep["intensificadores"])/total_palabras
    penalizacion += min(ratio_intensificadores*2, 0.3)

    # palabras subjetivas o con emoción
    palabras_subj = PALABRAS_ES if lang == "es" else PALABRAS_EN
    texto_minusculas = texto.lower()
    count_subj = sum(1 for p in palabras_subj if p in texto_minusculas)
    penalizacion += min(count_subj*0.05, 0.25)

    # palabras en mayúsculas (exluyendo siglas de menos de 3 letras)
    palabras_mayusc = [p for p in palabras if p.isupper() and len(p) > 3]
    ratio_mayusc = len(palabras_mayusc)/total_palabras
    penalizacion += min(ratio_mayusc*3, 0.2)

    # exclamaciones e interragociones múltiples
    signos = texto.count("!") + texto.count("?")
    penalizacion += min(signos*0.02, 0.15)

    # palabras en mayúsculas en el título
    if texto[:100].isupper():
        penalizacion += 0.2

    objetividad = max(0.0, round(1.0-penalizacion, 4))
    return objetividad


def analizar_texto(texto: str, titulo: str = "", lang: str = "es") -> dict:
    resultado = {
        "sentimiento": "NEU",
        "prob_sentimiento": {},
        "emocion": "-",
        "prob_emocion": {},
        "punt_sentimiento": 0.0,
        "punt_objetividad": 1.0,
        "indicadores": [],
        "entidades": [],
        "lemas": [],
    }

    if not texto:
        return resultado
    
    try:
        lang = "es" if lang.lower() in ["es", "español", "spanish"] else "en"

        sentiment_analyzer, emotion_analyzer, nlp = _get_models(lang)

        texto_truncado = texto[:1000]
        texto_analisis = f"{titulo}.{texto_truncado}" if titulo else texto_truncado
        
        # Preprocesamiento
        doc = nlp(texto_truncado)
        prep = _preprocesar_texto(texto_truncado, doc, lang)

        resultado["entidades"] = prep["entidades"]
        resultado["lemas"] = prep["lemas"][:50]

        # Análisis de sentimientos
        sentiment_result = sentiment_analyzer.predict(texto_analisis)
        resultado["sentimiento"] = sentiment_result.output
        resultado["prob_sentimiento"] = {k: round(v, 4) for k, v in sentiment_result.probas.items()}

        # puntuación numérica
        probas = sentiment_result.probas
        resultado["punt_sentimiento"] = round(
            probas.get("POS", 0) - probas.get("NEG", 0), 4
        )

        # Análisis de emociones
        emotion_result = emotion_analyzer.predict(texto_analisis)
        resultado["emocion"] = emotion_result.output
        resultado["prob_emocion"] = {k: round(v, 4) for k, v in emotion_result.probas.items()}

        # análisis de objetividad con spacy
        resultado["punt_objetividad"] = _calcular_objetividad(texto, prep, lang)

        # indicadores de sensacionalismo
        indicadores = []
        palabras_subj = PALABRAS_ES if lang == "es" else PALABRAS_EN
        texto_minusc = texto.lower()

        texto_limpio = re.sub(r'[¡!¿?.,;]', '', texto_minusc)

        for palabra in palabras_subj:
            if palabra.lower() in texto_limpio:
                indicadores.append(f"lenguaje subjetivo:{palabra}")

        if texto.count("!") > 2:
            indicadores.append("exclamaciones excesivas")

        palabras = texto.split()
        palabras_mayusc = [p for p in palabras if p.isupper() and len(p) > 3]
        if len(palabras_mayusc)/max(len(palabras), 1) > 0.1:
            indicadores.append("exceso de mayúsculas")

        resultado["indicadores"] = indicadores

    except Exception as e:
        logger.error(f"Error en el análisis PLN {e}")

    return resultado