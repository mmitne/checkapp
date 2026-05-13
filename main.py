import os
import io
import PIL.Image
from fastapi import FastAPI, UploadFile, File, Request, Body
from fastapi.responses import HTMLResponse
import google.generativeai as genai

app = FastAPI()

# Configuração IA
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# Banco de dados temporário para a Demo
proposals = []

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <title>CheckApp | Pitch TI em Saúde</title>
    </head>
    <body class="bg-gray-100">
        <nav class="bg-indigo-900 p-6 text-white shadow-lg flex justify-between items-center">
            <h1 class="text-2xl font-black italic">CheckApp</h1>
            <div class="space-x-4">
                <button onclick="tab('paciente')" class="font-bold">Paciente</button>
                <button onclick="tab('lab')" class="font-bold">Laboratório</button>
            </div>
        </nav>
        <main class="max-w-5xl mx-auto p-6">
            <div id="paciente" class="bg-white p-8 rounded-3xl shadow-md">
                <h2 class="text-xl font-bold mb-6">Busca de Exames</h2>
                <div class="grid md:grid-cols-2 gap-4 mb-6">
                    <input id="cep" placeholder="CEP" class="p-3 border rounded">
                    <select id="exame" class="p-3 border rounded">
                        <option>Hemograma Completo</option><option>Vitamina D</option>
                        <option>Ressonância Magnética Joelho</option><option>Ultrassom Abdomem total</option>
                    </select>
                </div>
                <button onclick="buscar()" class="bg-indigo-600 text-white w-full py-3 rounded font-bold mb-8">BUSCAR REDE CREDENCIADA</button>
                <div class="border-2 border-dashed p-6 text-center rounded-xl">
                    <input type="file" id="upload" class="mb-4">
                    <button onclick="analyze()" class="bg-emerald-600 text-white px-8 py-3 rounded font-bold">ANALISAR RECEITA (IA)</button>
                </div>
                <div id="res" class="mt-4 p-4 bg-blue-50 text-blue-900 font-bold rounded hidden"></div>
            </div>

            <div id="lab" class="hidden bg-white p-8 rounded-3xl shadow-md">
                <h2 class="text-xl font-bold mb-6">Cadastrar Proposta B2B</h2>
                <div class="grid md:grid-cols-2 gap-4 mb-6">
                    <select id="l-exame" class="p-3 border rounded">
                        <option>Hemograma Completo</option><option>Vitamina D</option>
                        <option>Ressonância Magnética Joelho</option><option>Ultrassom Abdomem total</option>
                    </select>
                    <input id="l-valor" type="number" placeholder="Valor (R$)" class="p-3 border rounded">
                    <input id="l-data" type="date" class="p-3 border rounded">
                    <input id="l-hora" type="time" class="p-3 border rounded">
                </div>
                <button onclick="save()" class="w-full bg-pink-600 text-white py-3 rounded font-bold mb-8">ENVIAR PROPOSTA</button>
                <table class="w-full border"><tbody id="tbl"></tbody></table>
            </div>
        </main>
        <script>
            function tab(t){ document.getElementById('paciente').classList.toggle('hidden', t!=='paciente'); document.getElementById('lab').classList.toggle('hidden', t!=='lab'); }
            async function analyze(){
                const f = document.getElementById('upload').files[0];
                const fd = new FormData(); fd.append('file', f);
                const r = await fetch('/analyze', {method:'POST', body: fd});
                const d = await r.json();
                document.getElementById('res').innerText = "Exame Detectado: " + d.exame;
                document.getElementById('res').classList.remove('hidden');
            }
            async function save(){
                const d = {exame: document.getElementById('l-exame').value, valor: document.getElementById('l-valor').value, data: document.getElementById('l-data').value, hora: document.getElementById('l-hora').value};
                await fetch('/save', {method:'POST', body: JSON.stringify(d), headers:{'Content-Type':'application/json'}});
                location.reload();
            }
            async function buscar(){
                alert("Rede encontrada: 3 unidades com valores a partir de R$ 85,00");
            }
            fetch('/proposals').then(r=>r.json()).then(l => {
                document.getElementById('tbl').innerHTML = l.map(p => `<tr><td class="p-2 border">${p.exame}</td><td class="p-2 border">R$ ${p.valor}</td><td class="p-2 border">${p.data} ${p.hora}</td></tr>`).join('');
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
        res = model.generate_content(["Identifique o exame nesta receita.", img])
        return {"exame": res.text.strip()}
    except Exception as e: return {"exame": "Erro na IA"}

@app.post("/save")
async def save(data: dict = Body(...)):
    proposals.append(data)
    return {"status": "ok"}

@app.get("/proposals")
async def get_props(): return proposals
