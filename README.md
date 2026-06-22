# HOOT — Detección Multimodal de Fake News

![Python](https://img.shields.io/badge/Python-3.11-534AB7)
![JavaScript](https://img.shields.io/badge/JavaScript-ES2024-ffdb64)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-7a74cc)
![React](https://img.shields.io/badge/React-19-a49bdf)
![Docker](https://img.shields.io/badge/Docker-Compose-25215e)
![License](https://img.shields.io/badge/Licencia-MIT-yellow)

Trabajo Fin de Grado — Ingeniería Informática, Universidad de Granada.

HOOT es una plataforma web para la detección automática de noticias 
falsas en español e inglés. Combina un clasificador de texto entrenado, 
análisis de imagen y explicaciones generadas por LLM para emitir un 
veredicto razonado sobre la autenticidad de una noticia.

---

## Tecnologías

**Frontend:** JavaScript · React + Vite  
**Backend:** Python · FastAPI · SQLModel · MySQL  
**ML/NLP:** scikit-learn · pysentimiento · spaCy · CLIP  
**LLM:** Llama 3.2 via Ollama  
**Despliegue:** Docker Compose  

---

## Requisitos

- Docker y Docker Compose
- Ollama ejecutándose en el host:

```bash
ollama pull llama3.2:3b
```

---

## Instalación

```bash
git clone https://github.com/anarajer10/TFG.git
cd TFG
```

Crea un archivo `.env` en la raíz con las variables `PASSWORD_DB`, 
`NAME_DB`, `URL_DB`, `HUGGINGFACE_API_KEY`, `OLLAMA_URL` y 
`OLLAMA_MODEL`, y levanta los contenedores:

```bash
docker compose up --build
```

La aplicación estará disponible en el puerto 3000.

---

## Modelos de clasificación

| Idioma | Modelo | F1 (test) | ROC-AUC |
|---|---|---|---|
| ES | CalibratedClassifierCV(LinearSVC) | 0.804 | 0.894 |
| EN | LogisticRegression | 0.845 | 0.926 |

---

## Autora

Ana Aragón Jerónimo

---

## Licencia

[MIT](LICENSE)
