"""Servicio de negocio para la relación cursos-asignaturas."""
from sqlalchemy.orm import Session
from src.database.repositories.curso_asignatura_repository import (
    CursoAsignaturaRepository,
)
from src.database.repositories.curso_repository import CursoRepository
from src.database.repositories.asignatura_repository import AsignaturaRepository


class CursoAsignaturaService:
    """Servicio que gestiona la asignación de asignaturas a cursos."""

    def __init__(self, repository: CursoAsignaturaRepository | None = None,
                 curso_repository: CursoRepository | None = None,
                 asignatura_repository: AsignaturaRepository | None = None):
        self.repository = repository or CursoAsignaturaRepository()
        self.curso_repository = curso_repository or CursoRepository()
        self.asignatura_repository = asignatura_repository or AsignaturaRepository()

    def crear(self, db: Session, curso_id: int, asignatura_id: int,
              horas_semanales: int):
        """Asigna una asignatura a un curso con horas semanales.

        Args:
            db: Sesión activa de base de datos.
            curso_id: ID del curso.
            asignatura_id: ID de la asignatura.
            horas_semanales: Horas semanales dedicadas.

        Returns:
            La relación curso-asignatura creada.

        Raises:
            ValueError: Si el curso o la asignatura no existen,
                       o las horas semanales son inválidas.
        """
        curso = self.curso_repository.get_by_id(db, curso_id)
        if not curso:
            raise ValueError(f"Curso con id {curso_id} no encontrado")
        asignatura = self.asignatura_repository.get_by_id(db, asignatura_id)
        if not asignatura:
            raise ValueError(f"Asignatura con id {asignatura_id} no encontrada")
        if horas_semanales <= 0:
            raise ValueError("Las horas semanales deben ser mayores a cero")
        try:
            obj = self.repository.create(
                db, curso_id=curso_id, asignatura_id=asignatura_id,
                horas_semanales=horas_semanales
            )
            db.commit()
            return obj
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al crear relación curso-asignatura: {e}") from e

    def obtener_por_id(self, db: Session, id: int):
        """Obtiene una relación curso-asignatura por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la relación.

        Returns:
            La relación encontrada o None.
        """
        return self.repository.get_by_id(db, id)

    def obtener_todos(self, db: Session):
        """Obtiene todas las relaciones curso-asignatura.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Lista de relaciones.
        """
        return self.repository.get_all(db)

    def contar(self, db: Session):
        """Obtiene el número total de relaciones curso-asignatura.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Número total de relaciones.
        """
        return self.repository.count(db)

    def obtener_por_curso(self, db: Session, curso_id: int):
        """Obtiene las asignaturas de un curso.

        Args:
            db: Sesión activa de base de datos.
            curso_id: ID del curso.

        Returns:
            Lista de relaciones del curso.
        """
        return self.repository.get_by_curso(db, curso_id)

    def obtener_por_asignatura(self, db: Session, asignatura_id: int):
        """Obtiene los cursos que tienen una asignatura.

        Args:
            db: Sesión activa de base de datos.
            asignatura_id: ID de la asignatura.

        Returns:
            Lista de relaciones de la asignatura.
        """
        return self.repository.get_by_asignatura(db, asignatura_id)

    def actualizar(self, db: Session, id: int,
                   curso_id: int | None = None,
                   asignatura_id: int | None = None,
                   horas_semanales: int | None = None):
        """Actualiza una relación curso-asignatura.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la relación.
            curso_id: Nuevo curso (opcional).
            asignatura_id: Nueva asignatura (opcional).
            horas_semanales: Nuevas horas semanales (opcional).

        Returns:
            La relación actualizada.

        Raises:
            ValueError: Si algún FK no existe, horas inválidas,
                       o la relación no existe.
        """
        if curso_id is not None:
            curso = self.curso_repository.get_by_id(db, curso_id)
            if not curso:
                raise ValueError(f"Curso con id {curso_id} no encontrado")
        if asignatura_id is not None:
            asignatura = self.asignatura_repository.get_by_id(db, asignatura_id)
            if not asignatura:
                raise ValueError(f"Asignatura con id {asignatura_id} no encontrada")
        if horas_semanales is not None and horas_semanales <= 0:
            raise ValueError("Las horas semanales deben ser mayores a cero")
        kwargs = {}
        if curso_id is not None:
            kwargs["curso_id"] = curso_id
        if asignatura_id is not None:
            kwargs["asignatura_id"] = asignatura_id
        if horas_semanales is not None:
            kwargs["horas_semanales"] = horas_semanales
        try:
            obj = self.repository.update(db, id, **kwargs)
            if not obj:
                raise ValueError(
                    f"Relación curso-asignatura con id {id} no encontrada"
                )
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(
                f"Error al actualizar relación curso-asignatura: {e}"
            ) from e

    def eliminar(self, db: Session, id: int):
        """Elimina una relación curso-asignatura.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la relación.

        Raises:
            ValueError: Si la relación no existe.
        """
        try:
            result = self.repository.delete(db, id)
            if not result:
                raise ValueError(
                    f"Relación curso-asignatura con id {id} no encontrada"
                )
            db.commit()
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(
                f"Error al eliminar relación curso-asignatura: {e}"
            ) from e
