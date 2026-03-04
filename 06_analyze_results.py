#!/usr/bin/env python
# 06_analyze_results.py
# Generate all figures and metrics for scientific paper - Version finale corrigée

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
import os
import joblib
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')  # Ignorer les avertissements

from config import (
    OUTPUTS_DIR, MODELS_DIR, FIGURES_DIR, DATA_DIR,
    EMOTION_COLORS, PATIENTS, get_output_filename,
    get_patient_figures_dir, get_patient_output_dir, get_patient_model_dir,
    get_patient_sessions, list_all_patients, get_patient_info
)

# Set style for scientific figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['legend.fontsize'] = 10

def figure1_pipeline_overview():
    """Figure 1: Pipeline overview diagram"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Create pipeline steps
    steps = [
        "EEG Acquisition\n(8 channels, 256 Hz)",
        "Emotion Tagging\n(Streamlit Interface)",
        "Feature Extraction\n(Band powers, FAA, Connectivity)",
        "Self-Organizing Map\n(10x10 neurons)",
        "Patient-Specific Model\n(Random Forest)"
    ]
    
    y_pos = np.arange(len(steps))
    
    # Create horizontal bars
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(steps)))
    bars = ax.barh(y_pos, [1]*len(steps), left=np.arange(len(steps)), 
                   height=0.6, color=colors, alpha=0.7)
    
    # Add labels
    for i, (bar, step) in enumerate(zip(bars, steps)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2,
                step, ha='center', va='center', fontsize=11, fontweight='bold')
    
    # Add arrows between steps
    for i in range(len(steps)-1):
        ax.annotate('', xy=(i+1.5, i), xytext=(i+0.5, i),
                   arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
    
    ax.set_xlim(-0.5, len(steps)-0.5)
    ax.set_ylim(-0.5, len(steps)-0.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title('Figure 1: EEG Emotion Detection Pipeline', fontsize=18, pad=20)
    
    plt.tight_layout()
    
    # Sauvegarder dans le dossier général figures
    plt.savefig(os.path.join(FIGURES_DIR, 'figure1_pipeline.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIGURES_DIR, 'figure1_pipeline.pdf'), bbox_inches='tight')
    print("✓ Figure 1 saved in figures/")

def figure2_som_visualization(patient_id='P001'):
    """Figure 2: SOM visualization with emotion mapping - Version corrigée"""
    
    # Récupérer les dossiers spécifiques au patient
    patient_figures_dir = get_patient_figures_dir(patient_id)
    patient_output_dir = get_patient_output_dir(patient_id)
    
    # Récupérer les infos patient sans générer d'avertissement
    try:
        patient_info = get_patient_info(patient_id)
        age_display = patient_info.get('age', 'N/A')
    except:
        age_display = 'N/A'
    
    print(f"\n📊 Génération figure 2 pour patient {patient_id}...")
    
    # Load data
    clusters_file = os.path.join(patient_output_dir, "som_clusters.csv")
    if not os.path.exists(clusters_file):
        print(f"⚠ No clusters file found for {patient_id}")
        return
    
    df_clusters = pd.read_csv(clusters_file)
    
    # Load annotations if available
    annotations_file = os.path.join(patient_output_dir, "som_clusters_annotated.csv")
    has_annotations = os.path.exists(annotations_file)
    
    if has_annotations:
        df_annot = pd.read_csv(annotations_file)
        df_annot = df_annot.dropna(subset=['label_patient'])
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    
    # Plot 1: SOM U-Matrix
    ax1 = axes[0, 0]
    from minisom import MiniSom
    
    scaler_file = os.path.join(get_patient_model_dir(patient_id), "feature_scaler.joblib")
    if os.path.exists(scaler_file):
        # Create dummy SOM for visualization (simplified)
        som = MiniSom(10, 10, 9, sigma=1.0, learning_rate=0.5)
        
        # Load features
        features_file = os.path.join(patient_output_dir, "som_features.csv")
        if os.path.exists(features_file):
            df_feat = pd.read_csv(features_file)
            X = df_feat.drop('time_s', axis=1).values
            som.random_weights_init(X)
            som.train_random(X, 100)
            
            # Plot U-Matrix
            umatrix = som.distance_map()
            im = ax1.imshow(umatrix.T, cmap='viridis', origin='lower')
            plt.colorbar(im, ax=ax1, label='Distance')
            ax1.set_title('a) SOM U-Matrix', fontsize=14)
            ax1.set_xlabel('X')
            ax1.set_ylabel('Y')
    
    # Plot 2: BMU Distribution
    ax2 = axes[0, 1]
    bmu_counts = df_clusters.groupby(['bmu_x', 'bmu_y']).size().reset_index(name='count')
    heatmap_data = np.zeros((10, 10))
    for _, row in bmu_counts.iterrows():
        heatmap_data[int(row['bmu_x']), int(row['bmu_y'])] = row['count']
    
    sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax2,
                cbar_kws={'label': 'Number of Windows'})
    ax2.set_title('b) BMU Distribution', fontsize=14)
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    
    # Plot 3: Emotion Distribution
    ax3 = axes[1, 0]
    if has_annotations:
        emotion_counts = df_annot['label_patient'].value_counts()
        colors = [EMOTION_COLORS.get(e, '#888888') for e in emotion_counts.index]
        emotion_counts.plot(kind='bar', ax=ax3, color=colors)
        ax3.set_title('c) Emotion Distribution', fontsize=14)
        ax3.set_xlabel('Emotion')
        ax3.set_ylabel('Count')
        ax3.tick_params(axis='x', rotation=45)
    
    # Plot 4: Temporal Evolution
    ax4 = axes[1, 1]
    ax4.plot(df_clusters['time_s'], df_clusters['bmu_x'] * 10 + df_clusters['bmu_y'], 
             'b-', alpha=0.7, linewidth=1)
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('BMU ID')
    ax4.set_title('d) Temporal Evolution of Brain States', fontsize=14)
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle(f'Figure 2: SOM Analysis - Patient {patient_id} (Age: {age_display})', 
                 fontsize=16, y=1.02)
    plt.tight_layout()
    
    # Sauvegarder dans le dossier figures du patient
    plt.savefig(os.path.join(patient_figures_dir, f'figure2_som_{patient_id}.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(patient_figures_dir, f'figure2_som_{patient_id}.pdf'), bbox_inches='tight')
    print(f"✓ Figure 2 saved in {patient_figures_dir}")

def figure3_confusion_matrix(patient_id='P001'):
    """Figure 3: Confusion matrix for patient model - Version corrigée sans warning"""
    
    patient_figures_dir = get_patient_figures_dir(patient_id)
    patient_output_dir = get_patient_output_dir(patient_id)
    patient_model_dir = get_patient_model_dir(patient_id)
    
    # Récupérer les infos patient sans générer d'avertissement
    try:
        patient_info = get_patient_info(patient_id)
    except:
        patient_info = {"age": "N/A", "sexe": "N/A", "condition": "N/A"}
    
    print(f"\n📊 Génération figure 3 pour patient {patient_id}...")
    
    # Load model and test data
    model_file = os.path.join(patient_model_dir, "patient_model_rf.joblib")
    if not os.path.exists(model_file):
        print(f"⚠ No model found for {patient_id}")
        return
    
    artifact = joblib.load(model_file)
    model = artifact['model']
    classes = artifact['classes_']
    
    # Load annotated data
    annotated_file = os.path.join(patient_output_dir, "som_clusters_annotated.csv")
    features_file = os.path.join(patient_output_dir, "som_features.csv")
    
    if not os.path.exists(annotated_file) or not os.path.exists(features_file):
        print(f"⚠ Missing data files for confusion matrix")
        return
    
    df_annot = pd.read_csv(annotated_file)
    df_annot = df_annot.dropna(subset=['label_patient'])
    
    df_feat = pd.read_csv(features_file)
    
    # Merge
    df_merged = pd.merge(df_feat, df_annot[['time_s', 'label_patient']], on='time_s')
    
    if len(df_merged) == 0:
        print(f"⚠ No matching data for confusion matrix")
        return
    
    X = df_merged.drop(['time_s', 'label_patient'], axis=1).values
    y_true = df_merged['label_patient'].values
    
    # Predict
    y_pred = model.predict(X)
    
    # Vérifier le nombre de classes uniques
    unique_labels = np.unique(y_true)
    
    if len(unique_labels) < 2:
        print(f"⚠️ Pas assez de classes pour une matrice de confusion (trouvé: {unique_labels})")
        # Créer une figure avec message
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.text(0.5, 0.5, f"Pas assez de données pour matrice de confusion\n(1 seule classe: {unique_labels[0]})", 
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_title(f'Figure 3: Pas assez de données - Patient {patient_id}')
        ax.axis('off')
        plt.tight_layout()
        
        # Sauvegarder
        plt.savefig(os.path.join(patient_figures_dir, f'figure3_confusion_{patient_id}.png'), 
                   dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(patient_figures_dir, f'figure3_confusion_{patient_id}.pdf'), 
                   bbox_inches='tight')
        print(f"✓ Figure 3 saved (message d'information)")
        return {
            'accuracy': 0, 
            'n_samples': len(df_merged), 
            'n_classes': 1,
            'message': 'Pas assez de classes'
        }
    
    # Confusion matrix (avec toutes les classes)
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Normalize
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    im = ax.imshow(cm_norm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.colorbar(im, ax=ax, label='Normalized Accuracy')
    
    # Add labels
    tick_marks = np.arange(len(classes))
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(classes, rotation=45, ha='right')
    ax.set_yticklabels(classes)
    
    # Add text annotations
    thresh = cm_norm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f'{cm[i, j]}\n({cm_norm[i, j]:.2f})',
                   ha="center", va="center",
                   color="white" if cm_norm[i, j] > thresh else "black")
    
    ax.set_ylabel('True Label')
    ax.set_xlabel('Predicted Label')
    
    # Récupérer l'âge pour le titre
    age_display = patient_info.get('age', 'N/A')
    ax.set_title(f'Figure 3: Confusion Matrix - Patient {patient_id} (Age: {age_display})\nAccuracy: {np.trace(cm)/np.sum(cm):.2%}')
    
    plt.tight_layout()
    
    # Sauvegarder dans le dossier figures du patient
    plt.savefig(os.path.join(patient_figures_dir, f'figure3_confusion_{patient_id}.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(patient_figures_dir, f'figure3_confusion_{patient_id}.pdf'), bbox_inches='tight')
    print(f"✓ Figure 3 saved in {patient_figures_dir}")
    
    # Return metrics for paper
    return {
        'accuracy': np.trace(cm)/np.sum(cm),
        'n_samples': len(df_merged),
        'n_classes': len(classes)
    }

def figure4_feature_importance(patient_id='P001'):
    """Figure 4: Feature importance analysis - Version corrigée"""
    
    patient_figures_dir = get_patient_figures_dir(patient_id)
    patient_model_dir = get_patient_model_dir(patient_id)
    
    print(f"\n📊 Génération figure 4 pour patient {patient_id}...")
    
    model_file = os.path.join(patient_model_dir, "patient_model_rf.joblib")
    if not os.path.exists(model_file):
        print(f"⚠ No model found for {patient_id}")
        return
    
    artifact = joblib.load(model_file)
    model = artifact['model']
    feature_names = artifact.get('feature_names', 
                                 ['bp_delta', 'bp_theta', 'bp_alpha', 'bp_beta',
                                  'alpha_left', 'alpha_right', 'FAA',
                                  'mean_abs_corr', 'std_abs_corr'])
    
    # Get feature importance
    importance = model.feature_importances_
    indices = np.argsort(importance)[::-1]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Feature importance bar chart
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(feature_names)))
    ax1.bar(range(len(importance)), importance[indices], color=colors)
    ax1.set_xticks(range(len(importance)))
    ax1.set_xticklabels([feature_names[i] for i in indices], rotation=45, ha='right')
    ax1.set_xlabel('Features')
    ax1.set_ylabel('Importance')
    ax1.set_title('a) Feature Importance (Random Forest)')
    
    # Plot 2: Cumulative importance
    cumsum = np.cumsum(importance[indices])
    ax2.plot(range(len(cumsum)), cumsum, 'b-o', linewidth=2, markersize=8)
    ax2.axhline(y=0.95, color='r', linestyle='--', label='95% threshold')
    ax2.set_xlabel('Number of Features')
    ax2.set_ylabel('Cumulative Importance')
    ax2.set_title('b) Cumulative Feature Importance')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.suptitle(f'Figure 4: Feature Analysis - Patient {patient_id}', fontsize=14)
    plt.tight_layout()
    
    # Sauvegarder dans le dossier figures du patient
    plt.savefig(os.path.join(patient_figures_dir, f'figure4_features_{patient_id}.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(patient_figures_dir, f'figure4_features_{patient_id}.pdf'), bbox_inches='tight')
    print(f"✓ Figure 4 saved in {patient_figures_dir}")

def generate_all_figures(patient_id='P001'):
    """Generate all figures for the paper"""
    
    print(f"\n{'='*60}")
    print(f"Génération des figures pour patient {patient_id}")
    print(f"{'='*60}")
    
    # Figures spécifiques au patient
    figure2_som_visualization(patient_id)
    metrics = figure3_confusion_matrix(patient_id)
    figure4_feature_importance(patient_id)
    
    return metrics

def generate_paper_table():
    """Generate summary table for paper - Version sans warning"""
    
    results = []
    
    # Utiliser list_all_patients() pour trouver tous les patients
    patients = list_all_patients()
    
    if not patients:
        print("⚠️ Aucun patient trouvé dans data/patients/")
        return None
    
    for patient_id in patients:
        # Get metrics
        patient_model_dir = get_patient_model_dir(patient_id)
        patient_output_dir = get_patient_output_dir(patient_id)
        
        # Récupérer les infos sans warning
        try:
            patient_info = get_patient_info(patient_id)
            age = patient_info.get('age', 'N/A')
            sex = patient_info.get('sexe', 'N/A')
            condition = patient_info.get('condition', 'N/A')
        except:
            age = 'N/A'
            sex = 'N/A'
            condition = 'N/A'
        
        metrics = {
            'Patient': patient_id,
            'Age': age,
            'Sex': sex,
            'Condition': condition
        }
        
        # Count sessions
        sessions = get_patient_sessions(patient_id)
        metrics['Sessions'] = len(sessions)
        
        # Count annotations
        annotated_file = os.path.join(patient_output_dir, "som_clusters_annotated.csv")
        if os.path.exists(annotated_file):
            df = pd.read_csv(annotated_file)
            df = df.dropna(subset=['label_patient'])
            metrics['Annotations'] = len(df)
            metrics['Classes'] = df['label_patient'].nunique()
        
        # Model accuracy
        model_file = os.path.join(patient_model_dir, "patient_model_rf.joblib")
        if os.path.exists(model_file):
            try:
                artifact = joblib.load(model_file)
                accuracy = artifact.get('accuracy', 0)
                metrics['Accuracy'] = f"{accuracy:.2%}"
            except:
                metrics['Accuracy'] = 'N/A'
        
        results.append(metrics)
    
    # Create DataFrame
    df_results = pd.DataFrame(results)
    
    # Save
    df_results.to_csv(os.path.join(OUTPUTS_DIR, "paper_table.csv"), index=False)
    
    print("\n" + "="*60)
    print("TABLE 1: Patient Demographics and Results")
    print("="*60)
    print(df_results.to_string(index=False))
    
    return df_results

if __name__ == "__main__":
    print("="*60)
    print("GENERATING FIGURES FOR SCIENTIFIC PAPER")
    print("="*60)
    
    # Générer la figure générale
    figure1_pipeline_overview()
    
    # Générer pour tous les patients trouvés
    patients = list_all_patients()
    
    if patients:
        print(f"\n📋 Patients trouvés: {patients}")
        
        all_metrics = {}
        for patient_id in patients:
            metrics = generate_all_figures(patient_id)
            all_metrics[patient_id] = metrics
        
        # Generate summary table
        generate_paper_table()
    else:
        print("\n⚠️ Aucun patient trouvé dans data/patients/")
        print("   Voulez-vous générer les figures pour les patients par défaut?")
        response = input("   (o/N): ").lower()
        if response == 'o':
            default_patients = ['P001', 'P002']
            for patient_id in default_patients:
                generate_all_figures(patient_id)
            generate_paper_table()
    
    print("\n" + "="*60)
    print("✅ Toutes les figures générées avec succès!")
    print(f"📁 Figures générales: {FIGURES_DIR}")
    print(f"📁 Figures par patient: {FIGURES_DIR}/patient_*/")
    print("="*60)