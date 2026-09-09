import streamlit as st
import pandas as pd
import zipfile
import io
import re

# Função para garantir que o valor seja lido como número (ex: "1.000,00" -> 1000.0)
def limpar_valor(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    val_str = str(val).strip()
    if ',' in val_str and '.' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
        
    try:
        return float(val_str)
    except:
        return 0.0

# Limpa caracteres especiais do nome do projeto para evitar erros ao criar pastas
def limpar_nome_pasta(nome):
    return re.sub(r'[\\/*?:"<>|]', '_', str(nome)).strip()

# --- Interface Visual ---
st.title("Separador de PDFs por Projeto ✂️📂")
st.write("O sistema organizará os PDFs em pastas individuais para cada projeto dentro do arquivo ZIP.")

planilha_enviada = st.file_uploader("1. Envie a Planilha (Excel)", type=["xlsx", "xls"])
arquivos_enviados = st.file_uploader("2. Envie os PDFs (já renomeados com a Ordem)", type=["pdf"], accept_multiple_files=True)

if planilha_enviada:
    try:
        df = pd.read_excel(planilha_enviada)
        colunas = df.columns.tolist()
        
        st.write("---")
        st.write("⚙️ **Configuração das Colunas**")
        
        col_ordem = st.selectbox("Qual coluna contém a ORDEM (001, 002...)?", colunas)
        
        # Seleção múltipla para escolher quais projetos deseja processar de uma vez
        projetos_selecionados = st.multiselect(
            "Selecione os PROJETOS (colunas) que deseja separar:",
            options=colunas,
            default=[col for col in colunas if any(p in str(col).lower() for p in ['contrato', 'convenio'])]
        )
        
        if arquivos_enviados and projetos_selecionados and st.button("Separar PDFs por Projeto"):
            with st.spinner("Organizando arquivos por pasta de projeto..."):
                
                zip_buffer = io.BytesIO()
                resumo_projetos = {}
                
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    
                    # Processa cada projeto selecionado individualmente
                    for col_projeto in projetos_selecionados:
                        nome_pasta = limpar_nome_pasta(col_projeto)
                        
                        # 1. Identificar Ordens válidas (> 0) para o projeto atual
                        ordens_validas = set()
                        for _, row in df.iterrows():
                            valor = limpar_valor(row[col_projeto])
                            if valor > 0:
                                ordem = str(row[col_ordem]).strip()
                                if ordem.replace('.0', '').isdigit():
                                    ordens_validas.add(str(int(float(ordem))).zfill(3))
                        
                        # 2. Filtrar e incluir PDFs na pasta do projeto dentro do ZIP
                        qtd_salvos = 0
                        for arquivo in arquivos_enviados:
                            nome_pdf = arquivo.name
                            match_prefixo = re.match(r'^(.*?)\s*-', nome_pdf)
                            
                            if match_prefixo:
                                prefixo_texto = match_prefixo.group(1)
                                numeros_encontrados = re.findall(r'\d+', prefixo_texto)
                                ordens_do_pdf = [num.zfill(3) for num in numeros_encontrados]
                                
                                # Se o PDF pertence a este projeto, grava na pasta do projeto
                                if any(ordem in ordens_validas for ordem in ordens_do_pdf):
                                    caminho_no_zip = f"{nome_pasta}/{nome_pdf}"
                                    zip_file.writestr(caminho_no_zip, arquivo.getvalue())
                                    qtd_salvos += 1
                        
                        resumo_projetos[col_projeto] = qtd_salvos
                
                # 3. Exibir resultados do processamento
                st.success("🎉 Arquivos separados com sucesso!")
                
                st.write("📊 **Resumo dos PDFs separados por Projeto:**")
                for proj, qtd in resumo_projetos.items():
                    st.write(f"- **{proj}**: {qtd} PDF(s)")
                
                st.download_button(
                    label="⬇️ Baixar ZIP Completo (Com Subpastas por Projeto)",
                    data=zip_buffer.getvalue(),
                    file_name="PDFs_Separados_Por_Projeto.zip",
                    mime="application/zip"
                )
                
    except Exception as e:
        st.error(f"❌ Erro ao ler a planilha. Detalhe: {e}")
