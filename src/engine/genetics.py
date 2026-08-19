import numpy as np
import random
import copy
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

def creates_one_hour_gap(candidate_hour: int, duration: int, group_taken_hours: set[int]) -> bool:
    """Retorna True si colocar el evento en candidate_hour genera un bloque libre de exactamente 1 hora

    en el horario del grupo (antes o después del evento).
    """
    total_hours = len(academic_hours)
    candidate_day = academic_hours[candidate_hour].day_index

    # --- 1. REVISAR HUECO ANTES DEL BLOQUE CANDIDATO ---
    # Caso: [Clase] (h-2) -> [LIBRE] (h-1) -> [NUEVA CLASE] (candidate_hour)
    prev_1 = candidate_hour - 1  # Hora libre candidata
    prev_2 = candidate_hour - 2  # Hora de clase previa candidata

    if prev_1 >= 0 and academic_hours[prev_1].day_index == candidate_day:
        # La hora inmediatamente anterior está libre
        if prev_1 not in group_taken_hours:
            if prev_2 >= 0 and academic_hours[prev_2].day_index == candidate_day:
                # Si 2 horas atrás hay clase, prev_1 queda como un hueco aislado de 1 hora
                if prev_2 in group_taken_hours:
                    return True

    # --- 2. REVISAR HUECO DESPUÉS DEL BLOQUE CANDIDATO ---
    # Caso: [NUEVA CLASE] -> [LIBRE] (end_hour + 1) -> [Clase] (end_hour + 2)
    end_hour = candidate_hour + duration - 1
    next_1 = end_hour + 1  # Hora libre candidata
    next_2 = end_hour + 2  # Hora de clase posterior candidata

    if next_1 < total_hours and academic_hours[next_1].day_index == candidate_day:
        # La hora inmediatamente posterior está libre
        if next_1 not in group_taken_hours:
            if next_2 < total_hours and academic_hours[next_2].day_index == candidate_day:
                # Si 2 horas después hay clase, next_1 queda como un hueco aislado de 1 hora
                if next_2 in group_taken_hours:
                    return True

    return False

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

def create_timetable(events: list[Event], blocked_hours_by_group: dict = None):
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
        if group.year <= 3:
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
        start_hour = random_start_hour(event.duration, event.teacher)

        for _ in range(50):
            event_hours = set(range(start_hour, start_hour + event.duration))

            if (not groups_block[event.group].intersection(event_hours) and 
                not teachers_block[event.teacher].intersection(event_hours) and 
                is_teacher_available(event.teacher, start_hour, event.duration) and
                not is_subject_already_on_day(scheduled_subjects, event, start_hour) and
                not creates_one_hour_gap(start_hour, event.duration, groups_block[event.group])):
                
                event.start_hour = start_hour
                groups_block[event.group].update(event_hours)
                teachers_block[event.teacher].update(event_hours)

                assigned_day = academic_hours[start_hour].day_index
                scheduled_subjects.add((event.group, event.subject, assigned_day))

                found_block = True
                break

            start_hour = move_hour(start_hour, event.duration)

        # if not found_block:
        #     start_hour = random_start_hour(event.duration, event.teacher)
        #     for _ in range(100):
        #         event_hours = set(range(start_hour, start_hour + event.duration))
                
        #         if (not groups_block[event.group].intersection(event_hours) and
        #             is_teacher_available(event.teacher, start_hour, event.duration) and
        #             not is_subject_already_on_day(scheduled_subjects, event, start_hour)):

        #             event.start_hour = start_hour
        #             groups_block[event.group].update(event_hours)
        #             teachers_block[event.teacher].update(event_hours) 

        #             assigned_day = academic_hours[start_hour].day_index
        #             scheduled_subjects.add((event.group, event.subject, assigned_day))

        #             found_block = True
        #             break

        #         start_hour = move_hour(start_hour, event.duration)
            
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

            assigned_day = academic_hours[start_hour].day_index
            scheduled_subjects.add((event.group, event.subject, assigned_day))

        timetable.append(event)

    return timetable


def create_population(size: int, events: list[Event]):
    return [create_timetable(events) for _ in range(size)]

def selection(population, size):
    population.sort(key=lambda x: x[0])
    return population[:size]

def crossover(selected_population: list[list[Event]], population_size: int):
    new_population = []

    new_population.append(fast_copy_timetable(selected_population[0][1]))
    new_population.append(fast_copy_timetable(selected_population[1][1]))

    while len(new_population) < population_size:
        parents = random.sample(selected_population, 2)
        p1, p2 = parents[0][1], parents[1][1]
        
        point = random.randint(1, len(p1) - 1)
        child = [fast_copy_event(e) for e in p1[:point]] + [fast_copy_event(e) for e in p2[point:]]
        
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

