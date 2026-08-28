"""Exportación de horarios por PROFESOR a Excel (.xlsx).

Módulo espejo de pdf_exporter.py/teacher_pdf_exporter.py: replica la misma
plantilla "Propuesta de horario de la Salle" usando la infraestructura común
de excel_exporter.py, filtrando la grilla por event.teacher. Cada celda
muestra la asignatura y el curso con su aula.
"""
import os

from openpyxl import Workbook

from src.database.connection import SessionLocal
from src.database.repositories import SalonRepository
from src.engine.data import Data
from src.export.excel_exporter import _add_logo, write_grid, write_sheet_skeleton
from src.export.pdf_exporter import (
    _abbreviate_subject,
    _build_data_maps,
    _display_row,
    _year_label,
)


def _build_teacher_maps(data: Data) -> dict:
    """Mapas auxiliares para profesores; añade room_names al mapa base."""
    maps = _build_data_maps(data)
    db = SessionLocal()
    try:
        maps["room_names"] = {s.id: s.nombre for s in SalonRepository().get_all(db)}
    finally:
        db.close()
    return maps


def _teacher_name(teacher_id: int, maps: dict) -> str:
    """Nombre completo del profesor o un marcador legible si no está en los mapas."""
    return maps["teacher_names"].get(teacher_id, f"Profesor {teacher_id}")


def _group_short_label(group_id: int, maps: dict) -> str:
    """Curso compacto sin aula ('4to \"A\" EO'), el aula se muestra aparte."""
    info = maps["group_info"].get(group_id, {})
    year = _year_label(info.get("year", ""))
    seccion = info.get("seccion", "")
    mencion = info.get("mencion", "")
    return f'{year} "{seccion}" {mencion}'.strip()


def _room_label(event_room, group_info: dict, maps: dict) -> str | None:
    """Aula del evento (salon del evento; si no, el aula del curso)."""
    if event_room is not None:
        return maps.get("room_names", {}).get(event_room)
    aula = group_info.get("aula")
    if aula and not aula.lower().startswith("aula"):
        return f"Aula {aula}"
    return aula


def _cell_text(subject_id: int, group_id: int, event_room, maps: dict) -> str:
    """Texto de celda: 'Asignatura\nCurso · (Aula)'."""
    subject_names = maps["subject_names"]
    subject = _abbreviate_subject(subject_names.get(subject_id, str(subject_id)))
    curso = _group_short_label(group_id, maps)
    group_info = maps["group_info"].get(group_id, {})
    aula = _room_label(event_room, group_info, maps)
    if aula:
        aula = f"({aula})"

    line2 = " · ".join(part for part in (curso, aula) if part)
    return f"{subject}\n{line2}" if line2 else subject


def _build_grid_teacher(teacher_id: int, events: list, data: Data, maps: dict) -> tuple:
    """Construye la grilla de 12 filas x 5 días para un profesor.

    Espejo de pdf_exporter._build_grid filtrando por event.teacher.

    Returns:
        grid: list[list[str|None]] (12 filas, 5 columnas de día)
        spans: list[(r0, c0, r1, c1)] con filas de grilla 1-based (col 1..5)
    """
    grid = [[None] * 5 for _ in range(12)]
    spans = []

    for event in events:
        if event.teacher != teacher_id or event.start_hour is None:
            continue

        start = event.start_hour
        day = data.academic_hours[start].day_index
        day_min = data.academic_hours_limits[day]["min"]

        rows_for_event = []
        for hour_idx in range(start, start + event.duration):
            ah = data.academic_hours[hour_idx]
            if ah.day_index != day:
                break
            pos = hour_idx - day_min
            if pos < 0 or pos > 9:
                continue
            rows_for_event.append(_display_row(pos))

        if not rows_for_event:
            continue

        text = _cell_text(event.subject, event.group, event.room, maps)

        # Un evento no puede atravesar RECESO/ALMUERZO: dividimos en
        # segmentos de filas contiguas y cada uno se dibuja por separado.
        segments: list[list[int]] = []
        for row in rows_for_event:
            if segments and row == segments[-1][-1] + 1:
                segments[-1].append(row)
            else:
                segments.append([row])

        for segment in segments:
            r0, r1 = segment[0], segment[-1]
            grid[r0 - 1][day] = text
            spans.append(((r0, day + 1), (r1, day + 1)))

    return grid, spans


def export_teacher_excel(
    events: list,
    teacher_id: int,
    output_path: str,
    data: Data,
    maps: dict,
    year_label: str = "2025 - 2026",
) -> str:
    """Escribe el workbook de un profesor (una hoja)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Horario"
    write_sheet_skeleton(ws, f"Prof. {_teacher_name(teacher_id, maps)}", data, year_label)
    grid, spans = _build_grid_teacher(teacher_id, events, data, maps)
    write_grid(ws, data, grid, spans)
    _add_logo(ws)
    wb.save(output_path)
    return output_path


def export_all_teachers_excel(
    timetable: list,
    output_dir: str,
    year_label: str = "2025 - 2026",
    data: Data | None = None,
) -> list[str]:
    """Exporta un workbook por profesor con clases asignadas dentro de la
    subcarpeta 'Horarios_Profesores' del directorio de salida.
    Devuelve las rutas creadas."""
    if data is None:
        data = Data()
        data.load_data()

    maps = _build_teacher_maps(data)
    teachers_dir = os.path.join(output_dir, "Horarios_Profesores")
    os.makedirs(teachers_dir, exist_ok=True)

    teachers_by_id = {t.id: t for t in data.teachers}

    def sort_key(teacher_id: int) -> tuple:
        t = teachers_by_id.get(teacher_id)
        return ((t.last_name or "").lower(), (t.name or "").lower()) if t else ("~", "")

    teacher_ids = {
        e.teacher
        for e in timetable
        if getattr(e, "teacher", None) is not None and e.start_hour is not None
    }

    file_year = year_label.replace(" ", "_").replace("/", "-")
    created = []
    for teacher_id in sorted(teacher_ids, key=sort_key):
        t = teachers_by_id.get(teacher_id)
        slug = f"{t.last_name}_{t.name}" if t else str(_teacher_name(teacher_id, maps))
        slug = slug.replace(" ", "_")
        output_path = os.path.join(teachers_dir, f"Horario_Prof_{slug}_{file_year}.xlsx")
        export_teacher_excel(timetable, teacher_id, output_path, data, maps, year_label)
        created.append(output_path)

    return created
