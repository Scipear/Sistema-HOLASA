import re
import flet as ft
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal

# Importación de los servicios asociados proporcionados
from src.services.profesor_service import ProfesorService
from src.services.profesor_asignatura_service import ProfesorAsignaturaService
from src.services.sesion_profesor_service import SesionProfesorService

# Servicios adicionales inferidos para resolver los nombres reales
try:
    from src.services.curso_asignatura_service import CursoAsignaturaService
    from src.services.asignatura_service import AsignaturaService
    from src.services.sesion_service import SesionService
    from src.services.curso_service import CursoService
except ImportError:
    CursoAsignaturaService = None
    AsignaturaService = None
    SesionService = None
    CursoService = None


class vista_profesores(ft.Container):
    """Componente de vista para la gestión de profesores."""

    def __init__(self, on_volver_menu=None):
        super().__init__()
        self.expand = True
        self.padding = 20
        self.on_volver_menu = on_volver_menu

        # 1. Instanciación de Servicios
        self.prof_service = ProfesorService()
        self.prof_asig_service = ProfesorAsignaturaService()
        self.sesion_prof_service = SesionProfesorService()
        
        self.cur_asig_service = CursoAsignaturaService() if CursoAsignaturaService else None
        self.asig_service = AsignaturaService() if AsignaturaService else None
        self.sesion_service = SesionService() if SesionService else None
        self.curso_service = CursoService() if CursoService else None

        # 2. Estado Local de la Vista (Caché en memoria)
        self.map_profesores = {}
        self.map_asignaturas = {}
        self.map_sesiones = {}
        self.asignaturas_temp = []
        self.sesiones_temp = []
        self.profesor_actual_id = None

        # 3. Inicialización de la Interfaz
        self._construir_controles_ui()
        self.cargar_datos_iniciales()

    def _construir_controles_ui(self):
        """Define y estructura todos los controles visuales de la vista."""
        
        # Estilos base
        estilo_input = {
            "border_color": "#303346", 
            "focused_border_color": "#439A5D", 
            "border_radius": 10, 
            "bgcolor": "#13141C", 
            "color": ft.colors.WHITE,
            "label_style": ft.TextStyle(color="#A0A0B0"),
            "content_padding": ft.padding.only(left=15, right=45, top=15, bottom=15)
        }

        # Tabla Principal
        self.tabla_profesores = ft.DataTable(
            expand=True,
            bgcolor="#13141C",
            border_radius=15,
            border=ft.border.all(1, "#303346"),
            horizontal_lines=ft.border.BorderSide(1, "#303346"),
            vertical_lines=ft.border.BorderSide(0, ft.colors.TRANSPARENT),
            heading_row_color="#1A1C28",
            data_row_max_height=95,
            columns=[
                ft.DataColumn(ft.Text("Profesor", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Estado", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Cursos y Horarios", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acciones", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ],
            rows=[]
        )

        # Buscador y Totalizador
        self.txt_total = ft.Text("Profesores registrados: 0", color="#A0A0B0", size=14, weight=ft.FontWeight.W_500)
        self.txt_buscar = ft.TextField(
            hint_text="Búsqueda por nombre y/o apellido",
            width=320, height=40,
            content_padding=ft.padding.only(left=15, right=10),
            border_radius=10, border_color="#303346", focused_border_color="#439A5D",
            prefix=ft.Icon(ft.icons.SEARCH, color="#A0A0B0", size=20),
            hint_style=ft.TextStyle(color="#5A5D70", size=13),
            text_style=ft.TextStyle(color=ft.colors.WHITE, size=13),
            on_change=self.filtrar_profesores
        )

        # Campos de Formulario
        self.txt_nombre = ft.TextField(label="Nombre", **estilo_input)
        self.txt_apellido = ft.TextField(label="Apellido", **estilo_input)
        self.dd_estado = ft.Dropdown(
            label="Estado", value="Activo",
            options=[ft.dropdown.Option("Activo"), ft.dropdown.Option("Inactivo")],
            **estilo_input
        )
        
        # Selectores Relacionales
        self.dd_asig = ft.Dropdown(label="Selecciona asignatura y curso", **estilo_input)
        self.dd_dia = ft.Dropdown(label="Día", **estilo_input)
        self.dd_hora_inicio = ft.Dropdown(label="Hora Inicio", **estilo_input)
        self.dd_hora_fin = ft.Dropdown(label="Hora Final", **estilo_input)
        
        self.lista_chips_asig = ft.Row(wrap=True, spacing=10)
        self.lista_chips_sesion = ft.Row(wrap=True, spacing=10)

        # Modales
        self._construir_modales()

        # Estructura Principal
        self.content = ft.Column(
            expand=True,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row([
                            ft.IconButton(
                                ft.icons.ARROW_BACK, icon_color="#A0A0B0",
                                on_click=self.on_volver_menu if self.on_volver_menu else lambda e: None,
                            ) if self.on_volver_menu else ft.Container(),
                            ft.Column([
                                ft.Text("Gestión de Profesores", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.Text("Administra el plantel docente y sus asignaciones correspondientes", size=14, color="#A0A0B0"),
                            ], spacing=2),
                        ]),
                        ft.ElevatedButton(
                            "Añadir Profesor", icon=ft.icons.ADD, on_click=self.abrir_modal_crear,
                            bgcolor="#439A5D", color=ft.colors.WHITE,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=20),
                        ),
                    ]
                ),
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                ft.Container(
                    bgcolor="#1E202D", border_radius=15, padding=20, border=ft.border.all(1, "#303346"),
                    expand=True,
                    content=ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Icon(ft.icons.PEOPLE, color="#439A5D"),
                                ft.Text("Plantel Docente Registrado", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.VerticalDivider(width=10, color=ft.colors.TRANSPARENT),
                                self.txt_total,
                            ]),
                            self.txt_buscar,
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=5, color=ft.colors.TRANSPARENT),
                        ft.Container(
                            expand=True,
                            content=ft.Column([
                                ft.Row([
                                    ft.Container(expand=True, alignment=ft.alignment.center, content=ft.Container(width=1280, content=self.tabla_profesores))
                                ])
                            ], expand=True, scroll=ft.ScrollMode.AUTO)
                        ),
                    ], spacing=15, expand=True)
                )
            ]
        )

    def _construir_modales(self):
        """Define la estructura de los modales de la vista."""
        self.modal_confirmacion = ft.AlertDialog(
            bgcolor="#1E202D", 
            shape=ft.RoundedRectangleBorder(radius=15)
        )

        self.modal_formulario = ft.AlertDialog(
            title=ft.Text("Formulario de Profesor", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            bgcolor="#1E202D",
            shape=ft.RoundedRectangleBorder(radius=15),
            content=ft.Container(
                width=760,
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=self.txt_nombre, expand=True),
                        ft.Container(content=self.txt_apellido, expand=True)
                    ], spacing=15),
                    ft.Row([ft.Container(content=self.dd_estado, expand=True)]),
                    ft.Divider(color="#303346", height=10),
                    
                    ft.Text("Cursos y Asignaturas", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, size=14),
                    ft.Row([
                        ft.Container(content=self.dd_asig, expand=True), 
                        ft.Container(
                            content=ft.IconButton(ft.icons.ADD, on_click=self.agregar_asig, icon_color=ft.colors.WHITE), 
                            bgcolor="#439A5D", border_radius=10, height=52, width=52, alignment=ft.alignment.center
                        )
                    ], spacing=10),
                    self.lista_chips_asig,
                    
                    ft.Divider(color="#303346", height=10),
                    
                    ft.Text("Disponibilidad Horaria Diaria", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, size=14),
                    ft.Row([
                        ft.Container(content=self.dd_dia, expand=2),
                        ft.Container(content=self.dd_hora_inicio, expand=2),
                        ft.Container(content=self.dd_hora_fin, expand=2),
                        ft.Container(
                            content=ft.IconButton(ft.icons.ADD, on_click=self.agregar_sesion, icon_color=ft.colors.WHITE), 
                            bgcolor="#439A5D", border_radius=10, height=52, width=52, alignment=ft.alignment.center
                        )
                    ], spacing=10),
                    self.lista_chips_sesion
                ], tight=True, scroll=ft.ScrollMode.AUTO, spacing=12)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.cerrar_modal(self.modal_formulario, e), style=ft.ButtonStyle(color="#A0A0B0")),
                ft.ElevatedButton("Guardar Registro", on_click=self.ejecutar_guardado, bgcolor="#439A5D", color=ft.colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
            ],
            actions_padding=20
        )

    # =========================================================================
    # UTILIDADES DE UI
    # =========================================================================
    def mostrar_notificacion(self, e, mensaje: str, es_error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.colors.WHITE),
            bgcolor=ft.colors.RED_700 if es_error else ft.colors.GREEN_700,
            duration=3000
        )
        e.page.overlay.append(snack)
        snack.open = True
        e.page.update()

    def cerrar_modal(self, modal, e):
        modal.open = False
        e.page.update()

    def normalizar_hora(self, h_str):
        if not h_str: return ""
        try:
            partes = str(h_str).strip().split(":")
            if len(partes) >= 2:
                hora = int(partes[0])
                if 1 <= hora <= 6: hora += 12
                return f"{hora:02d}:{int(partes[1]):02d}"
        except: pass
        return str(h_str).strip()

    # =========================================================================
    # GESTIÓN DEL ESTADO LOCAL (CHIPS)
    # =========================================================================
    def refrescar_ui_asig(self):
        self.lista_chips_asig.controls.clear()
        for a_id in self.asignaturas_temp:
            nombre = self.map_asignaturas.get(a_id, f"Id:{a_id}")
            self.lista_chips_asig.controls.append(
                ft.Chip(
                    label=ft.Text(nombre, size=11, color=ft.colors.WHITE),
                    on_delete=lambda e, id_del=a_id: self.remover_asig(id_del, e),
                    bgcolor="#2A2D3E"
                )
            )

    def refrescar_ui_sesion(self):
        self.lista_chips_sesion.controls.clear()
        for s_id in self.sesiones_temp:
            nombre = self.map_sesiones.get(s_id, f"Id:{s_id}")
            self.lista_chips_sesion.controls.append(
                ft.Chip(
                    label=ft.Text(nombre, size=11, color=ft.colors.WHITE),
                    on_delete=lambda e, id_del=s_id: self.remover_sesion(id_del, e),
                    bgcolor="#2A2D3E"
                )
            )

    def remover_asig(self, id_del, e):
        if id_del in self.asignaturas_temp:
            self.asignaturas_temp.remove(id_del)
            self.refrescar_ui_asig()
            e.page.update()

    def remover_sesion(self, id_del, e):
        if id_del in self.sesiones_temp:
            self.sesiones_temp.remove(id_del)
            self.refrescar_ui_sesion()
            e.page.update()

    def agregar_asig(self, e):
        if not self.dd_asig.value: return
        val_id = int(self.dd_asig.value)
        if val_id not in self.asignaturas_temp:
            self.asignaturas_temp.append(val_id)
            self.refrescar_ui_asig()
            self.dd_asig.value = None
            e.page.update()
        else:
            self.mostrar_notificacion(e, "El curso/asignatura ya está asignado.", True)

    def agregar_sesion(self, e):
        if not all([self.dd_dia.value, self.dd_hora_inicio.value, self.dd_hora_fin.value]):
            self.mostrar_notificacion(e, "Complete día, hora de inicio y fin.", True)
            return
        
        # Búsqueda in-memory para no consultar BD cada vez
        sesion_encontrada = None
        for s_id, texto_sesion in self.map_sesiones.items():
            if (self.dd_dia.value.strip().lower() in texto_sesion.lower() and 
                self.dd_hora_inicio.value.strip() in texto_sesion and 
                self.dd_hora_fin.value.strip() in texto_sesion):
                sesion_encontrada = s_id
                break

        if sesion_encontrada:
            if sesion_encontrada not in self.sesiones_temp:
                self.sesiones_temp.append(sesion_encontrada)
                self.refrescar_ui_sesion()
                self.dd_dia.value = self.dd_hora_inicio.value = self.dd_hora_fin.value = None
                e.page.update()
            else:
                self.mostrar_notificacion(e, "Esta disponibilidad ya está agregada.", True)
        else:
            self.mostrar_notificacion(e, "No hay una sesión registrada en la base de datos con ese horario.", True)

    # =========================================================================
    # LÓGICA DE NEGOCIO (SERVICIOS Y EVENTOS)
    # =========================================================================
    def abrir_modal_crear(self, e):
        self.profesor_actual_id = None
        self.txt_nombre.value = self.txt_apellido.value = ""
        self.dd_estado.value = "Activo"
        self.asignaturas_temp.clear()
        self.sesiones_temp.clear()
        
        self.refrescar_ui_asig()
        self.refrescar_ui_sesion()
        
        e.page.dialog = self.modal_formulario
        self.modal_formulario.open = True
        e.page.update()

    def abrir_modal_editar(self, prof_id, e):
        p_data = self.map_profesores.get(prof_id)
        if not p_data: return
        
        self.profesor_actual_id = prof_id
        self.txt_nombre.value = p_data["nombre"]
        self.txt_apellido.value = p_data["apellido"]
        self.dd_estado.value = "Activo" if p_data["estado"] else "Inactivo"
        
        self.asignaturas_temp = list(p_data["asignaturas"])
        self.sesiones_temp = list(p_data["sesiones"])
        
        self.refrescar_ui_asig()
        self.refrescar_ui_sesion()
        
        e.page.dialog = self.modal_formulario
        self.modal_formulario.open = True
        e.page.update()

    def ejecutar_guardado(self, e):
        if not self.txt_nombre.value.strip() or not self.txt_apellido.value.strip():
            self.mostrar_notificacion(e, "Nombre y apellido son obligatorios.", es_error=True)
            return

        is_activo = (self.dd_estado.value == "Activo")
        
        with SessionLocal() as db:
            try:
                if not self.profesor_actual_id:
                    # Crear
                    nuevo_prof = self.prof_service.crear(db, self.txt_nombre.value.strip(), self.txt_apellido.value.strip(), is_activo)
                    for a_id in self.asignaturas_temp:
                        self.prof_asig_service.asignar(db, nuevo_prof.id, a_id)
                    for s_id in self.sesiones_temp:
                        self.sesion_prof_service.asignar(db, s_id, nuevo_prof.id)
                    self.mostrar_notificacion(e, "Profesor registrado exitosamente.")
                else:
                    # Actualizar
                    prof_id = self.profesor_actual_id
                    self.prof_service.actualizar(db, prof_id, self.txt_nombre.value.strip(), self.txt_apellido.value.strip(), is_activo)

                    # Conciliación Curso-Asignaturas
                    rels_asig = self.prof_asig_service.obtener_por_profesor(db, prof_id)
                    map_actuales_asig = {rel.curso_asignatura_id: rel.id for rel in rels_asig}

                    for a_id in self.asignaturas_temp:
                        if a_id not in map_actuales_asig:
                            self.prof_asig_service.asignar(db, prof_id, a_id)
                    for a_id, rel_id in map_actuales_asig.items():
                        if a_id not in self.asignaturas_temp:
                            self.prof_asig_service.desasignar(db, rel_id)

                    # Conciliación Sesiones
                    rels_ses = self.sesion_prof_service.obtener_por_profesor(db, prof_id)
                    map_actuales_ses = {rel.sesion_id: rel.id for rel in rels_ses}

                    for s_id in self.sesiones_temp:
                        if s_id not in map_actuales_ses:
                            self.sesion_prof_service.asignar(db, s_id, prof_id)
                    for s_id, rel_id in map_actuales_ses.items():
                        if s_id not in self.sesiones_temp:
                            self.sesion_prof_service.desasignar(db, rel_id)

                    self.mostrar_notificacion(e, "Profesor actualizado exitosamente.")

                self.cerrar_modal(self.modal_formulario, e)
                self.cargar_datos(db)
                self.txt_buscar.value = ""
                e.page.update()
                
            except Exception as ex:
                self.mostrar_notificacion(e, str(ex), es_error=True)

    def pedir_confirmacion_eliminar(self, prof_id, e):
        p_data = self.map_profesores.get(prof_id)
        nombre = f"{p_data['nombre']} {p_data['apellido']}" if p_data else f"ID {prof_id}"

        self.modal_confirmacion.title = ft.Text("¿Confirmar Eliminación?", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
        self.modal_confirmacion.content = ft.Text(f"¿Desea eliminar al profesor '{nombre}' y sus asignaciones permanentemente?", color="#A0A0B0")
        self.modal_confirmacion.actions = [
            ft.TextButton("No, Cancelar", on_click=lambda ex: self.cerrar_modal(self.modal_confirmacion, ex), style=ft.ButtonStyle(color="#A0A0B0")),
            ft.ElevatedButton("Sí, Eliminar", on_click=lambda ex: self.ejecutar_eliminacion(prof_id, ex), bgcolor="#E57373", color=ft.colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
        ]
        
        e.page.dialog = self.modal_confirmacion
        self.modal_confirmacion.open = True
        e.page.update()

    def ejecutar_eliminacion(self, prof_id, e):
        with SessionLocal() as db:
            try:
                self.prof_service.eliminar(db, prof_id)
                self.cerrar_modal(self.modal_confirmacion, e)
                self.mostrar_notificacion(e, "Profesor eliminado exitosamente.")
                self.cargar_datos(db)
                e.page.update()
            except Exception as ex:
                self.mostrar_notificacion(e, f"Error al eliminar: {str(ex)}", es_error=True)

    def filtrar_profesores(self, e):
        texto = self.txt_buscar.value.lower().strip() if self.txt_buscar.value else ""
        # Filtrado in-memory sin tocar la base de datos
        for row in self.tabla_profesores.rows:
            row.visible = (texto in str(row.data)) if row.data else True
        e.page.update()

    # =========================================================================
    # CARGA DE DATOS Y RENDERIZADO BATCH
    # =========================================================================
    def cargar_datos_iniciales(self):
        with SessionLocal() as db:
            self.cargar_datos(db)

    def cargar_datos(self, db: Session):
        """Consume servicios para construir las tablas en memoria antes del renderizado."""
        try:
            self.map_profesores.clear()
            self.map_asignaturas.clear()
            self.map_sesiones.clear()
            
            # Carga de Opciones: Cursos/Asignaturas
            if self.cur_asig_service and self.asig_service:
                all_ca = self.cur_asig_service.obtener_todos(db)
                opciones_ca = []
                for ca in all_ca:
                    asig_obj = self.asig_service.obtener_por_id(db, ca.asignatura_id)
                    nombre = asig_obj.nombre if asig_obj else "Desconocida"
                    curso = ""
                    if self.curso_service:
                        cur_obj = self.curso_service.obtener_por_id(db, ca.curso_id)
                        if cur_obj:
                            curso = f" ({getattr(cur_obj, 'year', '')} {getattr(cur_obj, 'seccion', '')})"
                            # Extracción de mención vía getattr
                            mencion_raw = getattr(cur_obj, 'mencion', None)
                            if mencion_raw and hasattr(mencion_raw, 'nombre'):
                                curso += f" [Mención: {mencion_raw.nombre}]"
                                
                    texto = f"{nombre}{curso}".strip()
                    self.map_asignaturas[ca.id] = texto
                    opciones_ca.append(ft.dropdown.Option(str(ca.id), texto))
                self.dd_asig.options = opciones_ca

                # Carga de Opciones: Sesiones
            if self.sesion_service:
                all_ses = self.sesion_service.obtener_todos(db)
                opciones_dias, horas_ini, horas_fin = set(), set(), set()
                
                for s in all_ses:
                    dia = str(getattr(s, 'dia', '')).strip()
                    h_i = self.normalizar_hora(getattr(s, 'hora_inicio', ''))
                    h_f = self.normalizar_hora(getattr(s, 'hora_fin', ''))
                    texto_ses = f"{dia}: {h_i}-{h_f}"
                    self.map_sesiones[s.id] = texto_ses
                    
                    if dia: opciones_dias.add(dia)
                    if h_i: horas_ini.add(h_i)
                    if h_f: horas_fin.add(h_f)
                
                # --- NUEVA LÓGICA DE ORDENAMIENTO DE DÍAS ---
                def orden_cronologico(d):
                    d_lower = d.lower().strip()
                    mapa_dias = {"lu": 1, "ma": 2, "mi": 3, "ju": 4, "vi": 5, "sa": 6, "do": 7}
                    for clave, valor in mapa_dias.items():
                        if d_lower.startswith(clave):
                            return valor
                    return 99 # Por si llega un dato anómalo
                # --------------------------------------------

                # Aplicamos la función 'key' al ordenar los días
                self.dd_dia.options = [ft.dropdown.Option(d) for d in sorted(list(opciones_dias), key=orden_cronologico)]
                
                self.dd_hora_inicio.options = [ft.dropdown.Option(h) for h in sorted(list(horas_ini))]
                self.dd_hora_fin.options = [ft.dropdown.Option(h) for h in sorted(list(horas_fin))]
            # Construcción Batch de Profesores
            profesores_db = self.prof_service.obtener_todos(db)
            rows_buffer = []

            for p in sorted(profesores_db, key=lambda x: f"{x.nombre} {x.apellido}".lower()):
                # Cruce estricto por servicios (Capa correcta)
                rels_asig = self.prof_asig_service.obtener_por_profesor(db, p.id)
                rels_ses = self.sesion_prof_service.obtener_por_profesor(db, p.id)
                
                asig_ids = {r.curso_asignatura_id for r in rels_asig}
                ses_ids = {r.sesion_id for r in rels_ses}

                self.map_profesores[p.id] = {
                    "id": p.id,
                    "nombre": p.nombre,
                    "apellido": p.apellido,
                    "estado": getattr(p, "estado", True),
                    "asignaturas": asig_ids,
                    "sesiones": ses_ids
                }

                # Construcción visual de la fila
                nombre_comp = f"{p.nombre} {p.apellido}"
                is_act = getattr(p, "estado", True)
                
                chip_estado = ft.Container(
                    content=ft.Text("Activo" if is_act else "Inactivo", size=11, weight=ft.FontWeight.BOLD, 
                                  color="#4CAF50" if is_act else "#E57373"),
                    bgcolor="#1E4620" if is_act else "#4A1B1B", 
                    padding=ft.padding.symmetric(horizontal=10, vertical=4), border_radius=12
                )

                str_asig = "Cursos: " + (", ".join([self.map_asignaturas.get(a, f"Id:{a}") for a in asig_ids]) if asig_ids else "Sin cursos")
                str_disp = "Horarios: " + (" | ".join([self.map_sesiones.get(s, f"Id:{s}") for s in ses_ids]) if ses_ids else "Sin horarios")

                rows_buffer.append(
                    ft.DataRow(
                        data=nombre_comp.lower(),
                        cells=[
                            ft.DataCell(ft.Row([ft.Icon(ft.icons.PERSON, color="#5B9BD5", size=18), ft.Text(nombre_comp, color=ft.colors.WHITE, weight=ft.FontWeight.W_500)], spacing=8)),
                            ft.DataCell(chip_estado),
                            ft.DataCell(ft.Container(content=ft.Column([
                                ft.Text(str_asig, size=11, color="#A0A0B0", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(str_disp, size=11, color="#F5B041", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                            ], spacing=2), padding=ft.padding.symmetric(vertical=8), expand=True)),
                            ft.DataCell(ft.Row([
                                ft.Container(content=ft.IconButton(ft.icons.EDIT, icon_color="#A0A0B0", icon_size=16, on_click=lambda ex, id_p=p.id: self.abrir_modal_editar(id_p, ex)), bgcolor="#2A2D3E", border_radius=8, width=32, height=32),
                                ft.Container(content=ft.IconButton(ft.icons.DELETE, icon_color="#E57373", icon_size=16, on_click=lambda ex, id_p=p.id: self.pedir_confirmacion_eliminar(id_p, ex)), bgcolor="#3E2A2A", border_radius=8, width=32, height=32),
                            ], spacing=8)),
                        ]
                    )
                )

            # Inserción Batch (Única actualización)
            self.tabla_profesores.rows = rows_buffer
            self.txt_total.value = f"Profesores registrados: {len(profesores_db)}"
            
        except Exception as ex:
            print(f"Error cargando datos: {ex}")