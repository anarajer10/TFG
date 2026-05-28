# La explicación automática se hace con Ollama (llama3.2:3b)
# Recibe los resultados de ambos análisis y genera una explicación en lenguaje natural con una justificación
import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

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
    elif score >= 0.55:
        return f"La imagen es coherente con el título de la noticia (similitud semántica: {score})"
    elif score >= 0.35:
        return f"La imagen es parcialmente coherente con el título (similitud semántica: {score})"
    else:
        return f"La imagen no parece estar relacionada con el contenido del título (similitud semántica: {score})"
    
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
        "NEU": "neutro"
    }
    sent_texto = mapa.get(sentimiento, sentimiento)

    if sentimiento == "NEG":
        return f"El análisis de sentimientos es {sent_texto} (puntuación: {round(punt, 2)}). El tono negativo es habitual en noticias sobre eventos adversos y no implica por sí solo desinformación"
        
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
        return f"Se detecta una emoción, concretamente '{emocion}', indicando un tono poco objetivo"
    if emocion.lower() in {"others", "other", "neutral"}:
        return f"La emoción predominante es neutra o mixta, sin indicar alarmismo"
    
    return f"Se ha detectado una emoción en el texto, '{emocion}'"

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
def _construir_prompt(resultado_imagen: dict, resultado_texto: dict, titulo: str, lang: str = "es", prob_falsa: float = 0.5) -> str:
    # Imagen
    ela = _interpretar_ela(resultado_imagen.get("ela_score", -1.0))
    ia = _interpretar_ia(resultado_imagen.get("es_ia", False), resultado_imagen.get("confianza_ia", -1.0))
    coherencia = _interpretar_coherencia(resultado_imagen.get("clip_score", -1.0))
    exif = _interpretar_exif(resultado_imagen.get("fuera_contexto", False), resultado_imagen.get("metadatos", {}))
    estatus_img = _interpretar_estatus_imagen(resultado_imagen.get("estatus", "autentica"))

    # Texto
    sentimiento = _interpretar_sentimiento(resultado_texto.get("sentimiento", "NEU"), resultado_texto.get("punt_sentimiento", 0.0))
    objetividad = _interpretar_objetividad(resultado_texto.get("punt_objetividad", -1.0))
    emocion = _interpretar_emocion(resultado_texto.get("emocion", "-"))
    indicadores = _interpretar_indicadores(resultado_texto.get("indicadores", []))
    dist = abs(prob_falsa - 0.5)
    confianza_es = "Alta" if dist >= 0.3 else "Media" if dist >= 0.15 else "Baja"
    confianza_en = "High" if dist >= 0.3 else "Medium" if dist >= 0.15 else "Low"


    if lang == "en":
        prompt = f"""You are an expert system in disinformation and fake news detection.
        Your task is to generate a clear, detailed explanation in English about the analysis performed on the following news article.

        News title: "{titulo}"
        Model fake probability: {round(prob_falsa*100, 1)}% (a low probability means the model considers the article TRUE; a high probability means FAKE)
        Model verdict: {"FAKE" if prob_falsa >= 0.6 else "TRUE" if prob_falsa <= 0.4 else "UNDETERMINED"}
        Model confidence: {confianza_en}

        Image analysis: 
        {ela}
        {ia}
        {coherencia}
        {exif}
        Final image classification: {estatus_img}

        Text analysis:
        {sentimiento}
        {objetividad}
        {emocion}
        {indicadores}

        IMPORTANT: Your entire response must be in English. All section headers MUST be written in English.
        Format each section header with double asterisks exactly like this: **General verdict**, **Image analysis**, **Text analysis**, **Final classification**, **Confidence level**. Do not use any other header format such as "Header:" or "# Header".

        Instructions:
        Generate a complete automatic explanation in English that does the following things:
        1. **General verdict** : Summarise in one sentence the general verdict on the news article (Do not conduct your own fact-checking, base your verdict solely on the model's classification).
        2. **Image analysis** : Explain in detail what each image analysis metric indicates and why it is relevant for detecting disinformation.
        3. **Text analysis** : Explain in detail what each text analysis metric indicates and how it contributes to the final verdict.
        4. **Final classification** : Evaluate whether the model's fake probability seems coherent with the analysed indicators and explain clearly, 
            and justify the final classification coherently with all the above data.
        5. **Confidence level** : The model confidence level is {confianza_en}. Confidence reflects how far the probability is from 50%: the closer to 0%, the more certain the model is that
            the article is TRUE; the closer to 100%, the more certain it is FAKE. Between 40% and 60% the result is undetermined, leaning towards TRUE if below 50% and towards FAKE if above.

        Be clear and accessible for a non-technical user. Write each section as a paragraph, not bullet points
        Do not invent additional data nor ramble, if a metric indicates it could not be analysed or has a negative value,
        mention it as limitation of the analysis performed. Don't use your world knowledge to verify whether the news is false or true,
        your task is simply to explain what the text and image indicators show, and the verdict is determined by the model, not you.
        Do not use bold markdown (**text**) within paragraphs to highlight values, only use it for section headers.
        """
    else:
        prompt = f"""Eres un sistema experto en detección de desinformación y fake news.
        Tu tarea es generar una explicación clara, detallada y en español sobre el análisis realizado a la siguiente noticia.

        Título de la noticia: "{titulo}"
        Probabilidad del modelo para asignarla como falsa: {round(prob_falsa*100, 1)}%
        Veredicto del modelo: {"FALSA" if prob_falsa >= 0.6 else "VERDADERA" if prob_falsa <= 0.4 else "INDETERMINADA"}
        Nivel de confianza del modelo: {confianza_es}

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

        IMPORTANTE: Escribe cada título de sección con dobles asteriscos exactamente así: **Veredicto general**, **Análisis de la imagen**, **Análisis del texto**, **Clasificación final**, 
        **Nivel de confianza**. No uses ningún otro formato de título como "Título:" o "# Título".

        Instrucciones:
        Genera una explicación automática completa en español que haga las siguientes cosas:
        1. Resuma en una frase el veredicto general de la noticia (no realices verificación de hechos propia, basa el veredicto exclusivamente en la clasificación del modelo).
        2. Explique de forma detallada qué indica cada métrica del análisis de imagen y por qué es relevante para detectar desinformación.
        3. Explique de forma detallada qué indica cada métrica del análisis de texto y cómo contribuye al veredicto final.
        4.  Evalúa si la probabilidad del modelo es coherente con los indicadores analizados y explícalo con claridad y justifique 
            la clasificación final de forma coherente con todos los datos anteriores.
        5. Indique el nivel de confianza del análisis como {confianza_es}. La confianza refleja cuánto se aleja la probabilidad del 50%: cuanto más cercana a 0%, más seguro
            es el modelo de que la noticia es VERDADERA; cuanto más cercana a 100%, más seguro es de que es FALSA. Entre el 40% y el 60% el resultado es indeterminado, con
            tendencia a verdadera si está por debajo del 50% y a falsa si está por encima.


        Sé claro, preciso y accesible para un usuario no técnico. No uses listas con viñetas, redacta en párrafos.
        No inventes datos adicionales ni desvaríes, si una métrica indica que no se ha podido analizar o tiene un valor negativo,
        menciónalo como una limitación del análisis realizado. No uses tu conocimiento del mundo para verificar si la noticia es falsa o verdadera,
        tu tarea es solo explicar qué indican los indicadores de texto e imagen, y el veredicto lo determina el modelo, no tú.
        No uses formato markdown en negrita (**texto**) dentro de los párrafos para resaltar valores, solo úsalo para los títulos de cada sección.
        """

    return prompt

# Llamada a Ollama para generar la explicación automática en lenguaje natural
def generar_explicacion(resultado_imagen: dict, resultado_texto: dict, titulo: str = "", lang: str = "es", prob_falsa = 0.5) -> str:
    prompt = _construir_prompt(resultado_imagen, resultado_texto, titulo, lang, prob_falsa)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 1024},
                "keep_alive": "5m"
            },
            timeout=180
        )
        logger.debug(f"STATUS OLLAMA: {response.status_code}")
        response.raise_for_status()
        return response.json().get("response", "No se ha podido generar la explicación")
    
    except requests.exceptions.ConnectionError as e:
        logger.error("Ollama no está ejecutándose")
        return (f"Debug error Ollama: {type(e).__name__} - {e}")
    # return "El servicio de explicación no está disponible, no funciona"
    
    except requests.exceptions.Timeout as e:
        logger.error(f" Timeout: {e}")
        return "Timeout"
    
    except Exception as e:
        logger.error(f"Error generando la explicación automática: {e}")
        return "No se ha podido generar la explicación"
