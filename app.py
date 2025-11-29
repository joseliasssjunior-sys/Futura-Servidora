import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import time
import os
import json
import random

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="TJ-MS | Painel Premium", page_icon="⚖️", layout="wide")

# --- 2. ESTILO CSS PROFISSIONAL ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #f8f9fa; }

    /* CARD DE PERFIL */
    .profile-card {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        padding: 20px; border-radius: 20px; color: white; text-align: center;
        box-shadow: 0 10px 20px rgba(37, 117, 252, 0.2); margin-bottom: 20px;
    }
    .profile-level { font-size: 12px; text-transform: uppercase; letter-spacing: 2px; opacity: 0.8; }
    .profile-xp { font-size: 36px; font-weight: 700; margin: 10px 0; }
    .profile-currency { background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 50px; font-size: 14px; }

    /* CRONÔMETRO */
    .timer-box {
        background-color: white; border: 2px solid #e0e0e0; border-radius: 20px;
        padding: 30px; text-align: center; box-shadow: 5px 5px 15px rgba(0,0,0,0.05); margin: 20px 0;
    }
    .timer-display {
        font-family: 'Courier New', monospace; font-size: 80px; font-weight: bold;
        color: #4B0082; text-shadow: 2px 2px 0px #eee;
    }

    /* LOJA */
    .shop-card {
        background: white; border-radius: 15px; padding: 20px; text-align: center;
        border: 1px solid #f0f0f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: all 0.3s ease; height: 100%;
    }
    .shop-card:hover { transform: translateY(-5px); border-color: #6a11cb; }
    .shop-icon { font-size: 50px; margin-bottom: 10px; }
    .shop-price { color: #2575fc; font-weight: bold; font-size: 18px; }

    /* FRASE MOTIVACIONAL */
    .quote-box {
        background-color: #e8f4fd; border-left: 5px solid #2575fc;
        padding: 15px; border-radius: 5px; margin-bottom: 20px;
        font-style: italic; color: #555;
    }

    .stButton > button { border-radius: 50px; font-weight: 600; text-transform: uppercase; border: none; transition: 0.2s; }
    .stButton > button:hover { transform: scale(1.02); }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #6a11cb, #2575fc); }
</style>
""", unsafe_allow_html=True)

# --- 3. DADOS E LISTAS ---
ARQUIVO_DADOS = "dados_tjms.json"

# BANCO DE FRASES (Adicione quantas quiser aqui!)
FRASES_DO_DIA = [
    "“Tudo posso naquele que me fortalece.” (Filipenses 4:13) 🙏",
    "“Seja forte e corajoso! Não se apavore nem desanime.” (Josué 1:9) 💪",
    "A disciplina é a ponte entre metas e realizações.",
    "“Consagre ao Senhor tudo o que você faz, e os seus planos serão bem-sucedidos.” (Provérbios 16:3)",
    "Estudar é plantar tâmaras: você colhe o doce fruto no futuro. 🌱",
    "O TJ-MS espera por você. Faça a sua parte hoje!",
    "“O Senhor é o meu pastor; de nada terei falta.” (Salmos 23:1)",
    "Não diminua seus sonhos, aumente sua fé e seu esforço.",
    "A dor do estudo é temporária, o cargo é para sempre. ⚖️",
    "“Mil cairão ao teu lado, dez mil à tua direita, mas tu não serás atingido.” (Salmos 91:7)",
    "Foco, Força e Fé. Sua toga está te esperando.",
    "“Tudo tem o seu tempo determinado, e há tempo para todo o propósito debaixo do céu.” (Eclesiastes 3:1)"
]

TEMPLATE_TJMS = {
    "config": {"nome": "Concurseira", "cargo": "TJ-MS"},
    "wallet": {"xp": 0, "nivel": 1},
    "recompensas": [
        {"item": "🍫 Chocolate", "custo": 60, "icon": "🍫"},
        {"item": "💆‍♀️ Massagem", "custo": 300, "icon": "💆‍♀️"},
        {"item": "🍿 Cinema", "custo": 400, "icon": "🍿"},
        {"item": "🍣 Jantar Japa", "custo": 1200, "icon": "🍣"},
        {"item": "💅 Manicure", "custo": 800, "icon": "💅"}
    ],
    "edital": {
        "Português": ["Ortografia", "Crase", "Sintaxe", "Pontuação", "Interpretação"],
        "D. Constitucional": ["Art. 5º", "Poderes", "Funções Essenciais", "Adm. Pública"],
        "D. Administrativo": ["Atos", "Poderes", "Improbidade", "Licitação (Lei 14.133)"],
        "Proc. Civil": ["Prazos", "Recursos", "Tutelas", "Audiências"],
        "Legislação MS": ["Regimento Interno", "Estatuto Servidores"]
    },
    "progresso_edital": {}, "revisoes": []
}

def carregar_dados():
    if not os.path.exists(ARQUIVO_DADOS): salvar_dados(TEMPLATE_TJMS); return TEMPLATE_TJMS
    try:
        with open(ARQUIVO_DADOS, "r", encoding='utf-8') as f: return json.load(f)
    except: return TEMPLATE_TJMS

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding='utf-8') as f: json.dump(dados, f, ensure_ascii=False, indent=4)

def adicionar_xp(dados, minutos):
    ganho = int(minutos)
    dados['wallet']['xp'] += ganho
    novo_nivel = (dados['wallet']['xp'] // 1000) + 1
    msg = ""
    if novo_nivel > dados['wallet']['nivel']:
        dados['wallet']['nivel'] = novo_nivel
        msg = f"🆙 LEVEL UP! NÍVEL {novo_nivel}!"
    salvar_dados(dados)
    return ganho, msg

def get_revisoes(dados):
    hoje = str(date.today())
    return [r for r in dados['revisoes'] if r['data'] <= hoje and not r['feito']]

# --- 4. INTERFACE ---
if 'cronometro' not in st.session_state: st.session_state.cronometro = {'ativo': False, 'inicio': None, 'acumulado': 0}
if 'frase_atual' not in st.session_state: st.session_state.frase_atual = random.choice(FRASES_DO_DIA)

stt = st.session_state.cronometro
dados = carregar_dados()

# SIDEBAR
with st.sidebar:
    st.markdown(f"""
    <div class="profile-card">
        <div class="profile-level">Nível {dados['wallet']['nivel']}</div>
        <div class="profile-xp">{dados['wallet']['xp']}</div>
        <span class="profile-currency">🪙 Estaloquecas</span>
    </div>
    """, unsafe_allow_html=True)
    total = sum(len(v) for v in dados['edital'].values())
    feito = sum(len(v) for v in dados['progresso_edital'].values())
    pct = feito / total if total > 0 else 0
    st.caption(f"Progresso do Edital ({int(pct*100)}%)")
    st.progress(pct)

# HEADER COM FRASE RANDÔMICA
st.markdown(f"### Olá, {dados['config']['nome']}! 👋")
st.markdown(f"""
<div class="quote-box">
    {st.session_state.frase_atual}
</div>
""", unsafe_allow_html=True)

# ABAS
tab1, tab2, tab3, tab4 = st.tabs(["⏱️ Estudar", "📋 Edital", "🛍️ Loja", "⚙️ Config"])

# ABA 1: FOCO
with tab1:
    revs = get_revisoes(dados)
    if revs:
        st.warning(f"⚠️ {len(revs)} revisões pendentes!")
        for i, r in enumerate(revs):
            c1, c2 = st.columns([0.8, 0.2])
            c1.markdown(f"**Revisar:** {r['assunto']}")
            if c2.button("✅ OK", key=f"ok_{i}"):
                dados['revisoes'][dados['revisoes'].index(r)]['feito'] = True
                adicionar_xp(dados, 15)
                st.toast("Revisada! +15 XP", icon="🔥"); time.sleep(1); st.rerun()

    st.markdown('<div class="timer-box">', unsafe_allow_html=True)
    tempo = time.time() - stt['inicio'] if stt['ativo'] else stt['acumulado']
    m, s = divmod(int(tempo), 60); h, m = divmod(m, 60)
    st.markdown(f'<div class="timer-display">{h:02d}:{m:02d}:{s:02d}</div>', unsafe_allow_html=True)
    
    c_sel, c_top = st.columns(2)
    mat = c_sel.selectbox("Matéria", list(dados['edital'].keys()), label_visibility="collapsed")
    topico = c_top.text_input("Assunto (Opcional)", placeholder="Ex: Crase", label_visibility="collapsed")
    
    b1, b2, b3 = st.columns([1,1,2])
    if b1.button("▶️", use_container_width=True): stt['ativo'] = True; stt['inicio'] = time.time() - stt['acumulado']; st.rerun()
    if b2.button("⏸️", use_container_width=True): stt['ativo'] = False; stt['acumulado'] = time.time() - stt['inicio']; st.rerun()
    if b3.button("💾 SALVAR SESSÃO", use_container_width=True, type="primary"):
        mins = (time.time() - stt['inicio'] if stt['ativo'] else stt['acumulado']) / 60
        if mins > 0.5:
            xp, msg_lvl = adicionar_xp(dados, mins)
            if topico: 
                hoje = date.today()
                dados['revisoes'].extend([{"assunto": f"{mat}: {topico}", "data": str(hoje + timedelta(days=1)), "feito": False},
                                          {"assunto": f"{mat}: {topico}", "data": str(hoje + timedelta(days=7)), "feito": False}])
                salvar_dados(dados)
            st.toast(f"+{xp} Estaloquecas!", icon="💰")
            if msg_lvl: st.balloons(); st.success(msg_lvl)
            stt['ativo']=False; stt['acumulado']=0; st.session_state.frase_atual = random.choice(FRASES_DO_DIA); time.sleep(1); st.rerun()
        else: st.toast("Tempo muito curto.", icon="❌")
    st.markdown('</div>', unsafe_allow_html=True)
    if stt['ativo']: time.sleep(1); st.rerun()

# ABA 2: EDITAL
with tab2:
    st.subheader("Mapa da Aprovação")
    col1, col2 = st.columns(2)
    itens = list(dados['edital'].items()); metade = len(itens)//2
    for idx, (materia, topicos) in enumerate(itens):
        coluna = col1 if idx < metade else col2
        with coluna:
            feitos = dados['progresso_edital'].get(materia, [])
            prog = len(feitos)/len(topicos) if topicos else 0
            with st.expander(f"{materia} ({int(prog*100)}%)"):
                st.progress(prog)
                for t in topicos:
                    chk = st.checkbox(t, value=(t in feitos), key=f"{materia}_{t}")
                    if chk and t not in feitos:
                        if materia not in dados['progresso_edital']: dados['progresso_edital'][materia] = []
                        dados['progresso_edital'][materia].append(t); adicionar_xp(dados, 10); st.toast("+10 XP!", icon="📚"); st.rerun()
                    elif not chk and t in feitos:
                        dados['progresso_edital'][materia].remove(t); salvar_dados(dados); st.rerun()

# ABA 3: LOJA
with tab3:
    st.subheader("Recompensas")
    cols = st.columns(3)
    for i, item in enumerate(dados['recompensas']):
        with cols[i % 3]:
            st.markdown(f"""<div class="shop-card"><div class="shop-icon">{item['icon']}</div><h4>{item['item']}</h4><div class="shop-price">{item['custo']} 🪙</div></div>""", unsafe_allow_html=True)
            if st.button("Resgatar", key=f"buy_{i}", use_container_width=True):
                if dados['wallet']['xp'] >= item['custo']:
                    dados['wallet']['xp'] -= item['custo']; salvar_dados(dados); st.balloons(); st.toast(f"Comprou: {item['item']}", icon="🎉"); time.sleep(2); st.rerun()
                else: st.toast("Saldo insuficiente!", icon="💸")

# ABA 4: CONFIG
with tab4:
    st.subheader("Configurações")
    with st.expander("📝 Editar Edital"):
        sel_m = st.selectbox("Matéria:", list(dados['edital'].keys()))
        txt = st.text_area("Tópicos", ", ".join(dados['edital'][sel_m]))
        if st.button("Salvar Edital"): dados['edital'][sel_m] = [x.strip() for x in txt.split(",") if x.strip()]; salvar_dados(dados); st.rerun()
    if st.button("⚠️ Resetar Sistema"):
        if os.path.exists(ARQUIVO_DADOS): os.remove(ARQUIVO_DADOS); st.rerun()