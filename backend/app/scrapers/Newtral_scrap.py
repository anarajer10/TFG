from datetime import datetime
from .scraper_base import ScraperBase
import xml.etree.ElementTree as ET
import requests
import re
from app.models.schema import EtiquetaEnum
from bs4 import BeautifulSoup

class NewtralScraper(ScraperBase):
    def __init__(self):
        super().__init__(url="https://www.newtral.es/tag/bulos/")

    def scrape(self, limit: int = 100):
        articles = []
        
        patron = re.compile(r'https://www\.newtral\.es/[^/]+/\d{8}/$')

        urls_articulos = set()
        page = 1
        
        try:
            while len(urls_articulos) < limit:
                if page == 1:
                    url = 'https://www.newtral.es/tag/bulos/'
                else:
                    url = f'https://www.newtral.es/tag/bulos/page/{page}/'

                response = requests.get(url, headers=self.headers, timeout=15)

                if response.status_code == 404:
                    break
                response.raise_for_status()
                response.encoding = response.apparent_encoding

                soup = BeautifulSoup(response.content, 'html.parser')

                nuevas = set()
                for a in soup.find_all('a', href=True):
                    href = a.get('href', '')
                    if patron.match(href):
                        nuevas.add(href)

                if not nuevas:
                    break

                urls_articulos.update(nuevas)
                page +=1

        except Exception as e:
            print(f"Error obteniendo urls de Newtral: {e}")

        for url in list(urls_articulos)[:limit]:
            article_data = self._scrape_article(url)
            if article_data:
                articles.append(article_data)

        return articles
    
    def _scrape_article(self, url: str) -> dict | None:
        try: 
            soup = self._get_soup(url)

            h1 = soup.find('h1', class_='post-title-1')
            if not h1:
                h1 = soup.find('h1')
            titulo = h1.get_text(strip=True) if h1 else 'Sin titulo'

            image_tag = (soup.find("meta", property="og:image"))
            imagen_url = image_tag.get("content") if image_tag else None

            fecha_publi = None
            for prop in ['article:modified_time', 'article:published_time']:
                date_tag = soup.find('meta', property=prop)
                if date_tag:
                    try:
                        dt_str = date_tag.get('content', '').split("+")[0]
                        fecha_publi = datetime.fromisoformat(dt_str)
                        break
                    except:
                        fecha_publi = datetime.now()


            main = soup.select_one('main')
            paragraphs = main.find_all('p') if main else soup.find_all('p')

            clean_paragraphs = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                
                # Para eliminar líneas vacías
                if not text:
                    continue

                # Para eliminar textos demasiado cortos
                if len(text) < 20:
                    continue

                # Para eliminar footer(entre otras cosas)
                if any(palabra in text for palabra in[
                    'Política de Cookies', 'Aviso legal', 'Todos los derechos',
                    'Suscríbete', 'Newsletter', 'síguenos', 'Síguenos'
                ]):
                    continue

                clean_paragraphs.append(text)

            content = "\n\n".join(clean_paragraphs)
            
            return {
                "titulo": titulo,
                "descripcion": content,    
                "categoria": "Fact-Check",
                "nombre_fuente": "Newtral.es",
                "url_fuente": "https://www.newtral.es/",
                "idioma_fuente": "es",
                "fecha_publi": fecha_publi,
                "texto_url": url,
                "imagen_url": imagen_url,
                "etiqueta": EtiquetaEnum.falsa # Newtral publica bulos desmentidos
            }
        
        except Exception as e:
            print(f"Error scraping Newtral {url}: {e}")
            return None

    