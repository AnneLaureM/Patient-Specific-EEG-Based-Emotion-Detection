# config.py
# Configuration centralisée pour tout le projet

import os
import json
from datetime import datetime

# Chemins de base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PATIENTS_DIR = os.path.join(DATA_DIR, "patients")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
MODELS_DIR = os.path.join(BASE_DIR, "models")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")

# Créer les dossiers
for d in [DATA_DIR, PATIENTS_DIR, OUTPUTS_DIR, MODELS_DIR, FIGURES_DIR]:
    os.makedirs(d, exist_ok=True)

# Fichier de session courante
CURRENT_SESSION_FILE = os.path.join(DATA_DIR, ".current_session.json")

# Paramètres d'acquisition
WINDOW_SEC = 4.0
STEP_SEC = 1.0
FS = 256  # Hz

# Paramètres SOM
SOM_X = 10
SOM_Y = 10
SOM_ITERS = 1000

# Mapping des régions cérébrales
REGIONS = {
    "Frontal_L": ["ch1", "ch3"],
    "Frontal_R": ["ch2", "ch4"],
    "Parietal_L": ["ch5", "ch7"],
    "Parietal_R": ["ch6", "ch8"],
}

# Mapping des émotions
EMOTION_COLORS = {
    "peur": "#FF4444",
    "joie": "#44FF44",
    "serenite": "#4444FF",
    "colere": "#FF8844",
    "excitation": "#FF44FF",
    "douleur": "#884444",
    "faim": "#44FF88",
    "soif": "#44AAFF",
    "envie": "#FFAA44",
    "fatigue": "#AA44FF",
    "parle": "#FFAA88",
    "neutre": "#AAAAAA"
}

# ============================================================
# INFORMATIONS PATIENTS (pour les figures et analyses)
# ============================================================
PATIENTS = {
    "P001": {
        "age": 42, 
        "sexe": "F", 
        "condition": "patient",
        "notes": "Premier patient, session resting_state"
    },
    "P002": {
        "age": 45, 
        "sexe": "F", 
        "condition": "patient",
        "notes": "Deuxième patient"
    },
    # Ajoutez d'autres patients selon vos besoins
    # "P003": {
    #     "age": 38,
    #     "sexe": "M",
    #     "condition": "contrôle",
    #     "notes": "Groupe contrôle"
    # },
}

def get_patient_info(patient_id):
    """
    Retourne les informations démographiques d'un patient
    
    Args:
        patient_id (str): Identifiant du patient (ex: "P001")
    
    Returns:
        dict: Informations du patient avec valeurs par défaut si non trouvé
    """
    default_info = {
        "age": "inconnu",
        "sexe": "inconnu", 
        "condition": "inconnu",
        "notes": ""
    }
    
    if patient_id in PATIENTS:
        info = PATIENTS[patient_id].copy()
        # Compléter avec les clés par défaut manquantes
        for key in default_info:
            if key not in info:
                info[key] = default_info[key]
        return info
    else:
        print(f"⚠️ Patient {patient_id} non trouvé dans la configuration")
        return default_info

def add_patient_info(patient_id, age=None, sexe=None, condition=None, notes=""):
    """
    Ajoute ou met à jour les informations d'un patient
    """
    if patient_id not in PATIENTS:
        PATIENTS[patient_id] = {}
    
    if age is not None:
        PATIENTS[patient_id]["age"] = age
    if sexe is not None:
        PATIENTS[patient_id]["sexe"] = sexe
    if condition is not None:
        PATIENTS[patient_id]["condition"] = condition
    if notes:
        PATIENTS[patient_id]["notes"] = notes
    
    # Sauvegarder dans un fichier JSON optionnel
    save_patients_config()
    
    return PATIENTS[patient_id]

def save_patients_config():
    """
    Sauvegarde la configuration des patients dans un fichier JSON
    """
    config_file = os.path.join(BASE_DIR, "patients_config.json")
    try:
        with open(config_file, 'w') as f:
            json.dump(PATIENTS, f, indent=2)
    except Exception as e:
        print(f"⚠️ Impossible de sauvegarder la config patients: {e}")

