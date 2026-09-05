import flet as ft
import threading
import os
from datetime import datetime

# Importaciones de tus módulos del proyecto
try:
    from src.engine import genetics
    from src.export.pdf_exporter import export_all
    from src.export.teacher_pdf_exporter import export_all_teachers
    from src.export.excel_exporter import export_all_excel
    from src.export.teacher_excel_exporter import export_all_teachers_excel
except ImportError:
    genetics = None
    export_all = None
    export_all_teachers = None
    export_all_excel = None
    export_all_teachers_excel = None


def vista_generacion():
    estilo_tarjeta_oscura = {
        "bgcolor": "#1E202D",
        "border_radius": 15,
        "padding": 20,
        "border": ft.border.all(1, "#303346")
    }

    # Estado de la vista
    estado_ref = {
        "generado": False, 
        "en_progreso": False,
        "exportando": False,
        "detener": False,
        "best_timetable": None,
        "final_report": None,
        "_pending_export_button": None,
    }

    # ── FilePicker para seleccionar carpeta de exportación ──────────
    def _on_directory_picked(e: ft.FilePickerResultEvent):
        """Callback cuando el usuario selecciona (o cancela) la carpeta."""
        button_triggered = estado_ref.get("_pending_export_button")
        page = e.page if hasattr(e, 'page') else e.control.page

        # Si el usuario canceló o cerró la ventana sin elegir
        if not e.path:
            if button_triggered:
                button_triggered.disabled = False
                button_triggered.update()
            return
        
        ejecutar_exportacion(page, output_dir=e.path, button_triggered=button_triggered)

    file_picker = ft.FilePicker(on_result=_on_directory_picked)

    progreso_bar = ft.ProgressBar(
        value=0, bgcolor="#1A1C28", color="#439A5D", height=6, visible=False
    )
    txt_progreso = ft.Text("", color="#A0A0B0", size=12, visible=False)

    def crear_panel_inicial():
        return ft.Column([
            ft.Icon(ft.icons.AUTO_AWESOME, size=60, color="#303346"),
            ft.Text("Generación de Horarios", size=20, color="#FFFFFF", weight=ft.FontWeight.BOLD),
            ft.Text(
                "Presiona 'Generar Horario' para ejecutar el algoritmo genético. "
                "Al finalizar podrás revisar la auditoría de choques antes de exportar a PDF.",
                size=13, color="#A0A0B0", text_align=ft.TextAlign.CENTER
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
           alignment=ft.MainAxisAlignment.CENTER, spacing=12)

    panel_info_container = ft.Container(
        **estilo_tarjeta_oscura,
        expand=True,
        content=crear_panel_inicial()
    )

    btn_generar = ft.ElevatedButton(
        "Generar Horario",
        icon=ft.icons.AUTO_FIX_HIGH,
        bgcolor="#439A5D", color=ft.colors.WHITE, height=48, expand=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )
    btn_detener = ft.ElevatedButton(
        "Detener",
        icon=ft.icons.STOP_CIRCLE_ROUNDED,
        bgcolor="#3A1C1C", color="#FF6B6B", height=48,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            side=ft.BorderSide(1, "#FF6B6B")
        ),
        visible=False
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

    # ---------------------------------------------------------------
    # HELPERS PARA CONFIGURACIÓN DE ACTIVIDAD COMPLEMENTARIA
    # ---------------------------------------------------------------
    def _get_days():
        """Retorna [(day_index, day_name), ...] desde academic_hours de genetics."""
        if genetics and hasattr(genetics, 'academic_hours') and genetics.academic_hours:
            seen = {}
            for ah in genetics.academic_hours:
                if ah.day_index not in seen:
                    seen[ah.day_index] = ah.day
            return sorted(seen.items())  # [(idx, name)]
        return [(0,"Lunes"),(1,"Martes"),(2,"Miércoles"),(3,"Jueves"),(4,"Viernes")]

    def _get_block_options(day_index):
        """Retorna opciones de bloque válidas para un día (excluye el último bloque)."""
        if genetics and hasattr(genetics, 'academic_hours') and genetics.academic_hours:
            day_blocks = sorted(
                [ah for ah in genetics.academic_hours if ah.day_index == day_index],
                key=lambda ah: ah.index
            )
            valid = day_blocks[:-1]  # excluir último (no alcanza para 2 horas)
            return [ft.dropdown.Option(key=str(ah.index), text=f"{ah.start_hour} – {ah.end_hour}") for ah in valid]
        return []

    def _find_day_index(name_fragment):
        """Busca day_index por fragmento de nombre."""
        for idx, name in _get_days():
            if name_fragment.lower() in name.lower():
                return idx
        return 0

    def _last_valid_block(day_index):
        """Retorna el índice del penúltimo bloque del día (el mayor start_index válido)."""
        if genetics and hasattr(genetics, 'academic_hours') and genetics.academic_hours:
            day_blocks = sorted(
                [ah for ah in genetics.academic_hours if ah.day_index == day_index],
                key=lambda ah: ah.index
            )
            if len(day_blocks) >= 2:
                return day_blocks[-2].index
        return None

    # Valores por defecto: años 1-3 → martes, años 4-5 → jueves (igual que antes)
    _def_martes = _find_day_index("martes")
    _def_jueves = _find_day_index("jueves")
    _def_blk_martes = _last_valid_block(_def_martes) or 18
    _def_blk_jueves = _last_valid_block(_def_jueves) or 38

    _YEAR_DEFAULTS = {
        1: (_def_martes, _def_blk_martes),
        2: (_def_martes, _def_blk_martes),
        3: (_def_martes, _def_blk_martes),
        4: (_def_jueves, _def_blk_jueves),
        5: (_def_jueves, _def_blk_jueves),
    }

    # Dropdowns por año
    _day_dds = {}    # year -> ft.Dropdown
    _block_dds = {}  # year -> ft.Dropdown

    def _build_block_dd(day_index, default_block_idx):
        opts = _get_block_options(day_index)
        default_key = str(default_block_idx) if opts else None
        if opts and default_key not in [o.key for o in opts]:
            default_key = opts[-1].key  # fallback al último válido
        return ft.Dropdown(
            options=opts,
            value=default_key,
            border_color="#303346", focused_border_color="#439A5D",
            bgcolor="#13141C", color=ft.colors.WHITE,
            height=48, border_radius=8, expand=True,
            text_size=11,
        )

    def _on_day_change(e, year):
        new_day_idx = int(e.control.value)
        new_opts = _get_block_options(new_day_idx)
        blk_dd = _block_dds[year]
        blk_dd.options = new_opts
        blk_dd.value = new_opts[-1].key if new_opts else None
        blk_dd.update()

    _YEAR_LABELS = {1:"1° Año", 2:"2° Año", 3:"3° Año", 4:"4° Año", 5:"5° Año"}

    def _crear_fila_anio(year):
        def_day, def_blk = _YEAR_DEFAULTS[year]
        day_opts = [ft.dropdown.Option(key=str(idx), text=name) for idx, name in _get_days()]
        day_dd = ft.Dropdown(
            options=day_opts,
            value=str(def_day),
            border_color="#303346", focused_border_color="#439A5D",
            bgcolor="#13141C", color=ft.colors.WHITE,
            height=48, border_radius=8,
            text_size=11,
            width=110,
        )
        blk_dd = _build_block_dd(def_day, def_blk)
        day_dd.on_change = lambda e: _on_day_change(e, year)
        _day_dds[year] = day_dd
        _block_dds[year] = blk_dd
        return ft.Row([
            ft.Text(_YEAR_LABELS[year], color="#A0A0B0", size=12, width=52),
            day_dd,
            blk_dd,
        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    filas_comp = [_crear_fila_anio(y) for y in range(1, 6)]

    def _leer_comp_config():
        """Lee los valores actuales de los dropdowns y devuelve el dict de config."""
        config = {}
        for year in range(1, 6):
            try:
                day_idx = int(_day_dds[year].value)
                blk_idx = int(_block_dds[year].value)
                config[year] = {"day_index": day_idx, "start_index": blk_idx}
            except (TypeError, ValueError):
                pass
        return config


    def _generar_opciones_anio() -> tuple[list, str]:
        """Genera períodos escolares desde 2025-2026 hasta el año vigente + 1."""
        hoy = datetime.now()
        # Año de inicio del período vigente (lógica venezolana: sept-ago)
        if hoy.month >= 9:
            anio_vigente_inicio = hoy.year
        else:
            anio_vigente_inicio = hoy.year - 1

        anio_inicio_base = 2025  # primer período disponible
        anio_fin_gen = anio_vigente_inicio + 1  # generar un período hacia adelante

        opciones = [
            ft.dropdown.Option(f"{y} - {y + 1}")
            for y in range(anio_inicio_base, anio_fin_gen + 1)
        ]
        valor_actual = f"{anio_vigente_inicio} - {anio_vigente_inicio + 1}"
        return opciones, valor_actual

    _opciones_anio, _valor_anio = _generar_opciones_anio()
    dd_anio = ft.Dropdown(
        options=_opciones_anio,
        value=_valor_anio,
        border_color="#303346", focused_border_color="#439A5D",
        bgcolor="#13141C", color=ft.colors.WHITE,
        height=48, border_radius=10
    )

    def resetear_vista(page):
        estado_ref["generado"] = False
        estado_ref["en_progreso"] = False
        estado_ref["best_timetable"] = None
        estado_ref["final_report"] = None

        panel_info_container.content = crear_panel_inicial()
        badge_estado.visible = False
        btn_generar.visible = True
        btn_generar.disabled = False
        btn_regenerar.visible = False
        btn_exportar.visible = False
        progreso_bar.visible = False
        txt_progreso.visible = False
        page.update()

    def _abrir_selector_carpeta(page, button_triggered=None):
        """Abre el diálogo nativo de selección de carpeta antes de exportar."""
        if estado_ref.get("exportando"):
            return

        # AQUÍ ESTÁ LA CLAVE: Agregar file_picker a page.overlay si aún no está añadido
        if file_picker not in page.overlay:
            page.overlay.append(file_picker)
            page.update()

        estado_ref["_pending_export_button"] = button_triggered

        if button_triggered:
            button_triggered.disabled = True
            button_triggered.update()

        # Ahora sí se puede llamar de forma segura
        file_picker.get_directory_path(
            dialog_title="Seleccionar carpeta para exportar horarios"
        )

    def ejecutar_exportacion(page, output_dir="data/export", button_triggered=None):
        if estado_ref.get("exportando"):
            return
        
        estado_ref["exportando"] = True

        if button_triggered:
            button_triggered.disabled = True
            button_triggered.text = "Exportando horarios..."
            button_triggered.update()

        btn_exportar.disabled = True
        btn_exportar.text = "Exportando horarios..."
        page.update()

        try:
            pdf_dir = os.path.join(output_dir, "Horarios PDF")
            excel_dir = os.path.join(output_dir, "Horarios Excel")
            os.makedirs(pdf_dir, exist_ok=True)
            os.makedirs(excel_dir, exist_ok=True)

            best_timetable = estado_ref.get("best_timetable")
            if best_timetable is not None:
                if export_all is not None:
                    export_all(
                        timetable=best_timetable,
                        output_dir=pdf_dir,
                        year_label=dd_anio.value
                    )

                if export_all_teachers is not None:
                    export_all_teachers(
                        timetable=best_timetable,
                        output_dir=pdf_dir,
                        year_label=dd_anio.value
                    )

                if export_all_excel is not None:
                    export_all_excel(
                        timetable=best_timetable,
                        output_dir=excel_dir,
                        year_label=dd_anio.value
                    )

                if export_all_teachers_excel is not None:
                    export_all_teachers_excel(
                        timetable=best_timetable,
                        output_dir=excel_dir,
                        year_label=dd_anio.value
                    )

            badge_estado.visible = True
            
            page.snack_bar = ft.SnackBar(
                ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="#439A5D"),
                    ft.Text(f"Horarios exportados exitosamente en '{output_dir}'", color=ft.colors.WHITE)
                ]),
                bgcolor="#1A2A20"
            )
            page.snack_bar.open = True
        except Exception as ex:
            page.snack_bar = ft.SnackBar(
                ft.Row(
                    [
                        ft.Icon(ft.icons.ERROR_OUTLINE, color="#FF6B6B"),
                        ft.Text(
                            f"Error durante la exportación: {str(ex)}",
                            color=ft.colors.WHITE,
                        ),
                    ]
                ),
                bgcolor="#3A1C1C",
            )
            page.snack_bar.open = True

        finally:
            estado_ref["exportando"] = False
            
            if button_triggered:
                button_triggered.text = "Exportado Exitosamente"
                button_triggered.icon = ft.icons.CHECK_CIRCLE
                button_triggered.bgcolor = "#1A3A2A"
                button_triggered.disabled = True

            btn_exportar.disabled = False
            btn_exportar.text = "Exportar Horarios"
            btn_exportar.visible = True
            btn_regenerar.visible = True
            btn_regenerar.disabled = False
            
            page.update()

    # -------------------------------------------------------------
    # FUNCIONES DE FORMATEO CONECTADAS A ESTRUCTURAS DE GENETICS
    # -------------------------------------------------------------
    def fmt_bloque(block_val):
        if block_val is None:
            return "Bloque N/A"
        try:
            b_int = int(block_val)
        except (ValueError, TypeError):
            return str(block_val)

        # 1. Buscar en la lista academic_hours de genetics
        if genetics and hasattr(genetics, 'academic_hours') and genetics.academic_hours:
            for ah in genetics.academic_hours:
                if getattr(ah, 'index', None) == b_int or getattr(ah, 'db_id', None) == b_int:
                    return f"{ah.start_hour} a {ah.end_hour}"
            if 0 <= b_int < len(genetics.academic_hours):
                ah = genetics.academic_hours[b_int]
                return f"{ah.start_hour} a {ah.end_hour}"

        # 2. Fallback por cálculo predeterminado
        bloques_hora = [
            "7:00 a 7:40", "7:40 a 8:20", "8:20 a 9:00", 
            "9:00 a 9:40", "9:40 a 10:20", "10:20 a 11:00", 
            "11:00 a 11:40", "11:40 a 12:20", "12:20 a 1:00"
        ]
        return bloques_hora[b_int % len(bloques_hora)]

    def fmt_profesor(teacher_ref):
        if teacher_ref is None:
            return "Sin Profesor"
        
        # Si viene el objeto Teacher directamente
        if hasattr(teacher_ref, 'name'):
            lname = getattr(teacher_ref, 'last_name', '')
            return f"{teacher_ref.name} {lname}".strip()
        
        if isinstance(teacher_ref, dict):
            return teacher_ref.get('name') or teacher_ref.get('nombre') or f"Profesor {teacher_ref.get('id', '')}"
        
        try:
            t_id = int(teacher_ref)
        except (ValueError, TypeError):
            return str(teacher_ref)

        # Buscar en TEACHERS_BY_ID de genetics
        if genetics and hasattr(genetics, 'TEACHERS_BY_ID') and t_id in genetics.TEACHERS_BY_ID:
            t = genetics.TEACHERS_BY_ID[t_id]
            return f"{t.name} {t.last_name}".strip()
        
        if genetics and hasattr(genetics, 'teachers') and genetics.teachers:
            for t in genetics.teachers:
                if getattr(t, 'id', None) == t_id:
                    return f"{t.name} {t.last_name}".strip()

        return f"Profesor #{t_id}"

    def fmt_grupo_nombre(group_ref):
        if group_ref is None:
            return "Sin Grupo"

        if hasattr(group_ref, 'name'):
            return group_ref.name

        if isinstance(group_ref, dict):
            return group_ref.get('name') or group_ref.get('nombre') or f"Grupo {group_ref.get('id', '')}"

        try:
            g_id = int(group_ref)
        except (ValueError, TypeError):
            return str(group_ref)

        # Buscar en GROUPS_BY_ID de genetics
        if genetics and hasattr(genetics, 'GROUPS_BY_ID') and g_id in genetics.GROUPS_BY_ID:
            g = genetics.GROUPS_BY_ID[g_id]
            return g.name

        if genetics and hasattr(genetics, 'groups') and genetics.groups:
            for g in genetics.groups:
                if getattr(g, 'id', None) == g_id:
                    return g.name

        return f"Grupo #{g_id}"

    def fmt_aula_nombre(room_ref):
        if room_ref is None:
            return "Sin Aula"

        if hasattr(room_ref, 'name'):
            return room_ref.name

        if isinstance(room_ref, dict):
            return room_ref.get('name') or room_ref.get('nombre') or f"Aula {room_ref.get('id', '')}"

        try:
            r_id = int(room_ref)
        except (ValueError, TypeError):
            return str(room_ref)

        # Buscar en rooms de genetics
        if genetics and hasattr(genetics, 'rooms') and genetics.rooms:
            for r in genetics.rooms:
                if getattr(r, 'id', None) == r_id:
                    return r.name

        return f"Aula #{r_id}"

    def fmt_materia_nombre(subject_ref):
        if subject_ref is None:
            return "Materia N/A"

        if hasattr(subject_ref, 'name'):
            return subject_ref.name

        if isinstance(subject_ref, dict):
            return subject_ref.get('name') or subject_ref.get('subject_name') or f"Materia #{subject_ref.get('id', '')}"

        try:
            s_id = int(subject_ref)
        except (ValueError, TypeError):
            return str(subject_ref)

        # Buscar en SUBJECTS_BY_ID de genetics
        if genetics and hasattr(genetics, 'SUBJECTS_BY_ID') and s_id in genetics.SUBJECTS_BY_ID:
            s = genetics.SUBJECTS_BY_ID[s_id]
            return s.name

        if genetics and hasattr(genetics, 'subjects') and genetics.subjects:
            for s in genetics.subjects:
                if getattr(s, 'id', None) == s_id:
                    return s.name

        return f"Materia #{s_id}"

    def fmt_evento(e):
        if not e:
            return "Evento N/A"

        subj_ref = None
        group_ref = None

        if isinstance(e, dict):
            subj_ref = e.get('subject') or e.get('subject_id') or e.get('subject_name')
            group_ref = e.get('group') or e.get('group_id')
        elif hasattr(e, 'subject'):
            subj_ref = e.subject
            group_ref = getattr(e, 'group', None)
        else:
            subj_ref = e

        materia = fmt_materia_nombre(subj_ref)
        
        if group_ref is not None:
            grp_nombre = fmt_grupo_nombre(group_ref)
            return f"'{materia}' ({grp_nombre})"
        return f"'{materia}'"

    # -------------------------------------------------------------
    # CONSTRUCCIÓN DEL PANEL DE REPORTE DE CHOQUES (AUDITORÍA)
    # -------------------------------------------------------------
    def construir_vista_reporte(report, page):
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        total_fitness = report.get("total_fitness", 0)

        color_fitness = "#439A5D" if total_fitness < 8000 else "#FF6B6B"
        
        items_reporte = [
            ft.Row([
                ft.Column([
                    ft.Text("Reporte de calidad del horario", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                    ft.Text(f"Puntaje de Horario Final: {total_fitness}", size=13, color=color_fitness, weight=ft.FontWeight.BOLD)
                ]),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(color="#303346", height=12)
        ]

        def helper_seccion(titulo, lista, fn_formato, icono=ft.icons.WARNING_AMBER_ROUNDED):
            cant = len(lista)
            if cant == 0:
                return ft.Container(
                    bgcolor="#1A2A20", border_radius=8, padding=10,
                    content=ft.Row([
                        ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, color="#439A5D", size=16),
                        ft.Text(f"{titulo}: Sin conflictos detectados", color="#439A5D", size=12, weight=ft.FontWeight.BOLD)
                    ])
                )
            
            filas = [
                ft.Row([
                    ft.Icon(icono, color="#FF6B6B", size=16),
                    ft.Text(f"{titulo} ({cant}):", color="#FF6B6B", size=13, weight=ft.FontWeight.BOLD)
                ])
            ]
            for elem in lista:
                filas.append(
                    ft.Text(f"  • {fn_formato(elem)}", color="#D0D0E0", size=11)
                )
            return ft.Container(
                bgcolor="#2A1C1C", border_radius=8, padding=10,
                content=ft.Column(filas, spacing=4),
                border=ft.border.all(1, "#5A2A2A")
            )

        # 1. Choques de Grupos
        def fmt_grupo(f):
            e1 = f.get('event_1', {})
            e2 = f.get('event_2', {})
            grp = fmt_grupo_nombre(f.get('group', ''))
            blk = fmt_bloque(f.get('block', ''))
            return f"La seccion {grp} tiene un choque entre la asignatura {fmt_evento(e1)} y {fmt_evento(e2)} en el bloque {blk}."

        items_reporte.append(helper_seccion("Choques de Grupos", report.get("group_collisions", []), fmt_grupo))

        # 2. Choques de Profesores
        def fmt_prof(f):
            e1 = f.get('event_1', {})
            e2 = f.get('event_2', {})
            prof = fmt_profesor(f.get('teacher_name') or f.get('teacher_id') or f.get('teacher', ''))
            blk = fmt_bloque(f.get('block', ''))
            return f"El profesor {prof} tiene un conflicto entre {fmt_evento(e1)} y {fmt_evento(e2)} en el bloque {blk}"

        items_reporte.append(helper_seccion("Choques de Profesores", report.get("teacher_collisions", []), fmt_prof))

        # 3. Choques de Aulas
        def fmt_aula(f):
            e1 = f.get('event_1', {})
            e2 = f.get('event_2', {})
            aula = fmt_aula_nombre(f.get('room_name') or f.get('room_id') or f.get('room', ''))
            blk = fmt_bloque(f.get('block', ''))
            return f"Las asignaturas {fmt_evento(e1)} y {fmt_evento(e2)} tienen un conflicto en el {aula} en el bloque {blk}."

        items_reporte.append(helper_seccion("Choques de Aulas", report.get("room_collisions", []), fmt_aula))

        # 4. Baches y Ventanas Horarias
        def fmt_gap(f):
            day_idx = f.get('day', 0)
            dia_str = dias_semana[day_idx] if isinstance(day_idx, int) and 0 <= day_idx < len(dias_semana) else str(day_idx)
            grp = fmt_grupo_nombre(f.get('group', ''))
            tipo = f.get('type', 'Hueco intermedio')
            
            if 'gaps_count' in f:
                detalle = f"tiene {f.get('gaps_count')} horas libres en los bloques: {f.get('hours', [])}"
            elif 'hours_count' in f:
                detalle = f"tiene una carga horaria de {f.get('hours_count')} horas"
            elif 'first_hour' in f:
                detalle = f"tiene entrada tardia a las {fmt_bloque(f.get('first_hour'))}"
            else:
                detalle = ""
            return f"La seccion {grp} {detalle} el dia {dia_str}.".strip()

        items_reporte.append(helper_seccion("Baches y Ventanas Horarias", report.get("gaps", []), fmt_gap, ft.icons.SCHEDULE_ROUNDED))

        # 5. Materias Repetidas el Mismo Día
        def fmt_rep(f):
            day_idx = f.get('day', 0)
            dia_str = dias_semana[day_idx] if isinstance(day_idx, int) and 0 <= day_idx < len(dias_semana) else str(day_idx)
            grp = fmt_grupo_nombre(f.get('group', ''))
            materia = fmt_materia_nombre(f.get('subject') or f.get('subject_name'))
            return f"La materia {materia} se dicta de forma repetida los dias {dia_str} para la seccion {grp}."

        items_reporte.append(helper_seccion("Materias Repetidas el Mismo Día", report.get("subject_duplications", []), fmt_rep, ft.icons.REPEAT_ROUNDED))

        # 6. Distribución de Horarios de Viernes
        def fmt_viernes(f):
            grp = fmt_grupo_nombre(f.get('group', ''))
            tipo = f.get('type', '')
            afternoon_hours = f.get('afternoon_hours', [])
            if afternoon_hours:
                return f"La sección {grp}: {tipo} (horas: {', '.join(afternoon_hours)})."
            return f"La sección {grp}: {tipo}."

        items_reporte.append(helper_seccion("Distribución de Horarios de Viernes", report.get("friday_distribution", []), fmt_viernes, ft.icons.EVENT_AVAILABLE_ROUNDED))

        btn_si_exportar = ft.ElevatedButton(
            "Sí, Exportar",
            icon=ft.icons.DOWNLOAD_ROUNDED,
            bgcolor="#439A5D", color=ft.colors.WHITE, height=42
        )
        btn_si_exportar.on_click = lambda e: _abrir_selector_carpeta(page, button_triggered=e.control)

        btn_no_descartar = ft.OutlinedButton(
            "No, Descartar",
            icon=ft.icons.CLOSE_ROUNDED,
            style=ft.ButtonStyle(color="#A0A0B0", side=ft.BorderSide(1, "#303346")), height=42,
            on_click=lambda _: resetear_vista(page)
        )

        bloque_decision = ft.Container(
            bgcolor="#13141C", border_radius=10, padding=15,
            border=ft.border.all(1, "#303346"),
            content=ft.Column([
                ft.Text("¿Desea exportar este horario?", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                ft.Row([btn_si_exportar, btn_no_descartar], spacing=10)
            ], spacing=10)
        )

        items_reporte.append(ft.Divider(color="#303346", height=8))
        items_reporte.append(bloque_decision)

        return ft.Column(items_reporte, scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)

    # -------------------------------------------------------------
    # EJECUCIÓN DEL ALGORITMO GENÉTICO EN SEGUNDO PLANO
    # -------------------------------------------------------------
    def _reset_ui_post_generacion(page):
        """Restaura botones y UI al terminar o cancelar la generación."""
        estado_ref["en_progreso"] = False
        estado_ref["detener"] = False
        progreso_bar.visible = False
        txt_progreso.visible = False
        btn_detener.visible = False
        btn_generar.disabled = False
        btn_generar.visible = True
        btn_regenerar.disabled = False
        page.update()

    def ejecutar_algoritmo_genetico(page):
        max_generaciones = 250

        if genetics is None:
            page.snack_bar = ft.SnackBar(ft.Text("Error: No se pudo importar src.engine.genetics"), bgcolor="#2A1C1C")
            page.snack_bar.open = True
            _reset_ui_post_generacion(page)
            return

        try:
            # ── Recargar datos desde BD para capturar cualquier cambio hecho en la interfaz ──
            if genetics and hasattr(genetics, 'reload_data'):
                txt_progreso.value = "Cargando datos actualizados desde la base de datos..."
                page.update()
                genetics.reload_data()

            # Leer config de actividad complementaria desde la UI
            comp_config = _leer_comp_config()
            if genetics and hasattr(genetics, 'set_complementary_config') and comp_config:
                genetics.set_complementary_config(comp_config)

            events = genetics.create_events()
            population = genetics.create_population(50, events, comp_config)

            past_value = 0
            count = 0

            academic_hours = getattr(genetics, 'academic_hours', None)
            academic_hours_limits = getattr(genetics, 'academic_hours_limits', None)

            for i in range(max_generaciones):
                # ── Chequeo de cancelación ──────────────────────────
                if estado_ref["detener"]:
                    txt_progreso.value = "Generación detenida por el usuario."
                    page.update()
                    _reset_ui_post_generacion(page)
                    return

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
                txt_progreso.value = f"Generación {i+1}/{max_generaciones} - Puntaje: {best_fitness}"
                page.update()

                if count > 150:
                    txt_progreso.value = f"Algoritmo convergido en gen {i+1}. Finalizando..."
                    page.update()
                    break

                past_value = best_fitness

            if academic_hours is not None and academic_hours_limits is not None:
                scores = genetics.fitness(population, academic_hours, academic_hours_limits)
            else:
                scores = genetics.fitness(population)

            fitness_population = list(zip(scores, population))
            fitness_population.sort(key=lambda x: x[0])
            best_timetable = fitness_population[0][1]
            
            estado_ref["best_timetable"] = best_timetable

            if hasattr(genetics, 'evaluate_and_report'):
                final_report = genetics.evaluate_and_report(best_timetable)
            else:
                final_report = {"total_fitness": fitness_population[0][0]}

            estado_ref["final_report"] = final_report
            panel_info_container.content = construir_vista_reporte(final_report, page)
            estado_ref["generado"] = True

            progreso_bar.visible = False
            txt_progreso.visible = False
            btn_detener.visible = False
            btn_generar.visible = False
            btn_regenerar.visible = True
            btn_regenerar.disabled = False
            btn_exportar.visible = True
            btn_exportar.disabled = False
            estado_ref["en_progreso"] = False
            estado_ref["detener"] = False
            page.update()

        except Exception as ex:
            import traceback
            err_msg = str(ex) or type(ex).__name__
            traceback.print_exc()  # sigue imprimiendo en consola para debug
            page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.icons.ERROR_ROUNDED, color="#FF6B6B", size=18),
                    ft.Text(
                        f"Error durante la generación: {err_msg}",
                        color=ft.colors.WHITE, size=12, expand=True
                    ),
                ]),
                bgcolor="#2A1C1C",
                duration=8000,
            )
            page.snack_bar.open = True
            _reset_ui_post_generacion(page)

    def iniciar_generacion(e):
        if estado_ref["en_progreso"]:
            return
        estado_ref["en_progreso"] = True
        estado_ref["detener"] = False
        progreso_bar.value = 0
        progreso_bar.visible = True
        txt_progreso.visible = True
        txt_progreso.value = "Iniciando algoritmo genético..."
        btn_generar.disabled = True
        btn_regenerar.disabled = True
        btn_exportar.visible = False
        badge_estado.visible = False
        btn_detener.visible = True
        btn_detener.disabled = False
        btn_detener.text = "Detener"
        e.page.update()

        threading.Thread(target=ejecutar_algoritmo_genetico, args=(e.page,), daemon=True).start()

    def regenerar(e):
        iniciar_generacion(e)

    def detener(e):
        estado_ref["detener"] = True
        btn_detener.disabled = True
        btn_detener.text = "Deteniendo..."
        e.page.update()

    def exportar(e):
        _abrir_selector_carpeta(e.page, button_triggered=e.control)

    btn_generar.on_click = iniciar_generacion
    btn_detener.on_click = detener
    btn_regenerar.on_click = regenerar
    btn_exportar.on_click = exportar

    panel_config = ft.Container(
        **estilo_tarjeta_oscura,
        content=ft.Column([
            ft.Text("Configuración", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ft.Text("Año Escolar", color="#A0A0B0", size=12),
            dd_anio,
            ft.Divider(color="#303346", height=8),
            ft.Row([
                ft.Icon(ft.icons.EVENT_NOTE_ROUNDED, color="#439A5D", size=16),
                ft.Text("Actividad Complementaria", size=13, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ], spacing=6),
            ft.Text(
                "Selecciona el día y bloque de inicio para cada año.",
                color="#6A6A80", size=11,
            ),
            ft.Row([
                ft.Text("", width=52),
                ft.Text("Día", color="#6A6A80", size=11, width=110),
                ft.Text("Bloque inicio", color="#6A6A80", size=11, expand=True),
            ], spacing=6),
            *filas_comp,
            ft.Divider(color="#303346", height=8),
            progreso_bar,
            txt_progreso,
            ft.Row([btn_generar, btn_regenerar], spacing=10),
            ft.Row([btn_detener], spacing=10),
            btn_exportar,
            badge_estado,
        ], spacing=10, scroll=ft.ScrollMode.AUTO)
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
                    ft.Text("Sistema de auditoría de choques activo", color="#439A5D", size=12)
                ])
            ),
        ], spacing=12)
    )

    # El FilePicker debe registrarse como overlay en la página.
    # Retornamos un contenedor que, al montarse, agrega el overlay.
    def _on_view_mount(e):
        page = e.page if hasattr(e, 'page') else e.control.page
        if page and file_picker not in (page.overlay or []):
            page.overlay.append(file_picker)
            page.update()

    main_container = ft.Container(
        padding=20, expand=True,
        on_click=None,
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
                        ft.Column(expand=4, spacing=20, controls=[panel_config, panel_stats], scroll=ft.ScrollMode.AUTO),
                        ft.Column(
                            expand=6,
                            spacing=0,
                            expand_loose=True,
                            controls=[
                                panel_info_container
                            ]
                        )
                    ]
                )
            ],
            expand=True,
            on_scroll_interval=0,
        )
    )

    # Registrar el file_picker en la página a través del did_mount del contenedor
    main_container.did_mount = _on_view_mount

    return main_container