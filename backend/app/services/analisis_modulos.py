import logging
from sqlmodel import Session
from app.models.schema import Noticia, Valoracion, EtiquetaEnum, ImagenEnum
from app.modules.analisis_texto import analizar_texto
from app.modules.analisis_imagen import analizar_imagen
from app.modules.explicacion_XAI import generar_explicacion
from app.modules.prediccion import predecir
from datetime import datetime

logger = logging.getLogger(__name__)

# Ajusta la probabilidad del modelo con el análisis realizado de la imagen 
def _ajustar_con_imagen(prob_falsa: float, resultado_imagen: dict | None) -> float:
    if not resultado_imagen:
        return prob_falsa
    
    estatus = resultado_imagen.get("estatus")

    if estatus == ImagenEnum.generada_ia:
        prob_falsa = min(prob_falsa + 0.2, 1.0)
    elif estatus == ImagenEnum.fuera_contexto:
        ela = resultado_imagen.get("ela_score", -1.0)
        if ela != -1.0 and ela > 15:
            prob_falsa = min(prob_falsa + 0.15, 1.0)
        else:
            prob_falsa = min(prob_falsa + 0.1, 1.0)

    return round(prob_falsa, 4)

# Ajusta la probabilidad del modelo con el análisis realizado del texto
def _ajustar_con_texto(prob_falsa: float, resultado_texto: dict) -> float:
    ajuste = 0.0

    if resultado_texto.get("punt_objetividad", 1.0) < 0.4:
        ajuste += 0.05
    if resultado_texto.get("punt_sentimiento", 0.0) < -0.3:
        ajuste += 0.05

    return round(min(prob_falsa + ajuste, 1.0), 4)

# Nivel de confianza de la predicción
def _nivel_confianza(prob_falsa: float) -> str:
    distancia = abs(prob_falsa - 0.5)
    if distancia >= 0.35:
        return "alta"
    elif distancia >= 0.15:
        return "media"
    else:
        return "baja"    

# Orquestador del análisis de noticias
def procesar_analisis_noticia(session: Session, noticia_id: int, lang: str = "es"):

    noticia = session.get(Noticia, noticia_id)
    if not noticia:
        logger.error(f"Noticia {noticia_id} no encontrada")
        return None
    
    try:
        logger.info(f"Análisis {noticia.titulo[:50]}")

        # Predicción principal con el modelo entrenado
        etiqueta_modelo, prob_falsa = predecir(noticia.titulo, noticia.descripcion, lang=lang)
        logger.info(f"Modelo: {etiqueta_modelo} {prob_falsa:.2f}")

        # análisis imagen
        resultado_imagen = None
        if noticia.imagen_url:
            resultado_imagen = analizar_imagen(noticia.imagen_url, fecha_publi=noticia.fecha_publi, titulo=noticia.titulo, texto_url=noticia.texto_url or "")

        # Ajuste multimodal, para ver si la imagen refuerza la predicción
        prob_final = _ajustar_con_imagen(prob_falsa, resultado_imagen)

        # análisis del texto
        texto_completo = f"{noticia.titulo}. {noticia.descripcion}"
        resultado_texto = analizar_texto(texto_completo, titulo=noticia.titulo) 
            
        prob_final = _ajustar_con_texto(prob_final, resultado_texto)
        confianza = _nivel_confianza(prob_final)

        # Valoración final
        if etiqueta_modelo == "pendiente":
            val = (EtiquetaEnum.falsa if resultado_texto["punt_objetividad"] < 0.45 else EtiquetaEnum.verdadera)
            prob_final = 0.5
        else:
            val = EtiquetaEnum.falsa if prob_final >= 0.5 else EtiquetaEnum.verdadera

        # Explicación XAI con Ollama
        try:
            explicacion = generar_explicacion(resultado_imagen or {}, resultado_texto, titulo=noticia.titulo, lang=lang, prob_falsa=prob_final)
            logger.info(f"Explicación generada: {explicacion[:1000]}")
        except Exception as e:
            logger.warning(f"XAI no disponible: {e}")
            indicadores = ", ".join(resultado_texto.get("indicadores", []))
            sin_indicadores = indicadores or "ninguno"
            explicacion = (
                f"Clasificada como {val.value} con probabilidad {prob_final:.0%}. "
                f"Confianza: {confianza}. "
                f"Emoción dominante: {resultado_texto.get('emocion', '-')}. "
                f"Indicadores: {sin_indicadores}."
            )

        # Y por último, se guarda la valoración
        nueva_val = Valoracion(
            noticia_id=noticia.id,
            resultado=val,
            probabilidad=float(prob_final),
            explicacion=explicacion,
            punt_sentimiento=resultado_texto["punt_sentimiento"],
            punt_objetividad=resultado_texto["punt_objetividad"],
            estatus_analisis_imagen=resultado_imagen["estatus"] if resultado_imagen else ImagenEnum.pendiente,
            fecha_analisis=datetime.now()
        )

        noticia.etiqueta = val

        session.add(nueva_val)
        session.add(noticia)
        session.commit()

        logger.info(f"Resultado final: {val} ({prob_final:.2f}) con una confianza {confianza}")

        return nueva_val

    except Exception as e:
        session.rollback()
        logger.error(f"Error en el proceso de análisis de la noticia {noticia_id}: {e}")
        return None
