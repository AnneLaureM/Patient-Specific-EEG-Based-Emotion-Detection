#!/usr/bin/env python
# copy_figures_to_paper.py - Version corrigée

import os
import shutil
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
FIGURES_SRC = BASE_DIR / "figures"
PAPER_FIGURES_DST = BASE_DIR / "paper" / "figures"

# Create destination
PAPER_FIGURES_DST.mkdir(exist_ok=True, parents=True)

# Check if source exists
if not FIGURES_SRC.exists():
    print(f"⚠️ Source figures directory not found: {FIGURES_SRC}")
    print("Creating empty directory...")
    FIGURES_SRC.mkdir(exist_ok=True)

# Mapping of generated figures to paper figures
figure_mapping = {
    "som_visualization.png": "figure2_som_patient.png",
    "figure3_confusion_P001.png": "figure3_confusion.png",
    "figure4_features_P001.png": "figure4_features.png",
    "figure5_timeline.png": "figure5_timeline.png",
    "figure6_connectivity.png": "figure6_connectivity.png",
    "figure7_spectral.png": "figure7_spectral.png",
}

# Copy and rename
copied = 0
for src_name, dst_name in figure_mapping.items():
    src = FIGURES_SRC / src_name
    dst = PAPER_FIGURES_DST / dst_name
    
    if src.exists():
        shutil.copy2(src, dst)
        print(f"✅ Copied {src_name} -> {dst_name}")
        copied += 1
    else:
        # Try alternative naming
        alt_name = src_name.replace("_P001", "")
        src_alt = FIGURES_SRC / alt_name
        if src_alt.exists():
            shutil.copy2(src_alt, dst)
            print(f"✅ Copied {alt_name} -> {dst_name}")
            copied += 1
        else:
            print(f"⚠️ Source not found: {src_name} or {alt_name}")

print(f"\n📁 Copied {copied} figures to: {PAPER_FIGURES_DST}")