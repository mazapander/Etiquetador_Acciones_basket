# AI_DEV_OPERATING_SYSTEM.md

Documento base reutilizable para todos los repos/proyectos.

Objetivo: optimizar la forma de trabajar con Codex, Cursor, ChatGPT, Claude Code u otros agentes de software, reduciendo tokens, evitando sobreingeniería y creando una base común de desarrollo.

---

## 1. Objetivo

Este documento define un sistema operativo de desarrollo para:

- Crear apps más rápido.
- Reutilizar una arquitectura base.
- Dar instrucciones consistentes a agentes de código.
- Reducir gasto de tokens.
- Evitar que los agentes toquen código no relacionado.
- Crear funcionalidades mediante issues claros.
- Crear skills reutilizables.
- Crear agentes especializados por rol.
- Mantener repos limpios, verificables y fáciles de continuar.

Este archivo debe copiarse o adaptarse en cada repo como:

```text
AGENTS.md
CODEX.md
CLAUDE.md
.cursor/rules/project-ai-workflow.mdc
docs/AI_DEV_OPERATING_SYSTEM.md
```

---

## 2. Principios base para agentes

Inspirado en las guías tipo Karpathy para reducir fallos comunes de LLMs de código.

### 2.1 Pensar antes de codificar

Antes de tocar código en tareas no triviales:

```md
## Análisis previo

### Objetivo entendido
...

### Supuestos
- ...

### Ambigüedades
- ...

### Riesgos
- ...

### Plan mínimo
1. ...
2. ...
3. ...

### Criterios de aceptación
- ...
```

Reglas:

- No asumir en silencio.
- No esconder confusión.
- No elegir una interpretación ambigua sin decirlo.
- Proponer la opción simple primero.
- Pedir aclaración solo si bloquea de verdad.
- Si no bloquea, asumir lo mínimo y documentarlo.

### 2.2 Simplicidad primero

Regla:

> La solución mínima que cumple el objetivo gana.

Evitar:

- Abstracciones prematuras.
- Arquitecturas genéricas sin uso real.
- Refactors grandes mezclados con features.
- Frameworks propios innecesarios.
- Añadir librerías sin justificar.
- Crear APIs flexibles cuando solo hay un caso de uso.

Test mental:

```text
¿Un senior diría que esto está sobrecomplicado?
Si sí, simplificar.
```

### 2.3 Cambios quirúrgicos

Al modificar un repo existente:

- Tocar solo archivos necesarios.
- No reformatear archivos enteros.
- No cambiar nombres, estilos o comentarios ajenos al objetivo.
- No borrar código muerto preexistente salvo que el issue lo pida.
- No hacer mejoras laterales en el mismo PR.
- Si aparece deuda técnica, crear nota o issue separado.

Cada línea cambiada debe poder trazarse al objetivo.

### 2.4 Ejecución por criterios verificables

Toda tarea debe tener criterios de aceptación.

Mal:

```text
Haz login.
```

Bien:

```text
Implementa login OIDC con Keycloak.

Criterios:
- /api/auth/login/keycloak redirige al proveedor.
- /api/auth/callback/keycloak crea usuario interno.
- /api/me devuelve usuario autenticado.
- Usuario no autenticado recibe 401.
- Hay test para normalización de claims.
```

### 2.5 Verificación obligatoria

Cada PR o entrega debe incluir:

```md
## Verificación realizada

- [ ] Tests backend
- [ ] Build frontend
- [ ] Migraciones
- [ ] Docker compose
- [ ] Prueba manual
- [ ] Revisión de permisos
- [ ] Revisión de secretos
- [ ] Riesgos pendientes
```

Si algo no se ha podido comprobar, decirlo claramente.

---

## 3. Stack base recomendado para nuevos proyectos

Para apps nuevas, salvo que el repo indique otra cosa:

```text
Frontend:
- React
- Vite
- TypeScript
- React Router
- TanStack Query
- Tailwind CSS
- shadcn/ui
- React Hook Form
- Zod

Backend:
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Pydantic Settings
- Authlib / PyJWT
- Uvicorn

Admin:
- SQLAdmin para primera versión
- React Admin solo si SQLAdmin se queda corto

Infra:
- Docker Compose
- PostgreSQL
- Backend
- Frontend
- Keycloak local opcional
- Adminer opcional local
```

Decisiones por defecto:

