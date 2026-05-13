import os
import io
import PIL.Image
from fastapi import FastAPI, UploadFile, File, Request, Body
from fastapi.responses import HTMLResponse
import google.generativeai as genai
from typing import List

app = FastAPI()

# Configuração da IA
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

# Banco de dados em memória para a demonstração
proposals = []

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>CheckApp Pro</title>
        <style>
            .gradient-bg { background: linear-gradient(135deg, #0f172a 0%, #312e81 100%); }
            .glass { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }
        </style>
    </head>
    <body class="bg-slate-100 min-h-screen">
        <nav class="gradient-bg p-6 text-white shadow-lg">
            <div class="max-w-5xl mx-auto flex justify-between items-center">
                <h1 class="text-3xl font-black italic">Check<span class="text-pink-400">App</span></h1>
                <div class="space-x-4">
                    <button onclick="tab('paciente')" class="px-4 py-2 font-bold hover:bg-white/10 rounded">Paciente</button>
                    <button onclick="tab('lab')" class="px-4 py-2 font-bold hover:bg-white/10 rounded">Laboratório</button>
                </div>
            </div>
        </nav>

        <main class="max-w-5xl mx-auto p-6">
            <div id="view-paciente" class="glass p-8 rounded-3xl shadow-xl">
                <h2 class="text-2xl font-bold text-slate-800 mb-6">Solicitar Exames</h2>
                <div class="grid md:grid-cols-2 gap-6">
                    <input id="cep" type="text" placeholder="CEP" class="p-4 border rounded-xl w-full">
                    <select id="exam-select" class="p-4 border rounded-xl w-full">
                        <option>Hemograma Completo</option><option>Vitamina D</option>
                        <option>Ultrassom de Abdômen</option><option>Ressonância</option>
                    </select>
                </div>
                <div class="mt-6 border-2 border-dashed border-slate-300 p-8 text-center rounded-2xl">
                    <input type="file" id="upload" class="mb-4">
                    <button onclick="analyze()" class="bg-indigo-600 text-white px-8 py-3 rounded-xl font-bold">ANALISAR PEDIDO</button>
                </div>
                <div id="res-paciente" class="mt-6 p-4 bg-emerald-50 rounded-lg hidden text-emerald-800 font-bold"></div>
            </div>

            <div id="view-lab" class="hidden glass p-8 rounded-3xl shadow-xl">
                <h2 class="text-2xl font-bold text-slate-800 mb-6">Cadastro de Proposta</h2>
                <div class="grid md:grid-cols-2 gap-4">
                    <select id="lab-exam" class="p-4 border rounded-lg">
                        <option>Hemograma Completo</option><option>Vitamina D</option>
                        <option>Ultrassom de Abdômen</option><option>Ressonância</option>
                    </select>
                    <input id="lab-price" type="number" placeholder="Valor (R$)" class="p-4 border rounded-lg">
                    <input id="lab-date" type="date" class="p-4 border rounded-lg">
                    <input id="lab-time" type="time" class="p-4 border rounded-lg">
                </div>
                <button onclick="saveProposal()" class="mt-4 w-full bg-pink-600 text-white py-4 rounded-xl font-bold">ENVIAR PROPOSTA</button>
                
                <h3 class="text-xl font-bold mt-10 mb-4">Comparativo de Propostas</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-left">
                        <thead class="bg-slate-200"><tr><th class="p-3">Exame</th><th class="p-3">Valor</th><th class="p-3">Data/Hora</th></tr></thead>
                        <tbody id="proposal-table"></tbody>
                    </table>
                </div>
            </div>
        </main>

        <script>
            function tab(t) {
                document.getElementById('view-paciente').classList.toggle('hidden', t !== 'paciente');
                document.getElementById('view-lab').classList.toggle('hidden', t !== 'lab');
            }
            async function analyze() {
                const f = document.getElementById('upload').files[0];
                const fd = new FormData(); fd.append('file', f);
                document.getElementById('res-paciente').innerText = "Processando com IA...";
                document.getElementById('res-paciente').classList.remove('hidden');
                const r = await fetch('/analyze', {method:'POST', body: fd});
                const d = await r.json();
                document.getElementById('res-paciente').innerText = "Exame identificado: " + d.exame;
            }
            async function saveProposal() {
                const data = {
                    exame: document.getElementById('lab-exam').value,
                    valor: document.getElementById('lab-price').value,
                    data: document.getElementById('lab-date').value + " " + document.getElementById('lab-time').value
                };
                await fetch('/save', {method:'POST', body: JSON.stringify(data), headers:{'Content-Type':'application/json'}});
                updateTable();
            }
            async function updateTable() {
                const r = await fetch('/proposals');
                const list = await r.json();
                const tbody = document.getElementById('proposal-table');
                tbody.innerHTML = list.map(p => `<tr><td class='p-3 border'>${p.exame}</td><td class='p-3 border'>R$ ${p.valor}</td><td class='p-3 border'>${p.data}</td></tr>`).join('');
            }
        </script>
    </body>
    </html>
    """

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        img = PIL.Image.open(io.BytesIO(await file.read()))
        res = model.generate_content(["Identifique apenas o nome do exame no pedido médico.", img])
        return {"exame": res.text.strip()}
    except: return {"exame": "Erro na análise"}

@app.post("/save")
async def save(data: dict = Body(...)):
    proposals.append(data)
    return {"status": "ok"}

@app.get("/proposals")
async def get_props():
    return proposals
