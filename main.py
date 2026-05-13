import os
import io
import PIL.Image
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import google.generativeai as genai

app = FastAPI()

# Configuração da IA (Via Environment Variable)
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

# Armazenamento em memória para a Demo (Simula um Banco de Dados)
lab_data = {"nome": "Laboratório Exemplo", "desconto": 0, "status": "Inativo"}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-50 p-6">
        <div class="max-w-4xl mx-auto">
            <h1 class="text-3xl font-bold mb-8">CheckApp | Plataforma B2B</h1>
            
            <div class="bg-white p-6 rounded-xl shadow mb-8">
                <h2 class="text-xl font-bold mb-4">Análise de Pedido Médico</h2>
                <input type="file" id="fileInput" class="mb-4">
                <button onclick="processar()" class="bg-blue-600 text-white px-4 py-2 rounded">Analisar</button>
                <div id="res" class="mt-4 font-bold text-lg text-blue-900"></div>
            </div>

            <div class="bg-slate-900 text-white p-6 rounded-xl">
                <h2 class="text-xl font-bold mb-4">Cadastro e Regras do Lab</h2>
                <input id="labNome" placeholder="Nome do Lab" class="w-full mb-2 p-2 text-black">
                <input id="labDesc" type="number" placeholder="Desconto %" class="w-full mb-2 p-2 text-black">
                <button onclick="salvarLab()" class="bg-green-600 px-4 py-2 rounded">Salvar Regras</button>
                <div id="statusLab" class="mt-4 text-green-400"></div>
            </div>
        </div>
        <script>
            async function processar() {
                const f = document.getElementById('fileInput').files[0];
                const fd = new FormData(); fd.append('file', f);
                document.getElementById('res').innerText = "Processando...";
                const r = await fetch('/ia-scan', {method:'POST', body: fd});
                const d = await r.json();
                document.getElementById('res').innerText = "Exame: " + d.exame;
            }
            async function salvarLab() {
                const n = document.getElementById('labNome').value;
                const d = document.getElementById('labDesc').value;
                const r = await fetch('/save-lab', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({nome: n, desconto: d})
                });
                document.getElementById('statusLab').innerText = "Regras salvas com sucesso!";
            }
        </script>
    </body>
    </html>
    """

@app.post("/ia-scan")
async def scan(file: UploadFile = File(...)):
    if not model: return {"exame": "Erro: Chave API ausente"}
    try:
        content = await file.read()
        img = PIL.Image.open(io.BytesIO(content))
        res = model.generate_content(["Identifique o exame principal.", img])
        return {"exame": res.text.strip()}
    except Exception as e:
        return {"exame": f"Erro: {str(e)}"}

@app.post("/save-lab")
async def save_lab(data: dict):
    lab_data.update(data)
    return {"status": "ok"}