```text
ORM: SQLAlchemy 2.x
DB: PostgreSQL
Auth: OIDC
Admin inicial: SQLAdmin
Sesión: cookie HttpOnly
Despliegue: Docker en VPS
```

---

## 4. Starter reutilizable de app

Todo proyecto nuevo que necesite usuarios debe partir de esta base.

### 4.1 Funcionalidades core

- Auth OIDC con:
  - Azure Entra ID
  - Google
  - Keycloak
  - Provider OIDC externo
- Usuarios internos.
- External identities.
- Roles.
- Permisos.
- Organizaciones/proyectos.
- Feature flags.
- App settings.
- Audit log.
- Panel admin.
- API base.
- Docker Compose.
- Tests mínimos.

### 4.2 Modelos base

```text
User
ExternalIdentity
Organization
Membership
Role
Permission
RolePermission
UserRole
AppProject
AppSetting
FeatureFlag
AuditLog
```

### 4.3 Endpoints mínimos

```text
GET  /api/health
GET  /api/health/db

GET  /api/auth/providers
GET  /api/auth/login/{provider}
GET  /api/auth/callback/{provider}
POST /api/auth/logout
GET  /api/auth/me

GET  /api/me
GET  /api/me/permissions

GET    /api/users
GET    /api/users/{user_id}
PATCH  /api/users/{user_id}

GET   /api/roles
GET   /api/permissions

GET   /api/admin/settings
PATCH /api/admin/settings/{key}
GET   /api/admin/audit
GET   /api/admin/feature-flags
PATCH /api/admin/feature-flags/{key}
```

### 4.4 OIDC

Variables esperadas:

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

Flujo:

1. Frontend llama a `/api/auth/login/{provider}`.
2. Backend redirige al provider.
3. Callback valida claims.
4. Backend crea/busca usuario interno.
5. Backend crea `ExternalIdentity`.
6. Backend crea cookie HttpOnly.
7. Frontend consulta `/api/me`.

### 4.5 Admin

Primera versión:

```text
/admin con SQLAdmin
```

Debe permitir:

- Ver usuarios.
- Activar/desactivar usuarios.
- Gestionar roles.
- Ver permisos.
- Ver settings.
- Ver feature flags.
- Ver audit log.
- Ver external identities solo lectura.

Reglas:

- Solo `is_superuser` o permiso `admin.access`.
- Ocultar secretos.
- AuditLog solo lectura.

---

## 5. Estructura recomendada de repo

```text
.
├── AGENTS.md
├── CODEX.md
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/
├── frontend/
├── docs/
│   ├── architecture.md
│   ├── auth.md
│   ├── permissions.md
│   ├── local-development.md
│   └── AI_DEV_OPERATING_SYSTEM.md
├── agents/
│   ├── architect.md
│   ├── backend.md
│   ├── frontend.md
│   ├── auth.md
│   ├── database.md
│   ├── admin.md
│   ├── qa.md
│   └── devops.md
├── skills/
│   ├── create-feature.md
│   ├── create-crud-module.md
│   ├── add-oidc-provider.md
│   ├── add-admin-view.md
│   ├── debug-bug.md
│   ├── review-pr.md
│   └── prepare-deploy.md
└── .github/
    ├── ISSUE_TEMPLATE/
    └── pull_request_template.md
```

---

## 6. Agentes

### 6.1 architect

Responsabilidad:

- Diseñar solución mínima.
- Evitar sobreingeniería.
- Definir fases.
- Definir criterios de aceptación.
- Decidir qué no hacer.

No debe:

- Implementar sin entender el repo.
- Meter tecnologías nuevas sin justificación.
- Crear abstracciones especulativas.

### 6.2 backend

Responsabilidad:

- FastAPI.
- SQLAlchemy.
- Services.
- Repositories.
- Schemas.
- Tests.
- Permisos en backend.

Reglas:

- Router fino.
- Service con lógica.
- Repository para DB.
- Nunca confiar en permisos del frontend.

### 6.3 frontend

Responsabilidad:

- React.
- Rutas.
- Formularios.
- Tablas.
- Consumo API.
- Estados loading/error/empty.

Reglas:

- TypeScript.
- TanStack Query.
- Componentes reutilizables.
- No duplicar reglas de negocio.

### 6.4 auth

Responsabilidad:

- OIDC.
- Sesiones.
- Usuarios.
- Roles.
- Permisos.
- Seguridad.

Reglas:

- Validar issuer/audience.
- Normalizar claims.
- No guardar tokens externos salvo necesidad.
- Cookies HttpOnly.
- Endpoints protegidos.

