"""Repositorio para la relación muchos a muchos cursos-asignaturas."""
from sqlalchemy.orm import Session
from src.database.models.models import CursoAsignaturaModel
from src.database.repositories.base import BaseRepository


class CursoAsignaturaRepository(BaseRepository):
    """Repositorio para operaciones CRUD de la tabla curso_asignatura."""

    def __init__(self):
        super().__init__(CursoAsignaturaModel)

    def get_by_curso(self, db: Session, curso_id: int):
        """Obtiene todas las asignaturas de un curso.

        Args:
            db: Sesión activa de base de datos.
            curso_id: ID del curso.

        Returns:
            Lista de relaciones curso-asignatura.
        """
        return db.query(self.model_class).filter(
            self.model_class.curso_id == curso_id
        ).all()

    def get_by_asignatura(self, db: Session, asignatura_id: int):
        """Obtiene todos los cursos que tienen una asignatura.

        Args:
            db: Sesión activa de base de datos.
            asignatura_id: ID de la asignatura.

        Returns:
            Lista de relaciones curso-asignatura.
        """
        return db.query(self.model_class).filter(
            self.model_class.asignatura_id == asignatura_id
        ).all()
