"""Mock de la capa de servicios para probar el service layer manualmente."""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.database.connection import Base

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_HOLASA.sqlite3")

from src.services.mencion_service import MencionService
from src.services.curso_service import CursoService
from src.services.asignatura_service import AsignaturaService
from src.services.profesor_service import ProfesorService
from src.services.sesion_service import SesionService
from src.services.salon_service import SalonService
from src.services.sesion_profesor_service import SesionProfesorService
from src.services.curso_asignatura_service import CursoAsignaturaService
from src.services.profesor_asignatura_service import ProfesorAsignaturaService


# ---------------------------------------------------------------------------
# Sesión
# ---------------------------------------------------------------------------

def abrir_sesion() -> Session:
    """Abre una sesión de base de datos. Crea tablas si no existen."""
    engine = create_engine(f"sqlite:///{TEST_DB_PATH}")
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    return TestSession()


def cerrar_sesion(db: Session):
    """Cierra la sesión de base de datos."""
    db.close()


# ---------------------------------------------------------------------------
# Mención
# ---------------------------------------------------------------------------

def crear_mencion(db: Session, nombre: str):
    service = MencionService()
    obj = service.crear(db, nombre=nombre)
    print(f"Mención creada: id={obj.id}, nombre={obj.nombre}")
    return obj


def obtener_mencion(db: Session, id: int):
    service = MencionService()
    obj = service.obtener_por_id(db, id)
    if obj:
        print(f"Mención: id={obj.id}, nombre={obj.nombre}")
    else:
        print(f"Mención {id} no encontrada")
    return obj


def listar_menciones(db: Session):
    service = MencionService()
    lista = service.obtener_todos(db)
    print(f"Menciones ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, nombre={o.nombre}")
    return lista


def actualizar_mencion(db: Session, id: int, nombre: str):
    service = MencionService()
    try:
        obj = service.actualizar(db, id, nombre=nombre)
        print(f"Mención actualizada: id={obj.id}, nombre={obj.nombre}")
        return obj
    except ValueError as e:
        print(str(e))
        return None


def eliminar_mencion(db: Session, id: int):
    service = MencionService()
    try:
        service.eliminar(db, id)
        print(f"Mención {id} eliminada")
    except ValueError as e:
        print(str(e))


# ---------------------------------------------------------------------------
# Curso
# ---------------------------------------------------------------------------

def crear_curso(db: Session, seccion: str, year: str,
                mencion_id: int | None = None):
    service = CursoService()
    obj = service.crear(db, seccion=seccion, year=year, mencion_id=mencion_id)
    print(f"Curso creado: id={obj.id}, {obj.seccion}/{obj.year}")
    return obj


def listar_cursos(db: Session):
    service = CursoService()
    lista = service.obtener_todos(db)
    print(f"Cursos ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, {o.seccion}/{o.year}, mencion_id={o.mencion_id}")
    return lista


def obtener_curso(db: Session, id: int):
    service = CursoService()
    obj = service.obtener_por_id(db, id)
    if obj:
        print(f"Curso: id={obj.id}, {obj.seccion}/{obj.year}")
    else:
        print(f"Curso {id} no encontrado")
    return obj


def cursos_por_year(db: Session, year: str):
    service = CursoService()
    lista = service.obtener_por_year(db, year)
    print(f"Cursos de {year} ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, {o.seccion}/{o.year}")
    return lista


def actualizar_curso(db: Session, id: int, seccion: str | None = None,
                     year: str | None = None,
                     mencion_id: int | None = None):
    service = CursoService()
    try:
        obj = service.actualizar(db, id, seccion=seccion, year=year,
                                 mencion_id=mencion_id)
        print(f"Curso actualizado: id={obj.id}, {obj.seccion}/{obj.year}")
        return obj
    except ValueError as e:
        print(str(e))
        return None


def eliminar_curso(db: Session, id: int):
    service = CursoService()
    try:
        service.eliminar(db, id)
        print(f"Curso {id} eliminado")
    except ValueError as e:
        print(str(e))


# ---------------------------------------------------------------------------
# Asignatura
# ---------------------------------------------------------------------------

def crear_asignatura(db: Session, nombre: str, tipo: str):
    service = AsignaturaService()
    obj = service.crear(db, nombre=nombre, tipo=tipo)
    print(f"Asignatura creada: id={obj.id}, {obj.nombre} ({obj.tipo})")
    return obj


def obtener_asignatura(db: Session, id: int):
    service = AsignaturaService()
    obj = service.obtener_por_id(db, id)
    if obj:
        print(f"Asignatura: id={obj.id}, {obj.nombre} ({obj.tipo})")
    else:
        print(f"Asignatura {id} no encontrada")
    return obj


