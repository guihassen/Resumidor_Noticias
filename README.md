# 📈 Resumidor de Notícias & Morning Call Automático

Este projeto é um sistema inteligente de curadoria e análise de notícias voltado para investidores. Ele agrega as principais notícias do dia através de RSS feeds, cruza essas informações com a sua carteira de investimentos pessoal e utiliza a IA **Google Gemini** para gerar um "Morning Call" personalizado, enviado diretamente para o seu Telegram.

## 🚀 Como Funciona?

1.  **Coleta de Dados**: O script busca notícias em tempo real de fontes renomadas (InfoMoney, Money Times, Exame, Canaltech, etc.).
2.  **Leitura de Carteira**: Ele extrai informações da sua carteira de investimentos a partir de um arquivo `wallet.pdf` (localmente) ou de uma variável de ambiente (em produção).
3.  **Processamento com IA**: Utiliza modelos avançados do Gemini (2.0/2.5) para analisar o impacto macroeconômico e tecnológico especificamente sobre os ativos que você possui.
4.  **Entrega**: O resumo é formatado em blocos e enviado via Bot do Telegram, respeitando os limites de caracteres e garantindo uma leitura limpa.
5.  **Automação**: O projeto está configurado para rodar automaticamente 3 vezes ao dia via GitHub Actions.

## ✨ Funcionalidades Principais

- **Análise Multi-Setorial**: Cobertura de Cenário Global, Nacional, Empresas, Agro e Tecnologia.
- **Análise de Carteira**: Insights personalizados sobre como as notícias do dia podem afetar sua posição.
- **Fallback de Modelos**: Sistema inteligente que tenta usar diferentes versões do Gemini (Pro, Flash, Lite) caso uma falhe.
- **Formatação HTML**: Mensagens elegantes e organizadas no Telegram.

## 🛠️ Tecnologias Utilizadas

- **Python 3.11+**
- **Google Gemini API**: Escolha das Melhores Noticias e Linguagem Natural.
- **Feedparser**: Consumo de RSS Feeds.
- **PyPDF2**: Extração de dados de PDFs.
- **Telegram Bot API**: Interface de entrega.
- **GitHub Actions**: Automação e agendamento (Cron).

## ⚙️ Configuração e Instalação

### Pré-requisitos

- Python instalado.
- Uma API Key do [Google AI Studio](https://aistudio.google.com/).
- Um Bot no Telegram (criado via @BotFather) e o seu `CHAT_ID`.

### Instalação Local

1. Clone o repositório:

   ```bash
   git clone https://github.com/seu-usuario/Resumidor_Noticias.git
   cd Resumidor_Noticias
   ```

2. Instale as dependências:

   ```bash
   pip install google-genai requests feedparser PyPDF2 python-dotenv
   ```

3. Crie um arquivo `.env` na raiz do projeto:

   ```env
   GEMINI_KEY=sua_chave_aqui
   TELEGRAM_TOKEN=token_do_seu_bot
   CHAT_ID=seu_id_do_telegram
   ```

4. Coloque o arquivo `wallet.pdf` na raiz para leitura local.

## 🤖 Automação (GitHub Actions)

O projeto já conta com um workflow configurado em `.github/workflows/cron.yml`. Para que funcione no GitHub:

1.  **Gerar texto da Carteira**: Como o GitHub Actions não terá acesso ao seu PDF físico por segurança, você deve extrair o texto dele localmente:
    - Coloque seu `wallet.pdf` na raiz do projeto.
    - Execute: `python leitor_wallet.py`.
    - Copie todo o texto que aparecer no terminal.
2.  **Configurar Secrets**: Vá em seu repositório no GitHub em **Settings > Secrets and variables > Actions**.
3.  Adicione as seguintes _Repository Secrets_:
    - `GEMINI_KEY`: Sua chave de API do Google.
    - `TELEGRAM_TOKEN`: Token do seu bot.
    - `CHAT_ID`: Seu ID de chat.
    - `CARTEIRA`: Cole aqui o texto que você copiou no passo 1.

O script rodará automaticamente às **10h, 14h e 18h** (horário de Brasília).

## 📁 Estrutura do Projeto

- `main.py`: Lógica principal, integração com Gemini e Telegram.
- `leitor_wallet.py`: Módulo especializado em extração de texto de PDFs.
- `.github/workflows/cron.yml`: Configuração da automação do GitHub.
- `wallet.pdf`: (Não incluso) Seu arquivo de carteira para testes locais.

---

_Nota: Este projeto é para fins informativos e de automação de estudos. Decisões de investimento devem ser tomadas com cautela._
