import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAÇÃO E CONEXÃO COM O BANCO DE DADOS (SQLite)
# ==============================================================================
# Conectamos ao banco de dados local 'escala_hospitalar.db' para salvar todas as alterações.
conn = sqlite3.connect("escala_hospitalar.db", check_same_thread=False)
cursor = conn.cursor()

# Tabela responsável por guardar o histórico de alterações registradas
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

# Configuração visual e título do aplicativo web
st.set_page_config(page_title="Gestão de Escalas e Ocorrências", page_icon="🏥", layout="wide")

st.title("🏥 Sistema de Gestão de Escalas e Ocorrências")
st.caption("Atenção Domiciliar - Registro de Alterações, Notificações e Histórico")

# ==============================================================================
# 2. BASE DE DADOS DE PACIENTES (Em Ordem Alfabética de A a Z)
# ==============================================================================
# Mapeamento dos pacientes vinculados à terceirizada e seus respectivos programas (PUL/PCP).
PACIENTES_BASE = {
    "Ana Beatriz Corcino da Silva": "PUL",
    "Ana Vitoria Soares Silva": "PCP",
    "Antenor Oliveira Matos": "PUL",
    "Bruno Rafael da Silva": "PUL",
    "Catarina de Carvalho Jambeiro": "PUL",
    "Davi Lucas Ribeiro de Souza Lino": "PUL",
    "Enzo Gabriel Borges Amorim": "PUL",
    "Evellyn Vitoria Lopes de Melo": "PUL",
    "Ezequiel Marques de Araujo": "PUL",
    "João Alves Pereira": "PUL",
    "Jose Rutenio do Amaral Junior": "PUL",
    "Julio Vinícius de Melo": "PCP",
    "Maiane Silva de Lima": "PUL",
    "Maria das Graças Sobreira de Almeida": "PUL",
    "Maria Julia Almeida de Oliveira": "PUL",
    "Matheus Oliveira Guimarães": "PUL",
    "Noah Benício Brito de Vasconcelos": "PUL",
    "Pedro Vinícius Costa da Silva": "PUL",
    "Pérola Jasmin Viana": "PCP",
    "Samuel Rozendo do Nascimento": "PUL",
    "Sebastiana Maria de Souza Lima": "PUL",
    "Terezinha de Jesus Alencar": "PUL",
    "Thaiane Santos de Morgado": "PUL",
    "Valéria Pereira dos Santos": "PUL",
    "Victor Emanoel Almeida de Freitas": "PUL",
    "Zezito Gomes Pereira Junior": "PUL",
    "➕ Cadastrar Novo Paciente": "PUL"
}

# Criamos a lista de nomes a partir das chaves do dicionário
lista_nomes_ordenada = list(PACIENTES_BASE.keys())

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
    st.write("Selecione o paciente na lista suspensa (em ordem alfabética) para registrar a ocorrência.")

    # Menu de seleção com os nomes ordenados de A a Z
    paciente_selecionado = st.selectbox("Selecione o Paciente *", lista_nomes_ordenada)

    # Identifica o programa padrão (PUL ou PCP) do paciente escolhido
    programa_sugerido = PACIENTES_BASE.get(paciente_selecionado, "PUL")

    # Tratamento para quando for um novo paciente
    if paciente_selecionado == "➕ Cadastrar Novo Paciente":
        nome_paciente_final = st.text_input("Digite o Nome Completo do Novo Paciente *", placeholder="Ex: Ana Maria de Souza")
    else:
        nome_paciente_final = paciente_selecionado

    # Formulário de entrada de dados
    with st.form("form_terceirizada"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Seleção do programa com a sugestão automática ativada (PUL / PCP / Outros)
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
            profissionais = st.text_area("Profissionais Envolvidos (Nome e Conselho)", placeholder="SAÍDA: ... | SUPORTE: ...")

        with col2:
            ja_da_escala = st.radio("Já é da escala do paciente?", ["Sim", "Não"])
            ja_passou_escala = st.radio("Já passou pela escala antes?", ["Sim", "Não"])
            motivo = st.text_input("Motivo da Alteração", placeholder="Ex: Solicitação a próprio pedido")
            datas_plantao = st.text_input("Data da Rotina / Período / Início", placeholder="Ex: Suporte: 01/10/2026 - Noturno")
            
            # Campo de digitação manual do WhatsApp da família
            telefone_familia = st.text_input("WhatsApp do Responsável/Família (com DDD e 55) *", placeholder="Ex: 5587999998888")

        observacoes = st.text_area("Observações Gerais", value="Favor comunicar a família.")
        
        btn_enviar = st.form_submit_button("💾 Salvar e Enviar para a Unidade")

    # Ação de salvamento no banco de dados
    if btn_enviar:
        if not nome_paciente_final or not telefone_familia:
            st.error("⚠️ Os campos 'Nome do Paciente' e 'WhatsApp da Família' são obrigatórios.")
        else:
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tipos_str = ", ".join(tipo_alteracao) if tipo_alteracao else "Não informado"
            
            cursor.execute('''
                INSERT INTO ocorrencias (
                    data_registro, paciente, programa, tipo_alteracao, profissionais,
                    ja_escala, ja_passou, motivo, datas_plantao, observacoes,
                    telefone_familia, status_notificacao, data_notificacao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data_atual, nome_paciente_final, programa, tipos_str, profissionais,
                ja_da_escala, ja_passou_escala, motivo, datas_plantao, observacoes,
                telefone_familia, "Pendente", "Não notificado"
            ))
            conn.commit()
            st.success(f"✅ Informe do paciente '{nome_paciente_final}' gravado com sucesso no banco de dados!")

# ==============================================================================
# ABA 2: PAINEL DE NOTIFICAÇÃO (UNIDADE DE SAÚDE)
# ==============================================================================
with aba2:
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
                st.write(f"**Telefone Família:** {row['telefone_familia']}")

                # Construção do texto formatado para o WhatsApp
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
                    if st.button(f"✅ Marcar como Notificado (ID #{row['id']})"):
                        data_notif = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute('''
                            UPDATE ocorrencias 
                            SET status_notificacao = 'Concluído', data_notificacao = ? 
                            WHERE id = ?
                        ''', (data_notif, row['id']))
                        conn.commit()
                        st.success(f"Status do registro #{row['id']} atualizado para Concluído!")
                        st.rerun()

# ==============================================================================
# ABA 3: HISTÓRICO COMPLETO E EXTRAÇÃO DE RELATÓRIOS
# ==============================================================================
with aba3:
    st.header("📊 Histórico Completo de Ocorrências e Relatórios")
    df_todos = pd.read_sql_query("SELECT * FROM ocorrencias ORDER BY id DESC", conn)

    if df_todos.empty:
        st.warning("Nenhum registro encontrado no banco de dados.")
    else:
        st.dataframe(df_todos, use_container_width=True)

        csv = df_todos.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Relatório Completo (CSV/Excel)",
            data=csv,
            file_name=f"relatorio_alteracao_escalas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
