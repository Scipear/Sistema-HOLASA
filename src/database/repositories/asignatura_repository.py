"""Repositorio para la entidad Asignatura."""
from sqlalchemy.orm import Session
from src.database.models.models import AsignaturaModel
from src.database.repositories.base import BaseRepository


class AsignaturaRepository(BaseRepository):
    """Repositorio para operaciones CRUD de asignaturas."""

    def __init__(self):
        super().__init__(AsignaturaModel)

    def get_by_tipo(self, db: Session, tipo: str):
        """Obtiene asignaturas filtradas por tipo.

        Args:
            db: Sesión activa de base de datos.
            tipo: Tipo de asignatura a filtrar.

        Returns:
            Lista de asignaturas del tipo especificado.
        """
        return db.query(self.model_class).filter(self.model_class.tipo == tipo).all()
