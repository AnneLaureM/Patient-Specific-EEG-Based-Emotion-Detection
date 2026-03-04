# eeg_utils.py
# EEG signal processing utilities

import numpy as np
import pandas as pd
from scipy.signal import welch, butter, filtfilt
from scipy.integrate import trapezoid
import itertools

# Default channel names (8 channels for Bitbrain Air)
DEFAULT_CHANNEL_NAMES = [f"ch{i}" for i in range(1, 9)]

# Frequency bands
BANDS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
}

def load_eeg(csv_path, channel_names=None):
    """
    Load EEG data from CSV file
    
    Parameters:
    -----------
    csv_path : str
        Path to CSV file
    channel_names : list
        List of channel column names
    
    Returns:
    --------
    time : array
        Time vector
    data : array
        EEG data (samples × channels)
    fs : float
        Sampling frequency
    ch_names : list
        Channel names
    """
    if channel_names is None:
        channel_names = DEFAULT_CHANNEL_NAMES
    
    df = pd.read_csv(csv_path)
    
    # Check required columns
    if "time_s" not in df.columns:
        raise ValueError("CSV must contain 'time_s' column")
    
    # Get time and data
    time = df["time_s"].values
    data = df[channel_names].values
    
    # Estimate sampling frequency
    dt = np.median(np.diff(time))
    fs = 1.0 / dt
    
    return time, data, fs, channel_names

def butter_bandpass(lowcut, highcut, fs, order=4):
    """Create Butterworth bandpass filter"""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype="band")
    return b, a

def bandpass_filter(data, fs, lowcut=1., highcut=40.):
    """
    Apply bandpass filter to EEG data
    
    Parameters:
    -----------
    data : array
        EEG data (samples × channels)
    fs : float
        Sampling frequency
    lowcut, highcut : float
        Filter cutoff frequencies
    
    Returns:
    --------
    filtered : array
        Filtered data
    """
    b, a = butter_bandpass(lowcut, highcut, fs)
    return filtfilt(b, a, data, axis=0)

def quick_qc(data, channel_names=None, low_var_threshold=1e-3):
    """
    Quick quality control of EEG channels
    
    Parameters:
    -----------
    data : array
        EEG data (samples × channels)
    channel_names : list
        Channel names
    low_var_threshold : float
        Variance threshold for bad channels
    
    Returns:
    --------
    dict : Quality metrics
    """
    if channel_names is None:
        channel_names = DEFAULT_CHANNEL_NAMES[:data.shape[1]]
    
    mean = data.mean(axis=0)
    var = data.var(axis=0)
    minv = data.min(axis=0)
    maxv = data.max(axis=0)
    
    # Find bad channels (low variance)
    bad_idx = [i for i, v in enumerate(var) if v < low_var_threshold]
    good_idx = [i for i in range(data.shape[1]) if i not in bad_idx]
    
    return {
        "mean": mean,
        "var": var,
        "min": minv,
        "max": maxv,
        "good_idx": good_idx,
        "bad_idx": bad_idx,
    }

def bandpower_welch(data, fs, band, nperseg=256):
    """
    Compute band power using Welch's method
    
    Parameters:
    -----------
    data : array
        EEG data (samples × channels)
    fs : float
        Sampling frequency
    band : tuple
        (fmin, fmax)
    nperseg : int
        Segment length for Welch
    
    Returns:
    --------
    bp : array
        Band power per channel
    """
    fmin, fmax = band
    bp = []
    
    for ch in range(data.shape[1]):
        f, Pxx = welch(data[:, ch], fs=fs, nperseg=nperseg)
        idx = (f >= fmin) & (f <= fmax)
        bp_ch = trapezoid(Pxx[idx], f[idx])
        bp.append(bp_ch)
    
    return np.array(bp)

def compute_band_powers(data, fs, bands=None):
    """
    Compute power in all frequency bands
    
    Parameters:
    -----------
    data : array
        EEG data (samples × channels)
    fs : float
        Sampling frequency
    bands : dict
        Dictionary of band names and frequency ranges
    
    Returns:
    --------
    dict : Band powers per channel
    """
    if bands is None:
        bands = BANDS
    
    return {
        name: bandpower_welch(data, fs, band)
        for name, band in bands.items()
    }

def zscore_per_channel(data):
    """Z-score normalize each channel"""
    mean = data.mean(axis=0, keepdims=True)
    std = data.std(axis=0, keepdims=True) + 1e-9
    return (data - mean) / std

def emotion_indices(band_powers, good_idx=None):
    """
    Compute emotion indices from band powers
    
    Parameters:
    -----------
    band_powers : dict
        Dictionary of band powers
    good_idx : list
        Indices of good channels
    
    Returns:
    --------
    dict : Arousal and relaxation indices
    """
    alpha = band_powers.get("alpha")
    beta = band_powers.get("beta")
    theta = band_powers.get("theta")
    
    if alpha is None or beta is None or theta is None:
        return None
    
    if good_idx is None:
        good_idx = np.arange(len(alpha))
    
    a = alpha[good_idx]
    b = beta[good_idx]
    t = theta[good_idx]
    
    arousal = np.mean(b / (a + t + 1e-9))
    relaxation = np.mean(a / (b + 1e-9))
    
    return {
        "arousal": float(arousal),
        "relaxation": float(relaxation)
    }

def compute_alpha_asymmetry_regions(data, fs, ch_names, left_region, right_region, regions):
    """
    Compute frontal alpha asymmetry between regions
    
    Parameters:
    -----------
    data : array
        EEG data
    fs : float
        Sampling frequency
    ch_names : list
        Channel names
    left_region, right_region : str
        Region names
    regions : dict
        Mapping of region names to channel lists
    
    Returns:
    --------
    dict : Alpha asymmetry metrics
    """
    bp = compute_band_powers(data, fs)
    alpha = bp["alpha"]
    
    # Get channels for each region
    left_channels = regions.get(left_region, [])
    right_channels = regions.get(right_region, [])
    
    # Find indices
    left_idx = [ch_names.index(ch) for ch in left_channels if ch in ch_names]
    right_idx = [ch_names.index(ch) for ch in right_channels if ch in ch_names]
    
    if not left_idx or not right_idx:
        return None
    
    # Average alpha power per region
    alpha_left = np.mean(alpha[left_idx])
    alpha_right = np.mean(alpha[right_idx])
    
    # Compute asymmetry
    faa = np.log(alpha_right + 1e-12) - np.log(alpha_left + 1e-12)
    
    return {
        "alpha_left": float(alpha_left),
        "alpha_right": float(alpha_right),
        "FAA": float(faa),
    }

def compute_connectivity_corr(data, ch_names):
    """
    Compute correlation-based connectivity
    
    Parameters:
    -----------
    data : array
        EEG data
    ch_names : list
        Channel names
    
    Returns:
    --------
    corr_mat : array
        Correlation matrix
    edges : list
        List of (ch_i, ch_j, correlation)
    """
    corr_mat = np.corrcoef(data.T)
    
    edges = []
    for i, j in itertools.combinations(range(len(ch_names)), 2):
        edges.append((ch_names[i], ch_names[j], float(corr_mat[i, j])))
    
    return corr_mat, edges