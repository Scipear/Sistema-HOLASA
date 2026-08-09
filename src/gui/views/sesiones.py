import flet as ft
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.services.sesion_service import SesionService

# Instancia global del servicio
sesion_service = SesionService()

# Constantes globales
DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

# Prioridad de días para ordenamiento
PRIORIDAD_DIAS = {
    "lunes": 1,
    "martes": 2,
    "miercoles": 3,
    "miércoles": 3,
    "jueves": 4,
    "viernes": 5,
}

# Horarios académicos oficiales en formato 24 horas
HORAS_DISPONIBLES = [
    "07:00", "07:40", "08:20", "08:30", "09:10", "09:50",
    "10:30", "11:10", "11:50", "12:10", "12:50", "13:30", "14:10"
]

COLOR_DIA = {
    "Lunes": ("#1A3A5C", "#5B9BD5"),
    "Martes": ("#1A2A20", "#439A5D"),
    "Miércoles": ("#332415", "#E69138"),
    "Jueves": ("#1A3A38", "#76C7C0"),
    "Viernes": ("#3A1A30", "#D988B9"),
}


def normalizar_dia(dia_str: str) -> str:
    """Normaliza variantes de texto de días a la clave oficial con tildes."""
    if not dia_str:
        return ""
    texto = dia_str.strip().lower()
    if texto in ["miercoles", "miércoles"]:
        return "Miércoles"
    return dia_str.strip().capitalize()


def normalizar_hora(hora_str: str) -> str:
    """Convierte cadenas de hora ('H:MM', '01:30') al formato 24h estándar ('13:30')."""
    if not hora_str:
        return "07:00"
    try:
        partes = hora_str.strip().split(":")
        h = int(partes[0])
        m = int(partes[1])
        # Si la hora está entre 1 y 6 (formato 12h vespertino), ajustar a 24h (+12)
        if 1 <= h <= 6:
            h += 12
        return f"{h:02d}:{m:02d}"
    except (ValueError, IndexError):
        return hora_str.strip()


def obtener_indice_hora(hora_str: str) -> int:
    """Obtiene el índice de prioridad según la lista oficial HORAS_DISPONIBLES."""
    hora_norm = normalizar_hora(hora_str)
    if hora_norm in HORAS_DISPONIBLES:
        return HORAS_DISPONIBLES.index(hora_norm)
    
    # Cálculo alternativo en minutos en caso de horarios fuera de la lista estándar
    try:
        h, m = map(int, hora_norm.split(":"))
        return h * 60 + m
    except ValueError:
        return 9999


