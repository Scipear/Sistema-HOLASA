# Sistema HOLASA (Horarios de La Salle)

##  Requerimientos Previos

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

## 💾 Inicialización de la base de datos

### 1. Creación de la base de datos
```bash
python src/database/init_db.py
```

**Si tienes problemas también puedes intentar con el siguiente comando**

```bash
python -m src.database.init_db
```

### 2. Ejecucion de los seeders
```bash
python src/database/seeders.py
```

**Si tienes problemas también puedes intentar con el siguiente comando**

```bash
python -m src.database.seeders
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

---

## 🤖 Ejecución del algoritmo generador de horarios

```bash
python src/engine/genetics.py
```

**O si tienes problemas también puedes intentar con el siguiente comando**

```bash
python -m src.engine.genetics
```

---

## 📄 Exportación de horarios a PDF

Módulo independiente (`src/export/`) que genera un PDF por año de curso. 

**Demo rápida** (genera un horario aleatorio al vuelo):

```bash
python -m src.export.demo --output-dir data/export
```

**Con el algoritmo genético** (exporta el mejor horario del motor):

```bash
python -m src.export.demo --genetics --generations 2000 --output-dir data/export
```

**Nota:** usa `python -m src.export.demo`, no `python src/export/demo.py`.

Los PDFs se guardan en la carpeta indicada con el nombre
`Horario_<año_escolar>_<año_curso>.pdf` (uno por año, una página por curso).
