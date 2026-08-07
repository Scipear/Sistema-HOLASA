"""Tests de creación para todos los repositorios del sistema HOLASA.

Cada test crea un registro y lo persiste con commit.
Son idempotentes: si el registro ya existe, el test se salta.
Los datos creados pueden inspeccionarse con rainfrog y
son utilizados por los tests de consulta, actualización y eliminación.
"""
import pytest
from src.database.models.models import (
    MencionModel,
    CursoModel,
    AsignaturaModel,
    ProfesorModel,
    SesionModel,
    SalonModel,
    CursoAsignaturaModel,
)
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


def test_crear_mencion(db_session):
    if db_session.query(MencionModel).filter(
        MencionModel.nombre == "Humanidades"
    ).first():
        pytest.skip("Mención 'Humanidades' ya existe")
    repo = MencionRepository()
    obj = repo.create(db_session, nombre="Humanidades")
    db_session.commit()
    assert obj.id is not None
    assert obj.nombre == "Humanidades"


def test_crear_curso(db_session):
    mencion = (
        db_session.query(MencionModel)
        .filter(MencionModel.nombre == "Ciencias")
        .first()
    )
    if not mencion:
        mencion = MencionModel(nombre="Ciencias")
        db_session.add(mencion)
        db_session.flush()
    if db_session.query(CursoModel).filter(
        CursoModel.seccion == "A", CursoModel.year == "2025"
    ).first():
        pytest.skip("Curso 'A/2025' ya existe")
    repo = CursoRepository()
    obj = repo.create(
        db_session, seccion="A", year="2025", mencion_id=mencion.id
    )
    db_session.commit()
    assert obj.id is not None
    assert obj.seccion == "A"
    assert obj.year == "2025"


def test_crear_asignatura(db_session):
    if db_session.query(AsignaturaModel).filter(
        AsignaturaModel.nombre == "Historia"
    ).first():
        pytest.skip("Asignatura 'Historia' ya existe")
    repo = AsignaturaRepository()
    obj = repo.create(db_session, nombre="Historia", tipo="Obligatoria")
    db_session.commit()
    assert obj.id is not None
    assert obj.nombre == "Historia"


def test_crear_profesor(db_session):
    if db_session.query(ProfesorModel).filter(
        ProfesorModel.nombre == "Carlos"
    ).first():
        pytest.skip("Profesor 'Carlos' ya existe")
    repo = ProfesorRepository()
    obj = repo.create(
        db_session,
        nombre="Carlos",
        apellido="Mendoza",
        estado=True,
    )
    db_session.commit()
    assert obj.id is not None
    assert obj.nombre == "Carlos"


def test_crear_sesion(db_session):
    if db_session.query(SesionModel).filter(
        SesionModel.dia == "Lunes",
        SesionModel.hora_inicio == "08:00",
        SesionModel.hora_fin == "09:00",
    ).first():
        pytest.skip("Sesión 'Lunes 08:00-09:00' ya existe")
    repo = SesionRepository()
    obj = repo.create(
        db_session, dia="Lunes", hora_inicio="08:00", hora_fin="09:00"
    )
    db_session.commit()
    assert obj.id is not None
    assert obj.dia == "Lunes"


def test_crear_salon(db_session):
    if db_session.query(SalonModel).filter(
        SalonModel.nombre == "Laboratorio 1"
    ).first():
        pytest.skip("Salón 'Laboratorio 1' ya existe")
    repo = SalonRepository()
    obj = repo.create(db_session, nombre="Laboratorio 1")
    db_session.commit()
    assert obj.id is not None
    assert obj.nombre == "Laboratorio 1"


