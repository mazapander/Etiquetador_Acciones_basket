# CODEX.md — Starter framework reutilizable para apps

## Objetivo

Crear un starter/framework reutilizable para desarrollar aplicaciones web internas o SaaS ligeras sin repetir siempre la misma base técnica.

El framework debe servir como base común para varios proyectos en paralelo y debe incluir:

- Autenticación de usuarios mediante:
  - Azure Entra ID / Azure AD
  - Google OAuth/OIDC
  - Cualquier proveedor OIDC externo, especialmente Keycloak
- Backend API con FastAPI.
- ORM con SQLAlchemy 2.x.
- Migraciones con Alembic.
- Base de datos PostgreSQL.
- Panel de administración funcional y reutilizable.
- Modelo común de usuarios, roles, permisos, organizaciones/proyectos y auditoría.
- Docker Compose para desarrollo local.
- Estructura clara para que nuevos casos de uso se construyan encima sin rehacer auth, DB ni admin.
- Buenas prácticas para que Codex pueda desarrollar features por issues, ramas, commits y PRs.

---

## Contexto del usuario

Este starter debe estar pensado para un perfil que va a lanzar varios productos/proyectos en paralelo:

- Apps internas de empresa.
- MVPs SaaS.
- Herramientas de datos, IA, dashboards, automatización y operaciones.
- Apps con usuarios reales, roles, permisos y trazabilidad.
- Despliegue preferente en VPS con Docker.
- Posible integración posterior con Cloudflare, Tailscale, NGINX Proxy Manager o Traefik.
- Necesidad de ahorrar tokens y tiempo reutilizando una base común.

La prioridad no es crear un framework perfecto desde cero, sino un starter sólido, pragmático y mantenible que permita empezar rápido nuevos proyectos.

---

## Decisión de arquitectura recomendada

### Stack base

Usar esta arquitectura por defecto:

```text
frontend/
  React + Vite + TypeScript
  React Router
  TanStack Query
  Tailwind CSS
  shadcn/ui
  React Hook Form + Zod
  OIDC login flow usando backend como autoridad de sesión

backend/
  FastAPI
  SQLAlchemy 2.x
  Alembic
  PostgreSQL
  Authlib / python-jose / PyJWT para OIDC/JWT
  Pydantic Settings
  Uvicorn

admin/
  Opción A: SQLAdmin integrado en FastAPI para admin rápido
  Opción B: React Admin si se quiere un panel más profesional y extensible

infra/
  Docker Compose
  Postgres
  Backend
  Frontend
  Adminer opcional solo en local
  Keycloak opcional para entorno local de auth
```

### Decisión importante

Para terminarlo en una tarde:

- Usar **SQLAdmin** como primer panel de administración.
- No construir un admin custom completo desde cero.
- Preparar la API para que más adelante se pueda montar un admin en React Admin si el proyecto lo necesita.

SQLAdmin permite tener un CRUD de modelos SQLAlchemy muy rápido. Es suficiente para usuarios, roles, permisos, entidades base y debugging funcional.

---

## Repos/librerías a considerar antes de desarrollar desde cero

No reinventar estas piezas salvo que sea necesario:

### 1. Full Stack FastAPI Template

Referencia útil para estructura general de proyecto full-stack con FastAPI, Docker, PostgreSQL, frontend y despliegue.

Uso recomendado:

- Inspirarse en estructura.
- No copiar ciegamente si usa SQLModel y el objetivo aquí es SQLAlchemy.
- Aprovechar ideas de Docker, configuración, tests y organización.

### 2. FastAPI Users

Referencia útil para autenticación de usuarios.

Uso recomendado:

- Revisar si encaja con OIDC.
- Puede acelerar auth, usuarios y sesiones.
- Si complica demasiado la integración OIDC multi-provider, implementar auth propia simple sobre OIDC.

### 3. SQLAdmin

Referencia recomendada para panel admin inicial.

Uso recomendado:

- Integrarlo directamente en FastAPI.
- Crear vistas admin para:
  - User
  - Organization
  - Role
  - Permission
  - UserRole
  - AuditLog
  - Project/App
  - FeatureFlag
  - AppSetting

### 4. React Admin

Referencia útil si se quiere panel admin avanzado.

Uso recomendado:

- No usarlo en la primera tarde salvo que el objetivo explícito sea una UI admin potente.
- Preparar endpoints REST compatibles para adoptarlo más adelante.

