#!/usr/bin/env python
# 01_acquisition.py
# Acquisition EEG avec gestion multi-patients et compatibilité

"""
EEG Acquisition Script for Bitbrain Air Headset
Multi-patient support with session tracking
"""

import ctypes
from ctypes import c_int, c_ushort, c_short, c_char_p, c_double, POINTER, byref, Structure, CDLL
import subprocess
import os
import time
import csv
import numpy as np
import sys
from datetime import datetime

# Import local modules
from eeg_utils import (
    bandpass_filter, quick_qc, compute_band_powers,
    emotion_indices
)
from config import (
    DATA_DIR, REGIONS, WINDOW_SEC, STEP_SEC, FS,
    get_session_filename, get_annotations_file, set_current_session,
    list_all_patients
)
from file_utils import migrate_legacy_files

# SDK paths
SDK_BASE = "/home/anne/Nextcloud/Documents/Projets/Patient-Specific-EEG-Based-Emotion-Detection/bbt-sdk_2.8.6-ubuntu-22.04/sdk_linux_2.8.6/sdk/2.8.6"
SDK_LIB_DIR = os.path.join(SDK_BASE, "lib")
SDK_BIN_DIR = os.path.join(SDK_BASE, "bin")
DEVICE_NAME = "BBT-E08-AAB063"

# Configure library path
os.environ['LD_LIBRARY_PATH'] = f"{SDK_LIB_DIR}:{SDK_BIN_DIR}:" + os.environ.get('LD_LIBRARY_PATH', '')

# Load SDK
lib_path = os.path.join(SDK_LIB_DIR, "libsdk-2.8.6.so.2.8.6")
print(f"[1/8] Loading SDK from {lib_path}...")
sdk = CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
print("✓ SDK loaded successfully")

# C types structures
class bbt_device_t(ctypes.Structure):
    """Opaque device type"""
    pass

class bbt_device_signal_t(Structure):
    _fields_ = [
        ("type", c_int),
        ("channels", c_ushort),
        ("samples_in_block", c_ushort),
        ("sampling_rate", c_ushort),
    ]

class bbt_device_data_block_t(Structure):
    _fields_ = [
        ("sequence", c_ushort),
        ("battery", c_short),
        ("flags", c_ushort),
        ("signal_data", POINTER(c_double) * 10),
        ("impedances", POINTER(c_ushort)),
    ]

# Constants
BBT_SIGNAL_TYPE_EEG = 6
IMPEDANCE_QUALITY = {0: "Unknown", 1: "Saturated", 2: "Bad", 3: "Fair", 4: "Good"}

# Configure SDK functions
def setup_func(name, argtypes, restype):
    try:
        func = getattr(sdk, name)
        func.argtypes = argtypes
        func.restype = restype
        return func
    except AttributeError:
        print(f"⚠ Function {name} not found")
        return None

print("[2/8] Configuring SDK functions...")
bbt_device_new_air = setup_func("bbt_device_new_air", [c_char_p], POINTER(bbt_device_t))
bbt_device_connect = setup_func("bbt_device_connect", [POINTER(bbt_device_t)], c_int)
bbt_device_get_signals = setup_func("bbt_device_get_signals", 
    [POINTER(bbt_device_t), POINTER(c_ushort), POINTER(POINTER(bbt_device_signal_t))], c_int)
bbt_device_enable_signal = setup_func("bbt_device_enable_signal", [POINTER(bbt_device_t), c_ushort], c_int)
bbt_device_start = setup_func("bbt_device_start", [POINTER(bbt_device_t)], c_int)
bbt_device_read = setup_func("bbt_device_read", [POINTER(bbt_device_t), POINTER(bbt_device_data_block_t)], c_int)
bbt_device_stop = setup_func("bbt_device_stop", [POINTER(bbt_device_t)], c_int)
bbt_device_disconnect = setup_func("bbt_device_disconnect", [POINTER(bbt_device_t)], c_int)
bbt_device_free = setup_func("bbt_device_free", [POINTER(bbt_device_t)], None)

def select_patient():
    """Sélectionne ou crée un patient"""
    print("\n📋 GESTION DES PATIENTS")
    print("-" * 40)
    
    # Proposer migration des anciens fichiers
    migrate = input("Voulez-vous migrer les anciens fichiers? (o/N): ").lower()
    if migrate == 'o':
        migrate_legacy_files()
    
    patients = list_all_patients()
    
    if patients:
        print("Patients existants:")
        for i, p in enumerate(patients, 1):
            print(f"  {i}. {p}")
        print(f"  {len(patients)+1}. Nouveau patient")
        
        try:
            choice = int(input("\nChoix: "))
            if 1 <= choice <= len(patients):
                return patients[choice-1]
        except ValueError:
            pass
    
    # Nouveau patient
    patient_id = input("ID du nouveau patient (ex: P001): ").strip()
    if not patient_id:
        patient_id = f"P{len(patients)+1:03d}"
    return patient_id

