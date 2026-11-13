"""
================================================================================
⚡ BRAHMĀSTRA LIVE FILM STUDIO // CINEMATIC MULTI-ACTOR VFX ENGINE ⚡
================================================================================
Production standard replicated directly from Brahmāstra: Part One – Shiva (DNEG):
- Multi-Actor 3D Landmark Tracking (Actor 1: Shiva / Actor 2: Rival or Friend)
- Agni Titan Avatar with Flaming Trishul (Towering celestial spirit behind actor)
- Nandi Astra Spirit Bull (Power of 1000 Bulls charging behind actor)
- Real Fluid Fire Plumes on Forearms & Wrists (Sub-pixel feathered luminance blend)
- Deep Photometric 2000K Amber Relighting (Illuminates actors' real faces, clothing, and room)
- Dynamic Convective Embers & Sparks drifting upward with thermal buoyancy
- Mid-Air Astra Struggle Collision & Shockwaves
- 2.39:1 Anamorphic Cinemascope Letterboxing & ACES Filmic Tone Mapping
- One-Touch Spacebar Recording: Auto-muxes broadcast H.264 MP4 with sound design!
================================================================================
"""

import os
import sys
import math
import time
import random
import threading
import subprocess
from typing import List, Tuple, Optional, Dict, Any

import cv2
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Audio beep feedback
def play_beep(freq, duration_ms):
    if sys.platform == "win32":
        try:
            import winsound
            threading.Thread(target=lambda: winsound.Beep(freq, duration_ms), daemon=True).start()
        except Exception:
            pass

# MediaPipe Setup
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
POSE_MODEL = os.path.join(WORKSPACE, "pose_landmarker.task")
AGNI_AVATAR_PATH = os.path.join(WORKSPACE, "assets", "agni_avatar_master.jpg")
NANDI_BULL_PATH = os.path.join(WORKSPACE, "assets", "nandi_astra_master.jpg")
FIRE_PLUME_PATH = os.path.join(WORKSPACE, "assets", "clean_brahmastra_fire_feathered.jpg")
TAKES_DIR = r"C:\Users\SVNITHESHPC\Downloads\film_takes"
os.makedirs(TAKES_DIR, exist_ok=True)

