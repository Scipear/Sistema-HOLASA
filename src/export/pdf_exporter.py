"""Exportación de horarios generados a PDF.

Módulo independiente que NO modifica el resto del código: solo lee los datos
existentes (Data(), clases del motor y repositorios) para generar un PDF por
año de curso, donde cada página es el horario de un curso, replicando la
plantilla "Propueta de horario de la Salle".
"""
import os
from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.engine.data import Data
from src.database.connection import SessionLocal
from src.database.repositories import (
    CursoRepository,
    MencionRepository,
    SalonRepository,
)
from src.database.repositories.salon_curso_repository import SalonCursoRepository

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

_LOGO_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "Salle_sin_bg.png"
)
_LOGO_HEIGHT = 15 * mm

# Filas RECESO y ALMUERZO (no existen en la tabla de sesiones; son fijas de la plantilla)
RECESO_LABEL = "8:20 a 8:30"
ALMUERZO_LABEL = "11:50 a 12:10"

_YEAR_ORDINALS = {"1": "1ro", "2": "2do", "3": "3ro", "4": "4to", "5": "5to", "6": "6to"}

# Abreviaturas para nombres largos de asignaturas, respetando la ortografía
# exacta que trae la base de datos (igual estilo que la plantilla original).
_SUBJECT_ABBREVIATIONS = {
    "Biologia, Ambiente y Tecnologia": "Bio. Amb. y Tec.",
    "Maquinas, Distribucion y Control": "Maq. Dist. y Cont.",
    "Proyecto de Economia Socioproductiva y Tecnologia": "Proy. de Econ. Socioprod.",
    "Geografia, Historia y Soberania Nacional": "Geo. Hist. y Sob. Nacional",
    "Orientacion y Vinculacion Sociolaboral": "Orient. Vinc. Sociolab.",
    "Lengua y Literatura": "Lengua y Lit.",
    "Educación Física": "Ed. Física",
    "Telecomunicacion y Control": "Telecom. y Cont.",
    "Mantenimiento Maquinas": "Mant. Maquinas",
    "Sistema de Refrigeracion, Aire Acondicionado y Calderas": "Sist. de Refrig. A/C y Cal.",
    "Programacion y Diseno de Software y Redes": "Prog. y Diseno de Soft. y Redes",
    "Identidad Lasallista": "Ident. Lasallista",
}


def _abbreviate_subject(name: str) -> str:
    """Devuelve la abreviatura de una asignatura; si no hay mapeo, el nombre tal cual."""
    return _SUBJECT_ABBREVIATIONS.get(name, name)


def _year_label(year: str) -> str:
    """Convierte el año de la BD ('1') a ordinal legible ('1ro')."""
    return _YEAR_ORDINALS.get(str(year), f"{year}º")


def _draw_logo(canvas, doc) -> None:
    """Dibuja el logo de la Salle en la esquina superior izquierda de cada página."""
    if not os.path.exists(_LOGO_PATH):
        return
    image = ImageReader(_LOGO_PATH)
    width, height = image.getSize()
    ratio = width / height
    height = _LOGO_HEIGHT
    width = height * ratio
    x = doc.leftMargin
    y = doc.pagesize[1] - doc.topMargin - height
    canvas.saveState()
    canvas.drawImage(
        _LOGO_PATH,
        x,
        y,
        width=width,
        height=height,
        preserveAspectRatio=True,
        mask="auto",
    )
    canvas.restoreState()


def _build_data_maps(data: Data) -> dict:
    """Construye mapas auxiliares (solo lectura) para resolver nombres/años/aulas."""
    db = SessionLocal()
    try:
        menciones = {m.id: m.nombre for m in MencionRepository().get_all(db)}
        salon_curso_repo = SalonCursoRepository()
        salon_repo = SalonRepository()
        room_names = {s.id: s.nombre for s in salon_repo.get_all(db)}

        group_info = {}
        for curso in CursoRepository().get_all(db):
            aula = None
            relaciones = salon_curso_repo.get_by_curso(db, curso.id)
            if relaciones:
                salon = salon_repo.get_by_id(db, relaciones[0].salon_id)
                aula = salon.nombre if salon else None
            group_info[curso.id] = {
                "year": str(curso.year),
                "seccion": curso.seccion,
                "mencion": menciones.get(curso.mencion_id, ""),
                "aula": aula,
            }
    finally:
        db.close()

    return {
        "group_info": group_info,
        "subject_names": {s.id: s.name for s in data.subjects},
        "teacher_names": {t.id: f"{t.name} {t.last_name}".strip() for t in data.teachers},
        "room_names": room_names,
    }


