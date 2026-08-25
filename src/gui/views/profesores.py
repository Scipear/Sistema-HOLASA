import re
import flet as ft
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.connection import SessionLocal

from src.services.profesor_service import ProfesorService
from src.services.profesor_asignatura_service import ProfesorAsignaturaService
from src.services.sesion_profesor_service import SesionProfesorService
from src.services.salon_profesor_service import SalonProfesorService

try:
    from src.services.curso_asignatura_service import CursoAsignaturaService
    from src.services.asignatura_service import AsignaturaService
    from src.services.sesion_service import SesionService
    from src.services.curso_service import CursoService
    from src.services.salon_service import SalonService
except ImportError:
    CursoAsignaturaService = None
    AsignaturaService = None
    SesionService = None
    CursoService = None
    SalonService = None


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
        self.salon_prof_service = SalonProfesorService()
        
        self.cur_asig_service = CursoAsignaturaService() if CursoAsignaturaService else None
        self.asig_service = AsignaturaService() if AsignaturaService else None
        self.sesion_service = SesionService() if SesionService else None
        self.curso_service = CursoService() if CursoService else None
        self.salon_service = SalonService() if SalonService else None

        # 2. Estado Local de la Vista (Caché en memoria)
        self.map_profesores = {}
        self.map_asignaturas = {}
        self.map_asignaturas_detalladas = {}
        self.sesiones_completas = {}
        self.dias_sesiones = {}
        self.map_salones = {}
        self.asignaturas_temp = []
        self.sesiones_temp = []
        self.salones_temp = []
        self.profesor_actual_id = None

        # 3. Inicialización de la Interfaz
        self._construir_controles_ui()
        self.cargar_datos_iniciales()

    def _construir_controles_ui(self):
        """Define y estructura todos los controles visuales de la vista."""
        
        estilo_input = {
            "border_color": "#303346", 
            "focused_border_color": "#439A5D", 
            "border_radius": 10, 
            "bgcolor": "#13141C", 
            "color": ft.colors.WHITE,
            "label_style": ft.TextStyle(color="#A0A0B0"),
            "content_padding": ft.padding.only(left=15, right=45, top=15, bottom=15)
        }

        self.tabla_profesores = ft.DataTable(
            expand=True,
            bgcolor="#13141C",
            border_radius=15,
            border=ft.border.all(1, "#303346"),
            horizontal_lines=ft.border.BorderSide(1, "#303346"),
            vertical_lines=ft.border.BorderSide(0, ft.colors.TRANSPARENT),
            heading_row_color="#1A1C28",
            data_row_min_height=70,
            data_row_max_height=80,
            columns=[
                ft.DataColumn(ft.Text("Profesor", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Estado", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Cursos, Aula y Horarios", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acciones", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ],
            rows=[]
        )

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

        self.txt_nombre = ft.TextField(label="Nombre", **estilo_input)
        self.txt_apellido = ft.TextField(label="Apellido", **estilo_input)
        self.dd_estado = ft.Dropdown(
            label="Estado", value="Activo",
            options=[ft.dropdown.Option("Activo"), ft.dropdown.Option("Inactivo")],
            **estilo_input
        )
        
        self.dd_salon = ft.Dropdown(label="Selecciona aula", **estilo_input)
        self.lista_chips_salon = ft.Row(wrap=True, spacing=10)
        
        self.dd_asig = ft.Dropdown(label="Selecciona asignatura y curso", **estilo_input)
        self.dd_dia = ft.Dropdown(label="Día", on_change=self.al_cambiar_dia, **estilo_input)
        self.dd_sesion_inicio = ft.Dropdown(label="Sesión Inicial", on_change=self.al_cambiar_sesion_inicio, **estilo_input)
        self.dd_sesion_fin = ft.Dropdown(label="Sesión Final", **estilo_input)
        
        self.lista_chips_asig = ft.Row(wrap=True, spacing=10)
        self.lista_chips_sesion = ft.Row(wrap=True, spacing=10)

        self.contenido_panel_detalle = ft.Column([], spacing=12)
        self._construir_modales()

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

        self.modal_detalle = ft.AlertDialog(
            title=ft.Text("Detalle de Asignaciones", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            bgcolor="#1E202D",
            shape=ft.RoundedRectangleBorder(radius=15),
            content=ft.Container(
                width=520,
                height=420,
                padding=5,
                content=ft.Column(
                    [self.contenido_panel_detalle],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True
                )
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self.cerrar_modal(self.modal_detalle, e), style=ft.ButtonStyle(color="#A0A0B0"))
            ],
            actions_padding=15
        )

        self.modal_formulario = ft.AlertDialog(
            title=ft.Text("Formulario de Profesor", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            bgcolor="#1E202D",
            shape=ft.RoundedRectangleBorder(radius=15),
            content=ft.Container(
                width=800,
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=self.txt_nombre, expand=True),
                        ft.Container(content=self.txt_apellido, expand=True)
                    ], spacing=15),
                    ft.Row([
                        ft.Container(content=self.dd_estado, expand=True)
                    ], spacing=15),
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
                    
                    ft.Text("Aula(s)", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, size=14),
                    ft.Row([
                        ft.Container(content=self.dd_salon, expand=True), 
                        ft.Container(
                            content=ft.IconButton(ft.icons.ADD, on_click=self.agregar_salon, icon_color=ft.colors.WHITE), 
                            bgcolor="#439A5D", border_radius=10, height=52, width=52, alignment=ft.alignment.center
                        )
                    ], spacing=10),
                    self.lista_chips_salon,
                    
                    ft.Divider(color="#303346", height=10),
                    
                    ft.Text("Disponibilidad Horaria (Bloques de Sesiones)", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, size=14),
                    ft.Row([
                        ft.Container(content=self.dd_dia, expand=2),
                        ft.Container(content=self.dd_sesion_inicio, expand=3),
                        ft.Container(content=self.dd_sesion_fin, expand=3),
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

    def abrir_modal_detalle(self, prof_id, e):
        """Abre el panel flotante con la información detallada del profesor seleccionado."""
        p_data = self.map_profesores.get(prof_id)
        if not p_data: 
            return

        self.contenido_panel_detalle.controls.clear()

        self.contenido_panel_detalle.controls.append(
            ft.Row([
                ft.Icon(ft.icons.PERSON, color="#5B9BD5", size=20),
                ft.Text(f"{p_data['nombre']} {p_data['apellido']}", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
            ], spacing=8)
        )

        self.contenido_panel_detalle.controls.append(ft.Divider(color="#303346", height=5))

        self.contenido_panel_detalle.controls.append(
            ft.Text("Curso y Asignatura", size=14, weight=ft.FontWeight.BOLD, color="#439A5D")
        )

        asig_ids = p_data["asignaturas"]
        if asig_ids:
            for a_id in asig_ids:
                detalles = self.map_asignaturas_detalladas.get(a_id, {})
                texto_formateado = detalles.get("texto_formateado") or self.map_asignaturas.get(a_id, f"Id:{a_id}")
                
                self.contenido_panel_detalle.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.BOOK, size=14, color="#439A5D"),
                            ft.Text(texto_formateado, size=13, color=ft.colors.WHITE, weight=ft.FontWeight.W_500)
                        ], spacing=8),
                        bgcolor="#252836",
                        padding=10,
                        border_radius=8,
                        border=ft.border.all(1, "#3A3E54")
                    )
                )
        else:
            self.contenido_panel_detalle.controls.append(
                ft.Text("Sin cursos o asignaturas afiliadas.", size=12, color="#5A5D70")
            )

        self.contenido_panel_detalle.controls.append(ft.Divider(color="#303346", height=5))

        self.contenido_panel_detalle.controls.append(
            ft.Text("Aula(s)", size=14, weight=ft.FontWeight.BOLD, color="#4B93F8")
        )

        salon_ids = p_data.get("salones", [])
        if salon_ids:
            for s_id in salon_ids:
                nombre_salon = self.map_salones.get(s_id, f"Id:{s_id}")
                self.contenido_panel_detalle.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.MEETING_ROOM, size=14, color="#4B93F8"),
                            ft.Text(nombre_salon, size=13, color=ft.colors.WHITE, weight=ft.FontWeight.W_500)
                        ], spacing=8),
                        bgcolor="#252836",
                        padding=10,
                        border_radius=8,
                        border=ft.border.all(1, "#3A3E54")
                    )
                )
        else:
            self.contenido_panel_detalle.controls.append(
                ft.Text("Sin aulas asignadas.", size=12, color="#5A5D70")
            )

        self.contenido_panel_detalle.controls.append(ft.Divider(color="#303346", height=5))

        self.contenido_panel_detalle.controls.append(
            ft.Text("Horarios Disponibles", size=14, weight=ft.FontWeight.BOLD, color="#F5B041")
        )

        bloques_disp = self.agrupar_sesiones_bloques(list(p_data["sesiones"]))
        if bloques_disp:
            for b in bloques_disp:
                self.contenido_panel_detalle.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.SCHEDULE, size=14, color="#F5B041"),
                            ft.Text(b['texto'], size=13, color="#FFFFFFFF", weight=ft.FontWeight.W_500)
                        ], spacing=8),
                        bgcolor="#252836",
                        padding=10,
                        border_radius=8,
                        border=ft.border.all(1, "#3A3E54")
                    )
                )
        else:
            self.contenido_panel_detalle.controls.append(
                ft.Text("Sin horarios disponibles registrados.", size=12, color="#5A5D70")
            )

        e.page.dialog = self.modal_detalle
        self.modal_detalle.open = True
        e.page.update()

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

    def normalizar_y_minutos(self, h_str):
        if not h_str: return "", 0
        try:
            partes = str(h_str).strip().split(":")
            if len(partes) >= 2:
                hora = int(partes[0])
                minutos = int(partes[1])
                if 1 <= hora <= 6: hora += 12
                h_norm = f"{hora:02d}:{minutos:02d}"
                t_min = (hora * 60) + minutos
                return h_norm, t_min
        except: pass
        return str(h_str).strip(), 0
    
    def agrupar_sesiones_bloques(self, ses_ids):
        dias_agrupados = {}
        for s_id in ses_ids:
            s_data = self.sesiones_completas.get(s_id)
            if s_data:
                dia = s_data['dia']
                if dia not in dias_agrupados:
                    dias_agrupados[dia] = []
                dias_agrupados[dia].append(s_data)

        bloques = []
        def orden_cronologico(d):
            d_lower = d.lower().strip()
            mapa = {"lu": 1, "ma": 2, "mi": 3, "ju": 4, "vi": 5, "sa": 6, "do": 7}
            for clave, valor in mapa.items():
                if d_lower.startswith(clave): return valor
            return 99

        for dia in sorted(dias_agrupados.keys(), key=orden_cronologico):
            sesiones_dia = sorted(dias_agrupados[dia], key=lambda x: x['min_i'])
            
            if sesiones_dia:
                primera = sesiones_dia[0]
                ultima = sesiones_dia[-1]
                ids_bloque = [s['id'] for s in sesiones_dia]
                
                if primera['id'] == ultima['id']:
                    texto = f"{dia} {primera['h_i']} - {primera['h_f']}"
                else:
                    texto = f"{dia} {primera['h_i']} - {primera['h_f']} a {ultima['h_i']} - {ultima['h_f']}"
                
                bloques.append({"texto": texto, "ids": ids_bloque})
                
        return bloques

    def al_cambiar_dia(self, e):
        dia_sel = self.dd_dia.value
        if not dia_sel: return
        sesiones_del_dia = self.dias_sesiones.get(dia_sel, [])
        self.dd_sesion_inicio.options = [
            ft.dropdown.Option(key=str(s['id']), text=f"{s['h_i']} - {s['h_f']}") 
            for s in sesiones_del_dia
        ]
        self.dd_sesion_fin.options = []
        self.dd_sesion_inicio.value = None
        self.dd_sesion_fin.value = None
        e.page.update()

    def al_cambiar_sesion_inicio(self, e):
        dia_sel = self.dd_dia.value
        id_ini = self.dd_sesion_inicio.value
        if not dia_sel or not id_ini: return
        
        sesiones_del_dia = self.dias_sesiones.get(dia_sel, [])
        min_inicio = 0
        for s in sesiones_del_dia:
            if str(s['id']) == id_ini:
                min_inicio = s['min_i']
                break
        
        self.dd_sesion_fin.options = [
            ft.dropdown.Option(key=str(s['id']), text=f"{s['h_i']} - {s['h_f']}") 
            for s in sesiones_del_dia if s['min_i'] >= min_inicio
        ]
        self.dd_sesion_fin.value = None
        e.page.update()

    def refrescar_ui_salon(self):
        self.lista_chips_salon.controls.clear()
        for s_id in self.salones_temp:
            nombre = self.map_salones.get(s_id, f"Id:{s_id}")
            self.lista_chips_salon.controls.append(
                ft.Chip(
                    label=ft.Text(nombre, size=11, color=ft.colors.WHITE),
                    on_delete=lambda e, id_del=s_id: self.remover_salon(id_del, e),
                    bgcolor="#2A2D3E"
                )
            )

    def refrescar_ui_asig(self):
        self.lista_chips_asig.controls.clear()
        for a_id in self.asignaturas_temp:
            detalles = self.map_asignaturas_detalladas.get(a_id)
            nombre = detalles["texto_formateado"] if detalles else self.map_asignaturas.get(a_id, f"Id:{a_id}")
            self.lista_chips_asig.controls.append(
                ft.Chip(
                    label=ft.Text(nombre, size=11, color=ft.colors.WHITE),
                    on_delete=lambda e, id_del=a_id: self.remover_asig(id_del, e),
                    bgcolor="#2A2D3E"
                )
            )

    def refrescar_ui_sesion(self):
        self.lista_chips_sesion.controls.clear()
        bloques = self.agrupar_sesiones_bloques(self.sesiones_temp)
        for bloque in bloques:
            self.lista_chips_sesion.controls.append(
                ft.Chip(
                    label=ft.Text(bloque['texto'], size=11, color=ft.colors.WHITE),
                    on_delete=lambda e, ids_del=bloque['ids']: self.remover_bloque_sesion(ids_del, e),
                    bgcolor="#2A2D3E"
                )
            )

    def remover_salon(self, id_del, e):
        if id_del in self.salones_temp:
            self.salones_temp.remove(id_del)
            self.refrescar_ui_salon()
            e.page.update()

    def remover_asig(self, id_del, e):
        if id_del in self.asignaturas_temp:
            self.asignaturas_temp.remove(id_del)
            self.refrescar_ui_asig()
            e.page.update()

    def remover_bloque_sesion(self, ids_del, e):
        for id_del in ids_del:
            if id_del in self.sesiones_temp:
                self.sesiones_temp.remove(id_del)
        self.refrescar_ui_sesion()
        e.page.update()

    def agregar_salon(self, e):
        if not self.dd_salon.value: return
        val_id = int(self.dd_salon.value)
        if val_id not in self.salones_temp:
            self.salones_temp.append(val_id)
            self.refrescar_ui_salon()
            self.dd_salon.value = None
            e.page.update()
        else:
            self.mostrar_notificacion(e, "El aula ya está asignada.", True)

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
        dia_sel = self.dd_dia.value
        id_ini = self.dd_sesion_inicio.value
        id_fin = self.dd_sesion_fin.value

        if not all([dia_sel, id_ini, id_fin]):
            self.mostrar_notificacion(e, "Complete día, sesión inicial y sesión final.", True)
            return

        sesiones_del_dia = self.dias_sesiones.get(dia_sel, [])
        min_i_ini = next((s['min_i'] for s in sesiones_del_dia if str(s['id']) == id_ini), 0)
        min_i_fin = next((s['min_i'] for s in sesiones_del_dia if str(s['id']) == id_fin), float('inf'))

        agregadas = False
        for s in sesiones_del_dia:
            if min_i_ini <= s['min_i'] <= min_i_fin:
                if s['id'] not in self.sesiones_temp:
                    self.sesiones_temp.append(s['id'])
                    agregadas = True
        
        if agregadas:
            self.refrescar_ui_sesion()
            self.dd_dia.value = None
            self.dd_sesion_inicio.value = None
            self.dd_sesion_fin.value = None
            self.dd_sesion_inicio.options = []
            self.dd_sesion_fin.options = []
            e.page.update()
        else:
            self.mostrar_notificacion(e, "Las sesiones en este rango temporal ya están agregadas.", True)

    def abrir_modal_crear(self, e):
        self.profesor_actual_id = None
        self.txt_nombre.value = self.txt_apellido.value = ""
        self.dd_estado.value = "Activo"
        self.dd_salon.value = None 
        
        self.asignaturas_temp.clear()
        self.sesiones_temp.clear()
        self.salones_temp.clear() 
        
        self.refrescar_ui_asig()
        self.refrescar_ui_sesion()
        self.refrescar_ui_salon() 
        
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
        self.dd_salon.value = None 
        
        self.asignaturas_temp = list(p_data["asignaturas"])
        self.sesiones_temp = list(p_data["sesiones"])
        self.salones_temp = list(p_data.get("salones", [])) 
        
        self.refrescar_ui_asig()
        self.refrescar_ui_sesion()
        self.refrescar_ui_salon() 
        
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
                    nuevo_prof = self.prof_service.crear(db, self.txt_nombre.value.strip(), self.txt_apellido.value.strip(), is_activo)
                    prof_id = nuevo_prof.id
                else:
                    prof_id = self.profesor_actual_id
                    self.prof_service.actualizar(db, prof_id, self.txt_nombre.value.strip(), self.txt_apellido.value.strip(), is_activo)

                # --- Asignaturas ---
                rels_asig_existentes = self.prof_asig_service.obtener_por_profesor(db, prof_id)
                ids_ya_asignados = {rel.curso_asignatura_id for rel in rels_asig_existentes}
                map_rel_id_asig = {rel.curso_asignatura_id: rel.id for rel in rels_asig_existentes}

                for a_id in self.asignaturas_temp:
                    if a_id not in ids_ya_asignados:
                        try:
                            self.prof_asig_service.asignar(db, prof_id, a_id)
                        except ValueError as ex:
                            self.mostrar_notificacion(e, f"Aviso de Asignatura: {str(ex)}", es_error=True)

                for a_id, rel_id in map_rel_id_asig.items():
                    if a_id not in self.asignaturas_temp:
                        self.prof_asig_service.desasignar(db, rel_id)

                # --- Sesiones ---
                rels_ses_existentes = self.sesion_prof_service.obtener_por_profesor(db, prof_id)
                ids_ses_asignadas = {rel.sesion_id for rel in rels_ses_existentes}
                map_rel_id_ses = {rel.sesion_id: rel.id for rel in rels_ses_existentes}

                for s_id in self.sesiones_temp:
                    if s_id not in ids_ses_asignadas:
                        try:
                            self.sesion_prof_service.asignar(db, s_id, prof_id)
                        except ValueError as ex:
                            self.mostrar_notificacion(e, f"Aviso de Sesión: {str(ex)}", es_error=True)

                for s_id, rel_id in map_rel_id_ses.items():
                    if s_id not in self.sesiones_temp:
                        self.sesion_prof_service.desasignar(db, rel_id)

                # --- Salones (Aulas) ---
                rels_salon_exist = self.salon_prof_service.obtener_por_profesor(db, prof_id)
                ids_salon_asignados = {rel.salon_id for rel in rels_salon_exist}
                map_rel_id_salon = {rel.salon_id: rel.id for rel in rels_salon_exist}

                for s_id in self.salones_temp:
                    if s_id not in ids_salon_asignados:
                        asignado_exitosamente = False
                        try:
                            self.salon_prof_service.asignar(db, s_id, prof_id)
                            asignado_exitosamente = True
                        except Exception:
                            # Intento alternativo robusto si el método de servicio directo falla
                            try:
                                if hasattr(self.salon_prof_service, 'create'):
                                    self.salon_prof_service.create(db, {"salon_id": s_id, "profesor_id": prof_id})
                                    asignado_exitosamente = True
                                elif hasattr(self.salon_prof_service, 'crear'):
                                    self.salon_prof_service.crear(db, {"salon_id": s_id, "profesor_id": prof_id})
                                    asignado_exitosamente = True
                            except Exception:
                                pass
                            
                            # Fallback final por SQL directo si las estrategias de servicio fallan
                            if not asignado_exitosamente:
                                try:
                                    db.execute(
                                        text("INSERT INTO salon_profesor (salon_id, profesor_id) VALUES (:salon_id, :profesor_id)"),
                                        {"salon_id": s_id, "profesor_id": prof_id}
                                    )
                                    db.commit()
                                    asignado_exitosamente = True
                                except Exception as ex_sql:
                                    self.mostrar_notificacion(e, f"Aviso de Salón: {str(ex_sql)}", es_error=True)

                for s_id, rel_id in map_rel_id_salon.items():
                    if s_id not in self.salones_temp:
                        self.salon_prof_service.desasignar(db, rel_id)

                self.mostrar_notificacion(e, "Profesor guardado/actualizado exitosamente.")
                self.cerrar_modal(self.modal_formulario, e)
                self.cargar_datos(db)
                self.txt_buscar.value = ""
                e.page.update()
                
            except Exception as ex:
                self.mostrar_notificacion(e, f"Error general al procesar: {str(ex)}", es_error=True)

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
        for row in self.tabla_profesores.rows:
            row.visible = (texto in str(row.data)) if row.data else True
        e.page.update()

    def cargar_datos_iniciales(self):
        with SessionLocal() as db:
            self.cargar_datos(db)

    def cargar_datos(self, db: Session):
        """Consume servicios para construir las tablas en memoria antes del renderizado."""
        try:
            self.map_profesores.clear()
            self.map_asignaturas.clear()
            self.map_asignaturas_detalladas.clear()
            self.sesiones_completas.clear()
            self.dias_sesiones.clear()
            self.map_salones.clear() 
            
            if self.salon_service:
                all_salones = self.salon_service.obtener_todos(db)
                opciones_salones = []
                for s in all_salones:
                    nombre_salon = getattr(s, 'nombre', f"Salón {s.id}")
                    self.map_salones[s.id] = nombre_salon
                    opciones_salones.append(ft.dropdown.Option(key=str(s.id), text=nombre_salon))
                self.dd_salon.options = opciones_salones

            if self.cur_asig_service and self.asig_service:
                all_ca = self.cur_asig_service.obtener_todos(db)
                opciones_ca = []

                map_menciones_db = {}
                for tabla_mencion in ['mencion', 'menciones']:
                    try:
                        res_m = db.execute(text(f"SELECT id, nombre FROM {tabla_mencion}"))
                        for row_m in res_m:
                            map_menciones_db[row_m[0]] = row_m[1]
                        if map_menciones_db:
                            break
                    except Exception:
                        continue

                for ca in all_ca:
                    asig_obj = self.asig_service.obtener_por_id(db, ca.asignatura_id)
                    nombre_asig = asig_obj.nombre if asig_obj else "Desconocida"
                    
                    curso_str = ""
                    mencion_str = ""
                    if self.curso_service:
                        cur_obj = self.curso_service.obtener_por_id(db, ca.curso_id)
                        if cur_obj:
                            year = getattr(cur_obj, 'year', '') or getattr(cur_obj, 'anio', '') or getattr(cur_obj, 'grado', '')
                            seccion = getattr(cur_obj, 'seccion', '') or getattr(cur_obj, 'grupo', '')
                            
                            mencion_id = getattr(cur_obj, 'mencion_id', None)
                            if mencion_id and mencion_id in map_menciones_db:
                                mencion_str = str(map_menciones_db[mencion_id]).strip()
                            
                            if not mencion_str:
                                mencion_obj = getattr(cur_obj, 'mencion', None)
                                if mencion_obj:
                                    if hasattr(mencion_obj, 'nombre') and mencion_obj.nombre:
                                        mencion_str = str(mencion_obj.nombre).strip()
                                    elif isinstance(mencion_obj, str) and mencion_obj.strip():
                                        mencion_str = mencion_obj.strip()
                                    elif isinstance(mencion_obj, int) and mencion_obj in map_menciones_db:
                                        mencion_str = str(map_menciones_db[mencion_obj]).strip()
                            
                            if not mencion_str:
                                posibles_campos = ['especialidad', 'modalidad', 'area', 'carrera', 'mencion_nombre', 'nombre_mencion', 'especialidad_id']
                                for campo in posibles_campos:
                                    val = getattr(cur_obj, campo, None)
                                    if val is not None:
                                        if isinstance(val, int) and val in map_menciones_db:
                                            mencion_str = str(map_menciones_db[val]).strip()
                                            break
                                        elif isinstance(val, str) and val.strip():
                                            mencion_str = val.strip()
                                            break
                                        elif hasattr(val, 'nombre') and val.nombre:
                                            mencion_str = str(val.nombre).strip()
                                            break

                            partes_curso = []
                            info_base = f"{year} {seccion}".strip()
                            if info_base:
                                partes_curso.append(info_base)
                            
                            if mencion_str:
                                if "mención" not in mencion_str.lower() and "mencion" not in mencion_str.lower():
                                    mencion_formateada = f"Mención {mencion_str}"
                                else:
                                    mencion_formateada = mencion_str
                                partes_curso.append(mencion_formateada)
                            
                            if partes_curso:
                                curso_str = f"({', '.join(partes_curso)})"
                                
                    texto_formateado = f"{nombre_asig} {curso_str}".strip()
                    
                    self.map_asignaturas[ca.id] = texto_formateado
                    self.map_asignaturas_detalladas[ca.id] = {
                        "nombre_asig": nombre_asig,
                        "curso_str": curso_str,
                        "texto_formateado": texto_formateado
                    }
                    opciones_ca.append(ft.dropdown.Option(str(ca.id), texto_formateado))
                
                self.dd_asig.options = opciones_ca

            if self.sesion_service:
                all_ses = self.sesion_service.obtener_todos(db)
                for s in all_ses:
                    dia = str(getattr(s, 'dia', '')).strip().capitalize()
                    h_i, min_i = self.normalizar_y_minutos(getattr(s, 'hora_inicio', ''))
                    h_f, min_f = self.normalizar_y_minutos(getattr(s, 'hora_fin', ''))
                    
                    s_data = {'id': s.id, 'dia': dia, 'h_i': h_i, 'h_f': h_f, 'min_i': min_i, 'min_f': min_f}
                    self.sesiones_completas[s.id] = s_data
                    
                    if dia not in self.dias_sesiones:
                        self.dias_sesiones[dia] = []
                    self.dias_sesiones[dia].append(s_data)

                def orden_cronologico_dias(d):
                    d_lower = d.lower().strip()
                    mapa = {"lu": 1, "ma": 2, "mi": 3, "ju": 4, "vi": 5, "sa": 6, "do": 7}
                    for clave, valor in mapa.items():
                        if d_lower.startswith(clave): return valor
                    return 99

                for dia in self.dias_sesiones:
                    self.dias_sesiones[dia].sort(key=lambda x: x['min_i'])
                
                self.dd_dia.options = [ft.dropdown.Option(d) for d in sorted(self.dias_sesiones.keys(), key=orden_cronologico_dias)]

            profesores_db = self.prof_service.obtener_todos(db)
            rows_buffer = []

            for p in sorted(profesores_db, key=lambda x: f"{x.nombre} {x.apellido}".lower()):
                rels_asig = self.prof_asig_service.obtener_por_profesor(db, p.id)
                rels_ses = self.sesion_prof_service.obtener_por_profesor(db, p.id)
                rels_salon = self.salon_prof_service.obtener_por_profesor(db, p.id) 
                
                asig_ids = {r.curso_asignatura_id for r in rels_asig}
                ses_ids = {r.sesion_id for r in rels_ses}
                salon_ids = {r.salon_id for r in rels_salon} 
                
                self.map_profesores[p.id] = {
                    "id": p.id,
                    "nombre": p.nombre,
                    "apellido": p.apellido,
                    "estado": getattr(p, "estado", True),
                    "asignaturas": asig_ids,
                    "sesiones": ses_ids,
                    "salones": salon_ids
                }

                nombre_comp = f"{p.nombre} {p.apellido}"
                is_act = getattr(p, "estado", True)
                
                chip_estado = ft.Container(
                    content=ft.Text("Activo" if is_act else "Inactivo", size=11, weight=ft.FontWeight.BOLD, 
                                  color="#4CAF50" if is_act else "#E57373"),
                    bgcolor="#1E4620" if is_act else "#4A1B1B", 
                    padding=ft.padding.symmetric(horizontal=10, vertical=4), border_radius=12
                )

                btn_ver = ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.icons.VISIBILITY, size=16, color=ft.colors.WHITE),
                        ft.Text("Ver", color=ft.colors.WHITE)
                    ], spacing=6, tight=True),
                    bgcolor="#2B4C7E",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8)
                    ),
                    on_click=lambda ex, id_p=p.id: self.abrir_modal_detalle(id_p, ex)
                )

                rows_buffer.append(
                    ft.DataRow(
                        data=nombre_comp.lower(),
                        cells=[
                            ft.DataCell(ft.Row([ft.Icon(ft.icons.PERSON, color="#5B9BD5", size=18), ft.Text(nombre_comp, color=ft.colors.WHITE, weight=ft.FontWeight.W_500)], spacing=8)),
                            ft.DataCell(chip_estado),
                            ft.DataCell(btn_ver),
                            ft.DataCell(ft.Row([
                                ft.Container(content=ft.IconButton(ft.icons.EDIT, icon_color="#A0A0B0", icon_size=16, on_click=lambda ex, id_p=p.id: self.abrir_modal_editar(id_p, ex)), bgcolor="#2A2D3E", border_radius=8, width=32, height=32),
                                ft.Container(content=ft.IconButton(ft.icons.DELETE, icon_color="#E57373", icon_size=16, on_click=lambda ex, id_p=p.id: self.pedir_confirmacion_eliminar(id_p, ex)), bgcolor="#3E2A2A", border_radius=8, width=32, height=32),
                            ], spacing=8)),
                        ]
                    )
                )

            self.tabla_profesores.rows = rows_buffer
            self.txt_total.value = f"Profesores registrados: {len(profesores_db)}"
            
        except Exception as ex:
            print(f"Error cargando datos: {ex}")