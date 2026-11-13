"""
================================================================================
⚡ RENDER ASTRAVERSE 3D CINEMATIC FILM // BLENDER EEVEE + FFMPEG ⚡
================================================================================
Renders the animated 3D Virtual Production scene from Blender and compiles
it into a 2.39:1 Hollywood Cinemascope MP4 and animated GIF preview.
================================================================================
"""

import os
import sys
import subprocess
import shutil

BASE_DIR = r"C:\Users\SVNITHESHPC\Downloads\Astraverse_Blender_Studio"
BLENDER_EXE = r"C:\Users\SVNITHESHPC\Downloads\blender-3.6.9-windows-x64\blender.exe"
BLEND_FILE = os.path.join(BASE_DIR, "Astraverse_3D_Virtual_Studio.blend")
FRAMES_DIR = os.path.join(BASE_DIR, "render_frames")
OUTPUT_MP4 = os.path.join(r"C:\Users\SVNITHESHPC\Downloads", "ASTRAVERSE_3D_VIRTUAL_STUDIO_SAMPLE.mp4")
OUTPUT_GIF = r"C:\Users\SVNITHESHPC\.gemini\antigravity\brain\972199e1-0395-45a5-b415-be1edfa58c26\blender_astraverse_3d_preview.gif"
FFMPEG_EXE = r"C:\Users\SVNITHESHPC\Downloads\Jarvis\venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

def render_film(start_frame=30, end_frame=65):
    print("=" * 70)
    print(f"⚡ RENDERING ASTRAVERSE 3D CINEMATIC SHOT: FRAMES {start_frame} TO {end_frame} ⚡")
    print("=" * 70)
    
    os.makedirs(FRAMES_DIR, exist_ok=True)
    out_pattern = os.path.join(FRAMES_DIR, "frame_####")
    
    # 1. Run Blender Headless Render
    cmd_blender = [
        BLENDER_EXE,
        "-b",
        BLEND_FILE,
        "-s", str(start_frame),
        "-e", str(end_frame),
        "-a",
        "-o", out_pattern
    ]
    
    print(f"[*] Executing Blender EEVEE renderer: frames {start_frame}-{end_frame}...")
    res = subprocess.run(cmd_blender)
    if res.returncode != 0:
        print("[!] Blender render failed!")
        return False
        
    print(f"[OK] Rendered frames saved to {FRAMES_DIR}")
    
    # 2. Compile to 2.39:1 Cinemascope MP4 via FFmpeg
    input_pattern = os.path.join(FRAMES_DIR, "frame_%04d.png")
    cmd_mp4 = [
        FFMPEG_EXE,
        "-y",
        "-framerate", "24",
        "-i", input_pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        OUTPUT_MP4
    ]
    
    print(f"[*] Compiling master MP4 to: {OUTPUT_MP4}...")
    subprocess.run(cmd_mp4)
    print(f"⚡ [SUCCESS] MASTER 3D CINEMATIC FILM READY: {OUTPUT_MP4} ⚡")
    
    # 3. Compile High-Quality Preview GIF
    cmd_gif = [
        FFMPEG_EXE,
        "-y",
        "-framerate", "18",
        "-i", input_pattern,
        "-vf", "scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        OUTPUT_GIF
    ]
    print(f"[*] Generating animated GIF preview to: {OUTPUT_GIF}...")
    subprocess.run(cmd_gif)
    print(f"⚡ [SUCCESS] PREVIEW GIF SAVED! ⚡\n")
    return True

if __name__ == "__main__":
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    e = int(sys.argv[2]) if len(sys.argv) > 2 else 55
    render_film(s, e)
