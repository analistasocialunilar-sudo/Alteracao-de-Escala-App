import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAÇÃO E CONEXÃO COM O BANCO DE DADOS (SQLite)
# ==============================================================================
TELEFONE_RECEPCAO_UNIDADE = "558791128133"

conn = sqlite3.connect("escala_hospitalar_v2.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS ocorrencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_registro TEXT,
        paciente TEXT,
        programa TEXT,
        tipo_alteracao TEXT,
        profissionais TEXT,
        ja_escala TEXT,
        ja_passou TEXT,
        motivo TEXT,
        datas_plantao TEXT,
        observacoes TEXT,
        telefone_familia TEXT,
        status_notificacao TEXT,
        data_notificacao TEXT,
        atendente_notificacao TEXT
    )
''')
conn.commit()

st.set_page_config(page_title="Gestão de Escalas e Ocorrências", page_icon="🏥", layout="wide")

# ==============================================================================
# 2. SISTEMA DE AUTENTICAÇÃO E LOGIN
# ==============================================================================
USUARIOS = {
    "terceirizada": {"senha": "123", "perfil": "Terceirizada", "nome": "Empresa Terceirizada"},
    "unidade": {"senha": "456", "perfil": "Unidade de Saúde", "nome": "Equipa da Unidade"},
    "admin": {"senha": "admin", "perfil": "Administrador", "nome": "Gestor do Sistema"}
}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario_nome"] = ""
    st.session_state["usuario_perfil"] = ""

def realizar_login(usuario, senha):
    if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
        st.session_state["autenticado"] = True
        st.session_state["usuario_nome"] = USUARIOS[usuario]["nome"]
        st.session_state["usuario_perfil"] = USUARIOS[usuario]["perfil"]
        st.success("Login efetuado com sucesso!")
        st.rerun()
    else:
        st.error("Utilizador ou palavra-passe incorretos.")

def realizar_logout():
    st.session_state["autenticado"] = False
    st.session_state["usuario_nome"] = ""
    st.session_state["usuario_perfil"] = ""
    st.rerun()

if not st.session_state["autenticado"]:
    st.title("🏥 Sistema de Gestão de Escalas e Ocorrências")
    st.subheader("🔐 Acesso Restrito - Faça o seu Login")
    
    with st.form("form_login"):
        user_input = st.text_input("Utilizador").strip().lower()
        pass_input = st.text_input("Palavra-passe", type="password")
        btn_login = st.form_submit_button("Entrar no Sistema")
        
        if btn_login:
            realizar_login(user_input, pass_input)
            
    st.info("💡 **Dica de Acesso Rápido para Testes:**\n- **Terceirizada:** Utilizador `terceirizada` | Palavra-passe `123`\n- **Unidade de Saúde:** Utilizador `unidade` | Palavra-passe `456`\n- **Administrador:** Utilizador `admin` | Palavra-passe `admin`")
    st.stop()

# ==============================================================================
# 3. BASE DE DADOS DE PACIENTES (Lista de Iniciais Personalizada)
# ==============================================================================
PACIENTES_BASE = {
    "A. B. C. S.": "PUL",
    "A. V. S. S.": "PCP",
    "A. O. M.": "PUL",
    "B. R. S.": "PUL",
    "C. C. J.": "PUL",
    "D. L. R. S. L.": "PUL",
    "E. G. B. A.": "PUL",
    "E. V. L. M.": "PUL",
    "E. M. A.": "PUL",
    "J. A. P.": "PUL",
    "J. R. A. J.": "PUL",
    "J. V. M.": "PCP",
    "M. S. L.": "PUL",
    "M. G. S. S. A.": "PUL",
    "M. J. A. O.": "PUL",
    "M. O. G.": "PUL",
    "N. B. B. V.": "PUL",
    "P. V. C. S.": "PUL",
    "P. J. V.": "PCP",
    "S. R. N.": "PUL",
    "S. M. S. L.": "PUL",
    "T. J. A.": "PUL",
    "T. S. M.": "PUL",
    "V. P. S.": "PUL",
    "V. E. A. F.": "PUL",
    "Z. G. P. J.": "PUL",
    "➕ Cadastrar Novo Paciente": "PUL"
}

lista_nomes_ordenada = list(PACIENTES_BASE.keys())

# ==============================================================================
# 4. CABEÇALHO DO SISTEMA E NAVEGAÇÃO DE PERFIS
# ==============================================================================
col_tit, col_user = st.columns([3, 1])
with col_tit:
    st.title("🏥 Sistema de Gestão de Escalas e Ocorrências")
    st.caption("Atenção Domiciliar - Registro de Alterações, Notificações e Histórico")

with col_user:
    st.write(f"👤 **{st.session_state['usuario_nome']}**")
    st.caption(f"Perfil: {st.session_state['usuario_perfil']}")
    if st.button("🚪 Sair / Logout"):
        realizar_logout()

st.divider()

perfil_atual = st.session_state["usuario_perfil"]

if perfil_atual == "Terceirizada":
    abas_disponiveis = ["📝 1. Registrar Alteração (Terceirizada)"]
elif perfil_atual == "Unidade de Saúde":
    abas_disponiveis = ["📲 2. Notificar Família (Unidade de Saúde)", "📊 3. Histórico e Relatórios"]
else:
    abas_disponiveis = [
        "📝 1. Registrar Alteração (Terceirizada)", 
        "📲 2. Notificar Família (Unidade de Saúde)", 
        "📊 3. Histórico e Relatórios"
    ]

abas = st.tabs(abas_disponiveis)

# ==============================================================================
# ABA 1: REGISTRO PELA TERCEIRIZADA
# ==============================================================================
if "📝 1. Registrar Alteração (Terceirizada)" in abas_disponiveis:
    idx_aba1 = abas_disponiveis.index("📝 1. Registrar Alteração (Terceirizada)")
    with abas[idx_aba1]:
        st.header("📋 Registrar Informe de Alteração de Escala")
        st.write("Selecione o paciente na lista suspensa para registrar a ocorrência.")

        paciente_selecionado = st.selectbox("Selecione o Paciente *", lista_nomes_ordenada)
        programa_sugerido = PACIENTES_BASE.get(paciente_selecionado, "PUL")

        if paciente_selecionado == "➕ Cadastrar Novo Paciente":
            nome_paciente_final = st.text_input("Digite as Iniciais do Novo Paciente *", placeholder="Ex: X. Y. Z.")
        else:
            nome_paciente_final = paciente_selecionado

        with st.form("form_terceirizada"):
            col1, col2 = st.columns(2)
            
            with col1:
                opcoes_programa = ["PUL (Unimed Lar)", "PCP (Cuidados Paliativos)", "Outros"]
                indice_padrao = 1 if programa_sugerido == "PCP" else 0
                
                programa = st.selectbox("Programa *", opcoes_programa, index=indice_padrao)
                
                tipo_alteracao = st.multiselect(
                    "Tipo de Alteração:",
                    [
                        "Entrada de novo profissional",
                        "Saída de profissional",
                        "Cobertura de folga/atestado/férias",
                        "Alteração de horário/escala",
                        "Conhecer a Rotina",
                        "Outros"
                    ]
                )
                profissionais = st.text_area("Profissionais Envolvidos (Nome e Conselho)", placeholder="Ex:\n- SAÍDA: xxx xxxx xxxx (COREN: x.xxx.xxx)\n- SUPORTE: TACIANA GOMES DE MEDEIROS (COREN: 1.710.047)")

            with col2:
                ja_da_escala = st.radio("Já é da escala do paciente?", ["Sim", "Não"])
                ja_passou_escala = st.radio("Já passou pela escala antes?", ["Sim", "Não"])
                motivo = st.text_input("Motivo da Alteração", placeholder="Ex: Cobertura de atestado/férias")
                datas_plantao = st.text_input("Data da Rotina / Período / Início", placeholder="Ex: Suporte: 01/10/2026 - plantão diurno")
                telefone_familia = st.text_input("WhatsApp do Responsável/Família (Opcional)", placeholder="Ex: 5587999998888")

            observacoes = st.text_area("Observações Gerais", value="Favor comunicar a família.")
            
            btn_enviar = st.form_submit_button("💾 Salvar e Enviar para a Unidade")

        if btn_enviar:
            if not nome_paciente_final:
                st.error("⚠️ O campo 'Paciente' é obrigatório.")
            else:
                data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                tipos_str = " e ".join(tipo_alteracao) if tipo_alteracao else "Não informado"
                telefone_salvar = telefone_familia.strip() if telefone_familia.strip() else "Não informado"
                
                cursor.execute('''
                    INSERT INTO ocorrencias (
                        data_registro, paciente, programa, tipo_alteracao, profissionais,
                        ja_escala, ja_passou, motivo, datas_plantao, observacoes,
                        telefone_familia, status_notificacao, data_notificacao, atendente_notificacao
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data_atual, nome_paciente_final, programa, tipos_str, profissionais,
                    ja_da_escala, ja_passou_escala, motivo, datas_plantao, observacoes,
                    telefone_salvar, "Pendente", "Não notificado", "Pendente"
                ))
                conn.commit()
                st.success(f"✅ Ocorrência salva no banco de dados com sucesso!")

                msg_recepcao = f"""*NOVO INFORME DE ALTERAÇÃO DE ESCALA* 🚨

*Paciente:* {nome_paciente_final}
*Programa:* {programa}
*Tipo de Alteração:* {tipos_str}

*Profissionais:*
{profissionais}

*Motivo:* {motivo}
*Data / Período:* {datas_plantao}
*Observações:* {observacoes}

_Por favor, realizar a notificação da família no sistema._"""

                msg_encoded = urllib.parse.quote(msg_recepcao)
                link_recepcao = f"https://wa.me/{TELEFONE_RECEPCAO_UNIDADE}?text={msg_encoded}"

                st.markdown("### 📲 Próximo Passo: Enviar para a Recepção da Unidade")
                st.markdown(f'''
                    <a href="{link_recepcao}" target="_blank">
                        <button style="background-color: #25D366; color: white; padding: 12px 20px; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer;">
                            📲 Enviar Informe via WhatsApp (+55 87 9112-8133)
                        </button>
                    </a>
                ''', unsafe_allow_html=True)

