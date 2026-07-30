# 📈 Resumidor de Noticias & Morning Call Automático

Este projeto agrega as principais notícias do dia, filtra as que citam os ativos da sua carteira, incorpora **projeções econômicas do Boletim Focus/Bacen** e usa a IA **Google Gemini** para gerar um "Morning Call" personalizado enviado diretamente para o seu Telegram.

## 🚀 Como Funciona?

1.  **Coleta de Notícias**: Busca notícias em tempo real via RSS (InfoMoney, Money Times, Valor, Exame, etc.).
2.  **Leitura da Carteira**: Extrai o texto do extrato (`wallet.pdf` local ou variável `CARTEIRA` em produção) e usa o Gemini para identificar os **ativos** (ticker, tipo, descrição).
3.  **Projeções Macro**: Consulta a API gratuita do Banco Central (Focus/SGS) para Selic, IPCA, Câmbio e PIB — valor atual e projeção.
4.  **Notícias Conectadas**: Filtra as notícias que citam seus ativos e extrai o **texto completo** das matérias (scraping com `trafilatura`) para análises mais profundas.
5.  **Processamento com IA**: O Gemini gera o Morning Call cruzando notícias gerais, notícias da carteira e projeções macro.
6.  **Entrega**: Texto formatado em blocos enviado via Bot do Telegram.
7.  **Automação**: Roda automaticamente 3 vezes ao dia via GitHub Actions.

## ✨ Funcionalidades Principais

* **Análise Multi-Setorial**: Cenário Global, Nacional, Projeções (Focus), Empresas, Agro e Tecnologia.
* **Notícias Conectadas à Carteira**: Seção dedicada que cruza notícias (com texto completo) aos seus ativos.
* **Projeções Econômicas**: Selic, IPCA, Câmbio e PIB do Boletim Focus/Bacen, com valor atual e câmbio atual.
* **Fallback de Modelos**: Alterna entre versões do Gemini (e Groq) caso ocorra erro de cota.
* **Arquitetura Modular**: Código organizado em `src/` (wallet, market, news, analysis, delivery).

## 🛠️ Tecnologias Utilizadas

* **Python 3.11+**
* **Google Gemini API**: Estruturação dos ativos da carteira e geração da análise.
* **API Olinda/BCB (Focus/SGS)**: Projeções macroeconômicas (gratuita).
* **yfinance**: Cotação atual do câmbio.
* **Feedparser + Trafilatura**: RSS e extração do texto completo das matérias.
* **PyPDF2**: Extração de texto do extrato em PDF.
* **Telegram Bot API**: Entrega de texto via chat.
* **GitHub Actions**: Automação e agendamento via Cron.

## ⚙️ Configuração e Instalação

### Instalação Local

1.  Clone o repositório:
    ```bash
    git clone [https://github.com/seu-usuario/Resumidor_Noticias.git](https://github.com/seu-usuario/Resumidor_Noticias.git)
    cd Resumidor_Noticias
    ```
2.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
3.  Crie um arquivo `.env` na raiz do projeto com suas credenciais:
    ```env
    GEMINI_KEY=sua_chave_aqui
    TELEGRAM_TOKEN=token_do_seu_bot
    CHAT_ID=seu_id_do_telegram
    # Opcional:
    GROQ_KEY=chave_groq_para_fallback
    ```
4.  Coloque o seu extrato da carteira renomeado para `wallet.pdf` na raiz da pasta.

## 🤖 Automação (GitHub Actions)

Para que o projeto rode na nuvem de forma segura e agendada:

1.  **Extração do Texto**: Rode `python leitor_wallet.py` no seu computador e copie todo o texto extraído da sua carteira que aparecer no terminal.
2.  **Configurar Secrets**: No seu repositório GitHub, vá em *Settings > Secrets and variables > Actions* e adicione as chaves:
    * `GEMINI_KEY`, `TELEGRAM_TOKEN`, `CHAT_ID`.
    * `CARTEIRA`: Cole aqui o texto que você copiou no passo 1.
    * *(Opcional)* `GROQ_KEY`.
3.  **Ativação Obrigatória**:
    > ⚠️ **IMPORTANTE**: O agendamento automático do GitHub Actions (Cron) só entrará em vigor após você executar o workflow manualmente pela primeira vez.
    * Vá na aba **Actions** do repositório.
    * Selecione o workflow **Resumidor Diario de Noticias**.
    * Clique no botão **Run workflow**. Isso valida suas credenciais e "acorda" o sistema de agendamento.

## 🛡️ Segurança

* Os arquivos `wallet.pdf`, `.env` e a pasta `.venv/` estão no `.gitignore` e **nunca** vão para o repositório.
* O acesso aos dados financeiros no GitHub Actions é feito exclusivamente via *Secrets* criptografados.

---
_Este projeto foi desenvolvido para fins acadêmicos e de automação pessoal. Decisões financeiras devem ser tomadas com cautela._
