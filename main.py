import os
import io
import PIL.Image
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
import google.generativeai as genai

app = FastAPI()

# Configuração da IA (A chave deve estar no Render como GOOGLE_API_KEY)
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# Banco de dados em memória para a demo
lab_database = {"nome": "Laboratório Exemplo", "preco": "0.00", "status": "Inativo"}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .gradient-bg { background: linear-gradient(135deg, #1e1b4b 0%, #d946ef 100%); }
            .glass { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }
        </style>
    </head>
    <body class="bg-slate-100">
        <nav class="gradient-bg p-6 text-white shadow-lg flex justify-between items-center">
            <h1 class="text-3xl font-black">Check<span class="text-pink-300">App</span></h1>
            <div class="space-x-6">
                <button onclick="changeTab('paciente')" class="font-bold text-white border-b-2 border-pink-300">Paciente</button>
                <button onclick="changeTab('lab')" class="font-bold text-pink-200">Laboratório</button>
            </div>
        </nav>

        <main class="max-w-4xl mx-auto p-6">
            <div id="tab-paciente" class="glass p-8 rounded-3xl shadow-xl">
                <h2 class="text-2xl font-bold mb-6">Upload do Pedido</h2>
                <input type="file" id="upload" class="mb-4 w-full p-4 border rounded-xl">
                <button onclick="scan()" class="w-full bg-indigo-600 text-white py-4 rounded-xl font-bold">ANALISAR PEDIDO COM IA</button>
                <div id="status" class="mt-4 text-indigo-600 font-bold hidden">Processando imagem...</div>
                <div id="res" class="mt-6 p-6 bg-emerald-50 rounded-xl border border-emerald-200 hidden">
                    <p class="text-emerald-800 font-bold">Exame Detectado:</p>
                    <p id="exame-nome" class="text-2xl font-black text-emerald-900"></p>
                </div>
            </div>

            <div id="tab-lab" class="hidden glass p-8 rounded-3xl shadow-xl">
                <h2 class="text-2xl font-bold mb-6">Cadastro de Laboratório (B2B)</h2>
                <div class="space-y-4">
                    <input id="in-nome" type="text" placeholder="Nome do Lab" class="w-full p-4 border rounded-xl">
                    <input id="in-preco" type="number" placeholder="Preço Base (R$)" class="w-full p-4 border rounded-xl">
                    <button onclick="save()" class="w-full bg-pink-600 text-white py-4 rounded-xl font-bold">SALVAR REGRAS DO LAB</button>
                    <div id="status-lab" class="mt-4 text-emerald-600 font-bold hidden">Configurações salvas com sucesso!</div>
                </div>
            </div>
        </main>

        <script>
            function changeTab(t) {
                document.getElementById('tab-paciente').classList.toggle('hidden', t !== 'paciente');
                document.getElementById('tab-lab').classList.toggle('hidden', t !== 'lab');
            }
            async function scan() {
                const f = document.getElementById('upload').files[0];
                if(!f) return alert("Selecione um arquivo");
                document.getElementById('status').classList.remove('hidden');
                const fd = new FormData(); fd.append('file', f);
                const r = await fetch('/ia-scan', {method:'POST', body: fd});
                const d = await r.json();
                document.getElementById('status').classList.add('hidden');
                document.getElementById('res').classList.remove('hidden');
                document.getElementById('exame-nome').innerText = d.exame;
            }
            async function save() {
                const n = document.getElementById('in-nome').value;
                const p = document.getElementById('in-preco').value;
                await fetch('/save-lab', {method:'POST', body: JSON.stringify({n, p}), headers:{'Content-Type':'application/json'}});
                document.getElementById('status-lab').classList.remove('hidden');
            }
        </script>
    </body>
    </html>
    """

@app.post("/ia-scan")
async def scan(file: UploadFile = File(...)):
    if not model: return {"exame": "ERRO: Chave API ausente"}
    try:
        content = await file.read()
        img = PIL.Image.open(io.BytesIO(content))
        res = model.generate_content(["Identifique o exame principal.", img])
        return {"exame": res.text.strip()}
    except: return {"exame": "Imagem ilegível"}

@app.post("/save-lab")
async def save_lab(req: Request):
    data = await req.json()
    lab_database.update(data)
    return {"status": "ok"}
