from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import os

# 1) Cargar variables de entorno (.env)
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
PUERTO = int(os.getenv("PUERTO", "8080"))
MODELO_POR_DEFECTO = os.getenv("MODELO_POR_DEFECTO", "gpt-5-nano")

# 2) Inicializar cliente OpenAI (lee API_KEY)
cliente = OpenAI(api_key=API_KEY, timeout=900.0)

# 3) Crear app Flask
app = Flask(__name__)

INSTRUCCIONES_FIJAS = (
    "你是 ToneHelper，一名语气重写助手。严格保持原意与事实，不新增/删除关键信息。"
    "输出必须是 JSON：{original:'', versiones:[{tono:'', texto:''}]}。"
    "拒绝输出与请求无关的解释。"
)

def construir_entrada(texto_usuario: str, lista_tonos: list[str]) -> str:
    return (
        f"原句：\n{texto_usuario}\n\n"
        f"需要的语气（已指定）：\n{lista_tonos}\n"
        "请按模板输出 JSON。"
    )

@app.post("/api/tone")
def cambiar_tono():
    """Entrada JSON: { texto: string, tonos?: string[] }"""
    cuerpo = request.get_json(force=True) or {}
    texto = cuerpo.get("texto", "").strip()
    tonos = cuerpo.get("tonos") or ["温和", "口语化", "专业"]

    if not texto:
        return jsonify({"error": "texto vacío"}), 400

    entrada = construir_entrada(texto, tonos)

    respuesta = cliente.with_options(timeout=900.0).responses.create(
        model=MODELO_POR_DEFECTO,            # 经济模型：gpt-5-nano
        instructions=INSTRUCCIONES_FIJAS,    # 建议开启缓存（后续可加）
        input=entrada,
        response_format={"type": "json_object"},
        temperature=0.3,
        max_output_tokens=600,
        service_tier="flex",
    )

    # SDK 提供 output_text，为纯文本 JSON
    return app.response_class(
        response=respuesta.output_text,
        status=200,
        mimetype="application/json; charset=utf-8"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PUERTO)
