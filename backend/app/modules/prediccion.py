# Carga el modelo entrenado y crea una función de predicción
import pickle
import os
import logging

logger = logging.getLogger(__name__)

# Rutas a los archivos del modelo
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELO_PATH = os.path.join(_BASE_DIR, "modelo_fake_news.pkl")
VECTORIZER_PATH = os.path.join(_BASE_DIR, "vectorizer.pkl")

# Solo se cargan la primera vez
_modelo = None
_vectorizer = None

def _cargar_modelo():
    global _modelo, _vectorizer

    if _modelo is not None:
        return True
    
    if not os.path.exists(MODELO_PATH) or not os.path.exists(VECTORIZER_PATH):
        logger.error("No se han encontrado el modelo_fake_news.pkl y/o el vectorizer.pkl")
        return False
    
    try:
        with open(MODELO_PATH, "rb") as f:
            _modelo = pickle.load(f)
        with open(VECTORIZER_PATH, "rb") as f:
            _vectorizer = pickle.load(f)
        logger.info("Modelo de fakenews cargado")
        return True
    except Exception as e:
        logger.error(f"Error cargando el modelo: {e}")
        return False
    
# Predicción de noticias reales/falsas usando el modelo entrenado
def predecir(titulo: str, descripcion: str) -> tuple[str, float]:
    if not _cargar_modelo():
        return "pendiente", 0.5
    
    texto = f"{titulo}. {descripcion}".strip()
    if not texto or len(texto) < 5:
        return "pendiente", 0.5
    
    try:
        X = _vectorizer.transform([texto])
        prob_falsa = float(_modelo.predict_proba(X)[0][1])
        etiqueta = "falsa" if prob_falsa >= 0.5 else "verdadera"
        return etiqueta, round(prob_falsa, 4)
    
    except Exception as e:
        logger.error(f"Error en la predicción: {e}")
        return "pendiente", 0.5

    
