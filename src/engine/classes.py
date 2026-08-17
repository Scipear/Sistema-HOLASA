from __future__ import annotations

class Teacher():
    def __init__(self, id: int, name: str, last_name: str, availabilities: list[Academic_Hour], rooms: list[Room] = None):
        self.id = id
        self.name = name
        self.last_name = last_name
        self.availabilities = availabilities
        self.rooms = rooms

class Subject():
    def __init__(self, id: int, name: str, subject_type: str, hours: int, teacher: Teacher):
        self.id = id
        self.name = name
        self.hours = hours
        self.subject_type = subject_type
        self.teacher = teacher

class Academic_Hour:
    def __init__(self, db_id: int, index: int, day: str, day_index: int, start_hour: str, end_hour: str):
        self.db_id = db_id #Indice real en la base de datos
        self.index = index #Indice virtual o ficticio para llevar un conteo continuo y tener control de las horas
        self.day = day #Dia de la semana
        self.day_index = day_index #Indice del dia de la semana
        self.start_hour = start_hour #Hora de inicio
        self.end_hour = end_hour #Hora de fin

class Availability:
    def __init__(self, start_idx: int, end_idx: int):
        self.start_idx = start_idx #Indice virtual inicial
        self.end_idx = end_idx #Indice virtual final

class Room():
    def __init__(self, id:int, name: str):
        self.id = id
        self.name = name

class Group():
    def __init__(self, id: int, year: int, name: str, subjects: list[Subject], rooms: list[Room] = None):
        self.id = id
        self.year = year
        self.name = name
        self.subjects = subjects
        self.rooms = rooms
        
class Event():
    def __init__(self, id: int, teacher: Teacher, subject: Subject, group: Group, duration: int, room: Room = None):
        self.id = id
        self.group = group.id
        self.teacher = teacher.id if teacher is not None else teacher
        self.subject = subject.id
        self.duration = duration
        self.start_hour = None
        self.room = room
    
    @property
    def room(self):
        return self._room

    @room.setter
    def room(self, value):
        # Si le asignan un objeto Room, extrae automáticamente el .id
        if hasattr(value, 'id'):
            self._room = value.id
        else:
            self._room = value
    
    def __repr__(self):
        return f"(g {self.group} | s {self.subject} | t {self.teacher} | d {self.duration}h | s_h {self.start_hour} | e_h {(self.start_hour + self.duration) - 1} | r {self.room})"