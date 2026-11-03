import os
import sys
import subprocess
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def build_3dcg_short():
    src_mp4 = r"C:\Users\SVNITHESHPC\Downloads\Jarvis\static\anime_renders\jarvis_3dcg_youtube_crossover_220855.mp4"
    out_dir = r"C:\Users\SVNITHESHPC\Desktop\Jarvis_Studios"
    os.makedirs(out_dir, exist_ok=True)
    out_mp4 = os.path.join(out_dir, "doraemon_3dcg_shorts_master.mp4")
    temp_dir = os.path.join(out_dir, "temp_shorts_render")
    os.makedirs(temp_dir, exist_ok=True)
    temp_video = os.path.join(temp_dir, "video_silent.mp4")
    temp_audio = os.path.join(temp_dir, "audio.aac")

    ffmpeg_exe = r"C:\Users\SVNITHESHPC\Downloads\Jarvis\venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

    print("[1/4] Extracting high-fidelity audio from 3D CGI master...")
    subprocess.run([
        ffmpeg_exe, "-y", "-i", src_mp4,
        "-vn", "-c:a", "aac", "-b:a", "192k", temp_audio
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    cap = cv2.VideoCapture(src_mp4)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Source video: {src_w}x{src_h} @ {fps} FPS, {total_frames} frames ({total_frames/fps:.1f}s)")

    target_w, target_h = 1080, 1920
    center_h = int(target_w * (src_h / src_w)) # 1080 * (720/1280) = 607.5 -> 608 px
    center_y = (target_h - center_h) // 2

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(temp_video, fourcc, fps, (target_w, target_h))

    # Pre-render static overlay elements with Pillow
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Gradient dark fades above and below the center frame
    for y in range(0, center_y):
        alpha = int(255 * (1.0 - (y / center_y) ** 1.5))
        draw.line([(0, y), (target_w, y)], fill=(10, 12, 20, 240))
    for y in range(center_y + center_h, target_h):
        rel = (y - (center_y + center_h)) / (target_h - (center_y + center_h))
        draw.line([(0, y), (target_w, y)], fill=(10, 12, 20, 240))

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 46)
        font_sub = ImageFont.truetype("arial.ttf", 30)
        font_badge = ImageFont.truetype("arialbd.ttf", 26)
        font_footer = ImageFont.truetype("arialbd.ttf", 32)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_badge = ImageFont.load_default()
        font_footer = ImageFont.load_default()

    # Top Header Card
    # Studio pill
    pill_box = (target_w // 2 - 260, 120, target_w // 2 + 260, 175)
    draw.rounded_rectangle(pill_box, radius=12, fill=(20, 35, 65, 230), outline=(0, 210, 255, 255), width=2)
    draw.text((target_w // 2, 147), "NITESH 3D CGI STUDIOS", fill=(0, 230, 255), font=font_badge, anchor="mm")

    # Main Title
    draw.text((target_w // 2, 240), "STAND BY ME DORAEMON 3D", fill=(255, 255, 255), font=font_title, anchor="mm")
    draw.text((target_w // 2, 305), "EPISODE 1: BAMBOO COPTER OVER TOKYO", fill=(255, 215, 0), font=font_sub, anchor="mm")

    # Framing border around the 3D cinema center
    draw.rectangle([0, center_y - 4, target_w, center_y], fill=(0, 210, 255, 255))
    draw.rectangle([0, center_y + center_h, target_w, center_y + center_h + 4], fill=(0, 210, 255, 255))

    # Bottom Footer Card
    foot_pill = (target_w // 2 - 340, target_h - 260, target_w // 2 + 340, target_h - 190)
    draw.rounded_rectangle(foot_pill, radius=16, fill=(255, 45, 85, 240), outline=(255, 255, 255, 255), width=2)
    draw.text((target_w // 2, target_h - 225), "SUBSCRIBE FOR EPISODE 2", fill=(255, 255, 255), font=font_footer, anchor="mm")

    draw.text((target_w // 2, target_h - 140), "Full 3D Skeletal Rigging • Bamboo Copter Flight Mechanics", fill=(180, 200, 220), font=font_sub, anchor="mm")
    draw.text((target_w // 2, target_h - 95), "100% Monetization Safe CGI Animation", fill=(120, 150, 180), font=font_badge, anchor="mm")

    overlay_np = np.array(overlay)
    ov_bgr = overlay_np[:, :, :3][:, :, ::-1]
    ov_alpha = (overlay_np[:, :, 3] / 255.0)[:, :, np.newaxis]

    print("[2/4] Rendering 9:16 vertical 1080x1920 frames with dynamic ambient blur...")
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 1. Background: Blurred & scaled ambient layer
        # Scale to fill vertical 1080x1920
        bg_scale = max(target_w / src_w, target_h / src_h)
        bg_w = int(src_w * bg_scale)
        bg_h = int(src_h * bg_scale)
        bg_resized = cv2.resize(frame, (bg_w, bg_h), interpolation=cv2.INTER_LINEAR)
        bg_x = (bg_w - target_w) // 2
        bg_y = (bg_h - target_h) // 2
        bg_crop = bg_resized[bg_y:bg_y+target_h, bg_x:bg_x+target_w]
        # Gaussian blur background
        bg_blurred = cv2.GaussianBlur(bg_crop, (51, 51), 0)
        # Darken background slightly
        bg_blurred = cv2.addWeighted(bg_blurred, 0.45, np.zeros_like(bg_blurred), 0.55, 0)

        # 2. Foreground: Center sharp 3D frame
        center_sharp = cv2.resize(frame, (target_w, center_h), interpolation=cv2.INTER_LANCZOS4)
        bg_blurred[center_y:center_y+center_h, 0:target_w] = center_sharp

        # 3. Composite static UI overlay
        final_frame = (bg_blurred * (1.0 - ov_alpha) + ov_bgr * ov_alpha).astype(np.uint8)

        writer.write(final_frame)
        frame_idx += 1
        if frame_idx % 200 == 0:
            print(f"  Rendered {frame_idx}/{total_frames} frames ({frame_idx/total_frames*100:.1f}%)...")

    cap.release()
    writer.release()
    print("[3/4] Frame rendering complete.")

    print("[4/4] Muxing video and audio streams with FFmpeg H.264/AAC...")
    subprocess.run([
        ffmpeg_exe, "-y",
        "-i", temp_video,
        "-i", temp_audio,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        out_mp4
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Clean up temp
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    file_size_mb = os.path.getsize(out_mp4) / (1024 * 1024)
    print(f"[SUCCESS] Stand by Me Doraemon 3D Shorts Master ready: {out_mp4} ({file_size_mb:.2f} MB)")

if __name__ == "__main__":
    build_3dcg_short()
