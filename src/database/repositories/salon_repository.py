"""Repositorio para la entidad Salón."""
from src.database.models.models import SalonModel
from src.database.repositories.base import BaseRepository


class SalonRepository(BaseRepository):
    """Repositorio para operaciones CRUD de salones."""

    def __init__(self):
        super().__init__(SalonModel)