def listar_asignaturas(db: Session):
    service = AsignaturaService()
    lista = service.obtener_todos(db)
    print(f"Asignaturas ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, {o.nombre} ({o.tipo})")
    return lista


def actualizar_asignatura(db: Session, id: int, nombre: str | None = None,
                          tipo: str | None = None):
    service = AsignaturaService()
    try:
        obj = service.actualizar(db, id, nombre=nombre, tipo=tipo)
        print(f"Asignatura actualizada: id={obj.id}, {obj.nombre} ({obj.tipo})")
        return obj
    except ValueError as e:
        print(str(e))
        return None


def eliminar_asignatura(db: Session, id: int):
    service = AsignaturaService()
    try:
        service.eliminar(db, id)
        print(f"Asignatura {id} eliminada")
    except ValueError as e:
        print(str(e))


# ---------------------------------------------------------------------------
# Profesor
# ---------------------------------------------------------------------------

def crear_profesor(db: Session, nombre: str, apellido: str,
                   telefono: str | None = None,
                   correo: str | None = None):
    service = ProfesorService()
    obj = service.crear(db, nombre=nombre, apellido=apellido,
                        telefono=telefono, correo=correo)
    print(f"Profesor creado: id={obj.id}, {obj.nombre} {obj.apellido}")
    return obj


def obtener_profesor(db: Session, id: int):
    service = ProfesorService()
    obj = service.obtener_por_id(db, id)
    if obj:
        print(f"Profesor: id={obj.id}, {obj.nombre} {obj.apellido}")
    else:
        print(f"Profesor {id} no encontrado")
    return obj


def listar_profesores(db: Session):
    service = ProfesorService()
    lista = service.obtener_todos(db)
    print(f"Profesores ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, {o.nombre} {o.apellido}, correo={o.correo}")
    return lista


def profesores_activos(db: Session):
    service = ProfesorService()
    lista = service.obtener_activos(db)
    print(f"Profesores activos ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, {o.nombre} {o.apellido}")
    return lista


def actualizar_profesor(db: Session, id: int,
                        nombre: str | None = None,
                        apellido: str | None = None,
                        telefono: str | None = None,
                        correo: str | None = None,
                        estado: bool | None = None):
    service = ProfesorService()
    try:
        obj = service.actualizar(db, id, nombre=nombre, apellido=apellido,
                                 telefono=telefono, correo=correo,
                                 estado=estado)
        print(f"Profesor actualizado: id={obj.id}, {obj.nombre} {obj.apellido}")
        return obj
    except ValueError as e:
        print(str(e))
        return None


def eliminar_profesor(db: Session, id: int):
    service = ProfesorService()
    try:
        service.eliminar(db, id)
        print(f"Profesor {id} eliminado")
    except ValueError as e:
        print(str(e))


# ---------------------------------------------------------------------------
# Sesión
# ---------------------------------------------------------------------------

def crear_sesion(db: Session, dia: str, hora_inicio: str, hora_fin: str):
    service = SesionService()
    obj = service.crear(db, dia=dia, hora_inicio=hora_inicio,
                        hora_fin=hora_fin)
    print(f"Sesión creada: id={obj.id}, {obj.dia} {obj.hora_inicio}-{obj.hora_fin}")
    return obj


def obtener_sesion(db: Session, id: int):
    service = SesionService()
    obj = service.obtener_por_id(db, id)
    if obj:
        print(f"Sesión: id={obj.id}, {obj.dia} {obj.hora_inicio}-{obj.hora_fin}")
    else:
        print(f"Sesión {id} no encontrada")
    return obj


def listar_sesiones(db: Session):
    service = SesionService()
    lista = service.obtener_todos(db)
    print(f"Sesiones ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, {o.dia} {o.hora_inicio}-{o.hora_fin}")
    return lista


def sesiones_por_dia(db: Session, dia: str):
    service = SesionService()
    lista = service.obtener_por_dia(db, dia)
    print(f"Sesiones de {dia} ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, {o.hora_inicio}-{o.hora_fin}")
    return lista


def verificar_overlap(db: Session, dia: str, hora_inicio: str, hora_fin: str):
    service = SesionService()
    overlaps = service.verificar_superposicion(db, dia, hora_inicio, hora_fin)
    if overlaps:
        print(f"Superposición detectada en {dia}:")
        for o in overlaps:
            print(f"  {o.hora_inicio}-{o.hora_fin}")
    else:
        print(f"No hay superposición en {dia} {hora_inicio}-{hora_fin}")


def actualizar_sesion(db: Session, id: int, dia: str | None = None,
                      hora_inicio: str | None = None,
                      hora_fin: str | None = None):
    service = SesionService()
    try:
        obj = service.actualizar(db, id, dia=dia, hora_inicio=hora_inicio,
                                 hora_fin=hora_fin)
        print(f"Sesión actualizada: id={obj.id}")
        return obj
    except ValueError as e:
        print(str(e))
        return None


