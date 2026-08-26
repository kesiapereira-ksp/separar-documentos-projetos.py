import streamlit as st
import pandas as pd
import zipfile
import io

# --- Interface Visual do Site ---
st.title("Filtro de PDFs por Valor na Planilha 🗂️💰")
st.write("Envie sua planilha e seus PDFs. O sistema vai ignorar os itens zerados na planilha e devolver apenas os arquivos válidos.")

# 1. Uploads
planilha_enviada = st.file_uploader("1. Envie a Planilha (Excel)", type=["xlsx", "xls"])
arquivos_enviados = st.file_uploader("2. Envie os PDFs", type=["pdf"], accept_multiple_files=True)

if planilha_enviada:
    try:
        # Lê a planilha
        df = pd.read_excel(planilha_enviada)
        
        st.write("---")
        st.write("⚙️ **Configuração das Colunas**")
        
        colunas = df.columns.tolist()
        
        # O usuário escolhe onde está a chave do documento e onde está o valor
        col_chave = st.selectbox("Qual coluna contém a IDENTIFICAÇÃO do arquivo (ex: Nome, NF, Histórico)?", colunas)
        col_valor = st.selectbox("Qual coluna contém o VALOR (para filtrar os zerados)?", colunas)
        
        if arquivos_enviados and st.button("Filtrar Documentos"):
            with st.spinner("Analisando valores e separando arquivos..."):
                
                # 1. Limpeza dos Dados: Transforma a coluna de valor em número (ignora erros/textos)
                df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce')
                
                # 2. Filtra a planilha: Mantém apenas as linhas onde o valor é MAIOR que zero
                df_validos = df[df[col_valor] > 0]
                
                # 3. Cria uma lista com as chaves (nomes/NFs) que passaram no filtro
                chaves_validas = df_validos[col_chave].dropna().astype(str).tolist()
                
                # Limpa as chaves para facilitar a busca (tudo minúsculo e sem espaços sobrando)
                chaves_validas = [chave.strip().lower() for chave in chaves_validas]
                
                # 4. Prepara o arquivo ZIP
                zip_buffer = io.BytesIO()
                arquivos_salvos = 0
                arquivos_ignorados = 0
                
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    for arquivo in arquivos_enviados:
                        nome_pdf = arquivo.name.lower()
                        
                        # Verifica se alguma das chaves válidas da planilha está escrita no nome do PDF
                        # Ex: Se a chave for "NF.123", ele checa se "nf.123" faz parte do nome do arquivo
                        arquivo_valido = False
                        for chave in chaves_validas:
                            if chave in nome_pdf:
                                arquivo_valido = True
                                break # Achou a chave, não precisa continuar procurando
                        
                        # Se for válido, coloca no ZIP
                        if arquivo_valido:
                            zip_file.writestr(arquivo.name, arquivo.getvalue())
                            arquivos_salvos += 1
                        else:
                            arquivos_ignorados += 1
                
                # 5. Exibe os resultados
                st.success(f"🎉 Pronto! {arquivos_salvos} arquivos possuíam valor e foram separados.")
                
                if arquivos_ignorados > 0:
                    st.info(f"ℹ️ {arquivos_ignorados} arquivos foram ignorados (valor zerado ou não encontrados na planilha).")
                
                # Botão de Download do ZIP pronto
                if arquivos_salvos > 0:
                    st.download_button(
                        label="⬇️ Baixar PDFs Válidos (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="PDFs_Com_Valor.zip",
                        mime="application/zip"
                    )
                
    except Exception as e:
        st.error(f"❌ Erro ao processar. Detalhe: {e}")

elif arquivos_enviados and not planilha_enviada:
    st.info("⚠️ Envie a planilha primeiro para configurar as colunas.")
