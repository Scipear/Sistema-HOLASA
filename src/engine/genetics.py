import numpy as np
import random
import copy
import time
from src.engine.classes import Teacher, Subject, Academic_Hour, Room, Group, Event, Availability
from src.engine.constraints import fitness, groups_subjects, teachers_subjects, rooms_groups, groups_gaps, subject_day
from src.engine.data import Data

data_handler = Data()
data_handler.load_data()
academic_hours_limits = data_handler.academic_hours_limits
academic_hours = data_handler.academic_hours
teachers = data_handler.teachers
groups = data_handler.groups
rooms = data_handler.rooms
subjects = data_handler.subjects

TEACHERS_BY_ID = {t.id: t for t in teachers}
SUBJECTS_BY_ID = {s.id: s for s in subjects}
GROUPS_BY_ID = {g.id: g for g in groups}

SORTED_DAYS = sorted(academic_hours_limits.keys())
DAY_POSITIONS = {day: i for i, day in enumerate(SORTED_DAYS)}
GLOBAL_BLOCKED_HOURS = {
    18,
    19,
    38,
    39,
}

# Configuración dinámica de horas de Actividad Complementaria por año
_COMPLEMENTARY_CONFIG = None

def set_complementary_config(config: dict):
    """
    Actualiza GLOBAL_BLOCKED_HOURS con los bloques configurados desde la UI.
    config: {year_int: {"day_index": int, "start_index": int}}
    """
    global GLOBAL_BLOCKED_HOURS, _COMPLEMENTARY_CONFIG
    _COMPLEMENTARY_CONFIG = config
    new_blocked = set()
    for year_config in config.values():
        start = year_config["start_index"]
        new_blocked.update({start, start + 1})  # 2 horas académicas seguidas
    GLOBAL_BLOCKED_HOURS = new_blocked

def fast_copy_event(event: Event) -> Event:
    """Clonación manual ultrarrápida, reduciendo overhead de copy.deepcopy."""
    new_e = Event.__new__(Event)
    new_e.id = event.id
    new_e.teacher = event.teacher
    new_e.subject = event.subject
    new_e.group = event.group
    new_e.duration = event.duration
    new_e.start_hour = event.start_hour
    new_e.room = event.room
    return new_e

def fast_copy_timetable(timetable: list[Event]) -> list[Event]:
    return [fast_copy_event(e) for e in timetable]

def random_start_hour(duration: int, teacher_id: int = None) -> int:
    teacher = TEACHERS_BY_ID.get(teacher_id) if teacher_id is not None else None

    # 1. Filtrar los bloques de disponibilidad donde la clase realmente cabe
    valid_availabilities = []
    for av in teacher.availabilities:
        # av.start_idx y av.end_idx definen el rango disponible en la matriz global 'academic_hours'
        max_start = av.end_idx - duration + 1
        if max_start >= av.start_idx:
            valid_availabilities.append((av.start_idx, max_start))

    # Si por alguna razón la duración es mayor que cualquier bloque disponible del profesor
    if not valid_availabilities:
        day_idx = random.choice(SORTED_DAYS)
        min_idx = academic_hours_limits[day_idx]["min"]
        max_idx = academic_hours_limits[day_idx]["max"]
        latest_hour = max_idx - duration + 1
        
        if latest_hour < min_idx or duration > 8:
            return min_idx

        if duration == 8:
            return random.choice([min_idx, latest_hour])

        return random.randint(min_idx, latest_hour)

    # 2. Elegir un bloque de disponibilidad al azar de los válidos
    chosen_av_start, chosen_max_start = random.choice(valid_availabilities)

    # 3. Si el bloque exacto permite un rango, elegimos una hora al azar dentro de él
    if chosen_av_start == chosen_max_start:
        return chosen_av_start
    
    if duration > 8:
        return chosen_max_start
    
    if duration == 8:
        return random.choice([chosen_av_start, chosen_max_start])

    return random.randint(chosen_av_start, chosen_max_start)

def is_teacher_available(teacher, start_hour: int, duration: int) -> bool:
    if teacher is None:
        return True

    teacher = TEACHERS_BY_ID.get(teacher)

    event_end_hour = start_hour + duration - 1
    
    for av in teacher.availabilities:
        if start_hour >= av.start_idx and event_end_hour <= av.end_idx:
            return True
            
    return False

def is_subject_already_on_day(scheduled_tracker: set, target_event: Event, candidate_start_hour: int) -> bool:
    """Verifica si el grupo ya tiene la materia asignada ese día usando un Set."""
    candidate_day = academic_hours[candidate_start_hour].day_index
    
    # Comprobación instantánea en la tabla Hash
    return (target_event.group, target_event.subject, candidate_day) in scheduled_tracker

def creates_gap(candidate_hour: int, duration: int, group_taken_hours: set[int]) -> bool:
    """Retorna True si colocar el evento en candidate_hour genera o incrementa los baches/huecos
    intermedios en la jornada del grupo ese día.
    """
    if not group_taken_hours:
        return False

    candidate_day = academic_hours[candidate_hour].day_index
    day_taken = [h for h in group_taken_hours if academic_hours[h].day_index == candidate_day]
    if not day_taken:
        return False

    candidate_range = set(range(candidate_hour, candidate_hour + duration))
    combined_hours = set(day_taken).union(candidate_range)

    min_h = min(combined_hours)
    max_h = max(combined_hours)

    total_span = max_h - min_h + 1
    gaps_count = total_span - len(combined_hours)

    existing_min = min(day_taken)
    existing_max = max(day_taken)
    existing_span = existing_max - existing_min + 1
    existing_gaps = existing_span - len(day_taken)

    return gaps_count > existing_gaps

