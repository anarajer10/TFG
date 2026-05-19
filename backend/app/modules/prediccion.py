# Carga el modelo entrenado y crea una función de predicción
import pickle
import os
import logging
from langdetect import detect # type: ignore

logger = logging.getLogger(__name__)

# Rutas a los archivos del modelo
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_RUTAS = {
    "es": (
        os.path.join(_BASE_DIR, "modelo_es.pkl"),
        os.path.join(_BASE_DIR, "vectorizer_es.pkl"),
    ),
    "en": (
        os.path.join(_BASE_DIR, "modelo_en.pkl"),
        os.path.join(_BASE_DIR, "vectorizer_en.pkl"),
    ),
}

# Solo se cargan la primera vez
_modelos = {"es": None, "en": None}
_vectorizers = {"es": None, "en": None}

def _detectar_idioma(texto: str) -> str:
    try:
        lang = detect(texto[:300])
        return lang if lang in _RUTAS else "es"
    except Exception:
        return "es"

def _cargar_modelo(lang: str) -> bool:

    if _modelos[lang] is not None:
        return True
    
    modelo_path, vectorizer_path = _RUTAS[lang]
    
    if not os.path.exists(modelo_path) or not os.path.exists(vectorizer_path):
        logger.error(f"No se han encontrado los archivos .pkl del modelo '{lang}'")
        return False
    
    try:
        with open(modelo_path, "rb") as f:
            _modelos[lang] = pickle.load(f)
        with open(vectorizer_path, "rb") as f:
            _vectorizers[lang] = pickle.load(f)
        logger.info(f"Modelo '{lang}' de fakenews cargado")
        return True
    except Exception as e:
        logger.error(f"Error cargando el modelo '{lang}': {e}")
        return False
    
# Predicción de noticias reales/falsas usando el modelo entrenado
def predecir(titulo: str, descripcion: str, lang: str | None = None) -> tuple[str, float]:
    texto = f"{titulo}. {descripcion}".strip()
    if not texto or len(texto) < 5:
        return "pendiente", 0.5
    
    lang = lang if lang in _RUTAS else _detectar_idioma(texto)

    # Si falla el modelo del idioma detectado, se intenta con el español como fallback
    if not _cargar_modelo(lang):
        if lang != "es" and _cargar_modelo("es"):
            lang = "es"
        else:
            return "pendiente", 0.5
    
    try:
        X = _vectorizers[lang].transform([texto])
        prob_falsa = float(_modelos[lang].predict_proba(X)[0][1])
        etiqueta = "falsa" if prob_falsa >= 0.5 else "verdadera"
        return etiqueta, round(prob_falsa, 4)
    
    except Exception as e:
        logger.error(f"Error en la predicción: {e}")
        return "pendiente", 0.5

    
