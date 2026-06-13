"""Repositorio para la entidad Mención."""
from src.database.models.models import MencionModel
from src.database.repositories.base import BaseRepository


class MencionRepository(BaseRepository):
    """Repositorio para operaciones CRUD de menciones."""

    def __init__(self):
        super().__init__(MencionModel)