def _fmt_time(raw: str) -> str:
    """'07:00' -> '7:00'."""
    try:
        h, m = raw.split(":")
        return f"{int(h)}:{m}"
    except (ValueError, AttributeError):
        return raw


def _display_row(pos_in_day: int) -> int:
    """Posición de la sesión dentro del día (0..9) -> fila de la grilla (1..12).

    Inserta la fila RECESO después del bloque 2 y la de ALMUERZO después del 7.
    """
    return pos_in_day + 1 + (1 if pos_in_day >= 2 else 0) + (1 if pos_in_day >= 7 else 0)


def _time_label_for_row(row: int, data: Data, day: int) -> str:
    """Etiqueta horaria de la columna 'Horarios' para la fila de la grilla."""
    if row == 3:
        return RECESO_LABEL
    if row == 9:
        return ALMUERZO_LABEL
    pos_in_day = row - 1 - (1 if row > 3 else 0) - (1 if row > 9 else 0)
    hour_idx = data.academic_hours_limits[day]["min"] + pos_in_day
    ah = data.academic_hours[hour_idx]
    return f"{_fmt_time(ah.start_hour)} a {_fmt_time(ah.end_hour)}"


def _build_grid(group_id: int, events: list, data: Data, maps: dict) -> tuple:
    """Construye la grilla de 12 filas x 5 días para un curso.

    Returns:
        grid: list[list[str|None]] (12 filas, 5 columnas de día)
        spans: list[(r0, c0, r1, c1)] con filas de grilla 1-based (col 1..5)
    """
    subject_names = maps["subject_names"]
    teacher_names = maps["teacher_names"]
    grid = [[None] * 5 for _ in range(12)]
    spans = []

    for event in events:
        if event.group != group_id or event.start_hour is None:
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

        subject_name = _abbreviate_subject(subject_names.get(event.subject, event.subject))
        teacher_name = teacher_names.get(event.teacher, event.teacher)
        text = f"{subject_name}\nProf. {teacher_name}"

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


def _group_title(group_id: int, maps: dict) -> str:
    info = maps["group_info"].get(group_id, {})
    year = _year_label(info.get("year", ""))
    seccion = info.get("seccion", "")
    mencion = info.get("mencion", "")
    aula = info.get("aula")

    title = f'{year} "{seccion}" {mencion}'.strip()
    if aula and not aula.lower().startswith("aula"):
        title = f"{title} Aula {aula}"
    elif aula:
        title = f"{title} {aula}"
    return title


def _cell_paragraph(text: str) -> Paragraph:
    if not text:
        return Paragraph("", _cell_style)
    parts = text.split("\n", 1)
    subject = parts[0]
    prof = parts[1] if len(parts) > 1 else ""
    body = f"<b>{subject}</b>"
    if prof:
        body += f"<br/>{prof}"
    return Paragraph(body, _cell_style)


