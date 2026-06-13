"""Repositorio para la entidad Sesión (bloques horarios)."""
from sqlalchemy.orm import Session
from src.database.models.models import SesionModel
from src.database.repositories.base import BaseRepository


class SesionRepository(BaseRepository):
    """Repositorio para operaciones CRUD de sesiones (bloques horarios)."""

    def __init__(self):
        super().__init__(SesionModel)

    def get_by_dia(self, db: Session, dia: str):
        """Obtiene sesiones filtradas por día.

        Args:
            db: Sesión activa de base de datos.
            dia: Día a filtrar (ej: 'Lunes', 'Martes').

        Returns:
            Lista de sesiones del día especificado.
        """
        return db.query(self.model_class).filter(self.model_class.dia == dia).all()

    def get_overlapping(self, db: Session, dia: str, hora_inicio: str,
                        hora_fin: str, exclude_id: int = None):
        """Obtiene sesiones que se superponen con un horario dado.

        Args:
            db: Sesión activa de base de datos.
            dia: Día a verificar.
            hora_inicio: Hora de inicio del nuevo bloque.
            hora_fin: Hora de fin del nuevo bloque.
            exclude_id: ID de sesión a excluir (para actualizaciones).

        Returns:
            Lista de sesiones superpuestas.
        """
        query = db.query(self.model_class).filter(
            self.model_class.dia == dia,
            self.model_class.hora_inicio < hora_fin,
            self.model_class.hora_fin > hora_inicio,
        )
        if exclude_id is not None:
            query = query.filter(self.model_class.id != exclude_id)
        return query.all()
