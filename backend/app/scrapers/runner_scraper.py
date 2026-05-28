from sqlmodel import Session, select
from app.database import engine
from app.models.schema import Noticia, Fuente
from .RTVE_scrap import RTVEScraper
from .Newtral_scrap import NewtralScraper
from .APNews_scrap import APNewsScraper
from .Snopes_scrap import SnopesScraper
from .VeinteMin_scrap import VeinteMinScraper
from .Independent_scrap import IndependentScraper
import sqlalchemy as sa
from app.services.analisis_modulos import procesar_analisis_noticia
from app.models.schema import Valoracion, Fuente

def _get_or_create_fuente(session: Session, nombre: str, url: str, idioma: str) -> Fuente:
    fuente = session.exec(select(Fuente).where(Fuente.url == url)).first()
    if not fuente:
        fuente = Fuente(nombre=nombre, url=url, idioma=idioma)
        session.add(fuente)
        session.flush() # Para obtener el id sin hacer commit aún
    return fuente

# Para el scraper de The Independent (noticias 'intermedias', ni verdaderas ni falsas)
def run_scraper_TheIndependent(limit: int = 100):
    scraper = IndependentScraper()
    articles = scraper.scrape(limit=limit)

    with Session(engine) as session:
        count = 0
        for article in articles:            # A LO MEJOR A LA LARGA SE AÑADEN MÁS COSAS
            statement = select(Noticia).where(Noticia.texto_url == article["texto_url"])
            existing = session.exec(statement).first()

            if existing:
                print(f"Ya existe: {article['texto_url']}")
                continue

            fuente = _get_or_create_fuente(
                session,
                nombre=article["nombre_fuente"],
                url=article["url_fuente"],
                idioma=article["idioma_fuente"]
            )
            
            noticia = Noticia(                     # Lo mismo que se almacena en schema.py 
                titulo=article["titulo"],
                descripcion=article["descripcion"],
                categoria=article["categoria"],
                fecha_publi=article["fecha_publi"],
                texto_url=article["texto_url"],
                imagen_url=article.get("imagen_url"),
                etiqueta=article["etiqueta"],
                fuente_id=fuente.id
            )
            session.add(noticia)
            count += 1

        session.commit()

        print(f"{len(articles)} noticias guardadas correctamente")
        print(f"Articulos nuevos guardados: {count}")


# Para el scraper de 20minutos.es (noticias 'intermedias', ni verdaderas ni falsas)
def run_scraper_VeinteMin(limit: int = 100):
    scraper = VeinteMinScraper()
    articles = scraper.scrape(limit=limit)

    with Session(engine) as session:
        count = 0
        for article in articles:            # A LO MEJOR A LA LARGA SE AÑADEN MÁS COSAS
            statement = select(Noticia).where(Noticia.texto_url == article["texto_url"])
            existing = session.exec(statement).first()

            if existing:
                print(f"Ya existe: {article['texto_url']}")
                continue

            fuente = _get_or_create_fuente(
                session,
                nombre=article["nombre_fuente"],
                url=article["url_fuente"],
                idioma=article["idioma_fuente"]
            )
            
            noticia = Noticia(                     # Lo mismo que se almacena en schema.py 
                titulo=article["titulo"],
                descripcion=article["descripcion"],
                categoria=article["categoria"],
                fecha_publi=article["fecha_publi"],
                texto_url=article["texto_url"],
                imagen_url=article.get("imagen_url"),
                etiqueta=article["etiqueta"],
                fuente_id=fuente.id
            )
            session.add(noticia)
            count += 1

        session.commit()

        print(f"{len(articles)} noticias guardadas correctamente")
        print(f"Articulos nuevos guardados: {count}")

# Para el scraper de Newtral.es (seccion de bulos)
def run_scraper_Newtral(limit: int = 100):
    scraper = NewtralScraper()
    articles = scraper.scrape(limit=limit)

    with Session(engine) as session:
        count = 0
        for article in articles:            # A LO MEJOR A LA LARGA SE AÑADEN MÁS COSAS
            statement = select(Noticia).where(Noticia.texto_url == article["texto_url"])
            existing = session.exec(statement).first()

            if existing:
                print(f"Ya existe: {article['texto_url']}")
                continue

            fuente = _get_or_create_fuente(
                session,
                nombre=article["nombre_fuente"],
                url=article["url_fuente"],
                idioma=article["idioma_fuente"]
            )
            
            noticia = Noticia(                     # Lo mismo que se almacena en schema.py 
                titulo=article["titulo"],
                descripcion=article["descripcion"],
                categoria=article["categoria"],
                fecha_publi=article["fecha_publi"],
                texto_url=article["texto_url"],
                imagen_url=article.get("imagen_url"),
                etiqueta=article["etiqueta"],
                fuente_id=fuente.id
            )
            session.add(noticia)
            count += 1

        session.commit()

        print(f"{len(articles)} noticias guardadas correctamente")
        print(f"Articulos nuevos guardados: {count}")   


