"""
AI Animation Studio - Sound Design & Anime Soundtrack Generator
---------------------------------------------------------------
Synthesizes custom studio sound design:
- Pentatonic anime celesta & bell theme
- High-speed propeller / rotor whirring harmonics for Take-copter
- Cheerful cartoon sparkle and bass warmth
Output: 44.1kHz Stereo 16-bit PCM WAV
"""

import numpy as np
import scipy.io.wavfile as wav
from pathlib import Path

def generate_soundtrack(output_wav, duration_sec=3.0, sample_rate=44100):
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    
    # 1. Take-copter Rotor Whirring (Fluttering acoustic propeller harmonics)
    rotor_base_freq = 42.0  # 42 Hz motor hum
    flutter = np.sin(2 * np.pi * 14.0 * t) # 14 Hz blade pass
    rotor_sound = 0.25 * np.sin(2 * np.pi * rotor_base_freq * t + 0.3 * flutter)
    rotor_sound += 0.15 * np.sin(2 * np.pi * (rotor_base_freq * 2.5) * t)
    # Wind turbulence
    noise = np.random.normal(0, 0.05, len(t))
    # Filter noise smoothly
    rotor_wind = np.convolve(noise, np.ones(20)/20, mode='same') * 0.15
    rotor_track = (rotor_sound + rotor_wind) * np.linspace(0.4, 1.0, len(t))

    # 2. Pentatonic Anime Melody (Whimsical celesta & bell notes)
    # Japanese pentatonic / happy cartoon progression: C5, E5, G5, A5, C6
    melody_notes = [
        (0.0, 0.6, 523.25),   # C5 (Hello!)
        (0.5, 0.6, 659.25),   # E5
        (1.0, 0.7, 783.99),   # G5 (Waving cheerful)
        (1.6, 0.8, 880.00),   # A5
        (2.2, 1.0, 1046.50),  # C6 (High sparkle finish)
    ]
    
    celesta_track = np.zeros_like(t)
    for start, dur, freq in melody_notes:
        note_mask = (t >= start) & (t < start + dur)
        t_note = t[note_mask] - start
        envelope = np.exp(-3.5 * t_note) # Pluck decay
        # Bell harmonics
        tone = (
            np.sin(2 * np.pi * freq * t_note) +
            0.45 * np.sin(2 * np.pi * freq * 2 * t_note) +
            0.20 * np.sin(2 * np.pi * freq * 3.01 * t_note) +
            0.10 * np.sin(2 * np.pi * freq * 4.2 * t_note)
        )
        celesta_track[note_mask] += tone * envelope * 0.40

    # 3. Cartoon Sparkle Shimmer (High frequency glitter chords)
    sparkle_track = np.zeros_like(t)
    sparkle_times = [0.2, 1.1, 2.1]
    for st in sparkle_times:
        mask = (t >= st) & (t < st + 0.5)
        t_sp = t[mask] - st
        env = np.exp(-6.0 * t_sp)
        sparkle = np.sin(2 * np.pi * 2093.0 * t_sp) + np.sin(2 * np.pi * 2637.0 * t_sp)
        sparkle_track[mask] += sparkle * env * 0.18

    # 4. Master Mix & Soft Limiter
    mix = (celesta_track * 0.55) + (rotor_track * 0.28) + (sparkle_track * 0.20)
    
    # Master Fade In/Out
    fade_len = min(int(sample_rate * 0.15), max(1, len(t) // 6))
    if fade_len > 0:
        fade_in = np.linspace(0, 1.0, fade_len)
        fade_out = np.linspace(1.0, 0, fade_len)
        mix[:fade_len] *= fade_in
        mix[-fade_len:] *= fade_out

    # Normalize to -1.0 dB
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = (mix / peak) * 0.89

    # Stereo widening
    left_channel = mix
    right_channel = np.roll(mix, int(sample_rate * 0.003)) # 3ms Haas effect

    stereo_pcm = np.stack([left_channel, right_channel], axis=-1)
    stereo_int16 = (stereo_pcm * 32767).astype(np.int16)

    Path(output_wav).parent.mkdir(parents=True, exist_ok=True)
    wav.write(output_wav, sample_rate, stereo_int16)
    print(f"[AUDIO READY] Synthesized {duration_sec}s audio to {output_wav}")

if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\SVNITHESHPC\Downloads\AI_Animation_Studio\renders\final\anime_soundtrack.wav"
    generate_soundtrack(out)
