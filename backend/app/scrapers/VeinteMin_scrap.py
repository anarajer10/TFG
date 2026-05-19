from datetime import datetime
from .scraper_base import ScraperBase
import xml.etree.ElementTree as ET
import requests
import re
from app.models.schema import EtiquetaEnum

class VeinteMinScraper(ScraperBase):
    def __init__(self):
        super().__init__(url="https://www.20minutos.es/")

    def scrape(self, limit: int = 100):
        articles = []
        
        sitemap_url = "https://www.20minutos.es/sitemap-noticias-incremental.xml"
        
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
                if elem.text and not any(palabra in elem.text for palabra in[
                    'bonoloto', 'cuponazo', 'horoscopo', 'horóscopo', 'euromillones',
                    'primitiva', 'loteria', 'lotería', 'once', 'quiniela'
                ])
            ]

            for url in urls:
                article_data = self._scrape_article(url)
                if article_data:
                    articles.append(article_data)

                if len(articles) >= limit:
                    break

        except Exception as e:
            print(f"Error cargando el sitemap de 20minutos: {e}")

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

            content_container = soup.select_one("article")
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
                    'Política de Cookies', 'Aviso legal', 'Todos los derechos',
                    'Suscríbete', 'Newsletter', 'síguenos', 'Síguenos', 
                    'publicidad', 'Publicidad'
                ]):
                    continue

                clean_paragraphs.append(text)

            content = "\n\n".join(clean_paragraphs)
            
            return {
                "titulo": titulo,
                "descripcion": content,    
                "categoria": "Noticias",
                "nombre_fuente": "20minutos.es",
                "url_fuente": "https://www.20minutos.es/",
                "idioma_fuente": "es",
                "fecha_publi": fecha_publi,
                "texto_url": url,
                "imagen_url": imagen_url,
                "etiqueta": EtiquetaEnum.pendiente 
            }
        
        except Exception as e:
            print(f"Error scraping 20minutos {url}: {e}")
            return None

    