# Imagem base oficial do Python slim para menor consumo de recursos
FROM python:3.12-slim

# Metadados
LABEL maintainer="ConcurseiroAI Team"
LABEL description="API e Plataforma Inteligente de Estudos para Concursos Públicos"

# Evita criação de arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

WORKDIR /app

# Instala dependências de compilação essenciais e curl para healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências primeiro para aproveitar o cache de camadas
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia os arquivos da aplicação
COPY . .

# Cria pasta de dados para persistência do banco SQLite
RUN mkdir -p /app/data

# Expõe a porta padrão da aplicação
EXPOSE 8000

# Healthcheck do container
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Comando de inicialização em produção com 4 workers Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
