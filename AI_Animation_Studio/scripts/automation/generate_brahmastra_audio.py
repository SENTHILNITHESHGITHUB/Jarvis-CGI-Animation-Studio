"""
================================================================================
🎬 BRAHMĀSTRA SOUND DESIGN ENGINE // PROCEDURAL CINEMA AUDIO SYNTHESIZER
================================================================================
Synthesizes Hollywood-grade sound design for the Brahmāstra Mesh MoCap Short:
1. 42Hz Seismic Sub-Bass Cosmic Rumble
2. 136.1Hz Sacred Sanskrit 'Om' Cosmic Harmonic Resonance (Aura Activation)
3. Swirling 3D Mandala Whoosh (Stereo Panned Frequency Modulated Sawtooth)
4. Agnyāstra Plasma Detonation & Thermal Energy Release (Pink Noise Burst)
================================================================================
"""

import os
import math
import numpy as np
from scipy.io import wavfile

def generate_brahmastra_soundtrack(output_path: str, duration: float = 2.0, sample_rate: int = 44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    num_samples = len(t)
    
    # 1. 42Hz Seismic Sub-Bass Drone with Low Riser
    sub_bass = np.sin(2 * np.pi * 42.0 * t) * 0.40
    # Gentle riser from 38Hz to 58Hz
    sub_bass += np.sin(2 * np.pi * (38.0 + 10.0 * (t / duration)**1.5) * t) * 0.35
    
    # 2. Sacred Cosmic Harmonic Drone (136.1Hz Om Fundamental + 272.2Hz + 408.3Hz)
    om_fund = np.sin(2 * np.pi * 136.1 * t) * 0.25
    om_harm2 = np.sin(2 * np.pi * 272.2 * t + 0.3) * 0.15
    om_harm3 = np.sin(2 * np.pi * 408.3 * t + 0.7) * 0.08
    om_aura = (om_fund + om_harm2 + om_harm3) * (0.4 + 0.6 * np.sin(2 * np.pi * 3.0 * t)**2)
    
    # 3. Rotating Mandala Plasma Whoosh (FM Chirp around 0.6s - 1.5s)
    mandala_whoosh_L = np.zeros(num_samples)
    mandala_whoosh_R = np.zeros(num_samples)
    
    start_whoosh = int(0.5 * sample_rate)
    end_whoosh = int(1.8 * sample_rate)
    w_t = np.linspace(0, 1.3, end_whoosh - start_whoosh, endpoint=False)
    
    # Sweeping frequency 350Hz -> 1100Hz with centrifugal mod
    chirp_freq = 350.0 + 750.0 * (w_t / 1.3)**2 + 80.0 * np.sin(2 * np.pi * 14.0 * w_t)
    phase = 2 * np.pi * np.cumsum(chirp_freq) / sample_rate
    chirp = np.sin(phase) * np.sin(np.pi * (w_t / 1.3)) * 0.35
    
    # Stereo panning for 3D rotation
    mandala_whoosh_L[start_whoosh:end_whoosh] = chirp * (0.5 + 0.5 * np.cos(2 * np.pi * 5.0 * w_t))
    mandala_whoosh_R[start_whoosh:end_whoosh] = chirp * (0.5 + 0.5 * np.sin(2 * np.pi * 5.0 * w_t))
    
    # 4. Agnyāstra Detonation Burst at 1.2s
    detonation_L = np.zeros(num_samples)
    detonation_R = np.zeros(num_samples)
    
    det_start = int(1.15 * sample_rate)
    det_len = num_samples - det_start
    if det_len > 0:
        det_t = np.linspace(0, (num_samples - det_start) / sample_rate, det_len, endpoint=False)
        decay = np.exp(-4.5 * det_t)
        # Noise burst filtered
        noise = np.random.normal(0, 1, det_len)
        # Low frequency impact thump (65Hz -> 30Hz exponential pitch drop)
        thump_pitch = 65.0 * np.exp(-6.0 * det_t)
        thump_phase = 2 * np.pi * np.cumsum(thump_pitch) / sample_rate
        thump = np.sin(thump_phase) * decay * 0.75
        
        # Fire crackle (bandpass simulation via modulated noise)
        crackle = noise * decay * 0.30
        
        detonation_L[det_start:] = thump + crackle
        detonation_R[det_start:] = thump + crackle * 0.95
        
    # Combine tracks
    channel_L = sub_bass + om_aura + mandala_whoosh_L + detonation_L
    channel_R = sub_bass + om_aura + mandala_whoosh_R + detonation_R
    
    # Master Normalization & Soft Limiter
    max_amp = max(np.max(np.abs(channel_L)), np.max(np.abs(channel_R)))
    if max_amp > 0:
        channel_L = (channel_L / max_amp) * 0.92
        channel_R = (channel_R / max_amp) * 0.92
        
    stereo = np.column_stack((channel_L, channel_R))
    audio_int16 = (stereo * 32767.0).astype(np.int16)
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    wavfile.write(output_path, sample_rate, audio_int16)
    print(f"[AUDIO ENGINE] Brahmastra Sound Design successfully generated -> {output_path}")

if __name__ == "__main__":
    out_file = r"C:\Users\SVNITHESHPC\Downloads\AI_Animation_Studio\renders\previews\brahmastra_cinema_soundtrack.wav"
    generate_brahmastra_soundtrack(out_file, duration=2.0)
