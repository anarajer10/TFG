from datetime import datetime
from .scraper_base import ScraperBase
import xml.etree.ElementTree as ET
import requests
import re
from app.models.schema import EtiquetaEnum

class IndependentScraper(ScraperBase):
    def __init__(self):
        super().__init__(url="https://www.independent.co.uk/")

    def scrape(self, limit: int = 100):
        articles = []
        
        sitemap_url = "https://www.independent.co.uk/sitemaps/sitemap-recent.xml"
        
        try:
            response = requests.get(sitemap_url, headers=self.headers, timeout=15)
            response.raise_for_status()

            # Aquí también, para que capte los acentos
            response.encoding = response.apparent_encoding

            root = ET.fromstring(response.content)

            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                          'news': 'http://www.google.com/schemas/sitemap-news/0.9'}

            urls = [
                elem.text for elem in root.findall(".//ns:loc", namespaces)
                if elem.text and (
                    '/news/' in elem.text or
                    '/tv/news/' in elem.text
                )
            ]

            for url in urls:
                article_data = self._scrape_article(url)
                if article_data:
                    articles.append(article_data)

                if len(articles) >= limit:
                    break

        except Exception as e:
            print(f"Error cargando el sitemap de The Independent: {e}")

        return articles
    
    def _scrape_article(self, url: str) -> dict | None:
        try: 
            soup = self._get_soup(url)

            h1 = soup.find('h1')
            titulo = h1.get_text(strip=True) if h1 else "Sin título"

            image_tag = (soup.find("meta", property="og:image"))
            imagen_url = image_tag.get("content") if image_tag else None

            fecha_publi = None
            for prop in ['article:modified_time', 'article:published_time']:
                date_tag = soup.find('meta', property=prop)
                if date_tag:
                    try:
                        dt_str = date_tag.get('content', '').split("+")[0]
                        fecha_publi = datetime.fromisoformat(dt_str)
                    except:
                        fecha_publi = datetime.now()

            content_container = soup.select_one("article") or soup.select_one("div#main")
            paragraphs = content_container.find_all("p") if content_container else soup.find_all("p")

            clean_paragraphs = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                
                # Para eliminar líneas vacías
                if not text:
                    continue

                # Para eliminar líneas con guiones (----)
                if re.fullmatch(r"\s*-{3,}\s*", text):
                    continue

                # Para eliminar textos demasiado cortos
                if len(text) < 20:
                    continue

                # Para eliminar footer(entre otras cosas)
                if any(palabra in text for palabra in[
                    'Copyright', 'All rights reserved', 'Follow us',
                    'Sign up', 'Suscribe', 'Newsletter', 'Cookie', 'Privacy Policy',
                    'Terms of Service', 'Log in', 'Cookie Policy',
                    'I would like to be emailed', 'Privacy notice', 'offers, events and updates'
                ]):
                    continue

                clean_paragraphs.append(text)

            content = "\n\n".join(clean_paragraphs)
            
            return {
                "titulo": titulo,
                "descripcion": content,    
                "categoria": "Noticias",
                "nombre_fuente": "independent.co.uk",
                "url_fuente": "https://www.independent.co.uk/",
                "idioma_fuente": "en",
                "fecha_publi": fecha_publi,
                "texto_url": url,
                "imagen_url": imagen_url,
                "etiqueta": EtiquetaEnum.pendiente 
            }
        
        except Exception as e:
            print(f"Error scraping The Independent {url}: {e}")
            return None

    