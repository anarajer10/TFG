from datetime import datetime
from .scraper_base import ScraperBase
import xml.etree.ElementTree as ET
import requests
import re
from app.models.schema import EtiquetaEnum
from bs4 import BeautifulSoup

class SnopesScraper(ScraperBase):
    def __init__(self):
        super().__init__(url="https://www.snopes.com")


    def scrape(self, limit: int = 100):
        articles = []
        
        sitemaps = [
            "https://media.snopes.com/sitemaps/sitemap-latest.xml",
        ]

        filtros_url = ['/tag/', '/category/', '/author/', '/facebook-questions/']

        urls = []
        for sitemap_url in sitemaps:
            try:
                response = requests.get(sitemap_url, headers=self.headers, timeout=15)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                root = ET.fromstring(response.content)
                all_urls = [elem.text for elem in root.iter() if elem.text and 'loc' in elem.tag]
        
                article_urls = [u for u in all_urls if '/fact-check/' in u]
                article_urls = [u for u in article_urls if not any(f in u for f in filtros_url)]
                urls.extend(article_urls)

            except Exception as e:
                print(f"Error cargando sitemap de Snopes: {e}")

            if len(urls) >= limit:
                break

        for url in urls[:limit]:
            article_data = self._scrape_article(url)
            if article_data:
                articles.append(article_data)


        return articles
    
    def _scrape_article(self, url: str) -> dict | None:
        try: 
            soup = self._get_soup(url)

            h1 = soup.find('h1') or soup.select_one("h1.title")
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

            
            main = soup.select_one("div.single-body-card") or soup.select_one("article")
            paragraphs = main.find_all('p') if main else soup.find_all('p')

            clean_paragraphs = []
            for p in paragraphs:
                for s in p(["script", "style", "aside"]):
                    s.decompose()

                text = p.get_text(strip=True)
                
                # Para eliminar líneas vacías
                if not text:
                    continue

                # Para eliminar textos demasiado cortos
                if len(text) < 20:
                    continue

                # Para eliminar footer(entre otras cosas)
                if any(palabra in text for palabra in[
                    'Copyright', 'All rights reserved', 'Rating:', 'Claim:',
                    'Our Rating', 'Contact us', 'Newsletter', 'Snopes.com'
                ]):
                    continue

                clean_paragraphs.append(text)

            content = "\n\n".join(clean_paragraphs)

            etiqueta = EtiquetaEnum.falsa
            imagen_rating = soup.select_one('div.rating-wrapper img')
            if imagen_rating and imagen_rating.get('alt'):
                imagen_rating = imagen_rating.get('alt').lower()
                if 'true' in imagen_rating or 'correct'in imagen_rating:
                    etiqueta = EtiquetaEnum.verdadera
            
            return {
                "titulo": titulo,
                "descripcion": content,    
                "categoria": "Fact-Check",
                "nombre_fuente": "Snopes.com",
                "url_fuente": "https://www.snopes.com/",
                "idioma_fuente": "Inglés",
                "fecha_publi": fecha_publi,
                "texto_url": url,
                "imagen_url": imagen_url,
                "etiqueta": etiqueta # AP News publica noticias verificadas
            }
        
        except Exception as e:
            print(f"Error scraping Snopes {url}: {e}")
            return None

    