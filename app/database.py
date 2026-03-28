import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from sqlmodel import create_engine, Session, SQLModel

load_dotenv()

db_username = os.getenv('USER_DB')
db_password = os.getenv('PASSWORD_DB')
db_host = os.getenv('HOST_DB')
db_port = os.getenv('PORT_DB')
db_name = os.getenv('NAME_DB')
db_driver = os.getenv('DRIVER_DB')

database_url = os.getenv('DATABASE_URL')

if not database_url:
    #mysqlclient
    database_url = f'{db_driver}://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4' # Hay que guardarlo todo, sino no tiene sentido
else:
    pass


engine = create_engine(database_url, echo=True, connect_args={"charset": "utf8mb4"})

# Para crear las tablas
def init_db():
    from app.models.schema import Noticia, Valoracion, Fuente 
    SQLModel.metadata.create_all(engine)

# Para obtener la sesión
def get_session():
    with Session(engine) as session:
        yield session


