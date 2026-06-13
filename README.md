# Sistema HOLASA (Horarios de La Salle)

## 🛠️ Requerimientos Previos

* **Python 3.12.0 o superior**
* **SQLite**

---

## 🚀 Instalación y Configuración

Sigue estos pasos para clonar el repositorio y configurar tu entorno local utilizando un entorno virtual:

### 1. Clonar el Repositorio
Abre tu terminal y ejecuta los siguientes comandos:
```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DE_LA_CARPETA>
```
### 2. Crear el entorno virtual
```bash
python -m venv .venv
```
### 3. Activar el entorno virtual
```bash
.venv\Scripts\Activate.ps1

```
### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. Ejecutar el proyecto
```bash
python main.py
```

---

## 🧪 Tests

### 1. Instalar pytest
```bash
pip install pytest
```

### 2. Ejecutar tests

**Suite completa** (crea → consulta → modifica → elimina):
```bash
pytest tests/ -v
```

**Por archivo** (orden recomendado):
```bash
pytest tests/test_01_creacion.py -v       # crea datos
pytest tests/test_02_consulta.py -v       # lee datos
pytest tests/test_03_actualizacion.py -v  # modifica datos
pytest tests/test_04_eliminacion.py -v    # elimina datos
```

### 3. Resetear la base de datos de tests

Eliminar manualmente el archivo `tests/test_HOLASA.sqlite3`.

Los tests de creación son **idempotentes**: si los datos ya existen,
se saltan automáticamente.
