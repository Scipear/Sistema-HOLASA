"""Repositorio para la entidad Curso."""
from sqlalchemy.orm import Session
from src.database.models.models import CursoModel
from src.database.repositories.base import BaseRepository


class CursoRepository(BaseRepository):
    """Repositorio para operaciones CRUD de cursos."""

    def __init__(self):
        super().__init__(CursoModel)

    def get_by_year(self, db: Session, year: str):
        """Obtiene cursos filtrados por año.

        Args:
            db: Sesión activa de base de datos.
            year: Año a filtrar.

        Returns:
            Lista de cursos del año especificado.
        """
        return db.query(self.model_class).filter(self.model_class.year == year).all()

    def get_by_mencion(self, db: Session, mencion_id: int):
        """Obtiene cursos filtrados por mención.

        Args:
            db: Sesión activa de base de datos.
            mencion_id: ID de la mención.

        Returns:
            Lista de cursos de la mención especificada.
        """
        return db.query(self.model_class).filter(self.model_class.mencion_id == mencion_id).all()
