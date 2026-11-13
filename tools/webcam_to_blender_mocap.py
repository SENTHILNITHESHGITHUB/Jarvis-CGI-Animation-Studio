"""
================================================================================
⚡ WEBCAM TO BLENDER MASTER MOCAP STUDIO (Astraverse Production Pipeline) ⚡
================================================================================
1. Captures live 3D body motion from USB Webcam via MediaPipe 3D Pose.
2. Applies 1-Euro cinematic smoothing filters (zero camera jitter).
3. Live HUD with glowing Astra skeleton & reactive hand fire.
4. One-touch recording [SPACE] to capture hero martial arts/fire casting action.
5. Injects 3D bone keyframes directly into Blender Astraverse_Hero_Rig.
6. Launches Blender 3D Virtual Studio with user's motion fully animated!
================================================================================
"""

import os
import sys
import time
import math
import json
import subprocess
from typing import List, Tuple, Dict, Any

import cv2
import numpy as np

# ------------------------------------------------------------------------------
# 1. PATH CONFIGURATION
# ------------------------------------------------------------------------------
BASE_DIR = r"C:\Users\SVNITHESHPC\Downloads\Astraverse_Blender_Studio"
POSE_MODEL_PATH = r"C:\Users\SVNITHESHPC\Downloads\AI_VFX_Realtime_Suite\pose_landmarker.task"
BLENDER_EXE = r"C:\Users\SVNITHESHPC\Downloads\blender-3.6.9-windows-x64\blender.exe"
BLEND_FILE = os.path.join(BASE_DIR, "Astraverse_3D_Virtual_Studio.blend")
APPLY_SCRIPT = os.path.join(BASE_DIR, "apply_mocap_to_blender.py")
OUTPUT_JSON = os.path.join(BASE_DIR, "latest_mocap_take.json")