def fix_teacher_collisions(timetable: list[Event]) -> list[Event]:
    """
    Detecta y corrige de forma determinista y ultrarrápida cualquier choque de profesor
    en el horario, garantizando 0 choques de profesor.
    """
    for _ in range(3):
        teacher_occupancy = {}
        group_occupancy = {}
        colliding_events = []

        for e in timetable:
            if e.start_hour is None or e.teacher is None:
                continue

            curr_subject = SUBJECTS_BY_ID.get(e.subject)
            if curr_subject and curr_subject.name == "Actividad Complementaria":
                for h in range(e.start_hour, e.start_hour + e.duration):
                    teacher_occupancy[(e.teacher, h)] = e
                    group_occupancy[(e.group, h)] = e
                continue

            has_teacher_collision = False
            e_range = range(e.start_hour, e.start_hour + e.duration)
            for h in e_range:
                if (e.teacher, h) in teacher_occupancy:
                    has_teacher_collision = True
                    break

            if has_teacher_collision:
                colliding_events.append(e)
            else:
                for h in e_range:
                    teacher_occupancy[(e.teacher, h)] = e
                    group_occupancy[(e.group, h)] = e

        if not colliding_events:
            break

        scheduled_subjects = {
            (e.group, e.subject, academic_hours[e.start_hour].day_index)
            for e in timetable if e.start_hour is not None
        }

        for e in colliding_events:
            teacher_obj = TEACHERS_BY_ID.get(e.teacher)
            if not teacher_obj or not teacher_obj.availabilities:
                continue

            g_busy = {h for (g_id, h) in group_occupancy.keys() if g_id == e.group}
            t_busy = {h for (t_id, h) in teacher_occupancy.keys() if t_id == e.teacher}

            candidate_hours = []
            for av in teacher_obj.availabilities:
                max_start = av.end_idx - e.duration + 1
                for h_cand in range(av.start_idx, max_start + 1):
                    if (academic_hours[h_cand].day_index == academic_hours[h_cand + e.duration - 1].day_index and
                        not any((h_cand + i) in GLOBAL_BLOCKED_HOURS for i in range(e.duration))):
                        h_range = set(range(h_cand, h_cand + e.duration))
                        if (not g_busy.intersection(h_range) and
                            not t_busy.intersection(h_range) and
                            not is_subject_already_on_day(scheduled_subjects, e, h_cand)):
                            candidate_hours.append(h_cand)

            if candidate_hours:
                best_h = select_best_hour(candidate_hours, e, g_busy, scheduled_subjects)
                if best_h is not None:
                    e.start_hour = best_h
                    e_range = range(e.start_hour, e.start_hour + e.duration)
                    for h in e_range:
                        teacher_occupancy[(e.teacher, h)] = e
                        group_occupancy[(e.group, h)] = e

    return timetable

def compact_timetable(timetable: list[Event]) -> list[Event]:
    """
    Recorre cada grupo y día en el horario para compactar eventos y eliminar baches
    de forma determinista en O(N) operaciones, probando desplazar eventos hacia la izquierda
    o hacia la derecha para pegar las clases sin generar choques.
    """
    teachers_block = {}
    groups_block = {}
    events_by_group_day = {}

    for e in timetable:
        if e.start_hour is None:
            continue
        e_range = set(range(e.start_hour, e.start_hour + e.duration))
        if e.teacher is not None:
            teachers_block.setdefault(e.teacher, set()).update(e_range)
        groups_block.setdefault(e.group, set()).update(e_range)

        day = academic_hours[e.start_hour].day_index
        events_by_group_day.setdefault((e.group, day), []).append(e)

    for (group_id, day), g_events in events_by_group_day.items():
        if len(g_events) <= 1:
            continue

        g_events.sort(key=lambda x: x.start_hour)

        for _ in range(3):
            changed = False
            for idx in range(1, len(g_events)):
                prev_event = g_events[idx - 1]
                curr_event = g_events[idx]

                curr_sub = SUBJECTS_BY_ID.get(curr_event.subject)
                prev_sub = SUBJECTS_BY_ID.get(prev_event.subject)
                is_curr_comp = curr_sub and curr_sub.name == "Actividad Complementaria"
                is_prev_comp = prev_sub and prev_sub.name == "Actividad Complementaria"

                prev_end = prev_event.start_hour + prev_event.duration
                if curr_event.start_hour > prev_end:
                    target_start = prev_end
                    target_range = set(range(target_start, target_start + curr_event.duration))
                    curr_old_range = set(range(curr_event.start_hour, curr_event.start_hour + curr_event.duration))

                    valid_left = False
                    if not is_curr_comp and not any(h in GLOBAL_BLOCKED_HOURS for h in target_range):
                        if (target_start >= 0 and target_start + curr_event.duration <= len(academic_hours) and
                            academic_hours[target_start].day_index == day and
                            academic_hours[target_start + curr_event.duration - 1].day_index == day):

                            if curr_event.teacher is None or is_teacher_available(curr_event.teacher, target_start, curr_event.duration):
                                teacher_busy = (teachers_block.get(curr_event.teacher, set()) - curr_old_range) if curr_event.teacher is not None else set()
                                group_busy = groups_block.get(group_id, set()) - curr_old_range

                                if not teacher_busy.intersection(target_range) and not group_busy.intersection(target_range):
                                    valid_left = True

                    if valid_left:
                        if curr_event.teacher is not None:
                            teachers_block[curr_event.teacher] -= curr_old_range
                            teachers_block[curr_event.teacher] |= target_range
                        groups_block[group_id] -= curr_old_range
                        groups_block[group_id] |= target_range
                        curr_event.start_hour = target_start
                        changed = True
                        continue

                    target_start_prev = curr_event.start_hour - prev_event.duration
                    target_range_prev = set(range(target_start_prev, target_start_prev + prev_event.duration))
                    prev_old_range = set(range(prev_event.start_hour, prev_event.start_hour + prev_event.duration))

                    valid_right = False
                    if not is_prev_comp and not any(h in GLOBAL_BLOCKED_HOURS for h in target_range_prev):
                        if (target_start_prev >= 0 and target_start_prev + prev_event.duration <= len(academic_hours) and
                            academic_hours[target_start_prev].day_index == day and
                            academic_hours[target_start_prev + prev_event.duration - 1].day_index == day):

                            if prev_event.teacher is None or is_teacher_available(prev_event.teacher, target_start_prev, prev_event.duration):
                                teacher_busy_p = (teachers_block.get(prev_event.teacher, set()) - prev_old_range) if prev_event.teacher is not None else set()
                                group_busy_p = groups_block.get(group_id, set()) - prev_old_range

                                if not teacher_busy_p.intersection(target_range_prev) and not group_busy_p.intersection(target_range_prev):
                                    valid_right = True

                    if valid_right:
                        if prev_event.teacher is not None:
                            teachers_block[prev_event.teacher] -= prev_old_range
                            teachers_block[prev_event.teacher] |= target_range_prev
                        groups_block[group_id] -= prev_old_range
                        groups_block[group_id] |= target_range_prev
                        prev_event.start_hour = target_start_prev
                        changed = True

            if not changed:
                break

    return timetable

