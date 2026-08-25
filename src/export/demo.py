"""Demo de exportación de horarios a PDF y Excel.

Uso:
    python src/export/demo.py                # horario rápido generado al vuelo
    python src/export/demo.py --genetics     # usa el pipeline real de src.engine.genetics
    python src/export/demo.py --generations 200 --output-dir data/export
    python src/export/demo.py --excel        # exporta también workbooks .xlsx

Por defecto exporta los PDFs por año/curso y también el horario individual de cada
profesor (Horario_Prof_*.pdf), siempre sobre el mismo horario generado.
Usa --no-profesores para exportar solo los horarios por año/curso.

Con --excel se generan además los horarios en formato Excel, separados de los
PDF: un workbook por año (una hoja por curso) en <output-dir>/excel/ y el
horario de cada profesor dentro de <output-dir>/excel/Horarios_Profesores/.
"""
import argparse
import os


def _print_created(created: list[str]) -> None:
    print("\nArchivos generados:")
    for path in created:
        print(f"  - {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo de exportación de horarios a PDF y Excel")
    parser.add_argument("--output-dir", default="data/export", help="Carpeta de salida")
    parser.add_argument("--year-label", default="2025 - 2026", help="Etiqueta del año escolar")
    parser.add_argument("--genetics", action="store_true",
                        help="Usar el pipeline real de src.engine.genetics")
    parser.add_argument("--generations", type=int, default=2000,
                        help="Generaciones a ejecutar si se usa --genetics")
    parser.add_argument("--profesores", action=argparse.BooleanOptionalAction, default=True,
                        help="Exporta también el horario de cada profesor (default: activado; "
                             "usa --no-profesores para desactivar)")
    parser.add_argument("--excel", action="store_true",
                        help="Exporta también los horarios en formato Excel (.xlsx)")
    args = parser.parse_args()

    extra_exporter = None
    if args.profesores or args.excel:
        from src.export.teacher_pdf_exporter import export_all_teachers

        def extra_exporter(timetable, output_dir, year_label):
            results = []
            if args.profesores:
                results += export_all_teachers(timetable, output_dir, year_label=year_label)
            if args.excel:
                from src.export.excel_exporter import export_all_excel
                from src.export.teacher_excel_exporter import export_all_teachers_excel

                excel_dir = os.path.join(output_dir, "excel")
                results += export_all_excel(timetable, excel_dir, year_label=year_label)
                results += export_all_teachers_excel(timetable, excel_dir, year_label=year_label)
            return results

    if args.genetics:
        from src.export.pdf_exporter import export_from_genetics

        created = export_from_genetics(
            args.output_dir,
            year_label=args.year_label,
            generations=args.generations,
            extra_exporter=extra_exporter,
        )
    else:
        from src.export.pdf_exporter import export_all
        from src.engine import genetics

        events = genetics.create_events()
        timetable = genetics.create_timetable(events)
        created = export_all(timetable, args.output_dir, year_label=args.year_label)

        if extra_exporter is not None:
            created += extra_exporter(timetable, args.output_dir, args.year_label)

    _print_created(created)


if __name__ == "__main__":
    main()
