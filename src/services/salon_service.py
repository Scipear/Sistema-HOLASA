"""Servicio de negocio para la entidad Salón."""
from sqlalchemy.orm import Session
from src.database.repositories.salon_repository import SalonRepository


class SalonService:
    """Servicio que gestiona la lógica de negocio de salones."""

    def __init__(self, repository: SalonRepository | None = None):
        self.repository = repository or SalonRepository()

    def crear(self, db: Session, nombre: str, tipo: str):
        """Crea un nuevo salón.

        Args:
            db: Sesión activa de base de datos.
            nombre: Nombre del salón.
            tipo: Tipo de salón (General, Taller).

        Returns:
            El salón creado.

        Raises:
            ValueError: Si el nombre está vacío.
        """
        if not nombre or not nombre.strip():
            raise ValueError("El nombre del salón no puede estar vacío")
        try:
            obj = self.repository.create(db, nombre=nombre.strip(), tipo=tipo.strip())
            db.commit()
            return obj
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al crear salón: {e}") from e

    def obtener_por_id(self, db: Session, id: int):
        """Obtiene un salón por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador del salón.

        Returns:
            El salón encontrado o None.
        """
        return self.repository.get_by_id(db, id)

    def obtener_todos(self, db: Session):
        """Obtiene todos los salones.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Lista de salones.
        """
        return self.repository.get_all(db)

    def contar(self, db: Session):
        """Obtiene el número total de salones.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Número total de salones.
        """
        return self.repository.count(db)

    def actualizar(self, db: Session, id: int, nombre: str, tipo: str):
        """Actualiza el nombre de un salón.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador del salón.
            nombre: Nuevo nombre del salón.
            tipo: Nuevo tipo de salón (General, Taller).

        Returns:
            El salón actualizado.

        Raises:
            ValueError: Si el nombre o el tipo están vacíos o el salón no existe.
        """
        if not nombre or not nombre.strip():
            raise ValueError("El nombre del salón no puede estar vacío")
        if not tipo or not tipo.strip():
            raise ValueError("El tipo del salón no puede estar vacío")
        try:
            obj = self.repository.update(db, id, nombre=nombre.strip(), tipo=tipo.strip())
            if not obj:
                raise ValueError(f"Salón con id {id} no encontrado")
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al actualizar salón: {e}") from e

    def eliminar(self, db: Session, id: int):
        """Elimina un salón por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador del salón.

        Raises:
            ValueError: Si el salón no existe.
        """
        try:
            result = self.repository.delete(db, id)
            if not result:
                raise ValueError(f"Salón con id {id} no encontrado")
            db.commit()
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al eliminar salón: {e}") from e