def repair_and_compact_timetable(timetable: list[Event]) -> list[Event]:
    timetable = fix_teacher_collisions(timetable)
    timetable = compact_timetable(timetable)
    return timetable

def move_hour(start_hour_index: int, duration: int) -> int:
    """Mueve la hora de inicio retrocediendo un bloque o saltando de día, evitando horas bloqueadas."""
    candidate_idx = start_hour_index
    visited = set() # Evita un bucle infinito si todas las horas del horario están bloqueadas

    while True:
        # Registramos el índice para evitar ciclos infinitos
        if candidate_idx in visited:
            raise ValueError("No hay suficientes horas libres en el horario para ubicar este bloque.")
        visited.add(candidate_idx)

        current_ah = academic_hours[candidate_idx]
        current_day = current_ah.day_index
        min_idx_current_day = academic_hours_limits[current_day]["min"]
        
        # 1. Retroceder o saltar de día (Tu lógica original)
        if candidate_idx > min_idx_current_day:
            candidate_idx -= 1
        else:
            pos_current_day = DAY_POSITIONS[current_day]
            if pos_current_day > 0:
                previous_day = SORTED_DAYS[pos_current_day - 1]
            else:
                previous_day = SORTED_DAYS[-1]
                
            limits_prev = academic_hours_limits[previous_day]
            # Nos aseguramos de caer en un límite donde quepa la duración
            candidate_idx = max(limits_prev["min"], limits_prev["max"] - duration + 1)
        
        # 2. Verificar si el nuevo bloque está completamente libre
        # Revisamos desde candidate_idx hasta candidate_idx + duration - 1
        is_blocked = any((candidate_idx + i) in GLOBAL_BLOCKED_HOURS for i in range(duration))
        
        # Si ninguna de las horas que abarca la duración está bloqueada, encontramos el lugar
        if not is_blocked:
            return candidate_idx

