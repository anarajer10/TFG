from datetime import datetime
from .scraper_base import ScraperBase
import xml.etree.ElementTree as ET
import requests
import re
from app.models.schema import EtiquetaEnum

class RTVEScraper(ScraperBase):
    def __init__(self):
        super().__init__(url="https://www.rtve.es/noticias/")

    def scrape(self, limit: int = 100):
        articles = []
        
        sitemap_url = "https://www.rtve.es/sitemaps/noticias/sitemap.xml"
        
        try:
            response = requests.get(sitemap_url, headers=self.headers, timeout=15)
            response.raise_for_status()

            # Aquí también, para que capte los acentos
            response.encoding = response.apparent_encoding

            root = ET.fromstring(response.content)

            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            urls = [
                elem.text for elem in root.findall(".//ns:loc", namespaces)
            ]

            for url in urls:
                if "/noticias/" in url:
                    article_data = self._scrape_article(url)
                    if article_data:
                        articles.append(article_data)

                if len(articles) >= limit:
                    break
        except Exception as e:
            print(f"Error cargando el sitemap de RTVE: {e}")

        return articles
    
    def _scrape_article(self, url: str) -> dict | None:
        try: 
            soup = self._get_soup(url)
            title_tag = (soup.select_one("h1.m-item-title") or soup.find("meta", property="og:title"))
            if title_tag:
                if title_tag.name == "meta":
                    titulo = title_tag.get("content", "").strip()
                else:
                    titulo = title_tag.get_text(strip=True)
            else:
                titulo = "Sin título"

            image_tag = (soup.find("meta", property="og:image") or
                         soup.select_one("figure img"))
            
            imagen_url = None
            if image_tag:
                imagen_url = image_tag.get("content") if image_tag.name == "meta" else image_tag.get("src")

            date_tag = soup.find("time")
            fecha_publi = None
            if date_tag and date_tag.has_attr("datetime"):
                try:
                    dt_str = date_tag["datetime"].split("+")[0]
                    fecha_publi = datetime.fromisoformat(dt_str)
                except:
                    fecha_publi = datetime.now()

            content_container = soup.select_one("div.noticia")

            if content_container:
                paragraphs = content_container.find_all("p", recursive=True)
            else:
                paragraphs = soup.find_all("p")

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

                # Para eliminar cookies
                if "Derechos reservados" in text:
                    continue

                clean_paragraphs.append(text)

            content = "\n\n".join(clean_paragraphs)
            content = re.sub(r"\n\s*-{3,}\s*\n", "\n", content) # Por si aparecen guiones fuera (en nodos sueltos dentro del div)

            return {
                "titulo": titulo,
                "descripcion": content,    
                "categoria": "Noticias",
                "nombre_fuente": "RTVE.es",
                "url_fuente": "https://www.rtve.es/noticias/",
                "idioma_fuente": "Español",
                "fecha_publi": fecha_publi,
                "texto_url": url,
                "imagen_url": imagen_url,
                "etiqueta": EtiquetaEnum.verdadera # RTVE publica noticias reales de forma imparcial
            }
        
        except Exception as e:
            print(f"Error scraping RTVE {url}: {e}")
            return None

    