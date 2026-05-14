import os
import io
import base64
import httpx
import PIL.Image
from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

app = FastAPI()

# CORS — permite que o frontend Vercel acesse este backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Configuração Google Gemini (existente)
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# 2. Chave Anthropic (nova)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# 3. Banco de Dados Simulado
propostas_db = []

# ─── ENDPOINT OCR — Leitura de Pedido Médico com IA ──────────────────────────
@app.post("/ocr")
async def ocr_pedido_medico(file: UploadFile = File(...)):
    """
    Recebe uma imagem de pedido médico e retorna os exames identificados.
    Usa Claude (Anthropic) como motor de OCR/IA.
    """
    if not ANTHROPIC_API_KEY:
        return {"erro": "Chave Anthropic não configurada no servidor.", "exames": []}

    # Lê a imagem enviada
    contents = await file.read()

    # Detecta o tipo correto
    mime_type = file.content_type or "image/jpeg"
    if mime_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        # Tenta converter para JPEG
        try:
            img = PIL.Image.open(io.BytesIO(contents))
            buffer = io.BytesIO()
            img.convert("RGB").save(buffer, format="JPEG")
            contents = buffer.getvalue()
            mime_type = "image/jpeg"
        except Exception:
            return {"erro": "Formato de imagem não suportado.", "exames": []}

    # Converte para base64
    b64_image = base64.b64encode(contents).decode("utf-8")

    # Chama a API do Claude
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-opus-4-5",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": b64_image,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": (
                                        "Você é um assistente médico especializado em laboratório clínico brasileiro. "
                                        "Analise esta imagem de pedido médico ou requisição laboratorial. "
                                        "Extraia SOMENTE os nomes dos exames laboratoriais solicitados. "
                                        "Normalize os nomes para o padrão brasileiro "
                                        "(ex: 'Hemograma completo', 'TSH ultrassensível', 'Glicemia em jejum', 'Colesterol total e frações'). "
                                        "Responda APENAS com JSON válido no formato: "
                                        "{\"exames\": [\"nome exame 1\", \"nome exame 2\"]} "
                                        "Se a imagem não for um pedido médico, responda: "
                                        "{\"exames\": [], \"erro\": \"Imagem não reconhecida como pedido médico\"} "
                                        "Não inclua markdown, não inclua explicações. Apenas o JSON."
                                    ),
                                },
                            ],
                        }
                    ],
                },
            )

        data = response.json()

        # Extrai o texto da resposta
        texto = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                texto += block.get("text", "")

        # Limpa e faz parse do JSON
        texto = texto.strip().replace("```json", "").replace("```", "").strip()
        import json
        resultado = json.loads(texto)

        return resultado

    except httpx.TimeoutException:
        return {"erro": "Tempo limite excedido. Tente novamente.", "exames": []}
    except Exception as e:
        return {"erro": f"Erro ao processar imagem: {str(e)}", "exames": []}


# ─── ENDPOINTS EXISTENTES (mantidos) ─────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "CheckApp API rodando", "versao": "2.0"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "anthropic": "configurado" if ANTHROPIC_API_KEY else "não configurado",
        "google": "configurado" if api_key else "não configurado",
    }


@app.post("/analisar-receita")
async def analisar_receita(file: UploadFile = File(...)):
    """Endpoint legado com Google Gemini (mantido para compatibilidade)"""
    if not model:
        return {"erro": "Google API não configurada", "exames": []}
    try:
        contents = await file.read()
        img = PIL.Image.open(io.BytesIO(contents))
        response = model.generate_content([
            "Liste apenas os nomes dos exames laboratoriais nesta receita médica, um por linha, sem explicações.",
            img
        ])
        exames = [e.strip() for e in response.text.strip().split("\n") if e.strip()]
        return {"exames": exames}
    except Exception as e:
        return {"erro": str(e), "exames": []}


@app.post("/proposta")
async def criar_proposta(proposta: dict = Body(...)):
    """Recebe uma proposta de laboratório para um leilão"""
    propostas_db.append(proposta)
    return {"status": "proposta recebida", "total": len(propostas_db)}


@app.get("/propostas/{leilao_id}")
async def listar_propostas(leilao_id: str):
    """Lista propostas de um leilão específico"""
    filtradas = [p for p in propostas_db if p.get("leilao_id") == leilao_id]
    return {"propostas": filtradas}


@app.delete("/propostas")
async def limpar_propostas():
    """Limpa todas as propostas (uso interno)"""
    propostas_db.clear()
    return {"status": "limpo"}
