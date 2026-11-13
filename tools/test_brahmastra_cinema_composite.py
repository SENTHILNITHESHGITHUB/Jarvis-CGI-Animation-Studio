import os
import sys
import math
import cv2
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE = r"C:\Users\SVNITHESHPC\Downloads\AI_VFX_Realtime_Suite"
ARTIFACT_DIR = r"C:\Users\SVNITHESHPC\.gemini\antigravity\brain\972199e1-0395-45a5-b415-be1edfa58c26"

AGNI_AVATAR_PATH = os.path.join(WORKSPACE, "assets", "agni_avatar_master.jpg")
NANDI_BULL_PATH = os.path.join(WORKSPACE, "assets", "nandi_astra_master.jpg")
FIRE_PLUME_PATH = os.path.join(WORKSPACE, "assets", "clean_brahmastra_fire_feathered.jpg")
SAMPLE_BG = os.path.join(ARTIFACT_DIR, "real_webcam_test.jpg")
if not os.path.exists(SAMPLE_BG):
    SAMPLE_BG = os.path.join(WORKSPACE, "assets", "real_webcam_test.jpg")

OUT_SHIVA = os.path.join(ARTIFACT_DIR, "brahmastra_shiva_agni_cinema.jpg")
OUT_NANDI = os.path.join(ARTIFACT_DIR, "brahmastra_nandi_bull_cinema.jpg")

def composite_emissive_asset(base_img, asset_bgr, center_x, center_y, scale=1.0, angle=0.0, flip_h=False, intensity=1.35, blend_mode="screen_add"):
    """
    Overlays an emissive VFX asset on black background with zero dark fringes and sub-pixel blending.
    """
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
    alpha = np.clip((gray - 10.0) / 190.0, 0.0, 1.0)
    alpha = (alpha ** 1.2)[:, :, None]

    roi = base_img[fy1:fy2, fx1:fx2].astype(np.float32)

    if blend_mode == "screen_add":
        # Screen background slightly and add emissive glow
        blended = roi * (1.0 - alpha * 0.40) + crop * alpha * intensity
    else:
        # Pure additive
        blended = roi + crop * alpha * intensity

    base_img[fy1:fy2, fx1:fx2] = np.clip(blended, 0.0, 255.0).astype(np.uint8)

def apply_deep_photometric_relighting(frame, light_sources, color_bgr=(18, 120, 255), intensity=1.6):
    """
    Simulates on-set interactive LED lighting rigs used by DNEG in Brahmāstra.
    Bathes the actor's skin, face, clothing, and room in rich warm flame light.
    """
    h_f, w_f = frame.shape[:2]
    if not light_sources:
        return frame

    scale = 0.25
    h_s, w_s = int(h_f * scale), int(w_f * scale)
    irradiance = np.zeros((h_s, w_s), dtype=np.float32)

    for lx, ly in light_sources:
        sx, sy = lx * scale, ly * scale
        sigma = 160.0 * scale
        y_g, x_g = np.ogrid[:h_s, :w_s]
        d2 = (x_g - sx)**2 + (y_g - sy)**2
        irradiance += np.exp(-d2 / (2.0 * (sigma**2)))

    irradiance = np.clip(irradiance * intensity, 0.0, 2.5)
    irradiance_full = cv2.resize(irradiance, (w_f, h_f), interpolation=cv2.INTER_LINEAR)

    light_color = np.array(color_bgr, dtype=np.float32)
    frame_flt = frame.astype(np.float32)
    illum = (irradiance_full[:, :, None] * light_color * 0.45)
    relit = np.clip(frame_flt + (frame_flt * illum / 255.0) * 1.30, 0.0, 255.0).astype(np.uint8)
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

def render_embers(frame, glow_buffer, emitters, count=250):
    np.random.seed(42)
    h_f, w_f = frame.shape[:2]
    for _ in range(count):
        em = emitters[np.random.randint(len(emitters))]
        x = em[0] + np.random.uniform(-180, 180)
        y = em[1] + np.random.uniform(-250, 40)
        size = np.random.uniform(1.5, 4.0)
        alpha = np.random.uniform(0.4, 1.0)
        color = (int(18 * alpha), int(120 * alpha), int(255 * alpha))
        ix, iy = int(x), int(y)
        if 0 <= ix < w_f and 0 <= iy < h_f:
            cv2.circle(glow_buffer, (ix, iy), int(size * 3), color, -1)
            cv2.circle(frame, (ix, iy), max(1, int(size)), (255, 255, 255), -1, cv2.LINE_AA)

