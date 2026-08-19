"""Demo de exportación de horarios a PDF.

Uso:
    python src/export/demo.py                # horario rápido generado al vuelo
    python src/export/demo.py --genetics     # usa el pipeline real de src.engine.genetics
    python src/export/demo.py --generations 200 --output-dir data/export
"""
import argparse


def _print_created(created: list[str]) -> None:
    print("\nPDFs generados:")
    for path in created:
        print(f"  - {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo de exportación de horarios a PDF")
    parser.add_argument("--output-dir", default="data/export", help="Carpeta de salida")
    parser.add_argument("--year-label", default="2025 - 2026", help="Etiqueta del año escolar")
    parser.add_argument("--genetics", action="store_true",
                        help="Usar el pipeline real de src.engine.genetics")
    parser.add_argument("--generations", type=int, default=2000,
                        help="Generaciones a ejecutar si se usa --genetics")
    args = parser.parse_args()

    if args.genetics:
        from src.export.pdf_exporter import export_from_genetics

        created = export_from_genetics(
            args.output_dir,
            year_label=args.year_label,
            generations=args.generations,
        )
    else:
        from src.export.pdf_exporter import export_all
        from src.engine import genetics

        events = genetics.create_events()
        timetable = genetics.create_timetable(events)
        created = export_all(timetable, args.output_dir, year_label=args.year_label)

    _print_created(created)


if __name__ == "__main__":
    main()
