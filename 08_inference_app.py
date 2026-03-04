#!/usr/bin/env python
# 08_inference_app.py - Version avec lissage temporel ajustable
# Application d'inférence temps réel avec stabilité paramétrable

import streamlit as st
import numpy as np
import pandas as pd
import time
import os
import sys
import joblib
from datetime import datetime
from collections import deque, Counter
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (
    get_patient_model_dir, get_patient_output_dir,
    get_patient_sessions, list_all_patients, get_patient_info,
    EMOTION_COLORS
)
from eeg_utils import (
    bandpass_filter, compute_band_powers,
    DEFAULT_CHANNEL_NAMES
)

# Configuration de la page
st.set_page_config(
    page_title="Communication Augmentée EEG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .emotion-card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        text-align: center;
        border: 3px solid transparent;
        transition: all 0.3s ease;
    }
    
    .emotion-card-active {
        border-color: #4CAF50;
        box-shadow: 0 15px 40px rgba(76,175,80,0.3);
    }
    
    .giant-emoji {
        font-size: 8rem;
        text-align: center;
        margin: 1rem 0;
        animation: gentlePulse 2s infinite;
    }
    
    @keyframes gentlePulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    .emotion-text {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
        color: #333;
    }
    
    .probability-bar {
        width: 100%;
        height: 20px;
        background: #f0f0f0;
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .probability-fill {
        height: 100%;
        background: linear-gradient(90deg, #4CAF50, #8BC34A);
        transition: width 0.3s;
    }
    
    .stability-indicator {
        font-size: 1rem;
        color: #666;
        margin: 0.5rem 0;
        padding: 0.3rem;
        border-radius: 10px;
        background: rgba(0,0,0,0.05);
    }
    
    .connection-status {
        position: fixed;
        top: 10px;
        right: 10px;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        z-index: 1000;
    }
    
    .connected {
        background: #4CAF50;
        color: white;
        animation: blink 2s infinite;
    }
    
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    
    .disconnected {
        background: #f44336;
        color: white;
    }
    
    .history-item {
        background: rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 0.5rem 1rem;
        margin: 0.3rem 0;
        color: white;
        display: flex;
        justify-content: space-between;
        backdrop-filter: blur(5px);
    }
    
    .slider-container {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    @media (max-width: 768px) {
        .giant-emoji {
            font-size: 6rem;
        }
        .emotion-text {
            font-size: 2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Mapping émoji - émotion
EMOJI_MAP = {
    "joie": "😊",
    "serenite": "😌",
    "peur": "😨",
    "colere": "😠",
    "excitation": "🤩",
    "douleur": "😖",
    "faim": "🍽️",
    "soif": "💧",
    "envie": "🤔",
    "fatigue": "😴",
    "neutre": "😐",
    "parle": "🗣️"
}

# Descriptions longues
DESCRIPTION_MAP = {
    "joie": "Je suis content(e)",
    "serenite": "Je me sens calme",
    "peur": "J'ai peur",
    "colere": "Je suis en colère",
    "excitation": "Je suis excité(e)",
    "douleur": "J'ai mal",
    "faim": "J'ai faim",
    "soif": "J'ai soif",
    "envie": "J'aimerais quelque chose",
    "fatigue": "Je suis fatigué(e)",
    "neutre": "Je me sens neutre",
    "parle": "Je veux parler"
}

class StableInference:
    """
    Version avec lissage temporel paramétrable
    """
    
    def __init__(self, patient_id):
        self.patient_id = patient_id
        self.model = None
        self.classes = list(EMOJI_MAP.keys())
        
        # Paramètres ajustables
        self.buffer_size = 5  # Garder les 5 dernières prédictions (plus réactif)
        self.stability_threshold = 0.4  # 40% des dernières prédictions (plus sensible)
        self.min_confidence = 0.3  # Confiance minimale plus basse
        self.display_hold_time = 0.5  # Temps minimum d'affichage réduit à 0.5s
        
        # Buffers
        self.prediction_buffer = deque(maxlen=self.buffer_size)
        self.confidence_buffer = deque(maxlen=self.buffer_size)
        self.probabilities_buffer = deque(maxlen=self.buffer_size)
        
        # État courant
        self.current_display_emotion = "neutre"
        self.current_display_confidence = 0
        self.last_change_time = time.time()
        self.emotion_history = deque(maxlen=30)
        self.confidence_history = deque(maxlen=30)
        
        # Charger le modèle
        self.load_model()
    
    def load_model(self):
        """Tente de charger un modèle existant"""
        model_dir = get_patient_model_dir(self.patient_id)
        model_path = os.path.join(model_dir, "patient_model_rf.joblib")
        
        if os.path.exists(model_path):
            try:
                artifact = joblib.load(model_path)
                self.model = artifact['model']
                self.classes = artifact['classes_']
                return True
            except:
                pass
        return False
    
    def update_parameters(self, buffer_size=None, threshold=None, hold_time=None):
        """Met à jour les paramètres en temps réel"""
        if buffer_size is not None:
            self.buffer_size = buffer_size
            self.prediction_buffer = deque(maxlen=buffer_size)
            self.confidence_buffer = deque(maxlen=buffer_size)
            self.probabilities_buffer = deque(maxlen=buffer_size)
        if threshold is not None:
            self.stability_threshold = threshold
        if hold_time is not None:
            self.display_hold_time = hold_time
    
    def get_stable_prediction(self):
        """
        Retourne une prédiction stable avec paramètres ajustables
        """
        # Simulation pour le développement (à remplacer par vraie acquisition)
        time.sleep(0.2)
        
        # Simulation plus réaliste avec tendance
        if not hasattr(self, '_trend'):
            self._trend = 0
            self._current_emotion = random.choice(self.classes)
        
        # Garder la même émotion plus longtemps parfois
        if random.random() < 0.3:  # 30% de chance de changer
            self._current_emotion = random.choice(self.classes)
        
        new_emotion = self._current_emotion
        new_confidence = random.uniform(0.4, 0.9)
        
        # Simuler des probabilités pour toutes les classes
        probs = {}
        for c in self.classes:
            if c == new_emotion:
                probs[c] = new_confidence
            else:
                probs[c] = random.uniform(0, 0.3)
        
        # Normaliser
        total = sum(probs.values())
        probs = {k: v/total for k, v in probs.items()}
        
        # Ajouter au buffer
        self.prediction_buffer.append(new_emotion)
        self.confidence_buffer.append(new_confidence)
        self.probabilities_buffer.append(probs)
        
        # Analyser le buffer
        if len(self.prediction_buffer) == self.buffer_size:
            # Compter les occurrences
            counter = Counter(self.prediction_buffer)
            most_common = counter.most_common(1)[0]
            stable_emotion = most_common[0]
            stable_count = most_common[1]
            
            # Calculer la stabilité
            stability_ratio = stable_count / self.buffer_size
            avg_confidence = np.mean(list(self.confidence_buffer))
            
            # Moyenne des probabilités
            avg_probs = {}
            for c in self.classes:
                values = [p.get(c, 0) for p in self.probabilities_buffer]
                avg_probs[c] = np.mean(values)
            
            time_since_last_change = time.time() - self.last_change_time
            
            # Décider si on change
            should_change = False
            
            # Condition 1: Stabilité suffisante ET confiance suffisante
            if stability_ratio >= self.stability_threshold and avg_confidence >= self.min_confidence:
                should_change = True
            
            # Condition 2: Temps minimum écoulé
            if time_since_last_change < self.display_hold_time:
                should_change = False
            
            # Condition 3: C'est vraiment différent
            if stable_emotion == self.current_display_emotion:
                should_change = False
            
            if should_change:
                self.current_display_emotion = stable_emotion
                self.current_display_confidence = avg_confidence
                self.last_change_time = time.time()
                
                # Ajouter à l'historique
                self.emotion_history.append(stable_emotion)
                self.confidence_history.append(avg_confidence)
                
                return stable_emotion, avg_confidence, avg_probs
        
        return self.current_display_emotion, self.current_display_confidence, None

def main():
    # Initialisation
    if 'inference' not in st.session_state:
        st.session_state.inference = None
    if 'patient_selected' not in st.session_state:
        st.session_state.patient_selected = False
    if 'current_emotion' not in st.session_state:
        st.session_state.current_emotion = "neutre"
    if 'current_confidence' not in st.session_state:
        st.session_state.current_confidence = 0
    if 'current_probs' not in st.session_state:
        st.session_state.current_probs = None
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'show_stats' not in st.session_state:
        st.session_state.show_stats = False
    if 'buffer_size' not in st.session_state:
        st.session_state.buffer_size = 5
    if 'threshold' not in st.session_state:
        st.session_state.threshold = 0.4
    if 'hold_time' not in st.session_state:
        st.session_state.hold_time = 0.5
    if 'last_update' not in st.session_state:
        st.session_state.last_update = time.time()
    
    # Indicateur de connexion
    status_class = "connected" if st.session_state.running else "disconnected"
    status_text = "🔴 Acquisition en cours" if st.session_state.running else "⚪ En attente"
    st.markdown(f'<div class="connection-status {status_class}">{status_text}</div>', 
                unsafe_allow_html=True)
    
    # Titre
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: white; font-size: 2.5rem;">🧠 Communication Augmentée</h1>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.2rem;">
            Détection intelligente des émotions
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sélection du patient
    if not st.session_state.patient_selected:
        patients = list_all_patients()
        
        if not patients:
            st.warning("""
            ⚠️ Aucun patient trouvé.
            Mode démonstration - Utilisation de données simulées.
            """)
            patients = ["Démo"]
        
        st.markdown("### 👤 Sélection du patient")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            selected = st.selectbox(
                "Patient:",
                patients,
                format_func=lambda x: f"Patient {x}" if x != "Démo" else "🎮 Mode Démonstration",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("✅ Charger", width='stretch'):
                with st.spinner("Chargement..."):
                    st.session_state.inference = StableInference(selected)
                    st.session_state.patient_selected = True
                    st.session_state.patient_id = selected
                    st.rerun()
        return
    
    # Interface principale
    inference = st.session_state.inference
    
    # Barre de contrôle
    cols = st.columns(5)
    with cols[0]:
        if st.button("🏠", width='stretch'):
            st.session_state.patient_selected = False
            st.rerun()
    with cols[1]:
        if st.button("▶️", width='stretch'):
            st.session_state.running = True
            st.session_state.last_update = time.time()
    with cols[2]:
        if st.button("⏸️", width='stretch'):
            st.session_state.running = False
    with cols[3]:
        if st.button("📊", width='stretch'):
            st.session_state.show_stats = not st.session_state.show_stats
    with cols[4]:
        if st.button("🔄", width='stretch'):
            st.rerun()
    
    # Paramètres ajustables
    with st.expander("⚙️ Réglages de sensibilité", expanded=True):
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            new_buffer = st.slider("📊 Taille mémoire", 2, 10, st.session_state.buffer_size, 1,
                                  help="Nombre de mesures à mémoriser (plus = plus stable)")
        with col2:
            new_threshold = st.slider("🎯 Seuil stabilité", 0.1, 0.9, st.session_state.threshold, 0.1,
                                     help="% de mesures identiques pour changer (plus = plus stable)")
        
        new_hold = st.slider("⏱️ Temps minimum (s)", 0.1, 3.0, st.session_state.hold_time, 0.1,
                            help="Temps minimal d'affichage d'une émotion")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Mettre à jour les paramètres
        if (new_buffer != st.session_state.buffer_size or 
            new_threshold != st.session_state.threshold or 
            new_hold != st.session_state.hold_time):
            st.session_state.buffer_size = new_buffer
            st.session_state.threshold = new_threshold
            st.session_state.hold_time = new_hold
            inference.update_parameters(new_buffer, new_threshold, new_hold)
            st.success("✅ Paramètres mis à jour")
    
    # Mise à jour en temps réel
    if st.session_state.running:
        current_time = time.time()
        if current_time - st.session_state.last_update > 0.2:
            emotion, confidence, probs = inference.get_stable_prediction()
            st.session_state.current_emotion = emotion
            st.session_state.current_confidence = confidence
            st.session_state.current_probs = probs
            st.session_state.last_update = current_time
    
    # Affichage principal
    current_emoji = EMOJI_MAP.get(st.session_state.current_emotion, "😐")
    current_desc = DESCRIPTION_MAP.get(st.session_state.current_emotion, "")
    
    # Indicateur de stabilité
    stability_info = f"📊 Mémoire: {st.session_state.buffer_size} | Seuil: {st.session_state.threshold:.0%} | Mini: {st.session_state.hold_time:.1f}s"
    
    st.markdown(f"""
    <div class="emotion-card emotion-card-active">
        <div class="giant-emoji">{current_emoji}</div>
        <div class="emotion-text">{current_desc}</div>
        <div class="probability-bar">
            <div class="probability-fill" style="width: {st.session_state.current_confidence*100}%;"></div>
        </div>
        <div style="font-size: 1.2rem; color: #666; margin: 0.5rem 0;">
            Confiance: {st.session_state.current_confidence:.0%}
        </div>
        <div class="stability-indicator">{stability_info}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Baromètre des émotions
    if st.session_state.show_stats and st.session_state.current_probs:
        st.markdown("### 📊 Probabilités détaillées")
        
        # Trier par probabilité
        sorted_probs = sorted(st.session_state.current_probs.items(), 
                            key=lambda x: x[1], reverse=True)
        
        cols = st.columns(2)
        for i, (emotion, prob) in enumerate(sorted_probs[:6]):
            with cols[i % 2]:
                emoji = EMOJI_MAP.get(emotion, "😐")
                color = EMOTION_COLORS.get(emotion, "#808080")
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.1); border-radius: 10px; padding: 0.5rem; margin: 0.2rem;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 1.5rem;">{emoji}</span>
                        <div style="flex-grow: 1; margin-left: 0.5rem;">
                            <div style="color: white;">{emotion}</div>
                            <div style="background: rgba(255,255,255,0.2); border-radius: 5px; height: 8px;">
                                <div style="background: {color}; width: {prob*100}%; height: 8px; border-radius: 5px;"></div>
                            </div>
                        </div>
                        <span style="color: white;">{prob:.0%}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Historique
    if len(inference.emotion_history) > 0:
        st.markdown("### 📝 Historique des changements")
        
        history_html = ""
        recent_history = list(zip(
            list(inference.emotion_history)[-8:],
            list(inference.confidence_history)[-8:]
        ))
        
        for i, (emo, conf) in enumerate(reversed(recent_history)):
            emoji = EMOJI_MAP.get(emo, "😐")
            time_ago = f"• Changement {i+1}"
            
            history_html += f"""
            <div class="history-item">
                <span>{emoji} {emo}</span>
                <span>{conf:.0%} {time_ago}</span>
            </div>
            """
        
        st.markdown(history_html, unsafe_allow_html=True)
    
    # Mode démo
    if st.session_state.patient_id == "Démo":
        st.info("🎮 Mode Démonstration - Données simulées")
    
    # Auto-refresh
    if st.session_state.running:
        time.sleep(0.1)
        st.rerun()

if __name__ == "__main__":
    main()