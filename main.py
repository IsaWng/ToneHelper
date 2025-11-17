from typing import List, Literal
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import re

# -------------------- OpenAI 客户端（可选） --------------------
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
if USE_OPENAI:
    from openai import OpenAI
    client = OpenAI(timeout=900.0)

# -------------------- FastAPI 初始化 --------------------
app = FastAPI(title="Polite Rewriter API", version="0.2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RewriteIn(BaseModel):
    text: str = Field(min_length=20, max_length=300)
    tone: Literal["softer", "colloquial", "concise"]
    lang: Literal["auto", "zh", "en", "es"] = "auto"

class Candidate(BaseModel):
    text: str
    reason: str

class RewriteOut(BaseModel):
    rewrites: List[Candidate]

@app.get("/health")
async def health():
    return {"ok": True, "use_openai": USE_OPENAI}

@app.post("/api/rewrite", response_model=RewriteOut)
async def rewrite(payload: RewriteIn):
    text = sanitize(payload.text)
    if not text:
        raise HTTPException(400, "empty text after sanitize")

    lang = payload.lang if payload.lang != "auto" else detect_lang(text)

    # 尝试 OpenAI
    if USE_OPENAI:
        try:
            return await generate_via_openai(text, payload.tone, lang)
        except Exception as e:
            # 打印错误并回退到 mock
            print("OpenAI error:", repr(e))

    # 本地 mock 回退
    rewrites = mock_generate(text, payload.tone, lang)
    return RewriteOut(rewrites=rewrites)

# -------------------- 工具函数 --------------------

def sanitize(s: str) -> str:
    s = re.sub(r"[\u0000-\u001f]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:300]

def detect_lang(t: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", t):
        return "zh"
    if re.search(r"[ñáéíóúü¿¡]", t, re.I) or re.search(r"\b(gracias|hola|vale|por favor|perdón)\b", t, re.I):
        return "es"
    return "en"

# -------------------- Mock 规则引擎 --------------------

def mock_generate(text: str, tone: str, lang: str) -> List[Candidate]:
    if lang == "zh":
        return mock_zh(text, tone)
    if lang == "es":
        return mock_es(text, tone)
    return mock_en(text, tone)

def mock_zh(t: str, tone: str) -> List[Candidate]:
    base = t
    if tone == "softer":
        opts = [
            (f"请{base}，谢谢理解。", "语气缓和"),
            (f"如果方便的话，{base}，感谢配合。", "保留边界"),
            (f"麻烦{base}，先行致谢。", "减少冲突"),
        ]
    elif tone == "colloquial":
        opts = [
            (f"嗨，{base}，可以吗？", "更口语"),
            (f"咱们{base}，行不行？", "更自然"),
            (f"要不就{base}，怎么样？", "更日常"),
        ]
    else:
        b = re.sub(r"(请问|麻烦)", "请", base)
        b = re.sub(r"，?谢谢(理解|配合)?。?$", "", b)
        b = re.sub(r"[。.!?]$", "", b)
        opts = [
            (f"{b}。", "更简短"),
            (f"请{b}。", "核心保留"),
            (f"麻烦{b}。", "去冗余"),
        ]
    return [Candidate(text=a, reason=b) for a, b in opts]

def mock_en(t: str, tone: str) -> List[Candidate]:
    s = t.rstrip(". ")
    if tone == "softer":
        opts = [
            (f"Could we {lower_first(s)}? Thanks for understanding.", "softer tone"),
            (f"If possible, could we {lower_first(s)}?", "hedging"),
            (f"I’d appreciate it if we could {lower_first(s)}.", "polite request"),
        ]
    elif tone == "colloquial":
        opts = [
            (f"Hey, can we {lower_first(s)}?", "casual"),
            (f"Mind if we {lower_first(s)}?", "spoken"),
            (f"Let’s {lower_first(s)}, ok?", "friendly"),
        ]
    else:
        opts = [
            (f"Please {lower_first(s)}.", "concise"),
            (f"Let’s {lower_first(s)}.", "brief"),
            (f"{capitalize(s)}.", "shortened"),
        ]
    return [Candidate(text=a, reason=b) for a, b in opts]

def mock_es(t: str, tone: str) -> List[Candidate]:
    s = t.rstrip(". ")
    if tone == "softer":
        opts = [
            (f"¿Podríamos {lower_first_es(s)}? Gracias por la comprensión.", "tono suave"),
            (f"Si es posible, ¿podemos {lower_first_es(s)}?", "condicional"),
            (f"Te agradecería si {lower_first_es(s)}.", "cortesía"),
        ]
    elif tone == "colloquial":
        opts = [
            (f"Oye, ¿podemos {lower_first_es(s)}?", "coloquial"),
            (f"¿Te va si {lower_first_es(s)}?", "hablado"),
            (f"Mejor {lower_first_es(s)}, ¿vale?", "directo amable"),
        ]
    else:
        opts = [
            (f"Por favor, {lower_first_es(s)}.", "conciso"),
            (f"{capitalize(s)}.", "breve"),
            (f"Procedamos a {lower_first_es(s)}.", "formal breve"),
        ]
    return [Candidate(text=a, reason=b) for a, b in opts]

def lower_first(s: str) -> str:
    s = re.sub(r"^(to\s+)?", "", s, flags=re.I)
    return re.sub(r"^([A-Z])", lambda m: m.group(1).lower(), s)

def lower_first_es(s: str) -> str:
    return re.sub(r"^([A-ZÁÉÍÓÚÑ])", lambda m: m.group(1).lower(), s)

def capitalize(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    return s[0].upper() + s[1:]

# -------------------- OpenAI 生成 --------------------
async def generate_via_openai(text: str, tone: str, lang: str) -> RewriteOut:
    """使用 OpenAI Responses API（模型 o3）。
    要求：将输出格式化为 JSON 对象，字段 rewrites=[{text,reason}×3]。
    """
    instructions = (
        "你是礼貌与语域转换专家。目标：不改变事实和立场的前提下，根据语气与语言改写。"
        "输出 JSON 对象，形如 {\"rewrites\":[{\"text\":\"...\",\"reason\":\"...\"},…]}；"
        "不要输出除 JSON 以外的任何内容。每个 text 1-2 句。reason 不超过 20 字。"
    )
    prompt = f"原文: {text}\n语气: {tone}\n语言: {lang}"

    # 同步 SDK 调用；在 FastAPI 中用简单方式直接调用足够
    resp = client.with_options(timeout=900.0).responses.create(
        model="o3",
        instructions=instructions,
        input=prompt,
        service_tier="flex",
    )

    result_text = resp.output_text.strip()

    import json
    try:
        data = json.loads(result_text)
        rewrites = [Candidate(**r) for r in data.get("rewrites", [])]
        # 若模型未给够 3 条，用 mock 补齐
        while len(rewrites) < 3:
            rewrites.append(Candidate(text=text, reason="fallback"))
    except Exception:
        # 模型未返回 JSON，回退
        rewrites = mock_generate(text, tone, lang)

    return RewriteOut(rewrites=rewrites)

# 运行： uvicorn main:app --host 0.0.0.0 --port 8000
