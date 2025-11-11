# UNIHealth – Guía Postman (Registro, Login, Me, Refresh)

Esta guía explica cómo correr el backend y probar “registro y autenticación JWT” solo desde Postman, con ejemplos de requests y sin insertar datos manualmente fuera de Postman.

## 0) Levantar el backend

1) Activar entorno virtual:

```bash
.\.venv\Scripts\Activate.ps1
```

2) Ejecutar servidor:

```bash
cd backend
..\.venv\Scripts\python.exe manage.py runserver
```

3) Verificar salud:

```http
GET http://127.0.0.1:8000/api/health/
```

Deberías ver: `{ "status": "ok" }`

Si al registrar ves “no existe la relación «app.usuarios»”, ejecuta una sola vez:

```bash
cd backend
..\.venv\Scripts\python.exe manage.py init_app_schema
```

## 1) Variables de Postman (recomendado)

Crea un Environment en Postman con:

- baseUrl = `http://127.0.0.1:8000`
- email = `usuario.demo@unihealth.test`
- password = `UniHealth#2025`
- role = `user`
- access_token = (vacío, se completará solo)
- refresh_token = (vacío, se completará solo)

## 2) Registro – POST /api/auth/register

Crea un usuario en la base usando el rol elegido (por defecto `user`). La contraseña se guarda hasheada de forma segura.

Request:

```http
POST {{baseUrl}}/api/auth/register
Content-Type: application/json

{
  "email": "{{email}}",
  "password": "{{password}}",
  "role": "{{role}}"
}
```

Respuesta esperada (201 Created):

```json
{
  "access_token": "<JWT>",
  "refresh_token": "<JWT>",
  "token_type": "Bearer",
  "user": {
    "id": 1,
    "email": "usuario.demo@unihealth.test",
    "rol": "user",
    "activo": true
  }
}
```

En la pestaña “Tests” de Postman añade este script para guardar tokens automáticamente:

```javascript
const json = pm.response.json();
pm.environment.set("access_token", json.access_token);
pm.environment.set("refresh_token", json.refresh_token);
```

Notas:
- Si recibes “Email ya registrado”, cambia la variable `email` y vuelve a intentar.
- Si recibes “Rol inválido”, usa `role = user` o uno existente en tu tabla `app.roles`.

## 3) Login – POST /api/auth/login

Autentica con el usuario registrado y devuelve un nuevo par de tokens.

Request:

```http
POST {{baseUrl}}/api/auth/login
Content-Type: application/json

{
  "email": "{{email}}",
  "password": "{{password}}"
}
```

Respuesta 200 OK (igual formato que en registro). Añade el mismo script de Tests para refrescar tokens en el Environment.

## 4) Me – GET /api/auth/me

Devuelve información del usuario autenticado (requiere `Authorization: Bearer` con `access_token`).

Request:

```http
GET {{baseUrl}}/api/auth/me
Authorization: Bearer {{access_token}}
```

Respuesta 200 OK (ejemplo):

```json
{
  "id": 1,
  "email": "usuario.demo@unihealth.test",
  "rol": "user",
  "activo": true,
  "creado_en": "2025-01-01T00:00:00Z",
  "actualizado_en": "2025-01-01T00:00:00Z",
  "ultimo_login": "2025-01-01T00:00:00Z"
}
```

Si falta el header o el token caducó, verás 403/401.

## 5) Refresh – POST /api/auth/refresh

Solicita un nuevo `access_token` usando el `refresh_token` actual.

Request:

```http
POST {{baseUrl}}/api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "{{refresh_token}}"
}
```

Respuesta 200 OK:

```json
{
  "access_token": "<nuevo_access_token>",
  "token_type": "Bearer"
}
```

En Tests:

```javascript
const json = pm.response.json();
pm.environment.set("access_token", json.access_token);
```

## 6) Flujo recomendado en Postman (paso a paso)

1) Health → confirmar que responde OK.
2) Register → crear un usuario nuevo y guardar tokens (Tests).
3) Me → verificar que el `access_token` funciona.
4) Login (opcional) → comprobar que devuelve nuevos tokens.
5) Refresh → pedir nuevo `access_token` cuando caduque el actual.

## 7) Problemas comunes

- 400 en Register “Email ya registrado”: cambia `{{email}}` y repite.
- 400 en Register “Rol inválido”: usa `role=user` o un rol existente.
- 401/403 en Me: falta `Authorization` o token expirado → haz Login o Refresh.
- Error de conexión DB: revisa `.env` (DB_HOST, DB_PORT=5433, DB_USER=daswit, DB_PASSWORD) y que Postgres esté arriba.

Listo. Con esto puedes crear usuarios y probar autenticación JWT únicamente desde Postman, sin ejecutar SQL manual ni scripts adicionales.

---

# Patients – Perfil y Consentimientos (GET/PUT /me/profile, GET/POST /me/consentimientos)

Estos endpoints requieren estar autenticado (Bearer `{{access_token}}`).

## A) Perfil – GET /me/profile

Request:

```http
GET {{baseUrl}}/api/me/profile
Authorization: Bearer {{access_token}}
```

