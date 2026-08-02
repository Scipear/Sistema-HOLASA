import numpy as np
import random
import copy
from src.engine.classes import Teacher, Subject, Academic_Hour, Room, Group, Event, Availability
from src.engine.constraints import fitness, groups_subjects, teachers_subjects, groups_gaps, subject_day
from src.engine.data import Data

data_handler = Data()
data_handler.load_data()
academic_hours_limits = data_handler.academic_hours_limits
academic_hours = data_handler.academic_hours
teachers = data_handler.teachers
groups = data_handler.groups
rooms = data_handler.rooms
subjects = data_handler.subjects

def random_start_hour(duration: int) -> int:
    # Elegimos un día existente
    day_idx = random.choice(list(academic_hours_limits.keys()))
    min_idx = academic_hours_limits[day_idx]["min"]
    max_idx = academic_hours_limits[day_idx]["max"]
    
    # Calculamos la última hora del día en la que la clase cabe con su duración
    latest_hour = max_idx - duration + 1
    
    if latest_hour < min_idx:
        # Si el día entero tiene menos horas que la duración de la materia
        return min_idx
        
    return random.randint(min_idx, latest_hour)

def is_teacher_available(teacher, start_hour: int, duration: int) -> bool:
    teacher = next((t for t in teachers if t.id == teacher), None)

    if teacher is None:
        return False
        
    event_end_hour = start_hour + duration - 1
    
    for av in teacher.availabilities:
        if start_hour >= av.start_idx and event_end_hour <= av.end_idx:
            return True
            
    return False

def move_hour(start_hour_index: int, duration: int) -> int:
    """Mueve la hora de inicio retrocediendo un bloque o saltando de día."""
    current_ah = academic_hours[start_hour_index]
    current_day = current_ah.day_index
    min_idx_current_day = academic_hours_limits[current_day]["min"]
    
    # 1. Si aún podemos retroceder 1 hora DENTRO del mismo día
    if start_hour_index > min_idx_current_day:
        return start_hour_index - 1
        
    # 2. Si llegamos al inicio del día, saltamos al día anterior
    sorted_days = sorted(academic_hours_limits.keys())
    pos_current_day = sorted_days.index(current_day)
    
    if pos_current_day > 0:
        previous_day = sorted_days[pos_current_day - 1]
        max_idx_prev = academic_hours_limits[previous_day]["max"]
        min_idx_prev = academic_hours_limits[previous_day]["min"]
        
        # Posicionamos al final del día anterior asegurando que quepa la duración
        return max(min_idx_prev, max_idx_prev - duration + 1)
    else:
        # Si estamos en el primer día (ej. Lunes), saltamos al último día disponible
        latest_day = sorted_days[-1]
        max_idx_lat = academic_hours_limits[latest_day]["max"]
        min_idx_lat = academic_hours_limits[latest_day]["min"]
        
        return max(min_idx_lat, max_idx_lat - duration + 1)

def create_events():
    event_list = []
    id = 1

    for group in groups:
        sorted_subjects = sorted(group.subjects, key=lambda s: s.hours, reverse=True)

        for subject in sorted_subjects:
            left_hours = subject.hours
            teacher = random.choice(subject.teachers)

            while left_hours > 0:
                if left_hours > 2 and left_hours < 8:
                    if left_hours == 4:
                        duration = 2
                    else:
                        duration = random.randint(2, left_hours)

                elif left_hours == 8:
                    even_hours = [6, 8]
                    duration = random.choice(even_hours)

                else:
                    duration = left_hours

                event_list.append(Event(id, teacher, subject, group, duration))
                id += 1
                left_hours -= duration

    return event_list