### 6.5 database

Responsabilidad:

- Modelos.
- Migraciones.
- Seeds.
- Índices.
- Constraints.

Reglas:

- No cambiar modelo sin migración.
- Seeds idempotentes.
- Cuidar constraints.

### 6.6 admin

Responsabilidad:

- SQLAdmin.
- Backoffice.
- Gestión interna.

Reglas:

- SQLAdmin primero.
- Ocultar secretos.
- AuditLog solo lectura.
- Acceso restringido.

### 6.7 qa

Responsabilidad:

- Tests.
- Reproducción de bugs.
- Verificación.

Reglas:

- Bug no arreglado si no se puede reproducir o explicar.
- Verificar criterios de aceptación.
- Reportar lo no verificado.

### 6.8 devops

Responsabilidad:

- Docker.
- CI/CD.
- VPS.
- Reverse proxy.
- Variables.
- Healthchecks.

Reglas:

- No secretos en repo.
- `.env.example` completo.
- Docker compose funcional.
- Preparado para VPS.

---

## 7. Skills reutilizables

### 7.1 Skill: create-feature

Usar cuando se cree una funcionalidad end-to-end.

Pasos:

1. Entender objetivo.
2. Revisar repo.
3. Proponer diseño mínimo.
4. Crear modelo si aplica.
5. Crear migración.
6. Crear schema.
7. Crear repository.
8. Crear service.
9. Crear endpoint.
10. Crear UI.
11. Añadir permisos.
12. Añadir tests.
13. Verificar.

Output esperado:

- Código.
- Tests.
- Migración si aplica.
- Documentación mínima.
- PR claro.

### 7.2 Skill: create-crud-module

Pasos:

1. Modelo SQLAlchemy.
2. Migración Alembic.
3. Schemas Pydantic.
4. Repository.
5. Service.
6. Router.
7. Admin view.
8. Tests.
9. Frontend opcional.

### 7.3 Skill: add-oidc-provider

Inputs:

- Provider.
- Discovery URL.
- Client ID.
- Client Secret.
- Scopes.
- Claims esperados.
- Tenant rules.

Pasos:

1. Añadir config.
2. Registrar provider.
3. Validar discovery.
4. Normalizar claims.
5. Tests.
6. Docs.

### 7.4 Skill: add-admin-view

Pasos:

1. Revisar modelo.
2. Definir columnas visibles.
3. Definir columnas buscables.
4. Definir columnas editables.
5. Ocultar campos sensibles.
6. Añadir permisos.
7. Verificar acceso.

### 7.5 Skill: debug-bug

Pasos:

1. Entender síntoma.
2. Reproducir.
3. Aislar causa.
4. Aplicar cambio mínimo.
5. Test.
6. Explicar causa raíz.

### 7.6 Skill: review-pr

Checklist:

- ¿Cumple issue?
- ¿Hay cambios no relacionados?
- ¿Hay sobreingeniería?
- ¿Hay tests?
- ¿Hay migraciones?
- ¿Hay secretos?
- ¿Hay permisos backend?
- ¿Frontend maneja loading/error/empty?
- ¿Se puede probar?

### 7.7 Skill: prepare-deploy

Checklist:

- `.env`.
- Docker build.
- Migraciones.
- Healthchecks.
- Logs.
- Reverse proxy.
- CORS.
- Cookies Secure.
- OIDC redirect URIs.
- Backups DB.

---

## 8. Optimización de tokens y contexto

### 8.1 Regla general

No metas todo el repo en contexto salvo que sea necesario.

Usar niveles:

```text
Nivel 0: Issue + archivos concretos
Nivel 1: Árbol del repo + archivos relevantes
Nivel 2: Módulo completo
Nivel 3: Repo comprimido
Nivel 4: Repo entero
```

La mayoría de tareas deben resolverse en niveles 0-2.

### 8.2 Herramientas recomendadas

#### Repomix

Uso:

- Empaquetar repos en formato amigable para LLM.
- Contar tokens.
- Excluir archivos.
- Comprimir código con Tree-sitter.
- Generar contexto por carpetas o patrones.

Comandos útiles:

```bash
npx repomix@latest
npx repomix@latest --compress
npx repomix@latest --include "backend/app/**/*.py,frontend/src/**/*.tsx"
npx repomix@latest --ignore "**/*.test.*,node_modules,dist,build"
npx repomix@latest --token-count-tree 100
npx repomix@latest --include-diffs
npx repomix@latest --include-logs --include-logs-count 10
```

