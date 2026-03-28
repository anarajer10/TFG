import logging
from sqlmodel import Session
from app.models.schema import Noticia, Valoracion, EtiquetaEnum, ImagenEnum
from app.modules.analisis_texto import analizar_texto
from app.modules.analisis_imagen import analizar_imagen
from datetime import datetime

logger = logging.getLogger(__name__)

# Orquestador
def procesar_analisis_noticia(session: Session, noticia_id: int):

    noticia = session.get(Noticia, noticia_id)
    if not noticia:
        logger.error(f"Noticia {noticia_id} no encontrada")
        return None
    
    try:
        logger.info("Análisis {noticia.titulo[:50]}")

        # análisis texto
        texto_completo = f"{noticia.titulo}. {noticia.descripcion}"
        resultado_texto = analizar_texto(texto_completo, titulo=noticia.titulo, lang="es")

        # análisis imagen
        resultado_imagen = None
        if noticia.imagen_url:
            resultado_imagen = analizar_imagen(noticia.imagen_url, fecha_publi=noticia.fecha_publi, titulo=noticia.titulo)

        # Valoración final
        val = EtiquetaEnum.verdadera

        if resultado_texto["punt_objetividad"] < 0.45:
            val = EtiquetaEnum.falsa
        elif resultado_imagen and resultado_imagen["estatus"] != ImagenEnum.autentica:
            val = EtiquetaEnum.falsa

        prob_final = resultado_texto["prob_sentimiento"].get(resultado_texto["sentimiento"], 0.5)

        nueva_val = Valoracion(
            noticia_id=noticia.id,
            resultado=val,
            probabilidad=float(prob_final),
            # Falta añadir lo del LLM
            explicacion=f"emocion: {resultado_texto['emocion']}. Indicadores: {', '.join(resultado_texto['indicadores'])}",
            punt_sentimiento=resultado_texto["punt_sentimiento"],
            punt_objetividad=resultado_texto["punt_objetividad"],
            estatus_analisis_imagen=resultado_imagen["estatus"] if resultado_imagen else ImagenEnum.pendiente,
            fecha_analisis=datetime.now()
        )

        noticia.etiqueta = val

        session.add(nueva_val)
        session.add(noticia)
        session.commit()

        logger.info(f"Resultado: {val}")

        return nueva_val

    except Exception as e:
        session.rollback()
        logger.error(f"Error en el proceso de análisis de una noticia: {e}")
        return None