# ==============================================================================
# ABA 2: PAINEL DE NOTIFICAÇÃO
# ==============================================================================
if "📲 2. Notificar Família (Unidade de Saúde)" in abas_disponiveis:
    idx_aba2 = abas_disponiveis.index("📲 2. Notificar Família (Unidade de Saúde)")
    with abas[idx_aba2]:
        st.header("📥 Ocorrências Pendentes de Notificação")
        st.write("Abaixo estão as alterações cadastradas aguardando contato com a família.")

        df_pendentes = pd.read_sql_query("SELECT * FROM ocorrencias WHERE status_notificacao = 'Pendente'", conn)

        if df_pendentes.empty:
            st.info("🎉 Nenhuma notificação pendente no momento.")
        else:
            for idx, row in df_pendentes.iterrows():
                with st.expander(f"📌 Registro #{row['id']} - Paciente: {row['paciente']} ({row['programa']})"):
                    st.write(f"**Data de Registro:** {row['data_registro']}")
                    st.write(f"**Tipo de Alteração:** {row['tipo_alteracao']}")
                    st.write(f"**Profissionais:** {row['profissionais']}")
                    st.write(f"**Motivo:** {row['motivo']}")
                    st.write(f"**Detalhes do Plantão:** {row['datas_plantao']}")
                    st.write(f"**Observações:** {row['observacoes']}")
                    
                    tel_atual = "" if row['telefone_familia'] == "Não informado" else row['telefone_familia']
                    telefone_editado = st.text_input(
                        "WhatsApp do Responsável/Família (com 55 e DDD) *", 
                        value=tel_atual, 
                        key=f"tel_{row['id']}", 
                        placeholder="Ex: 5587999998888"
                    )

                    texto_whatsapp = f"""Comunicado Importante! - *AVISO DE AJUSTE DE ESCALA* •

Olá, boa tarde!

A fim de garantir a assistência do paciente *{row['paciente']}*, informamos o seguinte ajuste na escala: *{row['tipo_alteracao']}*:

{row['profissionais']}
*Data:* {row['datas_plantao']}

Favor, confirmar o recebimento e ciência deste comunicado.

Agradecemos sua atenção e colaboração!"""

                    texto_encoded = urllib.parse.quote(texto_whatsapp)
                    num_link = telefone_editado.strip() if telefone_editado.strip() else "000000000000"
                    link_wa = f"https://wa.me/{num_link}?text={texto_encoded}"

                    st.markdown("---")
                    col_wa, col_atendente, col_btn = st.columns([1, 1.5, 1.5])
                    
                    with col_wa:
                        if telefone_editado.strip():
                            st.markdown(f'''
                                <a href="{link_wa}" target="_blank">
                                    <button style="background-color: #25D366; color: white; padding: 10px 16px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                                        📱 Abrir WhatsApp
                                    </button>
                                </a>
                            ''', unsafe_allow_html=True)
                        else:
                            st.warning("⚠️ Insira o número do telefone acima para ativar o botão do WhatsApp.")
                    
                    with col_atendente:
                        nome_atendente = st.text_input(
                            f"Nome do Atendente/Servidor *", 
                            value=st.session_state["usuario_nome"] if st.session_state["usuario_nome"] != "Equipa da Unidade" else "",
                            key=f"atendente_{row['id']}",
                            placeholder="Digite o seu nome"
                        )
                    
                    with col_btn:
                        st.write("")
                        if st.button(f"✅ Concluir Notificação", key=f"btn_concluir_{row['id']}"):
                            if not nome_atendente.strip():
                                st.error("⚠️ Por favor, digite o nome do atendente antes de concluir.")
                            else:
                                data_notif = datetime.now().strftime("%Y-%m-%d %H:%