### 5. Authlib

Referencia recomendada para OIDC/OAuth.

Uso recomendado:

- Usar para login con Azure, Google y Keycloak.
- Centralizar providers en configuración.
- Normalizar claims externos a un modelo interno de usuario.

### 6. Keycloak

Referencia recomendada como OIDC provider local/self-hosted.

Uso recomendado:

- Añadir Keycloak opcional en Docker Compose.
- Usarlo para desarrollo local y pruebas de OIDC.
- No obligar a que todos los proyectos usen Keycloak en producción.

---

## Principios de diseño

### 1. El usuario externo no es el usuario interno

Los usuarios pueden venir de Azure, Google o Keycloak, pero la app debe tener su propia tabla `users`.

El login externo solo identifica. La autorización interna vive en la app.

### 2. Normalizar identidad

Todos los providers deben mapearse a una estructura común:

```text
provider: azure | google | keycloak | custom
provider_subject: sub claim del provider
email
display_name
avatar_url
email_verified
tenant_id externo si existe
```

### 3. Separar autenticación de autorización

Autenticación:

- Saber quién es el usuario.
- Validar OIDC/JWT.
- Crear sesión.

Autorización:

- Qué puede hacer.
- Roles.
- Permisos.
- Organización/proyecto.
- Estado activo/inactivo.

### 4. Multi-proyecto desde el principio, pero sin sobreingeniería

Crear estructura base para organizaciones/proyectos, aunque algunos MVPs solo usen una organización por defecto.

### 5. Admin común reutilizable

El admin debe permitir:

- Ver usuarios.
- Activar/desactivar usuarios.
- Asignar roles.
- Ver permisos.
- Ver auditoría.
- Ver settings.
- Ver proyectos/apps registrados.
- Gestionar feature flags.
- Inspeccionar errores básicos.

---

## Estructura de carpetas objetivo

```text
.
├── CODEX.md
├── README.md
├── docker-compose.yml
├── docker-compose.local.yml
├── .env.example
├── backend
│   ├── app
│   │   ├── main.py
│   │   ├── core
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── oidc.py
│   │   │   ├── permissions.py
│   │   │   └── logging.py
│   │   ├── db
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── init_db.py
│   │   ├── models
│   │   │   ├── user.py
│   │   │   ├── organization.py
│   │   │   ├── role.py
│   │   │   ├── permission.py
│   │   │   ├── audit_log.py
│   │   │   ├── app_setting.py
│   │   │   └── feature_flag.py
│   │   ├── schemas
│   │   │   ├── user.py
│   │   │   ├── auth.py
│   │   │   ├── role.py
│   │   │   └── common.py
│   │   ├── api
│   │   │   ├── deps.py
│   │   │   ├── router.py
│   │   │   └── routes
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       ├── admin.py
│   │   │       ├── me.py
│   │   │       ├── roles.py
│   │   │       └── health.py
│   │   ├── services
│   │   │   ├── users.py
│   │   │   ├── auth.py
│   │   │   ├── audit.py
│   │   │   └── permissions.py
│   │   ├── repositories
│   │   │   ├── users.py
│   │   │   ├── roles.py
│   │   │   └── organizations.py
│   │   ├── admin
│   │   │   ├── setup.py
│   │   │   └── views.py
│   │   └── tests
│   ├── alembic
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend
│   ├── src
│   │   ├── main.tsx
│   │   ├── app
│   │   ├── components
│   │   ├── features
│   │   │   ├── auth
│   │   │   ├── admin
│   │   │   ├── users
│   │   │   └── dashboard
│   │   ├── lib
│   │   │   ├── api.ts
│   │   │   ├── auth.ts
│   │   │   └── queryClient.ts
│   │   └── routes
│   ├── package.json
│   └── Dockerfile
└── docs
    ├── architecture.md
    ├── auth.md
    ├── permissions.md
    └── local-development.md
```

---

## Modelo de datos base

Implementar modelos SQLAlchemy 2.x con typing moderno.

### User

Campos mínimos:

```text
id: UUID primary key
email: string unique indexed
display_name: string nullable
avatar_url: string nullable
is_active: bool default true
is_superuser: bool default false
last_login_at: datetime nullable
created_at
updated_at
```

### ExternalIdentity

