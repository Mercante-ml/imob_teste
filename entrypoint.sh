#!/bin/sh

# O 'set -e' faz o script parar imediatamente se qualquer comando falhar.
set -e

echo "==> (Entrypoint) Rodando Collectstatic..."
python manage.py collectstatic --noinput

echo "==> (Entrypoint) Rodando Migrações do Banco de Dados..."
python manage.py migrate

echo "==> (Entrypoint) Iniciando o Servidor Daphne..."
# O 'exec' é crucial. Ele substitui o processo do script pelo daphne.
exec daphne -b 0.0.0.0 -p 8000 barbearia_projeto.asgi:application