def load_patients_config():
    """
    Charge la configuration des patients depuis le fichier JSON
    """
    global PATIENTS
    config_file = os.path.join(BASE_DIR, "patients_config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                loaded = json.load(f)
                PATIENTS.update(loaded)
        except Exception as e:
            print(f"⚠️ Impossible de charger la config patients: {e}")

# Charger automatiquement la config au démarrage
load_patients_config()

# ============================================================
# FONCTIONS DE GESTION DES PATIENTS
# ============================================================

def get_patient_dir(patient_id):
    """Retourne le dossier d'un patient"""
    patient_dir = os.path.join(PATIENTS_DIR, f"patient_{patient_id}")
    os.makedirs(patient_dir, exist_ok=True)
    return patient_dir

def get_session_filename(patient_id, session_type="eeg", description=""):
    """
    Génère un nom de fichier pour une session patient
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    patient_dir = get_patient_dir(patient_id)
    
    if description:
        description = f"_{description}"
    
    filename = f"{session_type}{description}_{timestamp}.csv"
    return os.path.join(patient_dir, filename)

def get_annotations_file(patient_id):
    """Retourne le fichier d'annotations d'un patient"""
    patient_dir = get_patient_dir(patient_id)
    return os.path.join(patient_dir, "annotations.csv")

def get_patient_sessions(patient_id):
    """Liste toutes les sessions d'un patient"""
    patient_dir = get_patient_dir(patient_id)
    sessions = []
    
    if os.path.exists(patient_dir):
        for f in os.listdir(patient_dir):
            if f.startswith('eeg_') and f.endswith('.csv') and f != 'annotations.csv':
                sessions.append({
                    'file': os.path.join(patient_dir, f),
                    'filename': f,
                    'timestamp': f.replace('eeg_', '').replace('.csv', ''),
                    'path': os.path.join(patient_dir, f)
                })
    
    # Trier par date (plus récent d'abord)
    sessions.sort(key=lambda x: x['timestamp'], reverse=True)
    return sessions

def list_all_patients():
    """Liste tous les patients"""
    patients = []
    if os.path.exists(PATIENTS_DIR):
        for item in os.listdir(PATIENTS_DIR):
            if item.startswith('patient_'):
                patient_id = item.replace('patient_', '')
                patients.append(patient_id)
    return sorted(patients)

def set_current_session(eeg_file, patient_id, description=""):
    """
    Enregistre la session en cours
    """
    session_info = {
        "eeg_file": eeg_file,
        "patient_id": patient_id,
        "description": description,
        "timestamp": datetime.now().isoformat(),
        "eeg_filename": os.path.basename(eeg_file)
    }
    with open(CURRENT_SESSION_FILE, 'w') as f:
        json.dump(session_info, f, indent=2)
    return session_info

def get_current_session():
    """
    Récupère les informations de la session en cours
    """
    if os.path.exists(CURRENT_SESSION_FILE):
        with open(CURRENT_SESSION_FILE, 'r') as f:
            return json.load(f)
    return None

def get_patient_output_dir(patient_id):
    """Retourne le dossier de sortie pour un patient"""
    output_dir = os.path.join(OUTPUTS_DIR, f"patient_{patient_id}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def get_patient_model_dir(patient_id):
    """Retourne le dossier de modèles pour un patient"""
    model_dir = os.path.join(MODELS_DIR, f"patient_{patient_id}")
    os.makedirs(model_dir, exist_ok=True)
    return model_dir

def get_patient_figures_dir(patient_id):
    """Retourne le dossier de figures pour un patient"""
    figures_dir = os.path.join(FIGURES_DIR, f"patient_{patient_id}")
    os.makedirs(figures_dir, exist_ok=True)
    return figures_dir

def get_output_filename(prefix, suffix="csv"):
    """Génère un nom de fichier de sortie (pour compatibilité)"""
    return os.path.join(OUTPUTS_DIR, f"{prefix}.{suffix}")