"""Exportación de horarios generados a Excel (.xlsx).

Módulo espejo de pdf_exporter.py: reutiliza sus helpers y replican la misma
plantilla "Propuesta de horario de la Salle" en hojas de cálculo. Genera un
workbook por año de curso con una hoja por curso. NO modifica el resto del
código: solo lee los datos existentes.
"""
import os
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from src.engine.data import Data
from src.export.pdf_exporter import (
    ALMUERZO_LABEL,
    DIAS,
    RECESO_LABEL,
    _LOGO_PATH,
    _build_data_maps,
    _build_grid,
    _empty_cell_spans,
    _group_title,
    _time_label_for_row,
    _year_label,
)

# La franja del logo ocupa la fila 1; el título/año van en las filas 2-3,
# la banda del curso/profesor en la 5 y la cabecera de la grilla en la fila 6.
GRID_START_ROW = 6
GRID_ROWS = 12
N_COLS = 6  # columna Horarios + 5 días
BREAK_ROWS = {3: "RECESO", 9: "ALMUERZO"}

_THIN_BLACK = Side(style="thin", color="000000")
_BORDER_ALL = Border(left=_THIN_BLACK, right=_THIN_BLACK, top=_THIN_BLACK, bottom=_THIN_BLACK)

_FILL_BAND = PatternFill("solid", fgColor="1F4E78")
_FILL_HEADER_DAYS = PatternFill("solid", fgColor="FFE699")
_FILL_HEADER_HOURS = PatternFill("solid", fgColor="E7E6E6")
_FILL_HOURS_COL = PatternFill("solid", fgColor="DDEBF7")
_FILL_BREAK = PatternFill("solid", fgColor="E7E6E6")

_FONT_TITLE = Font(bold=True, size=14)
_FONT_YEAR = Font(bold=True, size=12)
_FONT_BAND = Font(bold=True, color="FFFFFF", size=11)
_FONT_HEAD = Font(bold=True, size=11)
_FONT_HOUR = Font(size=9)
_FONT_CELL = Font(size=9)
_FONT_BREAK = Font(bold=True, size=10)
_FONT_FOOTER = Font(size=10)
_FONT_WARN = Font(bold=True, size=10, color="FF0000")

_ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
_ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")
_ALIGN_WRAP = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _safe_sheet_name(title: str, used: set) -> str:
    """Nombre válido de hoja: sin []:*?/\\, máx. 31 caracteres y único."""
    for ch in '[]:*?/\\':
        title = title.replace(ch, "")
    name = title.strip()[:31] or "Horario"
    candidate, i = name, 2
    while candidate in used:
        suffix = f" ({i})"
        candidate = name[:31 - len(suffix)] + suffix
        i += 1
    used.add(candidate)
    return candidate


def _add_logo(worksheet) -> None:
    """Inserta el logo de la Salle en la esquina superior izquierda (celda A1).

    openpyxl necesita Pillow para imágenes; si no está disponible o el
    archivo no existe, simplemente se omite el logo.
    """
    try:
        if not os.path.exists(_LOGO_PATH):
            return
        from openpyxl.drawing.image import Image as XLImage

        img = XLImage(_LOGO_PATH)
        ratio = img.width / img.height
        img.height = 110
        img.width = int(110 * ratio)
        worksheet.add_image(img, "A1")
    except Exception:
        pass


def write_sheet_skeleton(ws, band_text: str, data: Data, year_label: str) -> None:
    """Franja del logo (fila 1), título/año, banda azul y cabecera de la grilla."""
    # Fila 1: vacía y alta, reservada como franja exclusiva del logo.
    ws.row_dimensions[1].height = 84

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=N_COLS)
    c = ws.cell(row=2, column=1, value="Horario Año Escolar")
    c.font, c.alignment = _FONT_TITLE, _ALIGN_CENTER
    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=N_COLS)
    c = ws.cell(row=3, column=1, value=year_label)
    c.font, c.alignment = _FONT_YEAR, _ALIGN_CENTER
    ws.row_dimensions[2].height = 24
    ws.row_dimensions[3].height = 20
    ws.row_dimensions[4].height = 8

    ws.merge_cells(start_row=5, start_column=1, end_row=5, end_column=N_COLS)
    c = ws.cell(row=5, column=1, value=band_text)
    c.font, c.alignment, c.fill = _FONT_BAND, _ALIGN_CENTER, _FILL_BAND
    ws.row_dimensions[5].height = 22

    header_fills = [_FILL_HEADER_HOURS] + [_FILL_HEADER_DAYS] * 5
    for col, (label, fill) in enumerate(zip(["Horarios"] + DIAS, header_fills), start=1):
        c = ws.cell(row=GRID_START_ROW, column=col, value=label)
        c.font, c.alignment, c.fill, c.border = _FONT_HEAD, _ALIGN_CENTER, fill, _BORDER_ALL
    ws.row_dimensions[GRID_START_ROW].height = 26

    ws.column_dimensions["A"].width = 14
    for col_letter in ("B", "C", "D", "E", "F"):
        ws.column_dimensions[col_letter].width = 28


