from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from src.database.connection import Base

# 1. Modelo de Menciones
class MencionModel(Base):
    __tablename__ = "menciones"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)

# 2. Modelo de Cursos
class CursoModel(Base):
    __tablename__ = "cursos"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    seccion = Column(String(50), nullable=False)
    year = Column(String(50), nullable=False)
    mencion_id = Column(Integer, ForeignKey("menciones.id", ondelete="SET NULL"), nullable=True)

# 3. Modelo de Asignaturas
class AsignaturaModel(Base):
    __tablename__ = "asignaturas"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(100), nullable=False)

# 4. Modelo de Profesores
class ProfesorModel(Base):
    __tablename__ = "profesores"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    apellido = Column(String(255), nullable=False)
    telefono = Column(String(50), nullable=True)
    correo = Column(String(255), unique=True, nullable=True)
    estado = Column(Boolean, default=True)

# 5. Modelo de Sesiones
class SesionModel(Base):
    __tablename__ = "sesiones"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dia = Column(String(50), nullable=False)
    hora_inicio = Column(String(50), nullable=False)
    hora_fin = Column(String(50), nullable=False)

# 6. Modelo de Salón
class SalonModel(Base):
    __tablename__ = "salon"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)

# 7. Relación Sesiones - Profesores (sesiones_profesores)
class SesionProfesorModel(Base):
    __tablename__ = "sesiones_profesores"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sesion_id = Column(Integer, ForeignKey("sesiones.id", ondelete="CASCADE"), nullable=False)
    profesor_id = Column(Integer, ForeignKey("profesores.id", ondelete="CASCADE"), nullable=False)

# 8. Relación Curso - Asignatura (curso_asignatura)
class CursoAsignaturaModel(Base):
    __tablename__ = "curso_asignatura"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    curso_id = Column(Integer, ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False)
    asignatura_id = Column(Integer, ForeignKey("asignaturas.id", ondelete="CASCADE"), nullable=False)
    horas_semanales = Column(Integer, nullable=False)

# 9. Relación Profesor - Asignaturas (profesor_asignaturas)
class ProfesorAsignaturaModel(Base):
    __tablename__ = "profesor_asignaturas"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    profesor_id = Column(Integer, ForeignKey("profesores.id", ondelete="CASCADE"), nullable=False)
    curso_asignatura_id = Column(Integer, ForeignKey("curso_asignatura.id", ondelete="CASCADE"), nullable=False)
