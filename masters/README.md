# Rendered Master Video Deliverables

The rendered high-bitrate master MP4 deliverables are stored locally in the studio directory on your Desktop:
`C:\Users\SVNITHESHPC\Desktop\Jarvis_Studios\`

### Master Video Deliverables:
1. **`doraemon_3dcg_shorts_master.mp4`** (42.23 MB)
   - 1080×1920 (9:16 Vertical YouTube Shorts Format)
   - True 3D GLB Character Rigs (Doraemon, Nobita, Shizuka, Gian, Suneo, Shin-chan)
   - 3D Bamboo Copter flight over Tokyo rooftops & 3D Anywhere Door portal opening.

2. **`doraemon_3dcg_feature_master.mp4`** (19.78 MB)
   - 1280×720 (16:9 Landscape Widescreen Standard YouTube Format)
   - Full 60-second broadcast episode with character voice acting.

3. **`protocol_shiva_mocap_action_short.mp4`** (13.20 MB)
   - 1080×1920 (60 FPS Biomechanical Kinematics Short)
   - 11-segment hierarchical skeleton with walk cycles, combat tiger guards, power repulsors, ground slam, and supersonic rocket flight.

### Regeneration Commands:
- To re-render the 3D Doraemon Shorts Master:
  ```bash
  python scripts/render_3dcg_shorts_converter.py
  ```
- To re-render the Protocol Shiva Biomechanical Kinematics Master:
  ```bash
  python scripts/mocap_action_cinema_factory.py
  ```
