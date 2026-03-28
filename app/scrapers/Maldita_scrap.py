from datetime import datetime
from .scraper_base import ScraperBase
import xml.etree.ElementTree as ET
import requests
import re
from app.models.schema import EtiquetaEnum

class MalditaScraper(ScraperBase):
    def __init__(self):
        super().__init__(url="https://maldita.es/malditobulo/")

    def scrape(self, limit: int = 100):
        articles = []
        
        sitemap_url = "https://maldita.es/sitemap.malditobulo.xml"
        
        try:
            response = requests.get(sitemap_url, headers=self.headers, timeout=15)
            response.raise_for_status()

            # Aquí también, para que capte los acentos
            response.encoding = response.apparent_encoding

            root = ET.fromstring(response.content)

            urls = [
                elem.text for elem in root.iter() 
                if "loc" in elem.tag
            ]

            for url in urls:
                if "staging." in url:
                    continue

                article_data = self._scrape_article(url)
                if article_data:
                    articles.append(article_data)

                if len(articles) >= limit:
                    break
        except Exception as e:
            print(f"Error cargando sitemap de Maldita: {e}")

        return articles
    
    def _scrape_article(self, url: str) -> dict | None:
        try: 
            soup = self._get_soup(url)

            titulo = soup.find("h1").text.strip()

            # Para obtener las imágenes
            image_tag = soup.select_one("#article-content img")
            imagen_url = None

            if not image_tag:
                image_aux = soup.select_one('meta[property="og:image"]')
                if image_aux:
                    imagen_url = image_aux.get("content")

            if image_tag:
                imagen_url = image_tag.get("src") or image_tag.get("data-src") or image_tag.get("data-lazy-src")
                # Para convertir de webp a jpg (si es posible)
                if imagen_url and imagen_url.endswith(".webp"):
                    imagen_url = re.sub(r"-webp\.webp$", "-jpg.jpg", imagen_url)

            date_tag = soup.find("time")
            fecha_publi = (
                datetime.fromisoformat(date_tag["datetime"])
                if date_tag and date_tag.has_attr("datetime")
                else None
            )

            content_container = soup.select_one("#article-content")

            if content_container:
                for fig in content_container.find_all("figure"):
                    fig.decompose()
                paragraphs = content_container.find_all("p")
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
                if "Política de Cookies" in text:
                    continue

                clean_paragraphs.append(text)

            content = "\n".join(clean_paragraphs)
            content = re.sub(r"\n\s*-{3,}\s*\n", "\n", content) # Por si aparecen guiones fuera (en nodos sueltos dentro del div)


            return {
                "titulo": titulo,
                "descripcion": content,     
                "categoria": "Fact-Check",
                "nombre_fuente": "Maldita.es",
                "url_fuente": "https://maldita.es/malditobulo/",
                "idioma_fuente": "Español",
                "fecha_publi": fecha_publi,
                "texto_url": url,
                "imagen_url": imagen_url,
                "etiqueta": EtiquetaEnum.falsa # Maldita publica bulos desmentidos
            }
        
        except Exception as e:
            print(f"Error scraping Maldita {url}: {e}")
            return None

    