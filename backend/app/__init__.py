"""Application package bootstrap.

The FastAPI app instance currently lives in ``app.main``. Optional routers are
registered here so feature modules can stay decoupled from the monolithic main
module while the application is gradually modularized.
"""

from fastapi import FastAPI

_ORIGINAL_FASTAPI_INIT = FastAPI.__init__


def _patched_fastapi_init(self, *args, **kwargs):
    _ORIGINAL_FASTAPI_INIT(self, *args, **kwargs)

    if not getattr(self.state, "ml_routes_registered", False):
        try:
            from app.ml_routes import router as ml_router

            self.include_router(ml_router)
            self.state.ml_routes_registered = True
        except Exception:
            self.state.ml_routes_registered = False

    if not getattr(self.state, "dataset_routes_registered", False):
        try:
            from app.dataset_routes import router as dataset_router

            self.include_router(dataset_router)
            self.state.dataset_routes_registered = True
        except Exception:
            self.state.dataset_routes_registered = False


if getattr(FastAPI, "_basket_optional_routes_patch_applied", False) is False:
    FastAPI.__init__ = _patched_fastapi_init
    FastAPI._basket_optional_routes_patch_applied = True
