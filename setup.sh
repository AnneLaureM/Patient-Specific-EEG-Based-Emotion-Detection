#!/bin/bash
# setup.sh - Installation complète

echo "🔧 Installation du pipeline EEG et du papier..."

# 1. Installer LaTeX
echo "📄 Installation de LaTeX..."
sudo apt-get update
sudo apt-get install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science

# 2. Vérifier l'environnement conda
echo "🐍 Vérification de l'environnement conda..."
if ! conda env list | grep -q "eeg"; then
    echo "Création de l'environnement eeg..."
    conda create -n eeg python=3.9 -y
fi

# 3. Activer l'environnement et installer les dépendances
echo "📦 Installation des dépendances Python..."
source ~/anaconda3/etc/profile.d/conda.sh
conda activate eeg
pip install -r requirements.txt

# 4. Créer les dossiers nécessaires
echo "📁 Création des dossiers..."
mkdir -p data outputs models figures paper/figures paper/sections paper/bibliography

# 5. Rendre les scripts exécutables
echo "🔑 Configuration des permissions..."
chmod +x *.py
chmod +x *.sh

# 6. Vérifier les fichiers EEG
echo "🔍 Vérification des fichiers EEG..."
if [ -f data/eeg_acquisition.csv ]; then
    echo "✅ Fichier EEG trouvé"
    # Renommer avec la date actuelle
    DATE=$(date +%Y%m%d_%H%M%S)
    cp data/eeg_acquisition.csv data/eeg_acquisition_${DATE}.csv
    echo "✅ Copie créée: eeg_acquisition_${DATE}.csv"
else
    echo "⚠️ Aucun fichier EEG trouvé dans data/"
fi

echo ""
echo "✅ Installation terminée!"
echo ""
echo "🚀 Pour générer les analyses :"
echo "   conda activate eeg"
echo "   python 07_advanced_analysis.py"
echo "   python copy_figures_to_paper.py"
echo "   cd paper && make && make view"