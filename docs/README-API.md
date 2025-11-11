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

Instalado: pytest, pytest-django.

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest
```

Tests incluidos (por app):
- accounts: login/refresh
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


