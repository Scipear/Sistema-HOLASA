"""Modelos ORM SQLAlchemy del sistema HOLASA."""
from src.database.models.models import (
    MencionModel,
    CursoModel,
    AsignaturaModel,
    ProfesorModel,
    SesionModel,
    SalonModel,
    SesionProfesorModel,
    CursoAsignaturaModel,
    ProfesorAsignaturaModel,
)

__all__ = [
    "MencionModel",
    "CursoModel",
    "AsignaturaModel",
    "ProfesorModel",
    "SesionModel",
    "SalonModel",
    "SesionProfesorModel",
    "CursoAsignaturaModel",
    "ProfesorAsignaturaModel",
]
