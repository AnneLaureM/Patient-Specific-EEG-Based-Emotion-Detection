#!/usr/bin/env python
# run_pipeline.py
# Complete pipeline runner for scientific paper

import os
import sys
import subprocess
import time
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib

from config import (
    DATA_DIR, OUTPUTS_DIR, MODELS_DIR, FIGURES_DIR,
    PATIENTS, EMOTION_COLORS, get_output_filename
)

class EEGPipeline:
    """Complete EEG analysis pipeline for scientific paper"""
    
    def __init__(self, patient_id="P001"):
        self.patient_id = patient_id
        self.patient_info = PATIENTS[patient_id]
        self.results = {}
        
    def run_acquisition(self, duration=300):
        """Step 1: Run EEG acquisition"""
        print("\n" + "="*60)
        print("STEP 1: EEG ACQUISITION")
        print("="*60)
        
        cmd = f"python 01_acquisition.py"
        print(f"Running: {cmd}")
        print(f"Duration: {duration} seconds")
        
        # Run in subprocess
        proc = subprocess.Popen(cmd.split())
        time.sleep(duration)
        proc.terminate()
        
        print("✓ Acquisition completed")
        
    def run_tagging(self):
        """Step 2: Launch tagging interface"""
        print("\n" + "="*60)
        print("STEP 2: EMOTION TAGGING")
        print("="*60)
        print("Launching Streamlit interface...")
        print("URL: http://localhost:8501")
        
        subprocess.Popen(["streamlit", "run", "02_tagging_app.py"])
        
    def run_som_pipeline(self):
        """Step 3: Run SOM analysis"""
        print("\n" + "="*60)
        print("STEP 3: SOM ANALYSIS")
        print("="*60)
        
        from 03_som_pipeline import main as som_main
        som_main()
        
        # Load results
        features_file = get_output_filename("som_features")
        clusters_file = get_output_filename("som_clusters")
        
        if os.path.exists(features_file):
            self.results['features'] = pd.read_csv(features_file)
        if os.path.exists(clusters_file):
            self.results['clusters'] = pd.read_csv(clusters_file)
            
    def run_model_training(self):
        """Step 4: Train patient-specific model"""
        print("\n" + "="*60)
        print("STEP 4: MODEL TRAINING")
        print("="*60)
        
        from 05_train_model import main as train_main
        train_main()
        
        # Load model metrics
        metrics_file = get_output_filename("model_metrics", "txt")
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r') as f:
                self.results['metrics'] = f.read()
                
    def generate_paper_figures(self):
        """Generate all figures for scientific paper"""
        print("\n" + "="*60)
        print("GENERATING PAPER FIGURES")
        print("="*60)
        
        from 06_analyze_results import generate_all_figures
        generate_all_figures(self.patient_id)
        
    def get_paper_metrics(self):
        """Compute all metrics for paper"""
        
        metrics = {
            'patient_id': self.patient_id,
            'age': self.patient_info['age'],
            'sex': self.patient_info['sexe'],
            'n_sessions': len([f for f in os.listdir(DATA_DIR) if f.startswith('eeg_')]),
            'total_duration': 0,
            'n_windows': 0,
            'n_annotations': 0,
            'model_accuracy': 0,
            'n_classes': 0
        }
        
        # Calculate total EEG duration
        for f in os.listdir(DATA_DIR):
            if f.startswith('eeg_'):
                df = pd.read_csv(os.path.join(DATA_DIR, f))
                metrics['total_duration'] += df['time_s'].max() - df['time_s'].min()
        
        # Get model performance
        if 'metrics' in self.results:
            import re
            acc_match = re.search(r'accuracy:?\s*([0-9.]+)', self.results['metrics'].lower())
            if acc_match:
                metrics['model_accuracy'] = float(acc_match.group(1))
        
        # Get SOM info
        if 'clusters' in self.results:
            metrics['n_windows'] = len(self.results['clusters'])
            metrics['n_clusters'] = self.results['clusters'][['bmu_x', 'bmu_y']].drop_duplicates().shape[0]
        
        return metrics

def main():
    """Main pipeline runner"""
    
    print("="*60)
    print("PATIENT-SPECIFIC EEG EMOTION DETECTION")
    print("Scientific Pipeline v2.0")
    print("="*60)
    
    # Create pipelines for each patient
    patients = ['P001', 'P002']
    all_metrics = []
    
    for patient_id in patients:
        print(f"\n\n{'#'*60}")
        print(f"PROCESSING PATIENT {patient_id}")
        print(f"Age: {PATIENTS[patient_id]['age']}, Sex: {PATIENTS[patient_id]['sexe']}")
        print('#'*60)
        
        pipeline = EEGPipeline(patient_id)
        
        # Run pipeline steps
        # pipeline.run_acquisition(duration=300)  # Uncomment for new acquisition
        pipeline.run_som_pipeline()
        pipeline.run_model_training()
        
        # Generate figures
        pipeline.generate_paper_figures()
        
        # Get metrics
        metrics = pipeline.get_paper_metrics()
        all_metrics.append(metrics)
        
        print(f"\n✓ Patient {patient_id} processed")
        print(f"   Windows: {metrics['n_windows']}")
        print(f"   Accuracy: {metrics['model_accuracy']:.2%}")
    
    # Generate summary table
    print("\n" + "="*60)
    print("SUMMARY TABLE FOR PAPER")
    print("="*60)
    
    summary_df = pd.DataFrame(all_metrics)
    print(summary_df.to_string(index=False))
    
    # Save to CSV
    summary_file = get_output_filename("paper_summary", "csv")
    summary_df.to_csv(summary_file, index=False)
    print(f"\n✓ Summary saved to {summary_file}")

if __name__ == "__main__":
    main()