#!/usr/bin/env python
# 04_build_labels.py
# Construction des labels à partir des annotations - Multi-patient

import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (
    DATA_DIR, OUTPUTS_DIR, get_annotations_file, 
    list_all_patients, get_patient_output_dir
)

def select_patient():
    """Sélectionne un patient"""
    print("\n📋 SÉLECTION PATIENT")
    print("-" * 40)
    
    patients = list_all_patients()
    if not patients:
        raise ValueError("Aucun patient trouvé")
    
    print("Patients disponibles:")
    for i, p in enumerate(patients, 1):
        print(f"  {i}. {p}")
    
    choice = int(input("\nChoix patient: ")) - 1
    return patients[choice]

def load_annotations(patient_id):
    """Charge les annotations d'un patient"""
    annot_path = get_annotations_file(patient_id)
    
    if not os.path.exists(annot_path):
        raise FileNotFoundError(f"Annotations non trouvées: {annot_path}")
    
    df = pd.read_csv(annot_path)
    
    # Vérifier colonnes requises
    required = ["time_s", "label"]
    if not all(col in df.columns for col in required):
        raise ValueError(f"Annotations doivent contenir: {required}")
    
    # Nettoyer
    df = df.dropna(subset=["label"])
    df = df.sort_values("time_s").reset_index(drop=True)
    
    print(f"\n📊 {len(df)} annotations chargées")
    print(f"   Labels: {df['label'].unique()}")
    print(f"   Sessions: {df['session_id'].nunique() if 'session_id' in df.columns else 1}")
    
    return df

def load_clusters(patient_id):
    """Charge les clusters SOM du patient"""
    output_dir = get_patient_output_dir(patient_id)
    clusters_path = os.path.join(output_dir, "som_clusters.csv")
    
    if not os.path.exists(clusters_path):
        raise FileNotFoundError(f"Clusters non trouvés: {clusters_path}")
    
    df = pd.read_csv(clusters_path)
    
    if "time_s" not in df.columns:
        raise ValueError("Clusters doivent contenir 'time_s'")
    
    print(f"📊 {len(df)} fenêtres SOM chargées")
    
    return df

def assign_labels(df_clusters, df_annot):
    """Assigne les labels aux fenêtres"""
    
    if df_annot.empty:
        print("⚠️ Aucune annotation, tous les labels seront NaN")
        df_clusters["label_patient"] = np.nan
        return df_clusters
    
    # Temps des annotations
    t_ann = df_annot["time_s"].values
    labels = df_annot["label"].values
    
    # Pour chaque fenêtre, trouver l'annotation la plus récente
    t_win = df_clusters["time_s"].values
    window_labels = []
    
    for t in t_win:
        # Dernière annotation avant cette fenêtre
        idx = np.searchsorted(t_ann, t, side="right") - 1
        if idx >= 0:
            window_labels.append(labels[idx])
        else:
            window_labels.append(np.nan)
    
    df_clusters["label_patient"] = window_labels
    
    # Compter
    n_labeled = df_clusters["label_patient"].notna().sum()
    print(f"\n✅ {n_labeled}/{len(df_clusters)} fenêtres labellisées")
    
    if n_labeled > 0:
        print("\n📊 Distribution des labels:")
        print(df_clusters["label_patient"].value_counts())
    
    return df_clusters

def main():
    print("=" * 60)
    print("🏷️  LABELLISATION DES FENÊTRES - Multi-patient")
    print("=" * 60)
    
    try:
        # Sélectionner patient
        patient_id = select_patient()
        print(f"\nPatient sélectionné: {patient_id}")
        
        # Charger données
        df_annot = load_annotations(patient_id)
        df_clusters = load_clusters(patient_id)
        
        # Assigner labels
        df_labeled = assign_labels(df_clusters, df_annot)
        
        # Sauvegarder
        output_dir = get_patient_output_dir(patient_id)
        output_path = os.path.join(output_dir, "som_clusters_annotated.csv")
        df_labeled.to_csv(output_path, index=False)
        
        print(f"\n✅ Sauvegardé: {output_path}")
        
        # Résumé
        n_labeled = df_labeled["label_patient"].notna().sum()
        print("\n" + "=" * 60)
        print(f"RÉSUMÉ - Patient {patient_id}:")
        print(f"  Total fenêtres: {len(df_labeled)}")
        print(f"  Fenêtres labellisées: {n_labeled}")
        print(f"  Fenêtres non labellisées: {len(df_labeled) - n_labeled}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())