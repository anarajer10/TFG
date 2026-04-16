import re
import logging
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DDG_URL = "https://duckduckgo.com/"
DDG_IMG_URL = "https://duckduckgo.com/i.js"
MAX_PALABRAS = 8    # Número palabras del título como consulta
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": "https://duckduckgo.com/"
}

# Extrae el dominio raíz de una url, sin el www
def _dominio(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return ""
    
# Para extraer las palabras del título para la consulta
def _recortar_titulo(titulo: str) -> str:
    return " ".join(titulo.strip().split()[:MAX_PALABRAS])

# Uso de la API para la búsqueda
def _busqueda_duckduckgo(titulo: str) -> list[dict]:
    query = _recortar_titulo(titulo)

    try:
        respuesta = requests.get(
            DDG_URL,
            params={"q": query, "iax": "images", "ia": "images"},
            headers=HEADERS,
            timeout=15,
        )

        respuesta.raise_for_status()

        match = re.search(r'vqd=["\']?([\d-]+)["\']?', respuesta.text)
        if not match:
            logger.error("No se encontró el token vdq de DuckDuckGo")
            return []
        vqd = match.group(1)

    except Exception as e:
        logger.error(f"Error obteniendo el token de DuckDuckGo: {e}")
        return []
    
    try:
        params = {
            "l": "es-es",
            "o": "json",
            "q": query,
            "vqd": vqd,
            "f": ",,,,,",
            "p": "1",
        }
        headers_img = {
            "User-Agent": HEADERS["User-Agent"],
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": HEADERS["Accept-Language"],
            "Referer": f"https://duckduckgo.com/?q={query.replace(' ', '+')}&iax=images&ia=images",
            "X-Requested-With": "XMLHttpRequest",
        }
        respuesta = requests.get(
            DDG_IMG_URL,
            params=params,
            headers=headers_img,
            timeout=15,
        )
        respuesta.raise_for_status()
        return respuesta.json().get("results", [])
    
    except Exception as e:
        logger.error(f"Error obteniendo imágenes de DuckDuckGo: {e}")
        return []


# Verifica si la imagen es coherente con el título de la noticia buscando imágenes similares en Google Images
def analizar_coherencia_imagen(imagen_url: str, titulo: str) -> float:
    if not titulo or not titulo.strip():
        logger.warning("Título vacío, no se puede analizar coherencia")
        return -1.0
    
    if not imagen_url or not imagen_url.strip():
        logger.warning("URL de imagen vacía, no se puede analizar coherencia")
        return -1.0
    
    items = _busqueda_duckduckgo(titulo)
    # print("DOMINIOS DDG:", {_dominio(item.get("url", "") or item.get("image", "")) for item in items[:5]})
    # print("DOMINIO IMAGEN:", _dominio(imagen_url))
    # print("URLS IMAGEN:", [item.get("image", "")[:60] for item in items[:3]])

    if not items: # Sin resultados
        return -1.0
    
    dominio_imagen = _dominio(imagen_url)
     
    # Se extraen las urls y dominios de los resultados de DuckDuckGo
    urls_fuente = [item.get("url", "") for item in items]
    dominios = {_dominio(item.get("url", "")) for item in items}

    # La url exacta de la imagen aparece en los resultados
    if imagen_url in urls_fuente:
        logger.info(f"URL exacta encontrada para: {titulo:50}")
        return 1.0
    
     # El dominio de la imagen está entre los resultados
    if dominio_imagen and dominio_imagen in dominios:
        logger.info(f"Dominio '{dominio_imagen} presente en los resultados")
        return 0.75
    
     # Sin relación encontrada
    logger.info(f"Sin coherencia detectada para: {titulo:50}")
    return 0.25

    

