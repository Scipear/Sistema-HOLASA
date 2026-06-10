import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.database.connection import engine, Base
from src.database.models.models import (
    MencionModel,
    CursoModel,
    AsignaturaModel,
    ProfesorModel,
    SesionModel,
    SalonModel,
    SesionProfesorModel,
    CursoAsignaturaModel,
    ProfesorAsignaturaModel
)


def init_database():
    print("Inicializando base de datos local SQLite desde modelos...")
    Base.metadata.create_all(bind=engine)
    print("¡Tablas y modelos de SQLAlchemy creados exitosamente!")

if __name__ == "__main__":
    init_database()
