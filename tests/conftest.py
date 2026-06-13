"""Configuración de pytest para los tests del sistema HOLASA."""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.connection import Base

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_HOLASA.sqlite3")


@pytest.fixture
def db_session():
    """Provee una sesión de base de datos para cada test.

    Crea las tablas si no existen y conserva los datos en disco
    para que puedan inspeccionarse con rainfrog entre ejecuciones.
    """
    engine = create_engine(f"sqlite:///{TEST_DB_PATH}")
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()
