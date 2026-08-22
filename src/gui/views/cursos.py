import flet as ft
from src.database.connection import SessionLocal
from src.services.curso_service import CursoService
from src.services.curso_asignatura_service import CursoAsignaturaService
from src.services.mencion_service import MencionService
from src.services.asignatura_service import AsignaturaService

OPCIONES_YEARS = ["1ro", "2do", "3ro", "4to", "5to", "6to"]
OPCIONES_SECCIONES = ["A", "B", "C", "D"]

def normalizar_year(val) -> str:
    """Extrae el dígito principal del año para garantizar coincidencia en filtros."""
    if not val:
        return ""
    s = str(val).lower().strip()
    for digito in ["1", "2", "3", "4", "5", "6"]:
        if digito in s:
            return digito
    return s


def vista_cursos():
    # =========================================================================
    # PASO 1: Servicios e Inicialización de UI
    # =========================================================================
    curso_service = CursoService()
    curso_asig_service = CursoAsignaturaService()
    mencion_service = MencionService()
    asig_service = AsignaturaService()

    estilo_tarjeta_oscura = {
        "bgcolor": "#1E202D",
        "border_radius": 10,
        "padding": ft.padding.symmetric(horizontal=15, vertical=6),
        "border": ft.border.all(1, "#303346"),
        "height": 45
    }

    grilla_cursos = ft.Row(
        wrap=True, 
        spacing=20, 
        run_spacing=20, 
        alignment=ft.MainAxisAlignment.CENTER
    )
    
    txt_total = ft.Text("0", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
    txt_total_asig = ft.Text("0", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)

    estilo_input = {
        "border_color": "#303346",
        "focused_border_color": "#439A5D",
        "border_radius": 10,
        "bgcolor": "#13141C",
        "color": ft.colors.WHITE,
        "height": 52,
        "content_padding": 15
    }

    id_actual = ft.Text(visible=False)
    
    dd_year = ft.Dropdown(
        label="Año",
        options=[ft.dropdown.Option(y) for y in OPCIONES_YEARS],
        value="1ro",
        **estilo_input, expand=True
    )
    
    dd_seccion = ft.Dropdown(
        label="Sección",
        options=[ft.dropdown.Option(s) for s in OPCIONES_SECCIONES],
        value="A",
        **estilo_input, expand=True
    )

    def on_mencion_change(e):
        txt_nueva_mencion.visible = dd_mencion.value == "__nueva__"
        if not txt_nueva_mencion.visible:
            txt_nueva_mencion.value = ""
        txt_nueva_mencion.update()

    dd_mencion = ft.Dropdown(
        label="Mención Técnica",
        on_change=on_mencion_change,
        **estilo_input
    )

    txt_nueva_mencion = ft.TextField(
        label="Nombre de nueva mención",
        hint_text="Ej. Informática, Contabilidad...",
        visible=False,
        **estilo_input
    )

    def on_asignatura_change(e):
        container_nueva_asig.visible = dd_asignatura.value == "__nueva__"
        if not container_nueva_asig.visible:
            txt_nombre_nueva_asig.value = ""
        container_nueva_asig.update()

    dd_asignatura = ft.Dropdown(
        label="Asignatura",
        on_change=on_asignatura_change,
        **estilo_input
    )

    txt_nombre_nueva_asig = ft.TextField(
        label="Nombre de la nueva asignatura",
        hint_text="Ej. Física, Química...",
        **estilo_input
    )

    dd_tipo_nueva_asig = ft.Dropdown(
        label="Tipo de asignatura",
        **estilo_input
    )

    container_nueva_asig = ft.Column([
        txt_nombre_nueva_asig,
        dd_tipo_nueva_asig
    ], spacing=15, visible=False)
    
    dd_horas_asig = ft.Dropdown(
        label="Horas",
        options=[ft.dropdown.Option(str(h)) for h in range(1, 9)],
        value=None,
        border_color="#303346",
        focused_border_color="#439A5D",
        border_radius=10,
        bgcolor="#13141C",
        color=ft.colors.WHITE,
        height=52,
        content_padding=15,
        width=130
    )
    
    lista_chips_asig = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)

    dd_filtro_year = ft.Dropdown(
        label="Filtrar Año",
        options=[ft.dropdown.Option("TODOS", "Todos los Años")] + [ft.dropdown.Option(y) for y in OPCIONES_YEARS],
        value="TODOS", width=160,
        border_color="#303346", focused_border_color="#439A5D", border_radius=10,
        bgcolor="#13141C", color=ft.colors.WHITE, text_style=ft.TextStyle(size=13)
    )
    
    dd_filtro_mencion = ft.Dropdown(
        label="Filtrar Mención",
        options=[ft.dropdown.Option("TODAS", "Todas las Menciones")],
        value="TODAS", width=200,
        border_color="#303346", focused_border_color="#439A5D", border_radius=10,
        bgcolor="#13141C", color=ft.colors.WHITE, text_style=ft.TextStyle(size=13)
    )

    # Estado Local en Memoria
    asignaturas_temp = []
    map_menciones = {}
    map_menciones_orden = {}
    map_asignaturas = {}
    map_cursos = {}

    # =========================================================================
    # PASO 2: Métodos de soporte e interacción
    # =========================================================================
    def mostrar_notificacion(page: ft.Page, mensaje: str, es_error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.colors.WHITE),
            bgcolor=ft.colors.RED_700 if es_error else ft.colors.GREEN_700,
            duration=3000
        )
        page.snack_bar = snack
        snack.open = True
        page.update()

    def refrescar_chips_asig():
        lista_chips_asig.controls.clear()
        for asig in asignaturas_temp:
            lista_chips_asig.controls.append(
                ft.Container(
                    bgcolor="#2A2D3E", border=ft.border.all(1, "#5A5D70"), border_radius=10,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    content=ft.Row([
                        ft.Column([
                            ft.Text(asig["nombre"], color=ft.colors.WHITE, size=13, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{asig.get('tipo', 'Teórica')} · {asig['horas']}h/sem", color="#A0A0B0", size=11)
                        ], spacing=1, expand=True),
                        ft.IconButton(
                            ft.icons.CLOSE, icon_color="#A0A0B0", icon_size=14,
                            on_click=lambda e, a=asig: quitar_asig(e, a), width=20, height=20
                        )
                    ])
                )
            )

    def quitar_asig(e, asig):
        if asig in asignaturas_temp:
            asignaturas_temp.remove(asig)
            refrescar_chips_asig()
            lista_chips_asig.update()

    def agregar_asignatura(e):
        if not dd_horas_asig.value:
            mostrar_notificacion(e.page, "Debe seleccionar la cantidad de horas para esta materia.", es_error=True)
            return
            
        horas = int(dd_horas_asig.value)
        
        if dd_asignatura.value == "__nueva__":
            nombre_asig = txt_nombre_nueva_asig.value.strip() if txt_nombre_nueva_asig.value else ""
            tipo_asig = dd_tipo_nueva_asig.value or ""
            
            if not nombre_asig:
                mostrar_notificacion(e.page, "Debe ingresar el nombre de la nueva asignatura.", es_error=True)
                return
            
            if any(a["nombre"].lower() == nombre_asig.lower() for a in asignaturas_temp):
                mostrar_notificacion(e.page, "La asignatura ya está agregada al curso.", es_error=True)
                return

            asignaturas_temp.append({
                "id": None,
                "asignatura_id": None,
                "nombre": nombre_asig,
                "tipo": tipo_asig,
                "horas": horas,
                "es_nueva": True
            })
            
        else:
            asig_id_str = dd_asignatura.value
            if not asig_id_str:
                mostrar_notificacion(e.page, "Seleccione una asignatura para agregar.", es_error=True)
                return
            encontrado = map_asignaturas.get(int(asig_id_str))
            if not encontrado:
                return
            if any(not a.get("es_nueva") and str(a.get("asignatura_id")) == str(encontrado["id"]) for a in asignaturas_temp):
                mostrar_notificacion(e.page, "La asignatura ya está agregada al curso.", es_error=True)
                return
                
            asignaturas_temp.append({
                "id": encontrado["id"],
                "asignatura_id": encontrado["id"],
                "nombre": encontrado["nombre"],
                "tipo": encontrado["tipo"],
                "horas": horas,
                "es_nueva": False
            })

        dd_asignatura.value = None
        txt_nombre_nueva_asig.value = ""
        container_nueva_asig.visible = False
        dd_horas_asig.value = None 
        
        refrescar_chips_asig()
        
        dd_asignatura.update()
        dd_horas_asig.update()
        container_nueva_asig.update()
        lista_chips_asig.update()

    def cerrar_modal_formulario(e):
        asignaturas_temp.clear()
        refrescar_chips_asig()
        modal_formulario.open = False
        e.page.update()

    def cerrar_modal_confirmacion(e):
        modal_confirmacion.open = False
        e.page.update()

    def pre_guardar_curso(e):
        if not dd_year.value or not dd_seccion.value:
            mostrar_notificacion(e.page, "El año y la sección son obligatorios.", es_error=True)
            return

        if not dd_mencion.value:
            mostrar_notificacion(e.page, "Debe seleccionar una mención.", es_error=True)
            return

        if dd_mencion.value == "__nueva__":
            if not txt_nueva_mencion.value or not txt_nueva_mencion.value.strip():
                mostrar_notificacion(e.page, "Debe ingresar el nombre de la nueva mención.", es_error=True)
                return

        # VALIDACIÓN: Exigir al menos una asignatura registrada
        if not asignaturas_temp:
            mostrar_notificacion(e.page, "Debe registrar al menos una asignatura para el curso.", es_error=True)
            return

        id_form = str(id_actual.value).strip()
        year_form = str(dd_year.value).strip()
        seccion_form = str(dd_seccion.value).strip()
        
        if dd_mencion.value != "__nueva__":
            mencion_val = str(dd_mencion.value).strip()
            for c_id, c in map_cursos.items():
                if normalizar_year(c["year"]) == normalizar_year(year_form) and str(c["seccion"]).strip() == seccion_form:
                    if str(c.get("mencion_id")) == mencion_val:
                        if id_form == "" or str(c_id) != id_form:
                            mostrar_notificacion(e.page, "Este curso ya se encuentra registrado.", es_error=True)
                            return

        if id_form != "":
            modal_formulario.open = False
            modal_confirmacion.title = ft.Text("¿Confirmar Edición?", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
            modal_confirmacion.content = ft.Text("¿Desea guardar los cambios en este curso?", color="#A0A0B0")
            modal_confirmacion.actions = [
                ft.TextButton("Cancelar", on_click=cerrar_modal_confirmacion, style=ft.ButtonStyle(color="#A0A0B0")),
                ft.ElevatedButton("Sí, Confirmar", on_click=ejecutar_guardado, bgcolor="#439A5D", color=ft.colors.WHITE)
            ]
            e.page.dialog = modal_confirmacion
            modal_confirmacion.open = True
            e.page.update()
        else:
            ejecutar_guardado(e)

    def ejecutar_guardado(e):
        modal_confirmacion.open = False
        modal_formulario.open = False
        e.page.update()

        with SessionLocal() as db:
            try:
                mencion_id = None
                if dd_mencion.value == "__nueva__":
                    nombre_nueva = txt_nueva_mencion.value.strip()
                    nueva_menc = mencion_service.crear(db, nombre=nombre_nueva)
                    mencion_id = nueva_menc.id
                elif dd_mencion.value:
                    mencion_id = int(dd_mencion.value)

                asignaturas_procesadas = []
                for asig in asignaturas_temp:
                    asig_id = asig.get("asignatura_id")
                    if asig.get("es_nueva"):
                        nueva_asig_db = asig_service.crear(db, nombre=asig["nombre"], tipo=asig["tipo"])
                        asig_id = nueva_asig_db.id
                    
                    asignaturas_procesadas.append({
                        "asignatura_id": asig_id,
                        "horas": asig["horas"]
                    })

                if id_actual.value == "":
                    nuevo_curso = curso_service.crear(db, seccion=dd_seccion.value, year=dd_year.value, mencion_id=mencion_id)
                    
                    # Limpieza preventiva por si SQLite recicla un ID con datos huérfanos previos
                    rels_antiguas = curso_asig_service.obtener_por_curso(db, nuevo_curso.id)
                    for rel in rels_antiguas:
                        curso_asig_service.eliminar(db, rel.id)

                    for asig in asignaturas_procesadas:
                        curso_asig_service.crear(db, curso_id=nuevo_curso.id, asignatura_id=asig["asignatura_id"], horas_semanales=asig["horas"])
                    
                    mostrar_notificacion(e.page, "Curso registrado exitosamente.")
                else:
                    curso_id = int(id_actual.value)
                    curso_service.actualizar(db, curso_id, seccion=dd_seccion.value, year=dd_year.value, mencion_id=mencion_id)
                    
                    rels_actuales = curso_asig_service.obtener_por_curso(db, curso_id)
                    ids_actuales_asig = {r.asignatura_id: r for r in rels_actuales}
                    ids_nuevos_asig = {asig["asignatura_id"]: asig for asig in asignaturas_procesadas}

                    for asig_id, rel in ids_actuales_asig.items():
                        if asig_id not in ids_nuevos_asig:
                            curso_asig_service.eliminar(db, rel.id)

                    for asig_id, asig in ids_nuevos_asig.items():
                        if asig_id in ids_actuales_asig:
                            curso_asig_service.actualizar(db, ids_actuales_asig[asig_id].id, horas_semanales=asig["horas"])
                        else:
                            curso_asig_service.crear(db, curso_id=curso_id, asignatura_id=asig_id, horas_semanales=asig["horas"])
                    
                    mostrar_notificacion(e.page, "Curso actualizado exitosamente.")

                asignaturas_temp.clear()
                cargar_datos(e.page)
                
            except ValueError as ve:
                mostrar_notificacion(e.page, str(ve), es_error=True)
            except Exception as ex:
                mostrar_notificacion(e.page, f"Error inesperado: {str(ex)}", es_error=True)

    def pedir_confirmacion_eliminar(cur_id, e):
        modal_confirmacion.title = ft.Text("¿Confirmar Eliminación?", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
        modal_confirmacion.content = ft.Text("¿Desea eliminar de forma permanente este curso?", color="#A0A0B0")
        modal_confirmacion.actions = [
            ft.TextButton("Cancelar", on_click=cerrar_modal_confirmacion, style=ft.ButtonStyle(color="#A0A0B0")),
            ft.ElevatedButton("Sí, Eliminar", on_click=lambda ex: ejecutar_eliminacion(cur_id, ex), bgcolor="#E57373", color=ft.colors.WHITE)
        ]
        e.page.dialog = modal_confirmacion
        modal_confirmacion.open = True
        e.page.update()

    def ejecutar_eliminacion(cur_id, e):
        modal_confirmacion.open = False
        e.page.update()
        with SessionLocal() as db:
            try:
                curso_service.eliminar(db, cur_id)
                mostrar_notificacion(e.page, "Curso eliminado exitosamente.")
                cargar_datos(e.page)
            except ValueError as ve:
                mostrar_notificacion(e.page, str(ve), es_error=True)
            except Exception as ex:
                mostrar_notificacion(e.page, f"Error inesperado: {str(ex)}", es_error=True)

    def filtrar_grilla(e=None):
        grilla_cursos.controls.clear()
        total_asig = 0
        cursos_visibles = 0

        year_filtro = dd_filtro_year.value
        mencion_filtro = dd_filtro_mencion.value

        cursos_ordenados = sorted(
            map_cursos.values(),
            key=lambda x: (
                map_menciones_orden.get(x["mencion_id"], 999),
                int(normalizar_year(x["year"])) if normalizar_year(x["year"]).isdigit() else 99,
                str(x["seccion"]).upper()
            )
        )

        for cur in cursos_ordenados:
            cur_mencion_id = str(cur["mencion_id"]) if cur["mencion_id"] else ""

            if year_filtro and year_filtro != "TODOS":
                if normalizar_year(cur["year"]) != normalizar_year(year_filtro):
                    continue

            if mencion_filtro and mencion_filtro != "TODAS":
                if cur_mencion_id != mencion_filtro:
                    continue

            cursos_visibles += 1
            total_asig += len(cur.get("asignaturas", []))
            chips_asig = ft.Row(wrap=True, spacing=5)
            for asig in cur.get("asignaturas", []):
                chips_asig.controls.append(
                    ft.Container(
                        content=ft.Text(f"{asig['nombre']} ({asig['horas']}h)", size=10, color="#A0A0B0"),
                        bgcolor="#2A2D3E",
                        border=ft.border.all(1, "#5A5D70"),
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        border_radius=8
                    )
                )

            tarjeta = ft.Container(
                width=300, bgcolor="#1E202D", border_radius=15,
                border=ft.border.all(1, "#303346"), padding=0,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Column([
                    ft.Container(
                        bgcolor="#2A2D3E", padding=16,
                        border_radius=ft.border_radius.only(top_left=15, top_right=15),
                        content=ft.Row([
                            ft.Icon(ft.icons.CLASS_, color="#5B9BD5", size=24),
                            ft.Column([
                                ft.Text(f"{cur['year']} año — Sección {cur['seccion']}", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, size=15),
                                ft.Text(f"{cur['mencion']} ({cur.get('codigo_mencion', '')})", color="#5B9BD5", size=12)
                            ], spacing=1, expand=True),
                            ft.Container(
                                content=ft.Text(str(len(cur.get("asignaturas", []))), size=18, weight=ft.FontWeight.BOLD, color="#5B9BD5"),
                                bgcolor="#13141C", width=36, height=36, border_radius=8, alignment=ft.alignment.center
                            )
                        ], spacing=10)
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=14, vertical=12),
                        content=ft.Column([
                            ft.Text("Asignaturas:", color="#A0A0B0", size=11, weight=ft.FontWeight.BOLD),
                            chips_asig if chips_asig.controls else ft.Text("Sin asignaturas", color="#5A5D70", size=11),
                            ft.Container(height=6),
                            ft.Row([
                                ft.Container(
                                    content=ft.IconButton(ft.icons.EDIT, icon_color="#A0A0B0", icon_size=16,
                                                          on_click=lambda ex, cid=cur["id"]: abrir_modal_editar(cid, ex)),
                                    bgcolor="#2A2D3E", border_radius=8, width=32, height=32
                                ),
                                ft.Container(
                                    content=ft.IconButton(ft.icons.DELETE, icon_color="#E57373", icon_size=16,
                                                          on_click=lambda ex, cid=cur["id"]: pedir_confirmacion_eliminar(cid, ex)),
                                    bgcolor="#3E2A2A", border_radius=8, width=32, height=32
                                ),
                            ], spacing=8)
                        ], spacing=4)
                    )
                ], spacing=0)
            )
            grilla_cursos.controls.append(tarjeta)

        txt_total.value = str(cursos_visibles)
        txt_total_asig.value = str(total_asig)
        
        if e and e.page:
            grilla_cursos.update()
            txt_total.update()
            txt_total_asig.update()

    dd_filtro_year.on_change = filtrar_grilla
    dd_filtro_mencion.on_change = filtrar_grilla

    # =========================================================================
    # PASO 3: Modales estructurados
    # =========================================================================
    modal_confirmacion = ft.AlertDialog(
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        actions_padding=20,
        actions_alignment=ft.MainAxisAlignment.END
    )

    modal_formulario = ft.AlertDialog(
        title=ft.Text("Formulario de Curso", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
        bgcolor="#1E202D",
        shape=ft.RoundedRectangleBorder(radius=15),
        content=ft.Container(
            width=580,
            height=720,
            padding=ft.padding.only(top=5, right=5),
            content=ft.Column([
                id_actual,
                ft.Row([
                    dd_year,
                    dd_seccion,
                ], spacing=15),
                
                dd_mencion,
                txt_nueva_mencion,
                
                ft.Divider(color="#303346", height=10),

                dd_asignatura,
                container_nueva_asig,

                ft.Row([
                    dd_horas_asig,
                    ft.ElevatedButton(
                        "Agregar",
                        icon=ft.icons.ADD,
                        bgcolor="#439A5D",
                        color=ft.colors.WHITE,
                        on_click=agregar_asignatura,
                        height=52,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                            padding=ft.padding.symmetric(horizontal=20)
                        )
                    )
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                
                ft.Container(
                    content=lista_chips_asig,
                    height=200,
                    bgcolor="#13141C",
                    border=ft.border.all(1, "#303346"),
                    border_radius=10,
                    padding=10,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                ),
            ], spacing=15, scroll=ft.ScrollMode.AUTO)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=cerrar_modal_formulario, style=ft.ButtonStyle(color="#A0A0B0")),
            ft.ElevatedButton(
                "Guardar Registro", on_click=pre_guardar_curso,
                bgcolor="#439A5D", color=ft.colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            )
        ],
        actions_padding=20
    )

    def abrir_modal_crear(e):
        asignaturas_temp.clear()
        refrescar_chips_asig()
        
        id_actual.value = ""
        dd_year.value = "1ro"
        dd_seccion.value = "A"
        dd_mencion.value = dd_mencion.options[0].key if dd_mencion.options else None
        txt_nueva_mencion.value = ""
        txt_nueva_mencion.visible = False
        dd_asignatura.value = None
        txt_nombre_nueva_asig.value = ""
        if dd_tipo_nueva_asig.options:
            dd_tipo_nueva_asig.value = dd_tipo_nueva_asig.options[0].key
        container_nueva_asig.visible = False
        dd_horas_asig.value = None
        
        e.page.dialog = modal_formulario
        modal_formulario.open = True
        e.page.update()

    def abrir_modal_editar(cur_id, e):
        asignaturas_temp.clear()
        
        cur_dict = map_cursos.get(cur_id)
        if not cur_dict:
            return
        id_actual.value = str(cur_dict["id"])
        
        yr_norm = normalizar_year(cur_dict["year"])
        match_yr = next((y for y in OPCIONES_YEARS if normalizar_year(y) == yr_norm), "1ro")
        dd_year.value = match_yr

        dd_seccion.value = cur_dict["seccion"] if cur_dict["seccion"] in OPCIONES_SECCIONES else "A"
        dd_mencion.value = str(cur_dict["mencion_id"]) if cur_dict.get("mencion_id") else None
        
        txt_nueva_mencion.value = ""
        txt_nueva_mencion.visible = False

        dd_asignatura.value = None
        txt_nombre_nueva_asig.value = ""
        if dd_tipo_nueva_asig.options:
            dd_tipo_nueva_asig.value = dd_tipo_nueva_asig.options[0].key
        container_nueva_asig.visible = False
        
        dd_horas_asig.value = None

        for asig_data in cur_dict.get("asignaturas", []):
            asignaturas_temp.append({
                "id": asig_data["asignatura_id"],
                "asignatura_id": asig_data["asignatura_id"],
                "nombre": asig_data["nombre"],
                "tipo": asig_data.get("tipo", ""),
                "horas": asig_data["horas"],
                "es_nueva": False
            })
        
        refrescar_chips_asig()
        
        e.page.dialog = modal_formulario
        modal_formulario.open = True
        e.page.update()

    # =========================================================================
    # PASO 4: Carga de datos dinámicos desde Base de Datos
    # =========================================================================
    def cargar_datos(page: ft.Page | None = None):
        with SessionLocal() as db:
            try:
                menciones_db = mencion_service.obtener_todos(db)
                map_menciones.clear()
                map_menciones_orden.clear()
                
                for idx, m in enumerate(menciones_db):
                    map_menciones[m.id] = {
                        "id": m.id,
                        "nombre": m.nombre,
                        "codigo": getattr(m, "codigo", getattr(m, "siglas", ""))
                    }
                    map_menciones_orden[m.id] = idx

                asignaturas_db = asig_service.obtener_todos(db)
                map_asignaturas.clear()
                
                tipos_unicos = set()
                for a in asignaturas_db:
                    tipo_val = getattr(a, "tipo", None)
                    if tipo_val:
                        tipos_unicos.add(tipo_val)
                    map_asignaturas[a.id] = {
                        "id": a.id,
                        "nombre": a.nombre,
                        "tipo": tipo_val or ""
                    }

                dd_tipo_nueva_asig.options = [ft.dropdown.Option(t) for t in sorted(tipos_unicos)]
                if dd_tipo_nueva_asig.options:
                    dd_tipo_nueva_asig.value = dd_tipo_nueva_asig.options[0].key
                else:
                    dd_tipo_nueva_asig.value = None

                opciones_form_mencion = []
                for m in map_menciones.values():
                    nombre_val = m["nombre"]
                    nombre_texto = nombre_val if len(nombre_val) <= 25 else nombre_val[:22] + "..."
                    opciones_form_mencion.append(ft.dropdown.Option(text=nombre_texto, key=str(m["id"])))
                opciones_form_mencion.append(ft.dropdown.Option(text="[+] Nueva Mención", key="__nueva__"))
                dd_mencion.options = opciones_form_mencion

                opciones_filtro_mencion = [ft.dropdown.Option("TODAS", "Todas las Menciones")]
                for m in map_menciones.values():
                    nombre_val = m["nombre"]
                    nombre_texto = nombre_val if len(nombre_val) <= 20 else nombre_val[:17] + "..."
                    opciones_filtro_mencion.append(ft.dropdown.Option(key=str(m["id"]), text=nombre_texto))
                dd_filtro_mencion.options = opciones_filtro_mencion

                opciones_form_asig = []
                for a in map_asignaturas.values():
                    opciones_form_asig.append(ft.dropdown.Option(text=a["nombre"], key=str(a["id"])))
                opciones_form_asig.append(ft.dropdown.Option(text="[+] Nueva Asignatura", key="__nueva__"))
                dd_asignatura.options = opciones_form_asig

                cursos_db = curso_service.obtener_todos(db)
                map_cursos.clear()
                for c in cursos_db:
                    mencion_info = map_menciones.get(c.mencion_id) if c.mencion_id else None
                    m_nombre = mencion_info["nombre"] if mencion_info else "General"
                    m_codigo = mencion_info["codigo"] if mencion_info else ""

                    rels = curso_asig_service.obtener_por_curso(db, c.id)
                    asig_list = []
                    for r in rels:
                        asig_obj = map_asignaturas.get(r.asignatura_id)
                        if asig_obj:
                            asig_list.append({
                                "asignatura_id": r.asignatura_id,
                                "nombre": asig_obj["nombre"],
                                "tipo": asig_obj["tipo"],
                                "horas": r.horas_semanales
                            })

                    map_cursos[c.id] = {
                        "id": c.id,
                        "year": c.year,
                        "seccion": c.seccion,
                        "mencion": m_nombre,
                        "codigo_mencion": m_codigo,
                        "mencion_id": c.mencion_id,
                        "asignaturas": asig_list
                    }

                filtrar_grilla()
                if page:
                    page.update()

            except Exception as ex:
                if page:
                    mostrar_notificacion(page, f"Error al cargar datos: {str(ex)}", es_error=True)

    cargar_datos()

    # =========================================================================
    # PASO 5: Retorno con Cabecera Fija y Contenido Centrado y Separado
    # =========================================================================
    tarjeta_stats = ft.Container(
        **estilo_tarjeta_oscura,
        content=ft.Row([
            ft.Row([
                txt_total,
                ft.Text("Cursos registrados", color="#A0A0B0", size=13)
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.VerticalDivider(color="#303346", width=1),
            ft.Row([
                txt_total_asig,
                ft.Text("Asignaturas asignadas", color="#A0A0B0", size=13)
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=20, alignment=ft.MainAxisAlignment.CENTER)
    )

    return ft.Container(
        padding=20, 
        expand=True,
        alignment=ft.alignment.top_left,
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column([
                            ft.Text("Gestión de Cursos", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                            ft.Text("Administra los cursos, sus menciones y asignaturas", size=14, color="#A0A0B0")
                        ], spacing=2),
                        ft.Row([
                            ft.Row([
                                dd_filtro_year,
                                dd_filtro_mencion,
                            ], spacing=10),
                            ft.ElevatedButton(
                                "Añadir Curso", icon=ft.icons.ADD, on_click=abrir_modal_crear,
                                bgcolor="#439A5D", color=ft.colors.WHITE,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=20)
                            )
                        ], spacing=30, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                tarjeta_stats,
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                ft.Column(
                    controls=[
                        ft.Container(
                            content=grilla_cursos,
                            padding=ft.padding.only(left=20, right=35, top=5, bottom=20),
                            alignment=ft.alignment.center
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True
        )
    )