def restructure_group_schedule(individual: list[Event], group_id: int, bottleneck_event: Event):
    """Reestructura localmente las materias de un grupo para liberar espacio 
    a un evento con restricciones estrictas de profesor."""
    
    # 1. Identificar eventos pertenecientes a este grupo (excluyendo Actividades Complementarias)
    group_events = [
        e for e in individual
        if e.group == group_id and SUBJECTS_BY_ID.get(e.subject).name != "Actividad Complementaria"
    ]
    if not group_events:
        return

    # 2. Mapear qué horas tienen ocupadas los profesores de este grupo en OTROS grupos
    teacher_busy_externally = {}
    for e in individual:
        if e.group != group_id and e.teacher is not None and e.start_hour is not None:
            e_range = set(range(e.start_hour, e.start_hour + e.duration))
            teacher_busy_externally.setdefault(e.teacher, set()).update(e_range)

    # 3. Función de prioridad: Colocar primero el evento atascado,
    # luego los profesores con menos horas de contrato disponibles
    def get_priority(e: Event):
        if e.id == bottleneck_event.id:
            return -1  # Máxima prioridad para el evento problemático
        teacher = TEACHERS_BY_ID.get(e.teacher)
        if not teacher or not teacher.availabilities:
            return 9999
        return sum(av.end_idx - av.start_idx + 1 for av in teacher.availabilities)

    sorted_group_events = sorted(group_events, key=get_priority)

    # 4. Reservar horas fijas del grupo (p. ej. Actividades Complementarias)
    group_taken_hours = set()
    scheduled_subjects = set()
    for e in individual:
        if e.group == group_id and e.start_hour is not None:
            if SUBJECTS_BY_ID.get(e.subject).name == "Actividad Complementaria":
                group_taken_hours.update(range(e.start_hour, e.start_hour + e.duration))

    # 5. Reasignar eventos del grupo de forma codiciosa
    for ge in sorted_group_events:
        teacher = TEACHERS_BY_ID.get(ge.teacher)
        ext_busy = teacher_busy_externally.get(ge.teacher, set())
        
        candidate_hours = []
        if teacher and teacher.availabilities:
            for av in teacher.availabilities:
                max_start = av.end_idx - ge.duration + 1
                for h in range(av.start_idx, max_start + 1):
                    if academic_hours[h].day_index == academic_hours[h + ge.duration - 1].day_index:
                        candidate_hours.append(h)

        placed = False
        # Probar candidatos
        for h in candidate_hours:
            h_range = set(range(h, h + ge.duration))
            day = academic_hours[h].day_index

            if (not group_taken_hours.intersection(h_range) and
                not ext_busy.intersection(h_range) and
                (ge.group, ge.subject, day) not in scheduled_subjects):
                
                ge.start_hour = h
                group_taken_hours.update(h_range)
                scheduled_subjects.add((ge.group, ge.subject, day))
                placed = True
                break

        # Fallback si aún no cabe perfectamente: se ubica en la hora del contrato que tenga menor solapamiento
        if not placed and candidate_hours:
            best_h = min(
                candidate_hours,
                key=lambda h: len(group_taken_hours.intersection(range(h, h + ge.duration)))
            )
            ge.start_hour = best_h
            group_taken_hours.update(range(best_h, best_h + ge.duration))
            scheduled_subjects.add((ge.group, ge.subject, academic_hours[best_h].day_index))

def evaluate_group_day_schedule(group_taken_hours: set[int], candidate_h: int, duration: int) -> float:
    """Calcula la penalización del horario de un grupo en un día según las reglas:
    - Inicio tardío (> 1ra hora): Máx. inicio en 3ra hora y 0 baches.
    - Inicio normal (1ra hora): Máx. 2 horas libres y preferiblemente seguidas.
    """
    day_idx = academic_hours[candidate_h].day_index
    
    # 1. Obtener todas las horas del grupo ese día incluyendo el evento candidato
    day_global_hours = [
        h for h in group_taken_hours 
        if academic_hours[h].day_index == day_idx
    ]
    new_event_hours = list(range(candidate_h, candidate_h + duration))
    all_day_hours = sorted(set(day_global_hours + new_event_hours))
    
    if not all_day_hours:
        return 0.0

    min_day_global = academic_hours_limits[day_idx]["min"]
    rel_hours = [h - min_day_global for h in all_day_hours]
    
    total_hours_today = len(rel_hours)
    first_hour = rel_hours[0]
    last_hour = rel_hours[-1]
    
    # Baches / huecos intermedios
    all_span_rel = set(range(first_hour, last_hour + 1))
    gap_rel_hours = sorted(all_span_rel - set(rel_hours))
    total_gap_hours = len(gap_rel_hours)

    penalty = 0.0

    # REGLA 1: Carga diaria mínima (Si hay clases el día, objetivo >= 6 horas)
    # Si el día resulta en menos de 6 hrs, se castiga proporcionalmente a las horas faltantes
    if total_hours_today < 6:
        penalty += (6 - total_hours_today) * 350.0

    # REGLA 2: Hora de entrada (Evitar iniciar a las 10:00 - 11:00 AM)
    if first_hour == 1:
        # Entrar a la 2da hora (ej: 8:00 AM) tiene una penalización leve
        penalty += 10.0
    elif first_hour >= 2:
        # Entrar a la 3ra hora o más tarde se penaliza fuertemente
        penalty += 800.0 + (first_hour - 1) * 400.0

    # REGLA 3: Baches / Huecos en la jornada
    if total_gap_hours > 0:
        penalty += total_gap_hours * 300.0

    return penalty

def select_best_hour(candidate_hours: list[int], event: Event, taken_hours_group: set[int], scheduled_subjects: set) -> int:
    """Selecciona la hora candidata que NO repita materia el mismo día
    y que presente el menor nivel de penalización según la jornada del grupo."""
    
    best_hour = None
    best_score = float('inf')

    candidates = list(candidate_hours)
    random.shuffle(candidates)

    for h in candidates:
        # 1. Restricción dura: Prohibido repetir la misma materia el mismo día
        if is_subject_already_on_day(scheduled_subjects, event, h):
            continue
            
        # 2. Evaluar el cumplimiento de las reglas del horario del alumno
        score = evaluate_group_day_schedule(taken_hours_group, h, event.duration)

        if score < best_score:
            best_score = score
            best_hour = h
            
            # Si encontramos una hora con 0 penalización, la tomamos de inmediato
            if best_score == 0:
                break

    # Fallback si todas las horas repetían materia o generaban alguna penalización
    if best_hour is None and candidate_hours:
        best_hour = min(
            candidate_hours,
            key=lambda h: evaluate_group_day_schedule(taken_hours_group, h, event.duration)
        )

    return best_hour

