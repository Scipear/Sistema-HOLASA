"""Servicio de negocio para la relación salon-profesor."""
from sqlalchemy.orm import Session
from src.database.repositories.salon_profesor_repository import (
    SalonProfesorRepository,
)
from src.database.repositories.salon_repository import SalonRepository
from src.database.repositories.profesor_repository import ProfesorRepository


class SalonProfesorService:
    """Servicio que gestiona la relación salón-profesor."""

    def __init__(self, 
                repository: SalonProfesorRepository | None = None,
                salon_repo: SalonRepository | None = None,
                profesor_repo: ProfesorRepository | None = None):
        self.repository = repository or SalonProfesorRepository()
        self.salon_repository = salon_repo or SalonRepository()
        self.profesor_repository = profesor_repo or ProfesorRepository()

    def asignar(self, db: Session, salon_id: int, profesor_id: int):
        """Asigna un profesor a un salón.

        Args:
            db: Sesión activa de base de datos.
            salon_id: Identificador del salón.
            profesor_id: Identificador del profesor.

        Returns:
            La asignación salon-profesor creada.

        Raises:
            ValueError: Si el salón o el profesor no existe, o si hay duplicado.
        """
        salon = self.salon_repository.get_by_id(db, salon_id)
        if not salon:
            raise ValueError(f"Salón con id {salon_id} no encontrado")
        profesor = self.profesor_repository.get_by_id(db, profesor_id)
        if not profesor:
            raise ValueError(f"Profesor con id {profesor_id} no encontrado")
        if self.repository.exists(db, salon_id, profesor_id):
            raise ValueError(
                f"El profesor ya está asignado a este salón"
            )
        try:
            obj = self.repository.create(db, salon_id, profesor_id)
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al asignar salón a profesor: {e}") from e

    def desasignar(self, db: Session, id: int):
        """Elimina una asignación salon-profesor.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la asignación.

        Raises:
            ValueError: Si la asignación no existe.
        """
        try:
            result = self.repository.delete(db, id)
            if not result:
                raise ValueError(f"Asignación con id {id} no encontrada")
            db.commit()
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al desasignar salón: {e}") from e

    def obtener_por_id(self, db: Session, id: int):
        """Obtiene una asignación por su ID."""
        return self.repository.get_by_id(db, id)

    def obtener_todos(self, db: Session):
        """Obtiene todas las asignaciones de salones a profesores."""
        return self.repository.get_all(db)

    def contar(self, db: Session):
        """Obtiene el número de asignaciones de salones a profesores."""
        return self.repository.count(db)

    def obtener_por_salon(self, db: Session, salon_id: int):
        """Obtiene los profesores asignados a un salón."""
        return self.repository.get_by_salon(db, salon_id)

    def obtener_por_profesor(self, db: Session, profesor_id: int):
        """Obtiene los salones asignados a un profesor."""
        return self.repository.get_by_profesor(db, profesor_id)

    def actualizar(self, db: Session, id: int, salon_id: int, profesor_id: int):
        """Actualiza una asignación salon-profesor.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la asignación.
            salon_id: Nuevo salón.
            profesor_id: Nuevo profesor.

        Returns:
            La asignación actualizada.

        Raises:
            ValueError: Si algún FK no existe o la asignación duplicada.
        """
        if not self.repository.get_by_id(db, id):
            raise ValueError(f"Asignación con id {id} no encontrada")
        salon = self.salon_repository.get_by_id(db, salon_id)
        if not salon:
            raise ValueError(f"Salón con id {salon_id} no encontrado")
        profesor = self.profesor_repository.get_by_id(db, profesor_id)
        if not profesor:
            raise ValueError(f"Profesor con id {profesor_id} no encontrado")
        if self.repository.exists(db, salon_id, profesor_id):
            raise ValueError(
                f"El profesor ya está asignado a este salón"
            )
        try:
            obj = self.repository.update(db, id, salon_id, profesor_id)
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al actualizar salón a profesor: {e}") from e