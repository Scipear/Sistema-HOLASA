"""Repositorio base con operaciones CRUD genéricas."""
from sqlalchemy.orm import Session


class BaseRepository:
    """Implementación genérica del patrón repositorio.

    Proporciona operaciones básicas de creación, lectura, actualización
    y eliminación para cualquier modelo SQLAlchemy.

    Attributes:
        model_class: Clase del modelo SQLAlchemy asociada.
    """

    def __init__(self, model_class):
        """Inicializa el repositorio con la clase del modelo.

        Args:
            model_class: Clase del modelo SQLAlchemy.
        """
        self.model_class = model_class

    def create(self, db: Session, **kwargs):
        """Crea un nuevo registro en la base de datos.

        Args:
            db: Sesión activa de base de datos.
            **kwargs: Atributos del modelo a crear.

        Returns:
            La instancia del modelo creada.
        """
        obj = self.model_class(**kwargs)
        db.add(obj)
        db.flush()
        return obj

    def get_by_id(self, db: Session, id: int):
        """Obtiene un registro por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador del registro.

        Returns:
            La instancia del modelo o None si no existe.
        """
        return db.query(self.model_class).filter(self.model_class.id == id).first()

    def get_all(self, db: Session):
        """Obtiene todos los registros del modelo.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Lista de instancias del modelo.
        """
        return db.query(self.model_class).all()

    def update(self, db: Session, id: int, **kwargs):
        """Actualiza un registro existente.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador del registro a actualizar.
            **kwargs: Atributos a modificar.

        Returns:
            La instancia actualizada o None si no existe.
        """
        obj = self.get_by_id(db, id)
        if not obj:
            return None
        for key, value in kwargs.items():
            setattr(obj, key, value)
        db.flush()
        return obj

    def delete(self, db: Session, id: int):
        """Elimina un registro por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador del registro a eliminar.

        Returns:
            True si se eliminó, False si no existía.
        """
        obj = self.get_by_id(db, id)
        if not obj:
            return False
        db.delete(obj)
        db.flush()
        return True

    def count(self, db: Session):
        """Cuenta el total de registros.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Número total de registros.
        """
        return db.query(self.model_class).count()