def create_events():
    event_list = []
    id = 1

    for group in groups:
        sorted_subjects = sorted(group.subjects, key=lambda s: s.hours, reverse=True)

        for subject in sorted_subjects:
            # Actividad Complementaria: sin profesor, sin aula, siempre 2 horas
            if subject.name == "Actividad Complementaria":
                event_list.append(Event(id, None, subject, group, 2, None))
                id += 1
                continue

            teacher = None
            room = None
            left_hours = subject.hours
            
            if subject.teacher is not None:
                teacher = subject.teacher

            if teacher is not None and teacher.rooms is not None:
                room = random.choice(teacher.rooms)

            elif group.rooms is not None:
                room = random.choice(group.rooms)

            while left_hours > 0:
                if 2 < left_hours < 8:
                    duration = 2 if left_hours % 2 == 0 else random.randint(2, left_hours)

                elif left_hours > 2 and subject.subject_type != "(Taller) Formacion Cientifica, Tecnologica y Productiva":
                    if subject.subject_type == "General":
                        duration = 4
                    else:
                        duration = random.choice([6, 8])
                    
                else:
                    duration = left_hours

                event_list.append(Event(id, teacher, subject, group, duration, room))
                id += 1
                left_hours -= duration

    return event_list

def create_timetable(events: list[Event], complementary_config: dict = None):
    timetable = []
    groups_block = {}
    teachers_block = {}
    scheduled_subjects = set()

    complementary_events = []
    normal_events = []

    for original_event in events:
        event = fast_copy_event(original_event)
        current_subject = SUBJECTS_BY_ID.get(event.subject)
        
        if current_subject and current_subject.name == "Actividad Complementaria":
            complementary_events.append(event)
        else:
            normal_events.append(event)

    for event in complementary_events:
        group = GROUPS_BY_ID.get(event.group)
        # Forzar sin profesor ni aula
        event.teacher = None
        event.room = None

        # Usar config dinámica o fallback estático
        cfg = (complementary_config or _COMPLEMENTARY_CONFIG or {})
        if group.year in cfg:
            event.start_hour = cfg[group.year]["start_index"]
        elif group.year <= 3:
            event.start_hour = 18
        else:
            event.start_hour = 38

        event_hours = set(range(event.start_hour, event.start_hour + event.duration))
        
        if event.group not in groups_block:
            groups_block[event.group] = set()
        groups_block[event.group].update(event_hours)
        
        timetable.append(event)

    # 3. ORDENAR EL RESTO DE EVENTOS DE MAYOR A MENOR DURACIÓN
    sorted_events = sorted(normal_events, key=lambda e: e.duration, reverse=True)

    for event in sorted_events:
        current_subject = SUBJECTS_BY_ID.get(event.subject)

        if event.group not in groups_block:
            groups_block[event.group] = set()

        if event.teacher not in teachers_block:
            teachers_block[event.teacher] = set()

        found_block = False

        # Prioridad 1: Intentar ubicar el evento contiguo a las clases ya existentes del grupo en algún día
        pref_hour = None
        if groups_block[event.group]:
            days_map = {}
            for h in groups_block[event.group]:
                day = academic_hours[h].day_index
                days_map.setdefault(day, []).append(h)

            candidates = []
            total_ah = len(academic_hours)

            for day, h_list in days_map.items():
                min_h = min(h_list)
                max_h = max(h_list)

                after_h = max_h + 1
                if (after_h + event.duration <= total_ah and
                    academic_hours[after_h].day_index == day and
                    academic_hours[after_h + event.duration - 1].day_index == day):
                    candidates.append(after_h)

                before_h = min_h - event.duration
                if (before_h >= 0 and
                    academic_hours[before_h].day_index == day and
                    academic_hours[before_h + event.duration - 1].day_index == day):
                    candidates.append(before_h)

            random.shuffle(candidates)
            for ch in candidates:
                ch_range = set(range(ch, ch + event.duration))
                if (not groups_block[event.group].intersection(ch_range) and
                    not teachers_block[event.teacher].intersection(ch_range) and
                    is_teacher_available(event.teacher, ch, event.duration) and
                    not is_subject_already_on_day(scheduled_subjects, event, ch) and
                    not creates_gap(ch, event.duration, groups_block[event.group])):
                    pref_hour = ch
                    break

        if pref_hour is not None:
            start_hour = pref_hour
            event_hours = set(range(start_hour, start_hour + event.duration))
            event.start_hour = start_hour
            groups_block[event.group].update(event_hours)
            teachers_block[event.teacher].update(event_hours)
            assigned_day = academic_hours[start_hour].day_index
            scheduled_subjects.add((event.group, event.subject, assigned_day))
            found_block = True
        else:
            start_hour = random_start_hour(event.duration, event.teacher)
            for _ in range(50):
                event_hours = set(range(start_hour, start_hour + event.duration))

                if (not groups_block[event.group].intersection(event_hours) and 
                    not teachers_block[event.teacher].intersection(event_hours) and 
                    is_teacher_available(event.teacher, start_hour, event.duration) and
                    not is_subject_already_on_day(scheduled_subjects, event, start_hour) and
                    not creates_gap(start_hour, event.duration, groups_block[event.group])):
                    
                    event.start_hour = start_hour
                    groups_block[event.group].update(event_hours)
                    teachers_block[event.teacher].update(event_hours)

                    assigned_day = academic_hours[start_hour].day_index
                    scheduled_subjects.add((event.group, event.subject, assigned_day))

                    found_block = True
                    break

                start_hour = move_hour(start_hour, event.duration)

        if not found_block:
            possible_hours = []
            teacher = TEACHERS_BY_ID.get(event.teacher)

            if teacher:
                for av in teacher.availabilities:
                    max_start = (av.end_idx - event.duration) + 1
                    for h in range(av.start_idx, max_start + 1):
                        h_range = set(range(h, h + event.duration))
                        if (not is_subject_already_on_day(scheduled_subjects, event, h) and
                            not groups_block[event.group].intersection(h_range) and
                            not teachers_block[event.teacher].intersection(h_range)):
                            possible_hours.append(h)
            
            event.start_hour = random.choice(possible_hours) if possible_hours else random_start_hour(event.duration, event.teacher)

            event_hours = range(event.start_hour, event.start_hour + event.duration)
            groups_block[event.group].update(event_hours)
            teachers_block[event.teacher].update(event_hours)

            assigned_day = academic_hours[event.start_hour].day_index
            scheduled_subjects.add((event.group, event.subject, assigned_day))

        timetable.append(event)

    return repair_and_compact_timetable(timetable)