def eliminar_sesion(db: Session, id: int):
    service = SesionService()
    try:
        service.eliminar(db, id)
        print(f"Sesión {id} eliminada")
    except ValueError as e:
        print(str(e))


# ---------------------------------------------------------------------------
# Salón
# ---------------------------------------------------------------------------

def crear_salon(db: Session, nombre: str):
    service = SalonService()
    obj = service.crear(db, nombre=nombre)
    print(f"Salón creado: id={obj.id}, {obj.nombre}")
    return obj


def obtener_salon(db: Session, id: int):
    service = SalonService()
    obj = service.obtener_por_id(db, id)
    if obj:
        print(f"Salón: id={obj.id}, {obj.nombre}")
    else:
        print(f"Salón {id} no encontrado")
    return obj


def listar_salones(db: Session):
    service = SalonService()
    lista = service.obtener_todos(db)
    print(f"Salones ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, {o.nombre}")
    return lista


def actualizar_salon(db: Session, id: int, nombre: str):
    service = SalonService()
    try:
        obj = service.actualizar(db, id, nombre=nombre)
        print(f"Salón actualizado: id={obj.id}, {obj.nombre}")
        return obj
    except ValueError as e:
        print(str(e))
        return None


def eliminar_salon(db: Session, id: int):
    service = SalonService()
    try:
        service.eliminar(db, id)
        print(f"Salón {id} eliminado")
    except ValueError as e:
        print(str(e))


# ---------------------------------------------------------------------------
# CursoAsignatura
# ---------------------------------------------------------------------------

def asignar_asignatura_a_curso(db: Session, curso_id: int,
                               asignatura_id: int,
                               horas_semanales: int):
    service = CursoAsignaturaService()
    obj = service.crear(db, curso_id=curso_id, asignatura_id=asignatura_id,
                        horas_semanales=horas_semanales)
    print(f"Asignatura asignada a curso: id={obj.id}, horas={obj.horas_semanales}")
    return obj


def obtener_curso_asignatura(db: Session, id: int):
    service = CursoAsignaturaService()
    obj = service.obtener_por_id(db, id)
    if obj:
        print(f"Curso-Asignatura: id={obj.id}, curso_id={obj.curso_id}, "
              f"asig_id={obj.asignatura_id}, horas={obj.horas_semanales}")
    else:
        print(f"Curso-Asignatura {id} no encontrado")
    return obj


def listar_curso_asignaturas(db: Session):
    service = CursoAsignaturaService()
    lista = service.obtener_todos(db)
    print(f"Curso-Asignaturas ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, curso_id={o.curso_id}, asig_id={o.asignatura_id}, "
              f"horas={o.horas_semanales}")
    return lista


def actualizar_curso_asignatura(db: Session, id: int,
                                curso_id: int | None = None,
                                asignatura_id: int | None = None,
                                horas_semanales: int | None = None):
    service = CursoAsignaturaService()
    try:
        obj = service.actualizar(db, id, curso_id=curso_id,
                                 asignatura_id=asignatura_id,
                                 horas_semanales=horas_semanales)
        print(f"Curso-Asignatura actualizado: id={obj.id}, "
              f"horas={obj.horas_semanales}")
        return obj
    except ValueError as e:
        print(str(e))
        return None


def eliminar_curso_asignatura(db: Session, id: int):
    service = CursoAsignaturaService()
    try:
        service.eliminar(db, id)
        print(f"Curso-Asignatura {id} eliminado")
    except ValueError as e:
        print(str(e))


# ---------------------------------------------------------------------------
# SesionProfesor
# ---------------------------------------------------------------------------

def asignar_profesor_a_sesion(db: Session, sesion_id: int, profesor_id: int):
    service = SesionProfesorService()
    obj = service.asignar(db, sesion_id=sesion_id, profesor_id=profesor_id)
    print(f"Profesor {profesor_id} asignado a sesión {sesion_id}: id={obj.id}")


def listar_sesiones_profesores(db: Session):
    service = SesionProfesorService()
    lista = service.obtener_todos(db)
    print(f"Asignaciones sesión-profesor ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, sesion_id={o.sesion_id}, profesor_id={o.profesor_id}")
    return lista


def obtener_sesion_profesor(db: Session, id: int):
    service = SesionProfesorService()
    obj = service.obtener_por_id(db, id)
    if obj:
        print(f"Asignación: id={obj.id}, sesion_id={obj.sesion_id}, "
              f"profesor_id={obj.profesor_id}")
    else:
        print(f"Asignación sesión-profesor {id} no encontrada")
    return obj


