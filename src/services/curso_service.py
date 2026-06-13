"""Servicio de negocio para la entidad Curso."""
from sqlalchemy.orm import Session
from src.database.repositories.curso_repository import CursoRepository
from src.database.repositories.mencion_repository import MencionRepository


class CursoService:
    """Servicio que gestiona la lógica de negocio de cursos."""

    def __init__(self, repository: CursoRepository | None = None,
                 mencion_repository: MencionRepository | None = None):
        self.repository = repository or CursoRepository()
        self.mencion_repository = mencion_repository or MencionRepository()

    def crear(self, db: Session, seccion: str, year: str,
              mencion_id: int | None = None):
        """Crea un nuevo curso.

        Args:
            db: Sesión activa de base de datos.
            seccion: Sección del curso.
            year: Año del curso.
            mencion_id: ID de la mención asociada (opcional).

        Returns:
            El curso creado.

        Raises:
            ValueError: Si seccion o year están vacíos, o la mención no existe.
        """
        if not seccion or not seccion.strip():
            raise ValueError("La sección del curso no puede estar vacía")
        if not year or not year.strip():
            raise ValueError("El año del curso no puede estar vacío")
        if mencion_id is not None:
            mencion = self.mencion_repository.get_by_id(db, mencion_id)
            if not mencion:
                raise ValueError(f"Mención con id {mencion_id} no encontrada")
        try:
            obj = self.repository.create(
                db, seccion=seccion.strip(), year=year.strip(),
                mencion_id=mencion_id
            )
            db.commit()
            return obj
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al crear curso: {e}") from e

    def obtener_por_id(self, db: Session, id: int):
        """Obtiene un curso por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador del curso.

        Returns:
            El curso encontrado o None.
        """
        return self.repository.get_by_id(db, id)

    def obtener_todos(self, db: Session):
        """Obtiene todos los cursos.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Lista de cursos.
        """
        return self.repository.get_all(db)

    def contar(self, db: Session):
        """Obtiene el número total de cursos.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Número total de cursos.
        """
        return self.repository.count(db)

    def obtener_por_year(self, db: Session, year: str):
        """Obtiene cursos filtrados por año.

        Args:
            db: Sesión activa de base de datos.
            year: Año a filtrar.

        Returns:
            Lista de cursos del año especificado.
        """
        return self.repository.get_by_year(db, year)

    def obtener_por_mencion(self, db: Session, mencion_id: int):
        """Obtiene cursos filtrados por mención.

        Args:
            db: Sesión activa de base de datos.
            mencion_id: ID de la mención.

        Returns:
            Lista de cursos de la mención especificada.
        """
        return self.repository.get_by_mencion(db, mencion_id)

    def actualizar(self, db: Session, id: int, seccion: str | None = None,
                   year: str | None = None,
                   mencion_id: int | None = None):
        """Actualiza un curso existente.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador del curso.
            seccion: Nueva sección (opcional).
            year: Nuevo año (opcional).
            mencion_id: Nueva mención (opcional, None elimina la mención).

        Returns:
            El curso actualizado.

        Raises:
            ValueError: Si algún campo es inválido o el curso no existe.
        """
        if seccion is not None and not seccion.strip():
            raise ValueError("La sección del curso no puede estar vacía")
        if year is not None and not year.strip():
            raise ValueError("El año del curso no puede estar vacío")
        if mencion_id is not None:
            mencion = self.mencion_repository.get_by_id(db, mencion_id)
            if not mencion:
                raise ValueError(f"Mención con id {mencion_id} no encontrada")
        kwargs = {}
        if seccion is not None:
            kwargs["seccion"] = seccion.strip()
        if year is not None:
            kwargs["year"] = year.strip()
        if mencion_id is not None:
            kwargs["mencion_id"] = mencion_id
        try:
            obj = self.repository.update(db, id, **kwargs)
            if not obj:
                raise ValueError(f"Curso con id {id} no encontrado")
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al actualizar curso: {e}") from e

    def eliminar(self, db: Session, id: int):
        """Elimina un curso por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador del curso.

        Raises:
            ValueError: Si el curso no existe.
        """
        try:
            result = self.repository.delete(db, id)
            if not result:
                raise ValueError(f"Curso con id {id} no encontrado")
            db.commit()
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al eliminar curso: {e}") from e