Permite vincular un usuario interno a Azure, Google, Keycloak u otro OIDC provider.

```text
id: UUID
user_id: FK users.id
provider: string
provider_subject: string
provider_tenant_id: string nullable
raw_claims: JSONB nullable
created_at
updated_at
unique(provider, provider_subject)
```

### Organization

```text
id: UUID
name
slug unique
is_active
created_at
updated_at
```

### Membership

Relación entre usuario y organización.

```text
id: UUID
user_id
organization_id
status: active | invited | disabled
created_at
updated_at
unique(user_id, organization_id)
```

### Role

```text
id: UUID
name
slug
description
scope: global | organization | project
created_at
updated_at
```

### Permission

```text
id: UUID
code unique
description
created_at
updated_at
```

Ejemplos de permisos:

```text
admin.access
users.read
users.write
roles.read
roles.write
settings.read
settings.write
audit.read
projects.read
projects.write
```

### RolePermission

```text
role_id
permission_id
```

### UserRole

```text
user_id
role_id
organization_id nullable
project_id nullable
```

### AppProject

Entidad reutilizable para proyectos internos de cada app.

```text
id: UUID
organization_id nullable
name
slug
description nullable
is_active
created_at
updated_at
```

### AppSetting

Settings editables desde admin.

```text
id: UUID
key unique
value JSONB
description nullable
is_secret bool default false
created_at
updated_at
```

### FeatureFlag

```text
id: UUID
key unique
enabled bool
description nullable
created_at
updated_at
```

### AuditLog

```text
id: UUID
actor_user_id nullable
action string
entity_type string nullable
entity_id string nullable
metadata JSONB nullable
ip_address nullable
user_agent nullable
created_at
```

---

## Autenticación OIDC

### Providers soportados

Debe haber una configuración común para providers:

```env
OIDC_PROVIDERS=google,azure,keycloak

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration

AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=common
AZURE_DISCOVERY_URL=https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration

KEYCLOAK_CLIENT_ID=
KEYCLOAK_CLIENT_SECRET=
KEYCLOAK_DISCOVERY_URL=http://keycloak:8080/realms/dev/.well-known/openid-configuration

BACKEND_PUBLIC_URL=http://localhost:8000
FRONTEND_PUBLIC_URL=http://localhost:5173
SESSION_SECRET=
```

### Rutas backend requeridas

```text
GET  /api/auth/providers
GET  /api/auth/login/{provider}
GET  /api/auth/callback/{provider}
POST /api/auth/logout
GET  /api/auth/me
GET  /api/me
```

### Flujo recomendado

1. Frontend llama a `/api/auth/login/{provider}`.
2. Backend redirige al provider OIDC.
3. Provider devuelve a `/api/auth/callback/{provider}`.
4. Backend valida token y claims.
5. Backend busca `ExternalIdentity`.
6. Si no existe:
   - Busca usuario por email verificado.
   - Si no existe, crea usuario.
   - Crea ExternalIdentity.
   - Asigna rol por defecto.
7. Backend crea cookie de sesión segura.
8. Redirige al frontend.

### Sesión

Para apps propias, usar cookie HttpOnly firmada.

Requisitos:

```text
HttpOnly
Secure en producción
SameSite=Lax o None según dominio
Rotación posible
Expiración configurable
```

Evitar guardar access tokens externos salvo que haga falta llamar APIs del provider.

---

## Autorización y permisos

Crear dependencias FastAPI:

```python
current_user = Depends(get_current_user)
require_permission("users.read")
require_permission("admin.access")
require_superuser()
```

Crear helper:

```python
def user_has_permission(user, permission_code, organization_id=None) -> bool:
    ...
```

No hardcodear permisos en el frontend como fuente de verdad. El frontend solo oculta/muestra, el backend decide.

### Endpoint de permisos del usuario

```text
GET /api/me/permissions
```

Respuesta esperada:

```json
{
  "user_id": "...",
  "is_superuser": false,
  "permissions": [
    "admin.access",
    "users.read"
  ],
  "organizations": [
    {
      "id": "...",
      "slug": "default",
      "roles": ["admin"]
    }
  ]
}
```

---

## API base

Implementar endpoints mínimos:

### Health

```text
GET /api/health
GET /api/health/db
```

### Auth

```text
GET /api/auth/providers
GET /api/auth/login/{provider}
GET /api/auth/callback/{provider}
POST /api/auth/logout
GET /api/auth/me
```