def sesiones_de_profesor(db: Session, profesor_id: int):
    service = SesionProfesorService()
    lista = service.obtener_por_profesor(db, profesor_id)
    print(f"Sesiones del profesor {profesor_id} ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, sesion_id={o.sesion_id}")
    return lista


def eliminar_sesion_profesor(db: Session, id: int):
    service = SesionProfesorService()
    try:
        service.desasignar(db, id)
        print(f"Asignación sesión-profesor {id} eliminada")
    except ValueError as e:
        print(str(e))


# ---------------------------------------------------------------------------
# ProfesorAsignatura
# ---------------------------------------------------------------------------

def asignar_profesor_a_curso_asignatura(db: Session, profesor_id: int,
                                        curso_asignatura_id: int):
    service = ProfesorAsignaturaService()
    obj = service.asignar(db, profesor_id=profesor_id,
                          curso_asignatura_id=curso_asignatura_id)
    print(f"Profesor {profesor_id} asignado a CA {curso_asignatura_id}: "
          f"id={obj.id}")


def listar_profesores_asignaturas(db: Session):
    service = ProfesorAsignaturaService()
    lista = service.obtener_todos(db)
    print(f"Asignaciones profesor-CA ({len(lista)}):")
    for o in lista:
        print(f"  id={o.id}, profesor_id={o.profesor_id}, "
              f"curso_asignatura_id={o.curso_asignatura_id}")
    return lista


def obtener_profesor_asignatura(db: Session, id: int):
    service = ProfesorAsignaturaService()
    obj = service.obtener_por_id(db, id)
    if obj:
        print(f"Asignación: id={obj.id}, profesor_id={obj.profesor_id}, "
              f"curso_asignatura_id={obj.curso_asignatura_id}")
    else:
        print(f"Asignación profesor-CA {id} no encontrada")
    return obj


def eliminar_profesor_asignatura(db: Session, id: int):
    service = ProfesorAsignaturaService()
    try:
        service.desasignar(db, id)
        print(f"Asignación profesor-CA {id} eliminada")
    except ValueError as e:
        print(str(e))


# ---------------------------------------------------------------------------
# Demo rápida
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    db = abrir_sesion()

    print("── 1. CREACIÓN ──\n")

    m = crear_mencion(db, "Ciencias")

    a = crear_asignatura(db, "Álgebra", "Obligatoria")

    p = crear_profesor(db, "Juan", "Pérez", telefono="555-0100", correo="juan@test.com")

    s = crear_sesion(db, "Lunes", "08:00", "09:00")

    sl = crear_salon(db, "Aula 101")

    c = crear_curso(db, "A", "2026", mencion_id=m.id)

    ca = asignar_asignatura_a_curso(db, c.id, a.id, 5)

    asignar_profesor_a_sesion(db, s.id, p.id)

    asignar_profesor_a_curso_asignatura(db, p.id, ca.id)

    print("\n── 2. CONSULTA ──\n")

    obtener_mencion(db, m.id)
    listar_menciones(db)

    cursos_por_year(db, "2026")
    obtener_curso(db, c.id)

    obtener_asignatura(db, a.id)
    listar_asignaturas(db)

    obtener_profesor(db, p.id)
    profesores_activos(db)

    obtener_sesion(db, s.id)
    sesiones_por_dia(db, "Lunes")
    verificar_overlap(db, "Lunes", "08:30", "09:30")

    obtener_salon(db, sl.id)

    obtener_curso_asignatura(db, ca.id)

    listar_sesiones_profesores(db)
    sesiones_de_profesor(db, p.id)

    listar_profesores_asignaturas(db)

    print("\n── 3. ACTUALIZACIÓN ──\n")

    actualizar_mencion(db, m.id, nombre="**MODIFICADO**")
    actualizar_curso(db, c.id, seccion="**X**")
    actualizar_asignatura(db, a.id, tipo="**MODIFICADO**")
    actualizar_profesor(db, p.id, telefono="000-0000")
    actualizar_sesion(db, s.id, hora_inicio="99:99", hora_fin="99:99")
    actualizar_salon(db, sl.id, nombre="**MODIFICADO**")
    actualizar_curso_asignatura(db, ca.id, horas_semanales=999)

    print("\n── 4. ELIMINACIÓN ──\n")

    eliminar_profesor_asignatura(db, 1)
    eliminar_sesion_profesor(db, 1)
    eliminar_curso_asignatura(db, ca.id)
    eliminar_salon(db, sl.id)
    eliminar_sesion(db, s.id)
    eliminar_profesor(db, p.id)
    eliminar_asignatura(db, a.id)
    eliminar_curso(db, c.id)
    eliminar_mencion(db, m.id)

    print("\n── VERIFICACIÓN FINAL ──\n")
    listar_menciones(db)
    print("(vacío — todo eliminado correctamente)")

    cerrar_sesion(db)
