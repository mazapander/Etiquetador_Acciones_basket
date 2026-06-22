"""Application package bootstrap.

This project currently keeps the FastAPI app instance in ``app.main``. The ML
benchmark router is registered here so the new endpoints can be added without
rewriting the existing monolithic main module.
"""

from fastapi import FastAPI

_ORIGINAL_FASTAPI_INIT = FastAPI.__init__


def _patched_fastapi_init(self, *args, **kwargs):
    _ORIGINAL_FASTAPI_INIT(self, *args, **kwargs)
    if getattr(self.state, "ml_routes_registered", False):
        return
    try:
        from app.ml_routes import router as ml_router

        self.include_router(ml_router)
        self.state.ml_routes_registered = True
    except Exception:
        # Keep app imports safe during tooling/migration contexts. Runtime
        # request failures will surface from the actual ML route handlers.
        self.state.ml_routes_registered = False


if getattr(FastAPI, "_basket_ml_patch_applied", False) is False:
    FastAPI.__init__ = _patched_fastapi_init
    FastAPI._basket_ml_patch_applied = True
