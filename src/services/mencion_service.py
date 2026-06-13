"""Servicio de negocio para la entidad Mención."""
from sqlalchemy.orm import Session
from src.database.repositories.mencion_repository import MencionRepository


class MencionService:
    """Servicio que gestiona la lógica de negocio de menciones.

    Proporciona validación y operaciones CRUD sobre la entidad Mención.
    """

    def __init__(self, repository: MencionRepository | None = None):
        """Inicializa el servicio con un repositorio.

        Args:
            repository: Repositorio de menciones. Si no se provee, crea uno.
        """
        self.repository = repository or MencionRepository()

    def crear(self, db: Session, nombre: str):
        """Crea una nueva mención.

        Args:
            db: Sesión activa de base de datos.
            nombre: Nombre de la mención.

        Returns:
            La mención creada.

        Raises:
            ValueError: Si el nombre está vacío.
        """
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la mención no puede estar vacío")
        try:
            obj = self.repository.create(db, nombre=nombre.strip())
            db.commit()
            return obj
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al crear mención: {e}") from e

    def obtener_por_id(self, db: Session, id: int):
        """Obtiene una mención por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la mención.

        Returns:
            La mención encontrada o None.
        """
        return self.repository.get_by_id(db, id)

    def obtener_todos(self, db: Session):
        """Obtiene todas las menciones.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Lista de menciones.
        """
        return self.repository.get_all(db)

    def contar(self, db: Session):
        """Obtiene el número total de menciones.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Número total de menciones.
        """
        return self.repository.count(db)

    def actualizar(self, db: Session, id: int, nombre: str):
        """Actualiza el nombre de una mención.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la mención.
            nombre: Nuevo nombre de la mención.

        Returns:
            La mención actualizada.

        Raises:
            ValueError: Si el nombre está vacío o la mención no existe.
        """
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la mención no puede estar vacío")
        try:
            obj = self.repository.update(db, id, nombre=nombre.strip())
            if not obj:
                raise ValueError(f"Mención con id {id} no encontrada")
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al actualizar mención: {e}") from e

    def eliminar(self, db: Session, id: int):
        """Elimina una mención por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la mención.

        Raises:
            ValueError: Si la mención no existe.
        """
        try:
            result = self.repository.delete(db, id)
            if not result:
                raise ValueError(f"Mención con id {id} no encontrada")
            db.commit()
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al eliminar mención: {e}") from e
