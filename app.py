import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date
import time
import os
import random
import json
import google.generativeai as genai
from pypdf import PdfReader

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Futura Servidora", page_icon="⚖️", layout="wide")

# --- 2. CONEXÃO IA ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel('gemini-1.5-flash')
    IA_DISPONIVEL = True
except:
    IA_DISPONIVEL = False

# ARQUIVOS DE DADOS
ARQUIVO_ESTUDOS = "historico_estudos.csv"
ARQUIVO_CONFIG = "config_concurso.json"

# --- 3. FUNÇÕES DE DADOS ---
def carregar_config():
    if os.path.exists(ARQUIVO_CONFIG):
        with open(ARQUIVO_CONFIG, "r") as f:
            return json.load(f)
    return {
        "materias": ["Português", "Direito Constitucional", "Direito Administrativo"], 
        "data_prova": str(date.today()),
        "banca": "FGV", # Padrão
        "cargo": "Analista Judiciário"
    }

def salvar_config(materias, data_prova, banca, cargo):
    dados = {"materias": materias, "data_prova": str(data_prova), "banca": banca, "cargo": cargo}
    with open(ARQUIVO_CONFIG, "w") as f:
        json.dump(dados, f)

def carregar_estudos():
    if not os.path.exists(ARQUIVO_ESTUDOS):
        df = pd.DataFrame(columns=["Data", "Materia", "Minutos", "Qtd_Questões", "Acertos"])
        df.to_csv(ARQUIVO_ESTUDOS, index=False)
        return df
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
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO_ESTUDOS, index=False)

# --- 4. FUNÇÕES DE IA ESTRATÉGICA ---

def gerar_analise_estrategica(banca, cargo, materia):
    if not IA_DISPONIVEL: return "IA não conectada."
    
    prompt = f"""
    Atue como um Mentora de Concursos de Alto Nível especializada na banca {banca}.
    O aluno está estudando para o cargo de {cargo}.
    
    Faça uma análise estratégica da matéria: {materia}.
    
    Eu quero que você me entregue:
    1. **O Estilo da Banca:** Como a {banca} cobra essa matéria? (Ex: cobra muita lei seca? Doutrina? Jurisprudência? Textos longos?).
    2. **Top 3 Assuntos Quentes:** Quais são os 3 tópicos que SEMPRE caem para esse cargo?
    3. **A Pegadinha:** Qual é a armadilha comum dessa banca nessa matéria?
    4. **Dica de Ouro:** Uma estratégia prática para gabaritar.
    
    Use formatação bonita (Negrito, Tópicos, Emojis). Seja direta e técnica.
    """
    try:
        resp = modelo.generate_content(prompt)
        return resp.text
    except: return "Erro ao gerar estratégia."

def analisar_edital_completo(arquivo):
    if not IA_DISPONIVEL: return None
    leitor = PdfReader(arquivo)
    texto = ""
    for pag in leitor.pages[:20]: texto += pag.extract_text()
    
    prompt = f"""
    Analise o texto deste Edital. Extraia em JSON:
    1. "banca": Nome da banca.
    2. "cargo": Cargo principal.
    3. "materias": Lista de disciplinas.
    Responda APENAS JSON. Texto: {texto[:40000]}
    """
    try:
        resp = modelo.generate_content(prompt)
        return json.loads(resp.text.replace("```json", "").replace("```", ""))
    except: return None

def gerar_simulado(banca, cargo, materia, qtd):
    if not IA_DISPONIVEL: return []
    prompt = f"""
    Crie um simulado de {qtd} questões de múltipla escolha sobre {materia}, estilo banca {banca}, cargo {cargo}.
    Nível difícil.
    Retorne JSON: [{{ "pergunta": "...", "opcoes": ["A)...", "B)..."], "correta": "A", "comentario": "..." }}]
    """
    try:
        resp = modelo.generate_content(prompt)
        return json.loads(resp.text.replace("```json", "").replace("```", ""))
    except: return []

# --- 5. INTERFACE ---

# Variáveis de Estado
if 'cronometro' not in st.session_state: st.session_state.cronometro = {'ativo': False, 'inicio': None, 'acumulado': 0, 'materia': None}
if 'estrategia_cache' not in st.session_state: st.session_state.estrategia_cache = {}

config = carregar_config()

