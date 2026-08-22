from __future__ import annotations
from src.engine.classes import Event


def fitness(population: list[list[Event]], academic_hours: list[Academic_Hour], academic_hours_limits: dict):
    results = []
    
    for individual in population:
        # Extraemos solo el score numérico desestimando las listas de fallas con ', _'
        g_score, _ = groups_subjects(individual)
        t_score, _ = teachers_subjects(individual)
        r_score, _ = rooms_groups(individual) # Esta quedó igual que antes
        gap_score, _ = groups_gaps(individual, academic_hours, academic_hours_limits)
        sub_score, _ = subject_day(individual, academic_hours)
        
        total_score = g_score + t_score + r_score + gap_score + sub_score
        results.append(total_score)

    return results
        

def groups_subjects(individual: list[Event]):
    score = 0
    groups_occupation = {}
    collisions = []

    for event in individual:
        if event.start_hour is None:
            continue

        for block in range(event.start_hour, event.start_hour + event.duration):
            key = (event.group, block)

            if key in groups_occupation:
                existing_event = groups_occupation[key]
                score += 1250
                collisions.append({
                    "group": event.group,
                    "block": block,
                    "event_1": {"id": existing_event.id, "subject": existing_event.subject},
                    "event_2": {"id": event.id, "subject": event.subject}
                })
            else:
                groups_occupation[key] = event
    
    return score, collisions

def teachers_subjects(individual: list[Event]):
    score = 0
    teachers_occupation = {}
    collisions = [] 
    # Conjunto para rastrear choques conceptuales únicos ya penalizados
    # Guardará tuplas de (teacher_id, min_event_id, max_event_id)
    penalized_pairs = set()

    for event in individual:
        if event.start_hour is None or event.teacher is None:
            continue

        for block in range(event.start_hour, event.start_hour + event.duration):
            key = (event.teacher, block)

            if key in teachers_occupation:
                existing_event = teachers_occupation[key]
                
                # Identificadores ordenados para evitar contar (A, B) y (B, A) como diferentes
                event_pair = (event.teacher, min(existing_event.id, event.id), max(existing_event.id, event.id))
                
                # Solo sumamos al score de fitness si es la primera vez que detectamos este choque de eventos
                if event_pair not in penalized_pairs:
                    score += 2000
                    penalized_pairs.add(event_pair)
                
                    # Opcional: El reporte detallado puede seguir mostrando todos los bloques 
                    # o puedes filtrarlo aquí para que solo guarde una colisión conceptual.
                    # Mantenerlo aquí registrará cada bloque; si prefieres un reporte compacto, 
                    # puedes meter este append dentro del 'if event_pair not in penalized_pairs:'
                    collisions.append({
                        "teacher_id": event.teacher,
                        "block": block,
                        "event_1": {
                            "id": existing_event.id,
                            "subject": existing_event.subject,
                            "group": existing_event.group
                        },
                        "event_2": {
                            "id": event.id,
                            "subject": event.subject,
                            "group": event.group
                        }
                    })
            else:
                teachers_occupation[key] = event
    
    return score, collisions

def rooms_groups(individual: list[Event]):
    score = 0
    rooms_occupation = {}
    collisions = []

    for event in individual:
        if event.start_hour is None:
            continue
        
        for block in range(event.start_hour, event.start_hour + event.duration):
            if event.room is not None:
                key = (event.room, block)

                if key in rooms_occupation:
                    existing_event = rooms_occupation[key]
                    score += 0
                    collisions.append({
                        "room_id": event.room,
                        "block": block,
                        "event_1": {
                            "id": existing_event.id,
                            "subject": existing_event.subject,
                            "group": existing_event.group
                        },
                        "event_2": {
                            "id": event.id,
                            "subject": event.subject,
                            "group": event.group
                        }
                    })
                else:
                    rooms_occupation[key] = event
    
    return score, collisions

def groups_gaps(individual: list[Event], academic_hours: list[Academic_Hour], academic_hours_limits: dict):
    score = 0
    timetable_map = {}
    gaps_report = []

    # 1. Mapear bloques ocupados por cada grupo y día
    for event in individual:
        if event.start_hour is None:
            continue

        for block in range(event.start_hour, event.start_hour + event.duration):
            ah = academic_hours[block]
            day = ah.day_index
            
            if event.group not in timetable_map:
                timetable_map[event.group] = {}
                
            if day not in timetable_map[event.group]:
                timetable_map[event.group][day] = set()
                
            timetable_map[event.group][day].add(block)

    # 2. Evaluar reglas por grupo y día activo
    for group, days in timetable_map.items():
        for day, occupied_hours in days.items():
            if not occupied_hours:
                continue
            
            min_day_block = academic_hours_limits[day]["min"]
            first_block = min(occupied_hours)
            last_block = max(occupied_hours)
            
            total_hours = len(occupied_hours)
            first_relative_hour = first_block - min_day_block  # 0 = 1ra hora, 1 = 2da hora, 2 = 3ra hora (>= 10:00 AM)

            # --- A. DETECCIÓN Y PENALIZACIÓN DE HUECOS / BACHES ---
            gaps_count = 0
            specific_hours = []

            for block in range(first_block, last_block + 1):
                if block not in occupied_hours:
                    gaps_count += 1
                    specific_hours.append(academic_hours[block].start_hour)
            
            if gaps_count > 0:
                gap_penalty = gaps_count * 400
                score += gap_penalty
                gaps_report.append({
                    "group": group,
                    "day": day,
                    "type": "Huecos intermedios en la jornada",
                    "gaps_count": gaps_count,
                    "hours": specific_hours,
                    "penalty": gap_penalty
                })

            # --- B. PENALIZACIÓN POR DÍA CORTO (< 6 horas lectivas) ---
            if total_hours < 6:
                short_day_penalty = (6 - total_hours) * 400
                score += short_day_penalty
                gaps_report.append({
                    "group": group,
                    "day": day,
                    "type": f"Día corto ({total_hours} hrs lectivas, mínimo 6)",
                    "hours_count": total_hours,
                    "penalty": short_day_penalty
                })

            # --- C. PENALIZACIÓN POR ENTRADA TARDÍA (>= 3ra hora relativa / ~10:00 AM) ---
            if first_relative_hour > 2:
                late_penalty = (first_relative_hour - 1) * 400
                score += late_penalty
                gaps_report.append({
                    "group": group,
                    "day": day,
                    "type": f"Entrada tardía (Inicia en hora relativa {first_relative_hour + 1})",
                    "first_hour": academic_hours[first_block].start_hour,
                    "penalty": late_penalty
                })

    return score, gaps_report

def subject_day(individual: list[Event], academic_hours: list[Academic_Hour]):
    score = 0
    group_day_subjects = {}
    subject_duplications = []

    for event in individual:
        if event.start_hour is None:
            continue
        
        day = academic_hours[event.start_hour].day_index
        
        if event.group not in group_day_subjects:
            group_day_subjects[event.group] = {}
            
        if day not in group_day_subjects[event.group]:
            group_day_subjects[event.group][day] = {}
            
        # Si la materia ya fue registrada este día, guardamos la falla
        if event.subject in group_day_subjects[event.group][day]:
            score += 300
            existing_event_id = group_day_subjects[event.group][day][event.subject]
            subject_duplications.append({
                "group": event.group,
                "day": day,
                "subject": event.subject,
                "event_1_id": existing_event_id,
                "event_2_id": event.id
            })
        else:
            group_day_subjects[event.group][day][event.subject] = event.id

    return score, subject_duplications