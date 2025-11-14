# 1. Base: Começa de uma imagem Python 3.12 oficial e leve
FROM python:3.12-slim-bookworm

# 2. Variáveis de Ambiente:
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Instala Dependências do Sistema:
RUN apt-get update \
    && apt-get install -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Define o diretório de trabalho dentro do container
WORKDIR /app

# 5. Instala Dependências do Python:
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# 6. Copia o Código do App:
COPY . /app/

# 7. NOVO: Copia o script de entrypoint e o torna executável
# O Windows não salva permissões, então fazemos isso no Linux.
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# 8. Expõe a porta
EXPOSE 8000