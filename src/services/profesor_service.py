"""Servicio de negocio para la entidad Profesor."""
from sqlalchemy.orm import Session
from src.database.repositories.profesor_repository import ProfesorRepository


class ProfesorService:
    """Servicio que gestiona la lógica de negocio de profesores."""

    def __init__(self, repository: ProfesorRepository | None = None):
        self.repository = repository or ProfesorRepository()

    def crear(self, db: Session, nombre: str, apellido: str, estado: bool = True):
        """Crea un nuevo profesor.

        Args:
            db: Sesión activa de base de datos.
            nombre: Nombre del profesor.
            apellido: Apellido del profesor.
            estado: Estado activo/inactivo.

        Returns:
            El profesor creado.

        Raises:
            ValueError: Si nombre o apellido están vacíos, o el correo ya existe.
        """
        if not nombre or not nombre.strip():
            raise ValueError("El nombre del profesor no puede estar vacío")
        if not apellido or not apellido.strip():
            raise ValueError("El apellido del profesor no puede estar vacío")
        try:
            obj = self.repository.create(db, nombre=nombre.strip(), apellido=apellido.strip(), estado=estado)
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al crear profesor: {e}") from e

    def obtener_por_id(self, db: Session, id: int):
        """Obtiene un profesor por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador del profesor.

        Returns:
            El profesor encontrado o None.
        """
        return self.repository.get_by_id(db, id)

    def obtener_todos(self, db: Session):
        """Obtiene todos los profesores.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Lista de profesores.
        """
        return self.repository.get_all(db)

    def contar(self, db: Session):
        """Obtiene el número total de profesores.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Número total de profesores.
        """
        return self.repository.count(db)

    def obtener_por_apellido(self, db: Session, apellido: str):
        """Obtiene profesores filtrados por apellido.

        Args:
            db: Sesión activa de base de datos.
            apellido: Apellido a buscar.

        Returns:
            Lista de profesores con el apellido especificado.
        """
        return self.repository.get_by_apellido(db, apellido)

    def obtener_activos(self, db: Session):
        """Obtiene todos los profesores activos.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Lista de profesores activos.
        """
        return self.repository.get_activos(db)

    def actualizar(self, db: Session, id: int,
                   nombre: str | None = None,
                   apellido: str | None = None,
                   estado: bool | None = None):
        """Actualiza un profesor existente.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador del profesor.
            nombre: Nuevo nombre (opcional).
            apellido: Nuevo apellido (opcional).
            estado: Nuevo estado (opcional).

        Returns:
            El profesor actualizado.

        Raises:
            ValueError: Si algún campo es inválido, el correo ya existe,
                       o el profesor no existe.
        """
        if nombre is not None and not nombre.strip():
            raise ValueError("El nombre del profesor no puede estar vacío")
        if apellido is not None and not apellido.strip():
            raise ValueError("El apellido del profesor no puede estar vacío")
        kwargs = {}
        if nombre is not None:
            kwargs["nombre"] = nombre.strip()
        if apellido is not None:
            kwargs["apellido"] = apellido.strip()
        if estado is not None:
            kwargs["estado"] = estado
        try:
            obj = self.repository.update(db, id, **kwargs)
            if not obj:
                raise ValueError(f"Profesor con id {id} no encontrado")
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al actualizar profesor: {e}") from e

    def eliminar(self, db: Session, id: int):
        """Elimina un profesor por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador del profesor.

        Raises:
            ValueError: Si el profesor no existe.
        """
        try:
            result = self.repository.delete(db, id)
            if not result:
                raise ValueError(f"Profesor con id {id} no encontrado")
            db.commit()
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al eliminar profesor: {e}") from e
