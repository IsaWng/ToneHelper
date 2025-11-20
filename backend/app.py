"""FastAPI factory plus optional Flask variant."""

from __future__ import annotations

import os

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


def create_flask_app():
    """Return the legacy Flask implementation for compatibility."""
    from dotenv import load_dotenv
    from flask import Flask, jsonify, request
    from openai import OpenAI

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    default_model = os.getenv("MODELO_POR_DEFECTO", "gpt-5-nano")

    client = OpenAI(api_key=api_key, timeout=900.0)
    flask_app = Flask(__name__)

    instructions = (
        "你是 ToneHelper，一名语气重写助手。严格保持原意与事实，不新增/删除关键信息。"
        "输出必须是 JSON：{original:'', versiones:[{tono:'', texto:''}]}。"
        "拒绝输出与请求无关的解释。"
    )

    def build_prompt(text: str, tones: list[str]) -> str:
        return (
            f"原句：\n{text}\n\n"
            f"需要的语气（已指定）：\n{tones}\n"
            "请按模板输出 JSON。"
        )

    @flask_app.post("/api/tone")
    def cambiar_tono():
        """JSON body: { texto: string, tonos?: string[] }"""
        body = request.get_json(force=True) or {}
        text = body.get("texto", "").strip()
        tones = body.get("tonos") or ["温和", "口语化", "专业"]

        if not text:
            return jsonify({"error": "texto vacío"}), 400

        prompt = build_prompt(text, tones)

        response = client.with_options(timeout=900.0).responses.create(
            model=default_model,
            instructions=instructions,
            input=prompt,
            response_format={"type": "json_object"},
            temperature=0.3,
            max_output_tokens=600,
            service_tier="flex",
        )

        return flask_app.response_class(
            response=response.output_text,
            status=200,
            mimetype="application/json; charset=utf-8",
        )

    return flask_app


if __name__ == "__main__":
    port = int(os.getenv("PUERTO", "8080"))
    create_flask_app().run(host="0.0.0.0", port=port)
