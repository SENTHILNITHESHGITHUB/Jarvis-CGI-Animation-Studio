"""
================================================================================
⚡ APPLY MOCAP KEYFRAMES TO BLENDER ASTRAVERSE HERO RIG ⚡
================================================================================
Reads a mocap recording JSON (from webcam_to_blender_mocap.py) and keyframes
every bone on the Astraverse_Hero_Rig in Astraverse_3D_Virtual_Studio.blend.
================================================================================
"""

import bpy
import json
import sys
import os

def apply_mocap(json_path, blend_path=None):
    if not os.path.exists(json_path):
        print(f"[!] Mocap JSON not found: {json_path}")
        return False
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    frames = data.get("frames", [])
    if not frames:
        print("[!] No frames found in mocap data.")
        return False
        
    print(f"[*] Applying {len(frames)} mocap frames to Astraverse_Hero_Rig...")
    
    arm_obj = bpy.data.objects.get("Astraverse_Hero_Rig")
    if not arm_obj:
        print("[!] Astraverse_Hero_Rig not found in blend file!")
        return False
        
    # Clear existing animation
    if arm_obj.animation_data:
        arm_obj.animation_data_clear()
        
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')
    pb = arm_obj.pose.bones
    
    for bone_name in pb.keys():
        pb[bone_name].rotation_mode = 'XYZ'
        
    total_frames = len(frames)
    
    for f_idx, f_data in enumerate(frames):
        f_num = f_idx + 1
        bones_dict = f_data.get("bones", {})
        
        for b_name, b_info in bones_dict.items():
            if b_name in pb:
                bone = pb[b_name]
                loc = b_info.get("location")
                rot = b_info.get("rotation_euler")
                
                if loc is not None:
                    bone.location = (float(loc[0]), float(loc[1]), float(loc[2]))
                    bone.keyframe_insert(data_path="location", frame=f_num)
                    
                if rot is not None:
                    bone.rotation_euler = (float(rot[0]), float(rot[1]), float(rot[2]))
                    bone.keyframe_insert(data_path="rotation_euler", frame=f_num)
                    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Adjust scene timeline
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = total_frames
    
    # Adjust hand fire particle systems to match animation length
    for side in ["L", "R"]:
        emitter = bpy.data.objects.get(f"Hand_Fire_Emitter_{side}")
        if emitter and emitter.particle_systems:
            for ps in emitter.particle_systems:
                ps.settings.frame_end = total_frames
                
    # Save blend file
    save_path = blend_path or bpy.data.filepath
    if save_path:
        bpy.ops.wm.save_as_mainfile(filepath=save_path)
        print(f"⚡ [SUCCESS] Injected {total_frames} mocap frames into {save_path}! ⚡")
        
    return True

if __name__ == "__main__":
    # Check command line arguments after '--'
    args = []
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        
    if args:
        mocap_json = args[0]
        apply_mocap(mocap_json)
    else:
        default_json = r"C:\Users\SVNITHESHPC\Downloads\Astraverse_Blender_Studio\latest_mocap_take.json"
        apply_mocap(default_json)
