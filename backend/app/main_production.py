"""Production ASGI entrypoint.

Use this module in Docker/Nginx deployments:

    uvicorn app.main_production:app --host 0.0.0.0 --port 8000

It keeps the local development entrypoint intact while adding Supabase auth,
request auditing and admin production routes.
"""

from app.main import app
from app.production import register_production_features

register_production_features(app)
