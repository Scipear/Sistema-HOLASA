"""Tests de eliminación para los repositorios del sistema HOLASA.

Cada test elimina un registro existente creado por test_creacion.py.
Requiere ejecutar test_creacion.py primero para que existan datos.
"""
from src.database.repositories.mencion_repository import MencionRepository
from src.database.repositories.curso_repository import CursoRepository
from src.database.repositories.asignatura_repository import AsignaturaRepository
from src.database.repositories.profesor_repository import ProfesorRepository
from src.database.repositories.sesion_repository import SesionRepository
from src.database.repositories.salon_repository import SalonRepository
from src.database.repositories.sesion_profesor_repository import (
    SesionProfesorRepository,
)
from src.database.repositories.curso_asignatura_repository import (
    CursoAsignaturaRepository,
)
from src.database.repositories.profesor_asignatura_repository import (
    ProfesorAsignaturaRepository,
)


# =============================================================================
# MencionRepository
# =============================================================================

def test_eliminar_mencion(db_session):
    repo = MencionRepository()
    todas = repo.get_all(db_session)
    assert len(todas) > 0, "No hay datos. Ejecute test_creacion.py primero"
    id_original = todas[0].id
    assert repo.delete(db_session, id_original) is True
    db_session.commit()
    assert repo.get_by_id(db_session, id_original) is None


def test_eliminar_mencion_inexistente(db_session):
    repo = MencionRepository()
    assert repo.delete(db_session, 99999) is False


# =============================================================================
# CursoRepository
# =============================================================================

def test_eliminar_curso(db_session):
    repo = CursoRepository()
    todos = repo.get_all(db_session)
    assert len(todos) > 0
    id_original = todos[0].id
    assert repo.delete(db_session, id_original) is True
    db_session.commit()
    assert repo.get_by_id(db_session, id_original) is None


# =============================================================================
# AsignaturaRepository
# =============================================================================

def test_eliminar_asignatura(db_session):
    repo = AsignaturaRepository()
    todas = repo.get_all(db_session)
    assert len(todas) > 0
    id_original = todas[0].id
    assert repo.delete(db_session, id_original) is True
    db_session.commit()
    assert repo.get_by_id(db_session, id_original) is None


# =============================================================================
# ProfesorRepository
# =============================================================================

def test_eliminar_profesor(db_session):
    repo = ProfesorRepository()
    todos = repo.get_all(db_session)
    assert len(todos) > 0
    id_original = todos[0].id
    assert repo.delete(db_session, id_original) is True
    db_session.commit()
    assert repo.get_by_id(db_session, id_original) is None


# =============================================================================
# SesionRepository
# =============================================================================

def test_eliminar_sesion(db_session):
    repo = SesionRepository()
    todas = repo.get_all(db_session)
    assert len(todas) > 0
    id_original = todas[0].id
    assert repo.delete(db_session, id_original) is True
    db_session.commit()
    assert repo.get_by_id(db_session, id_original) is None


# =============================================================================
# SalonRepository
# =============================================================================

def test_eliminar_salon(db_session):
    repo = SalonRepository()
    todos = repo.get_all(db_session)
    assert len(todos) > 0
    id_original = todos[0].id
    assert repo.delete(db_session, id_original) is True
    db_session.commit()
    assert repo.get_by_id(db_session, id_original) is None


# =============================================================================
# SesionProfesorRepository
# =============================================================================

def test_eliminar_sesion_profesor(db_session):
    repo = SesionProfesorRepository()
    todos = repo.get_all(db_session)
    assert len(todos) > 0
    id_original = todos[0].id
    assert repo.delete(db_session, id_original) is True
    db_session.commit()
    assert repo.get_by_id(db_session, id_original) is None


# =============================================================================
# CursoAsignaturaRepository
# =============================================================================

def test_eliminar_curso_asignatura(db_session):
    repo = CursoAsignaturaRepository()
    todos = repo.get_all(db_session)
    assert len(todos) > 0
    id_original = todos[0].id
    assert repo.delete(db_session, id_original) is True
    db_session.commit()
    assert repo.get_by_id(db_session, id_original) is None


# =============================================================================
# ProfesorAsignaturaRepository
# =============================================================================

def test_eliminar_profesor_asignatura(db_session):
    repo = ProfesorAsignaturaRepository()
    todos = repo.get_all(db_session)
    assert len(todos) > 0
    id_original = todos[0].id
    assert repo.delete(db_session, id_original) is True
    db_session.commit()
    assert repo.get_by_id(db_session, id_original) is None
