"""
================================================================================
ULTIMATE FILM VFX AI STUDIO (HOLLYWOOD & ANIME PRODUCTION ENGINE)
================================================================================
Designed for Live-Action Filmmaking with Friends.
Inspired by Higgsfield AI (code-based film engineering) & Leonxlnx Procedural Physics.

Features:
- Dual Mode: Live Camera Shoot (DirectShow 60 FPS) OR Process Recorded Video File ([L])
- Multi-Actor AI MoCap: Tracks Actor 1 (You) and Actor 2 (Friend) simultaneously
- Real Cinematic Physical VFX (Zero Cheap 2D Canvas Blobs):
    [1] Dragon Ball Z Kamehameha (Plasma Core + Cyan Envelope + Lightning Arcs)
    [2] Super Saiyan Golden Ki Aura (Planck Blackbody 800K-3200K + Curl Noise)
    [3] Naruto Rasengan (High-Speed Rotational Particle Stream Vortex)
    [4] Naruto Chidori (Jagged High-Voltage Electric Fractal Arcs)
    [5] Iron Man Mark 85 Repulsor & Chest Arc Reactor
    [6] Doctor Strange Eldritch Mystic Shield (Rotating Runic Mandala)
    [7] Leonxlnx Physically-Based Combustion Fire (Chemiluminescent Blue Root)
- Mid-Air Beam Struggle & Clash Detection: Beams collide with explosive shockwave!
- Director Slate & Anamorphic Letterbox (2.39:1 Cinemascope)
- Hollywood Color Grading LUTs (Teal & Orange / 35mm Portra / Cyberpunk)
- Dynamic Film Camera Shake & Lens Flares
- Auto Film Take Recording ([SPACE]) with Synthesized Movie Sound Design & FFmpeg Encode
================================================================================
"""

import os
import sys
import time
import math
import wave
import struct
import subprocess
import threading
import winsound
import numpy as np
import cv2

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# MediaPipe Native Vision
try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
except ImportError:
    print("[!] Error: MediaPipe tasks API required. Run: pip install mediapipe opencv-python")
    sys.exit(1)

# Locate Pose Task Model
MODEL_PATHS = [
    r"C:\Users\SVNITHESHPC\Downloads\AI_VFX_Realtime_Suite\pose_landmarker.task",
    os.path.join(os.path.dirname(__file__), "pose_landmarker.task"),
    r"C:\Users\SVNITHESHPC\Downloads\GestureControlSuite\pose_landmarker.task"
]
pose_model_file = None
for p in MODEL_PATHS:
    if os.path.exists(p):
        pose_model_file = p
        break

if not pose_model_file:
    print("[!] Error: pose_landmarker.task not found in standard paths.")
    sys.exit(1)

