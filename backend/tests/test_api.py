from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field

app = FastAPI()

@app.get("/")
def hello():
    return {"msg": "Primera prueba"}

@app.get("/metricas")
def get_metricas():
    return {
        "es": {"modelo": "LinearSVC", "accuracy": 0.8144, "f1_falsa": 0.8043, "f1_real": 0.8235, "roc_auc": 0.8939},
        "en": {"modelo": "LogisticRegression", "accuracy": 0.8416, "f1_falsa": 0.8447, "f1_real": 0.8384, "roc_auc": 0.9258}
    }

@app.get("/noticias/recientes")
def get_noticias_recientes():
    return [
        {
            "noticia": {"id": 1, "titulo": "Noticia de prueba", "descripcion": "Descripción", "texto_url": "https://ejemplo.com/1",
                        "etiqueta": "verdadera", "categoria": None, "fecha_publi": None, "imagen_url": None, "fuente_id": None},
            "valoracion": {"id": 1, "noticia_id": 1, "resultado": "verdadera", "probabilidad": 0.25, "explicacion": None, 
                           "punt_sentimiento": None, "punt_objetividad": None, "estatus_analisis_imagen": "pendiente", "fecha_analisis": "2026-06-15T10:00:00"},
            "fuente_nombre": "ejemplo.com",
        }
    ]

@app.get("/noticias/{id}")
def get_noticia(id: int = Path(gt=0)):
    raise HTTPException(status_code=404, detail="Noticia no encontrada")

@app.get("/extraer")
def extraer_url(url: str = Query(...)):
    return {
        "titulo": "Título de la noticia extraída",
        "descripcion": "Contenido de la noticia de la URL proporcionada",
        "imagen_url": None,
        "fecha_publi": None,
        "fuente_nombre": "https://ejemplo.com",
        "texto_url": url
    }

class NoticiaCreate(BaseModel):
    titulo: str = Field(min_length=10)
    descripcion: str
    texto_url: str

@app.post("/analizar")
def analizar(noticia: NoticiaCreate):
    return {
        "noticia": {"id": 1, "titulo": noticia.titulo, "descripcion": noticia.descripcion, "texto_url": noticia.texto_url,
                    "etiqueta": "pendiente", "categoria": None, "fecha_publi": None, "imagen_url": None, "fuente_id": None},
        "valoracion": {"id": 1, "noticia_id": 1, "resultado": "falsa", "probabilidad": 0.73, "explicacion": "Explicación generada", 
                       "punt_sentimiento": -0.3, "punt_objetividad": 0.4, "estatus_analisis_imagen": "autentica", "fecha_analisis": "2026-06-15T10:00:00"},
        "fuente_nombre": None,
    }

client = TestClient(app)

def test_servidor_disponible():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["msg"] == "Primera prueba"

def test_metricas_estructura_correcta():
    response = client.get("/metricas")
    assert response.status_code == 200
    data = response.json()
    assert "es" in data and "en" in data
    for lang in ("es", "en"):
        assert "accuracy" in data[lang]
        assert "f1_falsa" in data[lang]
        assert "roc_auc" in data[lang]
        assert "modelo" in data[lang]

def test_noticias_recientes_lista():
    response = client.get("/noticias/recientes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "noticia" in data[0]
    assert "valoracion" in data[0]

def test_noticia_inexistente():
    response = client.get("/noticias/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Noticia no encontrada"

def test_extraer_url_campos():
    response = client.get("/extraer", params={"url": "https://ejemplo.com/noticia"})
    assert response.status_code == 200
    data = response.json()
    assert "titulo" in data
    assert "descripcion" in data
    assert "texto_url" in data

def test_analizar_datos_validos():
    payload = {
        "titulo": "Título válido",
        "descripcion": "Texto descriptivo de la noticia de prueba",
        "texto_url": "https://ejemplo.com/noticia-1"
    }

    response = client.post("/analizar", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "noticia" in data
    assert "valoracion" in data

def test_titulo_corto():
    payload = {
        "titulo": "Muy breve",
        "descripcion": "Texto descriptivo de la noticia de prueba",
        "texto_url": "https://ejemplo.com/noticia-2"
    }

    response = client.post("/analizar", json=payload)
    assert response.status_code == 422