# from pydantic import BaseModel, Field
# Sirve para crear los modelos
import enum
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, TEXT
import sqlalchemy as sa
from typing import Optional

"""""
class New(BaseModel):
    id: int
    #Para añadir más validaciones, con Field
    title: str = Field(default= "Nueva noticia", min_length=5, max_length= 150)
    subtitle: str
    description: str 
    category: str
    source: str

"""
# Son modelos de Pydantic
# A LO MEJOR A LA LARGA SE AÑADEN MÁS COSAS

# ENUMERADOS
# Enumerado para etiqueta (y resultado también)
class EtiquetaEnum(str, enum.Enum):
    pendiente = "pendiente"
    verdadera = "verdadera"
    falsa = "falsa"

# Enumerado para el estatus de la imagen analizada
class ImagenEnum(str, enum.Enum):
    pendiente = "pendiente"
    autentica = "autentica"
    fuera_contexto = "fuera_contexto"
    generada_ia = "generada_ia"

class FuenteBase(SQLModel):
    nombre: str
    url: str = Field(unique=True, index=True) # URL de la pág web (que no se repiten)
    idioma: str # Español o inglés

class Fuente(FuenteBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

class FuentePublic(FuenteBase):
    id: int

class FuenteCreate(FuenteBase):
    pass

class NoticiaBase(SQLModel):
    #Para añadir más validaciones, con Field
    titulo: str = Field(min_length=10)
    # subtitle: str | None = None
    descripcion: str = Field(sa_column=Column(TEXT))
    categoria: str | None = None              # None si la noticia está pendiente
    # source: str
    fecha_publi: datetime | None = None       # Fecha publicación
    texto_url: str = Field(unique=True, index=True) # URL de la pág web (que no se repiten)
    imagen_url: str | None = None             # Para las imágenes
    etiqueta: EtiquetaEnum = Field(default=EtiquetaEnum.pendiente) # Pendiente por defecto, si no se clasifica en V o F
    fuente_id: int | None = Field(default=None, foreign_key="fuente.id") # FK a Fuente para ligar una noticia a su fuente

# La tabla que SQLModel usará en la BD
class Noticia(NoticiaBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

class NoticiaPublic(NoticiaBase):
    id: int

class NoticiaCreate(NoticiaBase):
    # Se almacenan el nombre de la fuente y el idioma como datos de entrada (no como columnas iniciales en la BD)
    fuente_nombre: str | None = None
    lang: str | None = "es" # por defecto en español

# Como se ha eliminado el Update de la API, de momento esto se deja comentado
"""
class NewUpdate(NewBase):
    title: str | None = None
    subtitle: str | None = None
    description: str | None = None
    category: str | None = None
    source: str | None = None
"""

class ValoracionBase(SQLModel): #Cambio de BaseModel a SQLModel
    noticia_id: int | None = Field(default=None, foreign_key="noticia.id") # FK a noticia para ligarla a su valoracion
    # title: str
    # category: str
    resultado: EtiquetaEnum = Field(default=EtiquetaEnum.pendiente)
    probabilidad: float = Field(default=0.50, ge= 0.00, le= 1.00)
    explicacion: str | None = Field(default=None, sa_column=Column(sa.Text))           # Justificación (NLP/LLM)
    punt_sentimiento: float | None = None     # Análisis de sentimientos (tono neutro, positivo o negativo)
    punt_objetividad: float | None = None     # Análisis de objetividad (imparcial o no)
    estatus_analisis_imagen: ImagenEnum = Field(default=ImagenEnum.pendiente) # Etiqueta para saber si es fiable, manipulada o creada artificialmente

class Valoracion(ValoracionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    fecha_analisis: datetime = Field(default_factory=datetime.now)

class ValoracionPublic(ValoracionBase):
    id: int
    fecha_analisis: datetime 

class AnalisisResultado(SQLModel):
    noticia: NoticiaPublic
    valoracion: ValoracionPublic
    fuente_nombre: str | None = None # Evita una segunda llamada a GET /fuentes/{id}