# Para el scraper de RTVE.es (noticias)
def run_scraper_RTVE(limit: int = 100):
    scraper = RTVEScraper()
    articles = scraper.scrape(limit=limit)

    with Session(engine) as session:
        count = 0
        for article in articles:            # A LO MEJOR A LA LARGA SE AÑADEN MÁS COSAS
            statement = select(Noticia).where(Noticia.texto_url == article["texto_url"])
            existing = session.exec(statement).first()

            if existing:
                print(f"Ya existe: {article['texto_url']}")
                continue
            
            fuente = _get_or_create_fuente(
                session,
                nombre=article["nombre_fuente"],
                url=article["url_fuente"],
                idioma=article["idioma_fuente"]
            )
            
            noticia = Noticia(                     # Lo mismo que se almacena en schema.py 
                titulo=article["titulo"],
                descripcion=article["descripcion"],
                categoria=article["categoria"],
                fecha_publi=article["fecha_publi"],
                texto_url=article["texto_url"],
                imagen_url=article.get("imagen_url"),
                etiqueta=article["etiqueta"],
                fuente_id=fuente.id
            )
            session.add(noticia)
            count += 1

        session.commit()

        print(f"{len(articles)} noticias guardadas correctamente.")
        print(f"Articulos nuevos guardados: {count}")               # Núm. articulos por scrap hecho

#  Para el scraper de AP News
def run_scraper_APNews(limit: int = 100):
    scraper = APNewsScraper()
    articles = scraper.scrape(limit=limit)

    with Session(engine) as session:
        count = 0
        for article in articles:            # A LO MEJOR A LA LARGA SE AÑADEN MÁS COSAS
            statement = select(Noticia).where(Noticia.texto_url == article["texto_url"])
            existing = session.exec(statement).first()

            if existing:
                print(f"Ya existe: {article['texto_url']}")
                continue
            
            fuente = _get_or_create_fuente(
                session,
                nombre=article["nombre_fuente"],
                url=article["url_fuente"],
                idioma=article["idioma_fuente"]
            )
            
            noticia = Noticia(                     # Lo mismo que se almacena en schema.py 
                titulo=article["titulo"],
                descripcion=article["descripcion"],
                categoria=article["categoria"],
                fecha_publi=article["fecha_publi"],
                texto_url=article["texto_url"],
                imagen_url=article.get("imagen_url"),
                etiqueta=article["etiqueta"],
                fuente_id=fuente.id
            )
            session.add(noticia)
            count += 1

        session.commit()

        print(f"{len(articles)} noticias guardadas correctamente.")
        print(f"Articulos nuevos guardados: {count}") 

#  Para el scraper de Snopes
def run_scraper_Snopes(limit: int = 100):
    scraper = SnopesScraper()
    articles = scraper.scrape(limit=limit)

    with Session(engine) as session:
        count = 0
        for article in articles:            # A LO MEJOR A LA LARGA SE AÑADEN MÁS COSAS
            statement = select(Noticia).where(Noticia.texto_url == article["texto_url"])
            existing = session.exec(statement).first()

            if existing:
                print(f"Ya existe: {article['texto_url']}")
                continue
            
            fuente = _get_or_create_fuente(
                session,
                nombre=article["nombre_fuente"],
                url=article["url_fuente"],
                idioma=article["idioma_fuente"]
            )
            
            noticia = Noticia(                     # Lo mismo que se almacena en schema.py 
                titulo=article["titulo"],
                descripcion=article["descripcion"],
                categoria=article["categoria"],
                fecha_publi=article["fecha_publi"],
                texto_url=article["texto_url"],
                imagen_url=article.get("imagen_url"),
                etiqueta=article["etiqueta"],
                fuente_id=fuente.id
            )
            session.add(noticia)
            count += 1

        session.commit()

        print(f"{len(articles)} noticias guardadas correctamente.")
        print(f"Articulos nuevos guardados: {count}") 

# Analiza las últimas noticias almacenadas (con estado Pendiente)
def analizar_noticias_pendientes(limit: int = 100):
    with Session(engine) as session: 
        analyzed_ids = session.exec(select(Valoracion.noticia_id)).all()

        if analyzed_ids:
            stmt = select(Noticia).where(
                sa.not_(Noticia.id.in_(analyzed_ids))
            ).order_by(Noticia.id.desc()).limit(limit)
        else:
            stmt = select(Noticia).order_by(Noticia.id.desc()).limit(limit)

        pendientes = session.exec(stmt).all()
        print(f"Noticias pendientes de análisis: {len(pendientes)}")

        for noticia in pendientes:
            fuente = session.get(Fuente, noticia.fuente_id) if noticia.fuente_id else None
            lang = fuente.idioma if fuente and fuente.idioma in ("es", "en") else "es"
            try:
                procesar_analisis_noticia(session, noticia.id, lang=lang)
                print(f"Analizada la noticia {noticia.titulo[:60]}")
            except Exception as e:
                print(f"Error en la noticia {noticia.id}: {e}")
                continue


if __name__ == "__main__":
    run_scraper_Newtral(limit=20)
    run_scraper_RTVE(limit=20)
    run_scraper_APNews(limit=20) # Ha almacenado 47
    run_scraper_Snopes(limit=20) # Ha almacenado 47 también (EN TOTAL 194 noticias en la BD por ahora)
    run_scraper_VeinteMin(limit=20)
    run_scraper_TheIndependent(limit=20)