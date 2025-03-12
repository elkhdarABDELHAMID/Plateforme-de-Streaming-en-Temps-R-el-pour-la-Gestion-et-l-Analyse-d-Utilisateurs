# Image de base
FROM python:3.9-slim

# Définition du répertoire de travail
WORKDIR /app

# Copie des fichiers locaux vers le conteneur
COPY . /app/

# Installation des dépendances Python
RUN pip install --no-cache-dir streamlit pymongo cassandra-driver

# Exposition du port pour Streamlit
EXPOSE 8501

# Commande par défaut pour exécuter Streamlit
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]

# Description en arabe: هذا الملف يبني صورة لـ streamlit-dashboard باستخدام Python 3.9.
# يقوم بتثبيت Streamlit ومكتبات للاتصال بـ MongoDB وCassandra لعرض البيانات على المنفذ 8501.