Respuestas:
- 200 OK con el perfil si existe
- 404 si aún no tienes perfil

Ejemplo 200:
```json
{
  "usuario": 1,
  "nombres": "Paciente",
  "apellidos": "Demo",
  "fecha_nacimiento": "2000-01-01",
  "sexo": "X",
  "contacto_emergencia": "Contacto",
  "alergias": "Ninguna",
  "antecedentes": "N/A",
  "creado_en": "2025-01-01T00:00:00Z",
  "actualizado_en": "2025-01-01T00:00:00Z"
}
```

## B) Perfil – PUT /me/profile

Request:

```http
PUT {{baseUrl}}/api/me/profile
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "nombres": "Paciente",
  "apellidos": "Demo",
  "fecha_nacimiento": "2000-01-01",
  "sexo": "X",
  "contacto_emergencia": "Contacto",
  "alergias": "Ninguna",
  "antecedentes": "N/A"
}
```

Respuestas:
- 200 OK con el perfil actualizado/creado
- 400 si fallan validaciones (nombres/apellidos obligatorios, fecha no futura, sexo en M/F/X)

## C) Consentimientos – GET /me/consentimientos

Request:

```http
GET {{baseUrl}}/api/me/consentimientos
Authorization: Bearer {{access_token}}
```

Respuesta 200 OK (lista, posiblemente vacía):
```json
[
  {
    "id": 10,
    "version": "v1.0",
    "aceptado_en": "2025-01-01T00:00:00Z",
    "ip": "127.0.0.1"
  }
]
```

## D) Consentimientos – POST /me/consentimientos

Request:

```http
POST {{baseUrl}}/api/me/consentimientos
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "version": "v1.0"
}
```

Respuestas:
- 201 Created con la lista actualizada (ordenada por fecha descendente)
- 400 si falta `version` o excede tamaño

---

# Medical – Historia clínica y signos vitales

Requiere autenticación. Las operaciones de creación/listado por paciente están restringidas a Enfermería (rol `nurse`).

## A) Registros clínicos – GET /records (paciente actual)

```http
GET {{baseUrl}}/api/records
Authorization: Bearer {{access_token}}
```

Devuelve tus registros (si eres `user`). Enfermería usa el endpoint de abajo.

## B) Registros clínicos por paciente – GET /records/:paciente_id (enfermería)

```http
GET {{baseUrl}}/api/records/{{paciente_id}}
Authorization: Bearer {{access_token}}
```

Responde 200 con lista. Requiere rol `nurse`.

## C) Crear registro clínico – POST /records (enfermería)

```http
POST {{baseUrl}}/api/records
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "paciente_id": 1,
  "tipo_nota_codigo": "triaje",
  "nota": "Paciente estable"
}
```

Respuestas:
- 201 Created con el registro (incluye `tipo_nota` anidado)
- 400 si paciente o `tipo_nota_codigo` inválidos
- 403 si no eres `nurse`

Nota: Debe existir un `tipo_nota` activo con ese `codigo` (p.ej. `triaje`).
Si ves “Tipo de nota inválido”, ejecuta una vez:

```bash
cd backend
..\.venv\Scripts\python.exe manage.py seed_medical
```

## D) Crear signos vitales – POST /vitals (enfermería)

```http
POST {{baseUrl}}/api/vitals
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "paciente_id": 1,
  "pas_sistolica": 120,
  "pas_diastolica": 80,
  "spo2": 98
}
```

Respuestas:
- 201 Created con el registro de signos
- 400 si rangos inválidos o paciente inexistente
-$ 403 si no eres `nurse`

## E) Listar signos vitales por paciente – GET /vitals/:paciente_id (enfermería)

```http
GET {{baseUrl}}/api/vitals/{{paciente_id}}
Authorization: Bearer {{access_token}}
```

Respuestas:
- 200 OK con lista ordenada por `tomado_en` descendente
- 403 si no eres `nurse`

## F) Subir adjunto – POST /attachments (enfermería)

Envía multipart/form-data con el archivo y la referencia del recurso dueño (p.ej., un `registro_clinico`). El archivo se guarda en `MEDIA/attachments` y se crea un registro en `app.adjuntos`.

```http
POST {{baseUrl}}/api/attachments
Authorization: Bearer {{access_token}}
Content-Type: multipart/form-data

propietario_tabla = registros_clinicos
propietario_id = 123
file = <selecciona un archivo>
```

Respuestas:
- 201 Created con metadatos del adjunto
- 400 si faltan campos o el `propietario` no existe
- 403 si no eres `nurse`

Qué es propietario_id y de dónde sale
- Es el ID del recurso al que “pertenece” el archivo.
- Si adjuntas a un registro clínico: primero crea el registro con `POST /api/records` y toma el `id` que devuelve. Ese `id` es el `propietario_id` con `propietario_tabla=registros_clinicos`.
- Si adjuntas a una alerta: usa el `id` de la alerta y `propietario_tabla=alertas`.

Listar adjuntos por propietario (enfermería)
```http
GET {{baseUrl}}/api/attachments?propietario_tabla=registros_clinicos&propietario_id=123
Authorization: Bearer {{access_token}}
```

