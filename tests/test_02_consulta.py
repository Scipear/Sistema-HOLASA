"""Tests de consulta para todos los repositorios del sistema HOLASA.

Cada test ejecuta operaciones de lectura sobre los datos
creados previamente por test_creacion.py. No modifica ni elimina datos.

Requiere ejecutar test_creacion.py primero para que existan datos.
"""
from sqlalchemy.orm import Session
from src.database.models.models import (
    MencionModel,
    CursoModel,
    AsignaturaModel,
    ProfesorModel,
    SesionModel,
    SalonModel,
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


# =============================================================================
# MencionRepository
# =============================================================================

def _primera_mencion(db: Session):
    return db.query(MencionModel).order_by(MencionModel.id).first()


def test_get_mencion_por_id(db_session):
    repo = MencionRepository()
    primera = _primera_mencion(db_session)
    assert primera is not None, "No hay datos. Ejecute test_creacion.py primero"
    obj = repo.get_by_id(db_session, primera.id)
    assert obj is not None
    assert obj.nombre == primera.nombre


def test_get_todas_las_menciones(db_session):
    repo = MencionRepository()
    resultado = repo.get_all(db_session)
    assert len(resultado) > 0


def test_count_menciones(db_session):
    repo = MencionRepository()
    assert repo.count(db_session) > 0


# =============================================================================
# CursoRepository
# =============================================================================

def _curso_vinculado(db: Session):
    return db.query(CursoModel).filter(
        CursoModel.mencion_id.isnot(None)
    ).first()


def _mencion_con_curso(db: Session):
    return db.query(MencionModel).join(CursoModel).first()


def test_get_curso_por_year(db_session):
    repo = CursoRepository()
    resultado = repo.get_by_year(db_session, "2025")
    assert len(resultado) > 0
    assert all(c.year == "2025" for c in resultado)


def test_get_cursos_por_mencion(db_session):
    repo = CursoRepository()
    mencion = _mencion_con_curso(db_session)
    assert mencion is not None
    resultado = repo.get_by_mencion(db_session, mencion.id)
    assert len(resultado) > 0


# =============================================================================
# AsignaturaRepository
# =============================================================================

def _asignatura_obligatoria(db: Session):
    return db.query(AsignaturaModel).filter(
        AsignaturaModel.tipo == "Obligatoria"
    ).first()


def test_get_asignaturas_por_tipo(db_session):
    repo = AsignaturaRepository()
    resultado = repo.get_by_tipo(db_session, "Obligatoria")
    assert len(resultado) > 0


# =============================================================================
# ProfesorRepository
# =============================================================================

def _profesor_con_sesion(db: Session):
    from src.database.models.models import SesionProfesorModel
    sp = db.query(SesionProfesorModel).first()
    if sp:
        return db.query(ProfesorModel).get(sp.profesor_id)
    return None


def _profesor_carlos(db: Session):
    return db.query(ProfesorModel).filter(
        ProfesorModel.correo == "carlos@test.com"
    ).first()


def test_get_profesor_por_apellido(db_session):
    repo = ProfesorRepository()
    resultado = repo.get_by_apellido(db_session, "Mendoza")
    assert len(resultado) > 0


def test_get_profesores_activos(db_session):
    repo = ProfesorRepository()
    resultado = repo.get_activos(db_session)
    assert len(resultado) > 0


def test_get_profesor_por_correo(db_session):
    repo = ProfesorRepository()
    obj = repo.get_by_correo(db_session, "carlos@test.com")
    assert obj is not None
    assert obj.correo == "carlos@test.com"


# =============================================================================
# SesionRepository
# =============================================================================

def _sesion_lunes(db: Session):
    return db.query(SesionModel).filter(SesionModel.dia == "Lunes").first()


def test_get_sesiones_por_dia(db_session):
    repo = SesionRepository()
    resultado = repo.get_by_dia(db_session, "Lunes")
    assert len(resultado) > 0


def test_get_overlapping_finds_overlap(db_session):
    lunes = _sesion_lunes(db_session)
    assert lunes is not None, "No hay sesión el Lunes"
    repo = SesionRepository()
    resultado = repo.get_overlapping(
        db_session, dia="Lunes",
        hora_inicio=lunes.hora_inicio,
        hora_fin=lunes.hora_fin,
    )
    assert len(resultado) > 0


def test_get_overlapping_adjacent_no_overlap(db_session):
    repo = SesionRepository()
    resultado = repo.get_overlapping(
        db_session, dia="Lunes", hora_inicio="09:00", hora_fin="10:00"
    )
    assert len(resultado) == 0


def test_get_overlapping_different_day(db_session):
    repo = SesionRepository()
    resultado = repo.get_overlapping(
        db_session, dia="Miércoles",
        hora_inicio="08:00", hora_fin="09:00"
    )
    assert len(resultado) == 0


# =============================================================================
# SalonRepository
# =============================================================================

def test_get_todos_los_salones(db_session):
    repo = SalonRepository()
    resultado = repo.get_all(db_session)
    assert len(resultado) > 0


def test_count_salones(db_session):
    repo = SalonRepository()
    assert repo.count(db_session) > 0


# =============================================================================
# SesionProfesorRepository
# =============================================================================

def _asignacion_sp(db: Session):
    from src.database.models.models import SesionProfesorModel
    return db.query(SesionProfesorModel).first()


def test_get_sesiones_por_profesor(db_session):
    repo = SesionProfesorRepository()
    asignacion = _asignacion_sp(db_session)
    assert asignacion is not None, "No hay asignaciones"
    resultado = repo.get_by_profesor(db_session, asignacion.profesor_id)
    assert len(resultado) > 0


def test_get_profesores_por_sesion(db_session):
    repo = SesionProfesorRepository()
    asignacion = _asignacion_sp(db_session)
    assert asignacion is not None
    resultado = repo.get_by_sesion(db_session, asignacion.sesion_id)
    assert len(resultado) > 0


def test_sesion_profesor_exists_true(db_session):
    repo = SesionProfesorRepository()
    asignacion = _asignacion_sp(db_session)
    assert asignacion is not None
    assert repo.exists(
        db_session, asignacion.sesion_id, asignacion.profesor_id
    ) is True


# =============================================================================
# CursoAsignaturaRepository
# =============================================================================

def _curso_con_asignatura(db: Session):
    from src.database.models.models import CursoAsignaturaModel
    ca = db.query(CursoAsignaturaModel).first()
    if ca:
        return ca
    return None


def test_get_asignaturas_por_curso(db_session):
    ca = _curso_con_asignatura(db_session)
    assert ca is not None
    repo = CursoAsignaturaRepository()
    resultado = repo.get_by_curso(db_session, ca.curso_id)
    assert len(resultado) > 0


def test_get_cursos_por_asignatura(db_session):
    ca = _curso_con_asignatura(db_session)
    assert ca is not None
    repo = CursoAsignaturaRepository()
    resultado = repo.get_by_asignatura(db_session, ca.asignatura_id)
    assert len(resultado) > 0


# =============================================================================
# ProfesorAsignaturaRepository
# =============================================================================

def _asignacion_pa(db: Session):
    from src.database.models.models import ProfesorAsignaturaModel
    return db.query(ProfesorAsignaturaModel).first()


def test_get_profesor_asignatura_por_profesor(db_session):
    repo = ProfesorAsignaturaRepository()
    asignacion = _asignacion_pa(db_session)
    assert asignacion is not None
    resultado = repo.get_by_profesor(db_session, asignacion.profesor_id)
    assert len(resultado) > 0


def test_get_profesores_por_curso_asignatura(db_session):
    repo = ProfesorAsignaturaRepository()
    asignacion = _asignacion_pa(db_session)
    assert asignacion is not None
    resultado = repo.get_by_curso_asignatura(
        db_session, asignacion.curso_asignatura_id
    )
    assert len(resultado) > 0


def test_profesor_asignatura_exists_true(db_session):
    repo = ProfesorAsignaturaRepository()
    asignacion = _asignacion_pa(db_session)
    assert asignacion is not None
    assert repo.exists(
        db_session, asignacion.profesor_id, asignacion.curso_asignatura_id
    ) is True
