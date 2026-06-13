"""Servicio de negocio para la relación profesor-asignatura."""
from sqlalchemy.orm import Session
from src.database.repositories.profesor_asignatura_repository import (
    ProfesorAsignaturaRepository,
)
from src.database.repositories.profesor_repository import ProfesorRepository
from src.database.repositories.curso_asignatura_repository import (
    CursoAsignaturaRepository,
)


class ProfesorAsignaturaService:
    """Servicio que gestiona la asignación de profesores a curso-asignaturas."""

    def __init__(self, repository: ProfesorAsignaturaRepository | None = None,
                 profesor_repository: ProfesorRepository | None = None,
                 curso_asignatura_repository: CursoAsignaturaRepository | None = None):
        self.repository = repository or ProfesorAsignaturaRepository()
        self.profesor_repository = profesor_repository or ProfesorRepository()
        self.curso_asignatura_repository = (
            curso_asignatura_repository or CursoAsignaturaRepository()
        )

    def asignar(self, db: Session, profesor_id: int,
                curso_asignatura_id: int):
        """Asigna un profesor a una relación curso-asignatura.

        Args:
            db: Sesión activa de base de datos.
            profesor_id: ID del profesor.
            curso_asignatura_id: ID de la relación curso-asignatura.

        Returns:
            La asignación creada.

        Raises:
            ValueError: Si el profesor o la relación curso-asignatura no existen,
                       o la asignación ya existe.
        """
        profesor = self.profesor_repository.get_by_id(db, profesor_id)
        if not profesor:
            raise ValueError(f"Profesor con id {profesor_id} no encontrado")
        curso_asignatura = self.curso_asignatura_repository.get_by_id(
            db, curso_asignatura_id
        )
        if not curso_asignatura:
            raise ValueError(
                f"Relación curso-asignatura con id {curso_asignatura_id} "
                "no encontrada"
            )
        if self.repository.exists(db, profesor_id, curso_asignatura_id):
            raise ValueError(
                "El profesor ya está asignado a esta curso-asignatura"
            )
        try:
            obj = self.repository.create(
                db, profesor_id=profesor_id,
                curso_asignatura_id=curso_asignatura_id
            )
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(
                f"Error al asignar profesor a curso-asignatura: {e}"
            ) from e

    def desasignar(self, db: Session, id: int):
        """Elimina una asignación profesor-curso-asignatura.

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
        """Obtiene todas las asignaciones profesor-curso-asignatura.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Lista de asignaciones.
        """
        return self.repository.get_all(db)

    def contar(self, db: Session):
        """Obtiene el número total de asignaciones profesor-curso-asignatura.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Número total de asignaciones.
        """
        return self.repository.count(db)

    def obtener_por_profesor(self, db: Session, profesor_id: int):
        """Obtiene las curso-asignaturas asignadas a un profesor.

        Args:
            db: Sesión activa de base de datos.
            profesor_id: ID del profesor.

        Returns:
            Lista de asignaciones del profesor.
        """
        return self.repository.get_by_profesor(db, profesor_id)

    def obtener_por_curso_asignatura(self, db: Session,
                                      curso_asignatura_id: int):
        """Obtiene los profesores asignados a una curso-asignatura.

        Args:
            db: Sesión activa de base de datos.
            curso_asignatura_id: ID de la relación curso-asignatura.

        Returns:
            Lista de asignaciones de la curso-asignatura.
        """
        return self.repository.get_by_curso_asignatura(db, curso_asignatura_id)

    def actualizar(self, db: Session, id: int,
                   profesor_id: int | None = None,
                   curso_asignatura_id: int | None = None):
        """Actualiza una asignación profesor-curso-asignatura.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la asignación.
            profesor_id: Nuevo profesor (opcional).
            curso_asignatura_id: Nueva relación curso-asignatura (opcional).

        Returns:
            La asignación actualizada.

        Raises:
            ValueError: Si algún FK no existe, la asignación duplicada,
                       o la asignación no existe.
        """
        if profesor_id is not None:
            profesor = self.profesor_repository.get_by_id(db, profesor_id)
            if not profesor:
                raise ValueError(f"Profesor con id {profesor_id} no encontrado")
        if curso_asignatura_id is not None:
            curso_asignatura = self.curso_asignatura_repository.get_by_id(
                db, curso_asignatura_id
            )
            if not curso_asignatura:
                raise ValueError(
                    f"Relación curso-asignatura con id {curso_asignatura_id} "
                    "no encontrada"
                )
        if profesor_id is not None or curso_asignatura_id is not None:
            existente = self.repository.get_by_id(db, id)
            if not existente:
                raise ValueError(f"Asignación con id {id} no encontrada")
            final_profesor = (
                profesor_id if profesor_id is not None else existente.profesor_id
            )
            final_curso_asignatura = (
                curso_asignatura_id if curso_asignatura_id is not None
                else existente.curso_asignatura_id
            )
            if self.repository.exists(db, final_profesor, final_curso_asignatura):
                raise ValueError(
                    "La asignación ya existe entre este profesor y esta "
                    "curso-asignatura"
                )
        kwargs = {}
        if profesor_id is not None:
            kwargs["profesor_id"] = profesor_id
        if curso_asignatura_id is not None:
            kwargs["curso_asignatura_id"] = curso_asignatura_id
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
                f"Error al actualizar asignación profesor-curso-asignatura: {e}"
            ) from e
