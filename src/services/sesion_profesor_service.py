"""Servicio de negocio para la relación sesiones-profesores."""
from sqlalchemy.orm import Session
from src.database.repositories.sesion_profesor_repository import (
    SesionProfesorRepository,
)
from src.database.repositories.profesor_repository import ProfesorRepository
from src.database.repositories.sesion_repository import SesionRepository


class SesionProfesorService:
    """Servicio que gestiona la asignación de profesores a sesiones."""

    def __init__(self, repository: SesionProfesorRepository | None = None,
                 profesor_repository: ProfesorRepository | None = None,
                 sesion_repository: SesionRepository | None = None):
        self.repository = repository or SesionProfesorRepository()
        self.profesor_repository = profesor_repository or ProfesorRepository()
        self.sesion_repository = sesion_repository or SesionRepository()

    def asignar(self, db: Session, sesion_id: int, profesor_id: int):
        """Asigna un profesor a una sesión.

        Args:
            db: Sesión activa de base de datos.
            sesion_id: ID de la sesión.
            profesor_id: ID del profesor.

        Returns:
            La asignación creada.

        Raises:
            ValueError: Si la sesión o el profesor no existen,
                       o la asignación ya existe.
        """
        sesion = self.sesion_repository.get_by_id(db, sesion_id)
        if not sesion:
            raise ValueError(f"Sesión con id {sesion_id} no encontrada")
        profesor = self.profesor_repository.get_by_id(db, profesor_id)
        if not profesor:
            raise ValueError(f"Profesor con id {profesor_id} no encontrado")
        if self.repository.exists(db, sesion_id, profesor_id):
            raise ValueError(
                f"El profesor ya está asignado a esta sesión"
            )
        try:
            obj = self.repository.create(
                db, sesion_id=sesion_id, profesor_id=profesor_id
            )
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al asignar profesor a sesión: {e}") from e

    def desasignar(self, db: Session, id: int):
        """Elimina una asignación profesor-sesión.

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
            raise ValueError(f"Error al desasignar profesor: {e}") from e

    def obtener_por_id(self, db: Session, id: int):
        """Obtiene una asignación por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la asignación.

        Returns:
            La asignación encontrada o None.
        """
        return self.repository.get_by_id(db, id)

    def obtener_todos(self, db: Session):
        """Obtiene todas las asignaciones profesor-sesión.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Lista de asignaciones.
        """
        return self.repository.get_all(db)

    def contar(self, db: Session):
        """Obtiene el número total de asignaciones profesor-sesión.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Número total de asignaciones.
        """
        return self.repository.count(db)

    def obtener_por_profesor(self, db: Session, profesor_id: int):
        """Obtiene las sesiones asignadas a un profesor.

        Args:
            db: Sesión activa de base de datos.
            profesor_id: ID del profesor.

        Returns:
            Lista de asignaciones del profesor.
        """
        return self.repository.get_by_profesor(db, profesor_id)

    def obtener_por_sesion(self, db: Session, sesion_id: int):
        """Obtiene los profesores asignados a una sesión.

        Args:
            db: Sesión activa de base de datos.
            sesion_id: ID de la sesión.

        Returns:
            Lista de asignaciones de la sesión.
        """
        return self.repository.get_by_sesion(db, sesion_id)

    def actualizar(self, db: Session, id: int,
                   sesion_id: int | None = None,
                   profesor_id: int | None = None):
        """Actualiza una asignación profesor-sesión.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la asignación.
            sesion_id: Nueva sesión (opcional).
            profesor_id: Nuevo profesor (opcional).

        Returns:
            La asignación actualizada.

        Raises:
            ValueError: Si algún FK no existe, la asignación duplicada,
                       o la asignación no existe.
        """
        if sesion_id is not None:
            sesion = self.sesion_repository.get_by_id(db, sesion_id)
            if not sesion:
                raise ValueError(f"Sesión con id {sesion_id} no encontrada")
        if profesor_id is not None:
            profesor = self.profesor_repository.get_by_id(db, profesor_id)
            if not profesor:
                raise ValueError(f"Profesor con id {profesor_id} no encontrado")
        if sesion_id is not None or profesor_id is not None:
            existente = self.repository.get_by_id(db, id)
            if not existente:
                raise ValueError(f"Asignación con id {id} no encontrada")
            final_sesion = (
                sesion_id if sesion_id is not None else existente.sesion_id
            )
            final_profesor = (
                profesor_id if profesor_id is not None else existente.profesor_id
            )
            if self.repository.exists(db, final_sesion, final_profesor):
                raise ValueError(
                    "La asignación ya existe entre esta sesión y este profesor"
                )
        kwargs = {}
        if sesion_id is not None:
            kwargs["sesion_id"] = sesion_id
        if profesor_id is not None:
            kwargs["profesor_id"] = profesor_id
        try:
            obj = self.repository.update(db, id, **kwargs)
            if not obj:
                raise ValueError(f"Asignación con id {id} no encontrada")
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(
                f"Error al actualizar asignación profesor-sesión: {e}"
            ) from e
