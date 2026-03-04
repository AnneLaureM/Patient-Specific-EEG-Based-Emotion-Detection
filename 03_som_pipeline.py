#!/usr/bin/env python
# 03_som_pipeline.py
# Feature extraction and SOM training - Version avec compatibilité

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from minisom import MiniSom
from sklearn.preprocessing import StandardScaler
import os
import sys
import joblib
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (
    DATA_DIR, WINDOW_SEC, STEP_SEC, SOM_X, SOM_Y, SOM_ITERS, REGIONS,
    list_all_patients, get_patient_sessions, get_patient_output_dir,
    get_patient_model_dir, get_patient_figures_dir, get_current_session
)
from eeg_utils import (
    load_eeg, bandpass_filter, quick_qc, compute_band_powers,
    compute_alpha_asymmetry_regions, compute_connectivity_corr,
    DEFAULT_CHANNEL_NAMES
)
from file_utils import find_eeg_file_compat, ensure_patient_file, migrate_legacy_files

def select_patient_and_session():
    """Sélectionne un patient et une session avec compatibilité"""
    print("\n📋 SÉLECTION PATIENT")
    print("-" * 40)
    
    # Proposer migration des anciens fichiers
    migrate = input("Voulez-vous migrer les anciens fichiers? (o/N): ").lower()
    if migrate == 'o':
        migrate_legacy_files()
    
    # Vérifier la session courante d'abord
    current = get_current_session()
    if current:
        print(f"\n📌 Session courante trouvée:")
        print(f"  Patient: {current['patient_id']}")
        print(f"  Fichier: {current['eeg_filename']}")
        use_current = input("Utiliser cette session? (o/N): ").lower()
        if use_current == 'o':
            # Vérifier/compatibilité du fichier
            eeg_path = find_eeg_file_compat(
                current['eeg_file'], 
                current['patient_id']
            )
            return current['patient_id'], eeg_path
    
    # Sinon, lister tous les patients
    patients = list_all_patients()
    if not patients:
        print("\n⚠️ Aucun patient trouvé dans la nouvelle structure.")
        print("Recherche dans les anciens fichiers...")
        
        # Chercher dans l'ancien emplacement
        old_files = [f for f in os.listdir(DATA_DIR) 
                    if f.startswith('eeg_') and f.endswith('.csv')]
        
        if old_files:
            print(f"\n📋 Anciens fichiers trouvés:")
            for i, f in enumerate(old_files, 1):
                print(f"  {i}. {f}")
            
            choice = input("\nChoisissez un fichier à analyser (ou Entrée pour annuler): ")
            if choice.isdigit() and 1 <= int(choice) <= len(old_files):
                selected = old_files[int(choice)-1]
                
                # Demander le patient
                patient_id = input("ID du patient pour ce fichier (ex: P001): ") or "P001"
                
                # Migrer
                from file_utils import ensure_patient_file
                old_path = os.path.join(DATA_DIR, selected)
                new_path = ensure_patient_file(old_path, patient_id)
                
                return patient_id, new_path
        
        raise ValueError("Aucun fichier EEG trouvé")
    
    print("\nPatients disponibles:")
    for i, p in enumerate(patients, 1):
        sessions = get_patient_sessions(p)
        print(f"  {i}. {p} ({len(sessions)} sessions)")
    
    try:
        choice = int(input("\nChoix patient: ")) - 1
        patient_id = patients[choice]
    except (ValueError, IndexError):
        raise ValueError("Sélection invalide")
    
    # Lister les sessions du patient
    sessions = get_patient_sessions(patient_id)
    if not sessions:
        raise ValueError(f"Aucune session pour le patient {patient_id}")
    
    print(f"\nSessions pour {patient_id}:")
    for i, s in enumerate(sessions, 1):
        print(f"  {i}. {s['filename']}")
    
    try:
        sess_choice = int(input("\nChoix session: ")) - 1
        eeg_file = sessions[sess_choice]['path']
    except (ValueError, IndexError):
        raise ValueError("Sélection invalide")
    
    # Vérifier/compatibilité du fichier
    eeg_path = find_eeg_file_compat(eeg_file, patient_id)
    
    return patient_id, eeg_path

