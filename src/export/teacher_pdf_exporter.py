"""Exportación de horarios por PROFESOR a PDF.

Módulo espejo de pdf_exporter.py: reutiliza sus helpers, estilos y medidas
exactas para generar un PDF por profesor con clases asignadas, replicando la
misma plantilla "Propueta de horario de la Salle". Cada celda muestra la
asignatura y el curso con su aula.
"""
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.engine.data import Data
from src.export.pdf_exporter import (
    ALMUERZO_LABEL,
    DIAS,
    RECESO_LABEL,
    _abbreviate_subject,
    _break_style,
    _build_data_maps,
    _cell_paragraph,
    _cell_style,
    _course_style,
    _display_row,
    _draw_logo,
    _empty_cell_spans,
    _footer_style,
    _head_style,
    _hour_style,
    _time_label_for_row,
    _title_style,
    _year_label,
    _year_style,
)


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


def _teacher_page_story(
    story: list,
    teacher_id: int,
    events: list,
    data: Data,
    maps: dict,
    year_label: str,
) -> None:
    """Añade los flowables de la página de un profesor (encabezado + grilla + footer)."""
    story.append(Paragraph("Horario Año Escolar", _title_style))
    story.append(Paragraph(year_label, _year_style))
    story.append(Spacer(1, 14))

    teacher_band = Table(
        [[Paragraph(f"Prof. {_teacher_name(teacher_id, maps)}", _course_style)]],
        colWidths=[760],
        rowHeights=[22],
    )
    teacher_band.setStyle(TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1F4E78")),
            ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]
    ))
    story.append(teacher_band)

    grid, spans = _build_grid_teacher(teacher_id, events, data, maps)

    header = [Paragraph("Horarios", _head_style)] + [Paragraph(d, _head_style) for d in DIAS]
    rows = [header]

    for row in range(1, 13):
        time_label = (
            _time_label_for_row(row, data, 0)
            if row not in (3, 9)
            else RECESO_LABEL if row == 3 else ALMUERZO_LABEL
        )
        line = [Paragraph(time_label, _hour_style)]
        if row in (3, 9):
            label = "RECESO" if row == 3 else "ALMUERZO"
            line += [Paragraph(label, _break_style)] + [Paragraph("", _cell_style) for _ in range(4)]
        else:
            line += [_cell_paragraph(grid[row - 1][day] or "") for day in range(5)]
        rows.append(line)

    row_heights = [26, 33, 33, 26, 33, 33, 33, 33, 33, 26, 33, 33, 33]
    table = Table(rows, colWidths=[70, 138, 138, 138, 138, 138], rowHeights=row_heights)
    table.setStyle(TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
            ("BACKGROUND", (1, 1), (-1, -1), colors.HexColor("#FFFFFF")),
            ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#DDEBF7")),
            ("BACKGROUND", (0, 3), (0, 3), colors.HexColor("#E7E6E6")),
            ("BACKGROUND", (0, 9), (0, 9), colors.HexColor("#E7E6E6")),
            ("BACKGROUND", (1, 3), (-1, 3), colors.HexColor("#E7E6E6")),
            ("BACKGROUND", (1, 9), (-1, 9), colors.HexColor("#E7E6E6")),
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#E7E6E6")),
            ("BACKGROUND", (1, 0), (-1, 0), colors.HexColor("#FFE699")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("SPAN", (1, 3), (5, 3)),
            ("SPAN", (1, 9), (5, 9)),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]
    ))
    for (r0, c0), (r1, c1) in spans:
        table.setStyle(TableStyle([("SPAN", (c0, r0), (c1, r1))]))
    for (r0, c0), (r1, c1) in _empty_cell_spans(grid, spans):
        table.setStyle(TableStyle([("SPAN", (c0, r0), (c1, r1))]))

    story.append(table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("Realizado por HOLASA", _footer_style))


def export_teacher_pdf(
    events: list,
    teacher_id: int,
    output_path: str,
    data: Data,
    maps: dict,
    year_label: str = "2025 - 2026",
) -> str:
    """Escribe el PDF de un profesor (una página)."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=14 * mm,
        bottomMargin=12 * mm,
        title=f"Horario Año Escolar {year_label} - Prof. {_teacher_name(teacher_id, maps)}",
        author="HOLASA",
    )
    story = []
    _teacher_page_story(story, teacher_id, events, data, maps, year_label)
    doc.build(story, onFirstPage=_draw_logo, onLaterPages=_draw_logo)
    return output_path


def export_all_teachers(
    timetable: list,
    output_dir: str,
    year_label: str = "2025 - 2026",
    data: Data | None = None,
) -> list[str]:
    """Exporta un PDF por profesor con clases asignadas dentro de la subcarpeta
    'Horarios_Profesores' del directorio de salida. Devuelve las rutas creadas."""
    if data is None:
        data = Data()
        data.load_data()

    maps = _build_data_maps(data)
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
        output_path = os.path.join(teachers_dir, f"Horario_Prof_{slug}_{file_year}.pdf")
        export_teacher_pdf(timetable, teacher_id, output_path, data, maps, year_label)
        created.append(output_path)

    return created
