# Despliegue de produccion

Esta branch prepara el etiquetador para abrirlo a usuarios reales con:

- Supabase Auth para login.
- PostgreSQL externo como base principal.
- Docker para backend y frontend.
- Nginx Proxy Manager como entrada HTTPS.
- Auditoria funcional de accesos y cambios.

## 1. Backend de produccion

En produccion se debe arrancar este ASGI app:

```bash
uvicorn app.main_production:app --host 0.0.0.0 --port 8000
```

No uses `app.main:app` en produccion si quieres autenticacion y auditoria.

## 2. Variables principales

Ejemplo orientativo de `.env`:

```env
DATABASE_URL=postgresql+psycopg://etiquetador_user:CAMBIAR@postgres-main:5432/etiquetador
AUTH_ENABLED=true
SUPABASE_URL=https://TU_PROYECTO.supabase.co
ADMIN_EMAILS=["admin@tudominio.es"]

VIDEO_STORAGE_DIR=/app/storage/videos
VIDEO_LIBRARY_DIR=/app/storage/library
CLIP_EXPORTS_DIR=/app/storage/clip_exports
ETIQUETADOR_STORAGE_ROOT=/srv/etiquetador/storage

FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe

VITE_API_BASE_URL=/api
VITE_SUPABASE_URL=https://TU_PROYECTO.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=TU_CLAVE_PUBLICA
```

## 3. Migraciones

El contenedor backend ejecuta:

```bash
alembic upgrade head
```

La migracion `0002_production_auth_audit.py` crea:

- `app_users`
- `audit_events`
- `videos.uploaded_by_user_id`
- `tag_events.user_id`

## 4. Docker

Construccion y arranque:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

El compose espera dos redes externas:

- `npm_default` para Nginx Proxy Manager.
- `postgres-main` para conectar con tu Postgres existente.

Puedes cambiarlas con:

```env
NPM_NETWORK=nombre_red_npm
POSTGRES_NETWORK=nombre_red_postgres
```

## 5. Nginx Proxy Manager

Configuracion recomendada:

- Dominio: `etiquetador.tudominio.es`
- Frontend: `etiquetador-frontend:80`
- Location `/api`: `etiquetador-backend:8000`
- Force SSL: activado
- HTTP/2: activado
- Websockets: activado si se añaden en el futuro

Advanced config recomendado:

```nginx
client_max_body_size 10G;
proxy_read_timeout 3600s;
proxy_send_timeout 3600s;
proxy_request_buffering off;
proxy_buffering off;
```

## 6. Auditoria

Se guardan eventos en `audit_events` para acciones como:

- subida de video
- apertura de stream
- creacion, edicion y borrado de etiquetas
- exportacion de clips
- descarga de videos

Endpoint admin:

```text
GET /api/admin/audit-events
```

Solo usuarios con `role=admin` u `owner` pueden consultarlo. El rol admin se asigna automaticamente si el email esta en `ADMIN_EMAILS`.

## 7. Punto critico pendiente: streaming de video con auth

Las llamadas normales del frontend pasan el token de Supabase en `Authorization`.

El reproductor HTML `<video src="...">` no adjunta esa cabecera como un `fetch` normal. Por eso, con `AUTH_ENABLED=true`, el streaming puede requerir una solucion adicional:

- cookie de sesion httpOnly emitida por backend,
- `X-Accel-Redirect` desde Nginx,
- o URLs de media firmadas y de corta duracion.

No publiques videos como ficheros estaticos publicos si necesitas trazabilidad real.
