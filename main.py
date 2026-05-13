import os
import io
import PIL.Image
from fastapi import FastAPI, UploadFile, File, Body, Request
from fastapi.responses import HTMLResponse
import google.generativeai as genai

app = FastAPI()

# Configuração IA
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

# Banco de dados temporário para a Demo
proposals = []
labs = [
    {"nome": "Lab Saúde Pro", "distancia": "1.2km", "valor": "85.00"},
    {"nome": "Diagnóstico Rápido", "distancia": "2.5km", "valor": "92.00"},
    {"nome": "Centro Médico Prime", "distancia": "3.8km", "valor": "78.00"}
]

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <title>CheckApp B2B</title>
        <style>.grad { background: linear-gradient(135deg, #0f172a 0%, #312e81 100%); }</style>
    </head>
    <body class="bg-gray-100">
        <nav class="grad p-6 text-white shadow-lg flex justify-between items-center">
            <h1 class="text-2xl font-black italic">Check<span class="text-pink-400">App</span></h1>
            <div class="space-x-4">
                <button onclick="tab('paciente')" class="px-4 py-2 font-bold bg-white/20 rounded">Paciente</button>
                <button onclick="tab('lab')" class="px-4 py-2 font-bold bg-white/20 rounded">Laboratório</button>
            </div>
        </nav>

        <main class="max-w-5xl mx-auto p-6">
            <div id="paciente" class="bg-white p-8 rounded-3xl shadow-md">
                <h2 class="text-xl font-bold mb-6">Busca de Rede</h2>
                <div class="grid md:grid-cols-3 gap-4 mb-6">
                    <input id="cep" placeholder="CEP" class="p-3 border rounded">
                    <select id="exame" class="p-3 border rounded">
                        <option>Hemograma Completo</option><option>Vitamina D</option>
                    </select>
                    <button onclick="buscar()" class="bg-indigo-600 text-white font-bold rounded">BUSCAR</button>
                </div>
                <div id="lista-labs" class="grid gap-4 mb-8"></div>
                <div class="border-2 border-dashed p-6 text-center rounded-xl">
                    <input type="file" id="upload" class="mb-2">
                    <button onclick="analyze()" class="bg-emerald-600 text-white px-6 py-2 rounded font-bold">ANALISAR PEDIDO COM IA</button>
                    <div id="res" class="mt-4 font-bold text-lg text-emerald-800"></div>
                </div>
            </div>

            <div id="lab" class="hidden bg-white p-8 rounded-3xl shadow-md">
                <h2 class="text-xl font-bold mb-6">Cadastrar Proposta B2B</h2>
                <div class="grid md:grid-cols-2 gap-4 mb-6">
                    <input id="l-exame" placeholder="Nome do Exame" class="p-3 border rounded">
                    <input id="l-valor" placeholder="Valor R$" class="p-3 border rounded">
                    <input id="l-data" type="date" class="p-3 border rounded">
                    <input id="l-hora" type="time" class="p-3 border rounded">
                </div>
                <button onclick="save()" class="w-full bg-pink-600 text-white py-3 rounded font-bold">ENVIAR PROPOSTA</button>
                <h3 class="text-xl font-bold mt-10 mb-4">Marketplace de Propostas</h3>
                <table class="w-full text-left border">
                    <tr class="bg-gray-100"><th class="p-3">Exame</th><th class="p-3">Valor</th><th class="p-3">Agendamento</th></tr>
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
                const r = await fetch('/analyze', {method:'POST', body: fd});
                const d = await r.json();
                document.getElementById('res').innerText = "Exame: " + d.exame;
            }
            async function buscar(){
                const l = await (await fetch('/labs')).json();
                document.getElementById('lista-labs').innerHTML = l.map(l => `<div class='p-4 border rounded flex justify-between'><span>${l.nome}</span><span>R$ ${l.valor}</span></div>`).join('');
            }
            async function save(){
                const d = {exame: document.getElementById('l-exame').value, valor: document.getElementById('l-valor').value, data: document.getElementById('l-data').value, hora: document.getElementById('l-hora').value};
                await fetch('/save', {method:'POST', body: JSON.stringify(d), headers:{'Content-Type':'application/json'}});
                location.reload();
            }
            fetch('/proposals').then(r=>r.json()).then(l => {
                document.getElementById('tbl').innerHTML = l.map(p => `<tr><td class="p-3 border">${p.exame}</td><td class="p-3 border">R$ ${p.valor}</td><td class="p-3 border">${p.data} às ${p.hora}</td></tr>`).join('');
            });
        </script>
    </body>
    </html>
    """

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        img = PIL.Image.open(io.BytesIO(await file.read()))
        res = model.generate_content(["Identifique apenas o nome do exame nesta receita.", img])
        return {"exame": res.text.strip()}
    except: return {"exame": "Erro na análise."}

@app.post("/save")
async def save(data: dict = Body(...)):
    proposals.append(data)
    return {"status": "ok"}

@app.get("/labs")
async def get_labs(): return labs

@app.get("/proposals")
async def get_props(): return proposals
