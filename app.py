import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import urllib.parse

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E BANCO DE DADOS (SQLite)
# ==============================================================================
st.set_page_config(
    page_title="Gestão de Farmácia - Assistência Domiciliar",
    page_icon="💊",
    layout="wide"
)

DB_NAME = "estoque_farmacia.db"

PACIENTES_RAW = [
    {"nome": "MARCIA RODRIGUES RIBEIRO", "telefone": "5574991984281", "programa": "PCP"},
    {"nome": "SILVANA APARECIDA SILVA DE MELO", "telefone": "558781740027", "programa": "PCP"},
    {"nome": "VIRGINIA FERNANDES DE MEDEIROS DINIZ", "telefone": "5587988261915", "programa": "PCP"},
    {"nome": "JULIO VINICIUS DA CRUZ", "telefone": "557488631920", "programa": "PCP"},
    {"nome": "ANA VITORIA SOARES ALVES", "telefone": "5587981355610", "programa": "PCP"},
    {"nome": "ARISTON OLIVEIRA MARTINS", "telefone": "5574988127404", "programa": "PCP"},
    {"nome": "ASTOR MOLLER", "telefone": "5574988372718", "programa": "PCP"},
    {"nome": "ANTONIA MARIA SANDES GOMES", "telefone": "558738660679", "programa": "PCP"},
    {"nome": "FRANCISCO MUNIZ BARRETTO", "telefone": "5587988239169", "programa": "PCP"},
    {"nome": "ZILDA GONDIM DE MENDONCA", "telefone": "558788262357", "programa": "PCP"},
    {"nome": "TEREZINHA TELES DA SILVA", "telefone": "557488661963", "programa": "PCP"},
    {"nome": "ALMIRA COELHO ASSIS", "telefone": "557436112226", "programa": "PCP"},
    {"nome": "REGINA LUCIA DE AZEVEDO", "telefone": "558781185975", "programa": "PCP"},
    {"nome": "PEROLA JASMIN VIANA", "telefone": "558788687707", "programa": "PCP"},
    {"nome": "OLINDA CELINA CARDOSO", "telefone": "557488090018", "programa": "PCP"},
    {"nome": "GABRIEL FRANCISCO ALVES", "telefone": "558738618469", "programa": "PCP"},
    {"nome": "FELIX RODRIGUES DE ANDRADE", "telefone": "558738643655", "programa": "PCP"},
    {"nome": "RUTE CORREIA MOREIRA", "telefone": "5581981011560", "programa": "PCP"},
    {"nome": "ISABEL AMORIM GOMES SOUZA", "telefone": "558788298523", "programa": "PCP"},
    {"nome": "ARTUR GAEL BARBOSA VIEIRA DA SILVA CRUZ", "telefone": "558788362329", "programa": "PCP"}
]

PACIENTES_INICIAIS = []
for p in PACIENTES_RAW:
    enfermeira = "Nara Armentano" if "PEROLA JASMIN" in p["nome"].upper() else "Amanda Ellen Bezerra dos Santos"
    PACIENTES_INICIAIS.append({
        "nome": p["nome"],
        "telefone": p["telefone"],
        "programa": p["programa"],
        "enfermeiro": enfermeira,
        "responsavel": "Família"
    })

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            quantidade_atual INTEGER NOT NULL DEFAULT 0,
            quantidade_minima INTEGER NOT NULL DEFAULT 10,
            unidade_medida TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_paciente TEXT NOT NULL,
            telefone TEXT,
            programa TEXT NOT NULL,
            enfermeiro_referencia TEXT NOT NULL,
            responsavel_familia TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            tipo_movimentacao TEXT NOT NULL,
            produto_id INTEGER NOT NULL,
            produto_nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            paciente_nome TEXT,
            enfermeiro_referencia TEXT,
            responsavel_retirada TEXT,
            observacao TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contagem_domicilio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            paciente_nome TEXT NOT NULL,
            enfermeiro_referencia TEXT NOT NULL,
            produto_nome TEXT NOT NULL,
            quantidade_domicilio INTEGER NOT NULL,
            responsavel_contagem TEXT NOT NULL,
            observacao TEXT
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM pacientes")
    if cursor.fetchone()[0] == 0:
        for p in PACIENTES_INICIAIS:
            cursor.execute('''
                INSERT INTO pacientes (nome_paciente, telefone, programa, enfermeiro_referencia, responsavel_familia)
                VALUES (?, ?, ?, ?, ?)
            ''', (p["nome"], p["telefone"], p["programa"], p["enfermeiro"], p["responsavel"]))
    
    conn.commit()
    conn.close()