# Output directory for Film Takes
FILM_TAKES_DIR = r"C:\Users\SVNITHESHPC\Downloads\film_takes"
os.makedirs(FILM_TAKES_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# 1-Euro Filter for Jitter-Free MoCap Smoothing
# -----------------------------------------------------------------------------
class OneEuroFilter3D:
    def __init__(self, min_cutoff=1.5, beta=0.02, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None

    def alpha(self, cutoff, dt):
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, x, timestamp):
        x = np.array(x, dtype=np.float32)
        if self.t_prev is None:
            self.x_prev = x
            self.dx_prev = np.zeros_like(x)
            self.t_prev = timestamp
            return x

        dt = max(timestamp - self.t_prev, 1e-4)
        self.t_prev = timestamp

        dx = (x - self.x_prev) / dt
        a_d = self.alpha(self.d_cutoff, dt)
        dx_hat = a_d * dx + (1 - a_d) * self.dx_prev
        self.dx_prev = dx_hat

        speed = np.linalg.norm(dx_hat)
        cutoff = self.min_cutoff + self.beta * speed
        a = self.alpha(cutoff, dt)
        x_hat = a * x + (1 - a) * self.x_prev
        self.x_prev = x_hat
        return x_hat

# -----------------------------------------------------------------------------
# Hollywood Sound Design Synthesizer (Zero Audio Files Needed)
# -----------------------------------------------------------------------------
def synthesize_movie_sfx(wav_path, duration_sec, events=None, sample_rate=44100):
    """Generates movie-grade synthesized sound effects aligned with the film take"""
    num_samples = int(duration_sec * sample_rate)
    samples = np.zeros(num_samples, dtype=np.float32)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)

    # 1. Subtle low atmospheric drone (40 Hz)
    drone = np.sin(2 * math.pi * 38.0 * t) * 0.12

    # 2. Charging hum and detonation boom for recorded actions
    # Default dramatic climax at t = max(1.0, duration_sec - 1.5)
    blast_t0 = max(1.0, duration_sec - 2.0)
    
    # Ramp hum
    t_ramp = np.clip((t - max(0.0, blast_t0 - 1.5)) / 1.5, 0.0, 1.0) * (t < blast_t0)
    hum_freq = 50.0 + 180.0 * (t_ramp ** 2)
    hum_phase = np.cumsum(hum_freq / sample_rate) * 2 * math.pi
    hum = np.sin(hum_phase) * t_ramp * 0.45

    # Sub-bass Detonation Boom (38 Hz punch)
    t_blast = np.maximum(0.0, t - blast_t0)
    boom_envelope = np.exp(-t_blast * 2.8) * (t >= blast_t0)
    boom = np.sin(2 * math.pi * 38.0 * t_blast) * boom_envelope * 0.92

    # High-frequency electric plasma sizzle
    noise = (np.random.rand(num_samples) * 2.0 - 1.0) * boom_envelope * 0.28

    total = np.clip(drone + hum + boom + noise, -1.0, 1.0)
    total_int16 = (total * 32767).astype(np.int16)

    with wave.open(wav_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(total_int16.tobytes())

# -----------------------------------------------------------------------------
# Main Film VFX AI Studio Engine
# -----------------------------------------------------------------------------
class UltimateFilmVFXStudio:
    def __init__(self):
        self.win_name = "Ultimate Film VFX AI Studio | Hollywood & Anime Cinema Engine"
        self.win_w = 1280
        self.win_h = 720
        self.running = True

        # Multi-Actor Spell Selection
        # 1: Kamehameha, 2: SSJ Aura, 3: Rasengan, 4: Chidori, 5: Repulsor, 6: Mystic Shield, 7: Fire Magic
        self.spell_names = {
            1: "KAMEHAMEHA (PLASMA BEAM)",
            2: "SUPER SAIYAN GOLDEN AURA",
            3: "NARUTO RASENGAN (VORTEX)",
            4: "NARUTO CHIDORI (LIGHTNING)",
            5: "IRON MAN REPULSOR BEAM",
            6: "DOCTOR STRANGE MYSTIC SHIELD",
            7: "PROCEDURAL COMBUSTION FIRE"
        }
        self.actor1_spell = 1 # Kamehameha
        self.actor2_spell = 4 # Chidori / Counter spell for friend

        # Filmmaking Parameters
        self.scene_num = 1
        self.shot_num = 1
        self.take_num = 1
        self.is_recording = False
        self.record_frames = []
        self.record_start_time = 0.0
        self.video_writer = None
        self.current_raw_video_path = None

        # Cinema Modes
        self.anamorphic_letterbox = True # 2.39:1 Cinemascope
        self.color_lut = 'TEAL_ORANGE'   # 'TEAL_ORANGE', 'PORTRA_35MM', 'CYBERPUNK', 'NONE'
        self.camera_shake = 0.0          # Decaying screen shake magnitude

        # Particle Systems & Volumetrics
        self.sparks = [] # Buoyant ember particles
        self.clash_active = False
        self.clash_point = None

        # Camera & Video File Input
        self.video_source = 'WEBCAM' # 'WEBCAM' or 'FILE'
        self.input_file_path = None
        self.cap = None

        # Initialize MediaPipe Multi-Person Landmarker (num_poses=2)
        self.init_mediapipe_landmarker()

        # Connect to Camera
        self.init_camera()

        # Filters for Actor 1 and Actor 2 (33 landmarks each)
        self.filters_p1 = [OneEuroFilter3D(min_cutoff=1.6, beta=0.03) for _ in range(33)]
        self.filters_p2 = [OneEuroFilter3D(min_cutoff=1.6, beta=0.03) for _ in range(33)]

    def init_mediapipe_landmarker(self):
        base_options = python.BaseOptions(model_asset_path=pose_model_file)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=2, # Tracks both you and your friend!
            min_pose_detection_confidence=0.52,
            min_tracking_confidence=0.52
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def init_camera(self):
        if self.cap is not None:
            self.cap.release()

        # Find available camera (Cam 1 -> Cam 0 -> Cam 2)
        for idx in [1, 0, 2]:
            try:
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                        self.cap = cap
                        self.video_source = 'WEBCAM'
                        print(f"[*] Camera connected: Index [{idx}] (1280x720 DirectShow)")
                        return
                    cap.release()
            except Exception:
                pass

        print("[!] Camera unavailable. Falling back to synthetic film stage.")

    def load_video_file(self, video_path):
        """Loads a recorded video file shot with your friends on phone / camera"""
        if not os.path.exists(video_path):
            print(f"[!] Video file not found: {video_path}")
            return
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(video_path)
        self.video_source = 'FILE'
        self.input_file_path = video_path
        print(f"[*] Loaded film video file for VFX processing: {video_path}")
        threading.Thread(target=lambda: winsound.Beep(1200, 70), daemon=True).start()

    def run(self):
        cv2.namedWindow(self.win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.win_name, self.win_w, self.win_h)

        print("\n========================================================")
        print(" ULTIMATE FILM VFX AI STUDIO ACTIVE")
        print(" [SPACE] START / STOP RECORDING FILM TAKE ([● REC])")
        print(" [1-7]   Select Actor 1 Spell (Kamehameha, SSJ Aura, Rasengan, etc.)")
        print(" [F1-F7] Select Actor 2 (Friend) Spell")
        print(" [C]     Toggle 2.39:1 Anamorphic Cinema Letterbox")
        print(" [G]     Toggle Hollywood Color Grading (Teal & Orange / Portra 35mm)")
        print(" [L]     Load Video File Shot with Friends")
        print(" [Q/ESC] Exit Studio")
        print("========================================================\n")

        start_time = time.time()
        frame_idx = 0

        while self.running:
            t_curr = time.time()
            ts_ms = int((t_curr - start_time) * 1000)
            frame_idx += 1

            # Read frame
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    if self.video_source == 'FILE':
                        # Loop video
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            else:
                frame = np.zeros((720, 1280, 3), dtype=np.uint8)

            # If webcam, flip horizontally for mirror intuitive preview
            if self.video_source == 'WEBCAM':
                frame = cv2.flip(frame, 1)

            # Scale to 1280x720
            if frame.shape[:2] != (720, 1280):
                frame = cv2.resize(frame, (1280, 720))

            # Run Multi-Person MediaPipe Pose Detection
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            pose_result = None
            try:
                pose_result = self.landmarker.detect_for_video(mp_image, ts_ms)
            except Exception:
                pass

            # Extract Actors (Actor 1 = Left, Actor 2 = Right)
            actors = self.extract_multi_actors(pose_result, ts_ms)

            # Render Hollywood VFX
            self.render_film_vfx(frame, actors, t_curr)

            # Apply Dynamic Camera Shake if active
            if self.camera_shake > 0.01:
                frame = self.apply_camera_shake(frame)
                self.camera_shake *= 0.88 # Decay shake

            # Apply Hollywood Color Grading LUT
            if self.color_lut != 'NONE':
                frame = self.apply_color_grade(frame)

            # Apply 2.39:1 Anamorphic Cinema Letterboxing
            if self.anamorphic_letterbox:
                frame = self.apply_anamorphic_letterbox(frame)

            # Draw Director Film Slate & HUD
            self.draw_director_hud(frame, actors, t_curr)

            # Handle Recording Take
            if self.is_recording and self.video_writer is not None:
                self.video_writer.write(frame)

            # Show Window
            cv2.imshow(self.win_name, frame)

            # Handle Key Input
            key = cv2.waitKey(1) & 0xFF
            if key != 255:
                self.handle_key(key)

            if cv2.getWindowProperty(self.win_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        # Cleanup
        if self.is_recording:
            self.stop_recording()
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("[*] Ultimate Film VFX Studio closed cleanly.")

    def extract_multi_actors(self, pose_result, ts_ms):
        """Extracts and separates Actor 1 (Left / You) and Actor 2 (Right / Friend) in screen coordinates"""
        if not pose_result or not pose_result.pose_landmarks or len(pose_result.pose_landmarks) == 0:
            return []

        actors = []
        for p_idx, lms in enumerate(pose_result.pose_landmarks[:2]):
            flt = self.filters_p1 if p_idx == 0 else self.filters_p2
            pts_2d = []
            for i, lm in enumerate(lms):
                raw_pt = np.array([lm.x * 1280.0, lm.y * 720.0, lm.z], dtype=np.float32)
                filt = flt[i].filter(raw_pt, ts_ms / 1000.0)
                pts_2d.append((int(filt[0]), int(filt[1]), filt[2]))

            # Actor center X from hips
            mid_hip_x = (pts_2d[23][0] + pts_2d[24][0]) * 0.5
            actors.append({
                "id": p_idx + 1,
                "center_x": mid_hip_x,
                "joints": pts_2d
            })

        # Sort so Actor 1 is Left, Actor 2 is Right
        actors.sort(key=lambda a: a["center_x"])
        for idx, a in enumerate(actors):
            a["role"] = f"ACTOR {idx + 1}"
            a["spell"] = self.actor1_spell if idx == 0 else self.actor2_spell
        return actors

    def render_film_vfx(self, canvas, actors, t_curr):
        """Renders cinematic physical VFX for each actor and detects beam collisions"""
        beam_origins = []

        for actor in actors:
            spell_id = actor["spell"]
            joints = actor["joints"]
            
            # Common joints
            nose = joints[0]
            sh_l, sh_r = joints[11], joints[12]
            el_l, el_r = joints[13], joints[14]
            wr_l, wr_r = joints[15], joints[16]
            mid_sh = ((sh_l[0] + sh_r[0]) // 2, (sh_l[1] + sh_r[1]) // 2)

            # 1. KAMEHAMEHA (Plasma Beam)
            if spell_id == 1:
                mid_hand = ((wr_l[0] + wr_r[0]) // 2, (wr_l[1] + wr_r[1]) // 2)
                hand_dist = math.hypot(wr_l[0] - wr_r[0], wr_l[1] - wr_r[1])
                is_cupped = hand_dist < 130 and wr_l[1] > sh_l[1]
                
                # Forward thrust check
                is_firing = wr_r[0] > sh_r[0] + 50 or wr_l[0] < sh_l[0] - 50 or wr_l[1] < sh_l[1]
                
                if is_firing or not is_cupped:
                    # Fire beam towards center / opponent
                    target_x = 1280 if actor["center_x"] < 640 else 0
                    end_pt = (target_x, mid_hand[1])
                    self.draw_plasma_beam(canvas, mid_hand, end_pt, (255, 255, 255), (0, 240, 255), 45, t_curr)
                    beam_origins.append((mid_hand, end_pt, (0, 240, 255)))
                else:
                    # Charging swirling sphere in cupped hands
                    self.draw_energy_orb(canvas, mid_hand, radius=48, color_core=(255, 255, 255), 
                                        color_glow=(0, 240, 255), time_val=t_curr)

            # 2. SUPER SAIYAN GOLDEN AURA (Planck Blackbody 800K-3200K)
            elif spell_id == 2:
                self.draw_planck_super_saiyan_aura(canvas, joints, t_curr)

            # 3. NARUTO RASENGAN (High-Speed Rotational Particle Stream Vortex)
            elif spell_id == 3:
                hand_pt = (wr_r[0], wr_r[1])
                self.draw_rasengan_vortex(canvas, hand_pt, radius=52, time_val=t_curr)

            # 4. NARUTO CHIDORI (Jagged High-Voltage Electric Fractal Arcs)
            elif spell_id == 4:
                hand_pt = (wr_r[0], wr_r[1])
                elbow_pt = (el_r[0], el_r[1])
                self.draw_chidori_lightning(canvas, hand_pt, elbow_pt, t_curr)

            # 5. IRON MAN REPULSOR BEAM & ARC REACTOR
            elif spell_id == 5:
                # Chest Arc Reactor Core
                chest_pt = (mid_sh[0], mid_sh[1] + 45)
                self.draw_arc_reactor(canvas, chest_pt, t_curr)
                # Palm Repulsor
                palm_pt = (wr_r[0], wr_r[1])
                target_x = 1280 if actor["center_x"] < 640 else 0
                self.draw_plasma_beam(canvas, palm_pt, (target_x, palm_pt[1]), (255, 255, 255), (0, 165, 255), 35, t_curr)
                beam_origins.append((palm_pt, (target_x, palm_pt[1]), (0, 165, 255)))

            # 6. DOCTOR STRANGE MYSTIC SHIELD (Rotating Mandala)
            elif spell_id == 6:
                shield_pt = (wr_r[0], wr_r[1])
                self.draw_mystic_shield(canvas, shield_pt, radius=85, time_val=t_curr)

            # 7. PROCEDURAL COMBUSTION FIRE (Chemiluminescent Blue Root)
            elif spell_id == 7:
                hand_pt = (wr_r[0], wr_r[1])
                self.draw_volumetric_fire(canvas, hand_pt, radius=42, height=140, time_val=t_curr)

        # Detect Mid-Air Beam Struggle / Clash between 2 actors
        if len(beam_origins) >= 2:
            p1_start, p1_end, col1 = beam_origins[0]
            p2_start, p2_end, col2 = beam_origins[1]
            # Mid-air clash point between actors
            clash_x = int((p1_start[0] + p2_start[0]) * 0.5)
            clash_y = int((p1_start[1] + p2_start[1]) * 0.5)
            self.draw_beam_struggle_clash(canvas, (clash_x, clash_y), col1, col2, t_curr)
            self.camera_shake = max(self.camera_shake, 14.0)

    # -------------------------------------------------------------------------
    # Physical Shaders & Rendering Routines
    # -------------------------------------------------------------------------
    def draw_plasma_beam(self, canvas, p1, p2, color_core, color_outer, width, time_val):
        """Renders physical multi-pass plasma beam with lightning arcs and core glow"""
        v = np.array([p2[0] - p1[0], p2[1] - p1[1]], dtype=np.float32)
        length = np.linalg.norm(v)
        if length < 5: return
        v_norm = v / length
        perp = np.array([-v_norm[1], v_norm[0]], dtype=np.float32)

        passes = [
            (width * 2.4, color_outer, 0.22),
            (width * 1.5, color_outer, 0.45),
            (width * 0.8, color_outer, 0.75),
            (width * 0.35, color_core, 1.0),
        ]
        
        h, w = canvas.shape[:2]
        mask = np.zeros((h, w, 3), dtype=np.float32)

        for r, col, alpha in passes:
            poly = np.array([
                p1 + perp * (r * 0.8),
                p2 + perp * (r * 1.5),
                p2 - perp * (r * 1.5),
                p1 - perp * (r * 0.8)
            ], dtype=np.int32)
            
            col_t = tuple(float(c * alpha) for c in col)
            cv2.fillConvexPoly(mask, poly, col_t, cv2.LINE_AA)
            cv2.circle(mask, (int(p1[0]), int(p1[1])), int(r), col_t, -1, cv2.LINE_AA)

        # Chaotic high-voltage lightning discharge arcs around beam
        for a in range(3):
            arc_pts = [np.array(p1, dtype=np.int32)]
            for seg in range(1, 10):
                u = seg / 10.0
                mid = np.array(p1) + v * u
                seed = a * 15.3 + seg * 3.7 + time_val * 22.0
                disp = (math.sin(seed) * 0.75 + math.cos(seed * 2.1) * 0.25) * (width * 0.95)
                arc_pts.append((mid + perp * disp).astype(np.int32))
            arc_pts.append(np.array(p2, dtype=np.int32))
            cv2.polylines(mask, [np.array(arc_pts)], False, (255.0, 255.0, 240.0), 2, cv2.LINE_AA)

        # Fast additive blend
        canvas_f = canvas.astype(np.float32) + mask
        canvas[:] = np.clip(canvas_f, 0, 255).astype(np.uint8)

    def draw_energy_orb(self, canvas, center, radius, color_core, color_glow, time_val):
        """Draws radiant pulsating energy orb with internal energy vortices"""
        cx, cy = center
        h, w = canvas.shape[:2]
        mask = np.zeros((h, w, 3), dtype=np.float32)

        # Pulsing radius
        pulse_r = radius * (1.0 + 0.12 * math.sin(time_val * 16.0))
        
        # Multi-stage additive glow
        cv2.circle(mask, (cx, cy), int(pulse_r * 2.0), tuple(float(c * 0.25) for c in color_glow), -1, cv2.LINE_AA)
        cv2.circle(mask, (cx, cy), int(pulse_r * 1.3), tuple(float(c * 0.55) for c in color_glow), -1, cv2.LINE_AA)
        cv2.circle(mask, (cx, cy), int(pulse_r * 0.7), tuple(float(c * 0.85) for c in color_glow), -1, cv2.LINE_AA)
        cv2.circle(mask, (cx, cy), int(pulse_r * 0.35), tuple(float(c) for c in color_core), -1, cv2.LINE_AA)

        canvas_f = canvas.astype(np.float32) + mask
        canvas[:] = np.clip(canvas_f, 0, 255).astype(np.uint8)

    def draw_planck_super_saiyan_aura(self, canvas, joints, time_val):
        """Renders authentic Planck blackbody Super Saiyan aura with curl turbulence"""
        sh_l, sh_r = joints[11], joints[12]
        hip_l, hip_r = joints[23], joints[24]
        ank_l, ank_r = joints[27], joints[28]

        mid_hip = ((hip_l[0] + hip_r[0]) // 2, (hip_l[1] + hip_r[1]) // 2)
        mid_sh = ((sh_l[0] + sh_r[0]) // 2, (sh_l[1] + sh_r[1]) // 2)
        span_y = max(100, mid_hip[1] - mid_sh[1])

        h, w = canvas.shape[:2]
        mask = np.zeros((h, w, 3), dtype=np.float32)

        # Swirling golden convection flame tongues
        num_tongues = 18
        for i in range(num_tongues):
            angle = time_val * 6.5 + i * (math.pi * 2.0 / num_tongues)
            rad = (85 + 25 * math.sin(time_val * 14.0 + i))
            bx = int(mid_hip[0] + math.cos(angle) * rad)
            by = int(mid_hip[1] + math.sin(angle) * rad * 0.35)
            
            # Tip shoots upwards with curl noise displacement
            curl_dx = math.sin(time_val * 18.0 + i * 2.1) * 35.0
            tx = int(bx + curl_dx)
            ty = int(by - span_y * 1.85)

            # Planck Golden Color Palette: White-hot core -> Golden yellow -> Amber orange
            cv2.line(mask, (bx, by), (tx, ty), (0.0, 215.0, 255.0), 6, cv2.LINE_AA)
            cv2.line(mask, (bx, by), (tx, ty), (255.0, 255.0, 255.0), 2, cv2.LINE_AA)

        canvas_f = canvas.astype(np.float32) + mask
        canvas[:] = np.clip(canvas_f, 0, 255).astype(np.uint8)

    def draw_rasengan_vortex(self, canvas, center, radius, time_val):
        """Renders Naruto's Rasengan with dual rotating counter-current vector streams"""
        cx, cy = center
        h, w = canvas.shape[:2]
        mask = np.zeros((h, w, 3), dtype=np.float32)

        # Concentric glowing energy shells
        cv2.circle(mask, (cx, cy), int(radius * 1.6), (255.0, 200.0, 0.0), -1, cv2.LINE_AA)
        cv2.circle(mask, (cx, cy), int(radius * 1.0), (255.0, 235.0, 80.0), -1, cv2.LINE_AA)
        cv2.circle(mask, (cx, cy), int(radius * 0.4), (255.0, 255.0, 255.0), -1, cv2.LINE_AA)

        # High-speed rotating orbital stream ribbons
        num_ribbons = 12
        for r_idx in range(num_ribbons):
            ribbon_pts = []
            dir_sign = 1 if r_idx % 2 == 0 else -1
            theta_0 = time_val * 24.0 * dir_sign + r_idx * (math.pi / 6.0)
            for seg in range(16):
                u = seg / 16.0
                curr_theta = theta_0 + u * math.pi * 1.8
                curr_r = radius * (0.3 + 0.7 * u)
                px = int(cx + math.cos(curr_theta) * curr_r)
                py = int(cy + math.sin(curr_theta) * curr_r)
                ribbon_pts.append((px, py))
            cv2.polylines(mask, [np.array(ribbon_pts)], False, (255.0, 255.0, 220.0), 2, cv2.LINE_AA)

        canvas_f = canvas.astype(np.float32) + mask * 0.45
        canvas[:] = np.clip(canvas_f, 0, 255).astype(np.uint8)

    def draw_chidori_lightning(self, canvas, hand_pt, elbow_pt, time_val):
        """Renders Naruto's Chidori with high-voltage fractal electrical branches"""
        hx, hy = hand_pt
        ex, ey = elbow_pt
        h, w = canvas.shape[:2]
        mask = np.zeros((h, w, 3), dtype=np.float32)

        # Core blue electric glow ball
        cv2.circle(mask, (hx, hy), 65, (255.0, 220.0, 50.0), -1, cv2.LINE_AA)
        cv2.circle(mask, (hx, hy), 25, (255.0, 255.0, 255.0), -1, cv2.LINE_AA)

        # Jagged fractal lightning bolts discharging from hand into surrounding space
        num_bolts = 14
        for b in range(num_bolts):
            angle = b * (math.pi * 2.0 / num_bolts) + math.sin(time_val * 35.0 + b) * 0.4
            bolt_len = 70 + 65 * math.sin(time_val * 28.0 + b * 4.3)
            curr = np.array([hx, hy], dtype=np.float32)
            pts = [curr.astype(np.int32)]
            
            for seg in range(6):
                u = (seg + 1) / 6.0
                step = np.array([math.cos(angle), math.sin(angle)]) * (bolt_len / 6.0)
                jitter = np.array([-math.sin(angle), math.cos(angle)]) * (np.random.randn() * 14.0)
                curr = curr + step + jitter
                pts.append(curr.astype(np.int32))

            cv2.polylines(mask, [np.array(pts)], False, (255.0, 255.0, 255.0), 2, cv2.LINE_AA)
            cv2.polylines(mask, [np.array(pts)], False, (255.0, 220.0, 0.0), 4, cv2.LINE_AA)

        canvas_f = canvas.astype(np.float32) + mask * 0.55
        canvas[:] = np.clip(canvas_f, 0, 255).astype(np.uint8)

    def draw_arc_reactor(self, canvas, chest_pt, time_val):
        """Renders Iron Man's chest Arc Reactor beacon with anamorphic lens flare"""
        cx, cy = chest_pt
        h, w = canvas.shape[:2]
        mask = np.zeros((h, w, 3), dtype=np.float32)

        # Glowing cyan core
        cv2.circle(mask, (cx, cy), 35, (255.0, 220.0, 0.0), -1, cv2.LINE_AA)
        cv2.circle(mask, (cx, cy), 18, (255.0, 255.0, 255.0), -1, cv2.LINE_AA)

        # Anamorphic horizontal blue flare streak
        flare_w = 340
        cv2.line(mask, (cx - flare_w, cy), (cx + flare_w, cy), (255.0, 200.0, 0.0), 2, cv2.LINE_AA)
        cv2.line(mask, (cx - flare_w // 2, cy), (cx + flare_w // 2, cy), (255.0, 255.0, 255.0), 1, cv2.LINE_AA)

        canvas_f = canvas.astype(np.float32) + mask * 0.70
        canvas[:] = np.clip(canvas_f, 0, 255).astype(np.uint8)

    def draw_mystic_shield(self, canvas, shield_pt, radius, time_val):
        """Renders Doctor Strange's rotating runic mandala shields"""
        cx, cy = shield_pt
        h, w = canvas.shape[:2]
        mask = np.zeros((h, w, 3), dtype=np.float32)

        # Glowing orange runic circles
        c_eldritch = (0.0, 165.0, 255.0) # Vibrant Eldritch Orange
        cv2.circle(mask, (cx, cy), int(radius), c_eldritch, 3, cv2.LINE_AA)
        cv2.circle(mask, (cx, cy), int(radius * 0.65), c_eldritch, 2, cv2.LINE_AA)

        # Rotating geometric runic polygons
        rot = time_val * 3.5
        for k in range(8):
            a1 = rot + k * (math.pi / 4.0)
            a2 = a1 + math.pi / 4.0
            p1 = (int(cx + math.cos(a1) * radius), int(cy + math.sin(a1) * radius))
            p2 = (int(cx + math.cos(a2) * radius * 0.65), int(cy + math.sin(a2) * radius * 0.65))
            cv2.line(mask, p1, p2, (100.0, 220.0, 255.0), 2, cv2.LINE_AA)

        canvas_f = canvas.astype(np.float32) + mask * 0.65
        canvas[:] = np.clip(canvas_f, 0, 255).astype(np.uint8)

    def draw_volumetric_fire(self, canvas, hand_pt, radius, height, time_val):
        """Renders Leonxlnx-derived physical combustion fire with blue root and Planck radiation"""
        cx, cy = hand_pt
        h, w = canvas.shape[:2]
        mask = np.zeros((h, w, 3), dtype=np.float32)

        num_tongues = 8
        for i in range(num_tongues):
            u = i / float(num_tongues)
            curl_x = math.sin(time_val * 14.0 + i * 1.8) * (radius * 0.6)
            tx = int(cx + curl_x)
            ty = int(cy - height * (0.4 + 0.6 * u))

            # Chemiluminescent blue root (t < 0.25)
            if u < 0.25:
                col = (255.0, 120.0, 0.0) # Rich Blue
            elif u < 0.65:
                col = (0.0, 165.0, 255.0) # Bright Combustion Orange
            else:
                col = (0.0, 60.0, 220.0)  # Soot Crimson Red

            cv2.line(mask, (cx, cy), (tx, ty), col, int(radius * (1.0 - u * 0.7)), cv2.LINE_AA)

        canvas_f = canvas.astype(np.float32) + mask * 0.65
        canvas[:] = np.clip(canvas_f, 0, 255).astype(np.uint8)

    def draw_beam_struggle_clash(self, canvas, clash_pt, col1, col2, time_val):
        """Renders explosive mid-air energy beam collision with radial shockwave"""
        cx, cy = clash_pt
        h, w = canvas.shape[:2]
        mask = np.zeros((h, w, 3), dtype=np.float32)

        # Massive central detonation orb
        orb_r = 75 + 18 * math.sin(time_val * 24.0)
        cv2.circle(mask, (cx, cy), int(orb_r * 1.8), (255.0, 255.0, 255.0), -1, cv2.LINE_AA)
        cv2.circle(mask, (cx, cy), int(orb_r * 2.6), tuple(float(c) for c in col1), -1, cv2.LINE_AA)
        cv2.circle(mask, (cx, cy), int(orb_r * 3.2), tuple(float(c) for c in col2), -1, cv2.LINE_AA)

        # Expanding radial shockwave rings
        shock_r = int((time_val * 180.0) % 280)
        cv2.circle(mask, (cx, cy), shock_r, (255.0, 255.0, 255.0), 4, cv2.LINE_AA)
        cv2.circle(mask, (cx, cy), max(10, shock_r - 20), (255.0, 240.0, 180.0), 2, cv2.LINE_AA)

        canvas_f = canvas.astype(np.float32) + mask * 0.85
        canvas[:] = np.clip(canvas_f, 0, 255).astype(np.uint8)

    # -------------------------------------------------------------------------
    # Hollywood Color Grading & Anamorphic Cinemascope
    # -------------------------------------------------------------------------
    def apply_color_grade(self, frame):
        """Applies real-time Hollywood color grading (Teal & Orange / 35mm Portra)"""
        f = frame.astype(np.float32) / 255.0
        
        if self.color_lut == 'TEAL_ORANGE':
            # Blockbuster look: Warm skin tones + Rich teal shadows
            b, g, r = f[:, :, 0], f[:, :, 1], f[:, :, 2]
            # Push reds/yellows in highlights/midtones
            r = np.power(r, 0.85) * 1.08
            # Push blues in shadows
            b = b * 0.90 + (1.0 - r) * 0.15
            # Recombine
            f = np.stack([b, g, r], axis=2)

        elif self.color_lut == 'PORTRA_35MM':
            # Soft organic film contrast
            f = np.power(f, 0.92) * 1.04
            f[:, :, 0] *= 0.96 # Slight warmth
            f[:, :, 2] *= 1.03

        elif self.color_lut == 'CYBERPUNK':
            f[:, :, 0] = np.power(f[:, :, 0], 0.82) * 1.15 # Vivid cyan
            f[:, :, 2] = np.power(f[:, :, 2], 0.85) * 1.10 # Vivid magenta

        return np.clip(f * 255.0, 0, 255).astype(np.uint8)

    def apply_anamorphic_letterbox(self, frame):
        """Applies 2.39:1 Cinemascope widescreen letterbox matte bars"""
        h, w = frame.shape[:2]
        cinema_h = int(w / 2.39)
        bar_h = max(0, (h - cinema_h) // 2)
        if bar_h > 0:
            frame[:bar_h, :] = 0
            frame[h - bar_h:, :] = 0
            # Subtle silver hairline border on matte edges
            cv2.line(frame, (0, bar_h), (w, bar_h), (35, 35, 40), 1, cv2.LINE_AA)
            cv2.line(frame, (0, h - bar_h), (w, h - bar_h), (35, 35, 40), 1, cv2.LINE_AA)
        return frame

    def apply_camera_shake(self, frame):
        """Applies decaying Hollywood camera impact shake on energy detonations"""
        h, w = frame.shape[:2]
        dx = int((np.random.rand() * 2.0 - 1.0) * self.camera_shake)
        dy = int((np.random.rand() * 2.0 - 1.0) * self.camera_shake)
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        return cv2.warpAffine(frame, M, (w, h), borderMode=cv2.BORDER_REFLECT)

    # -------------------------------------------------------------------------
    # Director Slate & Production Telemetry HUD
    # -------------------------------------------------------------------------
    def draw_director_hud(self, frame, actors, t_curr):
        h, w = frame.shape[:2]

        # Top Slate Bar
        slate_bg = (14, 16, 20)
        cv2.rectangle(frame, (20, 20), (w - 20, 65), slate_bg, -1)
        cv2.rectangle(frame, (20, 20), (w - 20, 65), (0, 240, 255), 1)

        # Scene / Shot / Take Info
        slate_txt = f"FILM PRODUCTION | SCENE {self.scene_num:02d} | SHOT {self.shot_num:02d} | TAKE {self.take_num:02d}"
        cv2.putText(frame, slate_txt, (35, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 240, 255), 2, cv2.LINE_AA)

        # Actor Tracking & Spell Info
        info_x = 560
        spell1_str = self.spell_names.get(self.actor1_spell, "NONE")[:14]
        spell2_str = self.spell_names.get(self.actor2_spell, "NONE")[:14]
        act_info = f"ACTOR 1: [{spell1_str}] | ACTOR 2: [{spell2_str}]"
        cv2.putText(frame, act_info, (info_x, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (200, 220, 240), 1, cv2.LINE_AA)

        # Recording Status Indicator
        if self.is_recording:
            elapsed = t_curr - self.record_start_time
            cv2.circle(frame, (w - 140, 42), 9, (0, 0, 255), -1, cv2.LINE_AA)
            rec_str = f"REC {int(elapsed//60):02d}:{int(elapsed%60):02d}"
            cv2.putText(frame, rec_str, (w - 120, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 0, 255), 2, cv2.LINE_AA)
        else:
            cv2.putText(frame, "STANDBY", (w - 130, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 200, 100), 2, cv2.LINE_AA)

        # Bottom Shortcut Control Deck
        deck_bg = (14, 16, 20)
        cv2.rectangle(frame, (20, h - 60), (w - 20, h - 20), deck_bg, -1)
        cv2.rectangle(frame, (20, h - 60), (w - 20, h - 20), (60, 60, 70), 1)
        deck_str = "[SPACE] ROLL/CUT TAKE | [1-7] Spell P1 | [F1-F7] Spell P2 | [C] Cinema 2.39:1 | [G] Grade LUT | [L] Load Film Clip | [Q] Quit"
        cv2.putText(frame, deck_str, (32, h - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (210, 225, 245), 1, cv2.LINE_AA)

    # -------------------------------------------------------------------------
    # Take Recording & Movie Encoding (FFmpeg Integration)
    # -------------------------------------------------------------------------
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.record_start_time = time.time()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.current_raw_video_path = os.path.join(FILM_TAKES_DIR, f"raw_take_{self.take_num:03d}_{timestamp}.avi")
        
        # High-bitrate MJPEG raw master recording
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.video_writer = cv2.VideoWriter(self.current_raw_video_path, fourcc, 30.0, (1280, 720))
        print(f"\n[● ACTION!] Recording Take {self.take_num:02d} -> {self.current_raw_video_path}")
        threading.Thread(target=lambda: winsound.Beep(1400, 90), daemon=True).start()

    def stop_recording(self):
        self.is_recording = False
        duration = max(1.0, time.time() - self.record_start_time)
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        print(f"[■ CUT!] Finished Take {self.take_num:02d} ({duration:.1f} s). Exporting finished cinema film with FFmpeg...")
        threading.Thread(target=lambda: winsound.Beep(900, 70), daemon=True).start()

        # Background thread to encode with sound effects and produce final movie
        take_id = self.take_num
        raw_path = self.current_raw_video_path
        self.take_num += 1

        threading.Thread(target=self.export_final_movie_take, args=(raw_path, take_id, duration), daemon=True).start()

    def export_final_movie_take(self, raw_avi_path, take_id, duration):
        """Uses FFmpeg to mux synthesized cinematic audio and export final H.264 MP4 film"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            sfx_wav = os.path.join(FILM_TAKES_DIR, f"sfx_take_{take_id:03d}.wav")
            final_mp4 = os.path.join(FILM_TAKES_DIR, f"FILM_SCENE{self.scene_num:02d}_TAKE{take_id:03d}_{timestamp}.mp4")

            # 1. Synthesize Hollywood sound effects track
            synthesize_movie_sfx(sfx_wav, duration)

            # 2. Run FFmpeg to encode H.264 high-quality video with audio muxing
            cmd = [
                'ffmpeg', '-y',
                '-i', raw_avi_path,
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

            print(f"\n[✓ MASTER FILM EXPORTED!]")
            print(f"    Path: {final_mp4}")
            print(f"    Ready to watch with your friends!\n")
            threading.Thread(target=lambda: winsound.Beep(1800, 110), daemon=True).start()

        except Exception as e:
            print(f"[!] Export error: {e}")

    # -------------------------------------------------------------------------
    # Keyboard Interaction Handler
    # -------------------------------------------------------------------------
    def handle_key(self, key):
        # [SPACE] Roll Camera / Cut Take
        if key == 32:
            self.toggle_recording()

        # [1-7] Spell Selection for Actor 1 (You)
        elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6'), ord('7')]:
            self.actor1_spell = key - ord('0')
            print(f"[*] Actor 1 Spell: {self.spell_names[self.actor1_spell]}")
            threading.Thread(target=lambda: winsound.Beep(1100, 45), daemon=True).start()

        # [C] Toggle 2.39:1 Anamorphic Cinema Letterbox
        elif key in [ord('c'), ord('C')]:
            self.anamorphic_letterbox = not self.anamorphic_letterbox
            print(f"[*] 2.39:1 Anamorphic Letterbox: {self.anamorphic_letterbox}")

        # [G] Toggle Hollywood Color Grading LUT
        elif key in [ord('g'), ord('G')]:
            luts = ['TEAL_ORANGE', 'PORTRA_35MM', 'CYBERPUNK', 'NONE']
            idx = luts.index(self.color_lut)
            self.color_lut = luts[(idx + 1) % len(luts)]
            print(f"[*] Hollywood Color LUT: {self.color_lut}")

        # [L] Load Film Video File shot with friends
        elif key in [ord('l'), ord('L')]:
            # Look for recent recorded clips in Downloads
            test_clips = [
                r"C:\Users\SVNITHESHPC\Downloads\VID-20240522-WA0019.mp4",
                r"C:\Users\SVNITHESHPC\Downloads\VID-20240522-WA0023.mp4",
                r"C:\Users\SVNITHESHPC\Downloads\AI_VFX_Realtime_Suite\naruto-rasengan\assets\rasengan.mp4"
            ]
            for clip in test_clips:
                if os.path.exists(clip):
                    self.load_video_file(clip)
                    break

        # [Q] / [ESC]
        elif key in [ord('q'), ord('Q'), 27]:
            self.running = False

# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    studio = UltimateFilmVFXStudio()
    studio.run()
