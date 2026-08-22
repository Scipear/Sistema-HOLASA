import flet as ft
import threading
import os

# Importaciones de tus módulos del proyecto
try:
    from src.engine import genetics
    from src.export.pdf_exporter import export_all
except ImportError:
    # Manejo de fallback en caso de ejecuciones aisladas
    genetics = None
    export_all = None


def vista_generacion():
    estilo_tarjeta_oscura = {
        "bgcolor": "#1E202D",
        "border_radius": 15,
        "padding": 20,
        "border": ft.border.all(1, "#303346")
    }

    # Estado de la vista y almacenamiento del resultado
    estado_ref = {
        "generado": False, 
        "en_progreso": False,
        "best_timetable": None
    }

    progreso_bar = ft.ProgressBar(
        value=0, bgcolor="#1A1C28", color="#439A5D", height=6, visible=False
    )
    txt_progreso = ft.Text("", color="#A0A0B0", size=12, visible=False)

    # Panel informativo simplificado (sin la grilla de previsualización)
    panel_info_estado = ft.Container(
        expand=True,
        content=ft.Column([
            ft.Icon(ft.icons.AUTO_AWESOME, size=60, color="#303346"),
            ft.Text("Generación de Horarios", size=20, color="#FFFFFF", weight=ft.FontWeight.BOLD),
            ft.Text(
                "Presiona 'Generar Horario' para ejecutar el algoritmo genético y exportar los archivos PDF correspondientes.",
                size=13, color="#A0A0B0", text_align=ft.TextAlign.CENTER
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
           alignment=ft.MainAxisAlignment.CENTER, spacing=12),
        alignment=ft.alignment.center
    )

    btn_generar = ft.ElevatedButton(
        "Generar Horario",
        icon=ft.icons.AUTO_FIX_HIGH,
        bgcolor="#439A5D", color=ft.colors.WHITE, height=48, expand=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )
    btn_regenerar = ft.ElevatedButton(
        "Regenerar",
        icon=ft.icons.REFRESH,
        bgcolor="#1A3A5C", color=ft.colors.WHITE, height=48, expand=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        visible=False
    )
    btn_exportar = ft.ElevatedButton(
        "Exportar Horarios",
        icon=ft.icons.FILE_DOWNLOAD_ROUNDED,
        bgcolor="#332415", color="#E69138", height=48, expand=True,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            side=ft.BorderSide(1, "#E69138")
        ),
        visible=False
    )

    badge_estado = ft.Container(
        visible=False,
        content=ft.Row([
            ft.Icon(ft.icons.CHECK_CIRCLE, color="#439A5D", size=16),
            ft.Text("Generado y exportado correctamente", color="#439A5D", size=12, weight=ft.FontWeight.BOLD)
        ]),
        bgcolor="#1A2A20", border_radius=10,
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        border=ft.border.all(1, "#439A5D")
    )

    # Componentes visuales de configuración
    sw_priorizar_prof = ft.Switch(value=True, active_color="#439A5D")
    sw_priorizar_elec = ft.Switch(value=False, active_color="#439A5D")
    sw_min_vacios = ft.Switch(value=True, active_color="#439A5D")
    sw_aulas_tec = ft.Switch(value=True, active_color="#439A5D")

    dd_anio = ft.Dropdown(
        options=[ft.dropdown.Option("2024 - 2025"), ft.dropdown.Option("2025 - 2026")],
        value="2025 - 2026",
        border_color="#303346", focused_border_color="#439A5D",
        bgcolor="#13141C", color=ft.colors.WHITE,
        height=45, border_radius=10
    )

    def fila_switch(etiqueta, sw):
        return ft.Row([
            ft.Text(etiqueta, color=ft.colors.WHITE, size=13, expand=True), sw
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # -------------------------------------------------------------
    # EJECUCIÓN DEL ALGORITMO GENÉTICO EN SEGUNDO PLANO
    # -------------------------------------------------------------
    def ejecutar_algoritmo_genetico(page):
        max_generaciones = 250

        if genetics is None:
            page.snack_bar = ft.SnackBar(ft.Text("Error: No se pudo importar src.engine.genetics"))
            page.snack_bar.open = True
            page.update()
            return

        # 1. Inicialización de eventos y población
        events = genetics.create_events()
        population = genetics.create_population(50, events)
        past_value = 0
        count = 0

        academic_hours = getattr(genetics, 'academic_hours', None)
        academic_hours_limits = getattr(genetics, 'academic_hours_limits', None)

        for i in range(max_generaciones):
            if academic_hours is not None and academic_hours_limits is not None:
                scores = genetics.fitness(population, academic_hours, academic_hours_limits)
            else:
                scores = genetics.fitness(population)

            fitness_population = list(zip(scores, population))
            fitness_population.sort(key=lambda x: x[0])
            best_fitness = fitness_population[0][0]

            selected_population = genetics.selection(fitness_population, 10)
            population = genetics.crossover(selected_population, 50)

            if past_value == best_fitness:
                count += 1
            else:
                count = 0

            progreso = (i + 1) / max_generaciones
            progreso_bar.value = progreso
            txt_progreso.value = f"Generación {i+1}/{max_generaciones} - Mejor Fitness: {best_fitness}"
            page.update()

            if count > 150:
                txt_progreso.value = f"Algoritmo estancado en gen {i+1}. Finalizando..."
                page.update()
                break

            past_value = best_fitness

        # Evaluación final y obtención del mejor horario
        if academic_hours is not None and academic_hours_limits is not None:
            scores = genetics.fitness(population, academic_hours, academic_hours_limits)
        else:
            scores = genetics.fitness(population)

        fitness_population = list(zip(scores, population))
        fitness_population.sort(key=lambda x: x[0])
        best_timetable = fitness_population[0][1]
        
        # Guardamos en memoria el mejor horario calculado
        estado_ref["best_timetable"] = best_timetable

        # 2. Exportación a PDF llamando a export_all DIRECTAMENTE con el timetable calculado
        if export_all is not None:
            txt_progreso.value = "Generando archivos PDF de exportación..."
            page.update()
            export_all(
                timetable=best_timetable,
                output_dir="data/export",
                year_label=dd_anio.value
            )

        # Finalizar estado de la interfaz
        estado_ref["generado"] = True
        estado_ref["en_progreso"] = False

        progreso_bar.visible = False
        txt_progreso.visible = False
        btn_generar.disabled = False
        btn_regenerar.disabled = False
        btn_generar.visible = False
        btn_regenerar.visible = True
        btn_exportar.visible = True
        badge_estado.visible = True
        page.update()

    def iniciar_generacion(e):
        if estado_ref["en_progreso"]:
            return
        estado_ref["en_progreso"] = True
        progreso_bar.value = 0
        progreso_bar.visible = True
        txt_progreso.visible = True
        txt_progreso.value = "Iniciando algoritmo genético..."
        btn_generar.disabled = True
        btn_regenerar.disabled = True
        badge_estado.visible = False
        e.page.update()

        threading.Thread(target=ejecutar_algoritmo_genetico, args=(e.page,), daemon=True).start()

    def regenerar(e):
        btn_regenerar.visible = False
        btn_exportar.visible = False
        btn_generar.visible = True
        badge_estado.visible = False
        e.page.update()
        iniciar_generacion(e)

    def exportar(e):
        output_dir = "data/export"
        best_timetable = estado_ref.get("best_timetable")

        if export_all is not None and best_timetable is not None:
            export_all(
                timetable=best_timetable,
                output_dir=output_dir,
                year_label=dd_anio.value
            )
            msj = f"Horarios exportados exitosamente en '{output_dir}'"
        elif best_timetable is None:
            msj = "Primero debes generar un horario antes de exportar."
        else:
            msj = "Módulo de exportación no disponible"

        e.page.snack_bar = ft.SnackBar(
            ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE if best_timetable else ft.icons.WARNING, color="#439A5D"),
                ft.Text(msj, color=ft.colors.WHITE)
            ]),
            bgcolor="#1A2A20"
        )
        e.page.snack_bar.open = True
        e.page.update()

    btn_generar.on_click = iniciar_generacion
    btn_regenerar.on_click = regenerar
    btn_exportar.on_click = exportar

    panel_config = ft.Container(
        **estilo_tarjeta_oscura,
        content=ft.Column([
            ft.Text("Configuración", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ft.Tabs(
                selected_index=0,
                tabs=[ft.Tab(text="Parámetros"), ft.Tab(text="Preferencias")],
                label_color="#439A5D",
                unselected_label_color="#A0A0B0",
                indicator_color="#439A5D",
                height=46
            ),
            ft.Text("Año Escolar", color="#A0A0B0", size=12),
            dd_anio,
            ft.Divider(color="#303346", height=8),
            fila_switch("Priorizar Profesores", sw_priorizar_prof),
            fila_switch("Priorizar Electrónicos", sw_priorizar_elec),
            fila_switch("Minimizar Bloques Vacíos", sw_min_vacios),
            fila_switch("Asignar Aulas Técnicas", sw_aulas_tec),
            ft.Divider(color="#303346", height=8),
            progreso_bar,
            txt_progreso,
            ft.Row([btn_generar, btn_regenerar], spacing=10),
            btn_exportar,
            badge_estado,
        ], spacing=12)
    )

    panel_stats = ft.Container(
        **estilo_tarjeta_oscura,
        content=ft.Column([
            ft.Text("Resumen de Generación", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ft.Row([
                ft.Container(
                    bgcolor="#1A2A20", border_radius=10, padding=12, expand=True,
                    content=ft.Column([
                        ft.Text("7", size=28, weight=ft.FontWeight.BOLD, color="#439A5D"),
                        ft.Text("Cursos", size=11, color="#439A5D")
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                ft.Container(
                    bgcolor="#1A3A5C", border_radius=10, padding=12, expand=True,
                    content=ft.Column([
                        ft.Text("42", size=28, weight=ft.FontWeight.BOLD, color="#5B9BD5"),
                        ft.Text("Docentes", size=11, color="#5B9BD5")
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                ft.Container(
                    bgcolor="#332415", border_radius=10, padding=12, expand=True,
                    content=ft.Column([
                        ft.Text("7", size=28, weight=ft.FontWeight.BOLD, color="#E69138"),
                        ft.Text("Salones", size=11, color="#E69138")
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
            ], spacing=10),
            ft.Divider(color="#303346", height=8),
            ft.Text("Advertencias", color="#A0A0B0", size=13, weight=ft.FontWeight.BOLD),
            ft.Container(
                bgcolor="#1A2A20", border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                border=ft.border.all(1, "#439A5D"),
                content=ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, color="#439A5D", size=16),
                    ft.Text("Sin conflictos de superposición", color="#439A5D", size=12)
                ])
            ),
        ], spacing=12)
    )

    return ft.Container(
        padding=20, expand=True,
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column([
                            ft.Text("Generación de Horarios", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                            ft.Text("Genera y exporta los horarios del período académico", size=14, color="#A0A0B0")
                        ], spacing=2),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                ft.Row(
                    expand=True,
                    spacing=20,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Column(expand=4, spacing=20, controls=[panel_config, panel_stats]),
                        ft.Column(
                            expand=6,
                            spacing=0,
                            expand_loose=True,
                            controls=[
                                ft.Container(
                                    **estilo_tarjeta_oscura,
                                    expand=True,
                                    content=panel_info_estado
                                )
                            ]
                        )
                    ]
                )
            ],
            expand=True
        )
    )