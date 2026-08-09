import flet as ft
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.services.asignatura_service import AsignaturaService

# Instancia global del servicio
asignatura_service = AsignaturaService()


def vista_materias(on_volver_menu=None):
    # =========================================================================
    # 1. ASIGNACIÓN DE VARIABLES DE ESTADO LOCAL Y CONTROLES UI
    # =========================================================================
    cache_asignaturas = []
    map_asignaturas = {}

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

    tabla_materias = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(
                ft.Text("Asignatura", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)
            ),
            ft.DataColumn(
                ft.Text("Tipo", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)
            ),
            ft.DataColumn(
                ft.Text("Acciones", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)
            ),
        ],
        rows=[],
        **estilo_tabla,
    )

    txt_total = ft.Text(
        "Asignaturas registradas: 0",
        color="#A0A0B0",
        size=14,
        weight=ft.FontWeight.W_500,
    )

    id_actual = ft.Text(visible=False)
    txt_nombre = ft.TextField(
        label="Nombre de la Asignatura",
        border_radius=10,
        border_color="#303346",
        focused_border_color="#439A5D",
        color=ft.colors.WHITE,
        label_style=ft.TextStyle(color="#A0A0B0"),
    )

    dd_tipo = ft.Dropdown(
        label="Tipo de Asignatura",
        options=[],
        border_color="#303346",
        focused_border_color="#439A5D",
        border_radius=10,
        bgcolor="#13141C",
        color=ft.colors.WHITE,
        label_style=ft.TextStyle(color="#A0A0B0"),
    )

    # =========================================================================
    # 2. FUNCIONES INTERNAS Y MANEJO DE EVENTOS
    # =========================================================================
    def actualizar_opciones_dropdown(registros):
        tipos_unicos = sorted(
            list(
                {
                    str(getattr(m, "tipo", "General") or "General").strip()
                    for m in registros
                    if getattr(m, "tipo", None)
                }
            )
        )

        if not tipos_unicos:
            tipos_unicos = ["General"]

        dd_tipo.options = [ft.dropdown.Option(t) for t in tipos_unicos]
        if dd_tipo.value not in tipos_unicos:
            dd_tipo.value = tipos_unicos[0]

    def cerrar_modal_materia(e):
        modal_materia.open = False
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

    def pre_guardar_materia(e):
        nombre = txt_nombre.value.strip() if txt_nombre.value else ""
        if not nombre:
            e.page.snack_bar = ft.SnackBar(
                ft.Text("El nombre es obligatorio"), bgcolor="#E57373"
            )
            e.page.snack_bar.open = True
            e.page.update()
            return

        # Validación optimizada de duplicados mediante caché (sin consulta DB)
        materia_actual_id = int(id_actual.value) if id_actual.value else None
        for m in cache_asignaturas:
            if m.id != materia_actual_id:
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
        es_nuevo = id_actual.value == ""

        with SessionLocal() as db:
            try:
                if es_nuevo:
                    asignatura_service.crear(db, nombre=nombre, tipo=tipo)
                else:
                    asignatura_service.actualizar(
                        db, id=int(id_actual.value), nombre=nombre, tipo=tipo
                    )

                if modal_confirmacion.open:
                    cerrar_modal_confirmacion(e)

                cerrar_modal_materia(e)
                txt_buscar.value = ""
                cargar_datos_db()  # Refresca la caché local y renderiza

                if es_nuevo:
                    e.page.dialog = modal_info
                    modal_info.open = True
                e.page.update()

            except Exception as ex:
                error_msg = (
                    "Ya existe una asignatura con este nombre."
                    if "UNIQUE" in str(ex).upper()
                    else f"Error al guardar: {ex}"
                )
                e.page.snack_bar = ft.SnackBar(ft.Text(error_msg), bgcolor="#E57373")
                e.page.snack_bar.open = True
                e.page.update()

    def pedir_confirmacion_eliminar(mat_id: int, e):
        mat = map_asignaturas.get(mat_id)
        nombre_mat = mat.nombre if mat else f"ID {mat_id}"

        modal_confirmacion.title = ft.Text(
            "¿Confirmar Eliminación?",
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE,
        )
        modal_confirmacion.content = ft.Text(
            f"¿Está seguro de que desea eliminar la asignatura '{nombre_mat}'?",
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
                on_click=lambda ex: ejecutar_eliminacion(mat_id, ex),
                bgcolor="#E57373",
                color=ft.colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            ),
        ]
        e.page.dialog = modal_confirmacion
        modal_confirmacion.open = True
        e.page.update()

    def ejecutar_eliminacion(mat_id: int, e):
        with SessionLocal() as db:
            try:
                asignatura_service.eliminar(db, id=mat_id)
                cerrar_modal_confirmacion(e)
                txt_buscar.value = ""
                cargar_datos_db()  # Sincroniza y actualiza interfaz
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
    modal_materia = ft.AlertDialog(
        title=ft.Text(
            "Formulario de Asignatura",
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
                    dd_tipo,
                ],
                spacing=15,
                tight=True,
            ),
        ),
        actions=[
            ft.TextButton(
                "Cancelar",
                on_click=cerrar_modal_materia,
                style=ft.ButtonStyle(color="#A0A0B0"),
            ),
            ft.ElevatedButton(
                "Guardar Registro",
                on_click=pre_guardar_materia,
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
                    ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color="#439A5D", size=50
                ),
                ft.Text(
                    "Éxito",
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE,
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Asignatura añadida exitosamente.",
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
                    "Asignatura Duplicada",
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE,
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Estás intentando agregar o modificar una asignatura que ya"
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
        if dd_tipo.options:
            dd_tipo.value = dd_tipo.options[0].key or dd_tipo.options[0].text
        e.page.dialog = modal_materia
        modal_materia.open = True
        e.page.update()

    def abrir_modal_editar(mat_id: int, e):
        mat = map_asignaturas.get(mat_id)
        if not mat:
            return
        id_actual.value = str(mat.id)
        txt_nombre.value = mat.nombre
        tipo_mat = getattr(mat, "tipo", "General") or "General"

        if any((opt.key == tipo_mat or opt.text == tipo_mat) for opt in dd_tipo.options):
            dd_tipo.value = tipo_mat
        elif dd_tipo.options:
            dd_tipo.value = dd_tipo.options[0].key or dd_tipo.options[0].text

        e.page.dialog = modal_materia
        modal_materia.open = True
        e.page.update()

    def filtrar_materias(e):
        term = txt_buscar.value.lower().strip() if txt_buscar.value else ""
        # Llama únicamente al renderizador (trabaja en memoria) sin golpear la base de datos
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
        on_change=filtrar_materias,
    )

    # =========================================================================
    # 4. CARGA DE DATOS (BD) Y RENDERIZADO OPTIMIZADO (MEMORIA)
    # =========================================================================
    def cargar_datos_db():
        """Carga masiva única desde la BD al caché local."""
        nonlocal cache_asignaturas
        with SessionLocal() as db:
            try:
                cache_asignaturas = asignatura_service.obtener_todos(db) or []
                actualizar_opciones_dropdown(cache_asignaturas)
                renderizar_tabla(txt_buscar.value.lower().strip() if txt_buscar.value else "")
            except Exception:
                txt_total.value = "Error al cargar asignaturas"

    def renderizar_tabla(filtro=""):
        """Renderiza los datos tomando la información únicamente de la caché local."""
        tabla_materias.rows.clear()
        map_asignaturas.clear()

        # 1. Agrupar asignaturas manteniendo el orden de tipos
        orden_tipos = []
        grupos_por_tipo = {}

        for mat in cache_asignaturas:
            map_asignaturas[mat.id] = mat
            tipo = getattr(mat, "tipo", "General") or "General"

            if tipo not in grupos_por_tipo:
                grupos_por_tipo[tipo] = []
                orden_tipos.append(tipo)

            grupos_por_tipo[tipo].append(mat)

        # 2. Aplanar los registros agrupados
        registros_agrupados = []
        for tipo in orden_tipos:
            registros_agrupados.extend(grupos_por_tipo[tipo])

        # 3. Renderizado de filas en la tabla UI con filtrado en memoria
        for mat in registros_agrupados:
            tipo = getattr(mat, "tipo", "General") or "General"
            nombre = mat.nombre.lower() if mat.nombre else ""

            if filtro and (filtro not in nombre and filtro not in tipo.lower()):
                continue

            bg, col = "#2A2D3E", "#A0A0B0"
            icono = ft.icons.BOOK

            tabla_materias.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.Icon(icono, color=col, size=18),
                                    ft.Text(
                                        mat.nombre,
                                        color=ft.colors.WHITE,
                                        weight=ft.FontWeight.W_500,
                                        expand=True,
                                    ),
                                ],
                                expand=True,
                            )
                        ),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(
                                    tipo,
                                    size=12,
                                    color=col,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                bgcolor=bg,
                                padding=ft.padding.symmetric(horizontal=12, vertical=5),
                                border_radius=10,
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
                                            on_click=lambda e, m_id=mat.id: abrir_modal_editar(m_id, e),
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
                                            on_click=lambda e, m_id=mat.id: pedir_confirmacion_eliminar(m_id, e),
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

        txt_total.value = f"Asignaturas registradas: {len(cache_asignaturas)}"

    # Carga sincrónica inicial
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
                        ft.Row(
                            [
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
                                            "Gestión de Asignaturas",
                                            size=28,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.colors.WHITE,
                                        ),
                                        ft.Text(
                                            "Administra las materias disponibles y su clasificación académica",
                                            size=14,
                                            color="#A0A0B0",
                                        ),
                                    ],
                                    spacing=2,
                                ),
                            ]
                        ),
                        ft.ElevatedButton(
                            "Añadir Asignatura",
                            icon=ft.icons.ADD,
                            on_click=abrir_modal_crear,
                            bgcolor="#439A5D",
                            color=ft.colors.WHITE,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10), padding=20
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
                                    ft.Row(
                                        [
                                            ft.Icon(ft.icons.BOOK, color="#439A5D"),
                                            ft.Text(
                                                "Materias Registradas",
                                                size=16,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.colors.WHITE,
                                            ),
                                            ft.VerticalDivider(
                                                width=10, color=ft.colors.TRANSPARENT
                                            ),
                                            txt_total,
                                        ]
                                    ),
                                    txt_buscar,
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Divider(height=5, color=ft.colors.TRANSPARENT),
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Container(
                                                expand=True,
                                                alignment=ft.alignment.center,
                                                content=ft.Container(
                                                    width=1280,
                                                    content=tabla_materias,
                                                ),
                                            )
                                        ]
                                    )
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