import re
import flet as ft
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.services.salon_service import SalonService

# Instancia global del servicio
salon_service = SalonService()

# Constantes de configuración visual y dominio
TIPOS_SALON = ["Taller", "Normal"]

COLOR_TIPO = {
    "Taller": ("#332415", "#E69138"),
    "Normal": ("#1A3A5C", "#5B9BD5"),
}

ICONO_TIPO = {
    "Taller": ft.icons.BUILD,
    "Normal": ft.icons.MEETING_ROOM,
}


def vista_salones(on_volver_menu=None):
    # =========================================================================
    # 1. ASIGNACIÓN DE VARIABLES DE ESTADO LOCAL Y CONTROLES UI
    # =========================================================================
    cache_salones = []
    map_salones = {}

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

    tabla_salones = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(ft.Text("Salón", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Tipo", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Acciones", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
        **estilo_tabla,
    )

    txt_total = ft.Text("Salones registrados: 0", color="#A0A0B0", size=14, weight=ft.FontWeight.W_500)
    contadores_tipo = {
        t: ft.Text("0", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TIPO[t][1]) for t in TIPOS_SALON
    }

    id_actual = ft.Text(visible=False)
    txt_nombre = ft.TextField(
        label="Nombre del Salón",
        border_radius=10,
        border_color="#303346",
        focused_border_color="#439A5D",
        color=ft.colors.WHITE,
        label_style=ft.TextStyle(color="#A0A0B0"),
    )
    dd_tipo = ft.Dropdown(
        label="Tipo de Salón",
        options=[ft.dropdown.Option(t) for t in TIPOS_SALON],
        value="Normal",
        border_color="#303346",
        focused_border_color="#439A5D",
        border_radius=10,
        bgcolor="#13141C",
        color=ft.colors.WHITE,
        label_style=ft.TextStyle(color="#A0A0B0"),
    )

    # =========================================================================
    # 2. COMPILACIÓN DE CLOSURES Y FUNCIONES INTERNAS
    # =========================================================================
    def cerrar_modal_salon(e):
        modal_salon.open = False
        e.page.update()

    def cerrar_modal_info(e):
        modal_info.open = False
        e.page.update()

    def cerrar_modal_confirmacion(e):
        modal_confirmacion.open = False
        e.page.update()

    def cerrar_modal_advertencia(e):
        modal_advertencia.open = False
        e.page.update()

    def pre_guardar_salon(e):
        nombre = txt_nombre.value.strip() if txt_nombre.value else ""
        if not nombre:
            e.page.snack_bar = ft.SnackBar(ft.Text("El nombre es obligatorio"), bgcolor="#E57373")
            e.page.snack_bar.open = True
            e.page.update()
            return

        # Validación optimizada usando la caché en lugar de consultar la BD
        salon_actual_id = int(id_actual.value) if id_actual.value else None
        for s in cache_salones:
            if s.id != salon_actual_id:
                if s.nombre and s.nombre.strip().lower() == nombre.lower():
                    e.page.dialog = modal_advertencia
                    modal_advertencia.open = True
                    e.page.update()
                    return

        es_nuevo = not id_actual.value
        if not es_nuevo:
            modal_confirmacion.title = ft.Text(
                "¿Confirmar Cambios?", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE
            )
            modal_confirmacion.content = ft.Text(
                "¿Está seguro de que desea guardar las modificaciones realizadas?", color="#A0A0B0"
            )
            modal_confirmacion.actions = [
                ft.TextButton(
                    "No, Cancelar", on_click=cerrar_modal_confirmacion, style=ft.ButtonStyle(color="#A0A0B0")
                ),
                ft.ElevatedButton(
                    "Sí, Guardar",
                    on_click=ejecutar_guardado,
                    bgcolor="#439A5D",
                    color=ft.colors.WHITE,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                ),
            ]
            e.page.dialog = modal_confirmacion
            modal_confirmacion.open = True
            e.page.update()
        else:
            ejecutar_guardado(e)

    def ejecutar_guardado(e):
        nombre = txt_nombre.value.strip() if txt_nombre.value else ""
        tipo = dd_tipo.value
        es_nuevo = not id_actual.value

        with SessionLocal() as db:
            try:
                if es_nuevo:
                    salon_service.crear(db, nombre=nombre, tipo=tipo)
                else:
                    salon_service.actualizar(db, id=int(id_actual.value), nombre=nombre, tipo=tipo)

                if modal_confirmacion.open:
                    cerrar_modal_confirmacion(e)

                cerrar_modal_salon(e)
                txt_buscar.value = ""
                cargar_datos_db()

                if es_nuevo:
                    e.page.dialog = modal_info
                    modal_info.open = True
                e.page.update()

            except Exception as ex:
                e.page.snack_bar = ft.SnackBar(ft.Text(f"Error al guardar: {ex}"), bgcolor="#E57373")
                e.page.snack_bar.open = True
                e.page.update()

    def pedir_confirmacion_eliminar(sal_id: int, e):
        sal = map_salones.get(sal_id)
        nombre_salon = sal.nombre if sal else f"ID {sal_id}"

        modal_confirmacion.title = ft.Text(
            "¿Confirmar Eliminación?", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE
        )
        modal_confirmacion.content = ft.Text(
            f"¿Está seguro de que desea eliminar el espacio '{nombre_salon}'?", color="#A0A0B0"
        )
        modal_confirmacion.actions = [
            ft.TextButton(
                "No, Cancelar", on_click=cerrar_modal_confirmacion, style=ft.ButtonStyle(color="#A0A0B0")
            ),
            ft.ElevatedButton(
                "Sí, Confirmar",
                on_click=lambda ex: ejecutar_eliminacion(sal_id, ex),
                bgcolor="#E57373",
                color=ft.colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            ),
        ]
        e.page.dialog = modal_confirmacion
        modal_confirmacion.open = True
        e.page.update()

    def ejecutar_eliminacion(sal_id: int, e):
        with SessionLocal() as db:
            try:
                salon_service.eliminar(db, id=sal_id)
                cerrar_modal_confirmacion(e)
                txt_buscar.value = ""
                cargar_datos_db()
                e.page.update()
            except Exception as ex:
                e.page.snack_bar = ft.SnackBar(ft.Text(f"Error al eliminar: {ex}"), bgcolor="#E57373")
                e.page.snack_bar.open = True
                e.page.update()

    # =========================================================================
    # 3. DECLARACIÓN DE MODALES Y BÚSQUEDA
    # =========================================================================
    modal_salon = ft.AlertDialog(
        title=ft.Text("Formulario de Salón", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        content=ft.Container(
            width=460,
            content=ft.Column([
                id_actual,
                txt_nombre,
                dd_tipo,
            ], spacing=15, tight=True),
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=cerrar_modal_salon, style=ft.ButtonStyle(color="#A0A0B0")),
            ft.ElevatedButton(
                "Guardar Registro",
                on_click=pre_guardar_salon,
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
            ft.Text("Salón añadido exitosamente.", color="#A0A0B0", size=13, text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, tight=True, width=300),
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        actions=[
            ft.ElevatedButton(
                "OK",
                on_click=cerrar_modal_info,
                bgcolor="#439A5D",
                color=ft.colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            )
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        actions_padding=20,
    )

    modal_advertencia = ft.AlertDialog(
        content=ft.Column([
            ft.Icon(ft.icons.WARNING_ROUNDED, color="#E69138", size=50),
            ft.Text("Salón Duplicado", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE, size=16, text_align=ft.TextAlign.CENTER),
            ft.Text(
                "Estás intentando agregar o modificar un salón que ya existe, por favor verifícalo.",
                color="#A0A0B0",
                size=13,
                text_align=ft.TextAlign.CENTER,
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12, tight=True, width=300),
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        actions=[
            ft.ElevatedButton(
                "OK",
                on_click=cerrar_modal_advertencia,
                bgcolor="#E69138",
                color=ft.colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            )
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
        txt_nombre.value = ""
        dd_tipo.value = "Normal"
        e.page.dialog = modal_salon
        modal_salon.open = True
        e.page.update()

    def abrir_modal_editar(sal_id: int, e):
        sal = map_salones.get(sal_id)
        if not sal:
            return
        id_actual.value = str(sal.id)
        txt_nombre.value = sal.nombre
        dd_tipo.value = getattr(sal, "tipo", "Normal") or "Normal"
        e.page.dialog = modal_salon
        modal_salon.open = True
        e.page.update()

    def filtrar_salones(e):
        term = txt_buscar.value.lower().strip() if txt_buscar.value else ""
        renderizar_tabla(term)
        e.page.update()

    txt_buscar = ft.TextField(
        hint_text="Búsqueda por nombre o tipo",
        width=320,
        height=40,
        content_padding=ft.padding.only(left=15, right=10),
        border_radius=10,
        border_color="#303346",
        focused_border_color="#439A5D",
        prefix=ft.Icon(ft.icons.SEARCH, color="#A0A0B0", size=20),
        hint_style=ft.TextStyle(color="#5A5D70", size=13),
        text_style=ft.TextStyle(color=ft.colors.WHITE, size=13),
        on_change=filtrar_salones,
    )

    # =========================================================================
    # 4. CARGA DE DATOS (BD) Y RENDERIZADO OPTIMIZADO EN MEMORIA
    # =========================================================================
    def cargar_datos_db():
        nonlocal cache_salones
        with SessionLocal() as db:
            try:
                cache_salones = salon_service.obtener_todos(db) or []
                renderizar_tabla(txt_buscar.value.lower().strip() if txt_buscar.value else "")
            except Exception:
                txt_total.value = "Error al cargar salones"

    def renderizar_tabla(filtro=""):
        tabla_salones.rows.clear()
        map_salones.clear()
        conteo = {t: 0 for t in TIPOS_SALON}

        # Funciones de ordenamiento
        def natural_sort_key(s):
            if not s:
                return []
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

        def sort_key(sal):
            tipo = getattr(sal, "tipo", "Normal") or "Normal"
            try:
                tipo_idx = TIPOS_SALON.index(tipo)
            except ValueError:
                tipo_idx = len(TIPOS_SALON)
            return (tipo_idx, natural_sort_key(sal.nombre))

        registros_ordenados = sorted(cache_salones, key=sort_key)

        for sal in registros_ordenados:
            map_salones[sal.id] = sal
            tipo = getattr(sal, "tipo", "Normal") or "Normal"
            if tipo not in TIPOS_SALON:
                tipo = "Normal"
            
            nombre = sal.nombre.lower() if sal.nombre else ""
            conteo[tipo] += 1

            # Filtrado en memoria
            if filtro and (filtro not in nombre and filtro not in tipo.lower()):
                continue

            bg, col = COLOR_TIPO[tipo]
            icono = ICONO_TIPO[tipo]

            tabla_salones.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(
                        ft.Row([
                            ft.Icon(icono, color=col, size=18),
                            ft.Text(sal.nombre, color=ft.colors.WHITE, weight=ft.FontWeight.W_500, expand=True),
                        ], expand=True)
                    ),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(tipo, size=12, color=col, weight=ft.FontWeight.BOLD),
                            bgcolor=bg,
                            padding=ft.padding.symmetric(horizontal=12, vertical=5),
                            border_radius=10,
                        )
                    ),
                    ft.DataCell(
                        ft.Row([
                            ft.Container(
                                content=ft.IconButton(
                                    ft.icons.EDIT,
                                    icon_color="#A0A0B0",
                                    icon_size=16,
                                    on_click=lambda e, s_id=sal.id: abrir_modal_editar(s_id, e),
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
                                    on_click=lambda e, s_id=sal.id: pedir_confirmacion_eliminar(s_id, e),
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

        txt_total.value = f"Salones registrados: {len(cache_salones)}"
        for t in TIPOS_SALON:
            contadores_tipo[t].value = str(conteo.get(t, 0))

    # Carga inicial desde la base de datos
    cargar_datos_db()

    # =========================================================================
    # 5. RETORNO DEL CONTENEDOR UI
    # =========================================================================
    chips_tipos = ft.Row([
        ft.Container(
            bgcolor=COLOR_TIPO[t][0],
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            expand=True,
            content=ft.Row([
                ft.Icon(ICONO_TIPO[t], color=COLOR_TIPO[t][1], size=16),
                ft.Text(t, color=COLOR_TIPO[t][1], size=12, weight=ft.FontWeight.W_500),
                ft.VerticalDivider(width=5, color=ft.colors.TRANSPARENT),
                contadores_tipo[t],
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
        ) for t in TIPOS_SALON
    ], spacing=15)

    tarjeta_stats = ft.Container(
        **estilo_tarjeta_oscura,
        content=ft.Column([chips_tipos], spacing=0),
    )

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
                                ft.Text("Gestión de Salones", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.Text("Administra los espacios físicos disponibles para clases", size=14, color="#A0A0B0"),
                            ], spacing=2),
                        ]),
                        ft.ElevatedButton(
                            "Añadir Salón",
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
                                ft.Icon(ft.icons.MEETING_ROOM, color="#439A5D"),
                                ft.Text("Salones Registrados", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
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
                                        content=ft.Container(
                                            width=1280,
                                            content=tabla_salones,
                                        ),
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