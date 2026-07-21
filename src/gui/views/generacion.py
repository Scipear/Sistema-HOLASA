import flet as ft
import time

CURSOS_DISPONIBLES = [
    "4to - EO - A", "4to - EO - B", "4to - EL - A",
    "4to - MM - A", "4to - MT - A", "5to - EO - A", "5to - EL - A"
]

HORARIO_GENERADO_DEMO = {
    "4to - EO - A": {
        "Lunes":     ["Matemáticas / Prof. Navarro / Aula 3", "Matemáticas / Prof. Navarro / Aula 3",
                      "Física / Prof. Isea / Aula 5", "Física / Prof. Isea / Aula 5",
                      "", "Circ. Eléctricos / Prof. Peraza / Taller 2", "Circ. Eléctricos / Prof. Peraza / Taller 2",
                      "Ed. Física / - / Cancha", "Ed. Física / - / Cancha", ""],
        "Martes":    ["Lenguaje / Prof. López / Aula 1", "Lenguaje / Prof. López / Aula 1",
                      "", "", "Sist. Digitales / Prof. Isea / Lab 1", "Sist. Digitales / Prof. Isea / Lab 1",
                      "", "Matemáticas / Prof. Navarro / Aula 3", "Matemáticas / Prof. Navarro / Aula 3", ""],
        "Miércoles": ["Física / Prof. Isea / Aula 5", "Física / Prof. Isea / Aula 5",
                      "", "Circ. Eléctricos / Prof. Peraza / Taller 2", "Circ. Eléctricos / Prof. Peraza / Taller 2",
                      "", "Lenguaje / Prof. López / Aula 1", "", "", ""],
        "Jueves":    ["Sist. Digitales / Prof. Isea / Lab 1", "Sist. Digitales / Prof. Isea / Lab 1",
                      "", "Matemáticas / Prof. Navarro / Aula 3", "Matemáticas / Prof. Navarro / Aula 3",
                      "Ed. Física / - / Cancha", "Ed. Física / - / Cancha", "", "", ""],
        "Viernes":   ["Circ. Eléctricos / Prof. Peraza / Taller 2", "Circ. Eléctricos / Prof. Peraza / Taller 2",
                      "Lenguaje / Prof. López / Aula 1", "",
                      "Física / Prof. Isea / Aula 5", "Física / Prof. Isea / Aula 5",
                      "", "Sist. Digitales / Prof. Isea / Lab 1", "Sist. Digitales / Prof. Isea / Lab 1", ""],
    }
}

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
BLOQUES = [
    "7:00 - 7:40", "7:40 - 8:20", "8:30 - 9:10", "9:10 - 9:50",
    "9:50 - 10:30", "10:30 - 11:10", "11:10 - 11:50",
    "12:10 - 12:50", "12:50 - 1:30", "1:30 - 2:10"
]
RECESO = "11:50 - 12:10"

COLORES_MATERIAS = {}
PALETA_BG = ["#1A3A5C", "#1A2A20", "#332415", "#1A3A38", "#2A2D3E", "#3A1A2A", "#1C2A40"]
PALETA_TX = ["#5B9BD5", "#439A5D", "#E69138", "#76C7C0", "#C0C0C0", "#E091C0", "#8FBBDE"]

def color_materia(nombre):
    if not nombre:
        return None
    key = nombre.split("/")[0].strip()
    if key not in COLORES_MATERIAS:
        COLORES_MATERIAS[key] = PALETA_BG[len(COLORES_MATERIAS) % len(PALETA_BG)]
    return COLORES_MATERIAS[key]

def color_texto_materia(nombre):
    if not nombre:
        return None
    key = nombre.split("/")[0].strip()
    idx = list(COLORES_MATERIAS.keys()).index(key) if key in COLORES_MATERIAS else 0
    return PALETA_TX[idx % len(PALETA_TX)]

