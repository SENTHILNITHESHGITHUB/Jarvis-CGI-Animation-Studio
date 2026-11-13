import os
import sys
import math
import cv2
import numpy as np
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE = r"C:\Users\SVNITHESHPC\Downloads\AI_VFX_Realtime_Suite"
ARTIFACT_DIR = r"C:\Users\SVNITHESHPC\.gemini\antigravity\brain\972199e1-0395-45a5-b415-be1edfa58c26"
TAKES_DIR = r"C:\Users\SVNITHESHPC\Downloads\film_takes"
os.makedirs(TAKES_DIR, exist_ok=True)

AGNI_AVATAR_PATH = os.path.join(WORKSPACE, "assets", "agni_avatar_master.jpg")
NANDI_BULL_PATH = os.path.join(WORKSPACE, "assets", "nandi_astra_master.jpg")
FIRE_PLUME_PATH = os.path.join(WORKSPACE, "assets", "clean_brahmastra_fire_feathered.jpg")
SAMPLE_BG = os.path.join(ARTIFACT_DIR, "real_webcam_test.jpg")
if not os.path.exists(SAMPLE_BG):
    SAMPLE_BG = os.path.join(WORKSPACE, "assets", "real_webcam_test.jpg")

OUT_MP4 = os.path.join(TAKES_DIR, "BRAHMASTRA_SCENE01_AGNYASTRA.mp4")
OUT_GIF = os.path.join(ARTIFACT_DIR, "brahmastra_agni_preview.gif")

from test_brahmastra_cinema_composite import (
    composite_emissive_asset,
    apply_deep_photometric_relighting,
    apply_aces_tone_mapping,
    apply_anamorphic_letterbox
)

def synthesize_brahmastra_audio(wav_path, duration=3.5, sample_rate=44100):
    import wave
    import struct
    total_samples = int(sample_rate * duration)
    audio = np.zeros(total_samples, dtype=np.float32)
    t = np.linspace(0, duration, total_samples, endpoint=False)

    # 1. Deep Cosmic Rumble (36 Hz sub-bass)
    audio += 0.40 * np.sin(2 * np.pi * 36.0 * t)
    # 2. Roaring Fire Turbulence (Pink noise filtered)
    noise = np.random.normal(0, 0.25, total_samples)
    audio += noise * (0.15 + 0.10 * np.sin(2 * np.pi * 1.5 * t))
    # 3. Celestial Astra Chime / Shimmer (432 Hz divine overtone)
    audio += 0.12 * np.sin(2 * np.pi * 432.0 * t) * np.exp(-0.8 * (t % 1.5))

    audio = np.clip(audio, -0.95, 0.95)
    int16_data = (audio * 32767).astype(np.int16)

    with wave.open(wav_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16_data.tobytes())

