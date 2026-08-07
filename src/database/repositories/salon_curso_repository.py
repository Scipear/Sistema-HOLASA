"""Repositorio para la relación muchos a muchos salon-curso."""
from sqlalchemy.orm import Session
from src.database.models.models import SalonCursoModel
from src.database.repositories.base import BaseRepository


class SalonCursoRepository(BaseRepository):
    """Repositorio para operaciones CRUD de la tabla salon_curso."""

    def __init__(self):
        super().__init__(SalonCursoModel)

    def get_by_curso(self, db: Session, curso_id: int):
        """Obtiene todos los salones asignados a un curso."""
        return db.query(self.model_class).filter(
            self.model_class.curso_id == curso_id
        ).all()
    
    def get_by_salon(self, db: Session, salon_id: int):
        """Obtiene todos los cursos asignados a un salón."""
        return db.query(self.model_class).filter(
            self.model_class.salon_id == salon_id
        ).all()
    
    def exists(self, db: Session, salon_id: int, curso_id: int):
        """Verifica si un salon ya está asignado a un curso."""
        return db.query(self.model_class).filter(
            self.model_class.salon_id == salon_id,
            self.model_class.curso_id == curso_id,
        ).first() is not None
    