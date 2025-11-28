import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date
import time
import os
import json
import google.generativeai as genai
from pypdf import PdfReader

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Futura Servidora", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        text-align: center;
    }
    h1 {
        text-align: center; color: #8E44AD; 
        font-family: 'Helvetica', sans-serif; font-size: 2.5rem !important; 
    }
    .stButton>button {
        width: 100%; border-radius: 20px; height: 50px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CÉREBRO DE I.A. (INSPIRADO NO CÓDIGO ADVOGADO) ---
IA_DISPONIVEL = False
ERRO_IA_DETALHE = ""
modelo = None

def limpar_json_resposta(texto):
    """Limpa a resposta da IA para garantir um JSON válido (igual ao código do advogado)"""
    texto = texto.replace('```json', '').replace('```', '').strip()
    # Encontra onde começa { e termina }
    start = texto.find('{')
    end = texto.rfind('}') + 1
    if start != -1 and end != -1:
        texto = texto[start:end]
    return texto

def conectar_ia_robusta():
    """Tenta conectar em vários modelos até achar um que funcione"""
    global modelo, IA_DISPONIVEL, ERRO_IA_DETALHE
    
    if "GEMINI_API_KEY" not in st.secrets:
        ERRO_IA_DETALHE = "Chave API não configurada nos Secrets."
        return

    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # Lista de prioridade (do mais rápido para o mais compatível)
        tentativas = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        
        modelo_escolhido = None
        
        # Tenta inicializar cada um
        for m_nome in tentativas:
            try:
                # Teste rápido para ver se o modelo responde
                temp_model = genai.GenerativeModel(m_nome)
                # Não fazemos chamada real aqui para economizar, apenas instanciamos
                modelo_escolhido = m_nome
                modelo = temp_model
                break # Se não deu erro ao instanciar, usa esse!
            except:
                continue
        
        if modelo:
            IA_DISPONIVEL = True
        else:
            # Fallback final genérico
            modelo = genai.GenerativeModel('gemini-pro')
            IA_DISPONIVEL = True
            
    except Exception as e:
        ERRO_IA_DETALHE = str(e)
        IA_DISPONIVEL = False

# Inicializa a IA ao carregar o app
conectar_ia_robusta()

# --- 3. DADOS E FUNÇÕES DE ARQUIVO ---
ARQUIVO_ESTUDOS = "historico_estudos.csv"
ARQUIVO_CONFIG = "config_concurso.json"

def carregar_config():
    if os.path.exists(ARQUIVO_CONFIG):
        with open(ARQUIVO_CONFIG, "r") as f: return json.load(f)
    return {"materias": ["Português", "Direito Constitucional"], "data_prova": str(date.today()), "banca": "FGV", "cargo": "Analista"}

def salvar_config(materias, data_prova, banca, cargo):
    with open(ARQUIVO_CONFIG, "w") as f:
        json.dump({"materias": materias, "data_prova": str(data_prova), "banca": banca, "cargo": cargo}, f)

def carregar_estudos():
    if not os.path.exists(ARQUIVO_ESTUDOS):
        return pd.DataFrame(columns=["Data", "Materia", "Minutos", "Qtd_Questões", "Acertos"])
    return pd.read_csv(ARQUIVO_ESTUDOS)

def salvar_sessao(materia, minutos, questoes, acertos):
    df = carregar_estudos()
    novo = pd.DataFrame([{
        "Data": datetime.now().strftime("%Y-%m-%d"),
        "Materia": materia,
        "Minutos": int(minutos),
        "Qtd_Questões": int(questoes),
        "Acertos": int(acertos)
    }])
    pd.concat([df, novo], ignore_index=True).to_csv(ARQUIVO_ESTUDOS, index=False)

def analisar_edital_pdf(arquivo_pdf):
    """Lê o PDF usando pypdf e envia texto para a IA"""
    if not IA_DISPONIVEL: return None
    try:
        leitor = PdfReader(arquivo_pdf)
        texto = ""
        # Lê as primeiras 15 páginas (onde geralmente está o resumo)
        for pag in leitor.pages[:15]: 
            texto += pag.extract_text() or ""
        
        prompt = f"""
        Analise este edital de concurso. Extraia APENAS JSON com:
        "banca": nome da banca,
        "cargo": cargo principal,
        "materias": lista de strings com disciplinas.
        Texto: {texto[:20000]}
        """
        resp = modelo.generate_content(prompt)
        return json.loads(limpar_json_resposta(resp.text))
    except: return None

# --- 4. INTERFACE ---
if 'cronometro' not in st.session_state: st.session_state.cronometro = {'ativo': False, 'inicio': None, 'acumulado': 0}
config = carregar_config()

st.markdown(f"<h1>⚖️ Painel da Aprovação</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align: center; color: gray; margin-top: -20px;'>{config['cargo']} | {config['banca']}</h3>", unsafe_allow_html=True)

# Lógica de Data
try:
    dias = (datetime.strptime(config['data_prova'], "%Y-%m-%d").date() - date.today()).days
    msg_dias = f"📅 Faltam **{dias}** dias" if dias > 0 else ("🔥 É HOJE!" if dias == 0 else "🏁 Já passou")
except: msg_dias = "⚙️ Configure a data"
st.info(msg_dias, icon="⏳")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Painel", "⏱️ Foco", "📝 Simulado", "⚙️ Config"])

with tab1:
    df = carregar_estudos()
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card'><h3>{(df['Minutos'].sum()/60):.1f}h</h3><p>Horas</p></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><h3>{df['Qtd_Questões'].sum()}</h3><p>Questões</p></div>", unsafe_allow_html=True)
        st.altair_chart(alt.Chart(df).mark_bar().encode(x='Data', y='Qtd_Questões', color='Materia').properties(height=250), use_container_width=True)
    else: st.warning("Sem dados ainda.")

with tab2: # CRONÔMETRO
    st.markdown("### 🍅 Modo Pomodoro")
    foco = st.selectbox("Matéria:", config['materias'])
    place = st.empty()
    stt = st.session_state.cronometro
    
    b1, b2, b3 = st.columns(3)
    if b1.button("▶️", use_container_width=True): stt['ativo']=True; stt['inicio']=time.time()-stt['acumulado']; st.rerun()
    if b2.button("⏸️", use_container_width=True): stt['ativo']=False; stt['acumulado']=time.time()-stt['inicio']; st.rerun()
    if b3.button("💾", use_container_width=True):
        mins = (time.time()-stt['inicio'] if stt['ativo'] else stt['acumulado'])/60
        if mins > 0.1: salvar_sessao(foco, mins, 0, 0); st.success("Salvo!"); time.sleep(1)
        stt['ativo']=False; stt['acumulado']=0; st.rerun()
        
    tempo = time.time()-stt['inicio'] if stt['ativo'] else stt['acumulado']
    m,s=divmod(int(tempo),60); h,m=divmod(m,60)
    place.markdown(f"<div style='text-align:center; font-size:60px; color:#8E44AD;'>{h:02d}:{m:02d}:{s:02d}</div>", unsafe_allow_html=True)
    if stt['ativo']: time.sleep(1); st.rerun()

with tab3: # SIMULADO IA ROBUSTO
    st.markdown("### 🤖 Gerador Inteligente")
    if not IA_DISPONIVEL: st.error(f"Erro IA: {ERRO_IA_DETALHE}")
    else:
        topico = st.selectbox("Assunto:", config['materias'])
        if st.button("Gerar Questão"):
            p = f"Gere 1 questão difícil de múltipla escolha sobre {topico} ({config['banca']}). Responda JSON puro: {{pergunta, opcoes, correta, comentario}}"
            try:
                with st.spinner("IA analisando banca..."):
                    res = modelo.generate_content(p)
                    # AQUI ESTÁ A MÁGICA DO CÓDIGO ADVOGADO:
                    json_limpo = limpar_json_resposta(res.text)
                    st.session_state.quest = json.loads(json_limpo)
            except Exception as e: st.error(f"Erro na geração: {e}")
            
        if 'quest' in st.session_state:
            q = st.session_state.quest
            st.write(f"**{q['pergunta']}**")
            resp = st.radio("Opções:", q['opcoes'], label_visibility="collapsed")
            if st.button("Corrigir"):
                # Limpeza extra para garantir que pega só a letra (A, B, C...)
                letra_resp = resp.split(")")[0].strip() if resp else ""
                letra_corr = q['correta'].strip()
                
                if letra_resp == letra_corr: 
                    st.success("✅ CERTO!"); st.balloons(); salvar_sessao(topico, 5, 1, 1)
                else: 
                    st.error(f"❌ Errado! Era {letra_corr}")
                st.info(q['comentario'])

with tab4:
    with st.form("cfg"):
        c = st.text_input("Cargo", config['cargo'])
        b = st.text_input("Banca", config['banca'])
        d = st.date_input("Data")
        m = st.text_area("Matérias", ", ".join(config['materias']))
        if st.form_submit_button("Salvar"):
            salvar_config([x.strip() for x in m.split(",")], d, b, c)
            st.rerun()
            
    st.divider()
    st.markdown("### 📥 Importar Edital")
    arq = st.file_uploader("Solte o PDF do Edital aqui", type="pdf")
    if arq and st.button("Ler Edital com IA"):
        with st.spinner("Lendo PDF e configurando tudo..."):
            dados = analisar_edital_pdf(arq)
            if dados:
                salvar_config(dados['materias'], d, dados['banca'], dados['cargo'])
                st.success(f"Sucesso! Configurado para {dados['banca']} - {dados['cargo']}")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Não consegui ler o edital. Tente um PDF mais simples.")
