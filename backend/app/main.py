from fastapi import FastAPI
from app.routers.noticia import router as new_router
from app.database import init_db
from contextlib import asynccontextmanager
from app.scheduler import start_scheduler, stop_scheduler
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.on_event("startup")
# def on_startup():
#    init_db()

@app.get("/")
def hello():
    return {"msg": "Primera prueba"}

app.include_router(new_router)


