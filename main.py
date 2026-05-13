import os
import io
import PIL.Image
from fastapi import FastAPI, UploadFile, File, Request, Body
from fastapi.responses import HTMLResponse
import google.generativeai as genai
from typing import List

app = FastAPI()

# Configuração da IA (A chave é buscada do ambiente)
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# Banco de dados simulado
proposals = []

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>CheckApp B2B</title>
        <style>
            .grad { background: linear-gradient(135deg, #0f172a 0%, #312e81 100%); }
        </style>
    </head>
    <body class="bg-gray-100">
        <nav class="grad p-6 text-white shadow-lg flex justify-between items-center">
            <h1 class="text-2xl font-black italic">Check<span class="text-pink-400">App</span></h1>
            <div class="space-x-4">
                <button onclick="tab('paciente')" class="px-4 py-2 font-bold hover:bg-white/10 rounded">Paciente</button>
                <button onclick="tab('lab')" class="px-4 py-2 font-bold hover:bg-white/10 rounded">Laboratório</button>
            </div>
        </nav>

        <main class="max-w-4xl mx-auto p-6">
            <div id="paciente" class="bg-white p-8 rounded-2xl shadow-md">
                <h2 class="text-xl font-bold mb-6 text-slate-800">Busca por CEP e Exames</h2>
                <div class="grid md:grid-cols-2 gap-4 mb-6">
                    <input id="cep" type="text" placeholder="CEP" class="p-3 border rounded-lg">
                    <select id="exame" class="p-3 border rounded-lg">
                        <option value="Hemograma">Hemograma Completo</option>
                        <option value="Vitamina D">Vitamina D</option>
                        <option value="Ressonância">Ressonância Magnética</option>
                    </select>
                </div>
                <button onclick="buscar()" class="bg-indigo-600 text-white w-full py-3 rounded-lg font-bold mb-8">BUSCAR REDE CREDENCIADA</button>
                
                <div class="border-2 border-dashed p-6 rounded-xl">
                    <p class="font-bold mb-2">Análise de Receita via IA</p>
                    <input type="file" id="upload" class="mb-4">
                    <button onclick="analyze()" class="bg-emerald-600 text-white px-6 py-2 rounded-lg font-bold">ANALISAR IMAGEM</button>
                </div>
                <div id="res" class="mt-4 p-3 bg-blue-50 text-blue-800 font-bold hidden rounded"></div>
            </div>

            <div id="lab" class="hidden bg-white p-8 rounded-2xl shadow-md">
                <h2 class="text-xl font-bold mb-6 text-slate-800">Cadastro de Proposta</h2>
                <div class="grid md:grid-cols-2 gap-4 mb-6">
                    <input id="l-exame" class="p-3 border rounded" placeholder="Nome do Exame">
                    <input id="l-valor" type="number" class="p-3 border rounded" placeholder="Valor Proposta (R$)">
                    <input id="l-data" type="date" class="p-3 border rounded">
                    <input id="l-hora" type="time" class="p-3 border rounded">
                </div>
                <button onclick="save()" class="bg-pink-600 text-white w-full py-3 rounded-lg font-bold mb-8">ENVIAR PROPOSTA</button>
                
                <h3 class="font-bold mb-4">Comparativo de Mercado</h3>
                <table class="w-full text-left border-collapse">
                    <thead class="bg-gray-100"><tr><th class="p-2">Exame</th><th class="p-2">Valor</th><th class="p-2">Data/Hora</th></tr></thead>
                    <tbody id="tbl"></tbody>
                </table>
            </div>
        </main>
        <script>
            function tab(t){ document.getElementById('paciente').classList.toggle('hidden', t!=='paciente'); document.getElementById('lab').classList.toggle('hidden', t!=='lab'); }
            async function analyze(){
                const f = document.getElementById('upload').files[0];
                if(!f) return alert("Suba uma imagem");
                const fd = new FormData(); fd.append('file', f);
                document.getElementById('res').innerText = "Processando...";
                document.getElementById('res').classList.remove('hidden');
                try {
                    const r = await fetch('/analyze', {method:'POST', body: fd});
                    const d = await r.json();
                    document.getElementById('res').innerText = "Exame Identificado: " + d.exame;
                } catch(e) { document.getElementById('res').innerText = "Erro ao processar imagem."; }
            }
            async function save(){
                const data = {exame: document.getElementById('l-exame').value, valor: document.getElementById('l-valor').value, data: document.getElementById('l-data').value, hora: document.getElementById('l-hora').value};
                await fetch('/save', {method:'POST', body: JSON.stringify(data), headers:{'Content-Type':'application/json'}});
                location.reload();
            }
            fetch('/proposals').then(r=>r.json()).then(l => {
                document.getElementById('tbl').innerHTML = l.map(p => `<tr><td class="p-2 border">${p.exame}</td><td class="p-2 border">R$ ${p.valor}</td><td class="p-2 border">${p.data} ${p.hora}</td></tr>`).join('');
            });
            function buscar(){ alert("Busca concluída: 3 laboratórios encontrados na região (Simulação)."); }
        </script>
    </body>
    </html>
    """

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    if not model: return {"exame": "Erro: API Key não configurada"}
    try:
        content = await file.read()
        img = PIL.Image.open(io.BytesIO(content))
        res = model.generate_content(["Identifique apenas o nome do exame nesta receita médica.", img])
        return {"exame": res.text.strip()}
    except Exception as e:
        return {"exame": "Erro na análise: " + str(e)}

@app.post("/save")
async def save(data: dict = Body(...)):
    proposals.append(data)
    return {"status": "ok"}

@app.get("/proposals")
async def get_props():
    return proposals