### Users

```text
GET    /api/users
GET    /api/users/{user_id}
PATCH  /api/users/{user_id}
POST   /api/users/{user_id}/roles
DELETE /api/users/{user_id}/roles/{role_id}
```

### Roles

```text
GET /api/roles
GET /api/permissions
POST /api/roles
PATCH /api/roles/{role_id}
```

### Admin/settings

```text
GET   /api/admin/settings
PATCH /api/admin/settings/{key}
GET   /api/admin/audit
GET   /api/admin/feature-flags
PATCH /api/admin/feature-flags/{key}
```

---

## Admin panel

### Fase 1: SQLAdmin

Integrar SQLAdmin en `/admin`.

Debe incluir:

- Login protegido.
- Acceso solo a superusuarios o permiso `admin.access`.
- Vistas para:
  - User
  - ExternalIdentity
  - Organization
  - Membership
  - Role
  - Permission
  - UserRole
  - AppSetting
  - FeatureFlag
  - AuditLog

Criterios:

- No exponer secretos.
- En `AppSetting`, si `is_secret=true`, ocultar valor.
- AuditLog solo lectura.
- ExternalIdentity solo lectura salvo casos justificados.

### Fase 2 opcional: Admin frontend propio

Crear `/admin` en React solo si SQLAdmin se queda corto.

Módulos:

- Dashboard
- Usuarios
- Roles/permisos
- Organizaciones
- Feature flags
- Settings
- Auditoría

---

## Frontend base

Pantallas mínimas:

```text
/login
/auth/callback
/dashboard
/admin
/profile
/unauthorized
```

Componentes reutilizables:

```text
AppLayout
Sidebar
Topbar
ProtectedRoute
PermissionGate
UserMenu
ProviderLoginButton
DataTable
CrudPage
ConfirmDialog
FormDrawer
```

### Dashboard inicial

El dashboard debe mostrar:

- Usuario autenticado.
- Provider usado.
- Roles.
- Permisos.
- Organización activa.
- Estado de backend y DB.

---

## Docker Compose local

Debe levantar:

```text
postgres
backend
frontend
keycloak opcional
adminer opcional
```

Variables por defecto:

```env
POSTGRES_USER=app
POSTGRES_PASSWORD=app
POSTGRES_DB=app
DATABASE_URL=postgresql+psycopg://app:app@postgres:5432/app
```

Comandos esperados:

```bash
docker compose up --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.init_db
```

---

## Alembic

Configurar migraciones desde el principio.

Requisitos:

- `alembic revision --autogenerate -m "..."`
- `alembic upgrade head`
- Primera migración con todas las tablas core.
- Seed inicial con:
  - organización default
  - permisos base
  - rol superadmin
  - rol admin
  - rol member
  - feature flags iniciales

---

## Seed inicial

Crear comando:

```bash
python -m app.db.init_db
```

Debe:

1. Crear permisos base si no existen.
2. Crear roles base.
3. Asociar permisos a roles.
4. Crear organización `default`.
5. Crear superusuario si existe env `FIRST_SUPERUSER_EMAIL`.

Variables:

```env
FIRST_SUPERUSER_EMAIL=
FIRST_SUPERUSER_NAME=Ander
```

Si un usuario se autentica con ese email, se le asigna `is_superuser=true`.

---

## Seguridad mínima

Implementar desde el inicio:

- Cookies HttpOnly.
- CORS configurable.
- CSRF si se usan cookies en mutaciones sensibles.
- Validación de issuer/audience en OIDC.
- Nunca confiar en email si `email_verified=false`, salvo configuración explícita.
- Logs sin tokens ni secretos.
- Rate limit básico para auth.
- Headers seguros cuando se despliegue detrás de proxy.
- `.env.example` completo, pero ningún secreto real.

---

## Auditoría

Registrar eventos:

```text
auth.login_success
auth.login_failed
auth.logout
user.created
user.updated
role.assigned
role.removed
setting.updated
feature_flag.updated
admin.accessed
```

Cada evento debe guardar:

- actor_user_id
- action
- entity_type
- entity_id
- metadata
- ip_address
- user_agent
- created_at

---

## Testing mínimo

Crear tests para:

- Health check.
- DB session.
- Creación de usuario.
- Mapeo de claims OIDC.
- Permisos.
- Usuario sin permiso recibe 403.
- Superuser puede acceder.
- Seed idempotente.

---

## CI básico

Crear GitHub Actions:

```text
backend lint
backend tests
frontend build
docker compose config validation
```

No bloquear el MVP por una CI compleja.

---

## Workflow obligatorio para Codex

Cada cambio debe seguir este patrón:

1. Crear rama:
   ```bash
   git checkout -b feature/<short-name>
   ```

2. Implementar cambios pequeños y revisables.

3. Ejecutar:
   ```bash
   docker compose up --build
   docker compose exec backend pytest
   docker compose exec backend alembic upgrade head
   npm run build
   ```

4. Hacer commit:
   ```bash
   git add .
   git commit -m "feat: ..."
   ```

5. Hacer push:
   ```bash
   git push origin feature/<short-name>
   ```

6. Abrir Pull Request con:
   - Resumen
   - Cambios principales
   - Cómo probarlo
   - Riesgos
   - Pendientes

---

## Fases de implementación

### Fase 0 — Decisiones previas

Antes de escribir código, Codex debe confirmar o asumir:

```text
Backend: FastAPI
ORM: SQLAlchemy 2.x
DB: PostgreSQL
Admin inicial: SQLAdmin
Frontend: React + Vite + TypeScript
Auth: OIDC con Authlib
Sesión: cookie HttpOnly
Local OIDC: Keycloak opcional
```

Si no hay instrucciones contrarias, aplicar estas decisiones.

---

### Fase 1 — Scaffold

Crear:

- Backend FastAPI.
- Frontend React.
- Docker Compose.
- Postgres.
- `.env.example`.
- README básico.
- Health check.

Criterio de aceptación:

```text
docker compose up --build
GET /api/health responde OK
Frontend carga en local
```

---

### Fase 2 — DB y SQLAlchemy

Crear:

- Configuración SQLAlchemy.
- Modelos core.
- Alembic.
- Primera migración.
- Seed inicial.

Criterio de aceptación:

```text
alembic upgrade head funciona
init_db es idempotente
tablas creadas en PostgreSQL
```

---

### Fase 3 — Auth OIDC

Crear:

- Config OIDC multi-provider.
- Login Google.
- Login Azure.
- Login Keycloak.
- Callback.
- Normalización de claims.
- Creación/vinculación de usuario.
- Cookie de sesión.
- `/api/me`.

Criterio de aceptación:

```text
Usuario puede hacer login con al menos Keycloak local
Usuario aparece en tabla users
ExternalIdentity queda registrada
/api/me devuelve usuario autenticado
```

---

### Fase 4 — Permisos

Crear:

- Roles.
- Permisos.
- Dependencias `require_permission`.
- Endpoint `/api/me/permissions`.

Criterio de aceptación:

```text
Usuario sin permisos recibe 403
Usuario admin puede acceder a endpoints admin
Superuser puede acceder a todo
```

---

### Fase 5 — Admin

Crear SQLAdmin:

- Vistas para modelos core.
- Protección de acceso.
- AuditLog read-only.
- Settings con secretos ocultos.

Criterio de aceptación:

```text
/admin carga
Solo admin/superuser puede entrar
Usuarios y roles se pueden gestionar
AuditLog se puede consultar
```

---

### Fase 6 — Frontend base

Crear:

- Login page.
- Dashboard.
- Profile.
- ProtectedRoute.
- PermissionGate.
- Layout base.
- Pantalla unauthorized.

Criterio de aceptación:

```text
Login redirige correctamente
Dashboard muestra datos de /api/me
Rutas protegidas funcionan
```

---

### Fase 7 — Documentación

Crear docs:

```text
docs/architecture.md
docs/auth.md
docs/permissions.md
docs/local-development.md
```

Actualizar README con:

- Cómo levantar local.
- Cómo configurar Azure.
- Cómo configurar Google.
- Cómo configurar Keycloak.
- Cómo crear un nuevo proyecto usando este starter.

---

## Extras recomendados para acelerar futuros desarrollos

Implementar si no retrasa demasiado:

### 1. CLI interna

Crear comandos:

```bash
python -m app.cli create-module invoices
python -m app.cli create-admin-view Invoice
python -m app.cli seed
```

Puede ser una mejora enorme para reutilizar estructura.

### 2. Generador CRUD

