import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
from datetime import datetime
# ==============================================================================
# 1. CONFIGURAÇÃO E CONEXÃO COM O BANCO DE DADOS (SQLite)
# ==============================================================================
TELEFONE_RECEPCAO_UNIDADE = "558791128133"
TELEFONE_ACOLHIMENTO = "5587988143263"  # Número exato do Acolhimento
EMAIL_SUPORTE_UNIDADE = "analistasocial.unilar@gmail.com"

# Conexão ao banco de dados SQLite local 'escala_hospitalar_v2.db'
conn = sqlite3.connect("escala_hospitalar_v2.db", check_same_thread=False)
cursor = conn.cursor()

# Tabela de ocorrências com suporte a controle mensal e anual
cursor.execute('''
    CREATE TABLE IF NOT EXISTS ocorrencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_registro TEXT,
        mes_referencia TEXT,
        ano_referencia TEXT,
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

# Adiciona colunas de referência caso o banco seja de versão anterior
try:
    cursor.execute("ALTER TABLE ocorrencias ADD COLUMN mes_referencia TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE ocorrencias ADD COLUMN ano_referencia TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass

# Configuração da página no Streamlit
st.set_page_config(page_title="Gestão de Escalas e Ocorrências", page_icon="🏥", layout="wide")

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
    st.caption(f"📧 Contacto Institucional: {EMAIL_SUPORTE_UNIDADE}")
    
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
    st.caption(f"Atenção Domiciliar - Registo de Alterações, Notificações e Histórico Mensal/Anual (📧 {EMAIL_SUPORTE_UNIDADE})")

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
                agora = datetime.now()
                data_atual = agora.strftime("%Y-%m-%d %H:%M:%S")
                mes_ref = agora.strftime("%m/%Y")  # Exemplo: '10/2026'
                ano_ref = agora.strftime("%Y")   # Exemplo: '2026'
                
                tipos_str = " e ".join(tipo_alteracao) if tipo_alteracao else "Não informado"
                telefone_salvar = telefone_familia.strip() if telefone_familia.strip() else "Não informado"
                
                cursor.execute('''
                    INSERT INTO ocorrencias (
                        data_registro, mes_referencia, ano_referencia, paciente, programa, tipo_alteracao, profissionais,
                        ja_escala, ja_passou, motivo, datas_plantao, observacoes,
                        telefone_familia, status_notificacao, data_notificacao, atendente_notificacao
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data_atual, mes_ref, ano_ref, nome_paciente_final, programa, tipos_str, profissionais,
                    ja_da_escala, ja_passou_escala, motivo, datas_plantao, observacoes,
                    telefone_salvar, "Pendente", "Não notificado", "Pendente"
                ))
                conn.commit()
                st.success(f"✅ Ocorrência salva com sucesso no mês {mes_ref} / ano {ano_ref}!")

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
                                📲 Enviar p/ Acolhimento 
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)
                    
                with col_btn2:
                    st.markdown(f'''
                        <a href="{link_acolhimento}" target="_blank">
                            <button style="background-color: #128C7E; color: white; padding: 12px 20px; border: none; border-radius: 8px; font-weight: bold; font-size: 15px; cursor: pointer; width: 100%;">
                                🏥 Enviar p/ Serviço Social
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
                    st.write(f"**Mês de Referência:** {row.get('mes_referencia', 'Não informado')}")
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

                    texto_whatsapp = f"""*Comunicado Importante!* - *AVISO DE AJUSTE DE ESCALA* •

Olá!

A fim de garantir a assistência do paciente *{row['paciente']}*, informamos o seguinte ajuste na escala: *{row['tipo_alteracao']}*:

*{row['profissionais']}*

*Data:{row['datas_plantao']}*

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
                                data_notif = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                tel_final = telefone_editado.strip() if telefone_editado.strip() else "Não informado"
                                cursor.execute('''
                                    UPDATE ocorrencias 
                                    SET status_notificacao = 'Concluído', data_notificacao = ?, atendente_notificacao = ?, telefone_familia = ?
                                    WHERE id = ?
                                ''', (data_notif, nome_atendente.strip(), tel_final, row['id']))
                                conn.commit()
                                st.success(f"Status do registro #{row['id']} atualizado por {nome_atendente.strip()}!")
                                st.rerun()

# ==============================================================================
# ABA 3: HISTÓRICO COMPLETO E RELATÓRIOS MENSAIS/ANUAIS
# ==============================================================================
if "📊 3. Histórico e Relatórios Mensais/Anuais" in abas_disponiveis or "📊 3. Histórico e Relatórios" in abas_disponiveis:
    idx_aba3 = 1 if perfil_atual == "Unidade de Saúde" else 2
    with abas[idx_aba3]:
        st.header("📊 Histórico Completo de Ocorrências e Relatórios Mensais/Anuais")
        st.caption(f"Relatório gerado pela unidade: {EMAIL_SUPORTE_UNIDADE}")
        
        df_todos = pd.read_sql_query("SELECT * FROM ocorrencias ORDER BY id DESC", conn)

        if df_todos.empty:
            st.warning("Nenhum registro encontrado no banco de dados.")
        else:
            st.subheader("🔍 Filtros de Pesquisa por Ano, Mês e Categoria")
            f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)
            
            # Filtro por Ano
            anos_unicos = [a for a in df_todos['ano_referencia'].dropna().unique() if a]
            lista_anos_filtro = ["Todos"] + sorted(anos_unicos, reverse=True)
            with f_col1:
                filtro_ano = st.selectbox("📅 Ano:", lista_anos_filtro)

            # Filtro por Mês
            meses_unicos = [m for m in df_todos['mes_referencia'].dropna().unique() if m]
            lista_meses_filtro = ["Todos"] + sorted(meses_unicos, reverse=True)
            with f_col2:
                filtro_mes = st.selectbox("🗓️ Mês/Ano:", lista_meses_filtro)

            with f_col3:
                filtro_status = st.selectbox("Status:", ["Todos", "Pendente", "Concluído"])
            
            with f_col4:
                lista_pacientes_filtro = ["Todos"] + sorted(list(df_todos['paciente'].unique()))
                filtro_paciente = st.selectbox("Paciente:", lista_pacientes_filtro)
                
            with f_col5:
                lista_programas_filtro = ["Todos"] + sorted(list(df_todos['programa'].unique()))
                fil_programa = st.selectbox("Programa:", lista_programas_filtro)

            df_filtrado = df_todos.copy()

            if filtro_ano != "Todos":
                df_filtrado = df_filtrado[df_filtrado["ano_referencia"] == filtro_ano]

            if filtro_mes != "Todos":
                df_filtrado = df_filtrado[df_filtrado["mes_referencia"] == filtro_mes]

            if filtro_status != "Todos":
                df_filtrado = df_filtrado[df_filtrado["status_notificacao"] == filtro_status]
                
            if filtro_paciente != "Todos":
                df_filtrado = df_filtrado[df_filtrado["paciente"] == filtro_paciente]
                
            if fil_programa != "Todos":
                df_filtrado = df_filtrado[df_filtrado["programa"] == fil_programa]

            # Métricas rápidas
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Total no Período", len(df_filtrado))
            col_m2.metric("Concluídas", len(df_filtrado[df_filtrado["status_notificacao"] == "Concluído"]))
            col_m3.metric("Pendentes", len(df_filtrado[df_filtrado["status_notificacao"] == "Pendente"]))

            st.divider()
            st.write(f"Exibindo **{len(df_filtrado)}** registro(s) encontrado(s):")
            st.dataframe(df_filtrado, use_container_width=True)

            csv_organizado = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            
            nome_arquivo = f"relatorio_escalas_{filtro_mes.replace('/', '_') if filtro_mes != 'Todos' else filtro_ano}.csv"
            
            st.download_button(
                label=f"📥 Baixar Relatório Filtrado em Excel / CSV",
                data=csv_organizado,
                file_name=nome_arquivo,
                mime="text/csv"
            )
