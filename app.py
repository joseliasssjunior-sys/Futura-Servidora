import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import time
import os
import json
import random

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Painel TJ-MS", page_icon="⚖️", layout="wide")

# Estilos CSS para Gamificação e Visual Limpo
st.markdown("""
<style>
    /* Esconde menu padrão */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Card de XP */
    .xp-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    .xp-valor { font-size: 40px; font-weight: bold; }
    .xp-label { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Card de Recompensa */
    .reward-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        transition: transform 0.2s;
    }
    .reward-card:hover { transform: scale(1.02); border-color: #764ba2; }
    
    /* Barra de Progresso do Edital */
    .stProgress > div > div > div > div {
        background-color: #764ba2;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. GERENCIAMENTO DE DADOS (JSON) ---
ARQUIVO_DADOS = "dados_tjms.json"

# Template inicial do TJ-MS (Pode editar depois)
TEMPLATE_TJMS = {
    "config": {"nome": "Futura Servidora", "cargo": "Analista/Técnico TJ-MS"},
    "wallet": {"xp": 0, "nivel": 1},
    "recompensas": [
        {"item": "🍫 Chocolate/Doce", "custo": 60, "icon": "🍫"},
        {"item": "💆‍♀️ Massagem (15min)", "custo": 300, "icon": "💆‍♀️"},
        {"item": "🍕 Pedir Pizza/Japa", "custo": 1200, "icon": "🍣"},
        {"item": "🎬 Cinema/Série s/ Culpa", "custo": 400, "icon": "🍿"},
        {"item": "💅 Vale Manicure", "custo": 800, "icon": "💅"}
    ],
    "edital": {
        "Língua Portuguesa": ["Ortografia Oficial", "Acentuação", "Crase", "Sintaxe", "Interpretação de Texto", "Pontuação"],
        "Direito Constitucional": ["Direitos e Garantias Fundamentais", "Organização do Estado", "Poder Judiciário", "Funções Essenciais à Justiça"],
        "Direito Administrativo": ["Princípios", "Atos Administrativos", "Poderes", "Responsabilidade Civil", "Improbidade (Lei 8.429)"],
        "Processo Civil": ["Prazos Processuais", "Atos Processuais", "Tutelas Provisórias", "Recursos"],
        "Processo Penal": ["Inquérito Policial", "Ação Penal", "Provas", "Prisão e Liberdade Provisória"],
        "Legislação Específica": ["Regimento Interno TJ-MS", "Estatuto dos Servidores MS"]
    },
    "progresso_edital": {}, # Guarda o que já foi ticado: {"Língua Portuguesa": ["Crase"]}
    "revisoes": [] # Lista de revisões agendadas: {"assunto": "Crase", "data": "2023-10-20"}
}

def carregar_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        salvar_dados(TEMPLATE_TJMS)
        return TEMPLATE_TJMS
    with open(ARQUIVO_DADOS, "r", encoding='utf-8') as f:
        return json.load(f)

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# --- 3. LÓGICA DE NEGÓCIO ---

def adicionar_xp(dados, minutos):
    # 1 minuto = 1 XP (Simples e justo)
    xp_ganho = int(minutos)
    dados['wallet']['xp'] += xp_ganho
    
    # Check de Nível (A cada 1000xp sobe nível)
    novo_nivel = (dados['wallet']['xp'] // 1000) + 1
    msg_nivel = ""
    if novo_nivel > dados['wallet']['nivel']:
        dados['wallet']['nivel'] = novo_nivel
        msg_nivel = f"PARABÉNS! VOCÊ SUBIU PARA O NÍVEL {novo_nivel}! 🚀"
        st.balloons()
        
    salvar_dados(dados)
    return xp_ganho, msg_nivel

def agendar_revisao(dados, assunto):
    # Regra simples: Revisar amanhã (24h) e daqui a 7 dias
    hoje = date.today()
    datas = [hoje + timedelta(days=1), hoje + timedelta(days=7), hoje + timedelta(days=30)]
    
    for d in datas:
        dados['revisoes'].append({"assunto": assunto, "data": str(d), "feito": False})
    salvar_dados(dados)

def get_revisoes_hoje(dados):
    hoje = str(date.today())
    pendentes = [r for r in dados['revisoes'] if r['data'] <= hoje and not r['feito']]
    return pendentes

# --- 4. INTERFACE DO APP ---

dados = carregar_dados()

# SIDEBAR (CARTEIRA E PERFIL)
with st.sidebar:
    st.markdown(f"## 👮‍♀️ {dados['config']['cargo']}")
    
    # Cartão de XP
    st.markdown(f"""
    <div class="xp-card">
        <div class="xp-label">Nível {dados['wallet']['nivel']}</div>
        <div class="xp-valor">💎 {dados['wallet']['xp']}</div>
        <div class="xp-label">Estaloquecas</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    st.write("**Resumo do Edital:**")
    
    # Cálculo total do edital
    total_topicos = sum(len(v) for v in dados['edital'].values())
    total_feitos = sum(len(v) for v in dados['progresso_edital'].values())
    progresso_total = total_feitos / total_topicos if total_topicos > 0 else 0
    
    st.progress(progresso_total)
    st.caption(f"{total_feitos}/{total_topicos} tópicos concluídos ({int(progresso_total*100)}%)")

# ABAS PRINCIPAIS
tab_foco, tab_edital, tab_loja, tab_config = st.tabs(["⏱️ Foco & Revisão", "📋 Edital Verticalizado", "🎁 Banco de Recompensas", "⚙️ Ajustes"])

# --- ABA 1: FOCO E REVISÃO ---
with tab_foco:
    # 1. Alerta de Revisão (Prioridade Máxima)
    revisoes = get_revisoes_hoje(dados)
    if revisoes:
        st.error(f"🚨 **ATENÇÃO:** Você tem {len(revisoes)} revisões acumuladas para hoje!")
        with st.expander("Ver Revisões Pendentes", expanded=True):
            for i, rev in enumerate(revisoes):
                col_r1, col_r2 = st.columns([4, 1])
                col_r1.write(f"📅 {rev['data']} - **{rev['assunto']}**")
                if col_r2.button("✅ Feito", key=f"rev_{i}"):
                    # Marca como feito na lista original
                    idx_real = dados['revisoes'].index(rev)
                    dados['revisoes'][idx_real]['feito'] = True
                    # Ganha XP extra por revisar
                    adicionar_xp(dados, 15) 
                    st.success("+15 XP por revisar!")
                    time.sleep(1)
                    st.rerun()
    else:
        st.success("✨ Tudo em dia! Nenhuma revisão atrasada.")

    st.divider()

    # 2. Cronômetro de Estudo
    st.subheader("🍅 Hora de Estudar")
    
    if 'cronometro' not in st.session_state: 
        st.session_state.cronometro = {'ativo': False, 'inicio': None, 'acumulado': 0}
    stt = st.session_state.cronometro

    col_timer1, col_timer2 = st.columns([1, 1])
    with col_timer1:
        materia_atual = st.selectbox("O que vamos estudar?", list(dados['edital'].keys()))
        topico_livre = st.text_input("Qual assunto específico? (Ex: Crase)", placeholder="Digite o tópico...")

    with col_timer2:
        # Display Relógio
        tempo = time.time()-stt['inicio'] if stt['ativo'] else stt['acumulado']
        m, s = divmod(int(tempo), 60); h, m = divmod(m, 60)
        st.markdown(f"<div style='font-size: 60px; font-weight: bold; color: #4B0082; text-align: center;'>{h:02d}:{m:02d}:{s:02d}</div>", unsafe_allow_html=True)
        
        b1, b2, b3 = st.columns(3)
        if b1.button("▶️ INICIAR", use_container_width=True): stt['ativo']=True; stt['inicio']=time.time()-stt['acumulado']; st.rerun()
        if b2.button("⏸️ PAUSAR", use_container_width=True): stt['ativo']=False; stt['acumulado']=time.time()-stt['inicio']; st.rerun()
        if b3.button("💾 SALVAR", use_container_width=True):
            mins = (time.time()-stt['inicio'] if stt['ativo'] else stt['acumulado'])/60
            if mins > 1: 
                xp, msg = adicionar_xp(dados, mins)
                # Agenda revisão automaticamente se tiver tópico
                if topico_livre: agendar_revisao(dados, f"{materia_atual} - {topico_livre}")
                
                st.balloons()
                st.success(f"Show! +{xp} XP na carteira! {msg}")
                if topico_livre: st.info(f"📅 Revisão agendada para {topico_livre}")
                
                stt['acumulado']=0; stt['ativo']=False; time.sleep(2); st.rerun()
            else:
                st.warning("Tempo muito curto!")

    if stt['ativo']: time.sleep(1); st.rerun()

# --- ABA 2: EDITAL VERTICALIZADO ---
with tab_edital:
    st.header("📋 Controle de Edital")
    st.caption("Marque o que você já dominou. Isso agenda revisões e mostra seu progresso.")
    
    for materia, topicos in dados['edital'].items():
        # Cria um Accordion para cada matéria
        feitos_na_materia = dados['progresso_edital'].get(materia, [])
        progresso = len(feitos_na_materia) / len(topicos) if topicos else 0
        
        with st.expander(f"{materia}  --  {int(progresso*100)}% Concluído"):
            # Barra de progresso visual
            st.progress(progresso)
            
            # Checkboxes
            cols = st.columns(2) # Duas colunas para economizar espaço
            for i, topico in enumerate(topicos):
                is_checked = topico in feitos_na_materia
                # Truque: Usar o label como chave única
                col = cols[i % 2]
                if col.checkbox(topico, value=is_checked, key=f"chk_{materia}_{i}"):
                    if topico not in feitos_na_materia:
                        if materia not in dados['progresso_edital']: dados['progresso_edital'][materia] = []
                        dados['progresso_edital'][materia].append(topico)
                        adicionar_xp(dados, 10) # Bônus por fechar tópico
                        agendar_revisao(dados, f"{materia}: {topico}")
                        salvar_dados(dados)
                        st.rerun()
                else:
                    if topico in feitos_na_materia:
                        dados['progresso_edital'][materia].remove(topico)
                        salvar_dados(dados)
                        st.rerun()

# --- ABA 3: BANCO DE RECOMPENSAS ---
with tab_loja:
    st.header("🎁 Loja de Recompensas")
    st.markdown("Troque suas horas líquidas de estudo por mimos merecidos!")
    
    saldo = dados['wallet']['xp']
    st.info(f"💎 Seu Saldo Atual: **{saldo}** Estaloquecas")
    
    # Grid de Recompensas
    cols = st.columns(3)
    for i, item in enumerate(dados['recompensas']):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="reward-card">
                <div style="font-size:40px">{item['icon']}</div>
                <h3>{item['item']}</h3>
                <p style="color: #8E44AD; font-weight:bold">{item['custo']} XP</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão de Compra
            if st.button(f"Resgatar {item['item']}", key=f"buy_{i}", use_container_width=True):
                if saldo >= item['custo']:
                    dados['wallet']['xp'] -= item['custo']
                    salvar_dados(dados)
                    st.balloons()
                    st.success(f"🎉 Resgatado! Aproveite seu(sua) {item['item']}!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"Faltam {item['custo'] - saldo} XP para isso!")

# --- ABA 4: CONFIGURAÇÕES ---
with tab_config:
    st.header("⚙️ Ajustes do Sistema")
    
    with st.expander("📝 Editar Tópicos do Edital"):
        st.caption("Adicione novos tópicos separados por vírgula.")
        materia_edit = st.selectbox("Escolha a Matéria", list(dados['edital'].keys()))
        novos_topicos = st.text_area("Tópicos Atuais", ", ".join(dados['edital'][materia_edit]))
        
        if st.button("Salvar Edital"):
            lista = [t.strip() for t in novos_topicos.split(",") if t.strip()]
            dados['edital'][materia_edit] = lista
            salvar_dados(dados)
            st.success("Edital atualizado!")
            time.sleep(1)
            st.rerun()
            
    with st.expander("➕ Adicionar Nova Recompensa"):
        r_nome = st.text_input("Nome do Prêmio (Ex: Jantar no Japonês)")
        r_custo = st.number_input("Custo em XP (1h estudo = 60 XP)", value=100)
        r_icon = st.text_input("Emoji", "🎁")
        
        if st.button("Adicionar Prêmio"):
            dados['recompensas'].append({"item": r_nome, "custo": r_custo, "icon": r_icon})
            salvar_dados(dados)
            st.success("Prêmio adicionado à loja!")
            
    if st.button("🗑️ Resetar Tudo (Zerar XP e Edital)"):
        if os.path.exists(ARQUIVO_DADOS):
            os.remove(ARQUIVO_DADOS)
            st.rerun()