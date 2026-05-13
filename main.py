import os
import io
import PIL.Image
from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import HTMLResponse
import google.generativeai as genai

app = FastAPI()

# 1. Configuração Robusta da IA
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# 2. Banco de Dados Simulado
propostas_db = []

# 3. Rota Principal (Frontend Completo)
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>CheckApp | Plataforma B2B</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .header-bg { background: linear-gradient(135deg, #1e1b4b 0%, #4338ca 100%); }
        </style>
    </head>
    <body class="bg-slate-50 min-h-screen font-sans text-slate-800">
        
        <nav class="header-bg p-6 shadow-xl flex justify-between items-center text-white">
            <h1 class="text-3xl font-black tracking-tight italic">Check<span class="text-pink-500">App</span></h1>
            <div class="space-x-2">
                <button onclick="switchTab('paciente')" class="px-5 py-2 rounded font-bold transition hover:bg-white/20 border border-transparent focus:border-white">Área Paciente</button>
                <button onclick="switchTab('lab')" class="px-5 py-2 rounded font-bold transition hover:bg-white/20 border border-transparent focus:border-white">Área Laboratório</button>
            </div>
        </nav>

        <main class="max-w-5xl mx-auto p-8 mt-4">
            
            <section id="aba-paciente" class="bg-white p-8 rounded-2xl shadow-lg border border-slate-100">
                <h2 class="text-2xl font-bold mb-8 border-b pb-2 text-indigo-900">Buscar Exames na Rede</h2>
                
                <div class="bg-slate-50 p-6 rounded-xl border border-slate-200 mb-8">
                    <div class="grid md:grid-cols-3 gap-4 mb-4">
                        <input id="cep-busca" type="text" placeholder="Digite seu CEP" class="p-4 border border-slate-300 rounded-lg w-full focus:ring-2 focus:ring-indigo-500 outline-none">
                        <select id="exame-busca" class="p-4 border border-slate-300 rounded-lg w-full focus:ring-2 focus:ring-indigo-500 outline-none bg-white">
                            <option value="Hemograma Completo">Hemograma Completo</option>
                            <option value="Vitamina D">Vitamina D</option>
                            <option value="Ressonância Magnética Joelho">Ressonância Magnética Joelho</option>
                            <option value="Ultrassom Abdomem total">Ultrassom Abdomem total</option>
                        </select>
                        <button onclick="realizarBusca()" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-4 rounded-lg shadow transition">PESQUISAR REDE</button>
                    </div>
                    <div id="resultados-busca" class="hidden mt-6 space-y-3">
                        <h3 class="font-bold text-slate-700">Resultados Próximos:</h3>
                        <div id="lista-resultados"></div>
                    </div>
                </div>

                <h2 class="text-2xl font-bold mb-4 border-b pb-2 text-indigo-900">Análise Inteligente de Receita</h2>
                <div class="border-2 border-dashed border-slate-300 p-8 text-center rounded-xl bg-slate-50 hover:bg-slate-100 transition">
                    <p class="text-slate-500 mb-4">Faça o upload do seu pedido médico para identificação automática.</p>
                    <input type="file" id="arquivo-receita" class="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 mb-6 cursor-pointer mx-auto max-w-sm">
                    <button onclick="analisarReceita()" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-8 py-3 rounded-lg shadow transition w-full max-w-sm">INICIAR LEITURA COM IA</button>
                    
                    <div id="resultado-ia" class="hidden mt-6 p-4 bg-emerald-100 text-emerald-900 font-bold rounded-lg border border-emerald-200"></div>
                </div>
            </section>

            <section id="aba-lab" class="hidden bg-white p-8 rounded-2xl shadow-lg border border-slate-100">
                <h2 class="text-2xl font-bold mb-8 border-b pb-2 text-pink-700">Cadastro de Propostas B2B</h2>
                
                <div class="bg-slate-50 p-6 rounded-xl border border-slate-200 mb-8">
                    <div class="grid md:grid-cols-2 gap-4 mb-4">
                        <input id="lab-nome" type="text" placeholder="Nome do Laboratório" class="p-4 border border-slate-300 rounded-lg w-full">
                        <select id="lab-exame" class="p-4 border border-slate-300 rounded-lg w-full bg-white">
                            <option value="Hemograma Completo">Hemograma Completo</option>
                            <option value="Vitamina D">Vitamina D</option>
                            <option value="Ressonância Magnética Joelho">Ressonância Magnética Joelho</option>
                            <option value="Ultrassom Abdomem total">Ultrassom Abdomem total</option>
                        </select>
                        <input id="lab-valor" type="number" placeholder="Valor da Proposta (R$)" class="p-4 border border-slate-300 rounded-lg w-full">
                        <div class="grid grid-cols-2 gap-2">
                            <input id="lab-data" type="date" class="p-4 border border-slate-300 rounded-lg w-full">
                            <input id="lab-hora" type="time" class="p-4 border border-slate-300 rounded-lg w-full">
                        </div>
                    </div>
                    <button onclick="salvarProposta()" class="bg-pink-600 hover:bg-pink-700 text-white font-bold w-full py-4 rounded-lg shadow transition">ENVIAR PROPOSTA PARA O SISTEMA</button>
                </div>

                <h3 class="text-xl font-bold mb-4 text-slate-800">Comparativo de Mercado (Painel B2B)</h3>
                <div class="overflow-x-auto border border-slate-200 rounded-xl">
                    <table class="w-full text-left bg-white">
                        <thead class="bg-slate-100 border-b border-slate-200">
                            <tr>
                                <th class="p-4 font-semibold">Laboratório</th>
                                <th class="p-4 font-semibold">Exame</th>
                                <th class="p-4 font-semibold">Valor</th>
                                <th class="p-4 font-semibold">Agendamento</th>
                            </tr>
                        </thead>
                        <tbody id="tabela-propostas" class="divide-y divide-slate-100">
                            </tbody>
                    </table>
                </div>
            </section>

        </main>

        <script>
            // Lógica de Alternância de Abas
            function switchTab(tabName) {
                document.getElementById('aba-paciente').classList.toggle('hidden', tabName !== 'paciente');
                document.getElementById('aba-lab').classList.toggle('hidden', tabName !== 'lab');
            }

            // Lógica de Busca de CEP (Simulação Rica)
            function realizarBusca() {
                const cep = document.getElementById('cep-busca').value;
                const exame = document.getElementById('exame-busca').value;
                const resDiv = document.getElementById('resultados-busca');
                const listaDiv = document.getElementById('lista-resultados');
                
                if(!cep) { alert("Por favor, informe o CEP."); return; }

                resDiv.classList.remove('hidden');
                listaDiv.innerHTML = '<p class="text-slate-500 italic">Buscando parceiros na região...</p>';

                // Simulando tempo de resposta do servidor
                setTimeout(() => {
                    const html = `
                        <div class="p-4 bg-white border border-indigo-100 rounded-lg flex justify-between items-center shadow-sm">
                            <div><p class="font-bold text-indigo-900">Lab Dasa Prime</p><p class="text-sm text-slate-500">A 1.2 km de distância</p></div>
                            <div class="text-right"><p class="font-bold text-emerald-600">R$ 85,00</p><p class="text-xs text-slate-400">${exame}</p></div>
                        </div>
                        <div class="p-4 bg-white border border-indigo-100 rounded-lg flex justify-between items-center shadow-sm mt-2">
                            <div><p class="font-bold text-indigo-900">Centro Médico Fleury</p><p class="text-sm text-slate-500">A 3.5 km de distância</p></div>
                            <div class="text-right"><p class="font-bold text-emerald-600">R$ 110,00</p><p class="text-xs text-slate-400">${exame}</p></div>
                        </div>
                    `;
                    listaDiv.innerHTML = html;
                }, 800);
            }

            // Lógica da Inteligência Artificial (Tratamento Reforçado)
            async function analisarReceita() {
                const arquivoInput = document.getElementById('arquivo-receita');
                const resultDiv = document.getElementById('resultado-ia');
                
                if (!arquivoInput.files || arquivoInput.files.length === 0) {
                    alert("Selecione a imagem do pedido médico primeiro.");
                    return;
                }

                resultDiv.classList.remove('hidden');
                resultDiv.className = "mt-6 p-4 bg-blue-100 text-blue-900 font-bold rounded-lg border border-blue-200 animate-pulse";
                resultDiv.innerText = "Processando imagem com Inteligência Artificial...";

                const formData = new FormData();
                formData.append('file', arquivoInput.files[0]);

                try {
                    const response = await fetch('/api/analisar-imagem', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if(response.ok) {
                        resultDiv.className = "mt-6 p-4 bg-emerald-100 text-emerald-900 font-bold rounded-lg border border-emerald-200";
                        resultDiv.innerText = "✓ Exame Detectado: " + data.resultado;
                    } else {
                        resultDiv.className = "mt-6 p-4 bg-red-100 text-red-900 font-bold rounded-lg border border-red-200";
                        resultDiv.innerText = "❌ Erro: " + data.resultado;
                    }
                } catch (error) {
                    resultDiv.className = "mt-6 p-4 bg-red-100 text-red-900 font-bold rounded-lg border border-red-200";
                    resultDiv.innerText = "❌ Falha de comunicação com o servidor.";
                }
            }

            // Lógica de Salvamento e Tabela B2B
            async function salvarProposta() {
                const payload = {
                    laboratorio: document.getElementById('lab-nome').value,
                    exame: document.getElementById('lab-exame').value,
                    valor: document.getElementById('lab-valor').value,
                    data: document.getElementById('lab-data').value,
                    hora: document.getElementById('lab-hora').value
                };

                if(!payload.laboratorio || !payload.valor) {
                    alert("Preencha o Nome do Laboratório e o Valor.");
                    return;
                }

                await fetch('/api/salvar-proposta', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                
                // Limpar campos
                document.getElementById('lab-valor').value = '';
                atualizarTabela();
            }

            async function atualizarTabela() {
                const response = await fetch('/api/listar-propostas');
                const propostas = await response.json();
                
                const tbody = document.getElementById('tabela-propostas');
                tbody.innerHTML = propostas.map(p => `
                    <tr class="hover:bg-slate-50 transition">
                        <td class="p-4 border-t font-semibold text-indigo-900">${p.laboratorio}</td>
                        <td class="p-4 border-t text-slate-700">${p.exame}</td>
                        <td class="p-4 border-t font-bold text-emerald-600">R$ ${p.valor}</td>
                        <td class="p-4 border-t text-sm text-slate-500">${p.data} às ${p.hora}</td>
                    </tr>
                `).join('');
            }

            // Carregar tabela ao iniciar
            document.addEventListener("DOMContentLoaded", atualizarTabela);
        </script>
    </body>
    </html>
    """

# 4. Rota da IA (Robusta)
@app.post("/api/analisar-imagem")
async def api_analisar_imagem(file: UploadFile = File(...)):
    if not model:
        return {"resultado": "Chave API não configurada no servidor."}
    try:
        conteudo = await file.read()
        imagem = PIL.Image.open(io.BytesIO(conteudo))
        
        prompt = "Você é um assistente médico. Identifique apenas o nome principal do exame solicitado nesta receita. Responda de forma curta e direta."
        resposta = model.generate_content([prompt, imagem])
        
        texto_limpo = resposta.text.strip()
        if not texto_limpo:
            return {"resultado": "Não foi possível ler o exame com clareza."}
            
        return {"resultado": texto_limpo}
    except Exception as e:
        return {"resultado": f"Erro interno na leitura: {str(e)}"}

# 5. Rotas de Dados B2B
@app.post("/api/salvar-proposta")
async def api_salvar_proposta(payload: dict = Body(...)):
    propostas_db.append(payload)
    return {"status": "sucesso"}

@app.get("/api/listar-propostas")
async def api_listar_propostas():
    return propostas_db
