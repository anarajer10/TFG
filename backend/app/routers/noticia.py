from typing import Annotated
import logging
from fastapi import APIRouter, Path, Depends, HTTPException, Query
from sqlmodel import Session, select
from urllib.parse import urlparse
from newspaper import Article # para newspaper4k
from app.models.schema import Fuente, Noticia, NoticiaCreate, NoticiaPublic, ValoracionPublic, AnalisisResultado # de schema.py, para tener acceso a los modelos
from app.database import get_session
from app.services.analisis_modulos import procesar_analisis_noticia

router = APIRouter()
logger = logging.getLogger(__name__)

# Así se extrae la url del medio (no la del artículo en concreto)
def _dominio_fuente(url: str) -> str:
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}" if p.netloc else url
    except Exception:
        return url

# Para ver una lista de noticias
@router.get("/noticias", response_model=list[NoticiaPublic])
def get_noticias(
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    noticias = session.exec(select(Noticia).offset(offset).limit(limit)).all()
    return noticias

# Pra ver una noticia dado su id
@router.get("/noticias/{id}", response_model=NoticiaPublic)
def get_noticia(id: int = Path(gt=0), session: Session = Depends(get_session)):
    noticia = session.get(Noticia, id)
    if not noticia:
        raise HTTPException(status_code=404, detail="Noticia no encontrada")
    return noticia

# Análisis de la noticia introducida
@router.post("/analizar", response_model=AnalisisResultado)
def analizar_noticia(noticia: NoticiaCreate, session: Session = Depends(get_session)):
    # Primero se obtiene la fuente de una noticia
    fuente = None
    if noticia.fuente_nombre:
        fuente = session.exec(
            select(Fuente).where(Fuente.nombre == noticia.fuente_nombre)
        ).first()   # Reutiliza la fuente si ya existe en la BD
        if not fuente:
            fuente_url = (
                _dominio_fuente(noticia.texto_url)
                if noticia.texto_url and not noticia.texto_url.startswith("https://sin-url")
                else f"fuente://{noticia.fuente_nombre.lower().replace(' ', '-')}"
            )
            fuente = Fuente(nombre=noticia.fuente_nombre, url=fuente_url, idioma="es")
            session.add(fuente)
            session.commit()
            session.refresh(fuente)
    
    # Hay que excluir fuente_nombre porque no existe como columna en Noticia al crear el objeto en la BD
    datos = noticia.model_dump(exclude={"fuente_nombre"}) 
    datos["fuente_id"] = fuente.id if fuente else None
    db_noticia = Noticia(**datos)
    session.add(db_noticia)
    session.commit()
    session.refresh(db_noticia)

    valoracion = procesar_analisis_noticia(session, db_noticia.id)
    if not valoracion:
        raise HTTPException(status_code=500, detail="Error al analizar la noticia dada.")
    
    return AnalisisResultado(
        noticia=NoticiaPublic.model_validate(db_noticia),
        valoracion=ValoracionPublic.model_validate(valoracion),
        fuente_nombre=fuente.nombre if fuente else None
    )

# Extrae los datos de una url externa (la pasada por el usuario)
@router.get("/extraer")
def extraer_url(url: str):
    try:
        article = Article(url)
        article.download()
        article.parse()

        return{
            "titulo":       article.title or "",
            "descripcion":  article.text[:3000] if article.text else "",
            "imagen_url":    article.top_image or None,
            "fecha_publi":  article.publish_date.isoformat() if article.publish_date else None,
            "fuente_nombre":_dominio_fuente(url),
            "texto_url":    url,
        }
    
    except Exception as e:
        logger.error(f"Error extrayendo la url: {e}")
        raise HTTPException(status_code=422, detail=f"No se ha podido extraer la noticia: {e}")