def vista_generacion():
    estilo_tarjeta_oscura = {
        "bgcolor": "#1E202D",
        "border_radius": 15,
        "padding": 20,
        "border": ft.border.all(1, "#303346")
    }

    estado_ref = {"generado": False, "en_progreso": False}

    grilla_ref = ft.Column(spacing=0)
    dd_curso_preview = ft.Dropdown(
        label="Seleccionar Curso",
        options=[ft.dropdown.Option(c) for c in CURSOS_DISPONIBLES],
        value=CURSOS_DISPONIBLES[0],
        border_color="#303346", focused_border_color="#439A5D", border_radius=10,
        bgcolor="#13141C", color=ft.colors.WHITE, width=240
    )

    progreso_bar = ft.ProgressBar(
        value=0, bgcolor="#1A1C28", color="#439A5D", height=6, border_radius=3, visible=False
    )
    txt_progreso = ft.Text("", color="#A0A0B0", size=12, visible=False)

    panel_vacio = ft.Container(
        expand=True,
        content=ft.Column([
            ft.Icon(ft.icons.CALENDAR_TODAY, size=60, color="#303346"),
            ft.Text("Sin horario generado", size=18, color="#5A5D70", weight=ft.FontWeight.BOLD),
            ft.Text("Configura los parámetros y presiona Generar Horario", size=13, color="#5A5D70"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
           alignment=ft.MainAxisAlignment.CENTER, spacing=12),
        alignment=ft.alignment.center
    )

    panel_resultado = ft.Container(expand=True, visible=False, content=ft.Column([
        ft.Row([
            ft.Icon(ft.icons.GRID_ON, color="#439A5D"),
            ft.Text("Horario Semanal", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ft.Container(expand=True),
            dd_curso_preview,
        ]),
        ft.Container(
            content=ft.Column([grilla_ref], scroll=ft.ScrollMode.AUTO),
            expand=True
        )
    ], spacing=15, expand=True))

    def celda_clase(contenido, is_receso=False):
        if is_receso:
            return ft.Container(
                height=38, bgcolor="#0F1018", border=ft.border.all(1, "#303346"),
                content=ft.Text("RECESO", color="#5A5D70", size=11, italic=True,
                                 text_align=ft.TextAlign.CENTER),
                alignment=ft.alignment.center
            )
        if not contenido:
            return ft.Container(height=50, bgcolor="#13141C", border=ft.border.all(1, "#222435"))
        partes = contenido.split(" / ")
        materia = partes[0] if len(partes) > 0 else ""
        profesor = partes[1] if len(partes) > 1 else ""
        aula = partes[2] if len(partes) > 2 else ""
        bg = color_materia(materia) or "#1E202D"
        col = color_texto_materia(materia) or "#A0A0B0"
        return ft.Container(
            height=50, bgcolor=bg, border=ft.border.all(1, "#303346"),
            padding=ft.padding.symmetric(horizontal=6, vertical=4),
            content=ft.Column([
                ft.Text(materia, color=col, size=11, weight=ft.FontWeight.BOLD,
                        overflow=ft.TextOverflow.ELLIPSIS, max_lines=1),
                ft.Text(profesor, color="#A0A0B0", size=10, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(aula, color="#5A5D70", size=9),
            ], spacing=1)
        )

    def celda_hora(hora, is_receso=False):
        return ft.Container(
            width=100, height=50 if not is_receso else 38,
            bgcolor="#1A1C28" if not is_receso else "#0F1018",
            border=ft.border.all(1, "#303346"),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            content=ft.Text(hora, color="#A0A0B0" if not is_receso else "#5A5D70",
                            size=10, text_align=ft.TextAlign.CENTER),
            alignment=ft.alignment.center
        )

    def celda_cabecera(texto):
        return ft.Container(
            expand=True, height=40, bgcolor="#1A1C28",
            border=ft.border.all(1, "#303346"),
            content=ft.Text(texto, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD,
                            size=12, text_align=ft.TextAlign.CENTER),
            alignment=ft.alignment.center
        )

    def construir_grilla(curso):
        grilla_ref.controls.clear()
        horario = HORARIO_GENERADO_DEMO.get(curso, {d: [""] * len(BLOQUES) for d in DIAS})
        grilla_ref.controls.append(
            ft.Row([celda_hora("Hora")] + [celda_cabecera(d) for d in DIAS], spacing=0)
        )
        for i, bloque in enumerate(BLOQUES):
            fila = [celda_hora(bloque)]
            for dia in DIAS:
                celdas_dia = horario.get(dia, [""] * len(BLOQUES))
                contenido = celdas_dia[i] if i < len(celdas_dia) else ""
                fila.append(ft.Container(expand=True, content=celda_clase(contenido)))
            grilla_ref.controls.append(ft.Row(fila, spacing=0))
            if i == 6:
                fila_receso = [celda_hora(RECESO, is_receso=True)] + [
                    ft.Container(expand=True, content=celda_clase("", is_receso=True)) for _ in DIAS
                ]
                grilla_ref.controls.append(ft.Row(fila_receso, spacing=0))

    def cambiar_curso_preview(e):
        construir_grilla(dd_curso_preview.value)
        e.page.update()

    dd_curso_preview.on_change = cambiar_curso_preview

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
            ft.Text("Generado correctamente", color="#439A5D", size=12, weight=ft.FontWeight.BOLD)
        ]),
        bgcolor="#1A2A20", border_radius=10,
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        border=ft.border.all(1, "#439A5D")
    )

    sw_priorizar_prof = ft.Switch(value=True, active_color="#439A5D")
    sw_priorizar_elec = ft.Switch(value=False, active_color="#439A5D")
    sw_priorizar_prio = ft.Switch(value=False, active_color="#439A5D")
    sw_min_vacios = ft.Switch(value=True, active_color="#439A5D")
    sw_aulas_tec = ft.Switch(value=True, active_color="#439A5D")

    dd_anio = ft.Dropdown(
        options=[ft.dropdown.Option("2024-2"), ft.dropdown.Option("2025-1")],
        value="2024-2",
        border_color="#303346", focused_border_color="#439A5D",
        bgcolor="#13141C", color=ft.colors.WHITE,
        height=45, border_radius=10
    )

    def fila_switch(etiqueta, sw):
        return ft.Row([
            ft.Text(etiqueta, color=ft.colors.WHITE, size=13, expand=True), sw
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def iniciar_generacion(e):
        if estado_ref["en_progreso"]:
            return
        estado_ref["en_progreso"] = True
        progreso_bar.visible = True
        txt_progreso.visible = True
        btn_generar.disabled = True
        btn_regenerar.disabled = True
        panel_vacio.visible = True
        panel_resultado.visible = False
        badge_estado.visible = False
        e.page.update()

        pasos = [
            ("Analizando disponibilidad docente...", 0.2),
            ("Asignando sesiones por mención...", 0.45),
            ("Optimizando distribución de aulas...", 0.65),
            ("Resolviendo conflictos de horario...", 0.85),
            ("Finalizando generación...", 1.0),
        ]
        for texto, valor in pasos:
            progreso_bar.value = valor
            txt_progreso.value = texto
            e.page.update()
            time.sleep(0.5)

        estado_ref["generado"] = True
        estado_ref["en_progreso"] = False
        COLORES_MATERIAS.clear()
        construir_grilla(dd_curso_preview.value)
        progreso_bar.visible = False
        txt_progreso.visible = False
        btn_generar.disabled = False
        btn_regenerar.disabled = False
        btn_generar.visible = False
        btn_regenerar.visible = True
        btn_exportar.visible = True
        badge_estado.visible = True
        panel_vacio.visible = False
        panel_resultado.visible = True
        e.page.update()

    def regenerar(e):
        btn_regenerar.visible = False
        btn_exportar.visible = False
        btn_generar.visible = True
        badge_estado.visible = False
        panel_vacio.visible = True
        panel_resultado.visible = False
        e.page.update()
        iniciar_generacion(e)

    def exportar(e):
        e.page.snack_bar = ft.SnackBar(
            ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE, color="#439A5D"),
                ft.Text("Horarios exportados correctamente", color=ft.colors.WHITE)
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
                bgcolor="#332415", border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                border=ft.border.all(1, "#E69138"),
                content=ft.Row([
                    ft.Icon(ft.icons.WARNING_AMBER, color="#E69138", size=16),
                    ft.Text("2 docentes sin disponibilidad completa", color="#E69138", size=12)
                ])
            ),
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
                        ft.Column(expand=3, spacing=20, controls=[panel_config, panel_stats]),
                        ft.Column(expand=7, spacing=0, expand_loose=True, controls=[
                            ft.Container(
                                **estilo_tarjeta_oscura,
                                expand=True,
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.icons.GRID_ON, color="#439A5D"),
                                        ft.Text("Vista Previa del Horario", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                    ]),
                                    ft.Container(
                                        expand=True,
                                        content=ft.Column([panel_vacio, panel_resultado], expand=True)
                                    )
                                ], spacing=15, expand=True)
                            )
                        ])
                    ]
                )
            ],
            expand=True
        )
    )
