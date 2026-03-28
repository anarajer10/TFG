import os
import io
import base64
import requests
import logging
from datetime import datetime, timezone
from PIL import Image, ImageChops, ImageEnhance
from dotenv import load_dotenv
from app.models.schema import ImagenEnum
from PIL.ExifTags import TAGS

load_dotenv()

logger = logging.getLogger(__name__)

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_MODEL_URL = "https://router.huggingface.co/hf-inference/models/Nahrawy/AIorNot"
CLIP_MODEL_URL = "https://router.huggingface.co/fal-ai/models/openai/clip-vit-large-patch14-336"

ELA_QUALITY = 90
ELA_THRESHOLD = 15      # Umbral para considerar la manipulación de una imagen
AI_THRESHOLD = 0.80     # Umbral de confianza para considerar a una imagen como hecha por IA
CLIP_THRESHOLD = 0.20   # Umbral mínimo de similitud entre imagen y texto
DIAS_CONTEXTO = 180     # Días de diferencia máxima entre fecha de los metadatos y fecha de la noticia

# Con la url, descraga la imagen y devuelve sus bytes
def descargar_imagen(url: str) -> bytes | None:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # En caso de que haya error, para que devuelva el mensaje
        content_type = response.headers.get("Content-Type", "")

        magic_numbers = [
            b'\xff\xd8\xff',    # jpeg
            b'\x89PNG',         # png
            b'GIF8',            # gif
            b'RIFF',            # webp
        ]

        es_imagen = any(t in content_type for t in ["image/", "application/octet-stream"])
        es_imagen_por_bytes = any(response.content.startswith(m) for m in magic_numbers)
        
        if not es_imagen and not es_imagen_por_bytes:
            logger.warning(f"La url no es una imagen válida: {content_type}")
            return None
        
        return response.content
    
    except Exception as e:
        logger.error(f"Error descargando la imagen {url}: {e}")
        return None
    
# Para extraer metadatos EXIF de una imagen (QUITAR??)
def extraer_metadatos_exif(imagen_bytes: bytes) -> dict:
    metadatos = {}
    try:
        imagen = Image.open(io.BytesIO(imagen_bytes))
        metadatos["formato"] = imagen.format
        metadatos["modo"] = imagen.mode
        metadatos["dimensiones"] = imagen.size

        exif_datos = imagen.getexif()
        if exif_datos:
            for tag_id, valor in exif_datos.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag in ["Datetime", "Make", "Model", "Software", "GPSInfo"]:
                    metadatos[tag] = str(valor)

    except Exception as e:
        logger.warning(f"Error extrayendo EXIF: {e}")  

    return metadatos


# Análisis ELA (manipulación imagen, diferencia de píxeles)
def analizar_ela(imagen_bytes: bytes) -> float:
    try:   
        imagen_orig = Image.open(io.BytesIO(imagen_bytes)).convert("RGB")

        buffer = io.BytesIO()
        imagen_orig.save(buffer, format="JPEG", quality=ELA_QUALITY)
        buffer.seek(0)
        imagen_recomprimida = Image.open(buffer).convert("RGB")

        diferencia = ImageChops.difference(imagen_orig, imagen_recomprimida)
        diferencia_amplificada = ImageEnhance.Brightness(diferencia).enhance(10)

        pixels = list(diferencia_amplificada.getdata())
        media = sum(sum(p) / 3 for p in pixels) /len(pixels)

        return round(media, 4)

    except Exception as e:
        logger.error(f"Error en el análisis ELA: {e}")
        return -1.0
    

