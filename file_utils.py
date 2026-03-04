#!/usr/bin/env python
# file_utils.py
# Utilitaires de gestion de fichiers avec compatibilité ascendante

import os
import shutil
from datetime import datetime
from config import DATA_DIR, PATIENTS_DIR, get_patient_dir

def find_eeg_file_compat(eeg_path, patient_id=None):
    """
    Cherche un fichier EEG dans plusieurs emplacements possibles
    avec migration automatique vers la nouvelle structure
    
    Args:
        eeg_path: Chemin demandé
        patient_id: ID du patient (optionnel, sera extrait du chemin sinon)
    
    Returns:
        str: Chemin valide vers le fichier
    """
    
    # Si le fichier existe déjà, tant mieux
    if os.path.exists(eeg_path):
        return eeg_path
    
    print(f"\n🔍 Fichier non trouvé: {eeg_path}")
    print("   Recherche dans les anciens emplacements...")
    
    # Extraire le nom du fichier
    filename = os.path.basename(eeg_path)
    
    # Extraire le patient_id du chemin si non fourni
    if patient_id is None:
        # Essayer d'extraire de eeg_path
        if 'patient_' in eeg_path:
            import re
            match = re.search(r'patient_([^/]+)', eeg_path)
            if match:
                patient_id = match.group(1)
    
    # 1. Chercher dans l'ancien emplacement (racine data/)
    old_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(old_path):
        print(f"   ✅ Fichier trouvé dans l'ancien emplacement: {old_path}")
        
        if patient_id:
            # Déplacer vers le bon dossier patient
            patient_dir = get_patient_dir(patient_id)
            new_path = os.path.join(patient_dir, filename)
            
            print(f"   📦 Migration vers: {new_path}")
            shutil.move(old_path, new_path)
            print(f"   ✓ Fichier migré avec succès")
            return new_path
        else:
            print(f"   ⚠️ Impossible de migrer: patient_id inconnu")
            return old_path
    
    # 2. Chercher dans tous les dossiers patients
    if os.path.exists(PATIENTS_DIR):
        for patient_folder in os.listdir(PATIENTS_DIR):
            if patient_folder.startswith('patient_'):
                patient_path = os.path.join(PATIENTS_DIR, patient_folder, filename)
                if os.path.exists(patient_path):
                    print(f"   ✅ Fichier trouvé chez: {patient_folder}")
                    return patient_path
    
    # 3. Proposer une liste de tous les fichiers EEG disponibles
    all_eeg_files = []
    
    # Dans data/
    if os.path.exists(DATA_DIR):
        all_eeg_files.extend([
            ('ancien', os.path.join(DATA_DIR, f)) 
            for f in os.listdir(DATA_DIR) 
            if f.startswith('eeg_') and f.endswith('.csv')
        ])
    
    # Dans patients/
    if os.path.exists(PATIENTS_DIR):
        for patient_folder in os.listdir(PATIENTS_DIR):
            if patient_folder.startswith('patient_'):
                patient_path = os.path.join(PATIENTS_DIR, patient_folder)
                if os.path.exists(patient_path):
                    all_eeg_files.extend([
                        (patient_folder, os.path.join(patient_path, f))
                        for f in os.listdir(patient_path)
                        if f.startswith('eeg_') and f.endswith('.csv')
                    ])
    
    if all_eeg_files:
        print(f"\n📋 Fichiers EEG disponibles:")
        for i, (source, path) in enumerate(all_eeg_files, 1):
            print(f"  {i}. [{source}] {os.path.basename(path)}")
        
        try:
            choice = input(f"\nChoisissez un fichier (1-{len(all_eeg_files)}) ou Entrée pour annuler: ")
            if choice.isdigit() and 1 <= int(choice) <= len(all_eeg_files):
                source, selected_path = all_eeg_files[int(choice)-1]
                print(f"   ✅ Fichier sélectionné: {selected_path}")
                
                # Si on a un patient_id et que le fichier n'est pas au bon endroit, migrer
                if patient_id and source != f"patient_{patient_id}":
                    patient_dir = get_patient_dir(patient_id)
                    new_path = os.path.join(patient_dir, filename)
                    print(f"   📦 Migration vers dossier patient...")
                    shutil.copy2(selected_path, new_path)
                    print(f"   ✓ Copie effectuée")
                    return new_path
                
                return selected_path
        except (ValueError, KeyboardInterrupt):
            pass
    
    raise FileNotFoundError(f"Fichier introuvable: {filename}")

def migrate_legacy_files(patient_id=None):
    """
    Migre tous les anciens fichiers vers la nouvelle structure
    """
    print("\n🔄 Migration des fichiers legacy...")
    
    migrated = 0
    
    # Chercher les fichiers dans data/
    if os.path.exists(DATA_DIR):
        legacy_files = [
            f for f in os.listdir(DATA_DIR) 
            if f.startswith('eeg_') and f.endswith('.csv')
        ]
        
        for filename in legacy_files:
            old_path = os.path.join(DATA_DIR, filename)
            
            # Déterminer le patient
            if patient_id:
                target_patient = patient_id
            else:
                # Essayer d'extraire du .current_session.json
                from config import get_current_session
                session = get_current_session()
                if session and session.get('patient_id'):
                    target_patient = session['patient_id']
                else:
                    print(f"   ⚠️ Fichier ignoré (patient inconnu): {filename}")
                    continue
            
            # Migrer
            patient_dir = get_patient_dir(target_patient)
            new_path = os.path.join(patient_dir, filename)
            
            if not os.path.exists(new_path):
                print(f"   📦 Migration: {filename} -> patient_{target_patient}/")
                shutil.move(old_path, new_path)
                migrated += 1
            else:
                print(f"   ⚠️ Fichier déjà existant: {filename}")
    
    print(f"✅ {migrated} fichiers migrés")
    return migrated

def ensure_patient_file(eeg_path, patient_id):
    """
    Vérifie qu'un fichier est dans le bon dossier patient,
    le déplace si nécessaire
    """
    if not os.path.exists(eeg_path):
        return find_eeg_file_compat(eeg_path, patient_id)
    
    # Vérifier si le fichier est déjà dans le bon dossier
    patient_dir = get_patient_dir(patient_id)
    if not eeg_path.startswith(patient_dir):
        filename = os.path.basename(eeg_path)
        new_path = os.path.join(patient_dir, filename)
        
        print(f"📦 Déplacement du fichier vers dossier patient...")
        shutil.move(eeg_path, new_path)
        print(f"✓ Nouvel emplacement: {new_path}")
        return new_path
    
    return eeg_path