Crear patrón para generar:

- modelo
- schema
- repository
- service
- router
- admin view
- tests básicos

Aunque sea simple, ahorra mucho tiempo.

### 3. Feature flags

Útil para activar/desactivar módulos por proyecto sin tocar código.

### 4. App settings desde DB

Útil para cambiar parámetros sin redeploy.

### 5. Audit log común

Clave para apps empresariales.

### 6. Plantilla de issue

Crear `.github/ISSUE_TEMPLATE/feature.md`:

```md
## Objetivo

## Contexto

## Cambios esperados

## Criterios de aceptación

## Cómo probar

## Riesgos
```

### 7. Plantilla de PR

Crear `.github/pull_request_template.md`.

### 8. Modo demo

Crear seed de datos demo para enseñar MVPs a clientes rápido.

### 9. Tenant/organization ready

Aunque empieces con una organización, dejarlo listo para multi-tenant simple.

### 10. Módulo de archivos opcional

Preparar interfaz abstracta para storage:

- local
- S3/MinIO
- Azure Blob

No implementarlo entero salvo que haga falta.

---

## Cosas que NO debe hacer Codex inicialmente

No hacer todavía:

- Billing.
- Stripe.
- Multi-tenant complejo con row-level security.
- Admin frontend custom completo si SQLAdmin basta.
- Microservicios.
- Kubernetes.
- Event bus.
- Sistema avanzado de notificaciones.
- Abstracción excesiva tipo framework propio publicado como paquete.
- Gestión compleja de permisos estilo IAM si no hay caso real.

La prioridad es tener una base reutilizable, arrancable y fácil de extender.

---

## Definition of Done global

El proyecto se considera terminado cuando:

- `docker compose up --build` levanta todo.
- Backend responde `/api/health`.
- PostgreSQL funciona.
- Alembic aplica migraciones.
- Seed inicial funciona varias veces sin duplicar datos.
- Login OIDC funciona al menos con Keycloak local.
- La estructura permite configurar Google y Azure por `.env`.
- `/api/me` devuelve usuario autenticado.
- `/api/me/permissions` devuelve permisos.
- Admin `/admin` funciona y está protegido.
- Existen roles/permisos base.
- Existe audit log.
- Frontend tiene login, dashboard, profile y protected route.
- README explica cómo usarlo.
- Hay tests mínimos pasando.
- Hay una plantilla clara para crear nuevos módulos.

---

## Prompt operativo para Codex

Usa este bloque cuando abras el issue principal:

```md
Quiero que implementes este starter framework siguiendo `CODEX.md`.

Prioridad:
1. Scaffold Docker + FastAPI + React + PostgreSQL.
2. SQLAlchemy 2.x + Alembic + modelos core.
3. Auth OIDC multi-provider con Keycloak local primero.
4. Usuarios internos + ExternalIdentity.
5. Roles/permisos.
6. SQLAdmin protegido.
7. Frontend mínimo con login/dashboard/profile.
8. Documentación y tests mínimos.

No sobreingenierices. Queremos una base reutilizable y funcional esta misma tarde.

Trabaja en una rama `feature/app-starter-framework`, haz commits pequeños y deja PR con instrucciones de prueba.
```

---

## Preguntas que Codex debe responder antes de implementar

Antes de empezar, Codex debe revisar el repo actual y responder:

1. ¿El repo está vacío o ya tiene backend/frontend?
2. ¿Hay Docker Compose existente?
3. ¿Hay algún estándar de lint/test ya definido?
4. ¿Se prefiere SQLAdmin o React Admin para la primera versión?
5. ¿El primer provider OIDC real será Keycloak, Azure o Google?
6. ¿El despliegue objetivo inicial es local, VPS con Docker, o ambos?
7. ¿El frontend y backend irán en el mismo dominio o dominios separados?
8. ¿Se necesita multi-tenant real ya o solo dejarlo preparado?
9. ¿Hay que crear el repo desde cero o adaptar uno existente?
10. ¿Se quiere que la base sea template repository de GitHub?

Si no hay respuesta, asumir:
- repo desde cero,
- local + VPS Docker,
- SQLAdmin,
- Keycloak local primero,
- Google/Azure configurables,
- multi-tenant preparado pero no complejo,
- backend y frontend separados en desarrollo,
- posibilidad de mismo dominio en producción detrás de proxy.
```