# HEADER
st.title(f"👩‍⚖️ Painel da Aprovação | {config.get('cargo', 'Concurseira')}")
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown(f"**Foco Total na Banca:** <span style='color:#E74C3C; font-size:20px; font-weight:bold;'>{config.get('banca', 'Não definida')}</span>", unsafe_allow_html=True)
with c2:
    try:
        dias = (datetime.strptime(config['data_prova'], "%Y-%m-%d").date() - date.today()).days
        if dias >= 0: st.metric("Dias para a Prova", dias)
        else: st.error("A prova já passou!")
    except: st.warning("Configure a data")

# ABAS
tab_dash, tab_strat, tab_foco, tab_sim, tab_config = st.tabs([
    "📊 Dashboard Geral",
    "🎯 Pontos Estratégicos", 
    "⏱️ Modo Foco", 
    "📝 Simulador IA", 
    "⚙️ Ajustes"
])

# --- ABA 1: DASHBOARD (VISÃO GERAL) ---
with tab_dash:
    df = carregar_estudos()
    
    if df.empty:
        st.info("Comece a estudar para ver seus dados aqui!")
    else:
        # Métricas de Topo
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        
        total_horas = df["Minutos"].sum() / 60
        questoes_totais = df["Qtd_Questões"].sum()
        acertos_totais = df["Acertos"].sum()
        media_geral = (acertos_totais / questoes_totais * 100) if questoes_totais > 0 else 0
        
        col_kpi1.metric("Horas Líquidas", f"{total_horas:.1f}h")
        col_kpi2.metric("Questões Feitas", questoes_totais)
        col_kpi3.metric("Acertos", acertos_totais)
        col_kpi4.metric("Taxa de Acerto", f"{media_geral:.1f}%", delta_color="normal")
        
        st.divider()
        
        # Gráficos Lado a Lado
        g1, g2 = st.columns(2)
        
        with g1:
            st.markdown("### 🕒 Onde você gasta seu tempo?")
            chart_pizza = alt.Chart(df).mark_arc(innerRadius=60).encode(
                theta="sum(Minutos)",
                color=alt.Color("Materia", legend=alt.Legend(title="Disciplinas")),
                tooltip=["Materia", "sum(Minutos)"]
            ).properties(height=350)
            st.altair_chart(chart_pizza, use_container_width=True)
            
        with g2:
            st.markdown("### 🧠 Qualidade do Estudo (Acertos)")
            # Calcula % por matéria
            df_group = df.groupby("Materia")[["Qtd_Questões", "Acertos"]].sum().reset_index()
            df_group["Taxa"] = (df_group["Acertos"] / df_group["Qtd_Questões"] * 100).fillna(0)
            
            chart_bar = alt.Chart(df_group).mark_bar().encode(
                x=alt.X("Taxa", title="% de Acertos", scale=alt.Scale(domain=[0, 100])),
                y=alt.Y("Materia", sort="-x"),
                color=alt.condition(
                    alt.datum.Taxa > 80,
                    alt.value("#2ECC71"),  # Verde (Excelente)
                    alt.value("#E74C3C")   # Vermelho (Atenção)
                ),
                tooltip=["Materia", "Taxa", "Qtd_Questões"]
            ).properties(height=350)
            st.altair_chart(chart_bar, use_container_width=True)

# --- ABA 2: PONTOS ESTRATÉGICOS (A NOVA FUNÇÃO) ---
with tab_strat:
    st.header(f"🕵️‍♂️ Raio-X da {config.get('banca', 'Banca')}")
    st.markdown("Descubra o que a IA analisou sobre o perfil da banca para o seu cargo.")
    
    col_sel, col_btn = st.columns([3, 1])
    materia_analise = col_sel.selectbox("Qual matéria você quer hackear?", config['materias'])
    
    # Botão para gerar (ou buscar do cache para não gastar IA a toa)
    if col_btn.button("🔍 Gerar Estratégia"):
        with st.spinner(f"Analisando provas anteriores da {config.get('banca')}..."):
            analise = gerar_analise_estrategica(config.get('banca', 'Genérica'), config.get('cargo', 'Geral'), materia_analise)
            st.session_state.estrategia_cache[materia_analise] = analise
    
    # Mostra o resultado
    if materia_analise in st.session_state.estrategia_cache:
        st.markdown("---")
        st.markdown(st.session_state.estrategia_cache[materia_analise])
        st.info("💡 Dica: Salve essas informações no seu caderno de resumo!")
    else:
        st.info("Selecione uma matéria e clique em Gerar para ver a inteligência.")

