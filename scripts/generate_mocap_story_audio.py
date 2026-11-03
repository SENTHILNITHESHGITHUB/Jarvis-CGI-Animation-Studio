import os
import sys
import asyncio
import edge_tts
import wave
import subprocess
import numpy as np

OUTPUT_DIR = r"C:\Users\SVNITHESHPC\Desktop\Jarvis_Studios"
FFMPEG = r"C:\Users\SVNITHESHPC\Downloads\Jarvis\venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
TOTAL_DURATION = 26.0
SAMPLE_RATE = 44100

MOCAP_STORY_BEATS = [
    {
        "id": "mocap_beat_1",
        "text": "Deep beneath the mountains, an ancient celestial warrior awakens from three thousand years of stasis.",
        "start": 0.4,
        "end": 5.8
    },
    {
        "id": "mocap_beat_2",
        "text": "As the Agnyastra containment shatters, the armor locks into full combat overdrive!",
        "start": 6.0,
        "end": 11.5
    },
    {
        "id": "mocap_beat_3",
        "text": "Channeling pure cosmic kinetic energy... watch the output reach maximum power!",
        "start": 11.8,
        "end": 17.2
    },
    {
        "id": "mocap_beat_4",
        "text": "Blasting into the upper atmosphere! Subscribe now for Episode 2: The Cosmic Clash!",
        "start": 20.6,
        "end": 26.0
    }
]

VOICE = "en-US-ChristopherNeural"
RATE = "+2%"
PITCH = "-2Hz"

async def synth_beat(text: str, out_path: str):
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(out_path)
    print(f"[+] Saved VO beat: {out_path}")

def synthesize_all_vo():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for b in MOCAP_STORY_BEATS:
        p = os.path.join(OUTPUT_DIR, f"{b['id']}.mp3")
        loop.run_until_complete(synth_beat(b["text"], p))
    loop.close()

def create_mocap_sfx():
    t = np.linspace(0, TOTAL_DURATION, int(SAMPLE_RATE * TOTAL_DURATION), endpoint=False)
    
    # 1. Atmospheric Cavern Drone (45Hz + 2.5Hz throbbing pulse)
    drone = 0.22 * np.sin(2 * np.pi * 45 * t) * (1.0 + 0.3 * np.sin(2 * np.pi * 2.5 * t))
    
    # 2. Footsteps & Servos during Walk (0.5s to 5.5s)
    servos = np.zeros_like(t)
    for walk_t in np.arange(0.8, 5.5, 0.75):
        m = (t >= walk_t) & (t < walk_t + 0.12)
        dt_s = t[m] - walk_t
        servos[m] += 0.25 * np.sin(2 * np.pi * 180 * dt_s) * np.exp(-dt_s * 30.0)
        
    # 3. Electric Tesla crackle during Combat Stance (6.0s to 11.5s)
    electric = np.zeros_like(t)
    el_mask = (t >= 6.0) & (t <= 11.5)
    noise_el = np.random.uniform(-0.06, 0.06, np.sum(el_mask))
    electric[el_mask] = noise_el + 0.12 * np.sin(2 * np.pi * 140 * t[el_mask])
    
    # 4. Weapons Charging Riser (11.5s to 17.5s)
    riser = np.zeros_like(t)
    rise_mask = (t >= 11.5) & (t <= 17.5)
    t_rise = t[rise_mask] - 11.5
    prog = (t_rise / 6.0) ** 2.4
    freq = 110.0 + (1500.0 - 110.0) * prog
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    riser[rise_mask] = 0.40 * np.sin(phase) * (t_rise / 6.0)
    
    # 5. 42Hz Ground Slam Detonation at 17.5s
    slam = np.zeros_like(t)
    slam_mask = t >= 17.5
    t_slam = t[slam_mask] - 17.5
    drop_sine = np.sin(2 * np.pi * 42.0 * t_slam) * np.exp(-t_slam * 1.5)
    punch_impact = np.sin(2 * np.pi * 95.0 * t_slam) * np.exp(-t_slam * 8.0)
    slam[slam_mask] = 0.80 * drop_sine + 0.45 * punch_impact
    
    # 6. Rocket Thruster Roar during Supersonic Takeoff (20.5s to 26s)
    roar = np.zeros_like(t)
    r_mask = t >= 20.5
    t_r = t[r_mask] - 20.5
    r_noise = np.random.uniform(-0.15, 0.15, np.sum(r_mask))
    r_sub = 0.35 * np.sin(2 * np.pi * 65.0 * t_r)
    r_amp = np.clip(t_r / 2.0, 0.1, 1.0)
    roar[r_mask] = (r_noise + r_sub) * r_amp
    
    sfx = drone + servos + electric + riser + slam + roar
    return np.clip(sfx, -0.92, 0.92)

def mix_mocap_master_audio():
    synthesize_all_vo()
    sfx_wav = os.path.join(OUTPUT_DIR, "temp_mocap_sfx.wav")
    master_wav = os.path.join(OUTPUT_DIR, "mocap_story_master_audio.wav")
    
    sfx = create_mocap_sfx()
    samples = (sfx * 32767).astype(np.int16)
    with wave.open(sfx_wav, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(samples.tobytes())
        
    b1 = os.path.join(OUTPUT_DIR, "mocap_beat_1.mp3")
    b2 = os.path.join(OUTPUT_DIR, "mocap_beat_2.mp3")
    b3 = os.path.join(OUTPUT_DIR, "mocap_beat_3.mp3")
    b4 = os.path.join(OUTPUT_DIR, "mocap_beat_4.mp3")
    
    filter_complex = (
        "[1:a]adelay=400|400,volume=1.4[a1];"
        "[2:a]adelay=6000|6000,volume=1.4[a2];"
        "[3:a]adelay=11800|11800,volume=1.4[a3];"
        "[4:a]adelay=20600|20600,volume=1.4[a4];"
        "[0:a][a1][a2][a3][a4]amix=inputs=5:duration=first:dropout_transition=2[aout]"
    )
    
    cmd = [
        FFMPEG, "-y",
        "-i", sfx_wav,
        "-i", b1,
        "-i", b2,
        "-i", b3,
        "-i", b4,
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-c:a", "pcm_s16le",
        "-t", "26.0",
        master_wav
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    if os.path.exists(sfx_wav): os.remove(sfx_wav)
    print(f"[SUCCESS] Master MoCap Audio Mixed: {master_wav}")

if __name__ == "__main__":
    mix_mocap_master_audio()
