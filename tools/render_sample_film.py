import os
import sys
import time
import math
import cv2
import numpy as np
import subprocess

# Set stdout encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from ultimate_film_vfx_studio import UltimateFilmVFXStudio, synthesize_movie_sfx

studio = UltimateFilmVFXStudio()
takes_dir = r"C:\Users\SVNITHESHPC\Downloads\film_takes"
os.makedirs(takes_dir, exist_ok=True)
art_dir = r"C:\Users\SVNITHESHPC\.gemini\antigravity\brain\972199e1-0395-45a5-b415-be1edfa58c26"

fps = 30
duration = 5.0
total_frames = int(fps * duration)
w, h = 1280, 720

raw_avi = os.path.join(takes_dir, "sample_raw_temp.avi")
sfx_wav = os.path.join(takes_dir, "sample_sfx_temp.wav")
final_mp4 = os.path.join(takes_dir, "SAMPLE_FILM_SCENE01_CLASH.mp4")

# MJPEG temporary video writer
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
writer = cv2.VideoWriter(raw_avi, fourcc, float(fps), (w, h))

print(f"[*] Rendering {total_frames} frames of cinematic sample film...")

# Sample frames to save as images for artifact inspection
saved_inspection_frames = {}

for f_idx in range(total_frames):
    t = f_idx / float(fps)
    
    # Create cinematic live-action studio backdrop
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        u = y / float(h)
        # Deep cinematic slate with moody floor reflection
        frame[y, :] = (int(26 + 18 * u), int(22 + 14 * u), int(32 + 16 * u))

    # Grid floor perspective lines
    horizon = int(h * 0.58)
    for x_pos in np.linspace(-w * 0.3, w * 1.3, 14):
        cv2.line(frame, (w // 2, horizon), (int(x_pos), h), (35, 45, 65), 1, cv2.LINE_AA)
    cv2.line(frame, (0, horizon), (w, horizon), (45, 60, 85), 2, cv2.LINE_AA)

    # Actor 1 (Left / Nithesh) at x=320, y=360
    actor1_joints = [(0, 0, 0)] * 33
    actor1_joints[11] = (270, 280, 0) # Sh L
    actor1_joints[12] = (370, 280, 0) # Sh R
    actor1_joints[23] = (280, 460, 0) # Hip L
    actor1_joints[24] = (360, 460, 0) # Hip R
    actor1_joints[27] = (260, 640, 0) # Ankle L
    actor1_joints[28] = (380, 640, 0) # Ankle R

    # Actor 2 (Right / Friend) at x=960, y=360
    actor2_joints = [(0, 0, 0)] * 33
    actor2_joints[11] = (910, 280, 0)
    actor2_joints[12] = (1010, 280, 0)
    actor2_joints[23] = (920, 460, 0)
    actor2_joints[24] = (1000, 460, 0)
    actor2_joints[27] = (890, 640, 0)
    actor2_joints[28] = (1030, 640, 0)

    # Phase 1: Charging (0.0s - 1.2s)
    if t < 1.2:
        # Actor 1 in SSJ Golden Aura
        actor1_joints[13] = (250, 340, 0)
        actor1_joints[14] = (390, 340, 0)
        actor1_joints[15] = (240, 410, 0)
        actor1_joints[16] = (400, 410, 0)
        
        # Actor 2 charging Chidori
        actor2_joints[13] = (880, 340, 0)
        actor2_joints[14] = (980, 330, 0)
        actor2_joints[15] = (870, 420, 0)
        actor2_joints[16] = (960, 380, 0)
        
        actors = [
            {"id": 1, "center_x": 320, "joints": actor1_joints, "role": "ACTOR 1", "spell": 2}, # SSJ Aura
            {"id": 2, "center_x": 960, "joints": actor2_joints, "role": "ACTOR 2", "spell": 4}  # Chidori Lightning
        ]

    # Phase 2: Beam Attack & Clash (1.2s - 4.5s)
    elif t < 4.5:
        # Actor 1 firing Kamehameha
        actor1_joints[13] = (320, 340, 0)
        actor1_joints[14] = (380, 340, 0)
        actor1_joints[15] = (350, 360, 0)
        actor1_joints[16] = (410, 360, 0) # Hands forward!

        # Actor 2 firing Repulsor
        actor2_joints[13] = (900, 340, 0)
        actor2_joints[14] = (980, 340, 0)
        actor2_joints[15] = (870, 360, 0) # Left hand forward firing!
        actor2_joints[16] = (1020, 390, 0)

        actors = [
            {"id": 1, "center_x": 320, "joints": actor1_joints, "role": "ACTOR 1", "spell": 1}, # Kamehameha
            {"id": 2, "center_x": 960, "joints": actor2_joints, "role": "ACTOR 2", "spell": 5}  # Repulsor Beam
        ]
        
        # Camera shake peaks at collision
        if t >= 2.0:
            studio.camera_shake = max(studio.camera_shake, 12.0 * math.sin(t * 8.0))

    # Phase 3: Climax Explosion & Fade (4.5s - 5.0s)
    else:
        actors = []
        # Detonation flash
        flash_alpha = (5.0 - t) / 0.5
        cv2.circle(frame, (640, 360), int(380 * flash_alpha), (255, 255, 255), -1, cv2.LINE_AA)
        studio.camera_shake = 16.0 * flash_alpha

    # Render VFX
    studio.render_film_vfx(frame, actors, t)

    # Apply Camera Shake
    if studio.camera_shake > 0.01:
        frame = studio.apply_camera_shake(frame)
        studio.camera_shake *= 0.88

    # Apply Hollywood Color Grade (Teal & Orange)
    frame = studio.apply_color_grade(frame)

    # Apply 2.39:1 Anamorphic Cinema Letterbox
    frame = studio.apply_anamorphic_letterbox(frame)

    # Draw Director Slate HUD
    studio.draw_director_hud(frame, actors, t)

    # Save to video
    writer.write(frame)

    # Save key milestone frames for inspection
    if f_idx == int(0.8 * fps): # 0.8s: Charge phase
        saved_inspection_frames["sample_charge_08s"] = frame.copy()
    elif f_idx == int(2.2 * fps): # 2.2s: Initial beam fire
        saved_inspection_frames["sample_beam_22s"] = frame.copy()
    elif f_idx == int(3.5 * fps): # 3.5s: Maximum beam clash
        saved_inspection_frames["sample_clash_35s"] = frame.copy()

writer.release()
print(f"[✓] Raw video rendered to: {raw_avi}")

# Save inspection images
for name, img_f in saved_inspection_frames.items():
    p = os.path.join(art_dir, f"{name}.png")
    cv2.imwrite(p, img_f)
    print(f"Saved milestone frame: {p}")

# Synthesize Movie Sound Design (40Hz hum -> 38Hz boom -> noise)
print("[*] Synthesizing Hollywood audio track...")
synthesize_movie_sfx(sfx_wav, duration)

# FFmpeg Master Muxing
print("[*] Encoding final broadcast-ready H.264 MP4 film clip with FFmpeg...")
cmd = [
    'ffmpeg', '-y',
    '-i', raw_avi,
    '-i', sfx_wav,
    '-c:v', 'libx264',
    '-crf', '18',
    '-preset', 'fast',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-shortest',
    final_mp4
]
subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# Also create an animated preview GIF for the chat artifact (first 3 seconds, 15 fps)
preview_gif = os.path.join(art_dir, "sample_film_preview.gif")
cmd_gif = [
    'ffmpeg', '-y',
    '-i', final_mp4,
    '-t', '3.5',
    '-vf', 'fps=12,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
    preview_gif
]
try:
    subprocess.run(cmd_gif, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[✓] Animated preview GIF generated: {preview_gif}")
except Exception as e:
    print(f"[!] GIF generation note: {e}")

# Clean temporary raw files
try:
    if os.path.exists(raw_avi): os.remove(raw_avi)
    if os.path.exists(sfx_wav): os.remove(sfx_wav)
except Exception:
    pass

print(f"\n========================================================")
print(f" [✓] SAMPLE FILM CLIP COMPLETE!")
print(f" Output Video: {final_mp4}")
print(f" Size: {os.path.getsize(final_mp4) / 1024:.1f} KB")
print(f"========================================================\n")