# Detección de IA (con HuggingFace)
def detectar_ia(imagen_bytes: bytes) -> tuple[bool, float]:
    try:
        imagen = Image.open(io.BytesIO(imagen_bytes)).convert("RGB")
        imagen.thumbnail((512, 512), Image.LANCZOS)

        buffer = io.BytesIO()
        imagen.save(buffer, format="JPEG", quality=95)
        jpeg_bytes = buffer.getvalue()

        response = requests.post(
            HF_MODEL_URL,
            headers={
                "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
                "Content-Type": "image/jpeg",
                "Accept-Encoding": "identity",
            },
            data=jpeg_bytes,
            timeout=30,
            stream=False
        )
        response.raise_for_status()

        resultados = response.json()
        for resultado in resultados:
            if resultado["label"].lower() == "ai":
                confianza = resultado["score"]
                return confianza >= AI_THRESHOLD, confianza
            
        return False, -1.0

    except Exception as e:
        logger.error(f"Error en la detección de IA: {e}")
        return False, -1.0


# analizar la coherencia entre el texto y su imagen asociada
def analizar_clip(imagen_bytes: bytes, texto) -> float:
    if not texto or not texto.strip():
        return -1.0
    
    try:
        imagen_b64 = base64.b64encode(imagen_bytes).decode("utf-8")

        payload = {
            "inputs": imagen_b64,
            "parameters": {
                "candidate_labels": [texto, "otra cosa aleatoria"]
            }
        }

        response = requests.post(
            CLIP_MODEL_URL,
            headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        resultado = response.json()

        if isinstance(resultado, list):
            for item in resultado:
                if item["label"] == texto:
                    return round(float(item["score"]), 4)
        elif isinstance(resultado, dict) and "scores" in resultado:
            return round(float(resultado["scores"][0]), 4)

        return -1.0

    except Exception as e:
        logger.error(f"Error en el análisis CLIP: {e}")
        return -1.0  

# QUITAR?
# Análisis de metadatos EXIF para averoguar si la foto está fuera de contexto
def detectar_fuera_contexto(metadatos: dict, fecha_publi: datetime | None) -> bool:
    if not fecha_publi or "DateTime" not in metadatos:
        return False
    
    try:
        fecha_exif = datetime.strptime(metadatos["DateTime"], "%Y:%m:%d %H:%M:%S")

        # Normalización de las zonas horarias
        if fecha_publi.tzinfo is not None:
            fecha_publi = fecha_publi.replace(tzinfo=None)

        diferencia = (fecha_publi - fecha_exif).days
        return diferencia > DIAS_CONTEXTO
    
    except Exception as e:
        logger.warning(f"Error comparando las fechas: {e}")
        return False
    

def analizar_imagen(imagen_url: str, fecha_publi: datetime | None = None, titulo: str = "") -> dict:

    resultado = {
        "estatus": ImagenEnum.autentica,
        "ela_score": -1.0,
        "es_ia": -1.0,
        "confianza_ia": -1.0,
        "clip_score": -1.0,
        "fuera_contexto": False,
        "metadatos": {}
    }

    if not imagen_url:
        return resultado
    
    # primero se descarga la imagen
    imagen_bytes = descargar_imagen(imagen_url)
    if not imagen_bytes:
        return resultado
    
    # metadatos EXIF
    resultado["metadatos"] = extraer_metadatos_exif(imagen_bytes)

    # análisis ELA
    ela_score = analizar_ela(imagen_bytes)
    resultado["ela_score"] = ela_score

    # Detección de IA
    es_ia, confianza_ia = detectar_ia(imagen_bytes)
    resultado["es_ia"] = es_ia 
    resultado["confianza_ia"] = confianza_ia 

    # análisis CLIP
    clip_score = analizar_clip(imagen_bytes, titulo)
    resultado["clip_score"] = clip_score
    clip_incoherencia = clip_score != -1.0 and clip_score < CLIP_THRESHOLD

    # fuera contexto por fecha
    fuera_contexto = detectar_fuera_contexto(resultado["metadatos"], fecha_publi)
    resultado["fuera_contexto"] = fuera_contexto

    # clasificación final
    if es_ia:
        resultado["estatus"] = ImagenEnum.generada_ia
    elif fuera_contexto or ela_score > ELA_THRESHOLD or clip_incoherencia:
        resultado["estatus"] = ImagenEnum.fuera_contexto
        resultado["fuera_contexto"] = True
    else:
        resultado["estatus"] = ImagenEnum.autentica

    return resultado