def write_grid(ws, data: Data, grid: list, spans: list) -> None:
    """Escribe las 12 filas de la grilla (horas, RECESO/ALMUERZO y eventos)."""
    for grid_row in range(1, GRID_ROWS + 1):
        sheet_row = GRID_START_ROW + grid_row
        label = BREAK_ROWS.get(grid_row)
        if grid_row == 3:
            time_label = RECESO_LABEL
        elif grid_row == 9:
            time_label = ALMUERZO_LABEL
        else:
            time_label = _time_label_for_row(grid_row, data, 0)

        c = ws.cell(row=sheet_row, column=1, value=time_label)
        c.font, c.alignment, c.border = _FONT_HOUR, _ALIGN_CENTER, _BORDER_ALL
        c.fill = _FILL_BREAK if label else _FILL_HOURS_COL

        if label:
            ws.merge_cells(start_row=sheet_row, start_column=2, end_row=sheet_row, end_column=N_COLS)
            for col in range(2, N_COLS + 1):
                cc = ws.cell(row=sheet_row, column=col)
                cc.fill, cc.border = _FILL_BREAK, _BORDER_ALL
            c = ws.cell(row=sheet_row, column=2, value=label)
            c.font, c.alignment = _FONT_BREAK, _ALIGN_CENTER
            ws.row_dimensions[sheet_row].height = 26
        else:
            for day in range(5):
                c = ws.cell(row=sheet_row, column=day + 2, value=grid[grid_row - 1][day] or "")
                c.font, c.alignment, c.border = _FONT_CELL, _ALIGN_WRAP, _BORDER_ALL
            ws.row_dimensions[sheet_row].height = 33

    for (r0, c0), (r1, c1) in spans:
        ws.merge_cells(
            start_row=GRID_START_ROW + r0,
            start_column=c0 + 1,
            end_row=GRID_START_ROW + r1,
            end_column=c1 + 1,
        )

    for (r0, c0), (r1, c1) in _empty_cell_spans(grid, spans):
        ws.merge_cells(
            start_row=GRID_START_ROW + r0,
            start_column=c0 + 1,
            end_row=GRID_START_ROW + r1,
            end_column=c1 + 1,
        )

    footer_row = GRID_START_ROW + GRID_ROWS + 1
    ws.merge_cells(start_row=footer_row, start_column=1, end_row=footer_row, end_column=3)
    c = ws.cell(row=footer_row, column=1, value="Realizado por HOLASA")
    c.font, c.alignment = _FONT_FOOTER, _ALIGN_CENTER
    ws.merge_cells(start_row=footer_row, start_column=4, end_row=footer_row, end_column=N_COLS)
    w = ws.cell(row=footer_row, column=4, value="Horario sujeto a cambios")
    w.font, w.alignment = _FONT_WARN, _ALIGN_RIGHT


def export_year_excel(
    events: list,
    course_ids: list[int],
    year: str,
    output_path: str,
    data: Data,
    maps: dict,
    year_label: str = "2025 - 2026",
) -> str:
    """Escribe un workbook por año con una hoja por curso."""
    wb = Workbook()
    wb.remove(wb.active)
    used_names: set = set()

    for group_id in sorted(course_ids):
        title = _group_title(group_id, maps)
        ws = wb.create_sheet(title=_safe_sheet_name(title, used_names))
        write_sheet_skeleton(ws, title, data, year_label)
        grid, spans = _build_grid(group_id, events, data, maps)
        write_grid(ws, data, grid, spans)
        _add_logo(ws)

    wb.save(output_path)
    return output_path


def export_all_excel(
    timetable: list,
    output_dir: str,
    year_label: str = "2025 - 2026",
    data: Data | None = None,
) -> list[str]:
    """Exporta un workbook por año de curso. Devuelve las rutas creadas."""
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
        output_path = os.path.join(output_dir, f"Horario_{file_year}_{_year_label(year)}.xlsx")
        export_year_excel(timetable, by_year[year], year, output_path, data, maps, year_label)
        created.append(output_path)

    return created
