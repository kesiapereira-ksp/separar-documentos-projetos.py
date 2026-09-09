import streamlit as st
import pandas as pd
import zipfile
import io
import re

@st.cache_data
def carregar_planilha(file):
    return pd.read_excel(file)

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

def limpar_nome_pasta(nome):
    return re.sub(r'[\\/*?:"<>|]', '_', str(nome)).strip()

# --- Interface Visual ---
st.title("Separador de PDFs por Projeto")
st.write("O sistema organizará os PDFs em pastas individuais para cada projeto selecionado.")

planilha_enviada = st.file_uploader("1. Envie a Planilha (Excel)", type=["xlsx", "xls"], key="file_excel")
arquivos_enviados = st.file_uploader("2. Envie os PDFs (já renomeados com a Ordem)", type=["pdf"], accept_multiple_files=True, key="files_pdf")

if planilha_enviada:
    try:
        df = carregar_planilha(planilha_enviada)
        colunas = df.columns.tolist()
        
        st.write("---")
        st.write("⚙️ **Configuração das Colunas**")
        
        col_ordem = st.selectbox(
            "Qual coluna contém a ORDEM (001, 002...)?", 
            options=colunas,
            key="select_ordem"
        )
        
        projetos_selecionados = st.multiselect(
            "Selecione os PROJETOS (colunas) que deseja separar:",
            options=colunas,
            key="select_projetos"
        )
        
        if arquivos_enviados and projetos_selecionados and st.button("Separar PDFs por Projeto", key="btn_filtrar"):
            with st.spinner("Processando e otimizando arquivos..."):
                
                # Otimização 1: Mapeia as ordens de TODOS os PDFs de uma só vez (executa Regex apenas 1x por arquivo)
                mapa_pdfs_ordens = []
                for arquivo in arquivos_enviados:
                    nome_pdf = arquivo.name
                    match_prefixo = re.match(r'^(.*?)\s*-', nome_pdf)
                    
                    if match_prefixo:
                        prefixo_texto = match_prefixo.group(1)
                        numeros = re.findall(r'\d+', prefixo_texto)
                        ordens_formatadas = [num.zfill(3) for num in numeros]
                        mapa_pdfs_ordens.append({
                            "obj": arquivo,
                            "nome": nome_pdf,
                            "ordens": ordens_formatadas
                        })

                zip_buffer = io.BytesIO()
                resumo_projetos = {}
                
                # Otimização 2: Gravação sequencial do ZIP
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    for col_projeto in projetos_selecionados:
                        nome_pasta = limpar_nome_pasta(col_projeto)
                        
                        # Extrai ordens válidas (> 0) no projeto atual
                        ordens_validas = set()
                        for _, row in df.iterrows():
                            valor = limpar_valor(row[col_projeto])
                            if valor > 0:
                                ordem = str(row[col_ordem]).strip()
                                if ordem.replace('.0', '').isdigit():
                                    ordens_validas.add(str(int(float(ordem))).zfill(3))
                        
                        # Associa e inclui no ZIP
                        qtd_salvos = 0
                        for item in mapa_pdfs_ordens:
                            if any(ordem in ordens_validas for ordem in item["ordens"]):
                                caminho_no_zip = f"{nome_pasta}/{item['nome']}"
                                zip_file.writestr(caminho_no_zip, item["obj"].getvalue())
                                qtd_salvos += 1
                        
                        resumo_projetos[col_projeto] = qtd_salvos
                
                st.success("🎉 Arquivos separados com sucesso!")
                
                st.write("📊 **Resumo dos PDFs separados por Projeto:**")
                for proj, qtd in resumo_projetos.items():
                    st.write(f"- **{proj}**: {qtd} PDF(s)")
                
                st.download_button(
                    label="⬇️ Baixar ZIP Completo (Com Subpastas)",
                    data=zip_buffer.getvalue(),
                    file_name="PDFs_Separados_Por_Projeto.zip",
                    mime="application/zip",
                    key="btn_download"
                )
                
    except Exception as e:
        st.error(f"❌ Erro ao processar: {e}")