def create_timetable(events: list[Event]):
    timetable = []
    groups_block = {}
    teachers_block = {}
    #physic_education = [16, 17, 18]

    for event in events:
        if event.group not in groups_block:
            groups_block[event.group] = set()

        if event.teacher not in teachers_block:
            teachers_block[event.teacher] = set()

        found_block = False
        start_hour = random_start_hour(event.duration)

        for _ in range(100):
            event_hours = range(start_hour, start_hour + event.duration)

            if (not groups_block[event.group].intersection(event_hours) and 
                not teachers_block[event.teacher].intersection(event_hours) and 
                is_teacher_available(event.teacher, start_hour, event.duration)):
                
                event.start_hour = start_hour
                # if event.subject not in physic_education:
                #     event.room = random.choice(rooms).id

                groups_block[event.group].update(event_hours)
                teachers_block[event.teacher].update(event_hours)
                found_block = True
                break

            start_hour = move_hour(start_hour, event.duration)

        if not found_block:
            start_hour = random_start_hour(event.duration)
            for _ in range(100):
                event_hours = range(start_hour, start_hour + event.duration)
                
                if not groups_block[event.group].intersection(event_hours) and is_teacher_available(event.teacher, start_hour, event.duration):
                    event.start_hour = start_hour
                    # if event.subject not in physic_education:
                    #     event.room = random.choice(rooms).id
                    groups_block[event.group].update(event_hours)
                    teachers_block[event.teacher].update(event_hours) 
                    found_block = True
                    break

                start_hour = move_hour(start_hour, event.duration)
            
            if not found_block:
                possible_hours = []
                teacher_obj = next((t for t in teachers if t.id == event.teacher), None)

                if teacher_obj:
                    for av in teacher_obj.availabilities:
                        for h in range(av.start_idx, (av.end_idx - event.duration) + 2):
                            possible_hours.append(h)
                
                if possible_hours:
                    event.start_hour = random.choice(possible_hours)
                else:
                    event.start_hour = random_start_hour(event.duration)

                # if event.subject not in physic_education:
                #     event.room = random.choice(rooms).id

                event_hours = range(event.start_hour, event.start_hour + event.duration)
                groups_block[event.group].update(event_hours)
                teachers_block[event.teacher].update(event_hours)

        timetable.append(event)
    
    return timetable


def create_population(size: int, events: list[Event]):
    population = []

    for i in range(size):
        original_timetable = create_timetable(events)
        timetable_copy = copy.deepcopy(original_timetable)
        population.append(timetable_copy)
    
    return population

def selection(population, size):

    population.sort(key=lambda x: x[0])
    selected_population = population[:size]

    return selected_population

def crossover(selected_population: list[list[Event]], population_size: int):
    new_population = []

    new_population.append(copy.deepcopy(selected_population[0][1]))
    new_population.append(copy.deepcopy(selected_population[1][1]))

    while len(new_population) < population_size:
        parents = random.sample(selected_population, 2)
        p1, p2 = parents[0][1], parents[1][1]
        
        point = random.randint(1, len(p1) - 1)
        child = copy.deepcopy(p1[:point] + p2[point:])
        
        child = mutation(child)
        new_population.append(child)
        
    return new_population

