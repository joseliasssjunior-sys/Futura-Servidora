import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date
import time
import os
import json
import google.generativeai as genai

# --- 1. CONFIGURAÇÃO DA PÁGINA (WIDE + ÍCONE) ---
st.set_page_config(page_title="Futura Servidora", page_icon="⚖️", layout="wide")

# --- CSS PERSONALIZADO (A MÁGICA DO VISUAL) ---
st.markdown("""
<style>
    /* Esconde o menu padrão e rodapé para parecer app nativo */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Estilo dos Cards de Métricas */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    /* Título Mobile Friendly */
    h1 {
        text-align: center;
        color: #8E44AD;
        font-family: 'Helvetica', sans-serif;
        font-size: 2.5rem !important; 
    }
    
    /* Ajuste de botões */
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 50px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CONEXÃO COM A IA ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel('gemini-1.5-flash')
    IA_DISPONIVEL = True
except:
    IA_DISPONIVEL = False

# ARQUIVOS
ARQUIVO_ESTUDOS = "historico_estudos.csv"
ARQUIVO_CONFIG = "config_concurso.json"

# --- 3. FUNÇÕES (MANTIDAS, MAS SIMPLIFICADAS) ---
def carregar_config():
    if os.path.exists(ARQUIVO_CONFIG):
        with open(ARQUIVO_CONFIG, "r") as f: return json.load(f)
    # Configuração padrão inicial
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

# --- 4. INTERFACE NOVA ---

if 'cronometro' not in st.session_state: st.session_state.cronometro = {'ativo': False, 'inicio': None, 'acumulado': 0}
config = carregar_config()

# --- CABEÇALHO LIMPO E CENTRALIZADO ---
st.markdown(f"<h1>⚖️ Painel da Aprovação</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align: center; color: gray; margin-top: -20px;'>{config['cargo']} | {config['banca']}</h3>", unsafe_allow_html=True)

# Cálculo de Dias (Correção do BUG do Zero)
try:
    data_prova = datetime.strptime(config['data_prova'], "%Y-%m-%d").date()
    hoje = date.today()
    dias = (data_prova - hoje).days
    
    if dias < 0: msg_dias = "🏁 A prova já passou!"
    elif dias == 0: msg_dias = "🔥 É HOJE! BOA SORTE!"
    else: msg_dias = f"📅 Faltam **{dias}** dias"
except:
    msg_dias = "⚙️ Configure a data"

st.info(msg_dias, icon="⏳")

# --- ABAS COM ÍCONES ---
# Usamos nomes curtos para caber no celular
tab1, tab2, tab3, tab4 = st.tabs(["📊 Painel", "⏱️ Foco", "📝 Simulado", "⚙️ Config"])

# --- ABA 1: DASHBOARD VISUAL ---
with tab1:
    df = carregar_estudos()
    if df.empty:
        st.warning("Comece a estudar para ver seus gráficos aqui!")
    else:
        # Métricas em Cards (Melhor para mobile)
        total_h = df["Minutos"].sum() / 60
        questoes = df["Qtd_Questões"].sum()
        
        # Layout de colunas para métricas
        col_m1, col_m2 = st.columns(2)
        col_m1.markdown(f"<div class='metric-card'><h3>{total_h:.1f}h</h3><p>Horas Líquidas</p></div>", unsafe_allow_html=True)
        col_m2.markdown(f"<div class='metric-card'><h3>{questoes}</h3><p>Questões Feitas</p></div>", unsafe_allow_html=True)
        
        st.write("") # Espaço
        
        # Gráfico Simplificado
        st.caption("Evolução de Questões")
        chart = alt.Chart(df).mark_bar().encode(
            x='Data', y='Qtd_Questões', color='Materia'
        ).properties(height=250) # Altura menor para celular
        st.altair_chart(chart, use_container_width=True)

# --- ABA 2: CRONÔMETRO GIGANTE ---
with tab2:
    st.markdown("### 🍅 Modo Pomodoro")
    materia_foco = st.selectbox("Vou estudar:", config['materias'])
    
    state = st.session_state.cronometro
    
    # Lógica do tempo
    if state['ativo']:
        decorrido = time.time() - state['inicio']
        tempo_total = state['acumulado'] + decorrido
        time.sleep(1) # Atualiza a cada segundo
        st.rerun()
    else:
        tempo_total = state['acumulado']
        
    # Formata o relógio
    m, s = divmod(int(tempo_total), 60)
    h, m = divmod(m, 60)
    
    # RELÓGIO GIGANTE CENTRALIZADO
    st.markdown(f"""
    <div style='text-align: center; font-size: 80px; font-weight: bold; color: #8E44AD; margin: 20px 0;'>
        {h:02d}:{m:02d}:{s:02d}
    </div>
    """, unsafe_allow_html=True)
    
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    if c_btn1.button("▶️ INICIAR"):
        state['ativo'] = True
        state['inicio'] = time.time()
        st.rerun()
        
    if c_btn2.button("⏸️ PAUSAR"):
        if state['ativo']:
            state['acumulado'] += time.time() - state['inicio']
            state['ativo'] = False
        st.rerun()
        
    if c_btn3.button("💾 SALVAR"):
        minutos = tempo_total / 60
        if minutos > 1:
            salvar_sessao(materia_foco, minutos, 0, 0)
            state['acumulado'] = 0
            state['ativo'] = False
            st.balloons()
            st.success("Salvo com sucesso!")
            time.sleep(2)
            st.rerun()
        else:
            st.error("Estude pelo menos 1 minuto!")

# --- ABA 3: SIMULADOR IA (Simplificado) ---
with tab3:
    st.markdown("### 🤖 Gerador de Questões")
    if not IA_DISPONIVEL:
        st.error("IA não conectada. Configure a API Key no .streamlit/secrets.toml")
    else:
        topic = st.selectbox("Tópico:", config['materias'], key="sim_topic")
        if st.button("Gerar Questão Rápida"):
            prompt = f"Crie 1 questão difícil de múltipla escolha (A,B,C,D,E) sobre {topic} banca {config['banca']}. Formato JSON: {{pergunta, opcoes, correta, comentario}}"
            try:
                with st.spinner("IA pensando..."):
                    resp = modelo.generate_content(prompt)
                    # Tratamento simples para garantir JSON
                    txt = resp.text.replace("```json", "").replace("```", "")
                    q = json.loads(txt)
                    
                    # Salva no estado para não sumir
                    st.session_state.questao_atual = q
            except:
                st.error("Erro na IA. Tente de novo.")

        # Exibir Questão
        if 'questao_atual' in st.session_state:
            q = st.session_state.questao_atual
            st.info(q.get('pergunta', ''))
            
            escolha = st.radio("Sua resposta:", q.get('opcoes', []), key="radio_resp")
            
            if st.button("Conferir Resposta"):
                letra = escolha.split(")")[0] if escolha else ""
                if letra == q.get('correta'):
                    st.success("✅ ACERTOU!")
                    st.balloons()
                    salvar_sessao(topic, 5, 1, 1) # Salva 5 min e 1 acerto
                else:
                    st.error(f"❌ Errou! Era a letra {q.get('correta')}")
                
                with st.expander("Ver explicação"):
                    st.write(q.get('comentario'))

# --- ABA 4: CONFIGURAÇÕES ---
with tab4:
    st.markdown("### ⚙️ Ajustes")
    
    with st.form("config_form"):
        novo_cargo = st.text_input("Cargo Alvo", config.get('cargo'))
        nova_banca = st.text_input("Banca", config.get('banca'))
        nova_data = st.date_input("Data da Prova")
        
        # Editor de Matérias (Simples texto separado por vírgula para mobile)
        materias_str = st.text_area("Matérias (separe por vírgula)", ", ".join(config['materias']))
        
        if st.form_submit_button("Salvar Tudo"):
            lista_mat = [x.strip() for x in materias_str.split(",")]
            salvar_config(lista_mat, nova_data, nova_banca, novo_cargo)
            st.success("Configurações atualizadas!")
            time.sleep(1)
            st.rerun()

    # Botão de Reset (Cuidado)
    if st.checkbox("Mostrar Área de Perigo"):
        if st.button("🗑️ Apagar Todo Histórico"):
            if os.path.exists(ARQUIVO_ESTUDOS):
                os.remove(ARQUIVO_ESTUDOS)
                st.rerun()