Ver detalle de un adjunto (enfermería)
```http
GET {{baseUrl}}/api/attachments/45
Authorization: Bearer {{access_token}}
```

Descarga del archivo
- En el detalle/lista verás `ruta_storage` (por ejemplo, `/media/attachments/<archivo>`). Si estás en local, ábrela directamente en el navegador: `{{baseUrl}}/media/attachments/<archivo>`.

---

# Alerts – Emergencias en tiempo real

Antes de empezar:
- Asegura tipos de alerta y tablas: 
```bash
cd backend
..\.venv\Scripts\python.exe manage.py seed_alerts
```
- Conecta el WebSocket para ver eventos en vivo (opcional): `ws://127.0.0.1:8000/ws/alerts`

## A) Crear alerta – POST /alerts (rol user)

```http
POST {{baseUrl}}/api/alerts
Authorization: Bearer {{access_token}}   # de un usuario rol user
Content-Type: application/json

{
  "latitud": -17.7833,
  "longitud": -63.1821,
  "descripcion": "Dolor torácico",
  "tipo_alerta_codigo": "cardio",
  "fuente": "app"
}
```

Respuestas:
- 201 Created con datos de la alerta (estado=pendiente)
- Emite evento WS: { "event": "alert_created", "payload": { "id": ... } }

## B) Listar alertas – GET /alerts

```http
GET {{baseUrl}}/api/alerts
Authorization: Bearer {{access_token}}
```

- Rol user: ve sus alertas
- Rol nurse: ve todas

## C) Ver detalle – GET /alerts/:id

```http
GET {{baseUrl}}/api/alerts/{{alert_id}}
Authorization: Bearer {{access_token}}
```

## D) Asignar alerta – POST /alerts/:id/assign (rol nurse)

```http
POST {{baseUrl}}/api/alerts/{{alert_id}}/assign
Authorization: Bearer {{access_token}}     # rol nurse
Content-Type: application/json

{}
```

- Asigna por defecto al enfermero que hace la petición (o pasa `{"asignado_a_id": <id>}`).
- Cambia estado a en_curso si estaba pendiente.
- Emite eventos WS: alert_assigned y cambio de estado.

## E) Cambiar estado – POST /alerts/:id/status (rol nurse)

```http
POST {{baseUrl}}/api/alerts/{{alert_id}}/status
Authorization: Bearer {{access_token}}
Content-Type: application/json

{ "estado": "resuelta" }    # o "en_curso"
```

- Actualiza estado y marca resuelto_en si aplica.
- Emite evento WS: alert_status.

## F) Agregar evento libre – POST /alerts/:id/event (rol nurse)

```http
POST {{baseUrl}}/api/alerts/{{alert_id}}/event
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "tipo": "nota",
  "detalle_json": { "texto": "Paciente trasladado" }
}
```

- 201 Created con { ok: true, event_id }
- Emite evento WS: alert_event

---

# Scheduling – Citas y agenda

Antes de empezar (semillas mínimas):
```bash
cd backend
..\.venv\Scripts\python.exe manage.py seed_scheduling
```

Además, crea agendas para el enfermero (puedes hacerlo con SQL o tu cliente):
```sql
-- Ejemplo: lunes (1) de 09:00 a 12:00
INSERT INTO app.agendas(enfermero_id,dia_semana,hora_inicio,hora_fin) VALUES ({{nurse_id}}, 1, '09:00','12:00');
```

## A) Slots disponibles – GET /appointments/slots

```http
GET {{baseUrl}}/api/appointments/slots?enfermero_id={{nurse_id}}&date=2025-01-10&slot_minutes=30
Authorization: Bearer {{access_token}}
```

Respuestas:
- 200 OK con lista de slots [{ "start": "...", "end": "..." }]

## B) Crear cita – POST /appointments

```http
POST {{baseUrl}}/api/appointments
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "paciente_id": {{patient_id}},
  "enfermero_id": {{nurse_id}},
  "tipo_servicio_codigo": "control",
  "start_ts": "2025-01-10T09:00:00Z",
  "end_ts": "2025-01-10T09:30:00Z",
  "reason": "Chequeo"
}
```

Reglas:
- Usuario (rol user) solo puede crear para sí mismo (estado inicial: solicitada).
- Enfermería (rol nurse) crea confirmadas.
- Valida solapamiento; si choca con otra cita → 409 Conflict.

## C) Listar citas – GET /appointments?mine=true

```http
GET {{baseUrl}}/api/appointments?mine=true
Authorization: Bearer {{access_token}}
```

- Si eres user → tus citas como paciente.
- Si eres nurse → tus citas como enfermero.

## D) Actualizar estado – PATCH /appointments/:id

```http
PATCH {{baseUrl}}/api/appointments/{{id}}
Authorization: Bearer {{access_token}}
Content-Type: application/json

{ "estado": "cancelada" }   // o "confirmada" | "inasistencia" | "atendida"
```

Reglas:
- Nurse puede cambiar a cualquier estado.
- User solo puede cancelar sus citas.

