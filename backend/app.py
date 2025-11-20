"""FastAPI factory."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import HOME_FILE, USE_OPENAI
from .models import RewriteIn, RewriteOut
from .services import RewriteService


def create_app() -> FastAPI:
    app = FastAPI(title="Polite Rewriter API", version="0.3")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    rewrite_service = RewriteService()

    @app.get("/health")
    async def health():
        return {"ok": True, "use_openai": USE_OPENAI}

    @app.get("/", response_class=FileResponse)
    async def serve_home():
        if not HOME_FILE.is_file():
            raise HTTPException(status_code=404, detail="home.html not found")
        return FileResponse(str(HOME_FILE))

    @app.post("/api/rewrite", response_model=RewriteOut)
    async def rewrite(payload: RewriteIn):
        return await rewrite_service.rewrite(payload)

    return app
