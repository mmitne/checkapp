import os
import io
import PIL.Image
from fastapi import FastAPI, UploadFile, File, Request, Body
from fastapi.responses import HTMLResponse
import google.generativeai as genai

app = FastAPI()

# Configuração IA
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

# Banco de dados simulado em memória
proposals = [
    {"exame": "Hemograma Completo", "valor": "85.00", "data": "15/05 09:00"},
    {"exame": "Vitamina D", "valor": "120.00", "data": "15/05 10:30"}
]

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <title>CheckApp | Pitch</title>
        <style>
            .grad { background: linear-gradient(135deg, #0f172a 0%, #312e81 100%); }
        </style>
    </head>
    <body class="bg-gray-50">
        <nav class="grad p-6 text-white flex justify-between items-center shadow-lg">
            <h1 class="text-3xl font-black italic">Check<span class="text-pink-400">App</span></h1>
            <div class="space-x-4">
                <button onclick="tab('paciente')" class="px-4 py-2 font-bold hover:bg-white/10 rounded">Paciente</button>
                <button onclick="tab('lab')" class="px-4 py-2 font-bold hover:bg-white/10 rounded">Laboratório</button>
            </div>
        </nav>

        <main class="max-w-5xl mx-auto p-6">
            <div id="paciente" class="bg-white p-8 rounded-3xl shadow-xl">
                <h2 class="text-2xl font-bold mb-6 text-slate-800">Encontrar Exames no meu CEP</h2>
                <div class="grid md:grid-cols-3 gap-4 mb-6">
                    <input id="cep" type="text" placeholder="CEP" class="p-4 border rounded-xl">
                    <select id="exame" class="p-4 border rounded-xl">
                        <option>Hemograma Completo</option><option>Vitamina D</option>
                        <option>Ultrassom</option><option>Tomografia</option>
                    </select>
                    <button onclick="buscar()" class="bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700">BUSCAR</button>
                </div>
                
                <div class="border-2 border-dashed p-6 text-center rounded-2xl mb-6">
                    <input type="file" id="upload" class="mb-4">
                    <button onclick="analyze()" class="bg-emerald-600 text-white px-8 py-3 rounded-xl font-bold">ANALISAR RECEITA COM IA</button>
                </div>
                <div id="res" class="p-4 bg-emerald-50 text-emerald-800 font-bold rounded-lg hidden"></div>
            </div>

            <div id="lab" class="hidden bg-white p-8 rounded-3xl shadow-xl">
                <h2 class="text-2xl font-bold mb-6">Propostas B2B</h2>
                <div class="grid grid-cols-2 gap-4 mb-8">
                    <input id="l-exame" class="p-4 border rounded" placeholder="Exame">
                    <input id="l-valor" type="number" class="p-4 border rounded" placeholder="Valor R$">
                    <button onclick="save()" class="col-span-2 bg-pink-600 text-white py-4 rounded font-bold">ENVIAR PROPOSTA</button>
                </div>
                <table class="w-full text-left border-collapse">
                    <tr class="bg-gray-100"><th class="p-3">Exame</th><th class="p-3">Valor</th></tr>
                    <tbody id="tbl"></tbody>
                </table>
            </div>
        </main>
        <script>
            function tab(t){ document.getElementById('paciente').classList.toggle('hidden', t!=='paciente'); document.getElementById('lab').classList.toggle('hidden', t!=='lab'); }
            async function analyze(){
                const f = document.getElementById('upload').files[0];
                const fd = new FormData(); fd.append('file', f);
                document.getElementById('res').innerText = "Analisando...";
                document.getElementById('res').classList.remove('hidden');
                const r = await fetch('/analyze', {method:'POST', body: fd});
                const d = await r.json();
                document.getElementById('res').innerText = "Exame Detectado: " + d.exame;
            }
            async function buscar(){
                alert("Buscando rede credenciada para seu CEP...");
            }
            async function save(){
                const data = {exame: document.getElementById('l-exame').value, valor: document.getElementById('l-valor').value};
                await fetch('/save', {method:'POST', body: JSON.stringify(data), headers:{'Content-Type':'application/json'}});
                location.reload();
            }
            fetch('/proposals').then(r=>r.json()).then(l => {
                document.getElementById('tbl').innerHTML = l.map(p => `<tr><td class="p-3 border">${p.exame}</td><td class="p-3 border">R$ ${p.valor}</td></tr>`).join('');
            });
        </script>
    </body>
    </html>
    """

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        content = await file.read()
        img = PIL.Image.open(io.BytesIO(content))
        res = model.generate_content(["Identifique o nome do exame nesta receita. Responda apenas o nome.", img])
        return {"exame": res.text.strip()}
    except: return {"exame": "Erro na IA"}

@app.post("/save")
async def save(data: dict = Body(...)):
    proposals.append(data)
    return {"status": "ok"}

@app.get("/proposals")
async def get_props():
    return proposals
