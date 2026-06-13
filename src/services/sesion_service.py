"""Servicio de negocio para la entidad Sesión (bloques horarios)."""
from sqlalchemy.orm import Session
from src.database.repositories.sesion_repository import SesionRepository


class SesionService:
    """Servicio que gestiona la lógica de negocio de sesiones (bloques horarios)."""

    def __init__(self, repository: SesionRepository | None = None):
        self.repository = repository or SesionRepository()

    def crear(self, db: Session, dia: str, hora_inicio: str, hora_fin: str):
        """Crea una nueva sesión (bloque horario).

        Args:
            db: Sesión activa de base de datos.
            dia: Día de la semana.
            hora_inicio: Hora de inicio.
            hora_fin: Hora de fin.

        Returns:
            La sesión creada.

        Raises:
            ValueError: Si algún campo está vacío o hay superposición horaria.
        """
        if not dia or not dia.strip():
            raise ValueError("El día de la sesión no puede estar vacío")
        if not hora_inicio or not hora_inicio.strip():
            raise ValueError("La hora de inicio no puede estar vacía")
        if not hora_fin or not hora_fin.strip():
            raise ValueError("La hora de fin no puede estar vacía")
        if hora_inicio >= hora_fin:
            raise ValueError("La hora de inicio debe ser anterior a la hora de fin")
        superpuestas = self.repository.get_overlapping(
            db, dia.strip(), hora_inicio.strip(), hora_fin.strip()
        )
        if superpuestas:
            raise ValueError(
                f"Ya existe una sesión en {dia} de {hora_inicio} a {hora_fin} "
                "que se superpone con el horario solicitado"
            )
        try:
            obj = self.repository.create(
                db, dia=dia.strip(), hora_inicio=hora_inicio.strip(),
                hora_fin=hora_fin.strip()
            )
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al crear sesión: {e}") from e

    def obtener_por_id(self, db: Session, id: int):
        """Obtiene una sesión por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la sesión.

        Returns:
            La sesión encontrada o None.
        """
        return self.repository.get_by_id(db, id)

    def obtener_todos(self, db: Session):
        """Obtiene todas las sesiones.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Lista de sesiones.
        """
        return self.repository.get_all(db)

    def contar(self, db: Session):
        """Obtiene el número total de sesiones.

        Args:
            db: Sesión activa de base de datos.

        Returns:
            Número total de sesiones.
        """
        return self.repository.count(db)

    def verificar_superposicion(self, db: Session, dia: str,
                                  hora_inicio: str, hora_fin: str):
        """Verifica si existe una sesión superpuesta con el horario dado.

        Args:
            db: Sesión activa de base de datos.
            dia: Día de la semana.
            hora_inicio: Hora de inicio.
            hora_fin: Hora de fin.

        Returns:
            Lista de sesiones que se superponen.
        """
        return self.repository.get_overlapping(
            db, dia.strip(), hora_inicio.strip(), hora_fin.strip()
        )

    def obtener_por_dia(self, db: Session, dia: str):
        """Obtiene sesiones filtradas por día.

        Args:
            db: Sesión activa de base de datos.
            dia: Día a filtrar.

        Returns:
            Lista de sesiones del día especificado.
        """
        return self.repository.get_by_dia(db, dia)

    def actualizar(self, db: Session, id: int,
                   dia: str | None = None,
                   hora_inicio: str | None = None,
                   hora_fin: str | None = None):
        """Actualiza una sesión existente.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la sesión.
            dia: Nuevo día (opcional).
            hora_inicio: Nueva hora de inicio (opcional).
            hora_fin: Nueva hora de fin (opcional).

        Returns:
            La sesión actualizada.

        Raises:
            ValueError: Si algún campo es inválido, hay superposición,
                       o la sesión no existe.
        """
        if dia is not None and not dia.strip():
            raise ValueError("El día de la sesión no puede estar vacío")
        if hora_inicio is not None and not hora_inicio.strip():
            raise ValueError("La hora de inicio no puede estar vacía")
        if hora_fin is not None and not hora_fin.strip():
            raise ValueError("La hora de fin no puede estar vacía")
        existente = self.repository.get_by_id(db, id)
        if not existente:
            raise ValueError(f"Sesión con id {id} no encontrada")
        dia_final = dia.strip() if dia else existente.dia
        inicio_final = hora_inicio.strip() if hora_inicio else existente.hora_inicio
        fin_final = hora_fin.strip() if hora_fin else existente.hora_fin
        if inicio_final >= fin_final:
            raise ValueError("La hora de inicio debe ser anterior a la hora de fin")
        superpuestas = self.repository.get_overlapping(
            db, dia_final, inicio_final, fin_final, exclude_id=id
        )
        if superpuestas:
            raise ValueError(
                f"Los cambios causan superposición con otra sesión en {dia_final}"
            )
        kwargs = {}
        if dia is not None:
            kwargs["dia"] = dia.strip()
        if hora_inicio is not None:
            kwargs["hora_inicio"] = hora_inicio.strip()
        if hora_fin is not None:
            kwargs["hora_fin"] = hora_fin.strip()
        try:
            obj = self.repository.update(db, id, **kwargs)
            db.commit()
            return obj
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al actualizar sesión: {e}") from e

    def eliminar(self, db: Session, id: int):
        """Elimina una sesión por su ID.

        Args:
            db: Sesión activa de base de datos.
            id: Identificador de la sesión.

        Raises:
            ValueError: Si la sesión no existe.
        """
        try:
            result = self.repository.delete(db, id)
            if not result:
                raise ValueError(f"Sesión con id {id} no encontrada")
            db.commit()
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al eliminar sesión: {e}") from e
