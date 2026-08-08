"""Servicio de negocio para la relación salon-curso."""
from sqlalchemy.orm import Session
from src.database.repositories.salon_curso_repository import (
    SalonCursoRepository,
)
from src.database.repositories.salon_repository import SalonRepository
from src.database.repositories.curso_repository import CursoRepository

class SalonCursoService:
    """Servicio que gestiona la asignación de salones a cursos."""
    def __init__(self, repository: SalonCursoRepository | None = None,
                 salon_repository: SalonRepository | None = None,
                 curso_repository: CursoRepository | None = None):
        self.repository = repository or SalonCursoRepository()
        self.salon_repository = salon_repository or SalonRepository()
        self.curso_repository = curso_repository or CursoRepository()

    def asignar(self, db: Session, salon_id: int, curso_id: int):
        """Asigna un salón a un curso.

        Args:
            db: Sesión activa de base de datos.
            salon_id: ID del salón.
            curso_id: ID del curso.

        Returns:
            La asignación creada.

        Raises:
            ValueError: Si el salón o el curso no existen,
                       o la asignación ya existe.
        """
        salon = self.salon_repository.get_by_id(db, salon_id)
        if not salon:
            raise ValueError(f"Salón con id {salon_id} no encontrado")
        curso = self.curso_repository.get_by_id(db, curso_id)
        if not curso:
            raise ValueError(f"Curso con id {curso_id} no encontrado")
        if self.repository.exists(db, salon_id, curso_id):
            raise ValueError(
                f"El salón ya está asignado a este curso"
            )
        try:
            obj = self.repository.create(
                db, salon_id=salon_id, curso_id=curso_id
            )
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al asignar salón a curso: {e}") from e

    def desasignar(self, db: Session, id: int):
        """Elimina una asignación salón-curso.

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
        """Obtiene todas las asignaciones de salones a cursos."""
        return self.repository.get_all(db)

    def contar(self, db: Session):
        """Obtiene el número de asignaciones de salones a cursos."""
        return self.repository.count(db)

    def obtener_por_salon(self, db: Session, salon_id: int):
        """Obtiene los cursos asignados a un salón."""
        return self.repository.get_by_salon(db, salon_id)

    def obtener_por_curso(self, db: Session, curso_id: int):
        """Obtiene los salones asignados a un curso."""
        return self.repository.get_by_curso(db, curso_id)

    def actualizar(self, db: Session, id: int, salon_id: int, curso_id: int):
        """Actualiza una asignación salón-curso.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la asignación.
            salon_id: Nuevo salón.
            curso_id: Nuevo curso.

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
        curso = self.curso_repository.get_by_id(db, curso_id)
        if not curso:
            raise ValueError(f"Curso con id {curso_id} no encontrado")
        if self.repository.exists(db, salon_id, curso_id):
            raise ValueError(
                f"El salón ya está asignado a este curso"
            )
        try:
            obj = self.repository.update(db, id, salon_id, curso_id)
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al actualizar salón a curso: {e}") from e