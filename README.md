# Etiquetador de Video

Herramienta local para cargar un partido, reproducirlo y registrar acciones con timestamps.

## Requisitos

- Python 3.12+
- Node.js 24+
- FFmpeg/FFprobe accesible para extraer metadata del video

En este entorno se usa:

```text
C:\Users\afer\Desktop\ANDER\ffmpeg-2026-03-12\bin\ffprobe.exe
```

Si cambia la ubicacion, ajusta `FFPROBE_PATH` en el `.env` de la raiz del proyecto.
La galeria de videos revisables se carga desde `VIDEO_LIBRARY_DIR`, que por defecto apunta a `../videos` desde `backend/` y corresponde a la carpeta `videos/` del repo.
La exportacion automatica de clips usa `FFMPEG_PATH` y escribe resultados en `CLIP_EXPORTS_DIR`.

## Configuracion

Hay un unico archivo de ejemplo para todo el proyecto:

```powershell
copy .env.example .env
```

Frontend y backend leen desde ese mismo `.env`.

En Windows, confirma:

```powershell
C:\Users\afer\Desktop\ANDER\ffmpeg-2026-03-12\bin\ffprobe.exe -version
```

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

API: `http://localhost:8000`

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

## Flujo v1

- La app abre en la galeria de proyectos.
- Desde la galeria se pueden cargar videos nuevos y abrir partidos ya detectados en la libreria o guardados en la base de datos.
- La vista de reproduccion y etiquetado se abre al entrar desde la galeria.
- Las flechas izquierda/derecha mueven el video `-5s/+5s`.
- El salto de teclado es configurable desde la propia vista.
- Una tag de tipo `range` guarda inicio en el primer click y final en el segundo.
- Puede haber varias tags de rango abiertas a la vez.
- Si el playhead retrocede por detras del inicio de una tag abierta, la UI obliga a resolver o cancelar ese rango antes de cerrarlo.
- Una tag de tipo `instant` guarda un timestamp puntual.
- Cada evento guarda tambien el `start_frame` cuando hay `fps` disponible.
- Al cargar otro video, la app pregunta si el actual queda finalizado y conserva su historico en SQLite.
- La galeria muestra nombre del partido, duracion, calidad, fps y porcentaje estimado de tiempo etiquetado.

## Exportacion de clips

Primer bloque disponible por API:

- `POST /api/videos/{video_id}/clip-plan`: previsualiza segmentos exportables para una tag.
- `POST /api/videos/{video_id}/clip-export`: genera clips en disco y un `manifest.json`.

Modos soportados:

- `segments`: un clip por evento/rango de la tag.
- `concatenate`: genera clips por evento y un video concatenado final.
- `exclude`: genera los tramos complementarios a una tag de rango/antagonista.
