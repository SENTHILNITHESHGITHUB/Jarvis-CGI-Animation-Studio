"""
================================================================================
NATIVE CHARACTER MOTION CAPTURE & CGI ANIMATION STUDIO
================================================================================
Powered by MediaPipe Native Vision, OpenCV DirectShow 60 FPS Engine,
and PolinniZhong/character-asset-kit Multi-Character Architecture.

Features:
- 100% Native Desktop Application (Zero Web, Zero Browser lag)
- Ultra-Low Latency 3D Body MoCap (33 World-Space Skeletal Joints)
- Real-Time Kinematic Mapping to 3D Characters:
    [1] 3D Goku (Super Saiyan Master) with Spiky Golden Hair & Martial Arts Gi
    [2] 3D Vegeta (Royal Saiyan Prince) with Battle Armor & Royal Blue Aura
    [3] 3D Cyber Warrior (Nanotech Exoskeleton & Arc Reactor Core)
    [4] 3D BlindBox Chibi Figurine (character-asset-kit gates-blindbox3d-v1)
    [5] 3D GLB Asset (Doraemon / Nobita Imported Model)
- Multi-View Cinema Layouts ([V] Key):
    * Side-by-Side Studio (Camera Left | 3D Character Right)
    * Holographic AR Overlay (Character overlaid directly onto you)
    * Pure 3D Cinema (Full 3D Stage with 360° Orbit)
- Real-Time Gesture & Stance Detection:
    * Kamehameha Cupped Hands -> Charges Swirling Ki Energy Sphere
    * High Guard / Martial Stance
    * Punch & Kick Velocity Tracking with Audio Swooshes
- Character Asset Kit Integration:
    * Export Multi-View Turnaround Asset Sheet ([S])
    * Record Motion Capture Takes ([T])
================================================================================
"""

import os
import sys
import time
import math
import queue
import threading
import winsound
import numpy as np
import cv2

# Set UTF-8 encoding for standard output
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Verify MediaPipe and Task Landmarker
try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
except ImportError:
    print("[!] Error: MediaPipe tasks API is required. Please install via: pip install mediapipe")
    sys.exit(1)

# Paths to models
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSE_MODEL_PATHS = [
    os.path.join(r"C:\Users\SVNITHESHPC\Downloads\AI_VFX_Realtime_Suite", "pose_landmarker.task"),
    os.path.join(BASE_DIR, "pose_landmarker.task"),
    r"C:\Users\SVNITHESHPC\Downloads\GestureControlSuite\pose_landmarker.task"
]

pose_model_file = None
for p in POSE_MODEL_PATHS:
    if os.path.exists(p):
        pose_model_file = p
        break

if not pose_model_file:
    print(f"[!] Warning: pose_landmarker.task not found in standard paths. Checked: {POSE_MODEL_PATHS}")
    # Search Downloads
    search_dir = r"C:\Users\SVNITHESHPC\Downloads"
    for root, dirs, files in os.walk(search_dir):
        if "pose_landmarker.task" in files:
            pose_model_file = os.path.join(root, "pose_landmarker.task")
            break

print(f"[*] Native MoCap Engine initializing with model: {pose_model_file}")

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
# 3D Math & Perspective Projection Utility
# -----------------------------------------------------------------------------
class Camera3D:
    def __init__(self, width=640, height=720, fov=55.0):
        self.width = width
        self.height = height
        self.fov = fov
        self.update_intrinsics()

    def update_intrinsics(self):
        f = (self.width / 2.0) / math.tan(math.radians(self.fov / 2.0))
        self.K = np.array([
            [f, 0, self.width / 2.0],
            [0, f, self.height / 2.0],
            [0, 0, 1.0]
        ], dtype=np.float32)

    def project(self, pt3d):
        """Project (x, y, z) in camera coordinates to (u, v) screen pixel"""
        x, y, z = pt3d[0], pt3d[1], max(0.05, pt3d[2])
        u = int(self.K[0, 0] * (x / z) + self.K[0, 2])
        v = int(self.K[1, 1] * (y / z) + self.K[1, 2])
        return (u, v)

# -----------------------------------------------------------------------------
# 3D Character Renderer (Shaded Cylinders, Spheres, Hair Spikes, Accessories)
# -----------------------------------------------------------------------------
class Character3DRenderer:
    def __init__(self, camera):
        self.cam = camera
        self.light_dir = np.array([0.35, -0.85, -0.45], dtype=np.float32)
        self.light_dir /= np.linalg.norm(self.light_dir)

    def rotate_point_y(self, p, angle_rad, center=np.array([0, 0, 0], dtype=np.float32)):
        c, s = math.cos(angle_rad), math.sin(angle_rad)
        shifted = p - center
        rx = shifted[0] * c + shifted[2] * s
        rz = -shifted[0] * s + shifted[2] * c
        return np.array([rx, shifted[1], rz], dtype=np.float32) + center

    def draw_shaded_limb(self, canvas, p1, p2, radius, color, taper=0.92, sides=10):
        """Renders an anatomical shaded 3D tapered cylinder with Lambertian diffuse shading"""
        v = p2 - p1
        length = np.linalg.norm(v)
        if length < 1e-4:
            return
        v_norm = v / length

        ref = np.array([0, 1, 0], dtype=np.float32) if abs(v_norm[1]) < 0.9 else np.array([1, 0, 0], dtype=np.float32)
        u1 = np.cross(v_norm, ref)
        u1 /= np.linalg.norm(u1)
        u2 = np.cross(v_norm, u1)

        angles = np.linspace(0, 2 * math.pi, sides, endpoint=False)
        circle_pts = np.array([math.cos(a) * u1 + math.sin(a) * u2 for a in angles], dtype=np.float32)

        ring1 = p1 + circle_pts * radius
        ring2 = p2 + circle_pts * (radius * taper)

        proj1 = [self.cam.project(pt) for pt in ring1]
        proj2 = [self.cam.project(pt) for pt in ring2]

        quads = []
        for i in range(sides):
            nxt = (i + 1) % sides
            mid_z = (ring1[i][2] + ring1[nxt][2] + ring2[i][2] + ring2[nxt][2]) * 0.25
            norm = (circle_pts[i] + circle_pts[nxt]) * 0.5
            norm /= np.linalg.norm(norm)

            diffuse = max(0.22, float(np.dot(norm, -self.light_dir)))
            c = tuple(int(min(255, max(0, ch * diffuse))) for ch in color)
            poly = np.array([proj1[i], proj1[nxt], proj2[nxt], proj2[i]], dtype=np.int32)
            quads.append((mid_z, poly, c))

        # Painter's sort (back to front)
        quads.sort(key=lambda q: q[0], reverse=True)
        for _, poly, c in quads:
            cv2.fillConvexPoly(canvas, poly, c, cv2.LINE_AA)

    def draw_shaded_sphere(self, canvas, center, radius, color, rings=7, sectors=10):
        """Renders a 3D lit sphere for joints, head, and fists"""
        c_proj = self.cam.project(center)
        # Fast 2D radius estimate
        r_screen = max(2, int((self.cam.K[0, 0] * radius) / max(0.1, center[2])))

        # Draw smooth shaded sphere using radial gradient rings
        highlight_offset = np.array([-r_screen * 0.25, -r_screen * 0.25], dtype=np.float32)
        center_hl = (int(c_proj[0] + highlight_offset[0]), int(c_proj[1] + highlight_offset[1]))

        # Base circle
        cv2.circle(canvas, c_proj, r_screen, tuple(int(ch * 0.5) for ch in color), -1, cv2.LINE_AA)
        # Mid diffuse
        cv2.circle(canvas, (int((c_proj[0] + center_hl[0])*0.5), int((c_proj[1] + center_hl[1])*0.5)), 
                   int(r_screen * 0.75), color, -1, cv2.LINE_AA)
        # Specular shine
        bright_c = tuple(min(255, int(ch * 1.45)) for ch in color)
        cv2.circle(canvas, center_hl, max(1, int(r_screen * 0.35)), bright_c, -1, cv2.LINE_AA)

    def draw_hair_spike(self, canvas, base_pt, tip_pt, width, color):
        """Renders iconic 3D anime hair spikes (Goku/Vegeta)"""
        b_proj = self.cam.project(base_pt)
        t_proj = self.cam.project(tip_pt)

        v = tip_pt - base_pt
        length = np.linalg.norm(v)
        if length < 1e-4:
            return
        
        # Perpendicular screen vector
        dx, dy = t_proj[0] - b_proj[0], t_proj[1] - b_proj[1]
        dist = math.hypot(dx, dy)
        if dist < 1e-3:
            return
        px, py = -dy / dist * width, dx / dist * width

        p1 = (int(b_proj[0] + px), int(b_proj[1] + py))
        p2 = (int(b_proj[0] - px), int(b_proj[1] - py))
        p3 = t_proj

        pts = np.array([p1, p2, p3], dtype=np.int32)
        # Outer darker outline for anime look
        cv2.polylines(canvas, [pts], True, (20, 20, 20), 2, cv2.LINE_AA)
        cv2.fillConvexPoly(canvas, pts, color, cv2.LINE_AA)

