pyimport streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÃO E CONEXÃO COM BANCO DE DADOS (SQLite)
# ==============================================================================
# O SQLite cria um ficheiro local 'escala_hospitalar.db' para guardar os dados permanentemente.
conn = sqlite3.connect("escala_hospitalar.db", check_same_thread=False)
cursor = conn.cursor()

# Tabela para armazenar as ocorrências no banco de dados
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
        data_notificacao TEXT
    )
''')
conn.commit()

# Configuração visual da página
st.set_page_config(page_title="Gestão de Escalas e Ocorrências", page_icon="🏥", layout="wide")

st.title("🏥 Sistema de Gestão de Escalas e Ocorrências")
st.caption("Atenção Domiciliar - Registro de Alterações, Notificações e Histórico")

# --- NAVEGAÇÃO POR ABAS ---
aba1, aba2, aba3 = st.tabs([
    "📝 1. Registrar Alteração (Terceirizada)", 
    "📲 2. Notificar Família (Unidade de Saúde)", 
    "📊 3. Histórico e Relatórios"
])

# ==============================================================================
# ABA 1: REGISTRO PELA EMPRESA TERCEIRIZADA
# ==============================================================================
with aba1:
    st.header("📋 Registrar Informe de Alteração de Escala")
    st.write("Preencha o formulário abaixo. Os dados serão gravados permanentemente no banco de dados da unidade.")

    with st.form("form_terceirizada"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_beneficiario = st.text_input("Nome do Beneficiário *", placeholder="Ex: Leonice de Brito Monteiro")
            programa = st.selectbox("Programa *", ["Unimed Lar", "Cuidados Paliativos", "Outros"])
            
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
            profissionais = st.text_area("Profissionais Envolvidos (Nome e Conselho)", placeholder="SAÍDA: ... | SUPORTE: ...")

        with col2:
            ja_da_escala = st.radio("Já é da escala do paciente?", ["Sim", "Não"])
            ja_passou_escala = st.radio("Já passou pela escala antes?", ["Sim", "Não"])
            motivo = st.text_input("Motivo da Alteração", placeholder="Ex: Solicitação a próprio pedido")
            datas_plantao = st.text_input("Data da Rotina / Período / Início", placeholder="Ex: Suporte: 01/10/2026 - Noturno")
            
            telefone_familia = st.text_input("WhatsApp do Responsável/Família (com DDD) *", placeholder="Ex: 5511999998888")

        observacoes = st.text_area("Observações Gerais", value="Favor comunicar a família.")
        
        btn_enviar = st.form_submit_button("💾 Salvar e Enviar para a Unidade")

    if btn_enviar:
        if not nome_beneficiario or not telefone_familia:
            st.error("⚠️ Os campos 'Nome do Beneficiário' e 'WhatsApp da Família' são obrigatórios.")
        else:
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tipos_str = ", ".join(tipo_alteracao) if tipo_alteracao else "Não informado"
            
            # Inserção de dados no banco SQLite
            cursor.execute('''
                INSERT INTO ocorrencias (
                    data_registro, paciente, programa, tipo_alteracao, profissionais,
                    ja_escala, ja_passou, motivo, datas_plantao, observacoes,
                    telefone_familia, status_notificacao, data_notificacao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data_atual, nome_beneficiario, programa, tipos_str, profissionais,
                ja_da_escala, ja_passou_escala, motivo, datas_plantao, observacoes,
                telefone_familia, "Pendente", "Não notificado"
            ))
            conn.commit()
            st.success("✅ Informe gravado com sucesso no banco de dados!")

# ==============================================================================
# ABA 2: PAINEL DE NOTIFICAÇÃO (UNIDADE DE SAÚDE)
# ==============================================================================
with aba2:
    st.header("📥 Ocorrências Pendentes de Notificação")
    st.write("Abaixo estão as alterações cadastradas aguardando contato com a família.")

    # Consulta ao banco de dados buscando status 'Pendente'
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
                st.write(f"**Telefone Família:** {row['telefone_familia']}")

                # Construção do texto para envio via WhatsApp
                texto_whatsapp = f"""*INFORME DE ALTERAÇÃO DE ESCALA - ATENÇÃO DOMICILIAR* 🏥

Olá! Informamos que houve uma alteração na escala de atendimento do paciente *{row['paciente']}*.

*Programa:* {row['programa']}
*Tipo de Alteração:* {row['tipo_alteracao']}

*Profissionais:*
{row['profissionais']}

*Motivo:* {row['motivo']}
*Data / Período:* {row['datas_plantao']}

*Observações:* {row['observacoes']}

Estamos à disposição para eventuais dúvidas."""

                texto_encoded = urllib.parse.quote(texto_whatsapp)
                link_wa = f"https://wa.me/{row['telefone_familia']}?text={texto_encoded}"

                col_btn1, col_btn2 = st.columns([1, 2])
                with col_btn1:
                    st.markdown(f'''
                        <a href="{link_wa}" target="_blank">
                            <button style="background-color: #25D366; color: white; padding: 10px 16px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                                📱 Abrir WhatsApp
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)
                
                with col_btn2:
                    # Atualiza o status para concluído
                    if st.button(f"✅ Marcar como Notificado (ID #{row['id']})"):
                        data_notif = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute('''
                            UPDATE ocorrencias 
                            SET status_notificacao = 'Concluído', data_notificacao = ? 
                            WHERE id = ?
                        ''', (data_notif, row['id']))
                        conn.commit()
                        st.success(f"Status atualizado para Concluído!")
                        st.rerun()

# ==============================================================================
# ABA 3: HISTÓRICO COMPLETO E RELATÓRIOS
# ==============================================================================
with aba3:
    st.header("📊 Histórico Completo de Ocorrências e Relatórios")
    df_todos = pd.read_sql_query("SELECT * FROM ocorrencias ORDER BY id DESC", conn)

    if df_todos.empty:
        st.warning("Nenhum registo encontrado no banco de dados.")
    else:
        st.dataframe(df_todos, use_container_width=True)

        # Download do relatório em CSV/Excel
        csv = df_todos.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descarregar Relatório Completo (CSV/Excel)",
            data=csv,
            file_name=f"relatorio_alteracao_escalas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