Config recomendada `repomix.config.json`:

```json
{
  "output": {
    "filePath": "repomix-output.xml",
    "style": "xml",
    "compress": true,
    "removeComments": false,
    "removeEmptyLines": true,
    "showLineNumbers": true
  },
  "ignore": {
    "customPatterns": [
      "node_modules/**",
      "dist/**",
      "build/**",
      ".venv/**",
      "venv/**",
      "__pycache__/**",
      ".git/**",
      "*.log",
      "*.sqlite",
      "*.db",
      ".env",
      ".env.*",
      "coverage/**",
      ".pytest_cache/**"
    ]
  }
}
```

#### Gitingest

Uso:

- Crear digest prompt-friendly de repos.
- Útil en Python/data science.
- Puede usarse desde CLI o como paquete Python.
- Útil para generar summaries rápidos de repos.

Comandos:

```bash
pipx install gitingest
gitingest /path/to/repo
gitingest https://github.com/user/repo
gitingest /path/to/repo --output digest.txt
```

#### Cursor / rules

Crear:

```text
.cursor/rules/project-ai-workflow.mdc
```

Contenido mínimo:

```md
Usa AGENTS.md y CODEX.md como fuente de verdad.
Antes de editar, identifica archivos relevantes.
Haz cambios quirúrgicos.
No refactorices código no relacionado.
Ejecuta/verifica tests si existen.
```

#### Claude Code / CLAUDE.md

Crear `CLAUDE.md` o enlazar a `AGENTS.md`.

Contenido mínimo:

```md
Lee AGENTS.md.
Sigue principios:
- Think before coding.
- Simplicity first.
- Surgical changes.
- Goal-driven execution.
```

#### GitHub Copilot instructions

Crear:

```text
.github/copilot-instructions.md
```

Contenido:

```md
Sigue AGENTS.md y CODEX.md.
No hagas cambios no relacionados.
Usa patrones existentes.
Prioriza solución mínima.
Añade tests si la feature toca lógica.
```

---

## 9. Flujo óptimo para trabajar con IA

### 9.1 Antes de pedir código

Crear issue con:

```md
## Objetivo

## Contexto

## Archivos/módulos relevantes

## Lo que NO quiero tocar

## Criterios de aceptación

## Verificación esperada
```

### 9.2 Para pedir ayuda a ChatGPT/Codex

Prompt base:

```md
Lee AGENTS.md y CODEX.md.

Quiero implementar: [feature].

Contexto:
- [módulo]
- [restricciones]
- [archivos relevantes]

No hagas cambios no relacionados.
Antes de codificar, devuelve:
1. objetivo entendido
2. supuestos
3. plan mínimo
4. archivos a tocar
5. criterios de aceptación

Después implementa con cambios quirúrgicos y verifica.
```

### 9.3 Para bugs

Prompt:

```md
Lee AGENTS.md.

Bug:
- Síntoma:
- Pasos:
- Esperado:
- Actual:
- Logs:

Primero reproduce o explica la causa probable.
Después aplica el cambio mínimo.
No refactorices alrededor.
Añade test si es razonable.
```

### 9.4 Para refactor

Prompt:

```md
Quiero refactorizar [módulo].

Objetivo medible:
- ...

Restricciones:
- No cambiar comportamiento.
- Tests deben pasar antes y después.
- PR pequeño.
- No mezclar nuevas features.
```

---

## 10. Plantillas GitHub

### 10.1 Feature issue

```md
---
name: Feature
about: Nueva funcionalidad
title: "feat: "
labels: feature
---

## Objetivo

## Contexto

## Usuario / rol afectado

## Flujo esperado

## Cambios backend

## Cambios frontend

## Cambios DB

## Permisos

## Criterios de aceptación

- [ ]

## Verificación esperada

- [ ] Tests backend
- [ ] Build frontend
- [ ] Migraciones
- [ ] Prueba manual
```

### 10.2 Bug issue

```md
---
name: Bug
about: Error o comportamiento inesperado
title: "bug: "
labels: bug
---

## Síntoma

## Pasos para reproducir

## Resultado esperado

## Resultado actual

## Logs / capturas

## Criterios de aceptación

- [ ] Bug reproducido
- [ ] Fix aplicado
- [ ] Test añadido o justificación
```

### 10.3 PR template