# -----------------------------------------------------------------------------
# Main Native Studio Class
# -----------------------------------------------------------------------------
class NativeCharacterMoCapStudio:
    def __init__(self):
        # Window & Video properties
        self.win_name = "Native Character MoCap Studio | PolinniZhong Character-Asset-Kit"
        self.win_w = 1280
        self.win_h = 720
        self.running = True

        # View Modes:
        # 'SPLIT' = Left: Cam | Right: 3D Character
        # 'AR'    = Character overlaid directly on Camera scene
        # 'CINEMA'= Fullscreen 3D Character Stage
        self.view_mode = 'SPLIT' 
        self.stage_bg = 'DOJO' # 'DOJO', 'TIME_CHAMBER', 'CYBER', 'VOID', 'CAM'

        # Character Selection
        # 1: Goku SSJ, 2: Vegeta, 3: Cyber Warrior, 4: BlindBox Chibi, 5: GLB 3D
        self.char_idx = 1
        self.char_names = {
            1: "KR-04 HOU SHU (ANCIENT GUFENG SCHOLAR - CHARACTER ASSET KIT)",
            2: "3D GOKU (SUPER SAIYAN MASTER)",
            3: "3D VEGETA (ROYAL SAIYAN PRINCE)",
            4: "3D CYBER WARRIOR (NANOTECH)",
            5: "3D BLINDBOX CHIBI (GATES-BLINDBOX3D-V1)"
        }

        # 360° Turntable Orbit
        self.turntable_active = False
        self.turntable_angle = 0.0

        # Features & Options
        self.show_skeleton = True
        self.show_aura = True
        self.show_hud = True
        self.recording_take = False
        self.show_sheet_preview = False
        self.sheet_img = None
        sheet_path = r"C:\Users\SVNITHESHPC\.gemini\antigravity\brain\972199e1-0395-45a5-b415-be1edfa58c26\character_asset_kit_showcase_houshu.png"
        if os.path.exists(sheet_path):
            self.sheet_img = cv2.imread(sheet_path)

        # Load Hou Shu Photorealistic Action & Turnaround Sprites
        self.houshu_sprites = {}
        sprites_dir = r"C:\Users\SVNITHESHPC\Downloads\AI_VFX_Realtime_Suite\assets\houshu_cutouts"
        if os.path.exists(sprites_dir):
            for fname in os.listdir(sprites_dir):
                if fname.endswith(".png"):
                    key = fname[:-4]
                    sp = cv2.imread(os.path.join(sprites_dir, fname), cv2.IMREAD_UNCHANGED)
                    if sp is not None:
                        self.houshu_sprites[key] = sp
        print(f"[*] Loaded {len(self.houshu_sprites)} photorealistic Hou Shu sprites from character-asset-kit.")
        self.recorded_frames = []

        # Kinetic / Stance Detection
        self.cupped_hands = False
        self.ki_charge_ratio = 0.0
        self.punch_speed_l = 0.0
        self.punch_speed_r = 0.0
        self.last_lw = None
        self.last_rw = None

        # Camera & 3D Setup
        self.cam3d = Camera3D(width=640, height=720, fov=52.0)
        self.renderer = Character3DRenderer(self.cam3d)

        # Filters for all 33 landmarks
        self.filters = [OneEuroFilter3D(min_cutoff=1.8, beta=0.03) for _ in range(33)]

        # Background Pre-renders
        self.init_stage_backgrounds()

        # Initialize MediaPipe Task
        self.init_mediapipe_landmarker()

        # Camera Capture
        self.init_camera()

    def init_stage_backgrounds(self):
        """Creates high-fidelity cinema backdrops for the character stage"""
        w, h = 640, 720
        # 1. Cinema Dojo (Polished wooden floor & warm lighting)
        self.bg_dojo = np.zeros((h, w, 3), dtype=np.uint8)
        horizon = int(h * 0.60)
        # Wall gradient (deep slate charcoal to warm dark amber)
        for y in range(horizon):
            u = y / horizon
            c = (int(35 + 25 * u), int(32 + 20 * u), int(42 + 15 * u))
            self.bg_dojo[y, :] = c
        # Wooden floor planks with perspective lines
        for y in range(horizon, h):
            u = (y - horizon) / (h - horizon)
            c = (int(28 + 40 * u), int(45 + 55 * u), int(75 + 70 * u)) # Rich wood tones
            self.bg_dojo[y, :] = c
        # Perspective floor seams
        for x in np.linspace(-w * 0.5, w * 1.5, 14):
            cv2.line(self.bg_dojo, (w // 2, horizon), (int(x), h), (20, 35, 60), 1, cv2.LINE_AA)
        cv2.line(self.bg_dojo, (0, horizon), (w, horizon), (50, 75, 110), 2, cv2.LINE_AA)

        # 2. Hyperbolic Time Chamber (Endless pristine white void with golden horizon)
        self.bg_chamber = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            u = y / h
            c = (int(235 + 20 * (1 - u)), int(238 + 17 * (1 - u)), int(245 + 10 * (1 - u)))
            self.bg_chamber[y, :] = c
        for x in np.linspace(-w * 0.3, w * 1.3, 10):
            cv2.line(self.bg_chamber, (w // 2, horizon), (int(x), h), (210, 215, 225), 1, cv2.LINE_AA)

        # 3. Cyber Matrix Grid
        self.bg_cyber = np.zeros((h, w, 3), dtype=np.uint8)
        self.bg_cyber[:] = (15, 12, 18)
        for y in range(horizon, h, 28):
            cv2.line(self.bg_cyber, (0, y), (w, y), (80, 50, 20), 1, cv2.LINE_AA)
        for x in np.linspace(-w * 0.4, w * 1.4, 16):
            cv2.line(self.bg_cyber, (w // 2, horizon), (int(x), h), (180, 100, 30), 1, cv2.LINE_AA)

    def init_mediapipe_landmarker(self):
        base_options = python.BaseOptions(model_asset_path=pose_model_file)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.55,
            min_tracking_confidence=0.55
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def init_camera(self):
        self.cap = None
        # Auto-discover working camera (Cam 1 -> Cam 0 -> Cam 2)
        for idx in [1, 0, 2]:
            try:
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.cap = cap
                        self.cam_idx = idx
                        print(f"[*] Successfully connected to Camera Index [{idx}] at 640x480 DirectShow.")
                        return
                    cap.release()
            except Exception:
                pass

        if self.cap is None:
            print("[!] Warning: Could not open webcam directly. Creating synthetic fallback feed.")

    def run(self):
        cv2.namedWindow(self.win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.win_name, self.win_w, self.win_h)

        print("\n========================================================")
        print(" NATIVE CHARACTER MOCAP STUDIO ACTIVE")
        print(" [1-5] Switch Character (Goku SSJ, Vegeta, Cyber, BlindBox, Doraemon)")
        print(" [V]   Toggle View Mode (Split-Screen / AR Overlay / Full 3D Cinema)")
        print(" [B]   Toggle Stage Background (Dojo, Time Chamber, Cyber, Cam)")
        print(" [O]   Toggle 360° Turntable Orbit")
        print(" [M]   Toggle Skeleton Tracking Lines")
        print(" [A]   Toggle Energy Aura VFX")
        print(" [S]   Save Multi-View Asset Turnaround Sheet")
        print(" [T]   Record Motion Take (character-asset-kit)")
        print(" [H]   Toggle HUD")
        print(" [Q]   Quit")
        print("========================================================\n")

        # Soft audio chime on startup
        threading.Thread(target=lambda: winsound.Beep(980, 90), daemon=True).start()

        start_time = time.time()
        frame_idx = 0

        while self.running:
            t_curr = time.time()
            timestamp_ms = int((t_curr - start_time) * 1000)
            frame_idx += 1

            # Read camera frame
            if self.cap and self.cap.isOpened():
                ret, cam_frame = self.cap.read()
                if not ret or cam_frame is None:
                    cam_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            else:
                cam_frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # Mirror webcam horizontally for intuitive mirroring
            cam_frame = cv2.flip(cam_frame, 1)

            # Resize to fit studio half (640, 720) with aspect preservation
            cam_h, cam_w = cam_frame.shape[:2]
            scale = 720.0 / cam_h
            scaled_w = int(cam_w * scale)
            resized_cam = cv2.resize(cam_frame, (scaled_w, 720))
            crop_start = max(0, (scaled_w - 640) // 2)
            cam_display = resized_cam[:, crop_start:crop_start+640].copy()

            # Process PoseLandmarker in RGB
            rgb_frame = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            pose_result = None
            try:
                pose_result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
            except Exception as e:
                pass

            # Extract & Filter 3D Joint Positions
            joints_3d = self.process_landmarks(pose_result, timestamp_ms, t_curr)

            # Create Character Stage Canvas (640 x 720)
            stage_canvas = self.get_stage_background(cam_display)

            # Update Turntable Orbit
            if self.turntable_active:
                self.turntable_angle += 0.025
            else:
                self.turntable_angle = 0.0

            # Render 3D Character Rig onto Stage Canvas
            if joints_3d is not None:
                self.render_character(stage_canvas, joints_3d, t_curr)
                if self.show_skeleton:
                    self.render_mocap_skeleton_overlay(cam_display, joints_3d)

            # Combine Views according to Layout Mode
            final_canvas = self.assemble_final_view(cam_display, stage_canvas, joints_3d, t_curr)

            # Draw HUD & Telemetry
            if self.show_hud:
                self.draw_hud(final_canvas, joints_3d, t_curr)

            # Display Native OpenCV Window
            cv2.imshow(self.win_name, final_canvas)

            # Handle Keyboard Input
            key = cv2.waitKey(1) & 0xFF
            if key != 255:
                self.handle_key(key, final_canvas, joints_3d)

            # Window close check
            if cv2.getWindowProperty(self.win_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        # Cleanup
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("[*] Native Character MoCap Studio closed cleanly.")

    def process_landmarks(self, pose_result, timestamp_ms, t_curr):
        """Extracts and smooths 33 body joints in 3D metric camera space"""
        if not pose_result or not pose_result.pose_world_landmarks or len(pose_result.pose_world_landmarks) == 0:
            return None

        raw_landmarks = pose_result.pose_world_landmarks[0]
        smoothed_joints = []

        # Coordinate conversion:
        # MediaPipe world coordinates: X is right, Y is down/up, Z is depth from hips.
        # Scale into meters and center at scene origin
        for i, lm in enumerate(raw_landmarks):
            # Mirror X so right arm mirrors user's right arm intuitively
            raw_pt = np.array([-lm.x, lm.y, lm.z], dtype=np.float32)
            filtered_pt = self.filters[i].filter(raw_pt, timestamp_ms / 1000.0)
            smoothed_joints.append(filtered_pt)

        # Joint 3D offsets relative to hip center
        mid_hip = (smoothed_joints[23] + smoothed_joints[24]) * 0.5
        # Place character at distance Z = 2.45m in front of camera
        offset = np.array([0.0, 0.15, 2.45], dtype=np.float32)

        final_joints = [j - mid_hip + offset for j in smoothed_joints]

        # Detect Velocity & Martial Arts Punches
        lw = final_joints[15]
        rw = final_joints[16]
        if self.last_lw is not None:
            self.punch_speed_l = np.linalg.norm(lw - self.last_lw) * 60.0 # m/s
            self.punch_speed_r = np.linalg.norm(rw - self.last_rw) * 60.0
            if max(self.punch_speed_l, self.punch_speed_r) > 4.5:
                # Fast punch swoosh sound
                threading.Thread(target=lambda: winsound.Beep(750, 40), daemon=True).start()
        self.last_lw = lw.copy()
        self.last_rw = rw.copy()

        # Cupped Hands (Kamehameha Detection)
        hand_dist = np.linalg.norm(lw - rw)
        shoulders_y = (final_joints[11][1] + final_joints[12][1]) * 0.5
        if hand_dist < 0.22 and lw[1] > shoulders_y:
            self.cupped_hands = True
            self.ki_charge_ratio = min(1.0, self.ki_charge_ratio + 0.05)
        else:
            self.cupped_hands = False
            self.ki_charge_ratio = max(0.0, self.ki_charge_ratio - 0.08)

        # Record Take
        if self.recording_take:
            self.recorded_frames.append({
                "time": t_curr,
                "joints": [j.tolist() for j in final_joints]
            })

        return final_joints

    def get_stage_background(self, cam_display):
        if self.stage_bg == 'DOJO':
            return self.bg_dojo.copy()
        elif self.stage_bg == 'TIME_CHAMBER':
            return self.bg_chamber.copy()
        elif self.stage_bg == 'CYBER':
            return self.bg_cyber.copy()
        elif self.stage_bg == 'CAM':
            return cam_display.copy()
        else: # VOID
            return np.zeros((720, 640, 3), dtype=np.uint8)

    def overlay_sprite(self, canvas, sprite_rgba, center_x, bottom_y, target_height):
        # Alpha-blends a photorealistic RGBA sprite onto the stage canvas with contact shadow
        if sprite_rgba is None:
            return
        sh, sw = sprite_rgba.shape[:2]
        aspect = sw / max(1, sh)
        target_width = int(target_height * aspect)

        resized = cv2.resize(sprite_rgba, (target_width, target_height), interpolation=cv2.INTER_AREA)

        x1 = center_x - target_width // 2
        x2 = x1 + target_width
        y2 = bottom_y
        y1 = y2 - target_height

        ch, cw = canvas.shape[:2]
        src_x1 = max(0, -x1)
        src_y1 = max(0, -y1)
        src_x2 = target_width - max(0, x2 - cw)
        src_y2 = target_height - max(0, y2 - ch)

        dst_x1 = max(0, x1)
        dst_y1 = max(0, y1)
        dst_x2 = min(cw, x2)
        dst_y2 = min(ch, y2)

        if dst_x2 <= dst_x1 or dst_y2 <= dst_y1:
            return

        crop_sprite = resized[src_y1:src_y2, src_x1:src_x2]
        rgb = crop_sprite[:, :, :3]
        alpha = (crop_sprite[:, :, 3].astype(np.float32) / 255.0)[:, :, np.newaxis]

        # Ground contact shadow
        shadow_w = int(target_width * 0.70)
        shadow_h = int(target_height * 0.045)
        shadow_center = (center_x, bottom_y - 6)
        cv2.ellipse(canvas, shadow_center, (max(1, shadow_w // 2), max(1, shadow_h // 2)), 
                    0, 0, 360, (20, 22, 28), -1, cv2.LINE_AA)

        canvas_roi = canvas[dst_y1:dst_y2, dst_x1:dst_x2]
        canvas[dst_y1:dst_y2, dst_x1:dst_x2] = (rgb * alpha + canvas_roi * (1.0 - alpha)).astype(np.uint8)

    def render_houshu_kinematic(self, canvas, joints, t_curr):
        # Kinematically maps 33 MediaPipe joints to Hou Shu photorealistic poses from character-asset-kit
        if not self.houshu_sprites:
            return

        nose = joints[0]
        sh_l, sh_r = joints[11], joints[12]
        el_l, el_r = joints[13], joints[14]
        wr_l, wr_r = joints[15], joints[16]
        hip_l, hip_r = joints[23], joints[24]
        kn_l, kn_r = joints[25], joints[26]
        ank_l, ank_r = joints[27], joints[28]

        mid_sh = (sh_l + sh_r) * 0.5
        mid_hip = (hip_l + hip_r) * 0.5

        # Compute Body Yaw Angle
        dx_sh = sh_r[0] - sh_l[0]
        dz_sh = sh_r[2] - sh_l[2]
        yaw_deg = math.degrees(math.atan2(dz_sh, dx_sh))

        # Project 3D Screen Center
        pt_hip = self.cam3d.project(mid_hip)
        pt_sh = self.cam3d.project(mid_sh)
        pt_ank = self.cam3d.project((ank_l + ank_r) * 0.5)

        center_x = pt_hip[0]
        bottom_y = max(pt_ank[1] + 20, int(canvas.shape[0] * 0.92))
        fig_height = max(260, min(680, int((bottom_y - pt_sh[1]) * 1.55)))

        # Gesture Detection for Action Poses:
        selected_key = "master_standing"

        # 1. Waving Pose (A1): Right hand raised high above shoulder
        if wr_r[1] < sh_r[1] - 0.08:
            selected_key = "pose_a1_wave"
        # 2. Greeting / Polite Bow (A2): Hands clasped together near chest
        elif np.linalg.norm(wr_l - wr_r) < 0.22 and wr_l[1] > mid_sh[1] and wr_l[1] < mid_hip[1]:
            selected_key = "pose_a2_greet"
        # 3. Open Palms (A3): Both arms outstretched wide laterally
        elif wr_l[0] < el_l[0] - 0.08 and wr_r[0] > el_r[0] + 0.08:
            selected_key = "pose_a3_open_palms"
        # 4. Crossed Arms (A4): Forearms crossed across torso
        elif wr_l[0] > mid_sh[0] and wr_r[0] < mid_sh[0]:
            selected_key = "pose_a4_crossed_arms"
        # 5. Chin Resting (A5): Hand touching jaw / chin
        elif np.linalg.norm(wr_r - nose) < 0.20 or np.linalg.norm(wr_l - nose) < 0.20:
            selected_key = "pose_a5_chin_rest"
        # 6. Holding Fan Prop: Hands cupped / fanning gesture
        elif self.cupped_hands:
            selected_key = "pose_prop_fan"
        # 7. Holding Book Prop: Left hand raised holding reading pose
        elif wr_l[1] < mid_sh[1] + 0.05 and wr_r[1] > mid_sh[1] + 0.15:
            selected_key = "pose_prop_book"
        # 8. Holding Brush Prop: Right hand pointing / writing
        elif wr_r[1] < mid_sh[1] + 0.05 and wr_l[1] > mid_sh[1] + 0.15:
            selected_key = "pose_prop_brush"
        # 9. Stride / Walking (B1): Knees moving or high speed
        elif max(self.punch_speed_l, self.punch_speed_r) > 2.8:
            selected_key = "pose_b1_walk"
        # 10. Multi-View Turnaround Angles (when standing naturally)
        else:
            if abs(yaw_deg) < 22.0:
                selected_key = "turn_front"
            elif abs(yaw_deg) < 65.0:
                selected_key = "turn_front_quarter"
            elif abs(yaw_deg) < 118.0:
                selected_key = "turn_profile"
            elif abs(yaw_deg) < 155.0:
                selected_key = "turn_back_quarter"
            else:
                selected_key = "turn_back"

        # If Turntable active, force turntable turnaround angle
        if self.turntable_angle != 0.0:
            tt_deg = math.degrees(self.turntable_angle) % 360
            if tt_deg < 45 or tt_deg >= 315:
                selected_key = "turn_front"
            elif tt_deg < 90:
                selected_key = "turn_front_quarter"
            elif tt_deg < 180:
                selected_key = "turn_profile"
            elif tt_deg < 270:
                selected_key = "turn_back_quarter"
            else:
                selected_key = "turn_back"

        # Draw Hou Shu Sprite
        sprite = self.houshu_sprites.get(selected_key)
        if sprite is None:
            sprite = self.houshu_sprites.get("master_standing")
        if sprite is not None:
            self.overlay_sprite(canvas, sprite, center_x, bottom_y, fig_height)

        # Pose Badge Telemetry
        pose_label = selected_key.upper().replace("_", " ")
        cv2.rectangle(canvas, (center_x - 130, bottom_y - fig_height - 35), 
                      (center_x + 130, bottom_y - fig_height - 8), (15, 18, 24), -1)
        cv2.rectangle(canvas, (center_x - 130, bottom_y - fig_height - 35), 
                      (center_x + 130, bottom_y - fig_height - 8), (0, 240, 255), 1)
        cv2.putText(canvas, f"POSE: {pose_label}", (center_x - 118, bottom_y - fig_height - 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 240, 255), 1, cv2.LINE_AA)

    def render_character(self, canvas, joints, t_curr):
        """Renders 3D Character Rig with full volumetric anatomy, clothing, and anime hair"""
        if self.char_idx == 1 and self.houshu_sprites:
            # Render Photorealistic Hou Shu from character-asset-kit
            self.render_houshu_kinematic(canvas, joints, t_curr)
            return

        # Apply Turntable Rotation if active
        if self.turntable_angle != 0.0:
            center = (joints[23] + joints[24]) * 0.5
            joints = [self.renderer.rotate_point_y(j, self.turntable_angle, center) for j in joints]

        # Character Color Schemes & Styles
        if self.char_idx == 1:
            # KR-04 HOU SHU (ANCIENT HANFU SCHOLAR - GATES-REALHUMAN-GUFENG-V1)
            c_hair = (25, 25, 25)        # Sleek Black Hair Bun with Jade Crown
            c_gi = (248, 247, 246)       # Pure White Silk Flowing Robe (#FAF9F6)
            c_under = (62, 77, 27)       # Deep Forest Emerald Cross-Collar (#1B4D3E)
            c_skin = (188, 210, 238)     # Natural Real-Skin Tone (Kodak Portra 400)
            c_boots = (25, 25, 28)       # Black Traditional Boots & Sash
            c_aura = (180, 220, 190)     # Subtle Ethereal Bamboo Mint Glow
        elif self.char_idx == 2:
            # 3D GOKU SUPER SAIYAN
            c_hair = (0, 220, 255)       # Golden Yellow
            c_gi = (0, 105, 235)         # Orange Gi
            c_under = (180, 50, 20)      # Navy Blue undershirt & sash
            c_skin = (175, 205, 240)     # Anime Skin
            c_boots = (150, 35, 15)      # Navy boots with red accents
            c_aura = (0, 240, 255)       # Golden Aura
        elif self.char_idx == 2:
            # 3D VEGETA ROYAL PRINCE
            c_hair = (25, 25, 25)        # Pure Black Spikes
            c_gi = (240, 240, 245)       # White Armor Chest
            c_under = (150, 30, 15)      # Dark Royal Blue Bodysuit
            c_skin = (175, 205, 240)
            c_boots = (235, 235, 240)    # White boots
            c_aura = (245, 180, 0)       # Royal Blue / Cyan Aura
        elif self.char_idx == 3:
            # 3D CYBER WARRIOR
            c_hair = (200, 160, 40)      # Cyan Cyber Helmet
            c_gi = (45, 45, 50)          # Carbon Fiber Armor
            c_under = (255, 220, 0)      # Glowing Cyan Energy Underlayer
            c_skin = (180, 180, 185)     # Cybernetic Chrome
            c_boots = (70, 70, 75)
            c_aura = (255, 230, 0)
        elif self.char_idx == 4:
            # 3D BLINDBOX CHIBI (GATES-BLINDBOX3D-V1)
            c_hair = (180, 120, 240)     # Pastel Chibi Violet
            c_gi = (240, 180, 140)       # Pastel Peach
            c_under = (255, 255, 255)
            c_skin = (210, 225, 255)     # Porcelain Doll
            c_boots = (160, 100, 220)
            c_aura = (255, 190, 220)
        else: # 5: Doraemon Style
            c_hair = (230, 140, 0)       # Classic Doraemon Blue
            c_gi = (255, 255, 255)       # White belly
            c_under = (0, 0, 240)        # Red collar & bell
            c_skin = (255, 255, 255)
            c_boots = (255, 255, 255)
            c_aura = (255, 200, 0)

        # Joint Shortcuts
        nose = joints[0]
        sh_l, sh_r = joints[11], joints[12]
        el_l, el_r = joints[13], joints[14]
        wr_l, wr_r = joints[15], joints[16]
        hip_l, hip_r = joints[23], joints[24]
        kn_l, kn_r = joints[25], joints[26]
        ank_l, ank_r = joints[27], joints[28]

        mid_sh = (sh_l + sh_r) * 0.5
        mid_hip = (hip_l + hip_r) * 0.5
        spine_mid = (mid_sh + mid_hip) * 0.5

        # 1. Swirling Golden Ki Aura (Super Saiyan Power Field)
        if self.show_aura:
            aura_intensity = 0.5 + self.ki_charge_ratio * 0.5
            for k in range(16):
                angle = t_curr * 5.0 + k * (math.pi / 8.0)
                r_aura = 0.45 * (1.0 + 0.15 * math.sin(t_curr * 12.0 + k))
                y_aura = mid_hip[1] + (k / 16.0) * (mid_sh[1] - mid_hip[1] - 0.3)
                p_aura = np.array([
                    mid_hip[0] + math.cos(angle) * r_aura,
                    y_aura,
                    mid_hip[2] + math.sin(angle) * r_aura * 0.6
                ], dtype=np.float32)
                pt_scr = self.cam3d.project(p_aura)
                radius_scr = max(2, int(8 * aura_intensity))
                cv2.circle(canvas, pt_scr, radius_scr, c_aura, -1, cv2.LINE_AA)

        # 2. Torso (Anatomical Upper Chest & Abdomen Gi)
        self.renderer.draw_shaded_limb(canvas, mid_hip, spine_mid, radius=0.14, color=c_gi, taper=1.05)
        self.renderer.draw_shaded_limb(canvas, spine_mid, mid_sh, radius=0.16, color=c_gi, taper=1.12)
        # Undershirt V-neck accent
        chest_v = (mid_sh * 0.7 + spine_mid * 0.3)
        self.renderer.draw_shaded_sphere(canvas, chest_v, radius=0.08, color=c_under)

        # 3. Arms (Shoulders, Biceps, Forearms, Hands)
        # Left Arm
        self.renderer.draw_shaded_sphere(canvas, sh_l, radius=0.075, color=c_gi)
        self.renderer.draw_shaded_limb(canvas, sh_l, el_l, radius=0.065, color=c_skin, taper=0.92)
        self.renderer.draw_shaded_sphere(canvas, el_l, radius=0.06, color=c_skin)
        self.renderer.draw_shaded_limb(canvas, el_l, wr_l, radius=0.058, color=c_skin, taper=0.88)
        # Left Wristband & Fist
        self.renderer.draw_shaded_sphere(canvas, wr_l, radius=0.055, color=c_under)
        self.renderer.draw_shaded_sphere(canvas, wr_l + (wr_l - el_l) * 0.25, radius=0.06, color=c_skin)

        # Right Arm
        self.renderer.draw_shaded_sphere(canvas, sh_r, radius=0.075, color=c_gi)
        self.renderer.draw_shaded_limb(canvas, sh_r, el_r, radius=0.065, color=c_skin, taper=0.92)
        self.renderer.draw_shaded_sphere(canvas, el_r, radius=0.06, color=c_skin)
        self.renderer.draw_shaded_limb(canvas, el_r, wr_r, radius=0.058, color=c_skin, taper=0.88)
        # Right Wristband & Fist
        self.renderer.draw_shaded_sphere(canvas, wr_r, radius=0.055, color=c_under)
        self.renderer.draw_shaded_sphere(canvas, wr_r + (wr_r - el_r) * 0.25, radius=0.06, color=c_skin)

        # 4. Legs & Combat Boots
        # Pelvis / Belt Sash
        self.renderer.draw_shaded_limb(canvas, hip_l, hip_r, radius=0.10, color=c_under, taper=1.0)
        # Left Leg
        self.renderer.draw_shaded_limb(canvas, hip_l, kn_l, radius=0.082, color=c_gi, taper=0.92)
        self.renderer.draw_shaded_sphere(canvas, kn_l, radius=0.068, color=c_gi)
        self.renderer.draw_shaded_limb(canvas, kn_l, ank_l, radius=0.072, color=c_gi, taper=0.85)
        self.renderer.draw_shaded_sphere(canvas, ank_l, radius=0.065, color=c_boots)
        # Boot foot
        boot_tip_l = ank_l + np.array([0.0, 0.05, 0.12], dtype=np.float32)
        self.renderer.draw_shaded_limb(canvas, ank_l, boot_tip_l, radius=0.062, color=c_boots, taper=0.8)

        # Right Leg
        self.renderer.draw_shaded_limb(canvas, hip_r, kn_r, radius=0.082, color=c_gi, taper=0.92)
        self.renderer.draw_shaded_sphere(canvas, kn_r, radius=0.068, color=c_gi)
        self.renderer.draw_shaded_limb(canvas, kn_r, ank_r, radius=0.072, color=c_gi, taper=0.85)
        self.renderer.draw_shaded_sphere(canvas, ank_r, radius=0.065, color=c_boots)
        # Boot foot
        boot_tip_r = ank_r + np.array([0.0, 0.05, 0.12], dtype=np.float32)
        self.renderer.draw_shaded_limb(canvas, ank_r, boot_tip_r, radius=0.062, color=c_boots, taper=0.8)

        # 5. Head, Neck & Facial Expression
        neck = mid_sh + (nose - mid_sh) * 0.45
        self.renderer.draw_shaded_limb(canvas, mid_sh, neck, radius=0.055, color=c_skin, taper=0.95)
        head_center = nose + np.array([0.0, -0.06, 0.0], dtype=np.float32)
        head_radius = 0.11 if self.char_idx != 4 else 0.18 # Chibi oversized head
        self.renderer.draw_shaded_sphere(canvas, head_center, radius=head_radius, color=c_skin)

        # 6. Character Headpieces & Accoutrements (Jade Crown / Saiyan Hair)
        if self.char_idx == 1:
            # KR-04 Hou Shu: Traditional Jade Hair Crown (玉冠) & Hairpin
            crown_center = head_center + np.array([0.0, -0.13, 0.01], dtype=np.float32)
            # Jade Crown Top Knot (Cylindrical Jade Gem)
            self.renderer.draw_shaded_limb(canvas, crown_center + np.array([0, 0.03, 0]), 
                                          crown_center + np.array([0, -0.04, 0]), 
                                          radius=0.038, color=(160, 215, 175), taper=1.0)
            # Jade Hairpin traversing the bun horizontally
            pin_l = crown_center + np.array([-0.075, 0.0, 0.0], dtype=np.float32)
            pin_r = crown_center + np.array([0.075, 0.0, 0.0], dtype=np.float32)
            self.renderer.draw_shaded_limb(canvas, pin_l, pin_r, radius=0.008, color=(180, 230, 195), taper=1.0)
            # Cross-Collar Emerald Edge Accent on Chest
            collar_left = mid_sh + (sh_l - mid_sh) * 0.45
            collar_cross = spine_mid + (sh_r - mid_sh) * 0.25
            self.renderer.draw_shaded_limb(canvas, collar_left, collar_cross, radius=0.022, color=c_under, taper=1.0)
        elif self.char_idx == 2:
            # Goku Super Saiyan: 7 iconic upward flared golden hair spikes
            spike_offsets = [
                (np.array([0.0, -0.26, 0.04]), 0.08),     # Crown central spike
                (np.array([-0.14, -0.22, 0.02]), 0.07),   # Left flare
                (np.array([0.14, -0.22, 0.02]), 0.07),    # Right flare
                (np.array([-0.22, -0.12, 0.01]), 0.065),  # Left ear spike
                (np.array([0.22, -0.12, 0.01]), 0.065),   # Right ear spike
                (np.array([0.0, -0.18, -0.12]), 0.07),    # Back crest spike
                (np.array([0.08, -0.06, 0.10]), 0.045)    # Forehead bang
            ]
            for off, w in spike_offsets:
                self.renderer.draw_hair_spike(canvas, head_center, head_center + off, width=w * 180, color=c_hair)
        elif self.char_idx == 2:
            # Vegeta: Tall flame-shaped upward swept black spikes
            spike_offsets = [
                (np.array([0.0, -0.32, 0.01]), 0.075),
                (np.array([-0.09, -0.28, 0.0]), 0.07),
                (np.array([0.09, -0.28, 0.0]), 0.07),
                (np.array([-0.18, -0.19, 0.0]), 0.06),
                (np.array([0.18, -0.19, 0.0]), 0.06)
            ]
            for off, w in spike_offsets:
                self.renderer.draw_hair_spike(canvas, head_center, head_center + off, width=w * 170, color=c_hair)

        # 7. Cupped Hands Kamehameha Energy Sphere
        if self.ki_charge_ratio > 0.05:
            mid_hand = (wr_l + wr_r) * 0.5 + np.array([0.0, 0.0, -0.05], dtype=np.float32)
            orb_r = 0.06 + self.ki_charge_ratio * 0.14
            # Core bright white sphere
            self.renderer.draw_shaded_sphere(canvas, mid_hand, radius=orb_r * 0.55, color=(255, 255, 255))
            # Outer cyan energy glow rings
            pt_orb = self.cam3d.project(mid_hand)
            r_px = max(6, int((self.cam3d.K[0, 0] * orb_r) / max(0.1, mid_hand[2])))
            cv2.circle(canvas, pt_orb, r_px, (255, 230, 0), 3, cv2.LINE_AA)
            cv2.circle(canvas, pt_orb, int(r_px * 1.35), (255, 180, 0), 1, cv2.LINE_AA)

    def render_mocap_skeleton_overlay(self, canvas, joints):
        """Draws clean, professional skeletal tracking lines on the webcam view"""
        h, w = canvas.shape[:2]
        # Camera 3D to 2D projection
        pts_2d = [self.cam3d.project(j) for j in joints]

        # Bone Connections
        bones = [
            (11, 12), (11, 13), (13, 15), # Left Arm
            (12, 14), (14, 16),           # Right Arm
            (11, 23), (12, 24), (23, 24), # Torso
            (23, 25), (25, 27),           # Left Leg
            (24, 26), (26, 28)            # Right Leg
        ]

        # Draw bones
        for b1, b2 in bones:
            p1 = pts_2d[b1]
            p2 = pts_2d[b2]
            cv2.line(canvas, p1, p2, (0, 240, 255), 3, cv2.LINE_AA)

        # Draw key joint nodes
        for idx in [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]:
            p = pts_2d[idx]
            cv2.circle(canvas, p, 5, (0, 255, 0), -1, cv2.LINE_AA)
            cv2.circle(canvas, p, 7, (255, 255, 255), 1, cv2.LINE_AA)

    def assemble_final_view(self, cam_display, stage_canvas, joints, t_curr):
        """Assembles Split-Screen, AR Overlay, or Full 3D Cinema according to view mode"""
        if self.view_mode == 'SPLIT':
            # Side-by-Side: Left (Camera) | Right (3D Character)
            canvas = np.zeros((720, 1280, 3), dtype=np.uint8)
            canvas[:, :640] = cam_display
            canvas[:, 640:] = stage_canvas
            # Split separator bar
            cv2.line(canvas, (640, 0), (640, 720), (0, 240, 255), 2, cv2.LINE_AA)
            return canvas

        elif self.view_mode == 'AR':
            # AR Holographic Overlay: Render character directly over live camera
            ar_canvas = cam_display.copy()
            if joints is not None:
                self.render_character(ar_canvas, joints, t_curr)
            # Re-scale to 1280x720
            return cv2.resize(ar_canvas, (1280, 720))

        else: # 'CINEMA'
            # Full 1280x720 3D Cinema Stage
            cinema_cam = Camera3D(width=1280, height=720, fov=52.0)
            cinema_renderer = Character3DRenderer(cinema_cam)
            old_renderer = self.renderer
            self.renderer = cinema_renderer

            cinema_canvas = cv2.resize(stage_canvas, (1280, 720))
            if joints is not None:
                self.render_character(cinema_canvas, joints, t_curr)

            self.renderer = old_renderer
            if self.show_sheet_preview and self.sheet_img is not None:
                # Scale and center character sheet preview
                sh_h, sh_w = self.sheet_img.shape[:2]
                scale = min(680.0 / sh_h, 1200.0 / sh_w)
                disp_w = int(sh_w * scale)
                disp_h = int(sh_h * scale)
                sheet_resized = cv2.resize(self.sheet_img, (disp_w, disp_h))
                x_off = (1280 - disp_w) // 2
                y_off = (720 - disp_h) // 2
                # Dim background
                cinema_canvas = (cinema_canvas * 0.25).astype(np.uint8)
                cinema_canvas[y_off:y_off+disp_h, x_off:x_off+disp_w] = sheet_resized
                cv2.rectangle(cinema_canvas, (x_off, y_off), (x_off+disp_w, y_off+disp_h), (0, 240, 255), 2)
            return cinema_canvas

    def draw_hud(self, canvas, joints, t_curr):
        """Draws crisp, Hollywood-grade telemetry HUD and key shortcuts"""
        h, w = canvas.shape[:2]

        # Top Status Bar
        char_title = self.char_names.get(self.char_idx, "CHARACTER")
        status_text = f"PILOT: NITHESH | {char_title} | MODE: {self.view_mode} | STAGE: {self.stage_bg}"
        cv2.rectangle(canvas, (16, 16), (w - 16, 52), (15, 15, 20), -1)
        cv2.rectangle(canvas, (16, 16), (w - 16, 52), (0, 240, 255), 1)
        cv2.putText(canvas, status_text, (28, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 240, 255), 2, cv2.LINE_AA)

        # MoCap Tracking Status
        tracking_str = "MOCAP: LOCKED (33 JOINTS 3D)" if joints is not None else "MOCAP: SEARCHING FOR PILOT..."
        track_color = (0, 255, 120) if joints is not None else (0, 100, 255)
        cv2.putText(canvas, tracking_str, (w - 380, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, track_color, 2, cv2.LINE_AA)

        # Stance & Ki Power Bar
        if self.ki_charge_ratio > 0.05:
            bar_w = int(240 * self.ki_charge_ratio)
            cv2.rectangle(canvas, (28, 62), (28 + bar_w, 78), (0, 240, 255), -1)
            cv2.rectangle(canvas, (28, 62), (268, 78), (255, 255, 255), 1)
            cv2.putText(canvas, f"KI ENERGY: {int(self.ki_charge_ratio * 100)}% (KAMEHAMEHA)", 
                        (280, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 240, 255), 1, cv2.LINE_AA)

        # Bottom Shortcut Deck
        deck_text = "[1-5] Characters | [C] Sheet Preview | [V] View | [B] Stage | [O] 360 Orbit | [A] Aura | [S] Export | [Q] Quit"
        cv2.rectangle(canvas, (16, h - 46), (w - 16, h - 16), (15, 15, 20), -1)
        cv2.rectangle(canvas, (16, h - 46), (w - 16, h - 16), (60, 60, 70), 1)
        cv2.putText(canvas, deck_text, (26, h - 26), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (200, 220, 240), 1, cv2.LINE_AA)

        # Recording Take Indicator
        if self.recording_take:
            cv2.circle(canvas, (w - 50, h - 31), 8, (0, 0, 255), -1, cv2.LINE_AA)
            cv2.putText(canvas, "REC", (w - 95, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 0, 255), 2, cv2.LINE_AA)

    def handle_key(self, key, final_canvas, joints):
        # Character Switching [1-5]
        if key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5')]:
            self.char_idx = key - ord('0')
            print(f"[*] Switched to Character [{self.char_idx}]: {self.char_names[self.char_idx]}")
            threading.Thread(target=lambda: winsound.Beep(1100, 45), daemon=True).start()

        # View Mode Toggle [V]
        elif key in [ord('v'), ord('V')]:
            modes = ['SPLIT', 'AR', 'CINEMA']
            curr_idx = modes.index(self.view_mode)
            self.view_mode = modes[(curr_idx + 1) % len(modes)]
            print(f"[*] View Mode: {self.view_mode}")
            threading.Thread(target=lambda: winsound.Beep(850, 40), daemon=True).start()

        # Stage Background Toggle [B]
        elif key in [ord('b'), ord('B')]:
            stages = ['DOJO', 'TIME_CHAMBER', 'CYBER', 'VOID', 'CAM']
            curr_idx = stages.index(self.stage_bg)
            self.stage_bg = stages[(curr_idx + 1) % len(stages)]
            print(f"[*] Stage Background: {self.stage_bg}")

        # 360° Turntable Orbit [O]
        elif key in [ord('o'), ord('O')]:
            self.turntable_active = not self.turntable_active
            print(f"[*] 360° Turntable Orbit: {self.turntable_active}")

        # Character Sheet Preview Toggle [C]
        elif key in [ord('c'), ord('C')]:
            self.show_sheet_preview = not self.show_sheet_preview
            print(f"[*] Character Asset Kit Sheet Preview: {self.show_sheet_preview}")
            threading.Thread(target=lambda: winsound.Beep(1350, 60), daemon=True).start()

        # Skeleton Overlay Toggle [M]
        elif key in [ord('m'), ord('M')]:
            self.show_skeleton = not self.show_skeleton

        # Aura Toggle [A]
        elif key in [ord('a'), ord('A')]:
            self.show_aura = not self.show_aura

        # HUD Toggle [H]
        elif key in [ord('h'), ord('H')]:
            self.show_hud = not self.show_hud

        # Save Character Asset Kit Turnaround Sheet [S]
        elif key in [ord('s'), ord('S')]:
            self.save_asset_kit_sheet(joints)

        # Record Motion Take [T]
        elif key in [ord('t'), ord('T')]:
            self.recording_take = not self.recording_take
            if self.recording_take:
                self.recorded_frames = []
                print("[*] Started recording motion capture take...")
                threading.Thread(target=lambda: winsound.Beep(1400, 70), daemon=True).start()
            else:
                self.save_motion_take()

        # Quit [Q] / [ESC]
        elif key in [ord('q'), ord('Q'), 27]:
            self.running = False

    def save_asset_kit_sheet(self, joints):
        """Exports G2 Multi-View Turnaround Sheet in character-asset-kit format"""
        if joints is None:
            print("[!] Please stand in front of camera to capture character asset sheet.")
            return

        out_dir = os.path.join(r"C:\Users\SVNITHESHPC\Downloads\AI_VFX_Realtime_Suite", "character_asset_sheets")
        os.makedirs(out_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"asset_sheet_{self.char_idx}_{timestamp}.jpg"
        out_path = os.path.join(out_dir, filename)

        # Render 5-angle turnaround board (Front, 3/4 Left, Profile, Back, 3/4 Right)
        angles = [0.0, math.pi * 0.25, math.pi * 0.5, math.pi, -math.pi * 0.25]
        angle_names = ["FRONT (0°)", "3/4 LEFT (45°)", "PROFILE (90°)", "BACK (180°)", "3/4 RIGHT (-45°)"]
        
        cell_w, cell_h = 320, 480
        board = np.zeros((cell_h + 80, cell_w * 5, 3), dtype=np.uint8)
        board[:] = (20, 20, 24)

        cell_cam = Camera3D(width=cell_w, height=cell_h, fov=48.0)
        cell_renderer = Character3DRenderer(cell_cam)
        old_renderer = self.renderer
        self.renderer = cell_renderer

        center = (joints[23] + joints[24]) * 0.5

        for col, (ang, label) in enumerate(zip(angles, angle_names)):
            cell_canvas = np.zeros((cell_h, cell_w, 3), dtype=np.uint8)
            cell_canvas[:] = (30, 30, 35)
            # Ground grid
            for y_line in range(int(cell_h * 0.75), cell_h, 20):
                cv2.line(cell_canvas, (0, y_line), (cell_w, y_line), (45, 45, 52), 1)

            rot_joints = [cell_renderer.rotate_point_y(j, ang, center) for j in joints]
            self.render_character(cell_canvas, rot_joints, time.time())

            # Header label
            cv2.rectangle(cell_canvas, (0, 0), (cell_w, 34), (15, 15, 18), -1)
            cv2.putText(cell_canvas, label, (14, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 240, 255), 1, cv2.LINE_AA)

            board[80:, col*cell_w:(col+1)*cell_w] = cell_canvas

        # Board Title Header
        title = f"CHARACTER ASSET KIT: G2 MULTI-VIEW TURNAROUND | {self.char_names[self.char_idx]}"
        cv2.putText(board, title, (28, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 240, 255), 2, cv2.LINE_AA)

        self.renderer = old_renderer
        cv2.imwrite(out_path, board)
        print(f"[✓] Saved Character Asset Turnaround Sheet to: {out_path}")
        threading.Thread(target=lambda: winsound.Beep(1600, 90), daemon=True).start()

    def save_motion_take(self):
        """Saves recorded motion kinematics to JSON in character-asset-kit format"""
        import json
        out_dir = os.path.join(r"C:\Users\SVNITHESHPC\Downloads\AI_VFX_Realtime_Suite", "mocap_takes")
        os.makedirs(out_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"mocap_take_{self.char_idx}_{timestamp}.json"
        out_path = os.path.join(out_dir, filename)

        take_data = {
            "format": "character-asset-kit-v1.4",
            "character": self.char_names[self.char_idx],
            "fps": 60,
            "total_frames": len(self.recorded_frames),
            "frames": self.recorded_frames
        }

        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(take_data, f, indent=2)

        print(f"[✓] Saved Motion Capture Take ({len(self.recorded_frames)} frames) to: {out_path}")
        threading.Thread(target=lambda: winsound.Beep(1200, 70), daemon=True).start()

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    studio = NativeCharacterMoCapStudio()
    studio.run()
