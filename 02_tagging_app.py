#!/usr/bin/env python
# 02_tagging_app.py - Version corrigée avec width='stretch'
# Interface Streamlit pour annotation avec gestion patient

import streamlit as st
import time
import os
import csv
import pandas as pd
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (
    DATA_DIR, EMOTION_COLORS, get_annotations_file, 
    get_current_session, list_all_patients, get_patient_sessions
)
from file_utils import find_eeg_file_compat

# Configuration
st.set_page_config(
    page_title="EEG Emotion Tagging",
    page_icon="🧠",
    layout="wide"
)

# Initialisation session state
if "start_time" not in st.session_state:
    st.session_state.start_time = None
    st.session_state.n_events = 0
    st.session_state.session_id = None
    st.session_state.notes = ""
    st.session_state.current_patient = None
    st.session_state.current_eeg_file = None

def load_patient_data(patient_id):
    """Charge les données d'un patient"""
    annot_file = get_annotations_file(patient_id)
    
    if os.path.exists(annot_file):
        return pd.read_csv(annot_file)
    return pd.DataFrame()

def log_event(label):
    """Enregistre une annotation"""
    if st.session_state.start_time is None:
        st.warning("⚠️ Démarrez une session d'abord!")
        return
    
    if st.session_state.current_patient is None:
        st.warning("⚠️ Sélectionnez un patient d'abord!")
        return
    
    now = time.time()
    elapsed = now - st.session_state.start_time
    
    # Fichier d'annotations du patient
    annot_file = get_annotations_file(st.session_state.current_patient)
    
    # Créer avec en-tête si nécessaire
    if not os.path.exists(annot_file):
        with open(annot_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time_s", "label", "session_id", "eeg_file", "notes"])
    
    # Ajouter l'annotation
    with open(annot_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            f"{elapsed:.3f}", 
            label, 
            st.session_state.session_id,
            os.path.basename(st.session_state.current_eeg_file) if st.session_state.current_eeg_file else "",
            st.session_state.notes
        ])
    
    st.session_state.n_events += 1
    st.toast(f"✅ {label} à t={elapsed:.1f}s", icon="🎯")
    
    # Vider les notes
    st.session_state.notes = ""