def vista_sesiones(on_volver_menu=None):
    # =========================================================================
    # 1. ASIGNACIÓN DE VARIABLES DE ESTADO LOCAL Y CONTROLES UI
    # =========================================================================
    cache_sesiones = []  # Caché en memoria para optimizar búsquedas

    estilo_tarjeta_oscura = {
        "bgcolor": "#1E202D",
        "border_radius": 15,
        "padding": 20,
        "border": ft.border.all(1, "#303346"),
    }

    estilo_tabla = {
        "bgcolor": "#13141C",
        "border_radius": 15,
        "border": ft.border.all(1, "#303346"),
        "horizontal_lines": ft.border.BorderSide(1, "#303346"),
        "vertical_lines": ft.border.BorderSide(0, ft.colors.TRANSPARENT),
        "heading_row_color": "#1A1C28",
        "data_row_max_height": 64,
    }

    tabla_sesiones = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(ft.Text("Día", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Hora Inicio", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Hora Fin", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Acciones", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
        **estilo_tabla
    )

    txt_total = ft.Text("Sesiones registradas: 0", color="#A0A0B0", size=14, weight=ft.FontWeight.W_500)
    contadores_dia = {
        d: ft.Text("0", size=16, weight=ft.FontWeight.BOLD, color=COLOR_DIA[d][1]) for d in DIAS_SEMANA
    }

    id_actual = ft.Text(visible=False)
    dd_dia = ft.Dropdown(
        label="Día de la Sesión",
        options=[ft.dropdown.Option(d) for d in DIAS_SEMANA],
        value="Lunes",
        border_color="#303346",
        focused_border_color="#439A5D",
        border_radius=10,
        bgcolor="#13141C",
        color=ft.colors.WHITE,
    )
    dd_inicio = ft.Dropdown(
        label="Hora de Inicio",
        options=[ft.dropdown.Option(h) for h in HORAS_DISPONIBLES],
        value="07:00",
        border_color="#303346",
        focused_border_color="#439A5D",
        border_radius=10,
        bgcolor="#13141C",
        color=ft.colors.WHITE,
    )
    dd_fin = ft.Dropdown(
        label="Hora Final",
        options=[ft.dropdown.Option(h) for h in HORAS_DISPONIBLES],
        value="07:40",
        border_color="#303346",
        focused_border_color="#439A5D",
        border_radius=10,
        bgcolor="#13141C",
        color=ft.colors.WHITE,
    )

    # =========================================================================
    # 2. CLOSURES Y FUNCIONES INTERNAS (FLUJO Y EVENTOS)
    # =========================================================================
    def cerrar_modal(e):
        modal_sesion.open = False
        e.page.update()

    def cerrar_modal_info(e):
        modal_info.open = False
        e.page.update()

    def cerrar_modal_confirmacion(e):
        modal_confirmacion.open = False
        e.page.update()

    def pre_guardar_sesion(e):
        idx_inicio = HORAS_DISPONIBLES.index(dd_inicio.value) if dd_inicio.value in HORAS_DISPONIBLES else 0
        idx_fin = HORAS_DISPONIBLES.index(dd_fin.value) if dd_fin.value in HORAS_DISPONIBLES else 0

        # Validación estricta de UI
        if idx_inicio >= idx_fin:
            e.page.snack_bar = ft.SnackBar(
                ft.Text("La hora de inicio debe ser menor a la hora final"), bgcolor="#E57373"
            )
            e.page.snack_bar.open = True
            e.page.update()
            return

        es_nuevo = id_actual.value == ""
        if not es_nuevo:
            modal_confirmacion.title = ft.Text("¿Confirmar Cambios?", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
            modal_confirmacion.content = ft.Text("¿Está seguro de que desea guardar las modificaciones realizadas?", color="#A0A0B0")
            modal_confirmacion.actions = [
                ft.TextButton("No, Cancelar", on_click=cerrar_modal_confirmacion, style=ft.ButtonStyle(color="#A0A0B0")),
                ft.ElevatedButton("Sí, Guardar", on_click=ejecutar_guardado, bgcolor="#439A5D", color=ft.colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
            ]
            e.page.dialog = modal_confirmacion
            modal_confirmacion.open = True
            e.page.update()
        else:
            ejecutar_guardado(e)

    def ejecutar_guardado(e):
        es_nuevo = id_actual.value == ""
        
        with SessionLocal() as db:
            try:
                dia_normalizado = normalizar_dia(dd_dia.value)
                hora_ini = normalizar_hora(dd_inicio.value)
                hora_fn = normalizar_hora(dd_fin.value)

                if es_nuevo:
                    sesion_service.crear(db, dia=dia_normalizado, hora_inicio=hora_ini, hora_fin=hora_fn)
                else:
                    ses_id = int(id_actual.value)
                    sesion_service.actualizar(db, id=ses_id, dia=dia_normalizado, hora_inicio=hora_ini, hora_fin=hora_fn)

                if modal_confirmacion.open:
                    cerrar_modal_confirmacion(e)

                cerrar_modal(e)
                txt_buscar.value = ""
                cargar_datos_db()  # Refresca los datos desde la BD

                if es_nuevo:
                    e.page.dialog = modal_info
                    modal_info.open = True
                e.page.update()

            except Exception as error:
                # Captura elegante de las validaciones del servicio (ej. superposiciones de horas)
                e.page.snack_bar = ft.SnackBar(ft.Text(str(error)), bgcolor="#E57373")
                e.page.snack_bar.open = True
                e.page.update()

    def pedir_confirmacion_eliminar(ses_data, e):
        modal_confirmacion.title = ft.Text("¿Confirmar Eliminación?", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
        modal_confirmacion.content = ft.Text(
            f"¿Está seguro de que desea eliminar el bloque del {ses_data['dia']} ({ses_data['hora_inicio']} - {ses_data['hora_fin']})?",
            color="#A0A0B0",
        )
        modal_confirmacion.actions = [
            ft.TextButton("No, Cancelar", on_click=cerrar_modal_confirmacion, style=ft.ButtonStyle(color="#A0A0B0")),
            ft.ElevatedButton(
                "Sí, Confirmar",
                on_click=lambda ex: ejecutar_eliminacion(ses_data["id"], ex),
                bgcolor="#E57373",
                color=ft.colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            ),
        ]
        e.page.dialog = modal_confirmacion
        modal_confirmacion.open = True
        e.page.update()

    def ejecutar_eliminacion(ses_id, e):
        with SessionLocal() as db:
            try:
                sesion_service.eliminar(db, int(ses_id))
                cerrar_modal_confirmacion(e)
                txt_buscar.value = ""
                cargar_datos_db()  # Refresca caché tras borrar
            except Exception as error:
                e.page.snack_bar = ft.SnackBar(ft.Text(str(error)), bgcolor="#E57373")
                e.page.snack_bar.open = True
        
        e.page.update()

    # =========================================================================
    # 3. DECLARACIÓN DE MODALES Y COMPONENTES DE BÚSQUEDA
    # =========================================================================
    modal_sesion = ft.AlertDialog(
        title=ft.Text("Formulario de Sesión", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        content=ft.Container(
            width=460,
            content=ft.Column([
                id_actual,
                dd_dia,
                dd_inicio,
                dd_fin,
            ], spacing=15, tight=True)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=cerrar_modal, style=ft.ButtonStyle(color="#A0A0B0")),
            ft.ElevatedButton(
                "Guardar Registro",
                on_click=pre_guardar_sesion,
                bgcolor="#439A5D",
                color=ft.colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            ),
        ],
        actions_padding=20,
    )

    modal_info = ft.AlertDialog(
        content=ft.Column([
            ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color="#439A5D", size=50),
            ft.Text("Éxito", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE, size=16, text_align=ft.TextAlign.CENTER),
            ft.Text("Sesión añadida exitosamente.", color="#A0A0B0", size=13, text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, tight=True, width=300),
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        actions=[
            ft.ElevatedButton("OK", on_click=cerrar_modal_info, bgcolor="#439A5D", color=ft.colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        actions_padding=20,
    )

    modal_confirmacion = ft.AlertDialog(
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        actions_padding=20,
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def abrir_modal_crear(e):
        id_actual.value = ""
        dd_dia.value = "Lunes"
        dd_inicio.value = "07:00"
        dd_fin.value = "07:40"
        e.page.dialog = modal_sesion
        modal_sesion.open = True
        e.page.update()

    def abrir_modal_editar(ses_data, e):
        id_actual.value = str(ses_data["id"])
        dd_dia.value = ses_data["dia"]
        dd_inicio.value = ses_data["hora_inicio"]
        dd_fin.value = ses_data["hora_fin"]
        e.page.dialog = modal_sesion
        modal_sesion.open = True
        e.page.update()

    def filtrar_sesiones(e):
        # Filtra exclusivamente en memoria
        term = txt_buscar.value.lower().strip()
        renderizar_tabla(term)
        e.page.update()

    txt_buscar = ft.TextField(
        hint_text="Búsqueda por día",
        width=320,
        height=40,
        content_padding=ft.padding.only(left=15, right=10),
        border_radius=10,
        border_color="#303346",
        focused_border_color="#439A5D",
        prefix=ft.Icon(ft.icons.SEARCH, color="#A0A0B0", size=20),
        hint_style=ft.TextStyle(color="#5A5D70", size=13),
        text_style=ft.TextStyle(color=ft.colors.WHITE, size=13),
        on_change=filtrar_sesiones,
    )

    # =========================================================================
    # 4. CARGA DESDE LA BD Y RENDERIZADO OPTIMIZADO (SEPARACIÓN LÓGICA)
    # =========================================================================
    def cargar_datos_db():
        """Carga masiva única desde la BD al caché local."""
        nonlocal cache_sesiones
        with SessionLocal() as db:
            try:
                cache_sesiones = sesion_service.obtener_todos(db) or []
            except Exception:
                cache_sesiones = []
                txt_total.value = "Error al cargar sesiones"
        renderizar_tabla(txt_buscar.value.lower().strip() if txt_buscar.value else "")

    def renderizar_tabla(filtro=""):
        """Renderiza los datos tomando la información únicamente del caché."""
        tabla_sesiones.rows.clear()
        conteo = {d: 0 for d in DIAS_SEMANA}

        # ORDENAMIENTO EN MEMORIA POR DÍA (1-5) Y LUEGO POR POSICIÓN DE LA HORA
        sesiones_ordenadas = sorted(
            cache_sesiones,
            key=lambda s: (
                PRIORIDAD_DIAS.get(s.dia.strip().lower(), 99),
                obtener_indice_hora(s.hora_inicio),
            )
        )

        for ses in sesiones_ordenadas:
            dia_norm = normalizar_dia(ses.dia)
            hora_ini_norm = normalizar_hora(ses.hora_inicio)
            hora_fin_norm = normalizar_hora(ses.hora_fin)

            if dia_norm in conteo:
                conteo[dia_norm] += 1

            if filtro and filtro not in dia_norm.lower():
                continue

            bg, col = COLOR_DIA.get(dia_norm, ("#2A2D3E", "#A0A0B0"))
            ses_data = {
                "id": ses.id,
                "dia": dia_norm,
                "hora_inicio": hora_ini_norm,
                "hora_fin": hora_fin_norm,
            }

            tabla_sesiones.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(dia_norm, size=12, color=col, weight=ft.FontWeight.BOLD),
                            bgcolor=bg,
                            padding=ft.padding.symmetric(horizontal=12, vertical=5),
                            border_radius=10,
                        )
                    ),
                    ft.DataCell(ft.Text(hora_ini_norm, color=ft.colors.WHITE, weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(hora_fin_norm, color=ft.colors.WHITE, weight=ft.FontWeight.W_500)),
                    ft.DataCell(
                        ft.Row([
                            ft.Container(
                                content=ft.IconButton(
                                    ft.icons.EDIT,
                                    icon_color="#A0A0B0",
                                    icon_size=16,
                                    on_click=lambda e, s=ses_data: abrir_modal_editar(s, e),
                                ),
                                bgcolor="#2A2D3E",
                                border_radius=8,
                                width=32,
                                height=32,
                            ),
                            ft.Container(
                                content=ft.IconButton(
                                    ft.icons.DELETE,
                                    icon_color="#E57373",
                                    icon_size=16,
                                    on_click=lambda e, s=ses_data: pedir_confirmacion_eliminar(s, e),
                                ),
                                bgcolor="#3E2A2A",
                                border_radius=8,
                                width=32,
                                height=32,
                            ),
                        ], spacing=10)
                    ),
                ])
            )

        # Actualiza totales visuales
        txt_total.value = f"Sesiones registradas: {len(cache_sesiones)}"
        for d in DIAS_SEMANA:
            contadores_dia[d].value = str(conteo[d])

    # Carga inicial de datos al abrir la vista
    cargar_datos_db()

    # =========================================================================
    # 5. RETORNO DEL CONTENEDOR PRINCIPAL DE UI
    # =========================================================================
    chips_dias = ft.Row(
        [
            ft.Container(
                bgcolor=COLOR_DIA[d][0],
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                expand=True,
                content=ft.Row(
                    [
                        ft.Icon(ft.icons.ACCESS_TIME, color=COLOR_DIA[d][1], size=16),
                        ft.Text(d, color=COLOR_DIA[d][1], size=11, weight=ft.FontWeight.W_500),
                        ft.VerticalDivider(width=5, color=ft.colors.TRANSPARENT),
                        contadores_dia[d],
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5,
                ),
            )
            for d in DIAS_SEMANA
        ],
        spacing=10,
    )

    tarjeta_stats = ft.Container(**estilo_tarjeta_oscura, content=ft.Column([chips_dias], spacing=0))

    return ft.Container(
        padding=20,
        expand=True,
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Row([
                            ft.IconButton(
                                ft.icons.ARROW_BACK,
                                icon_color="#A0A0B0",
                                on_click=on_volver_menu if on_volver_menu else lambda e: None,
                            ) if on_volver_menu else ft.Container(),
                            ft.Column([
                                ft.Text("Gestión de Sesiones", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.Text("Define los bloques de horas académicas y días hábiles", size=14, color="#A0A0B0"),
                            ], spacing=2),
                        ]),
                        ft.ElevatedButton(
                            "Añadir Sesión",
                            icon=ft.icons.ADD,
                            on_click=abrir_modal_crear,
                            bgcolor="#439A5D",
                            color=ft.colors.WHITE,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=20),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                tarjeta_stats,
                ft.Divider(height=5, color=ft.colors.TRANSPARENT),
                ft.Container(
                    **estilo_tarjeta_oscura,
                    expand=True,
                    content=ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Icon(ft.icons.ACCESS_TIME, color="#439A5D"),
                                ft.Text("Sesiones Registradas", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.VerticalDivider(width=10, color=ft.colors.TRANSPARENT),
                                txt_total,
                            ]),
                            txt_buscar,
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=5, color=ft.colors.TRANSPARENT),
                        ft.Column(
                            [
                                ft.Row([
                                    ft.Container(
                                        expand=True,
                                        alignment=ft.alignment.center,
                                        content=ft.Container(width=1280, content=tabla_sesiones),
                                    )
                                ])
                            ],
                            expand=True,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                    ], spacing=15, expand=True),
                ),
            ],
            expand=True,
        ),
    )