def extract_features(eeg_path, patient_id):
    """Extrait les features d'un fichier EEG"""
    print(f"\n📊 Chargement EEG: {os.path.basename(eeg_path)}")
    
    # Vérifier que le fichier existe (avec compatibilité)
    eeg_path = find_eeg_file_compat(eeg_path, patient_id)
    
    # Charger données
    time, data_raw, fs, ch_names = load_eeg(eeg_path, DEFAULT_CHANNEL_NAMES)
    print(f"   Durée: {time[-1]:.2f}s")
    print(f"   Échantillons: {len(time)}")
    print(f"   Fréquence: {fs} Hz")
    
    # Filtrage
    data_filt = bandpass_filter(data_raw, fs, 1., 40.)
    
    # Contrôle qualité
    qc = quick_qc(data_filt, ch_names)
    good_idx = qc["good_idx"]
    
    if len(good_idx) == 0:
        raise ValueError("Aucun canal valide")
    
    data_good = data_filt[:, good_idx]
    ch_good = [ch_names[i] for i in good_idx]
    print(f"   Canaux valides: {ch_good}")
    
    # Créer fenêtres
    window_samples = int(WINDOW_SEC * fs)
    step_samples = int(STEP_SEC * fs)
    
    idx_starts = np.arange(0, len(time) - window_samples, step_samples)
    print(f"   Création de {len(idx_starts)} fenêtres...")
    
    features_list = []
    t_centers = []
    
    for i, start in enumerate(idx_starts):
        if i % 100 == 0:
            print(f"   Progression: {i}/{len(idx_starts)}", end='\r')
        
        end = start + window_samples
        window = data_good[start:end, :]
        
        # Extraire features
        bp = compute_band_powers(window, fs)
        bandnames = sorted(bp.keys())
        feat_bands = [np.mean(bp[b]) for b in bandnames]
        
        # Features régionales
        regions_good = {}
        for reg, chans in REGIONS.items():
            chans_good = [ch for ch in chans if ch in ch_good]
            if chans_good:
                regions_good[reg] = chans_good
        
        alpha_left = alpha_right = faa = np.nan
        if "Frontal_L" in regions_good and "Frontal_R" in regions_good:
            faa_res = compute_alpha_asymmetry_regions(
                window, fs, ch_good,
                left_region="Frontal_L",
                right_region="Frontal_R",
                regions=regions_good
            )
            if faa_res:
                if isinstance(faa_res, dict):
                    alpha_left = faa_res.get("alpha_left", np.nan)
                    alpha_right = faa_res.get("alpha_right", np.nan)
                    faa = faa_res.get("FAA", np.nan)
                else:
                    faa = faa_res
        
        # Connectivité
        corr_mat, _ = compute_connectivity_corr(window, ch_good)
        abs_corr = np.abs(corr_mat[np.triu_indices(len(ch_good), k=1)])
        mean_corr = np.mean(abs_corr) if len(abs_corr) > 0 else np.nan
        std_corr = np.std(abs_corr) if len(abs_corr) > 0 else np.nan
        
        # Combiner
        feats = np.concatenate([
            feat_bands,
            [alpha_left, alpha_right, faa],
            [mean_corr, std_corr]
        ])
        
        t_center = (time[start] + time[end-1]) / 2.0
        features_list.append(feats)
        t_centers.append(t_center)
    
    print()  # Nouvelle ligne
    
    X = np.vstack(features_list)
    t_centers = np.array(t_centers)
    
    # Noms des features
    feature_names = (
        [f"bp_{b}" for b in bandnames] +
        ["alpha_left", "alpha_right", "FAA"] +
        ["mean_abs_corr", "std_abs_corr"]
    )
    
    print(f"\n✅ Extraits: {len(X)} fenêtres x {X.shape[1]} features")
    
    return X, t_centers, feature_names, fs

