import os
import io
import PIL.Image
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import google.generativeai as genai

app = FastAPI(title="CheckApp Pro")

# --- CONFIGURAÇÃO DA IA ---
# O sistema busca a chave nas variáveis de ambiente do Render (Seguro!)
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CheckApp | Plataforma Completa</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .gradient-bg { background: linear-gradient(135deg, #1e1b4b 0%, #d946ef 100%); }
            .glass-card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }
        </style>
    </head>
    <body class="bg-slate-50 min-h-screen">
        <nav class="gradient-bg p-6 text-white shadow-lg">
            <div class="max-w-4xl mx-auto flex justify-between items-center">
                <h1 class="text-3xl font-black">CheckApp</h1>
                <div class="space-x-4">
                    <button onclick="showTab('paciente')" class="font-bold hover:text-pink-200">Paciente</button>
                    <button onclick="showTab('lab')" class="font-bold hover:text-pink-200">Laboratório</button>
                </div>
            </div>
        </nav>

        <main class="max-w-4xl mx-auto p-6 -mt-10">
            <div id="tab-paciente" class="glass-card rounded-3xl shadow-2xl p-8 border">
                <h2 class="text-2xl font-bold text-slate-800 mb-6">Solicitação de Exames</h2>
                <div class="grid md:grid-cols-2 gap-4 mb-6">
                    <input id="cep" type="text" placeholder="CEP" class="p-4 border rounded-xl">
                    <select id="exame" class="p-4 border rounded-xl">
                        <option>Hemograma</option><option>Vitamina D</option>
                        <option>USG Abdomen</option><option>Tomografia</option>
                    </select>
                </div>
                <label for="foto" class="block border-2 border-dashed border-indigo-300 p-8 text-center rounded-2xl cursor-pointer hover:border-pink-500">
                    📸 UPLOAD RECEITA MÉDICA
                    <input type="file" id="foto" class="hidden" accept="image/*" onchange="iaScan()">
                </label>
                <div id="status" class="mt-4 text-center font-bold text-indigo-600 hidden">Lendo com IA...</div>
                <div id="res" class="mt-6 p-6 bg-emerald-50 border border-emerald-200 rounded-2xl hidden">
                    <p class="text-emerald-800 font-bold">Exame Detectado:</p>
                    <p id="exame-nome" class="text-2xl font-black text-emerald-600"></p>
                </div>
            </div>

            <div id="tab-lab" class="hidden glass-card rounded-3xl shadow-2xl p-8 border">
                <h2 class="text-2xl font-bold text-slate-800 mb-6">Painel do Laboratório</h2>
                <div class="space-y-4">
                    <input id="lab-nome" type="text" placeholder="Nome do Lab" class="w-full p-4 border rounded-lg">
                    <div class="flex gap-4">
                        <input id="lab-desc" type="number" placeholder="Desconto %" class="w-1/2 p-4 border rounded-lg">
                        <input id="lab-hora" type="text" placeholder="Horário (ex: 13-17)" class="w-1/2 p-4 border rounded-lg">
                    </div>
                    <button onclick="saveLab()" class="w-full bg-pink-600 text-white p-4 rounded-lg font-bold">SALVAR CONFIGURAÇÕES</button>
                    <p id="save-msg" class="hidden text-emerald-600 font-bold text-center">Configurações salvas!</p>
                </div>
            </div>
        </main>

        <script>
            function showTab(tab) {
                document.getElementById('tab-paciente').classList.toggle('hidden', tab !== 'paciente');
                document.getElementById('tab-lab').classList.toggle('hidden', tab !== 'lab');
            }
            async function iaScan() {
                const file = document.getElementById('foto').files[0];
                document.getElementById('status').classList.remove('hidden');
                const fd = new FormData(); fd.append('file', file);
                const r = await fetch('/ia-scan', {method:'POST', body: fd});
                const d = await r.json();
                document.getElementById('status').classList.add('hidden');
                document.getElementById('res').classList.remove('hidden');
                document.getElementById('exame-nome').innerText = d.exame;
            }
            function saveLab() { document.getElementById('save-msg').classList.remove('hidden'); }
        </script>
    </body>
    </html>
    """

@app.post("/ia-scan")
async def scan(file: UploadFile = File(...)):
    if not model: return {"exame": "ERRO: CHAVE API NÃO CONFIGURADA"}
    try:
        img = PIL.Image.open(io.BytesIO(await file.read()))
        res = model.generate_content(["Identifique o exame principal nesta receita. Responda apenas o nome.", img])
        return {"exame": res.text.strip()}
    except Exception as e: return {"exame": "ERRO: IMAGEM ILEGÍVEL"}
