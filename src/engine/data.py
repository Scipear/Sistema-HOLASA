from datetime import datetime
from src.database.connection import SessionLocal
from src.database.repositories import (
    ProfesorRepository,
    SesionRepository,
    SalonRepository,
    CursoRepository,
    MencionRepository,
    AsignaturaRepository,
    SesionProfesorRepository,
    CursoAsignaturaRepository,
    ProfesorAsignaturaRepository,
    SalonCursoRepository,
    SalonProfesorRepository
)
from src.engine.classes import Teacher, Subject, Academic_Hour, Room, Group, Event, Availability

class Data():
    def __init__(self):
        self.teachers = []
        self.subjects = []
        self.academic_hours = []
        self.rooms = []
        self.groups = []
        self.academic_hours_limits = {}
        self.DAYS_ORDER = ["Lunes", "Martes", "Miércoles", "Miercoles", "Jueves", "Viernes"]

    def academic_hours_sort(self, s: Academic_Hour):
        day_pos = self.DAYS_ORDER.index(s.dia) if s.dia in self.DAYS_ORDER else 99
        real_hour = self.parse_24h(s.hora_inicio)
        return (day_pos, real_hour)

    def limits_by_day(self) -> dict:
        limits = {}
        for ah in self.academic_hours:
            if ah.day_index not in limits:
                limits[ah.day_index] = {"min": ah.index, "max": ah.index}
            else:
                limits[ah.day_index]["max"] = ah.index
        return limits

    def parse_24h(self, academic_hour: str) -> datetime.time:
        hour_clean = academic_hour.strip()

        for fmt in ("%I:%M %p", "%I:%M%p"):
            try:
                return datetime.strptime(hour_clean, fmt).time()
            except ValueError:
                pass

        try:
            dt = datetime.strptime(hour_clean, "%H:%M")

            if 1 <= dt.hour <= 6:
                dt = dt.replace(hour=dt.hour + 12)
                
            return dt.time()
            
        except ValueError:
            raise ValueError(f"Formato de hora no válido: '{academic_hour}'")

    def load_data(self):
        """Carga y adapta los datos desde la BD SQLite hacia las variables globales del motor."""
        db = SessionLocal()
        taller_room_type = "Taller"

        try:
            rooms_db = SalonRepository().get_all(db)
            self.rooms = [Room(id=s.id, name=s.nombre, is_taller=s.tipo.strip().lower() == taller_room_type.lower() if s.tipo else False) for s in rooms_db]
            rooms_dict = {r.id: r for r in self.rooms}

            academic_hours_db = SesionRepository().get_all(db)
            sorted_academic_hours = sorted(academic_hours_db, key=self.academic_hours_sort)

            days_visited = {}
            current_day_index = 0

            for idx, s in enumerate(sorted_academic_hours):
                if s.dia not in days_visited:
                    days_visited[s.dia] = current_day_index
                    current_day_index += 1

                ah = Academic_Hour(
                    db_id=s.id,
                    index=idx,
                    day=s.dia,
                    day_index=days_visited[s.dia],
                    start_hour=s.hora_inicio,
                    end_hour=s.hora_fin
                )
                self.academic_hours.append(ah)

            self.academic_hours_limits = self.limits_by_day()

            id_to_index = {ah.db_id: ah.index for ah in self.academic_hours}
            teachers_db = ProfesorRepository().get_activos(db)
            teachers_dict = {}
        
            for t in teachers_db:
                teacher_availabilities = SesionProfesorRepository().get_by_profesor(db, t.id)
                t_rooms = SalonProfesorRepository().get_by_profesor(db, t.id)

                total_items = len(teacher_availabilities)
                if total_items % 2 != 0:
                    total_items -= 1
                
                availabilities = []
                # Iteramos de 2 en 2 para agrupar los pares (inicio, fin)
                for i in range(0, total_items, 2):
                    start_id = teacher_availabilities[i].sesion_id
                    end_id = teacher_availabilities[i+1].sesion_id
                    
                    # Traducimos los IDs de la BD a nuestros índices virtuales de la memoria
                    start_idx = id_to_index[start_id]
                    end_idx = id_to_index[end_id]
                    
                    availabilities.append(Availability(start_idx, end_idx))
                
                if t_rooms:
                    teacher_rooms = []
                    for r in t_rooms:
                        teacher_rooms.append(rooms_dict[r.salon_id])
                else:
                    teacher_rooms = None

                t_obj = Teacher(
                    id=t.id,
                    name=t.nombre,
                    last_name=t.apellido,
                    availabilities=availabilities,
                    rooms=teacher_rooms
                )

                self.teachers.append(t_obj)
                teachers_dict[t.id] = t_obj

            groups_db = CursoRepository().get_all(db)
            for g in groups_db:
                speciality = MencionRepository().get_by_id(db, g.mencion_id)
                subjs = CursoAsignaturaRepository().get_by_curso(db, g.id)
                g_rooms = SalonCursoRepository().get_by_curso(db, g.id)
                group_subjects = []

                if g_rooms:
                    groups_rooms = []
                    for r in g_rooms:
                        groups_rooms.append(rooms_dict[r.salon_id])
                else:
                    groups_rooms = None
                    
                for s in subjs:
                    subject = AsignaturaRepository().get_by_id(db, s.asignatura_id)

                    if not subject:
                        continue

                    teacher_subject = ProfesorAsignaturaRepository().get_by_curso_asignatura(db, s.id)
                    ts = teacher_subject[0] if teacher_subject else None
                    assigned_teacher = (
                        teachers_dict[ts.profesor_id]
                        if ts and ts.profesor_id in teachers_dict
                        else None
                    )

                    subj_obj = Subject(
                        id=s.id,  # Usamos el ID de la relación curso_asignatura
                        name=subject.nombre,
                        hours=s.horas_semanales,
                        subject_type=subject.tipo,
                        teacher=assigned_teacher
                    )

                    group_subjects.append(subj_obj)
                    self.subjects.append(subj_obj)
                
                    
                group_obj = Group(
                    id=g.id,
                    year=g.year,
                    name=f"{g.year} {speciality.nombre} {g.seccion}",
                    subjects=group_subjects,
                    rooms=groups_rooms
                )
                self.groups.append(group_obj)

            print(f"✅ Carga exitosa desde BD: {len(self.teachers)} profesores, {len(self.groups)} cursos, {len(self.rooms)} salones.")
        
        finally:
            db.close()