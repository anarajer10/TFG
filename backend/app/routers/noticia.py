# from typing import Annotated
import logging
import json
import os
from fastapi import APIRouter, Path, Depends, HTTPException, Query
from sqlmodel import Session, select
from urllib.parse import urlparse
from newspaper import Article # para newspaper4k
from app.models.schema import Fuente, Noticia, NoticiaCreate, NoticiaPublic, Valoracion, ValoracionPublic, AnalisisResultado # de schema.py, para tener acceso a los modelos
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
""""
@router.get("/noticias", response_model=list[NoticiaPublic])
def get_noticias(
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    noticias = session.exec(select(Noticia).offset(offset).limit(limit)).all()
    return noticias

"""

@router.get("/noticias/recientes", response_model=list[AnalisisResultado])
def get_noticias_recientes(
    limit: int = Query(default=20, le=50),
    lang: str | None = Query(default=None),
    session: Session = Depends(get_session)
):
    if lang:
        stmt = (
            select(Valoracion).join(Noticia, Valoracion.noticia_id == Noticia.id)
            .join(Fuente, Noticia.fuente_id == Fuente.id).where(Fuente.idioma == lang)
            .order_by(Valoracion.fecha_analisis.desc()).limit(limit)
        )
        valoraciones = session.exec(stmt).all()
    else:
        valoraciones = session.exec(
            select(Valoracion).order_by(Valoracion.fecha_analisis.desc()).limit(limit)
        ).all()

    resultado = []
    seen_ids = set()
    for v in valoraciones:
        if v.noticia_id in seen_ids:
            continue
        noticia = session.get(Noticia, v.noticia_id)
        if not noticia:
            continue
        seen_ids.add(v.noticia_id)
        fuente = session.get(Fuente, noticia.fuente_id) if noticia.fuente_id else None
        resultado.append(AnalisisResultado(
            noticia=NoticiaPublic.model_validate(noticia),
            valoracion=ValoracionPublic.model_validate(v),
            fuente_nombre=fuente.nombre if fuente else None
        ))
        if len(resultado) >= limit:
            break

    return resultado


# Pra ver una noticia dado su id
@router.get("/noticias/{id}", response_model=AnalisisResultado)
def get_noticia(id: int = Path(gt=0), session: Session = Depends(get_session)):
    noticia = session.get(Noticia, id)
    if not noticia:
        raise HTTPException(status_code=404, detail="Noticia no encontrada")
    valoracion = session.exec(
        select(Valoracion).where(Valoracion.noticia_id == id)
        .order_by(Valoracion.fecha_analisis.desc())
    ).first()
    if not valoracion:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    fuente = session.get(Fuente, noticia.fuente_id) if noticia.fuente_id else None
    return AnalisisResultado(
        noticia=NoticiaPublic.model_validate(noticia),
        valoracion=ValoracionPublic.model_validate(valoracion),
        fuente_nombre=fuente.nombre if fuente else None
    )

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
            fuente = Fuente(nombre=noticia.fuente_nombre, url=fuente_url, idioma=noticia.lang or "es")
            session.add(fuente)
            session.commit()
            session.refresh(fuente)
    
    # Hay que excluir fuente_nombre porque no existe como columna en Noticia al crear el objeto en la BD
    datos = noticia.model_dump(exclude={"fuente_nombre"}) 
    datos["fuente_id"] = fuente.id if fuente else None
    
    if datos.get("texto_url") and not datos["texto_url"].startswith("https://sin-url"):
        existing = session.exec(
            select(Noticia).where(Noticia.texto_url == datos["texto_url"])
        ).first()
        if existing:
            valoracion_existente = session.exec(
                select(Valoracion).where(Valoracion.noticia_id == existing.id)
                .order_by(Valoracion.fecha_analisis.desc())
            ).first()
            if valoracion_existente:
                return AnalisisResultado(
                    noticia=NoticiaPublic.model_validate(existing),
                    valoracion=ValoracionPublic.model_validate(valoracion_existente),
                    fuente_nombre=fuente.nombre if fuente else(
                        session.get(Fuente, existing.fuente_id).nombre
                        if existing.fuente_id else None
                    )
                )
            db_noticia = existing
            valoracion = procesar_analisis_noticia(session, db_noticia.id, lang=noticia.lang)
            if not valoracion:
                raise HTTPException(status_code=500, detail="Error al analizar la noticia dada")
            return AnalisisResultado(
                noticia=NoticiaPublic.model_validate(db_noticia),
                valoracion=ValoracionPublic.model_validate(valoracion),
                fuente_nombre=fuente.nombre if fuente else None
            )

    db_noticia = Noticia(**datos)
    session.add(db_noticia)
    session.commit()
    session.refresh(db_noticia)

    valoracion = procesar_analisis_noticia(session, db_noticia.id, lang=noticia.lang)
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
    
# Se obtienen las métricas de cada modelo
@router.get("/metricas")
def get_metricas():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    resultado = {}

    for lang in ("es", "en"):
        path = os.path.join(base, f"metricas_{lang}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                resultado[lang] = json.load(f)

    return resultado
