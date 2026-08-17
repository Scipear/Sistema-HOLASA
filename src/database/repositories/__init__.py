"""Repositorios CRUD para cada entidad del sistema HOLASA."""
from src.database.repositories.mencion_repository import MencionRepository
from src.database.repositories.curso_repository import CursoRepository
from src.database.repositories.asignatura_repository import AsignaturaRepository
from src.database.repositories.profesor_repository import ProfesorRepository
from src.database.repositories.sesion_repository import SesionRepository
from src.database.repositories.salon_repository import SalonRepository
from src.database.repositories.sesion_profesor_repository import SesionProfesorRepository
from src.database.repositories.curso_asignatura_repository import CursoAsignaturaRepository
from src.database.repositories.profesor_asignatura_repository import ProfesorAsignaturaRepository
from src.database.repositories.salon_curso_repository import SalonCursoRepository
from src.database.repositories.salon_profesor_repository import SalonProfesorRepository

__all__ = [
    "MencionRepository",
    "CursoRepository",
    "AsignaturaRepository",
    "ProfesorRepository",
    "SesionRepository",
    "SalonRepository",
    "SesionProfesorRepository",
    "CursoAsignaturaRepository",
    "ProfesorAsignaturaRepository",
    "SalonCursoRepository",
    "SalonProfesorRepository"
]