def mutation(individual: list[Event]):
    #physic_education = [16, 17, 18]

    for event in individual:
        if random.random() < 0.02:
            current_subject = next((s for s in subjects if s.id == event.subject), None)
            available_teachers = []
            if current_subject:
                # 1. Encontrar todos los bloques horarios actuales de esta materia para este grupo
                # (Ya que al cambiar de profesor, se le cambiarán TODOS sus bloques asignados)
                current_blocks_of_subject = []
                for e in individual:
                    if e.subject == event.subject and e.group == event.group and e.start_hour is not None:
                        current_blocks_of_subject.append((e.start_hour, e.duration))
                
                # 2. Filtrar profesores candidatos
                for t in current_subject.teachers:
                    if t.id == event.teacher:
                        continue
                    
                    # Verificamos si este profesor está disponible en TODOS los bloques de la materia
                    is_available_for_all = True
                    for start_h, duration in current_blocks_of_subject:
                        if not is_teacher_available(t.id, start_h, duration):
                            is_available_for_all = False
                            break # Con un bloque en el que no pueda, queda descartado
                    
                    if is_available_for_all:
                        available_teachers.append(t)

            # DECISIÓN INTELIGENTE: Si hay profesores alternativos, tiramos una moneda (50/50).
            # Si el profesor es ÚNICO, lo obligamos a ir directamente a MUTAR HORA.
            mutar_profesor = False
            if available_teachers and random.choice([True, False]):
                mutar_profesor = True

            if mutar_profesor:
                # --- MUTAR PROFESOR ---
                new_teacher = random.choice(available_teachers)
                i_subject = event.subject
                i_group = event.group

                for e in individual:
                    if e.group > i_group:
                        break
                    if e.subject == i_subject and e.group == i_group:
                        e.teacher = new_teacher.id
                    
            else:
                # --- MUTAR HORA ---
                taken_hours = set()

                # CORRECCIÓN CRÍTICA: Bloqueamos las horas donde el grupo YA tiene clases
                # Y TAMBIÉN las horas donde este profesor YA está dictando otra clase en el instituto
                for e in individual:
                    if e.id != event.id and e.start_hour is not None:
                        # Si es del mismo grupo O es el mismo profesor, esa hora NO está disponible
                        if e.group == event.group or e.teacher == event.teacher:
                            taken_hours.update(range(e.start_hour, e.start_hour + e.duration))
                
                available_space = False

                # Intentamos buscar una hora aleatoria que no choque con nadie (Grupo o Profesor)
                # Subimos los intentos a 100 para dar más margen de búsqueda limpia
                for _ in range(100):
                    new_hour = random_start_hour(event.duration)
                    hours_block = range(new_hour, new_hour + event.duration)

                    # Si no colisiona con las horas ocupadas globales Y el profesor está disponible en su contrato
                    if not taken_hours.intersection(hours_block) and is_teacher_available(event.teacher, new_hour, event.duration):
                        event.start_hour = new_hour
                        available_space = True
                        break
                
                # Fallback de emergencia si el horario está muy apretado:
                # Lo movemos a cualquier hora donde el profesor esté disponible según contrato 
                # (aunque arriesguemos un choque de grupo que el fitness resolverá)
                if not available_space:
                    valid_hours_for_prof = []
                    teacher_obj = next((t for t in teachers if t.id == event.teacher), None)
                    
                    if teacher_obj:
                        for av in teacher_obj.availabilities:
                            max_start = av.end_idx - event.duration + 1

                            for h in range(av.start_idx, max_start + 1):
                                day_start = academic_hours[h].day_index
                                day_end = academic_hours[h + event.duration - 1].day_index

                                if day_start == day_end:
                                    valid_hours_for_prof.append(h)
                                
                    if valid_hours_for_prof:
                        event.start_hour = random.choice(valid_hours_for_prof)
        # else:
        #     if random.random() < 0.01 and event.subject not in physic_education:
        #         event.room = random.choice(rooms).id
    
    return individual

def main():

    events = create_events()
    i = 0
    population = create_population(50, events)

    while i < 1000:
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
        i += 1
    
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

    print(f"\n[!] Baches y Ventanas Horarias de Alumnos: {len(final_report['gaps'])}")
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    for fail in final_report['gaps']:
        print(f"  - Grupo {fail['group']} ({dias_semana[fail['day']]}): {fail['type']}. Tiene {fail['gaps_count']} horas muertas en los bloques internos: {fail['hours']}.")

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
    gap_score, gaps_report = groups_gaps(best_individual, academic_hours, academic_hours_limits)
    sub_score, subject_duplications = subject_day(best_individual, academic_hours)
    
    report = {
        "total_fitness": g_score + t_score + gap_score + sub_score,
        "group_collisions": group_collisions,
        "teacher_collisions": teacher_collisions,
        "gaps": gaps_report,
        "subject_duplications": subject_duplications
    }
    return report

if __name__ == "__main__":
    main()