def train_som(X, t_centers, feature_names, patient_id):
    """Entraîne le SOM pour un patient"""
    print("\n🧠 Entraînement Self-Organizing Map...")
    
    # Normalisation
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Sauvegarder le scaler
    model_dir = get_patient_model_dir(patient_id)
    joblib.dump(scaler, os.path.join(model_dir, "feature_scaler.joblib"))
    
    # Initialiser SOM
    som = MiniSom(
        x=SOM_X, y=SOM_Y,
        input_len=X_scaled.shape[1],
        sigma=1.0,
        learning_rate=0.5,
        neighborhood_function='gaussian',
        random_seed=42
    )
    
    # Initialiser poids
    som.random_weights_init(X_scaled)
    print(f"   Entraînement pour {SOM_ITERS} itérations...")
    
    # Entraîner
    som.train_random(X_scaled, SOM_ITERS)
    print("✓ SOM entraîné")
    
    # Obtenir BMUs
    bmu_coords = np.array([som.winner(x) for x in X_scaled])
    
    # Calculer erreurs
    quantization_errors = [np.linalg.norm(x - som.get_weights()[bmu_coords[i]]) 
                          for i, x in enumerate(X_scaled)]
    
    # Sauvegarder résultats
    output_dir = get_patient_output_dir(patient_id)
    
    df_features = pd.DataFrame(X, columns=feature_names)
    df_features.insert(0, "time_s", t_centers)
    df_features.to_csv(os.path.join(output_dir, "som_features.csv"), index=False)
    
    df_clusters = pd.DataFrame({
        "time_s": t_centers,
        "bmu_x": bmu_coords[:, 0],
        "bmu_y": bmu_coords[:, 1],
        "bmu_id": bmu_coords[:, 0] * SOM_Y + bmu_coords[:, 1],
        "qe": quantization_errors
    })
    df_clusters.to_csv(os.path.join(output_dir, "som_clusters.csv"), index=False)
    
    print(f"✓ Features sauvegardées: {output_dir}/som_features.csv")
    print(f"✓ Clusters sauvegardés: {output_dir}/som_clusters.csv")
    print(f"   QE (moyenne): {np.mean(quantization_errors):.4f}")
    
    return som, bmu_coords, X_scaled

def visualize_som(som, X_scaled, t_centers, bmu_coords, patient_id):
    """Visualisations SOM"""
    print("\n🎨 Création visualisations...")
    
    figures_dir = get_patient_figures_dir(patient_id)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    
    # 1. U-Matrix
    ax1 = axes[0, 0]
    umatrix = som.distance_map()
    im1 = ax1.imshow(umatrix.T, cmap='viridis', origin='lower')
    plt.colorbar(im1, ax=ax1, label='Distance')
    ax1.set_title('U-Matrix')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    
    # 2. Distribution BMU
    ax2 = axes[0, 1]
    bmu_counts = pd.DataFrame(bmu_coords, columns=['x', 'y']).groupby(['x', 'y']).size()
    heatmap = np.zeros((SOM_X, SOM_Y))
    for (x, y), count in bmu_counts.items():
        heatmap[x, y] = count
    
    im2 = ax2.imshow(heatmap.T, cmap='YlOrRd', origin='lower')
    plt.colorbar(im2, ax=ax2, label='Nb fenêtres')
    ax2.set_title('Distribution BMU')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    
    # 3. Évolution temporelle
    ax3 = axes[1, 0]
    scatter = ax3.scatter(t_centers, bmu_coords[:, 0] * SOM_Y + bmu_coords[:, 1],
                          c=t_centers, cmap='viridis', s=10, alpha=0.6)
    plt.colorbar(scatter, ax=ax3, label='Temps (s)')
    ax3.set_xlabel('Temps (s)')
    ax3.set_ylabel('BMU ID')
    ax3.set_title('États cérébraux dans le temps')
    ax3.grid(True, alpha=0.3)
    
    # 4. Component planes
    ax4 = axes[1, 1]
    weights = som.get_weights()
    n_features = min(4, weights.shape[2])
    for i in range(n_features):
        ax4.plot(weights[:, :, i].flatten()[:100], label=f'Feature {i+1}')
    ax4.set_xlabel('Neuron Index')
    ax4.set_ylabel('Weight')
    ax4.set_title('Component Planes')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle(f'SOM Analysis - Patient {patient_id}', fontsize=16)
    plt.tight_layout()
    
    # Sauvegarder
    plt.savefig(os.path.join(figures_dir, "som_visualization.png"), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(figures_dir, "som_visualization.pdf"), bbox_inches='tight')
    plt.show()
    print(f"✓ Visualisations sauvegardées: {figures_dir}")

def main():
    print("=" * 60)
    print("🧠 PIPELINE SOM - Patient-Specific")
    print("=" * 60)
    
    try:
        # Sélectionner patient et session
        patient_id, eeg_path = select_patient_and_session()
        print(f"\nPatient: {patient_id}")
        print(f"Fichier: {os.path.basename(eeg_path)}")
        
        # Extraire features
        X, t_centers, feature_names, fs = extract_features(eeg_path, patient_id)
        
        # Entraîner SOM
        som, bmu_coords, X_scaled = train_som(X, t_centers, feature_names, patient_id)
        
        # Visualiser
        visualize_som(som, X_scaled, t_centers, bmu_coords, patient_id)
        
        print("\n" + "=" * 60)
        print("✅ Pipeline SOM terminé avec succès")
        print(f"📁 Résultats dans: outputs/patient_{patient_id}/")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())