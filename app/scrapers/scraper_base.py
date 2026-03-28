import time 
import random
import requests
from abc import ABC, abstractmethod # Para la clase abstracta, que hereden después de ella
from bs4 import BeautifulSoup       # Para extracción de los datos de las págs web

class ScraperBase(ABC):

    # Constructor
    def __init__(self, url: str, delay_min: float = 1.0, delay_max: float = 3.0):
        self.url  = url
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
        }

    # A la hora de nombrar los métodos, comienzan con un guión bajo para señalar que no son públicos

    def _delay(self):
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    def _get_soup(self, url: str) -> BeautifulSoup:
        self._delay()
        response = requests.get(url, headers=self.headers, timeout=15)
        response.raise_for_status() # En caso de que haya error, para que devuelva el mensaje
        response.encoding = response.apparent_encoding   # Para que recoja también las letras con acentos
        return BeautifulSoup(response.content, "html.parser")

    @abstractmethod
    def scrape(self, limit: int = 100):
        pass