def main():
    print("[*] Loading base image...")
    if os.path.exists(SAMPLE_BG):
        base_img = cv2.imread(SAMPLE_BG)
    else:
        # Create cinematic dark studio frame
        base_img = np.zeros((720, 1280, 3), dtype=np.uint8)
        base_img[:] = (22, 20, 26)

    h_f, w_f = base_img.shape[:2]
    if (w_f, h_f) != (1280, 720):
        base_img = cv2.resize(base_img, (1280, 720))
        w_f, h_f = 1280, 720

    # Actor center: x=640, head at y=260, hands at (460, 480) and (820, 480)
    actor_head = (640, 240)
    actor_left_hand = (440, 480)
    actor_right_hand = (840, 480)
    hand_emitters = [actor_left_hand, actor_right_hand]

    # Load high-res assets
    agni_asset = cv2.imread(AGNI_AVATAR_PATH)
    nandi_asset = cv2.imread(NANDI_BULL_PATH)
    fire_asset = cv2.imread(FIRE_PLUME_PATH)

    # =========================================================================
    # RENDER 1: SHIVA AGNYASTRA + AGNI TITAN AVATAR WITH FLAMING TRISHUL
    # =========================================================================
    print("[*] Generating Brahmastra Shiva Agnyastra Scene...")
    scene1 = base_img.copy()

    # 1. Photometric Relighting (2000K warm amber light on actor & room)
    scene1 = apply_deep_photometric_relighting(scene1, [actor_head, actor_left_hand, actor_right_hand], color_bgr=(18, 125, 255), intensity=1.8)

    # 2. Agni Titan Avatar rising behind Shiva's head
    avatar_cx = actor_head[0]
    avatar_cy = actor_head[1] - 80
    composite_emissive_asset(scene1, agni_asset, avatar_cx, avatar_cy, scale=0.62, intensity=1.55)

    # 3. Roaring Fluid Fire Plumes on Forearms and Hands
    composite_emissive_asset(scene1, fire_asset, actor_left_hand[0], actor_left_hand[1] - 80, scale=0.48, angle=15, flip_h=False, intensity=1.65)
    composite_emissive_asset(scene1, fire_asset, actor_right_hand[0], actor_right_hand[1] - 80, scale=0.48, angle=-15, flip_h=True, intensity=1.65)

    # 4. Lens Flare & Core Incandescence
    glow_buffer = np.zeros_like(scene1)
    for em in hand_emitters:
        cv2.circle(glow_buffer, em, 38, (50, 200, 255), -1)
        cv2.circle(glow_buffer, em, 20, (255, 255, 255), -1)
        # Horizontal Anamorphic Flare
        cv2.line(glow_buffer, (em[0] - 180, em[1]), (em[0] + 180, em[1]), (60, 210, 255), 4, cv2.LINE_AA)
        cv2.line(scene1, (em[0] - 90, em[1]), (em[0] + 90, em[1]), (255, 255, 255), 2, cv2.LINE_AA)

    # 5. Floating Embers
    render_embers(scene1, glow_buffer, hand_emitters, count=320)

    # Bloom
    bloom1 = cv2.GaussianBlur(glow_buffer, (21, 21), 0)
    bloom2 = cv2.GaussianBlur(glow_buffer, (51, 51), 0)
    total_bloom = cv2.addWeighted(bloom1, 0.65, bloom2, 0.35, 0)
    scene1 = cv2.addWeighted(scene1, 1.0, total_bloom, 0.80, 0)

    # ACES Filmic Tone Mapping
    scene1 = apply_aces_tone_mapping(scene1)

    # 2.39:1 Cinemascope Anamorphic Letterbox
    scene1 = apply_anamorphic_letterbox(scene1, aspect=2.39)

    # Production Title Slate
    cv2.putText(scene1, "BRAHMASTRA // SHOT 01: SHIVA AWAKENS AGNYASTRA", (40, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(scene1, "AGNI AVATAR WITH FLAMING TRISHUL | 2000K PHOTOMETRIC RELIGHTING | ACES FILMIC", (40, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (50, 210, 255), 1, cv2.LINE_AA)

    cv2.imwrite(OUT_SHIVA, scene1, [cv2.IMWRITE_JPEG_QUALITY, 96])
    print(f"[✓] Saved Shiva Agnyastra Master Render: {OUT_SHIVA}")

    # =========================================================================
    # RENDER 2: NANDI ASTRA (1000 BULLS DIVINE POWER)
    # =========================================================================
    print("[*] Generating Brahmastra Nandi Astra Scene...")
    scene2 = base_img.copy()

    # 1. Cyan/Blue + Gold Photometric Relighting
    scene2 = apply_deep_photometric_relighting(scene2, [actor_head, actor_left_hand, actor_right_hand], color_bgr=(255, 180, 30), intensity=1.9)

    # 2. Celestial Raging Nandi Bull Spirit Avatar
    composite_emissive_asset(scene2, nandi_asset, actor_head[0], actor_head[1] - 90, scale=0.68, intensity=1.60)

    # 3. Forearm Strength Conduits & Lightning Flares
    glow_nandi = np.zeros_like(scene2)
    for em in hand_emitters:
        cv2.circle(glow_nandi, em, 45, (255, 190, 40), -1)
        cv2.circle(glow_nandi, em, 24, (255, 255, 255), -1)
        cv2.line(glow_nandi, (em[0] - 200, em[1]), (em[0] + 200, em[1]), (255, 210, 80), 4, cv2.LINE_AA)
        cv2.line(scene2, (em[0] - 100, em[1]), (em[0] + 100, em[1]), (255, 255, 255), 2, cv2.LINE_AA)

    # Soft Blue-Cyan Bloom
    b_nandi = cv2.GaussianBlur(glow_nandi, (31, 31), 0)
    scene2 = cv2.addWeighted(scene2, 1.0, b_nandi, 0.85, 0)

    # ACES Filmic Tone Mapping & Cinemascope
    scene2 = apply_aces_tone_mapping(scene2)
    scene2 = apply_anamorphic_letterbox(scene2, aspect=2.39)

    cv2.putText(scene2, "BRAHMASTRA // SHOT 02: NANDI ASTRA (POWER OF 1000 BULLS)", (40, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(scene2, "CELESTIAL BULL AVATAR | CYAN LIGHTNING CONDUITS | 2.39:1 ANAMORPHIC CINEMA", (40, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 200, 50), 1, cv2.LINE_AA)

    cv2.imwrite(OUT_NANDI, scene2, [cv2.IMWRITE_JPEG_QUALITY, 96])
    print(f"[✓] Saved Nandi Astra Master Render: {OUT_NANDI}")

if __name__ == "__main__":
    main()
