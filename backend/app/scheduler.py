import logging
from apscheduler.schedulers.background import BackgroundScheduler # type: ignore
from app.scrapers.runner_scraper import(
    run_scraper_RTVE,
    run_scraper_Newtral,
    run_scraper_APNews,
    run_scraper_Snopes,
    run_scraper_VeinteMin,
    run_scraper_TheIndependent,
    analizar_noticias_pendientes
)

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def _run_scrapers():
    run_scraper_RTVE(limit=20)
    run_scraper_Newtral(limit=20)
    run_scraper_APNews(limit=20)
    run_scraper_Snopes(limit=20)
    run_scraper_VeinteMin(limit=20)
    run_scraper_TheIndependent(limit=20)
    analizar_noticias_pendientes(limit=100)

def start_scheduler():
    # Se hará el scraping una vez cada 24 horas
    scheduler.add_job(_run_scrapers, "interval", hours=24)
    # Para que haga un scraping nada más encender el contenedor
    # scheduler.add_job(_run_scrapers)
    scheduler.start()
    logger.info("Scheduler activado")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler desactivado")