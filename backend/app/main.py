from fastapi import FastAPI
from app.routers.noticia import router as new_router
from app.database import init_db
from contextlib import asynccontextmanager
from app.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(lifespan=lifespan)

# @app.on_event("startup")
# def on_startup():
#    init_db()

@app.get("/")
def hello():
    return {"msg": "Primera pureba"}

app.include_router(new_router)


