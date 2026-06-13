"""Repositorio para la relación muchos a muchos profesor-asignatura."""
from sqlalchemy.orm import Session
from src.database.models.models import ProfesorAsignaturaModel
from src.database.repositories.base import BaseRepository


class ProfesorAsignaturaRepository(BaseRepository):
    """Repositorio para operaciones CRUD de la tabla profesor_asignaturas."""

    def __init__(self):
        super().__init__(ProfesorAsignaturaModel)

    def get_by_profesor(self, db: Session, profesor_id: int):
        """Obtiene todas las asignaturas asignadas a un profesor.

        Args:
            db: Sesión activa de base de datos.
            profesor_id: ID del profesor.

        Returns:
            Lista de relaciones profesor-asignatura.
        """
        return db.query(self.model_class).filter(
            self.model_class.profesor_id == profesor_id
        ).all()

    def get_by_curso_asignatura(self, db: Session, curso_asignatura_id: int):
        """Obtiene todos los profesores asignados a una relación curso-asignatura.

        Args:
            db: Sesión activa de base de datos.
            curso_asignatura_id: ID de la relación curso-asignatura.

        Returns:
            Lista de relaciones profesor-asignatura.
        """
        return db.query(self.model_class).filter(
            self.model_class.curso_asignatura_id == curso_asignatura_id
        ).all()

    def exists(self, db: Session, profesor_id: int, curso_asignatura_id: int):
        """Verifica si una asignación profesor-asignatura ya existe.

        Args:
            db: Sesión activa de base de datos.
            profesor_id: ID del profesor.
            curso_asignatura_id: ID de la relación curso-asignatura.

        Returns:
            True si ya existe, False en caso contrario.
        """
        return db.query(self.model_class).filter(
            self.model_class.profesor_id == profesor_id,
            self.model_class.curso_asignatura_id == curso_asignatura_id,
        ).first() is not None
