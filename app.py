import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
from datetime import datetime
import os

# ==============================================================================
# 1. CONFIGURAÇÃO E CONEXÃO COM O BANCO DE DADOS (SQLite Persistente)
# ==============================================================================
TELEFONE_RECEPCAO_UNIDADE = "558791128133"
TELEFONE_ACOLHIMENTO = "5587988143263"  # Número exato do Acolhimento
EMAIL_SUPORTE_UNIDADE = "analistasocial.unilar@gmail.com"

# Garantir que a pasta de dados existe para persistência segura no servidor
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DB_PATH = os.path.join(DATA_DIR, "escala_hospitalar_v2.db")

# Conexão ao banco de dados SQLite com caminho persistente
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
