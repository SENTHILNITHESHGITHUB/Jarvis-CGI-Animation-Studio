import subprocess
import sys

metadata_text = """TITLE:
STAND BY ME DORAEMON 3D (2026) // Bamboo Copter Tokyo Flight 🚁✨ #Shorts #Doraemon #3DAnimation #CGI

DESCRIPTION:
Experience the iconic 3D CGI world of STAND BY ME DORAEMON! 🚁✨
In this episode, Doraemon, Nobita, Shizuka, Gian, and Suneo activate their 3D Bamboo Copters and soar high above the Kasukabe and Tokyo neighborhood rooftops!

🎬 3D CGI ANIMATION PRODUCTION BREAKDOWN:
• Skeletal Rigging: Anatomical digital bone hierarchies driving full 3D character meshes.
• Kinematics (FK & IK): Realistic arm swings, stride cycles, and balance mechanics.
• Spline Keyframing: Smooth polynomial easing curves for natural organic momentum.
• Secondary Physics: Wind turbulence simulation, rotor drift, and dynamic camera tracking.

Produced by: Nitesh 3D CGI Studios
Software Pipeline: Three.js PBR Engine, Blender Rigging, GLTF 3D Shaders, Edge Audio Synthesis
Genre: 3D CGI Family Adventure / Anime Cinematic

🔔 SUBSCRIBE to Nitesh 3D CGI Studios for Episode 2!
👍 LIKE and SHARE if you grew up watching Doraemon!

TAGS:
#Doraemon #StandByMeDoraemon #3DAnimation #CGI #CharacterAnimation #Shorts #Anime #Nobita #BambooCopter #Blender #ThreeJS #YouTubeShorts #AnimationStudio
"""

def copy_to_clipboard(text: str):
    try:
        proc = subprocess.Popen(['powershell', '-NoProfile', '-Command', '$input | Set-Clipboard'], stdin=subprocess.PIPE, text=True, encoding='utf-8')
        proc.communicate(input=text)
        print("[SUCCESS] Stand by Me Doraemon 3D metadata successfully copied to Windows Clipboard!")
    except Exception as e:
        print(f"[ERROR] Failed to copy to clipboard: {e}")

if __name__ == "__main__":
    copy_to_clipboard(metadata_text)
