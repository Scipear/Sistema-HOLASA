"""Repositorio para la relación muchos a muchos sesiones-profesores."""
from sqlalchemy.orm import Session
from src.database.models.models import SesionProfesorModel
from src.database.repositories.base import BaseRepository


class SesionProfesorRepository(BaseRepository):
    """Repositorio para operaciones CRUD de la tabla sesiones_profesores."""

    def __init__(self):
        super().__init__(SesionProfesorModel)

    def get_by_profesor(self, db: Session, profesor_id: int):
        """Obtiene todas las asignaciones de un profesor.

        Args:
            db: Sesión activa de base de datos.
            profesor_id: ID del profesor.

        Returns:
            Lista de asignaciones del profesor ordenadas por sesión.
        """
        return db.query(self.model_class).filter(
            self.model_class.profesor_id == profesor_id
        ).order_by(self.model_class.sesion_id.asc()).all()

    def get_by_sesion(self, db: Session, sesion_id: int):
        """Obtiene todos los profesores asignados a una sesión.

        Args:
            db: Sesión activa de base de datos.
            sesion_id: ID de la sesión.

        Returns:
            Lista de asignaciones de la sesión.
        """
        return db.query(self.model_class).filter(
            self.model_class.sesion_id == sesion_id
        ).all()

    def exists(self, db: Session, sesion_id: int, profesor_id: int):
        """Verifica si una asignación sesión-profesor ya existe.

        Args:
            db: Sesión activa de base de datos.
            sesion_id: ID de la sesión.
            profesor_id: ID del profesor.

        Returns:
            True si ya existe, False en caso contrario.
        """
        return db.query(self.model_class).filter(
            self.model_class.sesion_id == sesion_id,
            self.model_class.profesor_id == profesor_id,
        ).first() is not None