```md
## Resumen

## Cambios principales

## Cómo probar

## Verificación realizada

- [ ] Tests backend
- [ ] Build frontend
- [ ] Migraciones
- [ ] Docker compose
- [ ] Prueba manual

## Riesgos

## Pendientes

## Checklist de calidad

- [ ] Cambios quirúrgicos
- [ ] Sin sobreingeniería
- [ ] Sin secretos
- [ ] Permisos validados en backend
- [ ] Tests o justificación
```

---

## 11. Rollout a todos los repos

### 11.1 Repos activos prioritarios

Aplicar primero a proyectos vivos:

```text
mazapander/anderdata_server
mazapander/StatsFEB
mazapander/HerramientaTranscripcion
mazapander/FacturasOCR
mazapander/GESTIONCITASWHATTSAPP
mazapander/TranscripcionesCorporativas
mazapander/gestion-sportstudio
mazapander/webapp-auth
mazapander/Jira
mazapander/IAExtraccionEntidades
mazapander/OpenBanking
mazapander/CortesMateriaPrima
mazapander/LandingPageTubacex
mazapander/TransaccionSAP
```

Evitar aplicar inicialmente a:

```text
repos vacíos
repos de cursos
repos antiguos de pruebas
forks grandes ajenos
```

### 11.2 Archivos a añadir por repo

Mínimo:

```text
AGENTS.md
repomix.config.json
.github/copilot-instructions.md
.github/ISSUE_TEMPLATE/feature.md
.github/ISSUE_TEMPLATE/bug.md
.github/pull_request_template.md
```

Opcional:

```text
CODEX.md
CLAUDE.md
.cursor/rules/project-ai-workflow.mdc
docs/AI_DEV_OPERATING_SYSTEM.md
```

### 11.3 Contenido recomendado de AGENTS.md por repo

```md
# AGENTS.md

Este repo sigue el sistema de desarrollo definido en `docs/AI_DEV_OPERATING_SYSTEM.md`.

Principios:
1. Pensar antes de codificar.
2. Simplicidad primero.
3. Cambios quirúrgicos.
4. Ejecución por criterios verificables.

Reglas:
- No tocar código no relacionado.
- No reformatear archivos enteros.
- No crear abstracciones innecesarias.
- Usar patrones existentes.
- Añadir tests cuando se toque lógica.
- Verificar antes de entregar.
- No introducir secretos.

Para contexto IA:
- Usar `repomix --compress`.
- Usar `repomix --include-diffs` para PRs.
- Usar contexto parcial antes que repo entero.
```

---

## 12. Definition of Done del sistema

Este sistema estará bien implantado cuando:

- Cada repo activo tenga `AGENTS.md`.
- Cada repo activo tenga `repomix.config.json`.
- Cada repo activo tenga plantillas de issue/PR.
- Los agentes sepan qué hacer antes de codificar.
- Las tareas se definan con criterios de aceptación.
- Se reduzcan cambios no relacionados en PRs.
- Se use contexto parcial/comprimido.
- Los repos nuevos partan del starter auth/db/admin.
- Los bugs se solucionen con reproducción/verificación.
- Las features se creen mediante skills.

---

## 13. Prompt maestro para nuevos proyectos

```md
Lee AGENTS.md, CODEX.md y docs/AI_DEV_OPERATING_SYSTEM.md.

Quiero crear un nuevo proyecto usando el starter estándar:

- FastAPI
- SQLAlchemy 2.x
- PostgreSQL
- Alembic
- React + Vite + TypeScript
- Auth OIDC con Keycloak local + Google/Azure configurable
- Usuarios internos
- Roles/permisos
- SQLAdmin
- Docker Compose
- Tests mínimos

Antes de codificar:
1. Resume objetivo.
2. Lista supuestos.
3. Propón plan mínimo.
4. Lista archivos a crear.
5. Define criterios de aceptación.

Después implementa por fases con cambios pequeños y verificables.
```

---

## 14. Prompt maestro para trabajar en repo existente

```md
Lee AGENTS.md.

Quiero implementar: [feature/bug/refactor].

Contexto:
- Repo:
- Módulo:
- Archivos relevantes:
- Restricciones:

No hagas cambios no relacionados.
No sobreingenierices.
No reformatees archivos enteros.

Primero devuelve:
1. objetivo entendido
2. supuestos
3. riesgos
4. plan mínimo
5. archivos que tocarías
6. criterios de aceptación

Después implementa y verifica.
```