def test_crear_curso_asignatura(db_session):
    mencion = (
        db_session.query(MencionModel)
        .filter(MencionModel.nombre == "Letras")
        .first()
    )
    if not mencion:
        mencion = MencionModel(nombre="Letras")
        db_session.add(mencion)
        db_session.flush()
    curso = (
        db_session.query(CursoModel)
        .filter(CursoModel.seccion == "B", CursoModel.year == "2025")
        .first()
    )
    if not curso:
        curso = CursoModel(seccion="B", year="2025", mencion_id=mencion.id)
        db_session.add(curso)
        db_session.flush()
    asignatura = (
        db_session.query(AsignaturaModel)
        .filter(AsignaturaModel.nombre == "Física")
        .first()
    )
    if not asignatura:
        asignatura = AsignaturaModel(nombre="Física", tipo="Optativa")
        db_session.add(asignatura)
        db_session.flush()
    if db_session.query(CursoAsignaturaModel).filter(
        CursoAsignaturaModel.curso_id == curso.id,
        CursoAsignaturaModel.asignatura_id == asignatura.id,
    ).first():
        pytest.skip("CursoAsignatura ya existe")
    repo = CursoAsignaturaRepository()
    obj = repo.create(
        db_session,
        curso_id=curso.id,
        asignatura_id=asignatura.id,
        horas_semanales=4,
    )
    db_session.commit()
    assert obj.id is not None
    assert obj.horas_semanales == 4


def test_crear_sesion_profesor(db_session):
    sesion = (
        db_session.query(SesionModel)
        .filter(
            SesionModel.dia == "Martes",
            SesionModel.hora_inicio == "10:00",
            SesionModel.hora_fin == "11:00",
        )
        .first()
    )
    if not sesion:
        sesion = SesionModel(
            dia="Martes", hora_inicio="10:00", hora_fin="11:00"
        )
        db_session.add(sesion)
        db_session.flush()
    profesor = (
        db_session.query(ProfesorModel)
        .filter(ProfesorModel.correo == "ana@test.com")
        .first()
    )
    if not profesor:
        profesor = ProfesorModel(
            nombre="Ana", apellido="López", correo="ana@test.com"
        )
        db_session.add(profesor)
        db_session.flush()
    repo = SesionProfesorRepository()
    if repo.exists(db_session, sesion.id, profesor.id):
        pytest.skip("Asignación sesión-profesor ya existe")
    obj = repo.create(
        db_session, sesion_id=sesion.id, profesor_id=profesor.id
    )
    db_session.commit()
    assert obj.id is not None


def test_crear_profesor_asignatura(db_session):
    profesor = (
        db_session.query(ProfesorModel)
        .filter(ProfesorModel.correo == "luis@test.com")
        .first()
    )
    if not profesor:
        profesor = ProfesorModel(
            nombre="Luis", apellido="García", correo="luis@test.com"
        )
        db_session.add(profesor)
        db_session.flush()
    mencion = (
        db_session.query(MencionModel)
        .filter(MencionModel.nombre == "Ingeniería")
        .first()
    )
    if not mencion:
        mencion = MencionModel(nombre="Ingeniería")
        db_session.add(mencion)
        db_session.flush()
    curso = (
        db_session.query(CursoModel)
        .filter(CursoModel.seccion == "C", CursoModel.year == "2025")
        .first()
    )
    if not curso:
        curso = CursoModel(seccion="C", year="2025", mencion_id=mencion.id)
        db_session.add(curso)
        db_session.flush()
    asignatura = (
        db_session.query(AsignaturaModel)
        .filter(AsignaturaModel.nombre == "Química")
        .first()
    )
    if not asignatura:
        asignatura = AsignaturaModel(nombre="Química", tipo="Obligatoria")
        db_session.add(asignatura)
        db_session.flush()
    ca = (
        db_session.query(CursoAsignaturaModel)
        .filter(
            CursoAsignaturaModel.curso_id == curso.id,
            CursoAsignaturaModel.asignatura_id == asignatura.id,
        )
        .first()
    )
    if not ca:
        ca = CursoAsignaturaModel(
            curso_id=curso.id,
            asignatura_id=asignatura.id,
            horas_semanales=3,
        )
        db_session.add(ca)
        db_session.flush()
    repo = ProfesorAsignaturaRepository()
    if repo.exists(db_session, profesor.id, ca.id):
        pytest.skip("Asignación profesor-asignatura ya existe")
    obj = repo.create(
        db_session, profesor_id=profesor.id, curso_asignatura_id=ca.id
    )
    db_session.commit()
    assert obj.id is not None