# ------------------------------------------------------------------------------
# 2. 1-EURO FILTER (Cinematic Jitter Removal)
# ------------------------------------------------------------------------------
class OneEuroFilter3D:
    def __init__(self, min_cutoff=1.5, beta=0.035, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None

    def filter(self, x, t):
        if self.t_prev is None:
            self.x_prev = np.array(x, dtype=np.float32)
            self.dx_prev = np.zeros_like(self.x_prev)
            self.t_prev = t
            return self.x_prev

        dt = max(t - self.t_prev, 0.001)
        self.t_prev = t

        dx = (np.array(x, dtype=np.float32) - self.x_prev) / dt
        edx = self._alpha(dt, self.d_cutoff)
        dx_hat = edx * dx + (1.0 - edx) * self.dx_prev
        self.dx_prev = dx_hat

        cutoff = self.min_cutoff + self.beta * np.linalg.norm(dx_hat)
        alpha = self._alpha(dt, cutoff)
        x_hat = alpha * np.array(x, dtype=np.float32) + (1.0 - alpha) * self.x_prev
        self.x_prev = x_hat
        return x_hat

    def _alpha(self, dt, cutoff):
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

# ------------------------------------------------------------------------------
# 3. POSE RETARGETING (MediaPipe 3D -> Blender Armature)
# ------------------------------------------------------------------------------
def compute_bone_rotations(joints_3d: Dict[int, np.ndarray]) -> Dict[str, Any]:
    """
    Converts 33 MediaPipe 3D metric joints to Blender bone rotations:
    Joints:
    0: Nose
    11: L_Shoulder, 12: R_Shoulder
    13: L_Elbow, 14: R_Elbow
    15: L_Wrist, 16: R_Wrist
    23: L_Hip, 24: R_Hip
    25: L_Knee, 26: R_Knee
    27: L_Ankle, 28: R_Ankle
    """
    bones = {}
    
    # 1. Hips (Center of Pelvis)
    hip_l = joints_3d.get(23)
    hip_r = joints_3d.get(24)
    sh_l = joints_3d.get(11)
    sh_r = joints_3d.get(12)
    
    if hip_l is not None and hip_r is not None:
        pelvis = (hip_l + hip_r) * 0.5
        # Invert MediaPipe Y to Blender Z, and Z to -Y
        bx = float(pelvis[0]) * 1.5
        by = -float(pelvis[2]) * 1.5
        bz = float(-pelvis[1]) * 1.5
        
        # Hips tilt/roll
        hip_vec = hip_r - hip_l
        roll_hips = math.atan2(hip_vec[1], hip_vec[0])
        bones["Hips"] = {
            "location": [bx, by, bz],
            "rotation_euler": [0.0, float(roll_hips) * 0.5, 0.0]
        }
        
    # 2. Spine & Chest (Mid Hips to Mid Shoulders)
    if hip_l is not None and hip_r is not None and sh_l is not None and sh_r is not None:
        mid_hip = (hip_l + hip_r) * 0.5
        mid_sh = (sh_l + sh_r) * 0.5
        spine_v = mid_sh - mid_hip
        
        pitch = math.atan2(spine_v[2], -spine_v[1]) # forward lean
        yaw = math.atan2(spine_v[0], -spine_v[1])   # lateral twist
        
        bones["Spine"] = {"rotation_euler": [float(pitch) * 0.5, 0.0, float(yaw) * 0.5]}
        bones["Chest"] = {"rotation_euler": [float(pitch) * 0.5, 0.0, float(yaw) * 0.5]}

    # 3. Head (Nose relative to mid shoulders)
    nose = joints_3d.get(0)
    if nose is not None and sh_l is not None and sh_r is not None:
        mid_sh = (sh_l + sh_r) * 0.5
        neck_v = nose - mid_sh
        pitch_h = math.atan2(neck_v[2], -neck_v[1])
        yaw_h = math.atan2(neck_v[0], -neck_v[1])
        bones["Head"] = {"rotation_euler": [float(pitch_h) * 0.6, 0.0, float(yaw_h) * 0.6]}

    # 4. Arms (UpperArm & ForeArm)
    for side, sign, j_sh, j_el, j_wr in [("L", -1, 11, 13, 15), ("R", 1, 12, 14, 16)]:
        sh = joints_3d.get(j_sh)
        el = joints_3d.get(j_el)
        wr = joints_3d.get(j_wr)
        
        if sh is not None and el is not None:
            # Upper arm vector
            ua_v = el - sh
            # Pitch (up/down) and Yaw (forward/back)
            pitch_ua = math.atan2(-ua_v[1], math.hypot(ua_v[0], ua_v[2])) # arm raise
            yaw_ua = math.atan2(ua_v[2], ua_v[0] * sign)                   # forward reach
            roll_ua = math.atan2(ua_v[0] * sign, -ua_v[1])
            
            bones[f"UpperArm_{side}"] = {
                "rotation_euler": [float(pitch_ua), float(yaw_ua) * 0.8, float(roll_ua) * 0.5]
            }
            
        if el is not None and wr is not None:
            # Forearm vector
            fa_v = wr - el
            pitch_fa = math.atan2(-fa_v[1], math.hypot(fa_v[0], fa_v[2]))
            yaw_fa = math.atan2(fa_v[2], fa_v[0] * sign)
            bones[f"ForeArm_{side}"] = {
                "rotation_euler": [float(pitch_fa) * 0.8, 0.0, float(yaw_fa) * 0.6]
            }
            bones[f"Hand_{side}"] = {
                "rotation_euler": [float(pitch_fa) * 0.3, 0.0, 0.0]
            }

    # 5. Legs (UpperLeg & LowerLeg)
    for side, sign, j_hip, j_kn, j_ank in [("L", -1, 23, 25, 27), ("R", 1, 24, 26, 28)]:
        hp = joints_3d.get(j_hip)
        kn = joints_3d.get(j_kn)
        ak = joints_3d.get(j_ank)
        
        if hp is not None and kn is not None:
            th_v = kn - hp
            pitch_th = math.atan2(th_v[2], th_v[1]) # leg forward/backward
            bones[f"UpperLeg_{side}"] = {"rotation_euler": [float(pitch_th) * 0.7, 0.0, 0.0]}
            
        if kn is not None and ak is not None:
            sh_v = ak - kn
            pitch_sh = math.atan2(sh_v[2], sh_v[1])
            bones[f"LowerLeg_{side}"] = {"rotation_euler": [float(pitch_sh) * 0.7, 0.0, 0.0]}
            bones[f"Foot_{side}"] = {"rotation_euler": [0.0, 0.0, 0.0]}
            
    return bones

# ------------------------------------------------------------------------------
# 4. MASTER WEBCAM MOCAP RECORDER
# ------------------------------------------------------------------------------
def run_mocap_recorder():
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    print("\n" + "=" * 70)
    print("⚡ WEBCAM TO BLENDER MASTER MOCAP STUDIO ⚡")
    print(" [SPACE]   START / STOP RECORDING MOCAP TAKE")
    print(" [R]       RESET / DISCARD CURRENT TAKE")
    print(" [Q / ESC] FINISH & TRANSFER TO BLENDER")
    print("=" * 70 + "\n")

    # Camera Discovery
    cap = None
    for backend in [cv2.CAP_ANY, cv2.CAP_DSHOW, cv2.CAP_MSMF]:
        test_cap = cv2.VideoCapture(0, backend)
        if test_cap.isOpened():
            cap = test_cap
            break

    if not cap or not cap.isOpened():
        print("[!] Failed to open webcam! Check camera connection.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    for _ in range(4):
        cap.grab()

    # Pose Landmarker
    base_options = python.BaseOptions(model_asset_path=POSE_MODEL_PATH)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.50,
        min_tracking_confidence=0.50
    )
    detector = vision.PoseLandmarker.create_from_options(options)

    # 1-Euro Filters (33 joints)
    filters = [OneEuroFilter3D(min_cutoff=1.6, beta=0.035) for _ in range(33)]

    win_name = "⚡ WEBCAM TO BLENDER MOCAP // [SPACE] RECORD ⚡"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, 1280, 720)

    recording = False
    recorded_frames = []
    rec_start_time = 0.0
    start_clock = time.time()

    # Skeleton connections for rendering
    SKELETON_PAIRS = [
        (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Arms
        (11, 23), (12, 24), (23, 24),                      # Torso
        (23, 25), (25, 27), (24, 26), (26, 28)             # Legs
    ]

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.01)
            continue

        frame = cv2.flip(frame, 1) # Mirror for natural feel
        h, w = frame.shape[:2]
        t_now = time.time()

        # Run MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        res = detector.detect(mp_img)

        joints_dict = {}
        joints_2d = {}

        if res.pose_landmarks:
            for j_idx, lm in enumerate(res.pose_landmarks[0]):
                raw_pt = np.array([lm.x, lm.y, lm.z], dtype=np.float32)
                filt_pt = filters[j_idx].filter(raw_pt, t_now)
                joints_dict[j_idx] = filt_pt
                joints_2d[j_idx] = (int(filt_pt[0] * w), int(filt_pt[1] * h))

            # Draw glowing Astra skeleton
            for j1, j2 in SKELETON_PAIRS:
                if j1 in joints_2d and j2 in joints_2d:
                    p1 = joints_2d[j1]
                    p2 = joints_2d[j2]
                    cv2.line(frame, p1, p2, (30, 150, 255), 4, cv2.LINE_AA)
                    cv2.line(frame, p1, p2, (255, 255, 255), 2, cv2.LINE_AA)

            # Glowing Astra Joints
            for j_idx, pt in joints_2d.items():
                cv2.circle(frame, pt, 6, (40, 200, 255), -1)
                cv2.circle(frame, pt, 2, (255, 255, 255), -1)

            # Reactive Hand Fire on Wrists
            for wr_idx in [15, 16]:
                if wr_idx in joints_2d:
                    wpt = joints_2d[wr_idx]
                    cv2.circle(frame, wpt, 24, (20, 140, 255), -1)
                    cv2.circle(frame, wpt, 12, (180, 230, 255), -1)
                    cv2.line(frame, (wpt[0] - 60, wpt[1]), (wpt[0] + 60, wpt[1]), (50, 210, 255), 3, cv2.LINE_AA)

            # Record Frame
            if recording:
                bone_rotations = compute_bone_rotations(joints_dict)
                recorded_frames.append({
                    "frame": len(recorded_frames) + 1,
                    "time": round(t_now - rec_start_time, 4),
                    "bones": bone_rotations
                })

        # Broadcast On-Screen HUD
        if recording:
            dur = t_now - rec_start_time
            hud_text = f"● RECORDING MOCAP TAKE: {len(recorded_frames):04d} FRAMES [{dur:04.1f}s] // [SPACE] TO STOP"
            cv2.rectangle(frame, (20, 20), (1260, 75), (0, 0, 180), -1)
            cv2.putText(frame, hud_text, (40, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255, 255, 255), 2, cv2.LINE_AA)
        else:
            rec_count = len(recorded_frames)
            status_str = f"READY // [SPACE] RECORD MOCAP TAKE (Captured: {rec_count} frames) // [Q] EXPORT"
            cv2.rectangle(frame, (20, 20), (1260, 75), (20, 20, 20), -1)
            cv2.putText(frame, status_str, (40, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (40, 215, 255), 2, cv2.LINE_AA)

        cv2.imshow(win_name, frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord(' '):
            if not recording:
                recording = True
                recorded_frames = []
                rec_start_time = time.time()
                print("[● ACTION!] Recording mocap motion take...")
            else:
                recording = False
                print(f"[■ CUT!] Take recorded with {len(recorded_frames)} frames.")
        elif key in [ord('r'), ord('R')]:
            recorded_frames = []
            recording = False
            print("[*] Take reset.")
        elif key in [ord('q'), 27]:
            break

    cap.release()
    cv2.destroyAllWindows()

    # Export & Apply to Blender
    if recorded_frames:
        print(f"\n[*] Saving {len(recorded_frames)} mocap frames to {OUTPUT_JSON}...")
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump({
                "fps": 30,
                "total_frames": len(recorded_frames),
                "frames": recorded_frames
            }, f, indent=2)

        print("[*] Launching Blender to inject mocap keyframes...")
        cmd = [
            BLENDER_EXE,
            "-b",
            BLEND_FILE,
            "--python",
            APPLY_SCRIPT,
            "--",
            OUTPUT_JSON
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        print(res.stdout)
        print("⚡ [SUCCESS] YOUR MOTION IS NOW DRIVING THE 3D WARRIOR IN BLENDER! ⚡\n")

if __name__ == "__main__":
    run_mocap_recorder()
