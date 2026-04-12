import PyPDF2 


def extrair_carteira(pdf):

    texto_carteira = ""

    with open(pdf,"rb") as wallet :
        leitor = PyPDF2.PdfReader(wallet)

        for i in range(len(leitor.pages)) :
            pagina = leitor.pages[i]
            texto_carteira += f"--- PÁGINA {i+1} ---\n{pagina.extract_text()}\n"

    return texto_carteira