# --- ABA 3: MODO FOCO ---
with tab_foco:
    st.markdown("### Cronômetro de Estudos")
    c1, c2 = st.columns([1, 2])
    with c1:
        m_foco = st.selectbox("Matéria", config['materias'], key="foco_mat")
    with c2:
        state = st.session_state.cronometro
        tempo = state['acumulado'] + (time.time() - state['inicio'] if state['ativo'] else 0)
        if state['ativo']: time.sleep(1); st.rerun()
        
        m, s = divmod(int(tempo), 60)
        h, m = divmod(m, 60)
        st.markdown(f"<div style='font-size:50px; font-weight:bold; color:#2980B9;'>{h:02d}:{m:02d}:{s:02d}</div>", unsafe_allow_html=True)

    b1, b2, b3 = st.columns(3)
    if b1.button("▶️ INICIAR"): state['ativo']=True; state['inicio']=time.time(); st.rerun()
    if b2.button("⏸️ PAUSAR"): state['ativo']=False; state['acumulado']+=time.time()-state['inicio']; st.rerun()
    if b3.button("⏹️ SALVAR"):
        minutos = state['acumulado']/60
        if minutos > 1:
            salvar_sessao(m_foco, minutos, 0, 0)
            st.success("Salvo!"); st.balloons()
        state['acumulado']=0; state['ativo']=False; st.rerun()

# --- ABA 4: SIMULADOR ---
with tab_sim:
    st.markdown("### 📝 Treinamento Intensivo")
    if 'questoes' not in st.session_state: st.session_state.questoes = []
    
    c_s1, c_s2 = st.columns(2)
    s_mat = c_s1.selectbox("Matéria", config['materias'], key="sim_mat")
    s_qtd = c_s2.slider("Qtd Questões", 3, 10, 5)
    
    if st.button("Gerar Questões Inéditas"):
        with st.spinner("Criando caderno de questões..."):
            st.session_state.questoes = gerar_simulado(config.get('banca'), config.get('cargo'), s_mat, s_qtd)
    
    if st.session_state.questoes:
        form = st.form("simulado_form")
        respostas = {}
        for i, q in enumerate(st.session_state.questoes):
            form.markdown(f"**{i+1}) {q['pergunta']}**")
            respostas[i] = form.radio(f"Resp {i+1}", q['opcoes'], key=f"q_{i}")
            form.markdown("---")
        
        if form.form_submit_button("Corrigir"):
            acertos = 0
            for i, q in enumerate(st.session_state.questoes):
                letra_user = respostas[i].split(")")[0]
                if letra_user == q['correta']:
                    acertos += 1
                    st.success(f"Q{i+1}: Correta! ✅")
                else:
                    st.error(f"Q{i+1}: Errou ❌ (Correta: {q['correta']})")
                with st.expander("Ver Comentário"): st.write(q['comentario'])
            
            nota = (acertos/len(st.session_state.questoes))*100
            st.metric("Resultado", f"{nota:.0f}%")
            salvar_sessao(s_mat, 15, len(st.session_state.questoes), acertos)

# --- ABA 5: CONFIGURAÇÕES ---
with tab_config:
    st.header("⚙️ Configurações do Concurso")
    
    # Upload Inteligente
    arquivo = st.file_uploader("Upload do Edital (PDF)", type="pdf")
    if arquivo and st.button("Ler Edital com IA"):
        with st.spinner("Lendo..."):
            dados = analisar_edital_completo(arquivo)
            if dados:
                salvar_config(dados['materias'], config['data_prova'], dados['banca'], dados['cargo'])
                st.success(f"Configurado para {dados['banca']} - {dados['cargo']}!")
                st.rerun()
    
    st.divider()
    
    # Edição Manual
    c_conf1, c_conf2, c_conf3 = st.columns(3)
    banca_man = c_conf1.text_input("Banca", config.get('banca', ''))
    cargo_man = c_conf2.text_input("Cargo", config.get('cargo', ''))
    data_man = c_conf3.date_input("Data da Prova", datetime.strptime(config['data_prova'], "%Y-%m-%d"))
    
    df_mat = pd.DataFrame(config['materias'], columns=["Materia"])
    edit_mat = st.data_editor(df_mat, num_rows="dynamic")
    
    if st.button("Salvar Manualmente"):
        salvar_config(edit_mat["Materia"].tolist(), data_man, banca_man, cargo_man)
        st.success("Salvo!")