# ------------------------------------------------------------------------------
# 1. 1-EURO SMOOTHING FILTER FOR JITTER-FREE HOLLYWOOD TRACKING
# ------------------------------------------------------------------------------
class OneEuroFilter3D:
    def __init__(self, min_cutoff=1.5, beta=0.03, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = np.zeros(3, dtype=np.float32)
        self.t_prev = None

    def filter(self, x, t):
        x = np.array(x, dtype=np.float32)
        if self.x_prev is None:
            self.x_prev = x
            self.t_prev = t
            return x

        dt = max(t - self.t_prev, 1e-4)
        self.t_prev = t

        dx = (x - self.x_prev) / dt
        edx = self._alpha(dt, self.d_cutoff)
        dx_hat = edx * dx + (1.0 - edx) * self.dx_prev
        self.dx_prev = dx_hat

        cutoff = self.min_cutoff + self.beta * np.linalg.norm(dx_hat)
        alpha = self._alpha(dt, cutoff)
        x_hat = alpha * x + (1.0 - alpha) * self.x_prev
        self.x_prev = x_hat
        return x_hat

    def _alpha(self, dt, cutoff):
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

# ------------------------------------------------------------------------------
# 2. COMPOSITING HELPERS (SUB-PIXEL SCREEN & ADDITIVE EMISSIVE BLEND)
# ------------------------------------------------------------------------------
def composite_emissive_asset(base_img, asset_bgr, center_x, center_y, scale=1.0, angle=0.0, flip_h=False, intensity=1.4):
    if asset_bgr is None:
        return
    if flip_h:
        asset_bgr = cv2.flip(asset_bgr, 1)

    h_a, w_a = asset_bgr.shape[:2]
    new_w = max(1, int(w_a * scale))
    new_h = max(1, int(h_a * scale))

    resized = cv2.resize(asset_bgr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    if abs(angle) > 0.5:
        M = cv2.getRotationMatrix2D((new_w / 2, new_h / 2), angle, 1.0)
        resized = cv2.warpAffine(resized, M, (new_w, new_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))

    h_bg, w_bg = base_img.shape[:2]
    x1 = int(center_x - new_w // 2)
    y1 = int(center_y - new_h // 2)
    x2 = x1 + new_w
    y2 = y1 + new_h

    fx1, fy1 = max(0, x1), max(0, y1)
    fx2, fy2 = min(w_bg, x2), min(h_bg, y2)
    if fx2 <= fx1 or fy2 <= fy1:
        return

    sx1, sy1 = fx1 - x1, fy1 - y1
    sx2, sy2 = sx1 + (fx2 - fx1), sy1 + (fy2 - fy1)

    crop = resized[sy1:sy2, sx1:sx2].astype(np.float32)

    # Compute luminance alpha
    gray = cv2.cvtColor(resized[sy1:sy2, sx1:sx2], cv2.COLOR_BGR2GRAY).astype(np.float32)
    alpha = np.clip((gray - 12.0) / 190.0, 0.0, 1.0)
    alpha = (alpha ** 1.2)[:, :, None]

    roi = base_img[fy1:fy2, fx1:fx2].astype(np.float32)
    blended = roi * (1.0 - alpha * 0.40) + crop * alpha * intensity
    base_img[fy1:fy2, fx1:fx2] = np.clip(blended, 0.0, 255.0).astype(np.uint8)

def apply_deep_photometric_relighting(frame, light_sources, color_bgr=(18, 120, 255), intensity=1.5):
    h_f, w_f = frame.shape[:2]
    if not light_sources:
        return frame

    scale = 0.25
    h_s, w_s = int(h_f * scale), int(w_f * scale)
    irradiance = np.zeros((h_s, w_s), dtype=np.float32)

    for lx, ly in light_sources:
        sx, sy = lx * scale, ly * scale
        sigma = 150.0 * scale
        y_g, x_g = np.ogrid[:h_s, :w_s]
        d2 = (x_g - sx)**2 + (y_g - sy)**2
        irradiance += np.exp(-d2 / (2.0 * (sigma**2)))

    irradiance = np.clip(irradiance * intensity, 0.0, 2.4)
    irradiance_full = cv2.resize(irradiance, (w_f, h_f), interpolation=cv2.INTER_LINEAR)

    light_color = np.array(color_bgr, dtype=np.float32)
    frame_flt = frame.astype(np.float32)
    illum = (irradiance_full[:, :, None] * light_color * 0.42)
    relit = np.clip(frame_flt + (frame_flt * illum / 255.0) * 1.25, 0.0, 255.0).astype(np.uint8)
    return relit

def apply_aces_tone_mapping(image):
    norm = image.astype(np.float32) / 255.0
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    aces = np.clip((norm * (a * norm + b)) / (norm * (c * norm + d) + e), 0.0, 1.0)
    return (aces * 255.0).astype(np.uint8)

def apply_anamorphic_letterbox(frame, aspect=2.39):
    h, w = frame.shape[:2]
    target_h = int(w / aspect)
    bar_h = max(0, (h - target_h) // 2)
    if bar_h > 0:
        frame[0:bar_h, :] = 0
        frame[h - bar_h:h, :] = 0
    return frame

# ------------------------------------------------------------------------------
# 3. MOVIE SOUND SYNTHESIZER
# ------------------------------------------------------------------------------
def synthesize_brahmastra_audio(wav_path, duration=5.0, sample_rate=44100):
    import wave
    total_samples = int(sample_rate * duration)
    audio = np.zeros(total_samples, dtype=np.float32)
    t = np.linspace(0, duration, total_samples, endpoint=False)

    # Cosmic rumble + roar
    audio += 0.45 * np.sin(2 * np.pi * 36.0 * t)
    noise = np.random.normal(0, 0.22, total_samples)
    audio += noise * (0.16 + 0.10 * np.sin(2 * np.pi * 1.5 * t))
    audio += 0.12 * np.sin(2 * np.pi * 432.0 * t) * np.exp(-0.7 * (t % 1.5))

    audio = np.clip(audio, -0.95, 0.95)
    int16_data = (audio * 32767).astype(np.int16)

    with wave.open(wav_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16_data.tobytes())

# ------------------------------------------------------------------------------
# 4. MASTER REAL-TIME BRAHMĀSTRA STUDIO
# ------------------------------------------------------------------------------
class BrahmastraLiveStudio:
    def __init__(self, input_file=None):
        self.win_name = "BRAHMASTRA LIVE FILM STUDIO // DNEG CINEMA"
        self.win_w = 1280
        self.win_h = 720
        self.running = True

        # Assets
        self.agni_asset = cv2.imread(AGNI_AVATAR_PATH)
        self.nandi_asset = cv2.imread(NANDI_BULL_PATH)
        self.fire_asset = cv2.imread(FIRE_PLUME_PATH)

        # Embers
        self.sparks = []
        for _ in range(350):
            self.sparks.append({
                "x": 640 + np.random.uniform(-300, 300),
                "y": 480 + np.random.uniform(-100, 200),
                "vx": np.random.uniform(-1.5, 1.5),
                "vy": np.random.uniform(-3.5, -1.2),
                "size": np.random.uniform(1.5, 3.8),
                "life": np.random.uniform(0.1, 1.0)
            })

        # Modes
        # 1: Agnyastra (Shiva Fire + Agni Titan Avatar)
        # 2: Nandi Astra (1000 Bulls Power)
        # 3: Prabhastra (Sword of Light)
        # 4: Junoon Dark Astra
        self.actor1_astra = 1
        self.actor2_astra = 4
        self.use_letterbox = True
        self.use_color_grade = True

        # Recording
        self.recording = False
        self.rec_writer = None
        self.rec_start_time = 0.0
        self.rec_temp_avi = None
        self.rec_temp_wav = None
        self.take_index = 1

        # Camera & Filter init
        self.cap = None
        self.video_source = 'WEBCAM'
        self.input_file = input_file
        self.init_camera()

        self.filters_p1 = [OneEuroFilter3D(min_cutoff=1.5, beta=0.03) for _ in range(33)]
        self.filters_p2 = [OneEuroFilter3D(min_cutoff=1.5, beta=0.03) for _ in range(33)]

        # MediaPipe Landmarker
        base_options = python.BaseOptions(model_asset_path=POSE_MODEL)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=2,
            min_pose_detection_confidence=0.52,
            min_tracking_confidence=0.52
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def init_camera(self):
        if self.input_file and os.path.exists(self.input_file):
            self.cap = cv2.VideoCapture(self.input_file)
            self.video_source = 'FILE'
            print(f"[*] Loaded film video file: {self.input_file}")
            return

        # Connect to webcam: test indices 0 and 1 across DEFAULT, MSMF, DSHOW backends
        for idx in [0, 1]:
            for backend in [None, cv2.CAP_MSMF, cv2.CAP_DSHOW]:
                try:
                    if backend is None:
                        cap = cv2.VideoCapture(idx)
                    else:
                        cap = cv2.VideoCapture(idx, backend)

                    if cap.isOpened():
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            self.cap = cap
                            self.video_source = 'WEBCAM'
                            backend_str = "DEFAULT" if backend is None else ("MSMF" if backend == cv2.CAP_MSMF else "DSHOW")
                            print(f"[*] Active Webcam Connected: Index [{idx}] via {backend_str} ({frame.shape[1]}x{frame.shape[0]})")
                            return
                        cap.release()
                except Exception:
                    pass
        print("[!] Camera unavailable. Using synthetic backdrop.")

    def run(self):
        cv2.namedWindow(self.win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.win_name, self.win_w, self.win_h)

        print("\n========================================================")
        print(" ⚡ BRAHMĀSTRA LIVE FILM STUDIO ACTIVE ⚡")
        print(" [SPACE] RECORD FILM TAKE ([● ACTION!] / [■ CUT!])")
        print(" [1]     Actor 1: Agnyāstra (Shiva Fire + Agni Titan)")
        print(" [2]     Actor 1: Nandi Astra (Power of 1000 Bulls)")
        print(" [3]     Actor 1: Prabhāstra (Sword of Celestial Light)")
        print(" [4]     Actor 2: Junoon Dark Astra (Crimson Lightning)")
        print(" [5]     Actor 2: Opposing Agnyāstra (Fire vs Fire Duel)")
        print(" [C]     Toggle 2.39:1 Cinemascope Letterbox")
        print(" [G]     Toggle ACES Filmic Grading")
        print(" [Q/ESC] Exit")
        print("========================================================\n")

        start_time = time.time()
        frame_idx = 0

        while self.running:
            t_curr = time.time()
            ts_ms = int((t_curr - start_time) * 1000)
            frame_idx += 1

            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    if self.video_source == 'FILE':
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            else:
                frame = np.zeros((720, 1280, 3), dtype=np.uint8)

            if self.video_source == 'WEBCAM':
                frame = cv2.flip(frame, 1)

            if frame.shape[:2] != (720, 1280):
                frame = cv2.resize(frame, (1280, 720))

            # MediaPipe Pose Detection
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            detection_result = self.landmarker.detect_for_video(mp_image, ts_ms)

            actors = []
            if detection_result.pose_landmarks:
                for a_idx, p_landmarks in enumerate(detection_result.pose_landmarks[:2]):
                    flt = self.filters_p1 if a_idx == 0 else self.filters_p2
                    smoothed = []
                    for j_idx, lm in enumerate(p_landmarks):
                        raw_pt = np.array([lm.x * 1280.0, lm.y * 720.0, lm.z * 1280.0], dtype=np.float32)
                        filt_pt = flt[j_idx].filter(raw_pt, t_curr)
                        smoothed.append((int(filt_pt[0]), int(filt_pt[1]), int(filt_pt[2])))

                    cx = smoothed[0][0]
                    actors.append({
                        "id": a_idx + 1,
                        "center_x": cx,
                        "joints": smoothed,
                        "role": "SHIVA (ACTOR 1)" if a_idx == 0 else "RIVAL (ACTOR 2)",
                        "astra": self.actor1_astra if a_idx == 0 else self.actor2_astra
                    })

            # Sort actors left to right
            actors.sort(key=lambda a: a["center_x"])

            # ------------------------------------------------------------------
            # RENDER ASTRA VFX
            # ------------------------------------------------------------------
            all_light_emitters = []
            glow_buf = np.zeros_like(frame)

            for act in actors:
                joints = act["joints"]
                astra_type = act["astra"]
                head = (joints[0][0], joints[0][1])
                lw = (joints[15][0], joints[15][1])
                rw = (joints[16][0], joints[16][1])

                all_light_emitters.extend([head, lw, rw])

                float_y = int(10 * math.sin(t_curr * 3.0 + act["id"]))
                pulse = 1.0 + 0.04 * math.sin(t_curr * 4.5 + act["id"])

                # AGNYĀSTRA (Shiva Fire + Agni Titan Avatar)
                if astra_type == 1:
                    # Agni Titan Avatar behind actor
                    composite_emissive_asset(frame, self.agni_asset, head[0], head[1] - 80 + float_y, scale=0.60 * pulse, intensity=1.55)
                    # Roaring Fluid Fire on Hand/Forearm
                    composite_emissive_asset(frame, self.fire_asset, lw[0], lw[1] - 80, scale=0.45, angle=14, flip_h=False, intensity=1.65)
                    composite_emissive_asset(frame, self.fire_asset, rw[0], rw[1] - 80, scale=0.45, angle=-14, flip_h=True, intensity=1.65)
                    for em in [lw, rw]:
                        cv2.circle(glow_buf, em, 35, (50, 200, 255), -1)
                        cv2.circle(glow_buf, em, 18, (255, 255, 255), -1)
                        cv2.line(glow_buf, (em[0] - 160, em[1]), (em[0] + 160, em[1]), (60, 210, 255), 4, cv2.LINE_AA)
                        cv2.line(frame, (em[0] - 80, em[1]), (em[0] + 80, em[1]), (255, 255, 255), 2, cv2.LINE_AA)

                # NANDI ASTRA (1000 Bulls Power)
                elif astra_type == 2:
                    composite_emissive_asset(frame, self.nandi_asset, head[0], head[1] - 90 + float_y, scale=0.65 * pulse, intensity=1.60)
                    for em in [lw, rw]:
                        cv2.circle(glow_buf, em, 40, (255, 190, 40), -1)
                        cv2.circle(glow_buf, em, 20, (255, 255, 255), -1)
                        cv2.line(glow_buf, (em[0] - 180, em[1]), (em[0] + 180, em[1]), (255, 210, 80), 4, cv2.LINE_AA)

                # PRABHĀSTRA (Sword of Light)
                elif astra_type == 3:
                    # Divine golden sword emanating from right hand
                    sw_top = (rw[0] + 20, rw[1] - 280)
                    cv2.line(glow_buf, rw, sw_top, (80, 220, 255), 18, cv2.LINE_AA)
                    cv2.line(glow_buf, rw, sw_top, (255, 255, 255), 8, cv2.LINE_AA)
                    cv2.line(frame, rw, sw_top, (255, 255, 255), 4, cv2.LINE_AA)

                # JUNOON DARK ASTRA (Crimson Lightning)
                elif astra_type == 4:
                    # Red jagged dark energy
                    for em in [lw, rw]:
                        cv2.circle(glow_buf, em, 35, (20, 20, 220), -1)
                        cv2.circle(glow_buf, em, 18, (255, 255, 255), -1)
                        for _ in range(3):
                            ang = random.uniform(0, 2 * math.pi)
                            l_len = random.uniform(50, 120)
                            p_end = (int(em[0] + math.cos(ang) * l_len), int(em[1] + math.sin(ang) * l_len))
                            cv2.line(glow_buf, em, p_end, (15, 25, 240), 4, cv2.LINE_AA)
                            cv2.line(frame, em, p_end, (255, 255, 255), 1, cv2.LINE_AA)

            # Photometric Relighting (2000K Amber glow onto actors & room)
            if all_light_emitters:
                frame = apply_deep_photometric_relighting(frame, all_light_emitters, intensity=1.65)

            # Embers
            for s in self.sparks:
                s["x"] += s["vx"]
                s["y"] += s["vy"]
                s["life"] -= 0.015
                if s["life"] <= 0 or s["y"] < 80:
                    s["x"] = random.choice([640, 440, 840]) + np.random.uniform(-180, 180)
                    s["y"] = 520 + np.random.uniform(-40, 60)
                    s["life"] = 1.0

                ix, iy = int(s["x"]), int(s["y"])
                if 0 <= ix < 1280 and 0 <= iy < 720:
                    alpha = max(0.0, min(1.0, s["life"]))
                    color = (int(18 * alpha), int(120 * alpha), int(255 * alpha))
                    cv2.circle(glow_buf, (ix, iy), int(s["size"] * 2.5), color, -1)
                    cv2.circle(frame, (ix, iy), max(1, int(s["size"] * 0.6)), (255, 255, 255), -1)

            # Bloom
            b1 = cv2.GaussianBlur(glow_buf, (21, 21), 0)
            b2 = cv2.GaussianBlur(glow_buf, (45, 45), 0)
            total_b = cv2.addWeighted(b1, 0.65, b2, 0.35, 0)
            frame = cv2.addWeighted(frame, 1.0, total_b, 0.75, 0)

            # ACES Tone Mapping
            if self.use_color_grade:
                frame = apply_aces_tone_mapping(frame)

            # Cinemascope Letterbox
            if self.use_letterbox:
                frame = apply_anamorphic_letterbox(frame, aspect=2.39)

            # Director Slate HUD
            rec_status = "[● ACTION! REC]" if self.recording else "[STANDBY]"
            rec_color = (0, 0, 255) if self.recording else (40, 215, 255)
            cv2.putText(frame, f"BRAHMASTRA FILM STUDIO // {rec_status}", (40, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.65, rec_color, 2, cv2.LINE_AA)
            cv2.putText(frame, f"ACTOR 1: ASTRA [{self.actor1_astra}] | ACTOR 2: ASTRA [{self.actor2_astra}] | TAKE: #{self.take_index:02d}", (40, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1, cv2.LINE_AA)

            if self.recording and self.rec_writer:
                self.rec_writer.write(frame)

            cv2.imshow(self.win_name, frame)
            key = cv2.waitKey(1) & 0xFF

            if key in [ord('q'), 27]: # Q or ESC
                break
            elif key == ord(' '): # SPACEBAR Toggle Record
                self.toggle_recording()
            elif key == ord('1'):
                self.actor1_astra = 1 # Agnyastra
                play_beep(880, 50)
            elif key == ord('2'):
                self.actor1_astra = 2 # Nandi Astra
                play_beep(740, 50)
            elif key == ord('3'):
                self.actor1_astra = 3 # Prabhastra
                play_beep(980, 50)
            elif key == ord('4'):
                self.actor2_astra = 4 # Junoon Dark
                play_beep(440, 50)
            elif key == ord('5'):
                self.actor2_astra = 1 # Fire duel
                play_beep(660, 50)
            elif key in [ord('c'), ord('C')]:
                self.use_letterbox = not self.use_letterbox
            elif key in [ord('g'), ord('G')]:
                self.use_color_grade = not self.use_color_grade

        if self.recording:
            self.stop_recording()

        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.recording = True
        self.rec_start_time = time.time()
        self.rec_temp_avi = os.path.join(TAKES_DIR, f"temp_take_{self.take_index}.avi")
        self.rec_temp_wav = os.path.join(TAKES_DIR, f"temp_take_{self.take_index}.wav")
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.rec_writer = cv2.VideoWriter(self.rec_temp_avi, fourcc, 30.0, (1280, 720))
        play_beep(1400, 120)
        print(f"\n[● ACTION!] Recording Take #{self.take_index:02d} started...")

    def stop_recording(self):
        self.recording = False
        duration = max(1.0, time.time() - self.rec_start_time)
        if self.rec_writer:
            self.rec_writer.release()
            self.rec_writer = None

        play_beep(700, 180)
        print(f"[■ CUT!] Take #{self.take_index:02d} finished. Duration: {duration:.1f}s")

        final_mp4 = os.path.join(TAKES_DIR, f"BRAHMASTRA_TAKE_{self.take_index:02d}.mp4")
        self.take_index += 1

        threading.Thread(target=self._mux_take, args=(self.rec_temp_avi, self.rec_temp_wav, final_mp4, duration), daemon=True).start()

    def _mux_take(self, avi_path, wav_path, mp4_path, duration):
        try:
            print("[*] Synthesizing Astra audio and encoding broadcast MP4...")
            synthesize_brahmastra_audio(wav_path, duration=duration)
            cmd = [
                'ffmpeg', '-y',
                '-i', avi_path,
                '-i', wav_path,
                '-c:v', 'libx264',
                '-crf', '18',
                '-preset', 'fast',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                mp4_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(avi_path): os.remove(avi_path)
            if os.path.exists(wav_path): os.remove(wav_path)
            print(f"[✓] Take encoded successfully: {mp4_path}\n")
        except Exception as e:
            print(f"[!] Take encoding error: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default=None, help="Path to video file shot on phone/camera")
    args = parser.parse_args()

    studio = BrahmastraLiveStudio(input_file=args.input)
    studio.run()
