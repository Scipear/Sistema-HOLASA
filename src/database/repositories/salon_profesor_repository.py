"""Repositorio para la relación muchos a muchos salon-profesor."""
from sqlalchemy.orm import Session
from src.database.models.models import SalonProfesorModel
from src.database.repositories.base import BaseRepository


class SalonProfesorRepository(BaseRepository):
    """Repositorio para operaciones CRUD de la tabla salon_profesor."""

    def __init__(self):
        super().__init__(SalonProfesorModel)

    def get_by_profesor(self, db: Session, profesor_id: int):
        """Obtiene todos los salones asignados a un profesor."""
        return db.query(self.model_class).filter(
            self.model_class.profesor_id == profesor_id
        ).all()
    
    def get_by_salon(self, db: Session, salon_id: int):
        """Obtiene todos los profesores asignados a un salón."""
        return db.query(self.model_class).filter(
            self.model_class.salon_id == salon_id
        ).all()
    
    def exists(self, db: Session, salon_id: int, profesor_id: int):
        """Verifica si un salon ya está asignado a un profesor."""
        return db.query(self.model_class).filter(
            self.model_class.salon_id == salon_id,
            self.model_class.profesor_id == profesor_id,
        ).first() is not None