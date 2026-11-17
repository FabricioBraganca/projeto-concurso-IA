# ⚖️ ConcurseiroAI — Plataforma Inteligente de Concursos Públicos

Plataforma Web completa e API REST desenvolvida com **FastAPI**, **PostgreSQL / SQLite**, **Google Gemini AI** e **HTML/CSS/JS moderno** com estética clássica e focada de estudos para concursos públicos brasileiros.

---

## 🚀 Funcionalidades Entregues no MVP (Fase 1)

1. **Dashboard de Estudos Completo**:
   - Métricas em tempo real: Taxa de aproveitamento geral (%), total de questões feitas, simulados concluídos e total de acertos.
   - Gráfico de aproveitamento por disciplina via Chart.js.
   - Concursos quentes no radar (Receita Federal, TSE Unificado, TCU, etc.).
   - Histórico de simulados recentes com atalho para revisão de gabarito.

2. **Gerador de Simulados Híbrido (Até 20 Questões)**:
   - Suporte a **3 Modos de Treino**:
     - 🏛️ **Apenas Questões Reais de Provas**: Carregamento ultrarrápido (`< 50ms`) a partir do acervo do banco de dados oficial.
     - 🤖 **Apenas Inéditas com IA**: Formuladas pelo Gemini 2.5 Flash no estilo e pegadinhas da banca examinadora (Cebraspe, FGV, FCC, Vunesp, etc.).
     - ⚡ **Misto (50% Reais + 50% IA)**: O melhor dos dois mundos para fixação de questões clássicas e treino com inéditas.
   - Seleção de até **20 Questões por Caderno** com tempo estendido e barra de progresso.
   - Caderno de prova oficial diagramado com folha de respostas e gabarito comentado para impressão e PDF.

3. **Catálogo de Disciplinas & Tópicos de Edital**:
   - 7 Grandes Disciplinas estruturadas: Direito Constitucional, Direito Administrativo, Língua Portuguesa, Raciocínio Lógico-Matemático, Direito Tributário, Informática/TI e Direito Penal.
   - Mais de 35 assuntos e subtópicos de alta incidência em concursos públicos.
   - Endpoints dedicados (`/api/v1/disciplinas/` e `/api/v1/disciplinas/{id}/assuntos`).

4. **Tutor de Concursos IA**:
   - Chatbot especializado em dúvidas doutrinárias, mnemônicos, pegadinhas de bancas e macetes de memorização.
   - Histórico de interações persistido no banco de dados.

5. **Radar de Concursos & Repositório de Provas**:
   - Scraping e feed RSS do PCI Concursos e editais oficiais.
   - Banco de cadernos de prova reais por banca (Cebraspe, FGV, FCC, Vunesp, etc.) com atalhos de treino.

6. **Flashcards & Repetição Espaçada (Método Anki / SM-2)**:
   - Algoritmo matemático SuperMemo-2 (SM-2) com cálculo de fator de facilidade (E-Factor), contagem de repetições e agendamento dinâmico de revisões.
   - Criação de novos flashcards pelo estudante e avaliação de retenção (Errei / Difícil / Fácil).

7. **Plano Semanal de Estudos Gerado por IA**:
   - Cronograma semanal estruturado por dias, blocos teóricos, metas diárias de questões e rotina de caderno de erros.
   - Customização de concurso alvo, cargo, horas diárias disponíveis e disciplinas com maior dificuldade.


---

## 🛠️ Tecnologias Utilizadas

- **Back-end:** Python 3.12, FastAPI, Uvicorn, SQLAlchemy, Pydantic v2
- **IA Generativa:** Google Gemini (`google-genai` SDK, modelo `gemini-2.5-flash`)
- **Front-end:** HTML5, Vanilla CSS3 (Dark Mode clássico de estudos), Jinja2 SSR, Chart.js
- **Banco de Dados:** SQLite (padrão local em `concursos.db`) ou PostgreSQL

---

## 🏃 Como Executar a Aplicação

### 1. Ativar o Ambiente Virtual
```bash
source venv/bin/activate
```

### 2. Configurar a Chave do Gemini (Opcional para IA Real)
No arquivo `.env`, adicione sua chave de API gratuita do Google AI Studio:
```env
GEMINI_API_KEY="sua_chave_aqui"
```
*(Nota: O sistema já conta com fallback inteligente caso a chave não esteja configurada no momento).*

### 3. Iniciar o Servidor
```bash
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Acessar no Navegador
- **Interface Gráfica:** [http://localhost:8000/](http://localhost:8000/)
- **Documentação Interativa Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Documentação Redoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
