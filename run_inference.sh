#!/bin/bash
# Script de lancement pour tablette

echo "🚀 Lancement de l'application d'inférence EEG"

# Configuration pour mobile
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_THEME_BASE="dark"

# Lancer l'application
streamlit run 08_inference_app.py \
    --server.maxUploadSize=10 \
    --browser.gatherUsageStats=false \
    --theme.primaryColor="#4CAF50" \
    --theme.backgroundColor="#667eea" \
    --theme.secondaryBackgroundColor="#764ba2" \
    --theme.textColor="#ffffff"