def main():
    st.title("🧠 Annotation Émotionnelle EEG - Multi-patients")
    st.markdown("---")
    
    # Sidebar - Sélection patient
    with st.sidebar:
        st.header("📋 Patient")
        
        # Récupérer session courante
        current_session = get_current_session()
        if current_session and not st.session_state.current_patient:
            st.session_state.current_patient = current_session['patient_id']
            st.session_state.current_eeg_file = current_session['eeg_file']
        
        # Lister tous les patients
        patients = list_all_patients()
        
        if not patients:
            st.warning("Aucun patient trouvé. Faites d'abord une acquisition ou migrez les anciens fichiers.")
            
            # Option de migration
            if st.button("🔄 Migrer anciens fichiers", width='stretch'):  # CORRECTION ICI
                from file_utils import migrate_legacy_files
                with st.spinner("Migration en cours..."):
                    n = migrate_legacy_files()
                st.success(f"{n} fichiers migrés!")
                st.rerun()
            return
        
        # Sélection patient
        selected_patient = st.selectbox(
            "Choisir un patient",
            patients,
            index=patients.index(st.session_state.current_patient) if st.session_state.current_patient in patients else 0
        )
        
        if selected_patient != st.session_state.current_patient:
            st.session_state.current_patient = selected_patient
            st.session_state.start_time = None
            st.rerun()
        
        # Lister les sessions du patient
        sessions = get_patient_sessions(selected_patient)
        
        if sessions:
            st.subheader("📁 Sessions disponibles")
            session_options = [f"{s['timestamp']} - {s['filename']}" for s in sessions]
            selected_session = st.selectbox("Session à annoter", session_options)
            
            # Récupérer le fichier sélectionné
            selected_idx = session_options.index(selected_session)
            st.session_state.current_eeg_file = sessions[selected_idx]['path']
            
            # Vérifier/compatibilité
            try:
                valid_path = find_eeg_file_compat(
                    st.session_state.current_eeg_file,
                    selected_patient
                )
                st.session_state.current_eeg_file = valid_path
                st.info(f"✅ Fichier: {os.path.basename(valid_path)}")
            except Exception as e:
                st.error(f"Fichier non trouvé: {e}")
        else:
            st.warning("Aucune session EEG pour ce patient")
        
        st.markdown("---")
        
        # Contrôle de session
        st.header("⏱️ Contrôle")
        
        if st.button("🟢 Démarrer session d'annotation", width='stretch'):  # CORRECTION ICI
            st.session_state.start_time = time.time()
            st.session_state.n_events = 0
            st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.success(f"Session {st.session_state.session_id} démarrée!")
            st.rerun()
        
        if st.session_state.start_time is not None:
            elapsed = time.time() - st.session_state.start_time
            st.info(f"⏱️ Temps: **{elapsed:.1f}s**")
            st.info(f"📊 Événements: **{st.session_state.n_events}**")
            
            if st.button("🔄 Réinitialiser", width='stretch'):  # CORRECTION ICI
                st.session_state.start_time = time.time()
                st.session_state.n_events = 0
                st.warning("Session réinitialisée!")
                st.rerun()
        
        st.markdown("---")
        st.header("📝 Notes")
        st.session_state.notes = st.text_area(
            "Notes pour la prochaine annotation:",
            value=st.session_state.notes,
            placeholder="ex: 'patient agité', 'moment calme'..."
        )
    
    # Zone principale - Boutons d'émotion
    col1, col2, col3 = st.columns(3)
    
    # Catégories d'émotions
    emotions = {
        "😊 Joie": "joie",
        "😌 Sérénité": "serenite",
        "😱 Peur": "peur",
        "😡 Colère": "colere",
        "🤩 Excitation": "excitation",
        "😖 Douleur": "douleur",
        "🥪 Faim": "faim",
        "💧 Soif": "soif",
        "🙋 Envie": "envie",
        "😐 Neutre": "neutre",
        "😴 Fatigue": "fatigue",
        "💬 Parle": "parle"
    }
    
    # Afficher les boutons en grille
    items = list(emotions.items())
    for i in range(0, len(items), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(items):
                display, code = items[i + j]
                with cols[j]:
                    color = EMOTION_COLORS.get(code, "#808080")
                    if st.button(display, width='stretch'):  # CORRECTION ICI
                        log_event(code)
    
    # Afficher les annotations récentes
    st.markdown("---")
    st.header("📋 Annotations récentes")
    
    if st.session_state.current_patient:
        df = load_patient_data(st.session_state.current_patient)
        
        if len(df) > 0:
            # Filtrer par session si une session est en cours
            if st.session_state.session_id:
                df_session = df[df['session_id'] == st.session_state.session_id]
                if len(df_session) > 0:
                    st.subheader("Session en cours")
                    st.dataframe(df_session.tail(10), use_container_width=True)
            
            st.subheader("Toutes les annotations")
            st.dataframe(df.tail(20), use_container_width=True)
            
            # Statistiques
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total annotations", len(df))
            with col2:
                st.metric("Émotions uniques", df['label'].nunique())
            with col3:
                if st.session_state.session_id:
                    session_count = len(df[df['session_id'] == st.session_state.session_id])
                    st.metric("Cette session", session_count)
        else:
            st.info("Aucune annotation pour ce patient")
    
    # Export
    if st.button("📥 Exporter les annotations", width='stretch'):  # CORRECTION ICI
        if st.session_state.current_patient:
            df = load_patient_data(st.session_state.current_patient)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Télécharger CSV",
                data=csv,
                file_name=f"annotations_{st.session_state.current_patient}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()