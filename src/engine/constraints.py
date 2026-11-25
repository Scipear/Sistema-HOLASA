from __future__ import annotations
from src.engine.classes import Event


def fitness(
    population: list[list[Event]],
    academic_hours: list[Academic_Hour] = None,
    academic_hours_limits: dict = None,
    groups_by_id: dict = None,
    subjects_by_id: dict = None,
    teachers_by_id: dict = None
):
    results = []
    
    for individual in population:
        # Extraemos solo el score numérico desestimando las listas de fallas con ', _'
        g_score, _ = groups_subjects(individual)
        t_score, _ = teachers_subjects(individual)
        r_score, _ = rooms_groups(individual)
        gap_score, _ = groups_gaps(individual, academic_hours, academic_hours_limits) if academic_hours and academic_hours_limits else (0, [])
        sub_score, _ = subject_day(individual, academic_hours) if academic_hours else (0, [])
        fri_score, _ = friday_distribution_constraints(individual, academic_hours, academic_hours_limits, groups_by_id, subjects_by_id) if academic_hours and academic_hours_limits else (0, [])
        t_gap_score, _ = teachers_gaps_and_load(individual, academic_hours, academic_hours_limits, teachers_by_id) if academic_hours and academic_hours_limits else (0, [])
        
        total_score = g_score + t_score + r_score + gap_score + sub_score + fri_score + t_gap_score
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
                score += 1800
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
                    score += 500
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
            
            if gaps_count > 1:
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


def friday_distribution_constraints(
    individual: list[Event],
    academic_hours: list[Academic_Hour],
    academic_hours_limits: dict,
    groups_by_id: dict = None,
    subjects_by_id: dict = None
):
    """
    Evalúa las reglas específicas para la distribución horaria de los Viernes:
    1. 1er y 2do año: En lo posible ven clases los viernes como máximo hasta el bloque de 12:10 a 12:50 (rel <= 7).
    2. Talleres los viernes:
       - Para todos los años excepto 4to y 5to, deben finalizar como máximo a las 12:50 (rel <= 7).
       - En las horas de la tarde del viernes (rel >= 8) es preferible cualquier otra clase menos Taller.
       - Para 4to y 5to año, la duración (10h) requiere la jornada completa, pero se fomenta colocarlos otros días si cabe.
    3. Minimizar la cantidad total de secciones que ven Taller los viernes.
    """
    if not academic_hours or not academic_hours_limits:
        return 0, []

    # Localizar el índice del día Viernes
    friday_day_index = next(
        (ah.day_index for ah in academic_hours if ah.day and ah.day.lower().startswith("vier")),
        4
    )
    if friday_day_index not in academic_hours_limits:
        return 0, []

    min_friday_block = academic_hours_limits[friday_day_index]["min"]

    # Fallback para obtener metadatos de grupos y materias si no fueron pasados
    if groups_by_id is None or subjects_by_id is None:
        try:
            from src.engine import genetics
            groups_by_id = groups_by_id or getattr(genetics, 'GROUPS_BY_ID', {})
            subjects_by_id = subjects_by_id or getattr(genetics, 'SUBJECTS_BY_ID', {})
        except Exception:
            groups_by_id = groups_by_id or {}
            subjects_by_id = subjects_by_id or {}

    score = 0
    friday_report = []
    friday_taller_groups = set()

    for event in individual:
        if event.start_hour is None:
            continue

        start_ah = academic_hours[event.start_hour]
        if start_ah.day_index != friday_day_index:
            continue

        grp = groups_by_id.get(event.group)
        grp_year = getattr(grp, 'year', None)

        subj = subjects_by_id.get(event.subject)
        s_type = (getattr(subj, 'subject_type', '') or '').lower()
        s_name = (getattr(subj, 'name', '') or '').lower()
        is_taller = "taller" in s_type or "taller" in s_name

        event_blocks = range(event.start_hour, event.start_hour + event.duration)
        afternoon_blocks = [b for b in event_blocks if (b - min_friday_block) >= 8]  # >= 12:50 PM

        # --- REGLA 1: 1ero y 2do año hasta las 12:50 los viernes ---
        if grp_year in (1, 2) and afternoon_blocks:
            penalty = len(afternoon_blocks) * 600
            score += penalty
            friday_report.append({
                "group": event.group,
                "day": friday_day_index,
                "type": "1er/2do año con clases el viernes después de 12:50",
                "afternoon_hours": [academic_hours[b].start_hour for b in afternoon_blocks],
                "penalty": penalty,
                "event_id": event.id,
                "subject": event.subject
            })

        # --- REGLA 2: Talleres los viernes en la tarde ---
        if is_taller:
            friday_taller_groups.add(event.group)
            
            if afternoon_blocks:
                if grp_year not in (4, 5):
                    # Para 1°, 2°, 3° y 6° año, el taller no debe estar en la tarde de los viernes
                    taller_aft_penalty = len(afternoon_blocks) * 1500
                    score += taller_aft_penalty
                    friday_report.append({
                        "group": event.group,
                        "day": friday_day_index,
                        "type": f"Taller ({getattr(subj, 'name', 'Taller')}) en la tarde del viernes (Año {grp_year} debe terminar máx 12:50)",
                        "afternoon_hours": [academic_hours[b].start_hour for b in afternoon_blocks],
                        "penalty": taller_aft_penalty,
                        "event_id": event.id,
                        "subject": event.subject
                    })
                else:
                    # Para 4to y 5to año es aceptable si su duración es de 10h, penalización suave de preferencia
                    mild_penalty = len(afternoon_blocks) * 150
                    score += mild_penalty

    # --- REGLA 3: Minimizar cantidad de secciones con Taller los viernes ---
    if friday_taller_groups:
        taller_groups_penalty = len(friday_taller_groups) * 450
        score += taller_groups_penalty
        for g_id in friday_taller_groups:
            friday_report.append({
                "group": g_id,
                "day": friday_day_index,
                "type": "Sección con Taller programado el día Viernes",
                "penalty": 450
            })

    return score, friday_report


