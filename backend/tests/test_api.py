from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException, Path
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

@app.get("/noticias/{id}")
def get_noticia(id: int = Path(gt=0)):
    raise HTTPException(status_code=404, detail="Noticia no encontrada")

class NoticiaCreate(BaseModel):
    titulo: str = Field(min_length=10)
    descripcion: str
    texto_url: str

@app.post("/analizar")
def analizar(noticia: NoticiaCreate):
    return {"resultado": "pendiente"}

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

def test_noticia_inexistente():
    response = client.get("/noticias/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Noticia no encontrada"

def test_titulo_corto():
    payload = {
        "titulo": "Muy breve",
        "descripcion": "Texto descriptivo de la noticia de prueba",
        "texto_url": "https://ejemplo.com/noticia"
    }

    response = client.post("/analizar", json=payload)
    assert response.status_code == 422