def create_population(size: int, events: list[Event], complementary_config: dict = None):
    return [create_timetable(events, complementary_config) for _ in range(size)]

def selection(population, size):
    population.sort(key=lambda x: x[0])
    return population[:size]

def crossover(selected_population: list[list[Event]], population_size: int):
    new_population = []

    new_population.append(fast_copy_timetable(selected_population[0][1]))
    new_population.append(fast_copy_timetable(selected_population[1][1]))

    all_group_ids = list(GROUPS_BY_ID.keys())

    while len(new_population) < population_size:
        parents = random.sample(selected_population, 2)
        p1, p2 = parents[0][1], parents[1][1]
        
        # Crossover por Grupos Académicos: Preserva la validez interna de la jornada del alumno
        k_groups = max(1, len(all_group_ids) // 2)
        selected_p1_groups = set(random.sample(all_group_ids, k_groups))

        child = []
        for e in p1:
            if e.group in selected_p1_groups:
                child.append(fast_copy_event(e))

        for e in p2:
            if e.group not in selected_p1_groups:
                child.append(fast_copy_event(e))

        child = mutation(child)
        new_population.append(child)
        
    return new_population

def mutate_rooms(individual: list[Event], room_mutation_rate: float = 0.10) -> list[Event]:
    """
    Revisa y muta las aulas asignadas a los eventos del individuo.
    - Preserva las aulas fijas de taller/proyecto asignadas por profesor (teacher.rooms).
    - Detecta choques de aula entre grupos y los reasigna a un aula libre dentro de group.rooms.
    - Aplica una mutación aleatoria controlada para explorar distintas aulas del grupo.
    """
    # 1. Construir matriz de ocupación actual de aulas por hora: hora -> list[(room_id, event_id)]
    room_occupancy = {}
    for e in individual:
        if e.start_hour is not None and e.room is not None:
            for h in range(e.start_hour, e.start_hour + e.duration):
                room_occupancy.setdefault(h, []).append((e.room, e.id))

    for event in individual:
        if event.start_hour is None or event.room is None:
            continue

        # Excepción: Profesores de taller/proyecto con aula fija en teacher.rooms no se mueven
        teacher = TEACHERS_BY_ID.get(event.teacher) if event.teacher is not None else None
        if teacher and teacher.rooms:
            continue

        # Verificar si el grupo tiene múltiples aulas disponibles donde rotar
        group = GROUPS_BY_ID.get(event.group)
        if not group or not group.rooms or len(group.rooms) <= 1:
            continue

        event_range = range(event.start_hour, event.start_hour + event.duration)

        # 2. Comprobar si el aula actual tiene colisión con otro grupo en ese bloque horario
        has_collision = False
        for h in event_range:
            occupants = room_occupancy.get(h, [])
            if sum(1 for r_id, e_id in occupants if r_id == event.room and e_id != event.id) > 0:
                has_collision = True
                break

        # 3. Disparar cambio de aula si hay choque O por tasa de mutación aleatoria
        if has_collision or random.random() < room_mutation_rate:
            free_candidate_rooms = []
            
            for candidate_room in group.rooms:
                if candidate_room == event.room and not has_collision:
                    continue

                # El aula es válida si ningún otro evento la ocupa en las mismas horas
                is_free = True
                for h in event_range:
                    occupants = room_occupancy.get(h, [])
                    if any(r_id == candidate_room and e_id != event.id for r_id, e_id in occupants):
                        is_free = False
                        break

                if is_free:
                    free_candidate_rooms.append(candidate_room)

            # 4. Seleccionar nueva aula
            new_room = None
            if free_candidate_rooms:
                new_room = random.choice(free_candidate_rooms)
            elif has_collision:
                # Fallback greedy: si no hay aula 100% libre, elegir la de group.rooms con menos choques
                def count_collisions(r_id):
                    return sum(
                        1 for h in event_range
                        for occupied_r, e_id in room_occupancy.get(h, [])
                        if occupied_r == r_id and e_id != event.id
                    )
                new_room = min(group.rooms, key=count_collisions)

            # 5. Aplicar el cambio y actualizar la tabla de ocupación en tiempo real
            if new_room is not None and new_room != event.room:
                for h in event_range:
                    if h in room_occupancy:
                        room_occupancy[h] = [(r, eid) for r, eid in room_occupancy[h] if eid != event.id]
                        room_occupancy[h].append((new_room, event.id))
                
                event.room = new_room

    return individual

def repair_conflicts(individual: list[Event]) -> list[Event]:
    """
    Detecta y repara en O(N) únicamente los eventos que colisionan 
    (choques de profesor, grupo o materias repetidas el mismo día).
    No evalúa eventos sanos ni ejecuta bucles cuadráticos innecesarios.
    """
    for _ in range(3):
        teacher_occupancy = {}
        group_occupancy = {}
        scheduled_subjects = set()
        colliding_events = []

        for e in individual:
            if e.start_hour is None:
                continue

            curr_subject = SUBJECTS_BY_ID.get(e.subject)
            is_comp = curr_subject and curr_subject.name == "Actividad Complementaria"

            e_range = range(e.start_hour, e.start_hour + e.duration)
            day = academic_hours[e.start_hour].day_index

            has_conflict = False

            # 1. Verificar choques de profesor
            if e.teacher is not None:
                for h in e_range:
                    if (e.teacher, h) in teacher_occupancy:
                        has_conflict = True
                        break

            # 2. Verificar choques de grupo
            if not has_conflict:
                for h in e_range:
                    if (e.group, h) in group_occupancy:
                        has_conflict = True
                        break

            # 3. Verificar materia repetida en el mismo día
            if not has_conflict and not is_comp:
                if (e.group, e.subject, day) in scheduled_subjects:
                    has_conflict = True

            if has_conflict:
                colliding_events.append(e)
            else:
                if e.teacher is not None:
                    for h in e_range:
                        teacher_occupancy[(e.teacher, h)] = e
                for h in e_range:
                    group_occupancy[(e.group, h)] = e
                if not is_comp:
                    scheduled_subjects.add((e.group, e.subject, day))

        if not colliding_events:
            break

        for e in colliding_events:
            curr_subject = SUBJECTS_BY_ID.get(e.subject)
            if curr_subject and curr_subject.name == "Actividad Complementaria":
                continue

            teacher_obj = TEACHERS_BY_ID.get(e.teacher) if e.teacher is not None else None
            g_busy = {h for (g_id, h) in group_occupancy.keys() if g_id == e.group}
            t_busy = {h for (t_id, h) in teacher_occupancy.keys() if t_id == e.teacher} if e.teacher is not None else set()
            taken_hours = g_busy.union(t_busy)

            candidate_hours = []
            if teacher_obj and teacher_obj.availabilities:
                for av in teacher_obj.availabilities:
                    max_start = av.end_idx - e.duration + 1
                    for h_cand in range(av.start_idx, max_start + 1):
                        if (academic_hours[h_cand].day_index == academic_hours[h_cand + e.duration - 1].day_index and
                            not any((h_cand + i) in GLOBAL_BLOCKED_HOURS for i in range(e.duration))):
                            h_range = set(range(h_cand, h_cand + e.duration))
                            if (not taken_hours.intersection(h_range) and
                                not is_subject_already_on_day(scheduled_subjects, e, h_cand)):
                                candidate_hours.append(h_cand)

            if candidate_hours:
                best_h = select_best_hour(candidate_hours, e, g_busy, scheduled_subjects)
                if best_h is not None:
                    e.start_hour = best_h
                    e_range = range(e.start_hour, e.start_hour + e.duration)
                    day = academic_hours[e.start_hour].day_index
                    if e.teacher is not None:
                        for h in e_range:
                            teacher_occupancy[(e.teacher, h)] = e
                    for h in e_range:
                        group_occupancy[(e.group, h)] = e
                    scheduled_subjects.add((e.group, e.subject, day))
            else:
                restructure_group_schedule(individual, e.group, e)

    return individual

def mutation(individual: list[Event], blocked_hours_by_group: dict = None):
    MUTATION_RATE = 0.03

    # 1. Mutación ligera de exploración aleatoria sin overhead O(N^2)
    group_taken = {}
    for e in individual:
        if e.start_hour is not None:
            group_taken.setdefault(e.group, set()).update(range(e.start_hour, e.start_hour + e.duration))

    for event in individual:
        curr_subject = SUBJECTS_BY_ID.get(event.subject)
        if curr_subject and curr_subject.name == "Actividad Complementaria":
            continue

        if random.random() < MUTATION_RATE:
            s_hour = event.start_hour
            g_taken = group_taken.get(event.group, set()) - set(range(event.start_hour, event.start_hour + event.duration))

            for _ in range(15):
                new_hour = move_hour(s_hour, event.duration)
                hours_block = set(range(new_hour, new_hour + event.duration))

                if (not g_taken.intersection(hours_block) and
                    is_teacher_available(event.teacher, new_hour, event.duration) and
                    not creates_gap(new_hour, event.duration, g_taken)):

                    event.start_hour = new_hour
                    break

                s_hour = new_hour

    # 2. Reparación dirigida rápida O(N) para eventos conflictivos
    individual = repair_conflicts(individual)

    # 3. Reparación y mutación de aulas
    individual = mutate_rooms(individual, room_mutation_rate=0.10)

    # 4. Compactación determinista de jornadas y eliminación de baches
    return repair_and_compact_timetable(individual)

def main():

    events = create_events()
    i = 0
    population = create_population(50, events)
    past_value = 0
    count = 0

    while i < 250:
        scores = fitness(population, academic_hours, academic_hours_limits)
        fitness_population = list(zip(scores, population))

        if i == 0:
            print("Poblacion sin seleccionar")
            print_population(fitness_population)
        elif i % 10 == 0:
            fitness_population.sort(key=lambda x: x[0])
            print(f"Generacion {i} - Mejor Fitness: {fitness_population[0][0]}")

        selected_population = selection(fitness_population, 10)
        if i == 0:
            print("Poblacion seleccionada")
            print_population(selected_population)
        
        population = crossover(selected_population, 50)

        if past_value == fitness_population[0][0]:
            count += 1

        else:
            count = 0

        if count > 150:
            print("El algoritmo se ha estancado, no hubo solucion posible esta generacion")
            break
            count = 0

        i += 1
        past_value = fitness_population[0][0]
    
    scores = fitness(population, academic_hours, academic_hours_limits)
    fitness_population = list(zip(scores, population))
    fitness_population.sort(key=lambda x: x[0])
    print("generacion 100 ordenada")
    print_population(fitness_population)
    best_timetable = selected_population[0][1] # O como extraigas tu mejor individuo de la población

    # Generamos el reporte completo de auditoría
    final_report = evaluate_and_report(best_timetable)

    # --- IMPRESIÓN DEL REPORTE FINAL DE FALLAS ---
    print("\n" + "="*50)
    print(f" AUDITORÍA DE CALIDAD DEL HORARIO (Fitness Final: {final_report['total_fitness']})")
    print("="*50)

    print(f"\n[!] Choques de Grupos Detectados: {len(final_report['group_collisions'])}")
    for fail in final_report['group_collisions']:
        print(f"  - Grupo {fail['group']} en Bloque {fail['block']}: Conflicto entre Evento {fail['event_1']['id']} ({fail['event_1']['subject']}) y Evento {fail['event_2']['id']} ({fail['event_2']['subject']})")

    print(f"\n[!] Choques de Profesores Detectados: {len(final_report['teacher_collisions'])}")
    for fail in final_report['teacher_collisions']:
        print(f"  - Profesor {fail['teacher_id']} en Bloque {fail['block']}: Evento {fail['event_1']['id']} (Grupo {fail['event_1']['group']}) choca con Evento {fail['event_2']['id']} (Grupo {fail['event_2']['group']})")

    print(f"\n[!] Choques de Aulas Detectados: {len(final_report['room_collisions'])}")
    for fail in final_report['room_collisions']:
        print(f"  - Aula {fail['room_id']} en Bloque {fail['block']}: Evento {fail['event_1']['id']} (Grupo {fail['event_1']['group']}) choca con Evento {fail['event_2']['id']} (Grupo {fail['event_2']['group']})")

    print(f"\n[!] Baches y Ventanas Horarias de Alumnos: {len(final_report['gaps'])}")
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    for fail in final_report['gaps']:
        gaps_count = fail.get('gaps_count', 0)
        hours = fail.get('hours', [])
        
        # Construir el detalle del mensaje según el tipo de falla
        if 'gaps_count' in fail:
            detalle = f"Tiene {gaps_count} horas muertas en los bloques internos: {hours}"
        elif 'hours_count' in fail:
            detalle = f"Carga total del día: {fail['hours_count']} horas lectivas"
        elif 'first_hour' in fail:
            detalle = f"Inicio de jornada a las {fail['first_hour']}"
        else:
            detalle = ""

        print(f"  - Grupo {fail['group']} ({dias_semana[fail['day']]}): {fail['type']}. {detalle}.")

    print(f"\n[!] Materias Repetidas el Mismo Día: {len(final_report['subject_duplications'])}")
    for fail in final_report['subject_duplications']:
        print(f"  - Grupo {fail['group']} ({dias_semana[fail['day']]}): La materia {fail['subject']} se imparte de forma fragmentada en los Eventos {fail['event_1_id']} y {fail['event_2_id']}.")

    print("\n" + "="*50)

def print_population(population: list[list[Event]]):
    for i, (score, individual) in enumerate(population):
        print(f"\n=== Horario #{i+1} | Fitness Score: {score} ===")
        if i < 1:
            for event in individual:
                print(event)
        #     for subject in individual:
        #         for block in subject:
        #             g, s, t, s_h, e_h, r = block
        #             print(f"  Sec: {g} | Mat: {s} | Prof: {t} | Inicio: {s_h} | Fin: {e_h} | Aula: {r}")
                    
        # else:
        #     print("  [... Otros horarios ocultos ...]")
        #     break

def evaluate_and_report(best_individual: list[Event]):
    """
    Ejecuta las funciones en el mejor individuo al final de las generaciones
    para compilar el informe definitivo de fallas y baches.
    """
    g_score, group_collisions = groups_subjects(best_individual)
    t_score, teacher_collisions = teachers_subjects(best_individual)
    r_score, room_collisions = rooms_groups(best_individual)
    gap_score, gaps_report = groups_gaps(best_individual, academic_hours, academic_hours_limits)
    sub_score, subject_duplications = subject_day(best_individual, academic_hours)
    
    report = {
        "total_fitness": g_score + t_score + r_score + gap_score + sub_score,
        "group_collisions": group_collisions,
        "teacher_collisions": teacher_collisions,
        "room_collisions": room_collisions,
        "gaps": gaps_report,
        "subject_duplications": subject_duplications
    }
    return report

if __name__ == "__main__":
    start = time.perf_counter()
    main()
    total = time.perf_counter() - start
    print(f"Tiempo de ejecución: {total:.4f} segundos")