def teachers_gaps_and_load(
    individual: list[Event],
    academic_hours: list[Academic_Hour],
    academic_hours_limits: dict,
    teachers_by_id: dict = None
):
    """
    Evalúa las reglas de calidad para la jornada de los profesores:
    1. Baches/Huecos intermedios: Minimizar ventanas vacías entre clases del profesor el mismo día.
    2. Límites diarios de carga:
       - No aplica a profesores de únicamente taller/proyecto.
       - Para profesores generales o mixtos, penaliza si dan menos horas que min_daily_hours
         o más horas que max_daily_hours en días activos.
    """
    if not academic_hours or not academic_hours_limits:
        return 0, []

    if teachers_by_id is None:
        try:
            from src.engine import genetics
            teachers_by_id = getattr(genetics, 'TEACHERS_BY_ID', {})
        except Exception:
            teachers_by_id = {}

    score = 0
    teacher_reports = []

    # 1. Mapear horas ocupadas por profesor y día
    teacher_day_map = {}
    for event in individual:
        if event.start_hour is None or event.teacher is None:
            continue

        t_id = event.teacher
        for block in range(event.start_hour, event.start_hour + event.duration):
            day = academic_hours[block].day_index
            teacher_day_map.setdefault(t_id, {}).setdefault(day, set()).add(block)

    # 2. Evaluar baches y límites por profesor y día activo
    for t_id, days in teacher_day_map.items():
        teacher_obj = teachers_by_id.get(t_id) if teachers_by_id else None
        t_name = f"{teacher_obj.name} {teacher_obj.last_name}" if teacher_obj else f"Profesor {t_id}"
        t_type = getattr(teacher_obj, 'teacher_type', 'general')
        min_dh = getattr(teacher_obj, 'min_daily_hours', None)
        max_dh = getattr(teacher_obj, 'max_daily_hours', None)

        for day, occupied_blocks in days.items():
            if not occupied_blocks:
                continue

            first_block = min(occupied_blocks)
            last_block = max(occupied_blocks)
            total_hours = len(occupied_blocks)

            # --- A. Baches / Huecos intermedios en el horario del profesor ---
            gaps_count = 0
            gap_hours = []
            for block in range(first_block, last_block + 1):
                if block not in occupied_blocks:
                    gaps_count += 1
                    gap_hours.append(academic_hours[block].start_hour)

            if gaps_count > 2:
                gap_penalty = gaps_count * 350
                score += gap_penalty
                teacher_reports.append({
                    "teacher_id": t_id,
                    "teacher_name": t_name,
                    "day": day,
                    "type": "Huecos intermedios en la jornada del profesor",
                    "gaps_count": gaps_count,
                    "hours": gap_hours,
                    "penalty": gap_penalty
                })

            # --- B. Límites de carga diaria (No aplica a taller_proyecto puro) ---
            if t_type == "general":
                # Día muy corto para el profesor (ej. 1 o 2 horas cuando su mínimo es 6)
                if min_dh is not None and min_dh > 0 and total_hours < min_dh:
                    short_penalty = (min_dh - total_hours) * 300
                    score += short_penalty
                    teacher_reports.append({
                        "teacher_id": t_id,
                        "teacher_name": t_name,
                        "day": day,
                        "type": f"Jornada muy corta ({total_hours} hrs lectivas, mínimo esperado {min_dh})",
                        "hours_count": total_hours,
                        "min_expected": min_dh,
                        "penalty": short_penalty
                    })

                # Día sobrecargado para el profesor (ej. 10 horas cuando su máximo es 8)
                if max_dh is not None and max_dh > 0 and total_hours > max_dh:
                    excess_penalty = (total_hours - max_dh) * 300
                    score += excess_penalty
                    teacher_reports.append({
                        "teacher_id": t_id,
                        "teacher_name": t_name,
                        "day": day,
                        "type": f"Jornada sobrecargada ({total_hours} hrs lectivas, máximo permitido {max_dh})",
                        "hours_count": total_hours,
                        "max_expected": max_dh,
                        "penalty": excess_penalty
                    })

    return score, teacher_reports
