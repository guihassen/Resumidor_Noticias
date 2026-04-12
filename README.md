# 📈 Resumidor de Noticias & Morning Call Automático

Este projeto é um sistema inteligente de curadoria e análise de notícias voltado para investidores. Ele agrega as principais notícias do dia através de RSS feeds, cruza essas informações com os ativos da sua carteira de investimentos pessoal e utiliza a IA **Google Gemini** para gerar um "Morning Call" personalizado, enviado diretamente para o seu Telegram.

## 🚀 Como Funciona?

1.  **Coleta de Dados**: O script busca notícias em tempo real de fontes renomadas (InfoMoney, Money Times, Exame, Canaltech, etc.).
2.  **Leitura de Carteira (Híbrida)**: 
    * **Localmente**: Extrai informações de ativos, quantidades e preços a partir de um arquivo `wallet.pdf` na raiz do projeto.
    * **Em Produção**: Utiliza a variável de ambiente `CARTEIRA` para processar os dados sem necessidade do arquivo físico no servidor.
3.  **Processamento com IA**: Utiliza modelos avançados do Gemini para analisar o impacto macroeconômico especificamente sobre os ativos que você possui
4.  **Entrega**: O resumo é formatado em blocos e enviado via Bot do Telegram, respeitando os limites de caracteres e garantindo uma leitura limpa.
5.  **Automação**: O projeto está configurado para rodar automaticamente 3 vezes ao dia via GitHub Actions.

## ✨ Funcionalidades Principais

* **Análise Multi-Setorial**: Cobertura de Cenário Global, Nacional, Empresas, Agro e Tecnologia.
* **Análise de Carteira**: Insights personalizados sobre como as notícias do dia podem afetar sua posição e possíveis recomendações.
* **Fallback de Modelos**: Sistema inteligente que alterna entre versões do Gemini (Flash, Pro, Lite) caso ocorra erro de cota ou indisponibilidade de um modelo específico.
* **Formatação HTML**: Mensagens organizadas com tags permitidas pelo Telegram para facilitar a leitura no celular.

## 🛠️ Tecnologias Utilizadas

* **Python 3.11+**
* **Google Gemini API**: Processamento de linguagem natural e análise financeira.
* **Feedparser**: Consumo de RSS Feeds de notícias.
* **PyPDF2**: Extração de texto de documentos PDF.
* **Telegram Bot API**: Entrega de relatórios via chat.
* **GitHub Actions**: Automação de tarefas e agendamento via Cron.

## ⚙️ Configuração e Instalação

### Instalação Local

1.  Clone o repositório:
    ```bash
    git clone [https://github.com/seu-usuario/Resumidor_Noticias.git](https://github.com/seu-usuario/Resumidor_Noticias.git)
    cd Resumidor_Noticias
    ```
2.  Instale as dependências:
    ```bash
    pip install google-genai requests feedparser PyPDF2 python-dotenv
    ```
3.  Crie um arquivo `.env` na raiz do projeto com suas credenciais:
    ```env
    GEMINI_KEY=sua_chave_aqui
    TELEGRAM_TOKEN=token_do_seu_bot
    CHAT_ID=seu_id_do_telegram
    ```
4.  Coloque o seu extrato da carteira renomeado para `wallet.pdf` na raiz da pasta.

## 🤖 Automação (GitHub Actions)

Para que o projeto rode na nuvem de forma segura e agendada:

1.  **Extração do Texto**: Rode `python leitor_wallet.py` no seu computador e copie todo o texto extraído da sua carteira que aparecer no terminal.
2.  **Configurar Secrets**: No seu repositório GitHub, vá em *Settings > Secrets and variables > Actions* e adicione as chaves:
    * `GEMINI_KEY`, `TELEGRAM_TOKEN`, `CHAT_ID`.
    * `CARTEIRA`: Cole aqui o texto que você copiou no passo 1.
3.  **Ativação Obrigatória**:
    > ⚠️ **IMPORTANTE**: O agendamento automático do GitHub Actions (Cron) só entrará em vigor após você executar o workflow manualmente pela primeira vez.
    * Vá na aba **Actions** do repositório.
    * Selecione o workflow **Resumidor Diario de Noticias**.
    * Clique no botão **Run workflow**. Isso valida suas credenciais e "acorda" o sistema de agendamento.

## 🛡️ Segurança

* O arquivo `wallet.pdf` e o arquivo `.env` estão listados no `.gitignore` e **nunca** serão enviados para o repositório público.
* O acesso aos dados financeiros no GitHub Actions é feito exclusivamente via *Secrets* criptografados.

---
_Este projeto foi desenvolvido para fins acadêmicos e de automação pessoal. Decisões financeiras devem ser tomadas com cautela._
