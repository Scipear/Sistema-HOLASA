"""Repositorio para la entidad Profesor."""
from sqlalchemy.orm import Session
from src.database.models.models import ProfesorModel
from src.database.repositories.base import BaseRepository


class ProfesorRepository(BaseRepository):
    """Repositorio para operaciones CRUD de profesores."""

    def __init__(self):
        super().__init__(ProfesorModel)

    def get_by_apellido(self, db: Session, apellido: str):
        """Obtiene profesores filtrados por apellido.

        Args:
            db: Sesión activa de base de datos.
            apellido: Apellido a buscar.

        Returns:
            Lista de profesores con el apellido especificado.
        """
        return db.query(self.model_class).filter(self.model_class.apellido == apellido).all()

    def get_activos(self, db: Session):
        """Obtiene todos los profesores activos.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Lista de profesores con estado activo.
        """
        return db.query(self.model_class).filter(self.model_class.estado == True).all()

    def get_by_correo(self, db: Session, correo: str):
        """Obtiene un profesor por su correo electrónico.

        Args:
            db: Sesión activa de base de datos.
            correo: Correo electrónico a buscar.

        Returns:
            El profesor encontrado o None si no existe.
        """
        return db.query(self.model_class).filter(self.model_class.correo == correo).first()
