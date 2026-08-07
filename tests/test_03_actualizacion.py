"""Tests de actualización para los repositorios del sistema HOLASA.

Cada test modifica un registro existente creado por test_creacion.py.
Requiere ejecutar test_creacion.py primero para que existan datos.
"""
from src.database.repositories.mencion_repository import MencionRepository
from src.database.repositories.curso_repository import CursoRepository
from src.database.repositories.asignatura_repository import AsignaturaRepository
from src.database.repositories.profesor_repository import ProfesorRepository
from src.database.repositories.sesion_repository import SesionRepository
from src.database.repositories.salon_repository import SalonRepository
from src.database.repositories.curso_asignatura_repository import (
    CursoAsignaturaRepository,
)


def test_actualizar_mencion(db_session):
    repo = MencionRepository()
    todas = repo.get_all(db_session)
    assert len(todas) > 0, "No hay datos. Ejecute test_creacion.py primero"
    obj = repo.update(db_session, todas[0].id, nombre="**MODIFICADO**")
    db_session.commit()
    assert obj is not None
    assert obj.nombre == "**MODIFICADO**"
    actualizado = repo.get_by_id(db_session, todas[0].id)
    assert actualizado.nombre == "**MODIFICADO**"


def test_actualizar_curso(db_session):
    repo = CursoRepository()
    todos = repo.get_all(db_session)
    assert len(todos) > 0
    obj = repo.update(db_session, todos[0].id, seccion="**X**")
    db_session.commit()
    assert obj is not None
    assert obj.seccion == "**X**"


def test_actualizar_asignatura(db_session):
    repo = AsignaturaRepository()
    todas = repo.get_all(db_session)
    assert len(todas) > 0
    obj = repo.update(db_session, todas[0].id, tipo="**MODIFICADO**")
    db_session.commit()
    assert obj is not None
    assert obj.tipo == "**MODIFICADO**"


# def test_actualizar_profesor(db_session):
#     repo = ProfesorRepository()
#     todos = repo.get_all(db_session)
#     assert len(todos) > 0
#     obj = repo.update(
#         db_session, todos[0].id, telefono="000-0000"
#     )
#     db_session.commit()
#     assert obj is not None
#     assert obj.telefono == "000-0000"


def test_actualizar_sesion(db_session):
    repo = SesionRepository()
    todas = repo.get_all(db_session)
    assert len(todas) > 0
    obj = repo.update(
        db_session, todas[0].id, hora_inicio="99:99", hora_fin="99:99"
    )
    db_session.commit()
    assert obj is not None
    assert obj.hora_inicio == "99:99"
    assert obj.hora_fin == "99:99"


def test_actualizar_salon(db_session):
    repo = SalonRepository()
    todos = repo.get_all(db_session)
    assert len(todos) > 0
    obj = repo.update(db_session, todos[0].id, nombre="**MODIFICADO**")
    db_session.commit()
    assert obj is not None
    assert obj.nombre == "**MODIFICADO**"


def test_actualizar_curso_asignatura(db_session):
    repo = CursoAsignaturaRepository()
    todos = repo.get_all(db_session)
    assert len(todos) > 0
    obj = repo.update(db_session, todos[0].id, horas_semanales=999)
    db_session.commit()
    assert obj is not None
    assert obj.horas_semanales == 999