def main():
    """Main acquisition function"""
    
    print("=" * 60)
    print("EEG ACQUISITION - Bitbrain Air")
    print("=" * 60)
    
    # Sélection du patient
    patient_id = select_patient()
    print(f"\nPatient sélectionné: {patient_id}")
    
    # Description de la session
    print("\nTypes de session:")
    print("  - resting_state (repos)")
    print("  - stimulation (stimulation)")
    print("  - task (tâche)")
    print("  - other (autre)")
    session_desc = input("Description de la session: ") or "resting_state"
    
    # Créer le fichier de sortie
    output_file = get_session_filename(patient_id, "eeg", session_desc)
    print(f"\n[3/8] Fichier de sortie: {output_file}")
    
    # Enregistrer la session courante
    set_current_session(output_file, patient_id, session_desc)
    
    # Start connection servers
    print("[4/8] Démarrage des serveurs Bitbrain...")
    try:
        bth_proc = subprocess.Popen([os.path.join(SDK_BIN_DIR, "bthserver")], cwd=SDK_BIN_DIR)
        conn_proc = subprocess.Popen([os.path.join(SDK_BIN_DIR, "bbt-connection-server")], cwd=SDK_BIN_DIR)
        time.sleep(3)
    except Exception as e:
        print(f"⚠ Erreur serveurs: {e}")
        print("Assurez-vous que les binaires sont exécutables")
        return 1
    
    device = None
    saved_rows = [["time_s"] + [f"ch{i}" for i in range(1, 9)]]
    
    try:
        # Create device
        print(f"[5/8] Création du device {DEVICE_NAME}...")
        device = bbt_device_new_air(DEVICE_NAME.encode())
        if not device:
            raise RuntimeError("Échec création device")
        print("✓ Device créé")
        
        # Connect
        print("[6/8] Connexion au casque...")
        if bbt_device_connect(device) != 1:
            raise RuntimeError("Échec connexion")
        print("✓ Connecté au casque")
        
        # Get signal information
        n_signals = c_ushort()
        signals_ptr = POINTER(bbt_device_signal_t)()
        bbt_device_get_signals(device, byref(n_signals), byref(signals_ptr))
        
        # Find EEG signal
        eeg_index = None
        for i in range(n_signals.value):
            if signals_ptr[i].type == BBT_SIGNAL_TYPE_EEG:
                eeg_index = i
                eeg_info = signals_ptr[i]
                break
        
        if eeg_index is None:
            raise RuntimeError("Signal EEG non trouvé")
        
        print(f"\n✓ Signal EEG trouvé:")
        print(f"  - Canaux: {eeg_info.channels}")
        print(f"  - Échantillons/bloc: {eeg_info.samples_in_block}")
        print(f"  - Fréquence: {eeg_info.sampling_rate} Hz")
        
        # Enable EEG
        bbt_device_enable_signal(device, eeg_index)
        print("\n[7/8] Démarrage acquisition...")
        bbt_device_start(device)
        
        # Acquisition loop
        print("\n[8/8] Acquisition en cours (Ctrl+C pour arrêter)")
        print("-" * 60)
        
        fs = eeg_info.sampling_rate
        win_samples = int(WINDOW_SEC * fs)
        buffer = np.zeros((win_samples, eeg_info.channels))
        buffer_filled = 0
        last_analysis = time.time()
        sample_count = 0
        block = bbt_device_data_block_t()
        
        while True:
            # Read data block
            if bbt_device_read(device, byref(block)) != 1:
                time.sleep(0.001)
                continue
            
            # Get EEG data
            eeg_ptr = block.signal_data[eeg_index]
            if not eeg_ptr:
                continue
            
            # Convert to numpy
            total = eeg_info.channels * eeg_info.samples_in_block
            data = np.array([eeg_ptr[i] for i in range(total)], dtype=np.float64)
            data = data.reshape((eeg_info.samples_in_block, eeg_info.channels))
            
            # Save raw data
            for s in range(eeg_info.samples_in_block):
                t = sample_count / fs
                saved_rows.append([t] + list(data[s, :]))
                sample_count += 1
            
            # Update circular buffer
            for s in range(eeg_info.samples_in_block):
                buffer[buffer_filled % win_samples, :] = data[s, :]
                buffer_filled += 1
            
            # Periodic analysis
            now = time.time()
            if now - last_analysis >= STEP_SEC and buffer_filled >= win_samples:
                last_analysis = now
                
                # Extract window
                idx_end = buffer_filled
                idx_start = buffer_filled - win_samples
                idxs = np.arange(idx_start, idx_end) % win_samples
                window = buffer[idxs, :]
                
                # Display info
                print(f"\n--- Fenêtre t={sample_count/fs:.1f}s ---")
                print(f"Séquence: {block.sequence}")
                print(f"Batterie: {block.battery}/5")
                
                # Show impedances
                if block.impedances:
                    imp = [block.impedances[i] for i in range(eeg_info.channels)]
                    imp_str = [f"{IMPEDANCE_QUALITY.get(i, str(i))}" for i in imp]
                    print(f"Impédances: {imp_str}")
                
                # Quick analysis
                data_filt = bandpass_filter(window, fs, 1., 40.)
                qc = quick_qc(data_filt, [f"ch{i}" for i in range(1, 9)])
                
                if len(qc["good_idx"]) > 0:
                    data_good = data_filt[:, qc["good_idx"]]
                    bp = compute_band_powers(data_good, fs)
                    emo = emotion_indices(bp)
                    if emo:
                        print(f"Arousal: {emo['arousal']:.3f}")
                        print(f"Relaxation: {emo['relaxation']:.3f}")
    
    except KeyboardInterrupt:
        print("\n\n⚠ Acquisition arrêtée par l'utilisateur")
    
    finally:
        # Save data
        if len(saved_rows) > 1:
            print(f"\nSauvegarde de {len(saved_rows)-1} échantillons...")
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(saved_rows)
            print(f"✓ Données sauvegardées: {output_file}")
        
        # Cleanup
        if device:
            print("Arrêt acquisition...")
            bbt_device_stop(device)
            bbt_device_disconnect(device)
            bbt_device_free(device)
        
        # Stop servers
        try:
            bth_proc.terminate()
            conn_proc.terminate()
        except:
            pass
        print("✓ Session terminée")
        
        # Afficher le chemin pour l'annotation
        print(f"\n📝 Pour annoter: streamlit run 02_tagging_app.py")
        print(f"   Patient: {patient_id}")

if __name__ == "__main__":
    sys.exit(main())