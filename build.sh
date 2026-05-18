#!/bin/bash
# Instalar dependencias
pip install -r requirements.txt

# Recopilar archivos estáticos
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Ejecutar migraciones
echo "Ejecutando migraciones de la base de datos..."
python manage.py migrate
