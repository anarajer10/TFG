import math
import numpy as np
import os
import io
from urllib.parse import urlparse
import requests
import logging
from datetime import datetime
from PIL import Image, ImageChops, ImageEnhance
from dotenv import load_dotenv
from app.models.schema import ImagenEnum
from PIL.ExifTags import TAGS
from sentence_transformers import SentenceTransformer, util  # type: ignore

load_dotenv()

logger = logging.getLogger(__name__)

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_MODEL_URL = "https://router.huggingface.co/hf-inference/models/Nahrawy/AIorNot"

ELA_QUALITY = 90
ELA_THRESHOLD = 15      # Umbral para considerar la manipulación de una imagen
AI_THRESHOLD = 0.80     # Umbral de confianza para considerar a una imagen como hecha por IA
DIAS_CONTEXTO = 180     # Días de diferencia máxima entre fecha de los metadatos y fecha de la noticia
CLIP_THRESHOLD = 0.35   # Por debajo de este valor, la imagen no es coherente con el título

_clip_model = None

def _cargar_clip() -> SentenceTransformer:
    global _clip_model
    if _clip_model is None:
        _clip_model = SentenceTransformer("clip-ViT-B-32-multilingual-v1")
    return _clip_model

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
                if tag in ["DateTime", "Make", "Model", "Software", "GPSInfo"]:
                    metadatos[tag] = str(valor)

    except Exception as e:
        logger.warning(f"Error extrayendo EXIF: {e}")  

    return metadatos


# Análisis ELA (manipulación imagen, diferencia de píxeles)
# Con una media alta y std alta, es más sospechoso, hay una manipulación localizada
# con una media alta pero std baja, es menos sospechoso
def analizar_ela(imagen_bytes: bytes) -> tuple[float, float]:
    try:   
        imagen_orig = Image.open(io.BytesIO(imagen_bytes)).convert("RGB")

        buffer = io.BytesIO()
        imagen_orig.save(buffer, format="JPEG", quality=ELA_QUALITY)
        buffer.seek(0)
        imagen_recomprimida = Image.open(buffer).convert("RGB")

        diferencia = ImageChops.difference(imagen_orig, imagen_recomprimida)
        diferencia_amplificada = ImageEnhance.Brightness(diferencia).enhance(10)

        pixels = list(diferencia_amplificada.getdata())
        valores = [sum(p) / 3 for p in pixels]
        media = sum(valores) /len(valores)
        std = math.sqrt(sum((v-media)**2 for v in valores)/len(valores))

        return round(media, 4), round(std, 4)

    except Exception as e:
        logger.error(f"Error en el análisis ELA: {e}")
        return -1.0, -1.0
    

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

# Detecta si el EXIF menciona algún software de edición
def _software_edicion(metadatos: dict) -> bool:
    software = metadatos.get("Software", "").lower()
    editores = ["photoshop", "gimp", "adobe", "lightroom", "affinity"]
    return any(e in software for e in editores)

# Comprueba si el dominio de la imagen coincide con el del artículo
# por ej si viene de un dominio distinto puede ser una imagen stock fuera de contexto
def _comprobar_dominio(imagen_url: str, texto_url: str) -> bool:
    if not texto_url:
        return True # que no penalice si no se tiene la url del articulo
    try:
        dom_imagen = urlparse(imagen_url).netloc.lower().replace("www.", "")
        dom_articulo = urlparse(texto_url).netloc.lower().replace("www.", "")
        return dom_imagen == dom_articulo or dom_imagen in dom_articulo or dom_articulo in dom_imagen
    except Exception:
        return True
    
# Detecta si la imagen es demasiado pequeña (como una captura d pantalla, por ej)
def _imagen_pequena(metadatos: dict) -> bool:
    dims = metadatos.get("dimensiones")
    if not dims:
        return False
    return dims[0] < 200 or dims[1] < 200

# Similitud semántica imagen-título usando CLIP multilingüe
def calcular_similitud_clip(imagen_bytes: bytes, titulo: str) -> float:
    try: 
        model = _cargar_clip()
        imagen = Image.open(io.BytesIO(imagen_bytes)).convert("RGB")
        imagen_emb = model.encode(np.array(imagen), convert_to_tensor=True)
        texto_emb = model.encode(titulo[:100], convert_to_tensor=True)
        similitud = float(util.cos_sim(imagen_emb, texto_emb)[0][0])
        return round((similitud+1)/2, 4) # para normalizar de [-1,1] a [0,1]
    except Exception as e:
        logger.error(f"Error en CLIP: {e}")
        return -1.0
    

def analizar_imagen(imagen_url: str, fecha_publi: datetime | None = None, titulo: str = "", texto_url: str = "") -> dict:

    resultado = {
        "estatus": ImagenEnum.autentica,
        "ela_score": -1.0,
        "ela_std": -1.0,
        "es_ia": False,
        "confianza_ia": -1.0,
        "fuera_contexto": False,
        "ela_manipulada": False,
        "software_edicion": False,
        "dominio_coincide": True,
        "imagen_pequena": False,
        "clip_score": -1.0,
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
    ela_score, ela_std = analizar_ela(imagen_bytes)
    resultado["ela_score"] = ela_score
    resultado["ela_std"] = ela_std

    # Detección de IA
    es_ia, confianza_ia = detectar_ia(imagen_bytes)
    resultado["es_ia"] = es_ia 
    resultado["confianza_ia"] = confianza_ia 
    
    # fuera contexto por fecha
    fuera_contexto = detectar_fuera_contexto(resultado["metadatos"], fecha_publi)
    resultado["fuera_contexto"] = fuera_contexto

    resultado["software_edicion"] = _software_edicion(resultado["metadatos"])
    resultado["dominio_coincide"] = _comprobar_dominio(imagen_url, texto_url)
    resultado["imagen_pequena"] = _imagen_pequena(resultado["metadatos"])

    # Similitud CLIP imagen-título
    if titulo:
        resultado["clip_score"] = calcular_similitud_clip(imagen_bytes, titulo)

    # Señales de manipulación ELA
    ela_alta = ela_score != -1.0 and ela_score > ELA_THRESHOLD
    ela_localizada = ela_alta and ela_std != -1.0 and ela_std > ELA_THRESHOLD * 0.5
    resultado["ela_manipulada"] = ela_alta

    clip_incoherente = resultado["clip_score"] != -1.0 and resultado["clip_score"] < CLIP_THRESHOLD

    # clasificación final
    if es_ia:
        resultado["estatus"] = ImagenEnum.generada_ia
    elif fuera_contexto or ela_localizada or resultado["software_edicion"] or not resultado["dominio_coincide"] or clip_incoherente:
        resultado["estatus"] = ImagenEnum.fuera_contexto
        resultado["fuera_contexto"] = True
    elif ela_alta:
        resultado["estatus"] = ImagenEnum.fuera_contexto
        resultado["fuera_contexto"] = True
    else:
        resultado["estatus"] = ImagenEnum.autentica

    return resultado