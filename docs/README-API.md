# UNIHealth API – Guía técnica rápida

## Arranque

```powershell
cd "C:\Users\Silvia Subirana\Documents\uniHealth"
.\.venv\Scripts\Activate.ps1
cd backend
..\.venv\Scripts\python.exe manage.py runserver
```

OpenAPI / Swagger / ReDoc:
- Schema JSON: GET http://127.0.0.1:8000/api/schema/
- Swagger UI: GET http://127.0.0.1:8000/api/schema/swagger-ui/
- ReDoc: GET http://127.0.0.1:8000/api/schema/redoc/

Colección Postman y guías:
- `docs/Postman-UNIHealth-Accounts.md` (incluye Accounts, Patients, Medical, Alerts, Scheduling)

## Endpoints por módulo (resumen)

- Auth:
  - POST /api/auth/register | /api/auth/login | /api/auth/refresh | GET /api/auth/me
- Patients:
  - GET/PUT /api/me/profile | GET/POST /api/me/consentimientos
- Medical:
  - GET /api/records | GET /api/records/:paciente_id | POST /api/records
  - POST /api/vitals | GET /api/vitals/:paciente_id
  - POST /api/attachments | GET /api/attachments?propietario_tabla&propietario_id | GET /api/attachments/:id
- Alerts:
  - POST /api/alerts | GET /api/alerts | GET /api/alerts/:id
  - POST /api/alerts/:id/assign | POST /api/alerts/:id/status | POST /api/alerts/:id/event
  - WS: ws://127.0.0.1:8000/ws/alerts
- Scheduling:
  - GET /api/appointments/slots
  - POST /api/appointments | GET /api/appointments?mine=true | PATCH /api/appointments/:id

## Pruebas (pytest)

Instalado: pytest, pytest-django, pytest-cov. Las pruebas usan PostgreSQL (según `config/settings.py`). Durante los tests cada suite crea el esquema/tablas mínimas con SQL, por lo que no dependemos de migraciones; necesitas igualmente una base de datos PostgreSQL accesible.

1) Preparación (una vez)

- Asegúrate de tener PostgreSQL corriendo localmente y una BD creada (por defecto `unihealth`).
- Crea `.env` en la raíz del repo con credenciales (ejemplo mínimo):

```env
DJANGO_SECRET_KEY=dev-secret-please-change
DB_NAME=unihealth
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

2) Activar venv e instalar dependencias

```powershell
cd "C:\Users\Silvia Subirana\Documents\uniHealth"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3) Ejecutar todos los tests (con cobertura)

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest
```

4) Ejecutar por app/archivo/expresión

- Por archivo:
```powershell
..\.venv\Scripts\python.exe -m pytest accounts/tests/test_auth.py
```
- Por palabra clave:
```powershell
..\.venv\Scripts\python.exe -m pytest -k "register or login"
```
- Ver salida detallada (sin -q) y solo fallos primero:
```powershell
..\.venv\Scripts\python.exe -m pytest -x -vv
```

5) Cobertura

- Consola (ya activada por defecto): `--cov=backend --cov-report=term-missing`
- HTML (reporte navegable):
```powershell
..\.venv\Scripts\python.exe -m pytest --cov=backend --cov-report=html
start .\htmlcov\index.html
```

Tests incluidos (por app):
- accounts: register/login/refresh/me
- patients: perfil y consentimientos
- medical: creación de registro y signos vitales
- alerts: flujo crear → asignar → cerrar
- scheduling: creación y conflicto por solapamiento

## Seeds útiles

```powershell
cd backend
..\.venv\Scripts\python.exe manage.py init_app_schema       # roles/usuarios (tablas base)
..\.venv\Scripts\python.exe manage.py seed_medical          # tipos_nota
..\.venv\Scripts\python.exe manage.py seed_alerts           # tipos_alerta + tablas
..\.venv\Scripts\python.exe manage.py seed_scheduling       # tipos_servicio
```


