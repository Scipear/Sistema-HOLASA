"""Servicio de negocio para la entidad Asignatura."""
from sqlalchemy.orm import Session
from src.database.repositories.asignatura_repository import AsignaturaRepository


class AsignaturaService:
    """Servicio que gestiona la lógica de negocio de asignaturas."""

    def __init__(self, repository: AsignaturaRepository | None = None):
        self.repository = repository or AsignaturaRepository()

    def crear(self, db: Session, nombre: str, tipo: str):
        """Crea una nueva asignatura.

        Args:
            db: Sesión activa de base de datos.
            nombre: Nombre de la asignatura.
            tipo: Tipo de asignatura.

        Returns:
            La asignatura creada.

        Raises:
            ValueError: Si nombre o tipo están vacíos.
        """
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la asignatura no puede estar vacío")
        if not tipo or not tipo.strip():
            raise ValueError("El tipo de asignatura no puede estar vacío")
        try:
            obj = self.repository.create(
                db, nombre=nombre.strip(), tipo=tipo.strip()
            )
            db.commit()
            return obj
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al crear asignatura: {e}") from e

    def obtener_por_id(self, db: Session, id: int):
        """Obtiene una asignatura por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la asignatura.

        Returns:
            La asignatura encontrada o None.
        """
        return self.repository.get_by_id(db, id)

    def obtener_todos(self, db: Session):
        """Obtiene todas las asignaturas.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Lista de asignaturas.
        """
        return self.repository.get_all(db)

    def contar(self, db: Session):
        """Obtiene el número total de asignaturas.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Número total de asignaturas.
        """
        return self.repository.count(db)

    def obtener_por_tipo(self, db: Session, tipo: str):
        """Obtiene asignaturas filtradas por tipo.

        Args:
            db: Sesión activa de base de datos.
            tipo: Tipo de asignatura a filtrar.

        Returns:
            Lista de asignaturas del tipo especificado.
        """
        return self.repository.get_by_tipo(db, tipo)

    def actualizar(self, db: Session, id: int,
                   nombre: str | None = None, tipo: str | None = None):
        """Actualiza una asignatura existente.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la asignatura.
            nombre: Nuevo nombre (opcional).
            tipo: Nuevo tipo (opcional).

        Returns:
            La asignatura actualizada.

        Raises:
            ValueError: Si algún campo es inválido o la asignatura no existe.
        """
        if nombre is not None and not nombre.strip():
            raise ValueError("El nombre de la asignatura no puede estar vacío")
        if tipo is not None and not tipo.strip():
            raise ValueError("El tipo de asignatura no puede estar vacío")
        kwargs = {}
        if nombre is not None:
            kwargs["nombre"] = nombre.strip()
        if tipo is not None:
            kwargs["tipo"] = tipo.strip()
        try:
            obj = self.repository.update(db, id, **kwargs)
            if not obj:
                raise ValueError(f"Asignatura con id {id} no encontrada")
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al actualizar asignatura: {e}") from e

    def eliminar(self, db: Session, id: int):
        """Elimina una asignatura por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la asignatura.

        Raises:
            ValueError: Si la asignatura no existe.
        """
        try:
            result = self.repository.delete(db, id)
            if not result:
                raise ValueError(f"Asignatura con id {id} no encontrada")
            db.commit()
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al eliminar asignatura: {e}") from e
