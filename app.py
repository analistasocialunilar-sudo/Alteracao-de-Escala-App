import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ==============================================================================
# 1. CONFIGURAÇÃO E CONEXÃO COM O GOOGLE SHEETS VIA GSPREAD
# ==============================================================================
TELEFONE_RECEPCAO_UNIDADE = "558791128133"
TELEFONE_ACOLHIMENTO = "558791128133"  # Substitua pelo número exato do Acolhimento

st.set_page_config(page_title="Gestão de Escalas e Ocorrências", page_icon="🏥", layout="wide")

@st.cache_resource
def obter_conexao_gspread():
    """
    Cria uma conexão direta e segura com o Google Sheets utilizando o gspread.
    Utiliza as credenciais guardadas em st.secrets["connections"]["gsheets"].
    """
    escopos = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Carrega as credenciais da seção Secrets do Streamlit Cloud
    info_credenciais = dict(st.secrets["connections"]["gsheets"])
    
    # Remove chaves de configuração do Streamlit que não pertencem ao Service Account
    info_credenciais.pop("spreadsheet", None)
    info_credenciais.pop("type", None)

    creds = Credentials.from_service_account_info(info_credenciais, scopes=escopos)
    client = gspread.authorize(creds)
    
    # Abre a planilha pelo URL fornecido nos Secrets
    url_planilha = st.secrets["connections"]["gsheets"]["spreadsheet"]
    sheet = client.open_by_url(url_planilha).worksheet("Ocorrencias")
    return sheet

def carregar_dados():
    """
    Lê todas as linhas da aba 'Ocorrencias' no Google Sheets e converte em DataFrame.
    """
    try:
        aba = obter_conexao_gspread()
        dados = aba.get_all_records()
        df = pd.DataFrame(dados)
        return df
    except Exception as e:
        colunas = [
            "id", "data_registro", "mes_referencia", "ano_referencia", "paciente", 
            "programa", "tipo_alteracao", "profissionais", "ja_escala", "ja_passou", 
            "motivo", "datas_plantao", "observacoes", "telefone_familia", 
            "status_notificacao", "data_notificacao", "atendente_notificacao"
        ]
        return pd.DataFrame(columns=colunas)

# ==============================================================================
# 2. SISTEMA DE AUTENTICAÇÃO E LOGIN
# ==============================================================================
USUARIOS = {
    "terceirizada": {"senha": "terceirizada@123", "perfil": "Terceirizada", "nome": "Empresa Terceirizada"},
    "unidade": {"senha": "un1m3d210", "perfil": "Unidade de Saúde", "nome": "Equipa da Unidade"},
    "admin": {"senha": "adu@210escalas", "perfil": "Administrador", "nome": "Gestor do Sistema"}
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
            
    st.stop()

# ==============================================================================
# 3. BASE DE DADOS DE PACIENTES
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
    st.caption("Atenção Domiciliar - Registro de Alterações, Notificações e Histórico no Google Sheets")

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
    abas_disponiveis = ["📲 2. Notificar Família (Unidade de Saúde)", "📊 3. Histórico e Relatórios Mensais/Anuais"]
else:
    abas_disponiveis = [
        "📝 1. Registrar Alteração (Terceirizada)", 
        "📲 2. Notificar Família (Unidade de Saúde)", 
        "📊 3. Histórico e Relatórios Mensais/Anuais"
    ]

abas = st.tabs(abas_disponiveis)

# ==============================================================================
# ABA 1: REGISTRO PELA TERCEIRIZADA (Adição de linha no Google Sheets)
# ==============================================================================
if "📝 1. Registrar Alteração (Terceirizada)" in abas_disponiveis:
    idx_aba1 = abas_disponiveis.index("📝 1. Registrar Alteração (Terceirizada)")
    with abas[idx_aba1]:
        st.header("📋 Registrar Informe de Alteração de Escala")
        st.write("Selecione o paciente na lista suspensa para registrar a ocorrência no Google Sheets.")

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
            
            btn_enviar = st.form_submit_button("💾 Salvar na Nuvem e Enviar para a Unidade")

        if btn_enviar:
            if not nome_paciente_final:
                st.error("⚠️ O campo 'Paciente' é obrigatório.")
            else:
                agora = datetime.now()
                data_atual = agora.strftime("%Y-%m-%d %H:%M:%S")
                mes_ref = agora.strftime("%m/%Y")
                ano_ref = agora.strftime("%Y")
                
                tipos_str = " e ".join(tipo_alteracao) if tipo_alteracao else "Não informado"
                telefone_salvar = telefone_familia.strip() if telefone_familia.strip() else "Não informado"
                
                # Obter dados atuais para gerar o novo ID
                df_existente = carregar_dados()
                novo_id = len(df_existente) + 1
                
                # Cria a lista exatamente na ordem das colunas da planilha
                nova_linha_lista = [
                    novo_id,
                    data_atual,
                    mes_ref,
                    ano_ref,
                    nome_paciente_final,
                    programa,
                    tipos_str,
                    profissionais,
                    ja_da_escala,
                    ja_passou_escala,
                    motivo,
                    datas_plantao,
                    observacoes,
                    telefone_salvar,
                    "Pendente",
                    "Não notificado",
                    "Pendente"
                ]

                # Anexa a nova linha diretamente no Google Sheets de forma segura
                aba_sheets = obter_conexao_gspread()
                aba_sheets.append_row(nova_linha_lista)
                
                st.success(f"✅ Ocorrência salva com sucesso no Google Sheets (Mês: {mes_ref} | Ano: {ano_ref})!")

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
                link_acolhimento = f"https://wa.me/{TELEFONE_ACOLHIMENTO}?text={msg_encoded}"

                st.markdown("### 📲 Próximo Passo: Enviar para a Equipa da Unidade")
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    st.markdown(f'''
                        <a href="{link_recepcao}" target="_blank">
                            <button style="background-color: #25D366; color: white; padding: 12px 20px; border: none; border-radius: 8px; font-weight: bold; font-size: 15px; cursor: pointer; width: 100%;">
                                📲 Enviar p/ Recepção (+55 87 9112-8133)
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)
                    
                with col_btn2:
                    st.markdown(f'''
                        <a href="{link_acolhimento}" target="_blank">
                            <button style="background-color: #128C7E; color: white; padding: 12px 20px; border: none; border-radius: 8px; font-weight: bold; font-size: 15px; cursor: pointer; width: 100%;">
                                🏥 Enviar p/ Acolhimento
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

        df_todos = carregar_dados()
        df_pendentes = df_todos[df_todos["status_notificacao"] == "Pendente"] if not df_todos.empty else pd.DataFrame()

        if df_pendentes.empty:
            st.info("🎉 Nenhuma notificação pendente no momento.")