init_db()

# ==============================================================================
# 2. AUTENTICAÇÃO E LOGIN
# ==============================================================================
USUARIOS = {
    "farmacia": {"senha": "123", "perfil": "Equipa da Farmácia", "nome": "Farmácia Central"},
    "enfermeiro": {"senha": "456", "perfil": "Enfermeiro de Referência", "nome": "Equipe de Enfermagem"},
    "familia": {"senha": "789", "perfil": "Cuidador / Família", "nome": "Acesso Familiar / Domiciliar"},
    "admin": {"senha": "admin", "perfil": "Administrador", "nome": "Gestão Geral"}
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
    st.title("💊 Gestão de Farmácia e Insumos - Assistência Domiciliar")
    st.subheader("🔐 Acesso ao Sistema")
    
    with st.form("form_login"):
        u_input = st.text_input("Utilizador").strip().lower()
        p_input = st.text_input("Palavra-passe", type="password")
        btn_login = st.form_submit_button("Entrar")
        
        if btn_login:
            realizar_login(u_input, p_input)
            
    st.info("💡 **Perfis de Acesso:**\n- **Farmácia/Admin:** `farmacia` (123) / `admin` (admin)\n- **Enfermeiro:** `enfermeiro` (456)\n- **Família:** `familia` (789)")
    st.stop()

# ==============================================================================
# 3. CABEÇALHO E ABAS DA APLICAÇÃO
# ==============================================================================
col_tit, col_user = st.columns([3, 1])
with col_tit:
    st.title("💊 Farmácia - Assistência Domiciliar")
    st.caption("Controle de Estoque, Dispensação por Paciente e Contagem Domiciliar")

with col_user:
    st.write(f"👤 **{st.session_state['usuario_nome']}**")
    st.caption(f"Perfil: {st.session_state['usuario_perfil']}")
    if st.button("🚪 Sair"):
        realizar_logout()

st.divider()

perfil = st.session_state["usuario_perfil"]

if perfil in ["Equipa da Farmácia", "Administrador"]:
    abas_nomes = ["📊 1. Painel & Alertas", "📦 2. Entradas & Lista de Compras", "🤝 3. Dispensação (Saídas)", "🏡 4. Contagens Domiciliares", "📋 5. Histórico & Pacientes"]
elif perfil == "Enfermeiro de Referência":
    abas_nomes = ["📊 1. Painel & Alertas", "🤝 3. Dispensação (Saídas)", "🏡 4. Contagens Domiciliares", "📋 5. Histórico & Pacientes"]
else:
    abas_nomes = ["🏠 Informar Estoque do Domicílio", "📋 Histórico de Contagens Enviadas"]

abas = st.tabs(abas_nomes)

def get_connection():
    return sqlite3.connect(DB_NAME)

# ==============================================================================
# MÓDULO EXCLUSIVO PARA O PERFIL: CUIDADOR / FAMÍLIA
# ==============================================================================
if perfil == "Cuidador / Família":
    with abas[0]:
        st.header("🏠 Informar Estoque Atual no Domicílio")
        st.write("Preencha os dados abaixo para informar à Farmácia e Enfermagem a quantidade atual de materiais/medicamentos em sua residência.")

        conn = get_connection()
        df_pacientes = pd.read_sql_query("SELECT * FROM pacientes ORDER BY nome_paciente ASC", conn)
        df_produtos = pd.read_sql_query("SELECT * FROM produtos ORDER BY nome ASC", conn)

        if df_pacientes.empty:
            st.warning("Nenhum paciente cadastrado.")
        else:
            lista_pacientes = df_pacientes["nome_paciente"].tolist()

            with st.form("form_contagem_familia"):
                pac_sel = st.selectbox("Selecione o Paciente *", lista_pacientes)
                
                dados_pac = df_pacientes[df_pacientes["nome_paciente"] == pac_sel].iloc[0]
                enf_ref = dados_pac["enfermeiro_referencia"]
                prog_pac = dados_pac["programa"]

                st.info(f"👩‍⚕️ **Enfermeira de Referência:** {enf_ref} | 📌 **Programa:** {prog_pac}")

                opcoes_produtos = ["-- Selecionar da lista --"] + df_produtos["nome"].tolist() + ["Outro (digitar manualmente)"] if not df_produtos.empty else ["Outro (digitar manualmente)"]
                item_opcao = st.selectbox("Selecione o Item / Medicamento *", opcoes_produtos)

                if item_opcao == "Outro (digitar manualmente)" or item_opcao == "-- Selecionar da lista --":
                    nome_item_final = st.text_input("Digite o nome do Medicamento / Material *", placeholder="Ex: Soro Fisiológico 500ml")
                else:
                    nome_item_final = item_opcao

                qtd_casa = st.number_input("Quantidade Atual na Residência *", min_value=0, value=1)
                nome_responsavel = st.text_input("Nome de quem realizou a contagem *", placeholder="Ex: Maria (Esposa / Cuidadora)")
                obs_familia = st.text_area("Observações para a Farmácia / Enfermagem", placeholder="Ex: Apenas 2 frascos restantes. Solicito envio para o próximo mês.")

                btn_enviar_contagem = st.form_submit_button("📤 Enviar Contagem para a Farmácia")

            if btn_enviar_contagem:
                if not nome_item_final.strip() or not nome_responsavel.strip():
                    st.error("⚠️ Por favor, informe o nome do item e o nome do responsável pela contagem.")
                else:
                    cursor = conn.cursor()
                    data_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute('''
                        INSERT INTO contagem_domicilio (
                            data_hora, paciente_nome, enfermeiro_referencia, produto_nome,
                            quantidade_domicilio, responsavel_contagem, observacao
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (data_agora, pac_sel, enf_ref, nome_item_final.strip(), qtd_casa, nome_responsavel.strip(), obs_familia))

                    conn.commit()
                    st.success("✅ Contagem enviada com sucesso! A farmácia e a equipe de enfermagem já têm acesso a estas informações.")
                    st.rerun()

        conn.close()

    with abas[1]:
        st.header("📋 Histórico de Contagens Enviadas")
        conn = get_connection()
        df_minhas_contagens = pd.read_sql_query("SELECT * FROM contagem_domicilio ORDER BY id DESC", conn)
        conn.close()

        if df_minhas_contagens.empty:
            st.info("Nenhuma contagem registrada até o momento.")
        else:
            st.dataframe(df_minhas_contagens[["data_hora", "paciente_nome", "produto_nome", "quantidade_domicilio", "responsavel_contagem", "observacao"]], use_container_width=True)

# ==============================================================================
# ABAS PARA FARMÁCIA / ADMINISTRADOR / ENFERMEIROS
# ==============================================================================
if perfil in ["Equipa da Farmácia", "Administrador", "Enfermeiro de Referência"]:

    # ABA 1: PAINEL GERAL & ALERTAS
    if "📊 1. Painel & Alertas" in abas_nomes:
        idx = abas_nomes.index("📊 1. Painel & Alertas")
        with abas[idx]:
            st.header("📊 Painel Geral de Estoque e Notificações Domiciliares")
            
            conn = get_connection()
            df_produtos = pd.read_sql_query("SELECT * FROM produtos", conn)
            df_mov = pd.read_sql_query("SELECT * FROM movimentacoes", conn)
            df_contagens_recentes = pd.read_sql_query("SELECT * FROM contagem_domicilio ORDER BY id DESC LIMIT 5", conn)
            conn.close()

            if df_produtos.empty:
                st.warning("Nenhum produto cadastrado até o momento. Cadastre itens na Aba 2.")
            else:
                df_criticos = df_produtos[df_produtos["quantidade_atual"] <= df_produtos["quantidade_minima"]]

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total de Itens Cadastrados", len(df_produtos))
                col2.metric("Itens com Estoque OK", len(df_produtos) - len(df_criticos))
                col3.metric("⚠️ Itens Críticos (Repor)", len(df_criticos), delta_color="inverse")
                col4.metric("Total de Dispensações", len(df_mov[df_mov["tipo_movimentacao"] == "Saída"]))

                st.divider()

                if not df_criticos.empty:
                    st.error("🚨 **ALERTAS DE ESTOQUE MÍNIMO ATINGIDO NA FARMÁCIA / COMPRA NECESSÁRIA:**")
                    st.dataframe(df_criticos[["nome", "categoria", "quantidade_atual", "quantidade_minima", "unidade_medida"]], use_container_width=True)
                else:
                    st.success("✅ Todos os itens da farmácia estão com estoque adequado!")

            st.divider()
            st.subheader("🏡 Últimas Contagens Domiciliares Enviadas pelas Famílias")
            if df_contagens_recentes.empty:
                st.info("Nenhuma contagem enviada pelas famílias ainda.")
            else:
                st.dataframe(df_contagens_recentes[["data_hora", "paciente_nome", "enfermeiro_referencia", "produto_nome", "quantidade_domicilio", "responsavel_contagem", "observacao"]], use_container_width=True)

    # ABA 2: ENTRADAS & COMPRAS
    if "📦 2. Entradas & Lista de Compras" in abas_nomes:
        idx = abas_nomes.index("📦 2. Entradas & Lista de Compras")
        with abas[idx]:
            st.header("📦 Gestão de Entradas e Compras")
            col_cad, col_ent = st.columns(2)

            conn = get_connection()
            df_produtos = pd.read_sql_query("SELECT * FROM produtos", conn)
            
            with col_cad:
                st.subheader("➕ Cadastrar Novo Medicamento / Insumo")
                with st.form("form_novo_produto"):
                    nome_p = st.text_input("Nome do Item / Medicamento *", placeholder="Ex: Soro Fisiológico 0,9% 500ml")
                    cat_p = st.selectbox("Categoria *", ["Medicamento", "Insumo / Curativo", "Equipamento", "Dieta / Nutrição", "Outros"])
                    qtd_ini = st.number_input("Quantidade Inicial", min_value=0, value=0)
                    qtd_min = st.number_input("Estoque Mínimo (Crítico) *", min_value=1, value=10)
                    unidade = st.selectbox("Unidade *", ["Frasco", "Caixa", "Unidade", "Ampola", "Pacote", "Rolo"])
                    btn_cad = st.form_submit_button("💾 Cadastrar Produto")

                if btn_cad:
                    if nome_p.strip():
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO produtos (nome, categoria, quantidade_atual, quantidade_minima, unidade_medida) VALUES (?, ?, ?, ?, ?)",
                                       (nome_p.strip(), cat_p, qtd_ini, qtd_min, unidade))
                        conn.commit()
                        st.success(f"Item '{nome_p}' cadastrado!")
                        st.rerun()

            with col_ent:
                st.subheader("📥 Registrar Entrada de Nota / Reposição")
                if not df_produtos.empty:
                    with st.form("form_entrada"):
                        prod_sel = st.selectbox("Selecione o Item", df_produtos["nome"].tolist())
                        qtd_in = st.number_input("Quantidade Recebida", min_value=1, value=1)
                        obs_in = st.text_input("Observação / Nº da Nota", placeholder="Ex: NF 9876")
                        btn_in = st.form_submit_button("📥 Confirmar Entrada")

                    if btn_in:
                        p_id = df_produtos[df_produtos["nome"] == prod_sel]["id"].values[0]
                        qtd_at = df_produtos[df_produtos["nome"] == prod_sel]["quantidade_atual"].values[0]
                        
                        cursor = conn.cursor()
                        cursor.execute("UPDATE produtos SET quantidade_atual = ? WHERE id = ?", (qtd_at + qtd_in, p_id))
                        cursor.execute("INSERT INTO movimentacoes (data_hora, tipo_movimentacao, produto_id, produto_nome, quantidade, observacao) VALUES (?, 'Entrada', ?, ?, ?, ?)",
                                       (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), p_id, prod_sel, qtd_in, obs_in))
                        conn.commit()
                        st.success(f"+{qtd_in} unidades adicionadas!")
                        st.rerun()

            conn.close()

            st.divider()

            st.subheader("🛒 Lista de Compras Automática")
            conn = get_connection()
            df_compras = pd.read_sql_query("SELECT * FROM produtos WHERE quantidade_atual <= quantidade_minima", conn)
            conn.close()

            if df_compras.empty:
                st.success("Nenhum item precisa de compra na farmácia no momento.")
            else:
                df_compras["Sugestão de Compra"] = df_compras["quantidade_minima"] * 2 - df_compras["quantidade_atual"]
                st.dataframe(df_compras[["nome", "categoria", "quantidade_atual", "quantidade_minima", "Sugestão de Compra", "unidade_medida"]], use_container_width=True)
                
                csv_c = df_compras.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Baixar Lista de Compras (Excel/CSV)", data=csv_c, file_name="lista_compras.csv", mime="text/csv")

    # ABA 3: DISPENSAÇÃO
    if "🤝 3. Dispensação (Saídas)" in abas_nomes:
        idx = abas_nomes.index("🤝 3. Dispensação (Saídas)")
        with abas[idx]:
            st.header("🤝 Registro de Saída / Dispensação Mensal")

            conn = get_connection()
            df_produtos = pd.read_sql_query("SELECT * FROM produtos WHERE quantidade_atual > 0", conn)
            df_pacientes = pd.read_sql_query("SELECT * FROM pacientes ORDER BY nome_paciente ASC", conn)

            if df_produtos.empty:
                st.error("⚠️ Sem estoque disponível na farmácia para dispensação.")
            elif df_pacientes.empty:
                st.warning("Nenhum paciente cadastrado.")
            else:
                lista_nomes_pacientes = df_pacientes["nome_paciente"].tolist()

                with st.form("form_dispensacao"):
                    st.subheader("📋 Formulário de Saída de Insumos")
                    c1, c2 = st.columns(2)

                    with c1:
                        pac_sel = st.selectbox("Selecione o Paciente *", lista_nomes_pacientes)
                        
                        dados_pac = df_pacientes[df_pacientes["nome_paciente"] == pac_sel].iloc[0]
                        enf_ref = dados_pac["enfermeiro_referencia"]
                        prog_pac = dados_pac["programa"]
                        tel_pac = dados_pac.get("telefone", "Não informado")

                        st.info(f"👩‍⚕️ **Enfermeira de Referência:** {enf_ref}\n\n📌 **Programa:** {prog_pac} | 📞 **Telefone:** {tel_pac}")

                        item_disp = st.selectbox("Medicamento / Insumo Solicitado *", df_produtos["nome"].tolist())
                        qtd_disp = df_produtos[df_produtos["nome"] == item_disp]["quantidade_atual"].values[0]
                        unid_disp = df_produtos[df_produtos["nome"] == item_disp]["unidade_medida"].values[0]
                        st.caption(f"Saldo atual em estoque: **{qtd_disp} {unid_disp}**")

                    with c2:
                        qtd_retirada = st.number_input(f"Quantidade Entregue ({unid_disp}) *", min_value=1, max_value=int(qtd_disp), value=1)
                        nome_retirou = st.text_input("Nome do Responsável pela Retirada (Cuidador/Familiar) *", placeholder="Ex: Maria (Esposa)")
                        obs_disp = st.text_area("Contagem / Observações do Domicílio", placeholder="Ex: Entregue lote referente ao mês. Contagem inicial em domicílio realizada.")

                    btn_disp = st.form_submit_button("✅ Salvar e Registrar Saída")

                if btn_disp:
                    if not nome_retirou.strip():
                        st.error("⚠️ Digite o nome do responsável pela retirada.")
                    else:
                        p_id = df_produtos[df_produtos["nome"] == item_disp]["id"].values[0]
                        nova_qtd = qtd_disp - qtd_retirada

                        cursor = conn.cursor()
                        cursor.execute("UPDATE produtos SET quantidade_atual = ? WHERE id = ?", (nova_qtd, p_id))
                        
                        data_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute('''
                            INSERT INTO movimentacoes (
                                data_hora, tipo_movimentacao, produto_id, produto_nome, quantidade,
                                paciente_nome, enfermeiro_referencia, responsavel_retirada, observacao
                            ) VALUES (?, 'Saída', ?, ?, ?, ?, ?, ?, ?)
                        ''', (data_agora, p_id, item_disp, qtd_retirada, pac_sel, enf_ref, nome_retirou.strip(), obs_disp))

                        conn.commit()
                        st.success(f"✅ Saída de {qtd_retirada}x {item_disp} registrada com sucesso para o paciente {pac_sel}!")
                        st.rerun()

            conn.close()

    # ABA 4: ACOMPANHAMENTO DE CONTAGENS DOMICILIARES COM NOTIFICAÇÃO VIA WHATSAPP
    if "🏡 4. Contagens Domiciliares" in abas_nomes:
        idx = abas_nomes.index("🏡 4. Contagens Domiciliares")
        with abas[idx]:
            st.header("🏡 Acompanhamento do Estoque nos Domicílios (Famílias)")
            st.write("Consulte as contagens enviadas pelos cuidadores e envie notificações via WhatsApp diretamente.")

            conn = get_connection()
            df_todas_contagens = pd.read_sql_query("SELECT * FROM contagem_domicilio ORDER BY id DESC", conn)
            df_pacientes = pd.read_sql_query("SELECT * FROM pacientes ORDER BY nome_paciente ASC", conn)
            conn.close()

            if df_todas_contagens.empty:
                st.info("Nenhuma contagem domiciliar registrada até o momento.")
            else:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    filtro_pac = st.selectbox("Filtrar por Paciente:", ["Todos"] + df_pacientes["nome_paciente"].tolist())
                with col_f2:
                    enfermeiros_unicos = ["Todos"] + sorted(list(df_todas_contagens["enfermeiro_referencia"].unique()))
                    filtro_enf = st.selectbox("Filtrar por Enfermeiro de Referência:", enfermeiros_unicos)

                df_cont_filtrado = df_todas_contagens.copy()
                if filtro_pac != "Todos":
                    df_cont_filtrado = df_cont_filtrado[df_cont_filtrado["paciente_nome"] == filtro_pac]
                if filtro_enf != "Todos":
                    df_cont_filtrado = df_cont_filtrado[df_cont_filtrado["enfermeiro_referencia"] == filtro_enf]

                st.write(f"Exibindo **{len(df_cont_filtrado)}** registro(s):")
                
                # Exibição detalhada item a item com botão interativo de WhatsApp
                for idx_row, row in df_cont_filtrado.iterrows():
                    # Busca o telefone do paciente
                    tel_pac_encontrado = ""
                    if not df_pacientes.empty and row["paciente_nome"] in df_pacientes["nome_paciente"].values:
                        tel_pac_encontrado = df_pacientes[df_pacientes["nome_paciente"] == row["paciente_nome"]]["telefone"].values[0]

                    with st.expander(f"📌 {row['paciente_nome']} - {row['produto_nome']} (Qtd no Domicílio: {row['quantidade_domicilio']})"):
                        st.write(f"**Data/Hora do Registro:** {row['data_hora']}")
                        st.write(f"**Enfermeira de Referência:** {row['enfermeiro_referencia']}")
                        st.write(f"**Responsável que Contou:** {row['responsavel_contagem']}")
                        st.write(f"**Observação:** {row['observacao']}")

                        st.divider()
                        
                        # Campo de telefone editável e montagem do link do WhatsApp
                        tel_input = st.text_input("WhatsApp do Responsável / Paciente (com DDD):", value=tel_pac_encontrado, key=f"tel_dom_{row['id']}")
                        
                        mensagem_wa = f"""*Acompanhamento de Estoque Domiciliar - Farmácia* 🏥

Olá! Recebemos o registro de contagem do paciente *{row['paciente_nome']}*:

- *Item/Material:* {row['produto_nome']}
- *Quantidade em casa:* {row['quantidade_domicilio']}
- *Responsável:* {row['responsavel_contagem']}
- *Observação:* {row['observacao']}

Estamos acompanhando a necessidade de reposição/envio junto à Enfermeira responsável *{row['enfermeiro_referencia']}*.
Agradecemos a colaboração!"""

                        msg_encoded = urllib.parse.quote(mensagem_wa)
                        link_whatsapp = f"https://wa.me/{tel_input.strip()}?text={msg_encoded}"

                        if tel_input.strip():
                            st.markdown(f'''
                                <a href="{link_whatsapp}" target="_blank">
                                    <button style="background-color: #25D366; color: white; padding: 10px 18px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">
                                        📱 Enviar Confirmação via WhatsApp
                                    </button>
                                </a>
                            ''', unsafe_allow_html=True)
                        else:
                            st.warning("⚠️ Insira o número do telefone acima para ativar o botão do WhatsApp.")

                st.divider()
                csv_domicilio = df_cont_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Baixar Relatório Domiciliar (Excel/CSV)", data=csv_domicilio, file_name="contagens_domiciliares.csv", mime="text/csv")

    # ABA 5: HISTÓRICO GERAL
    if "📋 5. Histórico & Pacientes" in abas_nomes:
        idx = abas_nomes.index("📋 5. Histórico & Pacientes")
        with abas[idx]:
            st.header("📋 Histórico Geral de Movimentações")

            conn = get_connection()
            df_mov = pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY id DESC", conn)
            df_pac = pd.read_sql_query("SELECT * FROM pacientes ORDER BY nome_paciente ASC", conn)
            conn.close()

            if df_mov.empty:
                st.info("Nenhuma movimentação registrada.")
            else:
                st.subheader("🔍 Filtros de Consulta")
                f1, f2, f3 = st.columns(3)
                with f1:
                    t_f = st.selectbox("Tipo:", ["Todos", "Entrada", "Saída"])
                with f2:
                    p_f = st.selectbox("Paciente:", ["Todos"] + df_pac["nome_paciente"].tolist())
                with f3:
                    e_f = st.selectbox("Enfermeiro de Referência:", ["Todos"] + sorted(list(df_pac["enfermeiro_referencia"].unique())))

                df_f = df_mov.copy()
                if t_f != "Todos":
                    df_f = df_f[df_f["tipo_movimentacao"] == t_f]
                if p_f != "Todos":
                    df_f = df_f[df_f["paciente_nome"] == p_f]
                if e_f != "Todos":
                    df_f = df_f[df_f["enfermeiro_referencia"] == e_f]

                st.write(f"Exibindo **{len(df_f)}** registro(s):")
                st.dataframe(df_f, use_container_width=True)

                csv_hist = df_f.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Baixar Histórico Filtrado (Excel/CSV)", data=csv_hist, file_name="historico_farmacia.csv", mime="text/csv")
