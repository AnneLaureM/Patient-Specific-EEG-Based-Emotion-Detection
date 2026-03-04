#!/usr/bin/env python
# migrate_all.py
# Script pour migrer tous les fichiers existants

import os
import shutil
import json
from datetime import datetime

BASE_DIR = "/home/anne/Nextcloud/Documents/Projets/Patient-Specific-EEG-Based-Emotion-Detection"
DATA_DIR = os.path.join(BASE_DIR, "data")
PATIENTS_DIR = os.path.join(DATA_DIR, "patients")

def migrate_all():
    print("=" * 60)
    print("🔄 MIGRATION COMPLÈTE VERS STRUCTURE PATIENTS")
    print("=" * 60)
    
    # Créer dossier patients
    os.makedirs(PATIENTS_DIR, exist_ok=True)
    
    # 1. Migrer les fichiers EEG
    eeg_files = [f for f in os.listdir(DATA_DIR) 
                 if f.startswith('eeg_') and f.endswith('.csv')]
    
    if eeg_files:
        print(f"\n📋 Fichiers EEG trouvés: {len(eeg_files)}")
        
        # Charger la session courante si elle existe
        current_session = None
        current_file = os.path.join(DATA_DIR, ".current_session.json")
        if os.path.exists(current_file):
            with open(current_file, 'r') as f:
                current_session = json.load(f)
            print(f"📌 Session courante: {current_session.get('eeg_filename')}")
        
        for eeg_file in eeg_files:
            print(f"\n📄 {eeg_file}")
            
            # Déterminer le patient
            if current_session and eeg_file == current_session.get('eeg_filename'):
                patient_id = current_session.get('patient_id', 'P001')
                print(f"   → Patient (session courante): {patient_id}")
            else:
                patient_id = input("   ID Patient (ex: P001): ").strip() or "P001"
            
            # Créer dossier patient
            patient_dir = os.path.join(PATIENTS_DIR, f"patient_{patient_id}")
            os.makedirs(patient_dir, exist_ok=True)
            
            # Déplacer
            old_path = os.path.join(DATA_DIR, eeg_file)
            new_path = os.path.join(patient_dir, eeg_file)
            shutil.move(old_path, new_path)
            print(f"   ✓ Déplacé vers: {new_path}")
            
            # Demander description pour renommer
            desc = input("   Description (resting_state/stimulation): ").strip()
            if desc:
                base = eeg_file.replace('eeg_acquisition_', '').replace('.csv', '')
                new_name = f"eeg_{desc}_{base}.csv"
                final_path = os.path.join(patient_dir, new_name)
                os.rename(new_path, final_path)
                print(f"   ✓ Renommé: {new_name}")
    
    # 2. Migrer les annotations
    annot_file = os.path.join(DATA_DIR, "annotations_patient.csv")
    if os.path.exists(annot_file):
        print(f"\n📋 Migration des annotations...")
        import pandas as pd
        df = pd.read_csv(annot_file)
        
        # Grouper par patient (basé sur session_id)
        if 'session_id' in df.columns:
            for session_id in df['session_id'].unique():
                df_session = df[df['session_id'] == session_id]
                
                # Chercher le fichier EEG correspondant
                found = False
                for root, dirs, files in os.walk(PATIENTS_DIR):
                    for f in files:
                        if session_id in f:
                            patient_dir = root
                            patient_id = os.path.basename(patient_dir).replace('patient_', '')
                            
                            # Sauvegarder annotations
                            out_file = os.path.join(patient_dir, "annotations.csv")
                            if os.path.exists(out_file):
                                df_existing = pd.read_csv(out_file)
                                df_combined = pd.concat([df_existing, df_session]).drop_duplicates()
                                df_combined.to_csv(out_file, index=False)
                            else:
                                df_session.to_csv(out_file, index=False)
                            
                            print(f"   ✓ Annotations pour patient {patient_id} sauvegardées")
                            found = True
                            break
                    if found:
                        break
    
    print("\n" + "=" * 60)
    print("✅ Migration terminée!")
    print("=" * 60)

if __name__ == "__main__":
    migrate_all()