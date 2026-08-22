import flet as ft
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.services.mencion_service import MencionService

# Instancia global del servicio 
mencion_service = MencionService()


def vista_menciones(on_volver_menu=None):
    # =========================================================================
    # 1. ASIGNACIÓN DE VARIABLES DE ESTADO LOCAL Y CONTROLES UI
    # =========================================================================
    cache_menciones = []
    map_menciones = {}

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

    tabla_menciones = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(
                ft.Text(
                    "Mención", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD
                )
            ),
            ft.DataColumn(
                ft.Text(
                    "Acciones",
                    color=ft.colors.WHITE,
                    weight=ft.FontWeight.BOLD,
                )
            ),
        ],
        rows=[],
        **estilo_tabla,
    )

    txt_total = ft.Text(
        "Menciones registradas: 0",
        color="#A0A0B0",
        size=14,
        weight=ft.FontWeight.W_500,
    )

    id_actual = ft.Text(visible=False)
    txt_nombre = ft.TextField(
        label="Nombre de la Mención",
        border_radius=10,
        border_color="#303346",
        focused_border_color="#439A5D",
        color=ft.colors.WHITE,
        label_style=ft.TextStyle(color="#A0A0B0"),
    )

    # =========================================================================
    # 2. FUNCIONES INTERNAS Y MANEJO DE EVENTOS
    # =========================================================================
    def cerrar_modal_mencion(e):
        modal_mencion.open = False
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

    def pre_guardar_mencion(e):
        nombre = txt_nombre.value.strip() if txt_nombre.value else ""
        if not nombre:
            e.page.snack_bar = ft.SnackBar(
                ft.Text("El nombre es obligatorio"), bgcolor="#E57373"
            )
            e.page.snack_bar.open = True
            e.page.update()
            return

        # Validación de duplicados local contra la caché antes de persistir
        mencion_actual_id = int(id_actual.value) if id_actual.value else None
        for m in cache_menciones:
            if m.id != mencion_actual_id:
                if m.nombre and m.nombre.strip().lower() == nombre.lower():
                    e.page.dialog = modal_advertencia
                    modal_advertencia.open = True
                    e.page.update()
                    return

        es_nuevo = id_actual.value == ""
        if not es_nuevo:
            modal_confirmacion.title = ft.Text(
                "¿Confirmar Cambios?",
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
            )
            modal_confirmacion.content = ft.Text(
                "¿Está seguro de que desea guardar las modificaciones realizadas?",
                color="#A0A0B0",
            )
            modal_confirmacion.actions = [
                ft.TextButton(
                    "No, Cancelar",
                    on_click=cerrar_modal_confirmacion,
                    style=ft.ButtonStyle(color="#A0A0B0"),
                ),
                ft.ElevatedButton(
                    "Sí, Guardar",
                    on_click=ejecutar_guardado,
                    bgcolor="#439A5D",
                    color=ft.colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                ),
            ]
            e.page.dialog = modal_confirmacion
            modal_confirmacion.open = True
            e.page.update()
        else:
            ejecutar_guardado(e)

    def ejecutar_guardado(e):
        nombre = txt_nombre.value.strip() if txt_nombre.value else ""
        es_nuevo = id_actual.value == ""

        with SessionLocal() as db:
            try:
                if es_nuevo:
                    mencion_service.crear(db, nombre=nombre)
                else:
                    mencion_service.actualizar(db, id=int(id_actual.value), nombre=nombre)

                if modal_confirmacion.open:
                    cerrar_modal_confirmacion(e)

                cerrar_modal_mencion(e)
                txt_buscar.value = ""
                cargar_datos_db()  # Refrescar la caché local desde la BD

                if es_nuevo:
                    e.page.dialog = modal_info
                    modal_info.open = True
                e.page.update()

            except ValueError as ve:
                e.page.snack_bar = ft.SnackBar(ft.Text(str(ve)), bgcolor="#E57373")
                e.page.snack_bar.open = True
                e.page.update()
            except Exception as ex:
                error_msg = (
                    "Ya existe una mención con este nombre."
                    if "UNIQUE" in str(ex).upper()
                    else f"Error al guardar: {ex}"
                )
                e.page.snack_bar = ft.SnackBar(ft.Text(error_msg), bgcolor="#E57373")
                e.page.snack_bar.open = True
                e.page.update()

    def pedir_confirmacion_eliminar(men_id: int, e):
        men = map_menciones.get(men_id)
        nombre_men = men.nombre if men else f"ID {men_id}"

        modal_confirmacion.title = ft.Text(
            "¿Confirmar Eliminación?",
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE,
        )
        modal_confirmacion.content = ft.Text(
            f"¿Está seguro de que desea eliminar la mención '{nombre_men}'?",
            color="#A0A0B0",
        )
        modal_confirmacion.actions = [
            ft.TextButton(
                "No, Cancelar",
                on_click=cerrar_modal_confirmacion,
                style=ft.ButtonStyle(color="#A0A0B0"),
            ),
            ft.ElevatedButton(
                "Sí, Confirmar",
                on_click=lambda ex: ejecutar_eliminacion(men_id, ex),
                bgcolor="#E57373",
                color=ft.colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            ),
        ]
        e.page.dialog = modal_confirmacion
        modal_confirmacion.open = True
        e.page.update()

    def ejecutar_eliminacion(men_id: int, e):
        with SessionLocal() as db:
            try:
                mencion_service.eliminar(db, id=men_id)
                cerrar_modal_confirmacion(e)
                txt_buscar.value = ""
                cargar_datos_db()  # Sincroniza la tabla eliminando el registro
                e.page.update()
            except Exception as ex:
                e.page.snack_bar = ft.SnackBar(
                    ft.Text(f"Error al eliminar: {ex}"), bgcolor="#E57373"
                )
                e.page.snack_bar.open = True
                e.page.update()

    # =========================================================================
    # 3. DECLARACIÓN DE MODALES Y BÚSQUEDA
    # =========================================================================
    modal_mencion = ft.AlertDialog(
        title=ft.Text(
            "Formulario de Mención",
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE,
        ),
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        content=ft.Container(
            width=460,
            content=ft.Column(
                [
                    id_actual,
                    txt_nombre,
                ],
                spacing=15,
                tight=True,
            ),
        ),
        actions=[
            ft.TextButton(
                "Cancelar",
                on_click=cerrar_modal_mencion,
                style=ft.ButtonStyle(color="#A0A0B0"),
            ),
            ft.ElevatedButton(
                "Guardar Registro",
                on_click=pre_guardar_mencion,
                bgcolor="#439A5D",
                color=ft.colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            ),
        ],
        actions_padding=20,
    )

    modal_info = ft.AlertDialog(
        content=ft.Column(
            [
                ft.Icon(
                    ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                    color="#439A5D",
                    size=50,
                ),
                ft.Text(
                    "Éxito",
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE,
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Mención agregada con éxito.",
                    color="#A0A0B0",
                    size=13,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            tight=True,
            width=300,
        ),
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
        content=ft.Column(
            [
                ft.Icon(ft.icons.WARNING_ROUNDED, color="#E69138", size=50),
                ft.Text(
                    "Mención Duplicada",
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE,
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Estás intentando agregar o modificar una mención que ya"
                    " existe, por favor verifícalo.",
                    color="#A0A0B0",
                    size=13,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            tight=True,
            width=300,
        ),
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
        e.page.dialog = modal_mencion
        modal_mencion.open = True
        e.page.update()

    def abrir_modal_editar(men_id: int, e):
        men = map_menciones.get(men_id)
        if not men:
            return
        id_actual.value = str(men.id)
        txt_nombre.value = men.nombre
        e.page.dialog = modal_mencion
        modal_mencion.open = True
        e.page.update()

    def filtrar_menciones(e):
        term = txt_buscar.value.lower().strip() if txt_buscar.value else ""
        renderizar_tabla(term)
        e.page.update()

    txt_buscar = ft.TextField(
        hint_text="Búsqueda por nombre",
        width=320,
        height=40,
        content_padding=ft.padding.only(left=15, right=10),
        border_radius=10,
        border_color="#303346",
        focused_border_color="#439A5D",
        prefix=ft.Icon(ft.icons.SEARCH, color="#A0A0B0", size=20),
        hint_style=ft.TextStyle(color="#5A5D70", size=13),
        text_style=ft.TextStyle(color=ft.colors.WHITE, size=13),
        on_change=filtrar_menciones,
    )

    # =========================================================================
    # 4. CARGA DE DATOS (BD) Y RENDERIZADO OPTIMIZADO (MEMORIA)
    # =========================================================================
    def cargar_datos_db():
        """Carga masiva única desde la BD al caché local."""
        nonlocal cache_menciones
        with SessionLocal() as db:
            try:
                cache_menciones = mencion_service.obtener_todos(db) or []
                renderizar_tabla(txt_buscar.value.lower().strip() if txt_buscar.value else "")
            except Exception:
                txt_total.value = "Error al cargar menciones"

    def renderizar_tabla(filtro=""):
        """Renderiza los datos tomando la información únicamente de la caché."""
        tabla_menciones.rows.clear()
        map_menciones.clear()

        for men in cache_menciones:
            map_menciones[men.id] = men
            nombre = men.nombre.lower() if men.nombre else ""

            if filtro and filtro not in nombre:
                continue

            tabla_menciones.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.icons.LABEL_OUTLINE,
                                        color="#439A5D",
                                        size=18,
                                    ),
                                    ft.Text(
                                        men.nombre,
                                        color=ft.colors.WHITE,
                                        weight=ft.FontWeight.W_500,
                                        expand=True,
                                    ),
                                ],
                                expand=True,
                            )
                        ),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.IconButton(
                                            ft.icons.EDIT,
                                            icon_color="#A0A0B0",
                                            icon_size=16,
                                            on_click=lambda e, m_id=men.id: abrir_modal_editar(
                                                m_id, e
                                            ),
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
                                            on_click=lambda e, m_id=men.id: pedir_confirmacion_eliminar(
                                                m_id, e
                                            ),
                                        ),
                                        bgcolor="#3E2A2A",
                                        border_radius=8,
                                        width=32,
                                        height=32,
                                    ),
                                ],
                                spacing=10,
                            )
                        ),
                    ]
                )
            )

        txt_total.value = f"Menciones registradas: {len(cache_menciones)}"

    # Carga inicial de datos
    cargar_datos_db()

    # =========================================================================
    # 5. RETORNO DEL FT.CONTAINER (ÁRBOL UI COMPLETO)
    # =========================================================================
    return ft.Container(
        padding=20,
        expand=True,
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Row([
                            (
                                ft.IconButton(
                                    ft.icons.ARROW_BACK,
                                    icon_color="#A0A0B0",
                                    on_click=(
                                        on_volver_menu
                                        if on_volver_menu
                                        else lambda e: None
                                    ),
                                )
                                if on_volver_menu
                                else ft.Container()
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Gestión de Menciones",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.WHITE,
                                    ),
                                    ft.Text(
                                        "Administra las menciones técnicas disponibles",
                                        size=14,
                                        color="#A0A0B0",
                                    ),
                                ],
                                spacing=2,
                            ),
                        ]),
                        ft.ElevatedButton(
                            "Añadir Mención",
                            icon=ft.icons.ADD,
                            on_click=abrir_modal_crear,
                            bgcolor="#439A5D",
                            color=ft.colors.WHITE,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                                padding=20,
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                ft.Container(
                    **estilo_tarjeta_oscura,
                    expand=True,
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Row([
                                        ft.Icon(ft.icons.LABEL, color="#439A5D"),
                                        ft.Text(
                                            "Menciones Registradas",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.colors.WHITE,
                                        ),
                                        ft.VerticalDivider(
                                            width=10, color=ft.colors.TRANSPARENT
                                        ),
                                        txt_total,
                                    ]),
                                    txt_buscar,
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Divider(height=5, color=ft.colors.TRANSPARENT),
                            ft.Column(
                                [
                                    ft.Row([
                                        ft.Container(
                                            expand=True,
                                            alignment=ft.alignment.center,
                                            content=ft.Container(
                                                width=1280,
                                                content=tabla_menciones,
                                            ),
                                        )
                                    ])
                                ],
                                expand=True,
                                scroll=ft.ScrollMode.AUTO,
                            ),
                        ],
                        spacing=15,
                        expand=True,
                    ),
                ),
            ],
            expand=True,
        ),
    )