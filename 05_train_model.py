#!/usr/bin/env python
# 05_train_model.py
# Entraînement modèle patient-spécifique

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (
    list_all_patients, get_patient_output_dir, get_patient_model_dir
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
        output_dir = get_patient_output_dir(p)
        model_dir = get_patient_model_dir(p)
        annotated = os.path.join(output_dir, "som_clusters_annotated.csv")
        status = "✓" if os.path.exists(annotated) else " "
        print(f"  {status} {i}. {p}")
    
    choice = int(input("\nChoix patient: ")) - 1
    return patients[choice]

def load_training_data(patient_id):
    """Charge les données d'entraînement pour un patient"""
    
    output_dir = get_patient_output_dir(patient_id)
    
    # Charger features
    features_path = os.path.join(output_dir, "som_features.csv")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features non trouvées: {features_path}")
    
    df_feat = pd.read_csv(features_path)
    
    # Charger labels
    labels_path = os.path.join(output_dir, "som_clusters_annotated.csv")
    if not os.path.exists(labels_path):
        raise FileNotFoundError(f"Labels non trouvés: {labels_path}")
    
    df_label = pd.read_csv(labels_path)
    
    # Fusionner
    df = pd.merge(df_feat, df_label[["time_s", "label_patient"]], on="time_s")
    
    # Enlever NaN
    df = df.dropna(subset=["label_patient"])
    
    if len(df) == 0:
        raise ValueError("Aucune fenêtre labellisée!")
    
    # Séparer features et labels
    feature_cols = [c for c in df.columns if c not in ["time_s", "label_patient"]]
    X = df[feature_cols].values
    y = df["label_patient"].values
    
    print(f"\n📊 Données d'entraînement - Patient {patient_id}:")
    print(f"   Échantillons: {len(X)}")
    print(f"   Features: {len(feature_cols)}")
    print(f"   Classes: {np.unique(y)}")
    print(f"   Distribution:")
    for cls in np.unique(y):
        print(f"     {cls}: {sum(y == cls)}")
    
    return X, y, feature_cols

def train_model(X, y, feature_names, patient_id):
    """Entraîne un modèle Random Forest"""
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    print(f"\n🧠 Entraînement Random Forest:")
    print(f"   Train: {len(X_train)} échantillons")
    print(f"   Test: {len(X_test)} échantillons")
    
    # Créer modèle
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        class_weight='balanced'
    )
    
    rf.fit(X_train, y_train)
    
    # Évaluer
    y_pred = rf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n📈 Performance:")
    print(f"   Test Accuracy: {accuracy:.2%}")
    
    # Cross-validation
    cv_scores = cross_val_score(rf, X, y, cv=5)
    print(f"   CV Accuracy (moy ± std): {cv_scores.mean():.2%} ± {cv_scores.std():.2%}")
    
    # Rapport détaillé
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Matrice de confusion
    cm = confusion_matrix(y_test, y_pred)
    print("\n📊 Matrice de confusion:")
    print(cm)
    
    # Importance des features
    importance = pd.DataFrame({
        'feature': feature_names,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🔍 Top 5 Features importantes:")
    print(importance.head().to_string(index=False))
    
    return rf, accuracy, cv_scores, importance

def save_model(model, feature_names, classes, accuracy, cv_scores, importance, patient_id):
    """Sauvegarde le modèle et métadonnées"""
    
    model_dir = get_patient_model_dir(patient_id)
    
    artifact = {
        'model': model,
        'feature_names': feature_names,
        'classes_': classes,
        'accuracy': accuracy,
        'cv_scores': cv_scores,
        'feature_importance': importance.to_dict('records'),
        'training_date': datetime.now().isoformat(),
        'patient_id': patient_id
    }
    
    model_path = os.path.join(model_dir, "patient_model_rf.joblib")
    joblib.dump(artifact, model_path)
    print(f"\n✅ Modèle sauvegardé: {model_path}")
    
    # Sauvegarder métriques
    metrics_path = os.path.join(model_dir, "model_metrics.txt")
    with open(metrics_path, 'w') as f:
        f.write(f"Patient: {patient_id}\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"Accuracy: {accuracy:.2%}\n")
        f.write(f"CV Accuracy (mean): {cv_scores.mean():.2%}\n")
        f.write(f"CV Accuracy (std): {cv_scores.std():.2%}\n")
        f.write("\nFeature Importance:\n")
        f.write(importance.to_string())
    
    print(f"✅ Métriques sauvegardées: {metrics_path}")

def main():
    print("=" * 60)
    print("🤖 ENTRAÎNEMENT MODÈLE PATIENT-SPÉCIFIQUE")
    print("=" * 60)
    
    try:
        # Sélectionner patient
        patient_id = select_patient()
        print(f"\nPatient sélectionné: {patient_id}")
        
        # Charger données
        X, y, feature_names = load_training_data(patient_id)
        
        # Entraîner modèle
        model, accuracy, cv_scores, importance = train_model(X, y, feature_names, patient_id)
        
        # Sauvegarder
        save_model(model, feature_names, np.unique(y), accuracy, cv_scores, importance, patient_id)
        
        print("\n" + "=" * 60)
        print(f"✅ Modèle patient {patient_id} entraîné avec succès!")
        print(f"📁 Modèle dans: models/patient_{patient_id}/")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())