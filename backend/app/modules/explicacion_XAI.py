# La explicación XAI se hace con Ollama (llama3.2:3b)
# Recibe los resultados de ambos análisis y genera una explicación en lenguaje natural con una justificación

import logging
import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

# Interpretación de las métricas

def _interpretar_ela(score: float) -> str:
    if score == -1.0:
        return "No se ha podido analizar la manipulación/diferencia de píxeles"
    elif score < 8:
        return f"El análisis ELA ({score}) detecta manipulación escasa de los píxeles"
    elif score < 15: 
        return f"El análisis ELA ({score}) muestra niveles moderados de compresión, indicando una edición leve"
    else:
        return f"El análisis ELA ({score}) supera el umbral de manipulación, por lo que existen diferencias de píxeles significativas. Esto significa que la imagen ha sido editada o posiblemente reciclada"
    
def _interpretar_ia(es_ia: bool, confianza: float) -> str:
    if confianza == -1.0:
        return "No se ha podido determinar si la imagen ha sido generada por IA"
    if es_ia:
        return f"El detector de IA ha clasificado la imagen como generada por IA con una confianza del {round(confianza*100, 1)}%"
    else:
        return f"El detector de IA ha clasificado la imagen como no generada por IA con una confianza del {round(confianza*100, 1)}%"

def _interpretar_coherencia(score: float) -> str:
    if score == -1.0:
        return "No se ha podido analizar la coherencia entre la imagen y el título de la noticia"
    elif score == 1.0:
        return "La imagen aparece entre los resultados de búsqueda para el título"
    elif score == 0.75:
        return "El dominio de la imagen está en los resultados de búsqueda para el título"
    else:
        return "Ni la imagen ni su dominio se encuentran entre los resultados de búsqueda para el título"
    
def _interpretar_exif(fuera_contexto: bool, metadatos: dict) -> str:
    if not metadatos:
        return "No se han encontrado los metadatos EXIF en la imagen. Es habitual en imágenes publicadas en medios digitales"
    if fuera_contexto:
        fecha = metadatos.get("DateTime", "desconocida")
        return f"Los metadatos EXIF indican que la imagen fue capturada en {fecha}, con una diferencia temporal significativa respecto a la fecha de publicación de la noticia."
    else:
        return "Los metadatos EXIF no revelan inconsistencias temporales relevantes"
    
def _interpretar_sentimiento(sentimiento: str, punt: float) -> str:
    mapa = {
        "POS": "positivo",
        "NEG": "negativo",
        "NEU": "neutro,"
    }

    sent_texto = mapa.get(sentimiento, sentimiento)
    return f"El análisis de sentimientos del texto es {sent_texto} (puntuación: {round(punt, 2)})"

def _interpretar_objetividad(punt: float) -> str:
    if punt >= 0.8:
        return f"El texto tiene un estilo objetivo y neutro (puntuación de objetividad: {punt})"
    elif punt >= 0.5:
        return f"El texto presenta cierto grado de subjetividad (puntuación de objetividad: {punt})"
    else:
        return f"El texto tiene un estilo subjetivo y no es neutral (puntuación de objetividad: {punt})"
    
def _interpretar_emocion(emocion: str) -> str:
    emociones = {"anger", "fear", "disgust", "sadness", "ira", "miedo", "asco", "tristeza"}

    if not emocion or emocion == "-":
        return "No se ha detectado una emoción destacable en el texto"
    if emocion.lower() in emociones:
        return f"Se detecta una emoción, concretamente '{emocion}, indicando un tono poco objetivo"
    
    return f"Se ha detectado una emoción en el texto, '{emocion}"

def _interpretar_indicadores(indicadores: list) -> str:
    if not indicadores:
        return "No se han detectado indicadores de sensacionalismo en el texto"
    lista = ", ".join(indicadores[:5])
    return f"Se han detectado los indicadores siguientes de posible sensacionalismo: {lista}"

def _interpretar_estatus_imagen(estatus) -> str:
    nombre = estatus.value if hasattr(estatus, "value") else str(estatus)
    mapa = {
        "autentica": "La imagen se clasifica como auténtica",
        "fuera_contexto": "La imagen se clasifica como posiblemente fuera de contexto o manipulada",
        "generada_ia": "La imagen se clasifica como generada por IA"
    }
    return mapa.get(nombre, f"Clasificación de la imagen: {nombre}")


# Construcción del prompt
def _construir_prompt(resultado_imagen: dict, resultado_texto: dict, titulo: str) -> str:
    # Imagen
    ela = _interpretar_ela(resultado_imagen.get("ela_score", -1.0))
    ia = _interpretar_ia(resultado_imagen.get("es_ia", False), resultado_imagen.get("confianza_ia", -1.0))
    coherencia = _interpretar_coherencia(resultado_imagen.get("coherencia_score", -1.0))
    exif = _interpretar_exif(resultado_imagen.get("fuera_contexto", False), resultado_imagen.get("metadatos", {}))
    estatus_img = _interpretar_estatus_imagen(resultado_imagen.get("estatus", "autentica"))

    # Texto
    sentimiento = _interpretar_sentimiento(resultado_texto.get("sentimiento", "NEU"), resultado_texto.get("punt_sentimiento", 0.0))
    objetividad = _interpretar_objetividad(resultado_texto.get("punt_objetividad", -1.0))
    emocion = _interpretar_emocion(resultado_texto.get("emocion", "-"))
    indicadores = _interpretar_indicadores(resultado_texto.get("indicadores", []))

    prompt = f"""Eres un sistema experto en detección de desinformación y fake news.
    Tu tarea es generar una explicación clara, detallada y en español sobre el análisis realizado a la siguiente noticia.

    Título de la noticia: "{titulo}"

    Análisis de la imagen: 
    {ela}
    {ia}
    {coherencia}
    {exif}
    Clasificación final de la imagen: {estatus_img}

    Análisis del texto:
    {sentimiento}
    {objetividad}
    {emocion}
    {indicadores}

    Instrucciones:
    Genera una explicación XAI (Inteligencia Artificial Explicable) completa en español que haga las siguientes cosas:
    1. Resuma en una frase el veredicto general de la noticia.
    2. Explique de forma detallada qué indica cada métrica del análisis de imagen y por qué es relevante para detectar desinformación.
    3. Explique de forma detallada qué indica cada métrica del análisis de texto y cómo contribuye al veredicto final.
    4. Justifique la clasificación final de forma coherente con todos los datos anteriores.
    5. Indique el nivel de confianza general de análisis (alto, medio o bajo) y por qué.

    Sé claro, preciso y accesible para un usuario no técnico. No uses listas con viñetas, redacta en párrafos.
    No inventes datos adicionales ni desvaríes, si una métrica indica que no se ha podido analizar o tiene un valor negativo,
    menciónalo como una limitación del análisis realizado.
    """

    return prompt

# Llamada a Ollama para generar la explicación XAI en lenguaje natural
def generar_explicacion(resultado_imagen: dict, resultado_texto: dict, titulo: str = "") -> str:
    prompt = _construir_prompt(resultado_imagen, resultado_texto, titulo)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 1024}
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "No se ha podido generar la explicación")
    
    except requests.ConnectionError:
        logger.error("Ollama no está ejecutándose")
        return "El servicio de explicación no está disponible"
    
    except Exception as e:
        logger.error(f"Error generando la explicación XAI: {e}")
        return "No se ha podido generar la explicación"