def _group_page_story(
    story: list,
    group_id: int,
    events: list,
    data: Data,
    maps: dict,
    year_label: str,
) -> None:
    """Añade los flowables de la página de un curso (encabezado + grilla + footer)."""
    story.append(Paragraph("Horario Año Escolar", _title_style))
    story.append(Paragraph(year_label, _year_style))
    story.append(Spacer(1, 14))

    course_band = Table(
        [[Paragraph(_group_title(group_id, maps), _course_style)]],
        colWidths=[760],
        rowHeights=[22],
    )
    course_band.setStyle(TableStyle(
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
    story.append(course_band)

    grid, spans = _build_grid(group_id, events, data, maps)

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

    story.append(table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("Realizado por HOLASA", _footer_style))


def export_year_pdf(
    events: list,
    course_ids: list[int],
    year: str,
    output_path: str,
    data: Data,
    maps: dict,
    year_label: str = "2025 - 2026",
) -> str:
    """Escribe un PDF por año con una página por curso."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=14 * mm,
        bottomMargin=12 * mm,
        title=f"Horario Año Escolar {year_label} - {_year_label(year)}",
        author="HOLASA",
    )
    story = []
    for index, course_id in enumerate(sorted(course_ids)):
        _group_page_story(story, course_id, events, data, maps, year_label)
        if index < len(course_ids) - 1:
            story.append(PageBreak())
    doc.build(story, onFirstPage=_draw_logo, onLaterPages=_draw_logo)
    return output_path


def export_all(
    timetable: list,
    output_dir: str,
    year_label: str = "2025 - 2026",
    data: Data | None = None,
) -> list[str]:
    """Exporta un PDF por año de curso. Devuelve las rutas de los PDF creados."""
    if data is None:
        data = Data()
        data.load_data()

    maps = _build_data_maps(data)
    os.makedirs(output_dir, exist_ok=True)

    by_year: dict[str, list[int]] = defaultdict(list)
    for group in data.groups:
        info = maps["group_info"].get(group.id, {})
        by_year[info.get("year", "?")].append(group.id)

    created = []
    file_year = year_label.replace(" ", "_").replace("/", "-")
    for year in sorted(by_year, key=lambda y: (len(y), y)):
        output_path = os.path.join(output_dir, f"Horario_{file_year}_{_year_label(year)}.pdf")
        export_year_pdf(timetable, by_year[year], year, output_path, data, maps, year_label)
        created.append(output_path)

    return created


def export_from_genetics(
    output_dir: str,
    year_label: str = "2025 - 2026",
    generations: int = 2000,
    population_size: int = 50,
    extra_exporter=None,
) -> list[str]:
    """Reproduce el pipeline de src.engine.genetics y exporta el mejor horario.

    Es la función de prueba para exportar horarios generados por el motor
    (equivalentes a los de `python -m src.engine.genetics`). No modifica nada
    de la genética: solo importa sus funciones y captura el best_timetable.
    Si se pasa extra_exporter, se invoca con (timetable, output_dir, year_label)
    para exportaciones adicionales sobre el mismo horario.
    """
    from src.engine import genetics

    events = genetics.create_events()
    population = genetics.create_population(population_size, events)
    selected = None

    for generation in range(generations):
        scores = genetics.fitness(population, genetics.academic_hours, genetics.academic_hours_limits)
        fitness_population = list(zip(scores, population))
        selected = genetics.selection(fitness_population, 10)
        population = genetics.crossover(selected, population_size)

        if generation == 0 or (generation + 1) % 10 == 0:
            fitness_population.sort(key=lambda x: x[0])
            print(f"Generacion {generation + 1} - Mejor Fitness: {fitness_population[0][0]}")

    best_timetable = selected[0][1]
    print("\nExportando horario generado por el motor de genética...")
    created = export_all(best_timetable, output_dir, year_label)
    if extra_exporter is not None:
        created += extra_exporter(best_timetable, output_dir, year_label)
    return created


_title_style = ParagraphStyle(
    "Title", fontName="Helvetica-Bold", fontSize=17, leading=19, alignment=1
)
_year_style = ParagraphStyle(
    "Year", fontName="Helvetica-Bold", fontSize=14, leading=16, alignment=1
)
_course_style = ParagraphStyle(
    "Course", fontName="Helvetica-Bold", fontSize=12, leading=14, alignment=1,
    backColor=colors.HexColor("#1F4E78"), textColor=colors.white
)
_head_style = ParagraphStyle(
    "Head", fontName="Helvetica-Bold", fontSize=11, leading=13, alignment=1
)
_hour_style = ParagraphStyle(
    "Hour", fontName="Helvetica", fontSize=9, leading=11, alignment=1
)
_cell_style = ParagraphStyle(
    "Cell", fontName="Helvetica", fontSize=8.5, leading=10.5, alignment=1
)
_break_style = ParagraphStyle(
    "Break", fontName="Helvetica-Bold", fontSize=10, leading=12, alignment=1
)
_footer_style = ParagraphStyle(
    "Footer", fontName="Helvetica", fontSize=10, leading=12, alignment=1
)