#!/usr/bin/env python
# 07_advanced_analysis.py - Version corrigée avec support multi-patients
# Génère toutes les figures pour le papier scientifique

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.signal import welch
from scipy.stats import pearsonr
import os
import sys
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (
    DATA_DIR, OUTPUTS_DIR, FIGURES_DIR, REGIONS,
    get_patient_figures_dir, get_patient_output_dir, get_patient_dir,
    get_patient_sessions, list_all_patients, get_patient_info,
    get_annotations_file
)
from eeg_utils import load_eeg, bandpass_filter

class AdvancedPaperAnalysis:
    """Generate advanced figures and statistics for the paper"""
    
    def __init__(self, patient_id=None, session_date=None):
        """
        Initialise l'analyse pour un patient spécifique
        
        Args:
            patient_id: ID du patient (ex: "P001", "Anne")
            session_date: Date de session optionnelle (sinon prend la plus récente)
        """
        from config import get_current_session
        
        self.patient_id = patient_id
        self.session_date = session_date
        
        # Récupérer la session courante si pas de patient spécifié
        if patient_id is None:
            current = get_current_session()
            if current:
                self.patient_id = current['patient_id']
                print(f"📌 Utilisation session courante: patient {self.patient_id}")
            else:
                # Lister tous les patients disponibles
                patients = list_all_patients()
                if patients:
                    self.patient_id = patients[0]
                    print(f"📌 Aucune session courante, utilisation du premier patient: {self.patient_id}")
                else:
                    raise ValueError("Aucun patient trouvé")
        
        # Récupérer les infos du patient
        self.patient_info = get_patient_info(self.patient_id)
        self.age = self.patient_info.get('age', 'N/A')
        
        # Déterminer le fichier EEG
        self.eeg_file = self._find_eeg_file()
        
        # Dossiers spécifiques au patient
        self.patient_figures_dir = get_patient_figures_dir(self.patient_id)
        self.patient_output_dir = get_patient_output_dir(self.patient_id)
        
        # Fichier d'annotations
        self.annot_file = get_annotations_file(self.patient_id)
        
        # Couleurs pour les figures
        self.colors = plt.cm.Set3(np.linspace(0, 1, 10))
        self.emotion_colors = {
            'fatigue': '#FF6B6B',
            'soif': '#4ECDC4',
            'serenite': '#45B7D1',
            'envie': '#96CEB4',
            'joie': '#FFEAA7',
            'neutre': '#D4D4D4',
            'peur': '#FF4444',
            'colere': '#FF8844',
            'excitation': '#FF44FF',
            'douleur': '#884444',
            'faim': '#44FF88',
            'parle': '#FFAA88'
        }
        
        self.results = {}
        
    def _find_eeg_file(self):
        """Trouve le fichier EEG pour le patient"""
        
        # Si une date spécifique est demandée
        if self.session_date:
            patient_dir = get_patient_dir(self.patient_id)
            possible_files = [
                os.path.join(patient_dir, f) 
                for f in os.listdir(patient_dir) 
                if f.startswith('eeg_') and self.session_date in f
            ]
            if possible_files:
                return possible_files[0]
        
        # Sinon, prendre la session la plus récente
        sessions = get_patient_sessions(self.patient_id)
        if sessions:
            print(f"📋 Sessions disponibles pour patient {self.patient_id}:")
            for i, s in enumerate(sessions[:5], 1):  # Afficher les 5 plus récentes
                print(f"   {i}. {s['filename']}")
            
            # Prendre la plus récente par défaut
            selected = sessions[0]['path']
            print(f"\n   ✅ Utilisation: {os.path.basename(selected)}")
            return selected
        
        raise FileNotFoundError(f"Aucun fichier EEG trouvé pour patient {self.patient_id}")
        
    def load_data(self):
        """Load EEG and annotation data"""
        print(f"\n📊 Chargement données patient {self.patient_id}...")
        
        # Vérifier fichier EEG
        if not os.path.exists(self.eeg_file):
            raise FileNotFoundError(f"Fichier EEG non trouvé: {self.eeg_file}")
        
        # Load EEG
        print(f"   Fichier: {os.path.basename(self.eeg_file)}")
        self.time, self.data_raw, self.fs, self.ch_names = load_eeg(self.eeg_file)
        self.data_filt = bandpass_filter(self.data_raw, self.fs, 1., 40.)
        
        # Load annotations
        if os.path.exists(self.annot_file):
            self.df_annot = pd.read_csv(self.annot_file)
            
            # Si une session spécifique est demandée, filtrer
            if self.session_date:
                mask = self.df_annot['eeg_file'].str.contains(self.session_date, na=False)
                self.df_annot = self.df_annot[mask]
            
            print(f"   Annotations: {len(self.df_annot)}")
            
            # Afficher la distribution
            if len(self.df_annot) > 0:
                print("\n   Distribution des annotations:")
                for label, count in self.df_annot['label'].value_counts().items():
                    print(f"     {label}: {count}")
        else:
            self.df_annot = pd.DataFrame()
            print("   ⚠️ Aucune annotation trouvée")
        
        print(f"\n   EEG durée: {self.time[-1]:.2f}s")
        print(f"   Échantillons: {len(self.time)}")
        print(f"   Fréquence: {self.fs} Hz")
        
        # Préparer les epochs
        self.prepare_epochs()
        
    def prepare_epochs(self, window_sec=4.0):
        """Prepare epochs around each annotation"""
        if len(self.df_annot) == 0:
            print("\n⚠️ Pas d'annotations - impossible de créer des epochs")
            self.epochs = {}
            return
            
        window_samples = int(window_sec * self.fs)
        self.epochs = {}
        
        print(f"\n📦 Préparation des epochs de {window_sec}s...")
        
        for _, row in self.df_annot.iterrows():
            state = row['label']
            t = row['time_s']
            
            # Trouver l'index autour de l'annotation
            center_idx = np.searchsorted(self.time, t)
            start_idx = max(0, center_idx - window_samples//2)
            end_idx = min(len(self.time), start_idx + window_samples)
            
            # Extraire l'epoch
            epoch = self.data_filt[start_idx:end_idx, :]
            
            # Vérifications qualité
            if epoch.shape[0] < window_samples * 0.8:  # Moins de 80% de la fenêtre
                print(f"   ⚠️ Epoch trop court pour {state} à t={t:.1f}s: {epoch.shape[0]}/{window_samples}")
                continue
                
            if np.std(epoch) < 1e-6:  # Signal constant
                print(f"   ⚠️ Signal constant pour {state} à t={t:.1f}s")
                continue
                
            if state not in self.epochs:
                self.epochs[state] = []
            
            self.epochs[state].append(epoch)
        
        # Statistiques
        print("\n📊 Epochs par état:")
        total_epochs = 0
        for state, epochs in self.epochs.items():
            print(f"   {state}: {len(epochs)} epochs")
            total_epochs += len(epochs)
        
        if total_epochs == 0:
            print("   ⚠️ Aucun epoch valide créé")
    
    def figure5_temporal_timeline(self):
        """Figure 5: Temporal timeline of EEG and annotations"""
        if len(self.df_annot) == 0:
            print("⚠️ No annotations for timeline figure")
            return
            
        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
        
        # Plot 1: Raw EEG (first 30 seconds)
        ax1 = axes[0]
        plot_duration = min(30, self.time[-1])
        plot_samples = int(plot_duration * self.fs)
        
        ax1.plot(self.time[:plot_samples], self.data_raw[:plot_samples, 0], 
                'b-', linewidth=0.5, alpha=0.7)
        ax1.set_ylabel('Amplitude (µV)')
        ax1.set_title(f'a) Raw EEG - Channel F3 (patient {self.patient_id})')
        ax1.grid(True, alpha=0.3)
        
        # Add annotation markers
        for _, row in self.df_annot.iterrows():
            if row['time_s'] < plot_duration:
                color = self.emotion_colors.get(row['label'], 'gray')
                ax1.axvline(x=row['time_s'], color=color, 
                           alpha=0.8, linewidth=2, linestyle='--')
                ax1.text(row['time_s'], ax1.get_ylim()[1]*0.9, row['label'], 
                        rotation=45, fontsize=8, ha='right', color=color)
        
        # Plot 2: Filtered EEG
        ax2 = axes[1]
        ax2.plot(self.time[:plot_samples], self.data_filt[:plot_samples, 0], 
                'g-', linewidth=0.5, alpha=0.7)
        ax2.set_ylabel('Amplitude (µV)')
        ax2.set_title('b) Filtered EEG (1-40 Hz)')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Annotation timeline
        ax3 = axes[2]
        y_pos = np.arange(len(self.df_annot))
        colors = [self.emotion_colors.get(l, 'gray') for l in self.df_annot['label']]
        ax3.scatter(self.df_annot['time_s'], y_pos, c=colors, s=100, alpha=0.8, 
                   edgecolors='black', linewidth=0.5)
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(self.df_annot['label'])
        ax3.set_xlabel('Time (seconds)')
        ax3.set_ylabel('Emotional State')
        ax3.set_title('c) Annotation Timeline')
        ax3.grid(True, alpha=0.3, axis='x')
        ax3.set_xlim(0, self.time[-1])
        
        age_display = self.patient_info.get('age', 'N/A')
        plt.suptitle(f'Figure 5: Temporal Dynamics - Patient {self.patient_id} (Age: {age_display})', 
                    fontsize=14, y=1.02)
        plt.tight_layout()
        
        # Sauvegarder dans le dossier du patient
        plt.savefig(os.path.join(self.patient_figures_dir, f'figure5_timeline_{self.patient_id}.png'), 
                   dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(self.patient_figures_dir, f'figure5_timeline_{self.patient_id}.pdf'), 
                   bbox_inches='tight')
        print(f"✅ Figure 5 saved in {self.patient_figures_dir}")
        
    def figure6_connectivity_matrices(self):
        """Figure 6: Connectivity matrices for different emotional states"""
        if not hasattr(self, 'epochs') or len(self.epochs) == 0:
            print("⚠️ No epochs available for connectivity analysis")
            return
            
        states = list(self.epochs.keys())
        n_states = len(states)
        
        if n_states == 0:
            return
            
        # Calculer la disposition des subplots
        n_cols = min(3, n_states)
        n_rows = (n_states + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
        if n_rows == 1 and n_cols == 1:
            axes = np.array([axes])
        axes = axes.flatten()
        
        channel_labels = ['F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2']
        
        print("\n🔗 Calcul des matrices de connectivité...")
        
        for idx, state in enumerate(states):
            if idx >= len(axes):
                break
                
            epochs = self.epochs[state]
            corr_mats = []
            
            for epoch in epochs:
                # Calculer la matrice de corrélation
                corr_mat = np.corrcoef(epoch.T)
                
                # Remplacer les NaN par 0
                corr_mat = np.nan_to_num(corr_mat, nan=0.0)
                
                # S'assurer que la diagonale est 1
                np.fill_diagonal(corr_mat, 1.0)
                
                corr_mats.append(corr_mat)
            
            if corr_mats:
                # Moyenne des matrices
                avg_corr = np.mean(corr_mats, axis=0)
                
                # Statistiques
                print(f"   {state}: {len(corr_mats)} matrices")
                print(f"      Corr moyenne: {np.mean(avg_corr[np.triu_indices_from(avg_corr, k=1)]):.3f}")
                
                # Plot
                im = axes[idx].imshow(avg_corr, cmap='RdBu_r', vmin=-1, vmax=1, aspect='equal')
                axes[idx].set_title(f'{state} (n={len(corr_mats)})', fontsize=12)
                axes[idx].set_xticks(range(8))
                axes[idx].set_yticks(range(8))
                axes[idx].set_xticklabels(channel_labels, rotation=45, fontsize=8)
                axes[idx].set_yticklabels(channel_labels, fontsize=8)
                
                # Ajouter une colorbar seulement pour le premier subplot
                if idx == 0:
                    plt.colorbar(im, ax=axes[idx], label='Pearson Correlation', 
                               fraction=0.046, pad=0.04)
            else:
                axes[idx].text(0.5, 0.5, 'Insufficient\ndata', ha='center', va='center', fontsize=12)
                axes[idx].set_title(f'{state} (no data)')
        
        # Cacher les subplots inutilisés
        for idx in range(len(states), len(axes)):
            axes[idx].set_visible(False)
        
        plt.suptitle(f'Figure 6: Functional Connectivity - Patient {self.patient_id}', 
                    fontsize=14, y=1.02)
        plt.tight_layout()
        
        # Sauvegarder dans le dossier du patient
        plt.savefig(os.path.join(self.patient_figures_dir, f'figure6_connectivity_{self.patient_id}.png'), 
                   dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(self.patient_figures_dir, f'figure6_connectivity_{self.patient_id}.pdf'), 
                   bbox_inches='tight')
        print(f"✅ Figure 6 saved in {self.patient_figures_dir}")
        
    def figure7_spectral_analysis(self):
        """Figure 7: Spectral analysis for different emotional states"""
        if not hasattr(self, 'epochs') or len(self.epochs) == 0:
            print("⚠️ No epochs available for spectral analysis")
            return
            
        states = list(self.epochs.keys())
        n_states = len(states)
        
        if n_states == 0:
            return
            
        # Calculer la disposition des subplots
        n_cols = min(3, n_states)
        n_rows = (n_states + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
        if n_rows == 1 and n_cols == 1:
            axes = np.array([axes])
        axes = axes.flatten()
        
        # Bandes de fréquence
        bands = {
            'delta': (1, 4, '#FF9999'),
            'theta': (4, 8, '#99FF99'),
            'alpha': (8, 13, '#9999FF'),
            'beta': (13, 30, '#FFFF99')
        }
        
        print("\n📈 Calcul des analyses spectrales...")
        
        for idx, state in enumerate(states):
            if idx >= len(axes):
                break
                
            epochs = self.epochs[state]
            all_psd = []
            
            for epoch in epochs:
                # Calculer la PSD avec Welch
                nperseg = min(256, len(epoch))
                if len(epoch) >= nperseg:
                    f, psd = welch(epoch, fs=self.fs, nperseg=nperseg, axis=0)
                    
                    # Normaliser
                    psd_norm = psd / (np.sum(psd, axis=0, keepdims=True) + 1e-12)
                    
                    # Moyenne sur tous les canaux
                    psd_mean = np.mean(psd_norm, axis=1)
                    all_psd.append(psd_mean)
            
            if all_psd:
                # S'assurer que toutes les PSD ont la même longueur
                min_len = min(len(p) for p in all_psd)
                all_psd = [p[:min_len] for p in all_psd]
                f = f[:min_len]
                
                mean_psd = np.mean(all_psd, axis=0)
                std_psd = np.std(all_psd, axis=0)
                
                # Plot
                ax = axes[idx]
                ax.plot(f, mean_psd, 'b-', linewidth=2, label='Mean PSD')
                ax.fill_between(f, mean_psd - std_psd, mean_psd + std_psd, 
                               alpha=0.3, color='blue', label='±1 SD')
                
                # Colorier les bandes
                for band_name, (fmin, fmax, color) in bands.items():
                    ax.axvspan(fmin, fmax, alpha=0.2, color=color, label=band_name)
                
                ax.set_xlim(1, 30)
                ax.set_ylim(0, max(mean_psd + std_psd) * 1.1)
                ax.set_xlabel('Frequency (Hz)')
                ax.set_ylabel('Normalized Power')
                ax.set_title(f'{state} (n={len(epochs)} epochs)')
                ax.grid(True, alpha=0.3)
                
                if idx == 0:
                    ax.legend(loc='upper right', fontsize=8)
            else:
                axes[idx].text(0.5, 0.5, 'Insufficient\ndata', ha='center', va='center', fontsize=12)
                axes[idx].set_title(f'{state} (no data)')
        
        # Cacher les subplots inutilisés
        for idx in range(len(states), len(axes)):
            axes[idx].set_visible(False)
        
        plt.suptitle(f'Figure 7: Spectral Signatures - Patient {self.patient_id}', 
                    fontsize=14, y=1.02)
        plt.tight_layout()
        
        # Sauvegarder dans le dossier du patient
        plt.savefig(os.path.join(self.patient_figures_dir, f'figure7_spectral_{self.patient_id}.png'), 
                   dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(self.patient_figures_dir, f'figure7_spectral_{self.patient_id}.pdf'), 
                   bbox_inches='tight')
        print(f"✅ Figure 7 saved in {self.patient_figures_dir}")
        
    def generate_statistics(self):
        """Generate statistical tests for the paper"""
        
        stats_dict = {
            'patient_id': self.patient_id,
            'age': self.age,
            'session_duration': self.time[-1] if hasattr(self, 'time') else 0,
            'n_samples': len(self.time) if hasattr(self, 'time') else 0,
            'fs': self.fs if hasattr(self, 'fs') else 0,
            'n_windows': len(self.time) // int(4 * self.fs) if hasattr(self, 'time') else 0,
            'n_annotations': len(self.df_annot) if hasattr(self, 'df_annot') else 0,
            'unique_states': len(self.df_annot['label'].unique()) if len(self.df_annot) > 0 else 0,
        }
        
        if len(self.df_annot) > 0:
            stats_dict['state_distribution'] = self.df_annot['label'].value_counts().to_dict()
        
        if hasattr(self, 'epochs'):
            stats_dict['epochs_per_state'] = {state: len(epochs) for state, epochs in self.epochs.items()}
        
        # Load model metrics
        metrics_file = os.path.join(self.patient_output_dir, "model_metrics.txt")
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r') as f:
                content = f.read()
                import re
                acc_match = re.search(r'Accuracy: ([\d.]+%)', content)
                if acc_match:
                    stats_dict['accuracy'] = acc_match.group(1)
                cv_match = re.search(r'CV Accuracy \(mean\): ([\d.]+%)', content)
                if cv_match:
                    stats_dict['cv_accuracy'] = cv_match.group(1)
        
        print("\n" + "="*50)
        print(f"📊 STATISTIQUES - Patient {self.patient_id}")
        print("="*50)
        for key, value in stats_dict.items():
            if key not in ['state_distribution', 'epochs_per_state']:
                print(f"   {key}: {value}")
        
        if 'state_distribution' in stats_dict:
            print("\n   Distribution des annotations:")
            for state, count in stats_dict['state_distribution'].items():
                print(f"      {state}: {count}")
        
        if 'epochs_per_state' in stats_dict:
            print("\n   Epochs par état:")
            for state, count in stats_dict['epochs_per_state'].items():
                print(f"      {state}: {count}")
        
        # Sauvegarder les stats
        stats_file = os.path.join(self.patient_output_dir, f"advanced_stats_{self.patient_id}.txt")
        with open(stats_file, 'w') as f:
            for key, value in stats_dict.items():
                f.write(f"{key}: {value}\n")
        
        return stats_dict

def select_patient():
    """Sélectionne un patient pour l'analyse avancée"""
    patients = list_all_patients()
    
    if not patients:
        print("⚠️ Aucun patient trouvé dans data/patients/")
        return None
    
    print("\n📋 Patients disponibles:")
    for i, p in enumerate(patients, 1):
        sessions = get_patient_sessions(p)
        info = get_patient_info(p)
        age = info.get('age', '?')
        print(f"  {i}. {p} (âge: {age}, {len(sessions)} sessions)")
    
    try:
        choice = input("\nChoix patient (ou Entrée pour le premier): ").strip()
        if choice:
            idx = int(choice) - 1
            return patients[idx]
        else:
            return patients[0]
    except (ValueError, IndexError):
        print("   Utilisation du premier patient")
        return patients[0]

def main():
    """Run all advanced analyses"""
    
    print("="*60)
    print("🔬 ANALYSES AVANCÉES - Multi-patients")
    print("="*60)
    
    # Sélectionner patient
    patient_id = select_patient()
    
    if not patient_id:
        print("❌ Aucun patient sélectionné")
        return 1
    
    # Créer l'analyzer pour le patient
    analyzer = AdvancedPaperAnalysis(patient_id=patient_id)
    
    try:
        # Charger les données
        analyzer.load_data()
        
        # Générer les figures
        print("\n🎨 Génération des figures...")
        
        if len(analyzer.df_annot) > 0:
            analyzer.figure5_temporal_timeline()
            analyzer.figure6_connectivity_matrices()
            analyzer.figure7_spectral_analysis()
        else:
            print("⚠️ Pas d'annotations - figures 5,6,7 non générées")
        
        # Statistiques
        stats = analyzer.generate_statistics()
        
        print(f"\n✅ Analyses terminées pour patient {patient_id}!")
        print(f"📁 Figures dans: {analyzer.patient_figures_dir}")
        print(f"📁 Statistiques dans: {analyzer.patient_output_dir}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())