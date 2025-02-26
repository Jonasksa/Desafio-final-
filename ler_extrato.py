import pdfplumber
import re
import pandas as pd
from fpdf import FPDF

MAPEAMENTO_NOMES = {
    "uber": ["uber", "uber* trip", "uber uber *one help.ub", "uber uber *trip help.u"],
    "Spotify": ["Dm *Spotify"],
    "apple": ["apple.com/bill"],
    "netflix": ["netflix.com", "netflixcom"],
    "mc donalds": ["mcdonalds"],
    "americanas": ["lojas americanas"],
}

def normalizar_nome(descricao):
    descricao = descricao.lower().strip()
    descricao = re.sub(r"[^a-z0-9 ]", "", descricao)

    for nome_padrao, variações in MAPEAMENTO_NOMES.items():
        if any(var in descricao for var in variações):
            return nome_padrao  

    return descricao  

def extrair_transacoes(arquivo_pdf):
    transacoes = []
    capturar = False

    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto:
                continue  

            linhas = texto.split("\n")
            for linha in linhas:
                if "TRANSAÇÕES DE" in linha:
                    capturar = True  
                    continue

                if capturar:
                    match = re.match(r"(\d{2} \w{3}) (.+) R\$ ([\d,.]+)", linha)
                    if match:
                        data, descricao, valor = match.groups()
                        valor = float(valor.replace(".", "").replace(",", "."))  
                        descricao = normalizar_nome(descricao)  
                        transacoes.append([data, descricao, valor])

    return pd.DataFrame(transacoes, columns=["Data", "Descrição", "Valor"])

def salvar_txt(df, valor_total, nome_arquivo):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("Relatório de Transações\n")
        f.write("=" * 30 + "\n")
        for _, row in df.iterrows():
            f.write(f"{row['Descrição']}: R$ {row['Valor']:.2f}\n")
        f.write("=" * 30 + "\n")
        f.write(f"Total: R$ {valor_total:.2f}\n")

def salvar_pdf(df, valor_total, nome_arquivo):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Relatório de Transações", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    for _, row in df.iterrows():
        pdf.cell(0, 10, f"{row['Descrição']}: R$ {row['Valor']:.2f}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(0, 10, f"Total: R$ {valor_total:.2f}", ln=True)
    
    pdf.output(nome_arquivo)

def processar_extrato(arquivo_pdf):
    df = extrair_transacoes(arquivo_pdf)
    if df.empty:
        print("Nenhuma transação encontrada no PDF.")
        return
    
    resumo = df.groupby("Descrição")["Valor"].sum().reset_index()
    resumo = resumo.sort_values(by="Valor", ascending=False)

    valor_total = resumo["Valor"].sum()

    salvar_txt(resumo, valor_total, "relatorio.txt")
    salvar_pdf(resumo, valor_total, "relatorio.pdf")

    print(resumo)
    print(f"Total: R$ {valor_total:.2f}")
    print("Relatórios salvos como 'relatorio.txt' e 'relatorio.pdf'.")

if __name__ == "__main__":
    arquivo = "extrato.pdf"  
    processar_extrato(arquivo)
