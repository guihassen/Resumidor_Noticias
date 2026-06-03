# 📈 Resumidor de Noticias & Morning Call Automático

Este projeto é um sistema inteligente de curadoria e análise voltado para investidores. Ele agrega as principais notícias do dia, **cruza com dados reais de mercado dos ativos da sua carteira** (cotações, valuation, dividend yield), incorpora **projeções econômicas do Boletim Focus/Bacen** e usa a IA **Google Gemini** para gerar um "Morning Call" personalizado — com texto e **gráficos** — enviado diretamente para o seu Telegram.

## 🚀 Como Funciona?

1.  **Coleta de Notícias**: Busca notícias em tempo real via RSS (InfoMoney, Money Times, Valor, Exame, etc.).
2.  **Leitura e Estruturação da Carteira**: Extrai o texto do extrato (`wallet.pdf` local ou variável `CARTEIRA` em produção) e usa o Gemini para convertê-lo em **ativos estruturados** (ticker, tipo, quantidade).
3.  **Dados de Mercado**: Busca cotações, P/L, P/VP, dividend yield, setor e visão de analistas (via `yfinance`, opcionalmente `brapi.dev`) e calcula métricas reais da carteira (alocação, exposição setorial, momentum).
4.  **Projeções Macro**: Consulta a API gratuita do Banco Central (Focus) para Selic, IPCA, Câmbio e PIB.
5.  **Notícias Conectadas**: Filtra as notícias que citam seus ativos e extrai o **texto completo** das matérias (scraping com `trafilatura`) para análises mais profundas.
6.  **Processamento com IA**: O Gemini gera o Morning Call usando todos esses dados reais — incluindo diagnóstico da carteira, pontos de melhoria e decisões.
7.  **Entrega**: Texto formatado em blocos + **gráficos** (alocação, rentabilidade por ativo, evolução do patrimônio) enviados via Bot do Telegram.
8.  **Persistência**: Snapshots diários da carteira vão para um **Postgres privado** (fora do repositório) para alimentar o histórico e o gráfico de evolução.
9.  **Automação**: Roda automaticamente 3 vezes ao dia via GitHub Actions.

## ✨ Funcionalidades Principais

* **Análise Multi-Setorial**: Cenário Global, Nacional, Projeções (Focus), Empresas, Agro e Tecnologia.
* **Métricas Reais da Carteira**: Valor total, alocação por classe, exposição setorial, dividend yield, valuation, rentabilidade por ativo e patrimônio oficial (relatório XP).
* **Notícias Conectadas à Carteira**: Seção dedicada que cruza notícias (com texto completo) aos seus ativos, sem repetir entre execuções (dedupe via banco).
* **Projeções Econômicas**: Selic, IPCA, Câmbio e PIB do Boletim Focus/Bacen + câmbio atual.
* **Expectativa do Dia**: Por ativo — tendência (médias móveis), RSI, posição no range de 52 semanas, eventos (resultados/dividendos), upside vs. preço-alvo e sentimento das notícias.
* **Gráficos dinâmicos**: Mapa da carteira (heatmap peso × variação de hoje), variação do dia por ativo, carteira vs. CDI/Ibovespa e evolução do patrimônio.
* **Fallback de Modelos**: Alterna entre versões do Gemini (e Groq) caso ocorra erro de cota.
* **Arquitetura Modular**: Código organizado em `src/` (wallet, market, news, analysis, charts, db, delivery).

## 🛠️ Tecnologias Utilizadas

* **Python 3.11+**
* **Google Gemini API**: Estruturação da carteira e geração da análise.
* **yfinance / brapi.dev**: Cotações, fundamentos e visão de analistas.
* **API Olinda/BCB (Focus)**: Projeções macroeconômicas (gratuita).
* **Feedparser + Trafilatura**: RSS e extração do texto completo das matérias.
* **Matplotlib**: Geração dos gráficos.
* **SQLAlchemy + PostgreSQL**: Persistência privada do histórico da carteira.
* **PyPDF2**: Extração de texto do extrato em PDF.
* **Telegram Bot API**: Entrega de texto e imagens via chat.
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
    # Opcionais:
    GROQ_KEY=chave_groq_para_fallback
    DATABASE_URL=postgresql://usuario:senha@host:5432/banco   # Postgres privado (histórico)
    BRAPI_TOKEN=token_brapi                                    # cotações via brapi.dev
    ```
4.  Coloque o seu extrato da carteira renomeado para `wallet.pdf` na raiz da pasta.

> **Sobre o `DATABASE_URL`**: é **opcional**. Sem ele, o pipeline roda normalmente, apenas sem o histórico e o gráfico de evolução do patrimônio. Use uma base **privada** (ex.: [Supabase](https://supabase.com) ou [Neon](https://neon.tech), free tier) — assim seus dados financeiros **nunca** ficam no repositório.

## 🤖 Automação (GitHub Actions)

Para que o projeto rode na nuvem de forma segura e agendada:

1.  **Extração do Texto**: Rode `python leitor_wallet.py` no seu computador e copie todo o texto extraído da sua carteira que aparecer no terminal.
2.  **Configurar Secrets**: No seu repositório GitHub, vá em *Settings > Secrets and variables > Actions* e adicione as chaves:
    * `GEMINI_KEY`, `TELEGRAM_TOKEN`, `CHAT_ID`.
    * `CARTEIRA`: Cole aqui o texto que você copiou no passo 1.
    * *(Opcionais)* `GROQ_KEY`, `DATABASE_URL` (Postgres privado para histórico/gráfico de evolução), `BRAPI_TOKEN`.
3.  **Ativação Obrigatória**:
    > ⚠️ **IMPORTANTE**: O agendamento automático do GitHub Actions (Cron) só entrará em vigor após você executar o workflow manualmente pela primeira vez.
    * Vá na aba **Actions** do repositório.
    * Selecione o workflow **Resumidor Diario de Noticias**.
    * Clique no botão **Run workflow**. Isso valida suas credenciais e "acorda" o sistema de agendamento.

## 🛡️ Segurança

* Os arquivos `wallet.pdf`, `.env` e a pasta `.venv/` estão no `.gitignore` e **nunca** vão para o repositório.
* O acesso aos dados financeiros no GitHub Actions é feito exclusivamente via *Secrets* criptografados.
* O histórico da carteira é gravado em um **Postgres privado** (fora do repositório), nunca em arquivo versionado — por isso seu patrimônio e posições não ficam expostos.

---
_Este projeto foi desenvolvido para fins acadêmicos e de automação pessoal. Decisões financeiras devem ser tomadas com cautela._
