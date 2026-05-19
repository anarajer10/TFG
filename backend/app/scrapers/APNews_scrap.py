from datetime import datetime
from .scraper_base import ScraperBase
import xml.etree.ElementTree as ET
import requests
import re
from app.models.schema import EtiquetaEnum
from bs4 import BeautifulSoup

class APNewsScraper(ScraperBase):
    def __init__(self):
        super().__init__(url="https://apnews.com")


    def scrape(self, limit: int = 100):
        articles = []
        
        now = datetime.now()
        sitemaps = [
            f"https://apnews.com/ap-sitemap-{now.strftime('%Y%m')}.xml",
            f"https://apnews.com/ap-sitemap-{now.year}{str(now.month-1).zfill(2)}.xml" if now.month > 1
            else f"https://apnews.com/ap-sitemap-{now.year-1}.12.xml"
        ]

        # patron_hash = re.compile(r'-[a-f0-9]{32}$')

        filtros_url = ['winning-numbers', 'data-skrive']

        filtros_idioma = [
            '/article/eeuu-',
            '/article/pentagono-',
            '/article/senegal-',
            '/article/marruecos-',
            '/article/rusia-',
            '/article/eeuu-',
        ]

        urls = []
        for sitemap_url in sitemaps:
            try:
                response = requests.get(sitemap_url, headers=self.headers, timeout=15)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                root = ET.fromstring(response.content)
                all_urls = [elem.text for elem in root.iter() if elem.text and 'loc' in elem.tag]
        
                article_urls = [u for u in all_urls if '/article/' in u]
                # article_urls = [u for u in article_urls if not patron_hash.search(u)]
                article_urls = [u for u in article_urls if not any(f in u for f in filtros_url)]
                article_urls = [u for u in article_urls if not any(f in u for f in filtros_idioma)]
                urls.extend(article_urls)

            except Exception as e:
                print(f"Error cargando sitemap de AP News: {e}")

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

            h1 = soup.find('h1', class_='Page-headline')
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
                    'Copyright', 'All rights reserved', 'Follow AP',
                    'Sign up', 'Suscribe', 'Newsletter', 'Cookie', 'Privacy Policy',
                    'Terms of Service', 'Log in', 'Cookie Policy'
                ]):
                    continue

                clean_paragraphs.append(text)

            content = "\n\n".join(clean_paragraphs)
            
            return {
                "titulo": titulo,
                "descripcion": content,    
                "categoria": "Noticias",
                "nombre_fuente": "APNews.com",
                "url_fuente": "https://apnews.com/article/",
                "idioma_fuente": "en",
                "fecha_publi": fecha_publi,
                "texto_url": url,
                "imagen_url": imagen_url,
                "etiqueta": EtiquetaEnum.verdadera # AP News publica noticias verificadas
            }
        
        except Exception as e:
            print(f"Error scraping AP News {url}: {e}")
            return None

    