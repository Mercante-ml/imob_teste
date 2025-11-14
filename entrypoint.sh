#!/bin/sh

# O 'set -e' faz o script parar imediatamente se qualquer comando falhar.
set -e

echo "==> (Entrypoint) Rodando Collectstatic..."
python manage.py collectstatic --noinput

echo "==> (Entrypoint) Rodando Migrações do Banco de Dados..."
python manage.py migrate

echo "==> (Entrypoint) Iniciando o Servidor Gunicorn..."
# O 'exec' é crucial. Ele substitui o processo do script pelo gunicorn,
# permitindo que o Render gerencie o servidor web corretamente.
exec gunicorn barbearia_projeto.wsgi