def main():
    fps = 30
    duration = 3.5
    total_frames = int(fps * duration)
    w, h = 1280, 720

    base_img = cv2.imread(SAMPLE_BG)
    if base_img is None or base_img.size == 0:
        base_img = np.zeros((h, w, 3), dtype=np.uint8)
        base_img[:] = (22, 20, 26)
    base_img = cv2.resize(base_img, (w, h))

    agni_asset = cv2.imread(AGNI_AVATAR_PATH)
    fire_asset = cv2.imread(FIRE_PLUME_PATH)

    temp_avi = os.path.join(TAKES_DIR, "temp_brahmastra.avi")
    temp_wav = os.path.join(TAKES_DIR, "temp_brahmastra.wav")

    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    writer = cv2.VideoWriter(temp_avi, fourcc, float(fps), (w, h))

    # Embers pool
    np.random.seed(42)
    num_sparks = 320
    sparks = []
    for _ in range(num_sparks):
        sparks.append({
            "x": 640 + np.random.uniform(-300, 300),
            "y": 480 + np.random.uniform(-100, 200),
            "vx": np.random.uniform(-1.5, 1.5),
            "vy": np.random.uniform(-3.5, -1.2),
            "size": np.random.uniform(1.5, 3.8),
            "life": np.random.uniform(0.1, 1.0)
        })

    print(f"[*] Rendering {total_frames} frames of true Brahmastra cinematic motion...")

    actor_head = (640, 240)
    actor_left_hand = (440, 480)
    actor_right_hand = (840, 480)
    hand_emitters = [actor_left_hand, actor_right_hand]

    for f_idx in range(total_frames):
        t_sec = f_idx / float(fps)
        frame = base_img.copy()

        # Dynamic breathing/floating pulsation
        float_y = int(12 * math.sin(t_sec * 2.8))
        pulse_scale = 1.0 + 0.04 * math.sin(t_sec * 4.2)

        # 1. Photometric Relighting (pulsing with fire intensity)
        light_intensity = 1.7 + 0.3 * math.sin(t_sec * 5.0)
        frame = apply_deep_photometric_relighting(frame, [actor_head, actor_left_hand, actor_right_hand], color_bgr=(18, 125, 255), intensity=light_intensity)

        # 2. Agni Titan Avatar (drifting and breathing behind actor)
        avatar_cx = actor_head[0]
        avatar_cy = actor_head[1] - 80 + float_y
        composite_emissive_asset(frame, agni_asset, avatar_cx, avatar_cy, scale=0.62 * pulse_scale, intensity=1.55)

        # 3. Roaring Fluid Fire Plumes on Hands
        fire_scale_l = 0.48 * (1.0 + 0.08 * math.sin(t_sec * 8.0))
        fire_scale_r = 0.48 * (1.0 + 0.08 * math.cos(t_sec * 8.0))
        composite_emissive_asset(frame, fire_asset, actor_left_hand[0], actor_left_hand[1] - 80, scale=fire_scale_l, angle=15 + 4 * math.sin(t_sec * 6), flip_h=False, intensity=1.65)
        composite_emissive_asset(frame, fire_asset, actor_right_hand[0], actor_right_hand[1] - 80, scale=fire_scale_r, angle=-15 - 4 * math.cos(t_sec * 6), flip_h=True, intensity=1.65)

        # 4. Lens Flares & Glowing Cores
        glow_buf = np.zeros_like(frame)
        for em in hand_emitters:
            flare_rad = int(36 + 6 * math.sin(t_sec * 7))
            cv2.circle(glow_buf, em, flare_rad, (50, 200, 255), -1)
            cv2.circle(glow_buf, em, int(flare_rad * 0.55), (255, 255, 255), -1)
            cv2.line(glow_buf, (em[0] - 180, em[1]), (em[0] + 180, em[1]), (60, 210, 255), 4, cv2.LINE_AA)
            cv2.line(frame, (em[0] - 90, em[1]), (em[0] + 90, em[1]), (255, 255, 255), 2, cv2.LINE_AA)

        # 5. Dynamic Floating Embers
        for s in sparks:
            s["x"] += s["vx"] + 0.4 * math.sin(t_sec * 4 + s["y"] * 0.05)
            s["y"] += s["vy"]
            s["life"] -= 0.015
            if s["life"] <= 0 or s["y"] < 60:
                s["x"] = 640 + np.random.uniform(-250, 250)
                s["y"] = 520 + np.random.uniform(-40, 60)
                s["life"] = 1.0

            ix, iy = int(s["x"]), int(s["y"])
            if 0 <= ix < w and 0 <= iy < h:
                alpha = max(0.0, min(1.0, s["life"]))
                color = (int(18 * alpha), int(120 * alpha), int(255 * alpha))
                cv2.circle(glow_buf, (ix, iy), int(s["size"] * 2.5), color, -1)
                cv2.circle(frame, (ix, iy), max(1, int(s["size"] * 0.6)), (255, 255, 255), -1)

        # Bloom
        bloom1 = cv2.GaussianBlur(glow_buf, (21, 21), 0)
        bloom2 = cv2.GaussianBlur(glow_buf, (45, 45), 0)
        tot_bloom = cv2.addWeighted(bloom1, 0.65, bloom2, 0.35, 0)
        frame = cv2.addWeighted(frame, 1.0, tot_bloom, 0.75, 0)

        # ACES Tone Mapping
        frame = apply_aces_tone_mapping(frame)

        # 2.39:1 Cinemascope
        frame = apply_anamorphic_letterbox(frame, aspect=2.39)

        # Director HUD
        cv2.putText(frame, "BRAHMASTRA // SCENE 01: AGNYASTRA EMERGENCE", (40, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"TAKE 01 | TIME: {t_sec:04.2f}s | FPS: 30 | AGNI AVATAR ACTIVE", (40, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (50, 210, 255), 1, cv2.LINE_AA)

        writer.write(frame)

    writer.release()
    print("[*] Synthesizing audio...")
    synthesize_brahmastra_audio(temp_wav, duration=duration)

    print("[*] Encoding final H.264 MP4 with FFmpeg...")
    cmd_mp4 = [
        'ffmpeg', '-y',
        '-i', temp_avi,
        '-i', temp_wav,
        '-c:v', 'libx264',
        '-crf', '18',
        '-preset', 'fast',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        OUT_MP4
    ]
    subprocess.run(cmd_mp4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print("[*] Generating animated GIF preview...")
    cmd_gif = [
        'ffmpeg', '-y',
        '-i', OUT_MP4,
        '-vf', 'fps=14,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
        OUT_GIF
    ]
    subprocess.run(cmd_gif, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Clean temporary files
    if os.path.exists(temp_avi): os.remove(temp_avi)
    if os.path.exists(temp_wav): os.remove(temp_wav)

    print("\n========================================================")
    print(" [✓] BRAHMASTRA CINEMA SAMPLE COMPLETE!")
    print(f" MP4 Video: {OUT_MP4} ({os.path.getsize(OUT_MP4) / 1024:.1f} KB)")
    print(f" GIF Preview: {OUT_GIF} ({os.path.getsize(OUT_GIF) / 1024:.1f} KB)")
    print("========================================================\n")

if __name__ == "__main__":
    main()
