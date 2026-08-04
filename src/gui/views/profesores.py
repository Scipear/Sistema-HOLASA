"""Archivo de vista para la gestión de profesores."""
import flet as ft
from src.database.connection import SessionLocal
from src.services.profesor_service import ProfesorService

opciones_estado = ["Activo", "Inactivo"]
opciones_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
opciones_horas = ["07:00", "07:40", "08:30", "09:10", "09:50", "10:30", "11:10", "11:50", "12:10", "12:50", "13:30", "14:10"]
opciones_materias = ["Matemática - 1er Año", "Física - 2do Año", "Química - 3er Año", "Castellano - 4to Año", "Telecomunicaciones - 4to Año", "Dibujo Técnico - 5to Año"]


def vista_profesores(on_volver_menu=None):
    profesor_service = ProfesorService()

    estilo_tarjeta_oscura = {
        "bgcolor": "#1E202D",
        "border_radius": 15,
        "padding": 20,
        "border": ft.border.all(1, "#303346")
    }

    estilo_tabla = {
        "bgcolor": "#13141C",
        "border_radius": 15,
        "border": ft.border.all(1, "#303346"),
        "horizontal_lines": ft.border.BorderSide(1, "#303346"),
        "vertical_lines": ft.border.BorderSide(0, ft.colors.TRANSPARENT),
        "heading_row_color": "#1A1C28",
        "data_row_max_height": 70,
    }

    tabla_profesores = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(ft.Text("Profesor", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Contacto", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Estado", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Acciones", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
        **estilo_tabla
    )

    txt_total = ft.Text("Profesores registrados: 0", color="#A0A0B0", size=14, weight=ft.FontWeight.W_500)
    
    id_actual = ft.Text(visible=False)
    txt_nombre = ft.TextField(label="Nombre", border_radius=10, border_color="#303346", focused_border_color="#439A5D", color=ft.colors.WHITE)
    txt_apellido = ft.TextField(label="Apellido", border_radius=10, border_color="#303346", focused_border_color="#439A5D", color=ft.colors.WHITE)
    txt_telefono = ft.TextField(label="Teléfono (Opcional)", border_radius=10, border_color="#303346", focused_border_color="#439A5D", color=ft.colors.WHITE)
    txt_correo = ft.TextField(label="Correo Electrónico (Opcional)", border_radius=10, border_color="#303346", focused_border_color="#439A5D", color=ft.colors.WHITE)
    dd_estado = ft.Dropdown(label="Estado", options=[ft.dropdown.Option(x) for x in opciones_estado], value="Activo", border_radius=10, border_color="#303346", focused_border_color="#439A5D", color=ft.colors.WHITE)

    def cerrar_modal(e):
        modal_profesor.open = False
        e.page.update()

    def cerrar_modal_info(e):
        modal_info.open = False
        e.page.update()

    def cerrar_modal_confirmacion(e):
        modal_confirmacion.open = False
        e.page.update()

    def pre_guardar_profesor(e):
        nombre = txt_nombre.value.strip() if txt_nombre.value else ""
        apellido = txt_apellido.value.strip() if txt_apellido.value else ""

        if not nombre or not apellido:
            e.page.snack_bar = ft.SnackBar(ft.Text("El nombre y apellido son campos requeridos"), bgcolor="#E57373")
            e.page.snack_bar.open = True
            e.page.update()
            return

        if not id_actual.value:
            modal_confirmacion.title = ft.Text("¿Confirmar Registro?", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
            modal_confirmacion.content = ft.Text("¿Está seguro de que desea registrar este profesor?", color="#A0A0B0")
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
        nombre = txt_nombre.value.strip() if txt_nombre.value else ""
        apellido = txt_apellido.value.strip() if txt_apellido.value else ""
        telefono = txt_telefono.value.strip() if txt_telefono.value else None
        correo = txt_correo.value.strip() if txt_correo.value else None
        estado_bool = (dd_estado.value == "Activo")

        db = SessionLocal()
        try:
            if not id_actual.value:
                profesor_service.crear(
                    db=db,
                    nombre=nombre,
                    apellido=apellido,
                    telefono=telefono if telefono else None,
                    correo=correo if correo else None,
                    estado=estado_bool
                )
            else:
                prof_id = int(id_actual.value)
                profesor_service.actualizar(
                    db=db,
                    id=prof_id,
                    nombre=nombre,
                    apellido=apellido,
                    telefono=telefono if telefono else None,
                    correo=correo if correo else None,
                    estado=estado_bool
                )
            
            if modal_confirmacion.open:
                cerrar_modal_confirmacion(e)

            cerrar_modal(e)
            cargar_datos()
            txt_buscar.value = ""

            if not id_actual.value:
                e.page.dialog = modal_info
                e.page.dialog.open = True
            e.page.update()

        except ValueError as err:
            e.page.snack_bar = ft.SnackBar(ft.Text(str(err)), bgcolor="#E57373")
            e.page.snack_bar.open = True
            e.page.update()
        except Exception as ex:
            e.page.snack_bar = ft.SnackBar(ft.Text(f"Error inesperado: {ex}"), bgcolor="#E57373")
            e.page.snack_bar.open = True
            e.page.update()
        finally:
            db.close()

    modal_info = ft.AlertDialog(
        content=ft.Column([
            ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color="#439A5D", size=50),
            ft.Text("Éxito", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE, size=16, text_align=ft.TextAlign.CENTER),
            ft.Text("Profesor añadido exitosamente a la base de datos.", color="#A0A0B0", size=13, text_align=ft.TextAlign.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, tight=True, width=300),
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        actions=[
            ft.ElevatedButton("OK", on_click=cerrar_modal_info, bgcolor="#439A5D", color=ft.colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        actions_padding=20
    )

    modal_profesor = ft.AlertDialog(
        title=ft.Text("Formulario de Profesor", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        content=ft.Container(
            width=500,
            content=ft.Column([
                id_actual,
                ft.Row([txt_nombre, txt_apellido], spacing=10),
                ft.Row([txt_telefono, txt_correo], spacing=10),
                dd_estado,
            ], spacing=15, scroll=ft.ScrollMode.AUTO, tight=True, height=260)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=cerrar_modal, style=ft.ButtonStyle(color="#A0A0B0")),
            ft.ElevatedButton("Guardar Registro", on_click=pre_guardar_profesor, bgcolor="#439A5D", color=ft.colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
        ],
        actions_padding=20
    )

    modal_confirmacion = ft.AlertDialog(
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        actions_padding=20,
        actions_alignment=ft.MainAxisAlignment.END
    )

    # Componentes para Visualización (Ver Info)
    info_nombre = ft.Text(size=22, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
    info_contacto = ft.Text(color="#A0A0B0", size=13)
    info_estado_badge = ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=5), border_radius=15)

    def cerrar_modal_ver(e):
        modal_ver.open = False
        e.page.update()

    modal_ver = ft.AlertDialog(
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        content=ft.Container(
            width=450,
            padding=10,
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=50, color="#439A5D"),
                    ft.Column([
                        info_nombre,
                        ft.Row([info_estado_badge, info_contacto], alignment=ft.MainAxisAlignment.START, spacing=10)
                    ], spacing=2)
                ]),
            ], tight=True, scroll=ft.ScrollMode.AUTO)
        ),
        actions=[
            ft.ElevatedButton("Cerrar", on_click=cerrar_modal_ver, bgcolor="#439A5D", color=ft.colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        actions_padding=20
    )

    def abrir_modal_ver(prof, e):
        info_nombre.value = f"{prof.nombre} {prof.apellido}"
        tel = prof.telefono if prof.telefono else "Sin teléfono"
        corr = prof.correo if prof.correo else "Sin correo"
        info_contacto.value = f"{tel} | {corr}"
        
        estado_texto = "Activo" if prof.estado else "Inactivo"
        info_estado_badge.content = ft.Text(estado_texto, size=11, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)
        info_estado_badge.bgcolor = "#2D6B3F" if prof.estado else "#E57373"

        e.page.dialog = modal_ver
        modal_ver.open = True
        e.page.update()

    def pedir_confirmacion_eliminar(prof, e):
        modal_confirmacion.title = ft.Text("¿Confirmar Eliminación?", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
        modal_confirmacion.content = ft.Text(f"¿Está seguro de que desea eliminar al docente '{prof.nombre} {prof.apellido}' del plantel?", color="#A0A0B0")
        modal_confirmacion.actions = [
            ft.TextButton("No, Cancelar", on_click=cerrar_modal_confirmacion, style=ft.ButtonStyle(color="#A0A0B0")),
            ft.ElevatedButton("Sí, Confirmar", on_click=lambda ex: ejecutar_eliminacion(prof.id, ex), bgcolor="#E57373", color=ft.colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
        ]
        e.page.dialog = modal_confirmacion
        modal_confirmacion.open = True
        e.page.update()

    def ejecutar_eliminacion(prof_id, e):
        db = SessionLocal()
        try:
            profesor_service.eliminar(db, prof_id)
            cerrar_modal_confirmacion(e)
            cargar_datos()
            txt_buscar.value = ""
            e.page.update()
        except Exception as ex:
            e.page.snack_bar = ft.SnackBar(ft.Text(f"Error al eliminar: {ex}"), bgcolor="#E57373")
            e.page.snack_bar.open = True
            e.page.update()
        finally:
            db.close()

    def abrir_modal_crear(e):
        id_actual.value = ""
        txt_nombre.value = ""
        txt_apellido.value = ""
        txt_telefono.value = ""
        txt_correo.value = ""
        dd_estado.value = "Activo"
        
        e.page.dialog = modal_profesor
        modal_profesor.open = True
        e.page.update()

    def abrir_modal_editar(prof, e):
        id_actual.value = str(prof.id)
        txt_nombre.value = prof.nombre
        txt_apellido.value = prof.apellido
        txt_telefono.value = prof.telefono if prof.telefono else ""
        txt_correo.value = prof.correo if prof.correo else ""
        dd_estado.value = "Activo" if prof.estado else "Inactivo"
        
        e.page.dialog = modal_profesor
        modal_profesor.open = True
        e.page.update()

    def filtrar_profesores(e):
        term = txt_buscar.value.lower() if txt_buscar.value else ""
        cargar_datos(term)
        e.page.update()

    txt_buscar = ft.TextField(
        hint_text="Buscar profesor por nombre, apellido o contacto",
        width=320,
        height=40,
        content_padding=ft.padding.only(left=15, right=10),
        border_radius=10,
        border_color="#303346",
        focused_border_color="#439A5D",
        prefix=ft.Icon(ft.icons.SEARCH, color="#A0A0B0", size=20),
        hint_style=ft.TextStyle(color="#5A5D70", size=13),
        text_style=ft.TextStyle(color=ft.colors.WHITE, size=13),
        on_change=filtrar_profesores
    )

    def cargar_datos(filtro=""):
        tabla_profesores.rows.clear()
        db = SessionLocal()
        try:
            registros = profesor_service.obtener_todos(db)
            total_count = 0
            for p in registros:
                nom = p.nombre.lower() if p.nombre else ""
                ape = p.apellido.lower() if p.apellido else ""
                tel = p.telefono.lower() if p.telefono else ""
                cor = p.correo.lower() if p.correo else ""
                
                if filtro and (filtro not in nom and filtro not in ape and filtro not in tel and filtro not in cor):
                    continue

                total_count += 1
                estado_activo = p.estado
                bg_est, col_est = ("#1A2A20", "#439A5D") if estado_activo else ("#3E2A2A", "#E57373")
                estado_str = "Activo" if estado_activo else "Inactivo"

                tabla_profesores.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Row([
                        ft.Icon(ft.icons.PERSON, color="#5B9BD5" if estado_activo else "#A0A0B0", size=18),
                        ft.Text(f"{p.nombre} {p.apellido}", color=ft.colors.WHITE, weight=ft.FontWeight.W_500)
                    ])),
                    ft.DataCell(ft.Column([
                        ft.Text(p.correo if p.correo else "Sin correo", color="#A0A0B0", size=12, weight=ft.FontWeight.W_400),
                        ft.Text(p.telefono if p.telefono else "Sin telf", color="#6C7A89", size=11)
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=1)),
                    ft.DataCell(ft.Container(
                        content=ft.Text(estado_str, size=11, color=col_est, weight=ft.FontWeight.BOLD),
                        bgcolor=bg_est, padding=ft.padding.symmetric(horizontal=10, vertical=4), border_radius=10
                    )),
                    ft.DataCell(ft.Row([
                        ft.Container(content=ft.IconButton(ft.icons.VISIBILITY, icon_color="#439A5D", icon_size=16, on_click=lambda e, pr=p: abrir_modal_ver(pr, e)), bgcolor="#1A2A20", border_radius=8, width=32, height=32),
                        ft.Container(content=ft.IconButton(ft.icons.EDIT, icon_color="#A0A0B0", icon_size=16, on_click=lambda e, pr=p: abrir_modal_editar(pr, e)), bgcolor="#2A2D3E", border_radius=8, width=32, height=32),
                        ft.Container(content=ft.IconButton(ft.icons.DELETE, icon_color="#E57373", icon_size=16, on_click=lambda e, pr=p: pedir_confirmacion_eliminar(pr, e)), bgcolor="#3E2A2A", border_radius=8, width=32, height=32),
                    ], spacing=10))
                ]))
            txt_total.value = f"Profesores registrados: {total_count}"
        except Exception as e:
            print(f"Error cargando profesores desde la BD: {e}")
        finally:
            db.close()

    cargar_datos()

    return ft.Container(
        padding=20, expand=True,
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Row([
                            ft.IconButton(ft.icons.ARROW_BACK, icon_color="#A0A0B0", on_click=on_volver_menu if on_volver_menu else lambda e: None) if on_volver_menu else ft.Container(),
                            ft.Column([
                                ft.Text("Gestión de Profesores", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.Text("Administra el plantel docente y sus asignaciones correspondientes", size=14, color="#A0A0B0")
                            ], spacing=2)
                        ]),
                        ft.ElevatedButton(
                            "Añadir Profesor",
                            icon=ft.icons.ADD,
                            on_click=abrir_modal_crear,
                            bgcolor="#439A5D",
                            color=ft.colors.WHITE,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=20)
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                ft.Container(
                    **estilo_tarjeta_oscura,
                    expand=True,
                    content=ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Icon(ft.icons.PEOPLE, color="#439A5D"),
                                ft.Text("Plantel Docente Registrado", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.VerticalDivider(width=10, color=ft.colors.TRANSPARENT),
                                txt_total
                            ]),
                            txt_buscar
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
                                            content=tabla_profesores
                                        )
                                    )
                                ])
                            ],
                            expand=True,
                            scroll=ft.ScrollMode.AUTO
                        )
                    ], spacing=15, expand=True)
                )
            ],
            expand=True
        )
    )