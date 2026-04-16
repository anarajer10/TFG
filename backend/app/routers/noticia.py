from typing import Annotated
from fastapi import APIRouter, Path, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.models.schema import Noticia, NoticiaCreate, NoticiaPublic, ValoracionPublic # de schema.py, para tener acceso a los modelos
from app.database import get_session
from app.services.analisis_modulos import procesar_analisis_noticia

router = APIRouter()

""" 
# Noticias de prueba
news = [
    {
        "id": 1,
        "title": "Noticia 1",
        "subtitle": "Subtítulo de la noticia 1",
        "description": "blablabla",
        "category": "Política",
        "source": "ElPais"
    },
    {
        "id": 2,
        "title": "Noticia 2",
        "subtitle": "Subtítulo de la noticia 2",
        "description": "blablable",
        "category": "Prensa rosa",
        "source": "HOLA"
    }
]
"""

# CRUD (Create, Read, Update, Delete)

# CORREGIDO --> Cambia el CRUD (eliminados Update y Delete, modificado Create (POST) 
# para analizar las noticias)

@router.get("/noticias", response_model=list[NoticiaPublic])
def get_noticias(
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    noticias = session.exec(select(Noticia).offset(offset).limit(limit)).all()
    return noticias

@router.get("/noticias/{id}")
def get_noticia(id: int = Path(gt=0), session: Session = Depends(get_session)):
    noticia = session.get(Noticia, id)
    if not noticia:
        raise HTTPException(status_code=404, detail="Noticia no encontrada")
    return noticia

@router.post("/analizar", response_model=ValoracionPublic)
# MODIFICAR MÁS ADELANTE
def analizar_noticia(noticia: NoticiaCreate, session: Session = Depends(get_session)):
    db_noticia = Noticia.model_validate(noticia)
    session.add(db_noticia)
    session.commit()
    session.refresh(db_noticia)

    valoracion = procesar_analisis_noticia(session, db_noticia.id)
    if not valoracion:
        raise HTTPException(status_code=500, detail="Error al analizar la noticia dada.")
    
    return valoracion
""""
# put es cuando se quiere actualizar todo por completo, patch es para algo en concreto
@router.patch("/news/{id}", response_model=NewPublic)
def update_new(id: int, new: NewUpdate, session: Session = Depends(get_session)):
    db_new = session.get(New, id)
    if not db_new:
        raise HTTPException(status_code=404, detail="Noticia no encontrada")
    
    new_data = new.model_dump(exclude_unset=True)
    db_new.sqlmodel_update(new_data)
    
    session.add(db_new)
    session.commit()
    session.refresh(db_new)
    return db_new

@router.delete("/news/{id}")
def delete_new(id: int, session: Session = Depends(get_session)):
    new = session.get(New, id)
    if not new:
        raise HTTPException(status_code=404, detail="Noticia no existente")
    
    session.delete(new)
    session.commit()
    return {"msg": "Noticia eliminada"}

"""