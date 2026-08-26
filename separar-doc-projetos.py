import streamlit as st
import pandas as pd
import zipfile
import io
import re

# Função para garantir que o valor seja lido como número, mesmo se o Excel estiver formatado como texto (ex: "1.000,00")
def limpar_valor(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    val_str = str(val).strip()
    # Converte padrão brasileiro para padrão de computador
    if ',' in val_str and '.' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
        
    try:
        return float(val_str)
    except:
        return 0.0

# --- Interface Visual ---
st.title("Separador de PDFs por Projeto✂️📂")
st.write("O sistema lerá a 'Ordem' do arquivo, verificará o valor no projeto selecionado e descartará os itens com valor 0,00.")

planilha_enviada = st.file_uploader("1. Envie a Planilha (Excel)", type=["xlsx", "xls"])
arquivos_enviados = st.file_uploader("2. Envie os PDFs (já renomeados com a Ordem)", type=["pdf"], accept_multiple_files=True)

if planilha_enviada:
    try:
        df = pd.read_excel(planilha_enviada)
        
        st.write("---")
        st.write("⚙️ **Configuração das Colunas**")
        
        colunas = df.columns.tolist()
        col_ordem = st.selectbox("Qual coluna contém a ORDEM (001, 002...)?", colunas)
        col_valor = st.selectbox("Qual é a coluna do PROJETO (para checar os valores)?", colunas)
        
        if arquivos_enviados and st.button("Filtrar Arquivos"):
            with st.spinner("Analisando valores..."):
                
                # 1. Identificar quais "Ordens" têm valor maior que zero
                ordens_validas = []
                
                for index, row in df.iterrows():
                    valor = limpar_valor(row[col_valor])
                    
                    if valor > 0:
                        # Pega a ordem (ex: 10) e formata para 3 dígitos (ex: "010")
                        ordem = str(row[col_ordem]).strip()
                        if ordem.replace('.0', '').isdigit():
                            ordem_formatada = str(int(float(ordem))).zfill(3)
                            ordens_validas.append(ordem_formatada)
                
                # 2. Filtrar os PDFs
                zip_buffer = io.BytesIO()
                arquivos_salvos = 0
                arquivos_ignorados = []
                
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    for arquivo in arquivos_enviados:
                        nome_pdf = arquivo.name
                        
                        # Captura os primeiros números do nome do arquivo (ex: pega "010" de "010 - Medicsys...")
                        match_ordem_pdf = re.match(r'^(\d+)\s*-', nome_pdf)
                        
                        if match_ordem_pdf:
                            ordem_do_pdf = match_ordem_pdf.group(1).zfill(3)
                            
                            # Se a ordem do PDF estiver na nossa lista de valores > 0, ele entra no ZIP
                            if ordem_do_pdf in ordens_validas:
                                zip_file.writestr(nome_pdf, arquivo.getvalue())
                                arquivos_salvos += 1
                            else:
                                arquivos_ignorados.append(nome_pdf)
                        else:
                            # Se por acaso o arquivo não tiver a ordem no nome, guarda numa lista de aviso
                            arquivos_ignorados.append(f"{nome_pdf} (Sem nº de ordem no nome)")
                
                # 3. Mostrar os Resultados
                st.success(f"🎉 Pronto! {arquivos_salvos} arquivos possuíam valor e foram separados no ZIP.")
                
                if arquivos_ignorados:
                    st.warning(f"⚠️ {len(arquivos_ignorados)} arquivos foram ignorados (Zerados no projeto ou erro de nome).")
                    with st.expander("Ver lista de arquivos ignorados"):
                        for arq in arquivos_ignorados:
                            st.write(f"- {arq}")
                
                if arquivos_salvos > 0:
                    st.download_button(
                        label="⬇️ Baixar PDFs Válidos (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"PDFs_Filtrados_{col_valor[:10].replace(' ', '_')}.zip",
                        mime="application/zip"
                    )
                
    except Exception as e:
        st.error(f"❌ Erro ao ler a planilha. Detalhe: {e}")
