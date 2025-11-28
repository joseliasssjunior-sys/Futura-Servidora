import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date
import time
import os
import json
import google.generativeai as genai

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Futura Servidora", page_icon="⚖️", layout="wide")

# --- CSS PERSONALIZADO (VISUAL APP) ---
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

# --- 2. CONEXÃO COM A IA (COM DEBUG DE ERRO) ---
IA_DISPONIVEL = False
ERRO_IA_DETALHE = ""

try:
    # Tenta pegar a chave secreta
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        modelo = genai.GenerativeModel('gemini-1.5-flash')
        IA_DISPONIVEL = True
    else:
        ERRO_IA_DETALHE = "Chave GEMINI_API_KEY não encontrada nos Secrets."
except Exception as e:
    ERRO_IA_DETALHE = f"Erro na conexão: {e}"

# ARQUIVOS
ARQUIVO_ESTUDOS = "historico_estudos.csv"
ARQUIVO_CONFIG = "config_concurso.json"

# --- 3. FUNÇÕES ---
def carregar_config():
    if os.path.exists(ARQUIVO_CONFIG):
        with open(ARQUIVO_CONFIG, "r") as f: return json.load(f)
    return {"materias": ["Português", "Direito Constitucional"], "data_prova": str(date.today()), "banca": "Definir Banca", "cargo": "Meu Cargo"}

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

# --- 4. INTERFACE ---

if 'cronometro' not in st.session_state: st.session_state.cronometro = {'ativo': False, 'inicio': None, 'acumulado': 0}
config = carregar_config()

# Cabeçalho
st.markdown(f"<h1>⚖️ Painel da Aprovação</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align: center; color: gray; margin-top: -20px;'>{config['cargo']} | {config['banca']}</h3>", unsafe_allow_html=True)

# Lógica da Data
try:
    data_prova = datetime.strptime(config['data_prova'], "%Y-%m-%d").date()
    hoje = date.today()
    dias = (data_prova - hoje).days
    if dias < 0: msg_dias = "🏁 A prova já passou!"
    elif dias == 0: msg_dias = "🔥 É HOJE! BOA SORTE!"
    else: msg_dias = f"📅 Faltam **{dias}** dias"
except: msg_dias = "⚙️ Configure a data"
st.info(msg_dias, icon="⏳")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Painel", "⏱️ Foco", "📝 Simulado", "⚙️ Config"])

# ABA 1: DASHBOARD
with tab1:
    df = carregar_estudos()
    if df.empty:
        st.warning("Estude para ver gráficos!")
    else:
        total_h = df["Minutos"].sum() / 60
        questoes = df["Qtd_Questões"].sum()
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card'><h3>{total_h:.1f}h</h3><p>Horas</p></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><h3>{questoes}</h3><p>Questões</p></div>", unsafe_allow_html=True)
        st.write("")
        chart = alt.Chart(df).mark_bar().encode(x='Data', y='Qtd_Questões', color='Materia').properties(height=250)
        st.altair_chart(chart, use_container_width=True)

# ABA 2: CRONÔMETRO (CORRIGIDO)
with tab2:
    st.markdown("### 🍅 Modo Pomodoro")
    materia_foco = st.selectbox("Matéria:", config['materias'], key="sel_foco")
    placeholder = st.empty() # Lugar onde o tempo aparece
    state = st.session_state.cronometro
    
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    
    if c_btn1.button("▶️", use_container_width=True):
        state['ativo'] = True
        state['inicio'] = time.time() - state['acumulado']
        st.rerun()
    if c_btn2.button("⏸️", use_container_width=True):
        state['ativo'] = False
        state['acumulado'] = time.time() - state['inicio']
        st.rerun()
    if c_btn3.button("💾", use_container_width=True):
        tempo_final = time.time() - state['inicio'] if state['ativo'] else state['acumulado']
        minutos = tempo_final / 60
        if minutos > 0.1:
            salvar_sessao(materia_foco, minutos, 0, 0)
            st.success("Salvo!")
            time.sleep(2)
        state['ativo'] = False; state['acumulado'] = 0; st.rerun()

    # Lógica de atualização
    if state['ativo']:
        tempo = time.time() - state['inicio']
        m, s = divmod(int(tempo), 60); h, m = divmod(m, 60)
        placeholder.markdown(f"<div style='text-align:center; font-size:60px; color:#8E44AD;'>{h:02d}:{m:02d}:{s:02d}</div>", unsafe_allow_html=True)
        time.sleep(1) # Espera 1s
        st.rerun()    # Força atualização
    else:
        tempo = state['acumulado']
        m, s = divmod(int(tempo), 60); h, m = divmod(m, 60)
        placeholder.markdown(f"<div style='text-align:center; font-size:60px; color:gray;'>{h:02d}:{m:02d}:{s:02d}</div>", unsafe_allow_html=True)

# ABA 3: SIMULADO COM DEBUG
with tab3:
    st.markdown("### 🤖 Gerador")
    if not IA_DISPONIVEL:
        st.error(f"⚠️ Erro na Conexão IA: {ERRO_IA_DETALHE}")
        st.info("Verifique seus Secrets no painel 'Manage App'.")
    else:
        topic = st.selectbox("Tópico:", config['materias'], key="sim_topic")
        if st.button("Gerar Questão"):
            prompt = f"Crie 1 questão difícil de múltipla escolha sobre {topic}, banca {config['banca']}. JSON: {{pergunta, opcoes, correta, comentario}}"
            try:
                with st.spinner("Pensando..."):
                    resp = modelo.generate_content(prompt)
                    try:
                        q = json.loads(resp.text.replace("```json", "").replace("```", ""))
                        st.session_state.questao_atual = q
                    except:
                        st.error("IA gerou formato inválido. Tente de novo.")
            except Exception as e:
                st.error(f"Erro ao chamar Gemini: {e}")

        if 'questao_atual' in st.session_state:
            q = st.session_state.questao_atual
            st.info(q.get('pergunta', ''))
            escolha = st.radio("Resp:", q.get('opcoes', []), key="radio_resp")
            if st.button("Conferir"):
                if escolha.split(")")[0] == q.get('correta'):
                    st.success("ACERTOU!"); st.balloons()
                    salvar_sessao(topic, 5, 1, 1)
                else: st.error(f"Errou! Correta: {q.get('correta')}")
                st.write(q.get('comentario'))

# ABA 4: CONFIG
with tab4:
    with st.form("conf"):
        cargo = st.text_input("Cargo", config.get('cargo'))
        banca = st.text_input("Banca", config.get('banca'))
        dt = st.date_input("Data")
        mats = st.text_area("Matérias (separar por vírgula)", ", ".join(config['materias']))
        if st.form_submit_button("Salvar"):
            salvar_config([x.strip() for x in mats.split(",")], dt, banca, cargo)
            st.rerun()
    if st.button("🗑️ Resetar App"):
        if os.path.exists(ARQUIVO_ESTUDOS): os.remove(ARQUIVO_ESTUDOS)
        st.rerun()
