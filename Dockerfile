# 1. On part d'une image Linux avec Python préinstallé
FROM python:3.10-slim

# 2. On se place dans un dossier de travail virtuel
WORKDIR /app

# 3. On copie le fichier des modules nécessaires (pandas, pymongo...)
COPY src/requirements.txt .

# 4. On installe ces modules
RUN pip install --no-cache-dir -r requirements.txt

# 5. On copie tout le reste de ton code (main.py, le dossier utils, le CSV)
COPY src/ ./src/

# 6. La commande par défaut pour lancer la migration
CMD ["python", "src/main.py"]