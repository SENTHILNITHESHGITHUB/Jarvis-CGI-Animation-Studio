import os
import sys
import json
import subprocess

META_PATH = r"C:\Users\SVNITHESHPC\Desktop\Jarvis_Studios\protocol_shiva_mocap_youtube_metadata.json"

if not os.path.exists(META_PATH):
    print("Metadata file not found:", META_PATH)
    sys.exit(1)

with open(META_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

pack = f"""TITLE:
{data['title']}

DESCRIPTION:
{data['description']}

TAGS:
{", ".join(data['tags'])}

PINNED COMMENT:
{data['pinned_comment']}
"""

try:
    p = subprocess.Popen(["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"], stdin=subprocess.PIPE, text=True, encoding="utf-8")
    p.communicate(input=pack)
    print("=" * 70)
    print("SUCCESS: 100% Crisp Unicode MoCap Metadata Copied to Clipboard!")
    print("=" * 70)
except Exception as e:
    print("Clipboard copy error:", e)