def mutation(individual: list[Event], blocked_hours_by_group: dict = None):
    MUTATION_RATE = 0.02
    REPAIR_RATE = 0.75

    for event in individual:
        current_subject = SUBJECTS_BY_ID.get(event.subject)

        if current_subject.name == "Actividad Complementaria":
            continue

        rand_val = random.random()

        if rand_val < (MUTATION_RATE + REPAIR_RATE):
            taken_hours = set()
            scheduled_subjects = set()

            for e in individual:
                if e.id != event.id and e.start_hour is not None:
                    if e.group == event.group or (event.teacher is not None and e.teacher == event.teacher):
                        taken_hours.update(range(e.start_hour, e.start_hour + e.duration))
                    
                    day = academic_hours[e.start_hour].day_index
                    scheduled_subjects.add((e.group, e.subject, day))
            
            # --- MUTAR HORA ---
            if rand_val < MUTATION_RATE:
                s_hour = event.start_hour

                group_taken_hours = {
                    h for e in individual
                    if e.id != event.id and e.start_hour is not None and e.group == event.group
                    for h in range(e.start_hour, e.start_hour + e.duration)
                }

                for _ in range(50):
                    new_hour = move_hour(s_hour, event.duration)
                    hours_block = set(range(new_hour, new_hour + event.duration))

                    if (not taken_hours.intersection(hours_block) and
                        is_teacher_available(event.teacher, new_hour, event.duration) and
                        not is_subject_already_on_day(scheduled_subjects, event, new_hour) and
                        not creates_one_hour_gap(new_hour, event.duration, group_taken_hours)):

                        event.start_hour = new_hour
                        break
                    
                    s_hour = new_hour
            
            elif event.teacher is not None:
                current_block = set(range(event.start_hour, event.start_hour + event.duration))

                if taken_hours.intersection(current_block) or is_subject_already_on_day(scheduled_subjects, event, event.start_hour):
                    valid_hours_for_prof = []
                    teacher = TEACHERS_BY_ID.get(event.teacher)

                    if teacher:
                        for av in teacher.availabilities:
                            max_start = av.end_idx - event.duration + 1

                            for h in range(av.start_idx, max_start + 1):
                                h_range = set(range(h, h + event.duration))

                                if (academic_hours[h].day_index == academic_hours[h + event.duration - 1].day_index and
                                    not is_subject_already_on_day(scheduled_subjects, event, h) and
                                    not taken_hours.intersection(h_range)):
                                    valid_hours_for_prof.append(h)
                                
                    if valid_hours_for_prof:
                        chosen_h = select_best_hour(valid_hours_for_prof, event, taken_hours, scheduled_subjects)

                        if chosen_h is not None:
                            event.start_hour = chosen_h
                    
                    else:
                        restructure_group_schedule(individual, event.group, event)

    # --- REPARACIÓN Y MUTACIÓN DE AULAS ---
    individual = mutate_rooms(individual, room_mutation_rate=0.10)

    return individual

def main():

    events = create_events()
    i = 0
    population = create_population(50, events)
    past_value = 0
    count = 0

    while i < 500:
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

def print_collisions_report(collisions: list):
    if not collisions:
        print("\n" + "="*50)
        print(" 🎉 ¡EXCELENTE! No se encontraron choques de profesores. 🎉")
        print("="*50 + "\n")
        return

    days_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

    print("\n" + "!"*60)
    print(f"       REPORTE DETALLADO DE CHOQUES ({len(collisions)} detectados)")
    print("!"*60)

    # Agrupamos o iteramos para mostrarlo visualmente limpio
    for i, c in enumerate(collisions, 1):
        # Calcular el día (0 a 4) y la hora dentro de ese día (1 a 10)
        day_index = (c["block"] - 1) // 10
        hour_in_day = ((c["block"] - 1) % 10) + 1
        
        day_name = days_names[day_index] if day_index < len(days_names) else f"Día {day_index}"

        print(f"\n💥 CHOQUE #{i} | Profesor ID: {c['teacher_id']} | {day_name} - Hora Bloque: {hour_in_day} (Global: {c['block']})")
        print(f"  └─ Clase A: Evento ID {c['event_1']['id']} | Materia ID: {c['event_1']['subject']} | Grupo ID: {c['event_1']['group']}")
        print(f"  └─ Clase B: Evento ID {c['event_2']['id']} | Materia ID: {c['event_2']['subject']} | Grupo ID: {c['event_2']['group']}")
    
    print("\n" + "="*60 + "\n")

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
    main()