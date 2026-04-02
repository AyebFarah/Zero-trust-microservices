FROM python:3.11-slim

# Répertoire de travail dans le conteneur
WORKDIR /app

# Copie les dépendances EN PREMIER (optimisation du cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie tout le code du service
COPY . .

# Le port sur lequel FastAPI va tourner
EXPOSE 8080

# Commande de démarrage
CMD ["python", "main.py"]
