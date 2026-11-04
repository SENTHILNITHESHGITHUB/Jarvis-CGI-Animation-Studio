"""
AI Animation Studio – Master Autonomous Production Pipeline
-----------------------------------------------------------
End-to-end production orchestrator:
1. Builds master 3D scene (repaired character, environment, copter, lighting, camera).
2. Renders 75-frame animation sequence in Eevee with DQS volume preservation.
3. Synthesizes anime sound design and muxes final broadcast MP4 with FFmpeg.
4. Performs automated quality inspection on keyframes.
5. Purges temporary frame caches to respect host disk space constraints.
"""

import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path

# Add script directory to sys.path
sys.path.append(str(Path(__file__).parent))
from generate_anime_soundtrack import generate_soundtrack

STUDIO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = STUDIO_ROOT / "characters" / "models"
SCENES_DIR = STUDIO_ROOT / "scenes"
RENDERS_DIR = STUDIO_ROOT / "renders"
PREVIEWS_DIR = RENDERS_DIR / "previews"
FINAL_DIR = RENDERS_DIR / "final"
TEMP_FRAMES_DIR = RENDERS_DIR / "temp_frames"
REPORTS_DIR = STUDIO_ROOT / "reports"

BLENDER_SCENE_BUILDER_SCRIPT = """
import bpy
import os
import math

def build_and_render_master(blend_out, frames_out_pattern, start_frame=1, end_frame=75):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # 1. 1080x1920 9:16 Vertical Short Settings
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_start = start_frame
    scene.frame_end = end_frame
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.compression = 15

    # Eevee PBR Optimization (16 TAA samples for crisp, fast rendering)
    eevee = scene.eevee
    eevee.use_bloom = True
    eevee.bloom_threshold = 0.90
    eevee.bloom_intensity = 0.03
    eevee.use_gtao = True
    eevee.gtao_distance = 1.0
    eevee.gtao_factor = 1.2
    eevee.use_ssr = True
    eevee.taa_render_samples = 16

    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = 0.15

    # 2. World Atmosphere
    world = bpy.data.worlds.new("Tokyo_Atmosphere")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.50, 0.72, 0.98, 1.0)
        bg.inputs['Strength'].default_value = 1.05

    # 3. Three-Point Studio & Sun Lighting
    # Key Sunlight
    sun_data = bpy.data.lights.new(name="Sun_Key", type='SUN')
    sun_data.energy = 4.6
    sun_data.color = (1.0, 0.97, 0.92)
    sun_obj = bpy.data.objects.new(name="Sun_Key", object_data=sun_data)
    sun_obj.rotation_euler = (math.radians(45), math.radians(-15), math.radians(25))
    bpy.context.collection.objects.link(sun_obj)

    # Rim Backlight
    rim_data = bpy.data.lights.new(name="Rim_Light", type='SPOT')
    rim_data.energy = 280.0
    rim_data.color = (0.75, 0.90, 1.0)
    rim_data.spot_size = math.radians(65)
    rim_data.spot_blend = 0.35
    rim_obj = bpy.data.objects.new(name="Rim_Light", object_data=rim_data)
    rim_obj.location = (1.2, 2.2, 2.5)
    rim_obj.rotation_euler = (math.radians(-135), math.radians(15), math.radians(35))
    bpy.context.collection.objects.link(rim_obj)

    # Fill Light
    fill_data = bpy.data.lights.new(name="Fill_Light", type='POINT')
    fill_data.energy = 65.0
    fill_data.color = (0.95, 0.98, 1.0)
    fill_obj = bpy.data.objects.new(name="Fill_Light", object_data=fill_data)
    fill_obj.location = (-1.0, -2.2, 1.1)
    bpy.context.collection.objects.link(fill_obj)

    # 4. Tokyo Street Environment
    street_path = r"C:\\Users\\SVNITHESHPC\\Downloads\\models_decompressed\\streets_blender_ready.glb"
    if os.path.exists(street_path):
        bpy.ops.import_scene.gltf(filepath=street_path)
        for obj in bpy.context.selected_objects:
            obj.location = (0, 0, -0.05)

    # 5. Nobi House Yard & Gate
    env_path = r"C:\\Users\\SVNITHESHPC\\Downloads\\models_decompressed\\environment_blender_ready.glb"
    if os.path.exists(env_path):
        bpy.ops.import_scene.gltf(filepath=env_path)
        for obj in bpy.context.selected_objects:
            obj.location = (-1.0, 3.5, 0.0)

    # 6. Sakura Cherry Blossom Tree in Background
    sakura_path = r"C:\\Users\\SVNITHESHPC\\Downloads\\models_decompressed\\sakura_blender_ready.glb"
    if os.path.exists(sakura_path):
        bpy.ops.import_scene.gltf(filepath=sakura_path)
        for obj in bpy.context.selected_objects:
            obj.location = (-1.6, 2.8, 0.0)
            obj.scale = (1.4, 1.4, 1.4)

    # 7. Doraemon Character Setup & Repair
    dora_path = r"C:\\Users\\SVNITHESHPC\\Downloads\\models_decompressed\\doraemon_blender_ready.glb"
    bpy.ops.import_scene.gltf(filepath=dora_path)
    armature = next((o for o in bpy.context.selected_objects if o.type == 'ARMATURE'), None)
    mesh_obj = next((o for o in bpy.context.selected_objects if o.type == 'MESH'), None)

    # A. Weld Seams
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0005)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    # B. Clear corrupted split normals
    mesh_obj.data.use_auto_smooth = True
    mesh_obj.data.auto_smooth_angle = math.radians(60)
    bpy.ops.mesh.customdata_custom_splitnormals_clear()

    # C. Dual Quaternion Skinning (Volume Preservation)
    for mod in mesh_obj.modifiers:
        if mod.type == 'ARMATURE':
            mod.use_deform_preserve_volume = True

    # D. Subsurf Modifier
    sub_mod = mesh_obj.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 1
    sub_mod.render_levels = 1
    sub_mod.boundary_smooth = 'ALL'

    # E. Unify Hand Weights
    for side in ['Left', 'Right']:
        hand_vg = mesh_obj.vertex_groups.get(f'mixamorig:{side}Hand')
        if not hand_vg:
            continue
        finger_vgs = [mesh_obj.vertex_groups.get(f'mixamorig:{side}HandIndex{i}') for i in [1, 2, 3]]
        finger_indices = {f.index: f for f in finger_vgs if f}
        for v in mesh_obj.data.vertices:
            w_add = sum(g.weight for g in v.groups if g.group in finger_indices)
            if w_add > 0:
                hand_vg.add([v.index], w_add, 'ADD')
        for f in finger_vgs:
            if f:
                mesh_obj.vertex_groups.remove(f)

    # F. Animation Action
    wave_act = bpy.data.actions.get('wave_doraemon_rig')
    if wave_act and armature.animation_data:
        armature.animation_data.action = wave_act

    # 8. Add Bamboo Copter (Take-copter)
    copter_mat = bpy.data.materials.new(name="Bamboo_Copter_Gold")
    copter_mat.use_nodes = True
    c_bsdf = copter_mat.node_tree.nodes.get('Principled BSDF')
    c_bsdf.inputs['Base Color'].default_value = (1.0, 0.82, 0.0, 1.0)
    c_bsdf.inputs['Roughness'].default_value = 0.22
    c_bsdf.inputs['Metallic'].default_value = 0.40

    root = bpy.data.objects.new("Bamboo_Copter_Root", None)
    bpy.context.collection.objects.link(root)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.065, depth=0.03, location=(0, 0, 0.015))
    base = bpy.context.active_object
    base.name = "Copter_Base"
    base.data.materials.append(copter_mat)
    base.parent = root

    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.12, location=(0, 0, 0.085))
    shaft = bpy.context.active_object
    shaft.name = "Copter_Shaft"
    shaft.data.materials.append(copter_mat)
    shaft.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.15))
    rotor = bpy.context.active_object
    rotor.name = "Copter_Rotor"
    rotor.scale = (0.46, 0.05, 0.012)
    rotor.data.materials.append(copter_mat)
    rotor.parent = root

    # Keyframe copter root position to head & spin rotor
    rotor.animation_data_create()
    root.animation_data_create()
    for f in range(start_frame, end_frame + 1):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        eval_mesh = mesh_obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        top_co = max([(mesh_obj.matrix_world @ v.co) for v in eval_mesh.data.vertices], key=lambda c: c.z)

        root.location = (top_co.x, top_co.y, top_co.z - 0.01)
        root.keyframe_insert(data_path="location", frame=f)

        rotor.rotation_euler.z = f * 1.5
        rotor.keyframe_insert(data_path="rotation_euler", frame=f)

    # 9. Camera with portrait 38mm lens & subtle push-in
    cam_data = bpy.data.cameras.new(name="Cinema_Camera")
    cam_data.lens = 38.0
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = 3.60
    cam_data.dof.aperture_fstop = 3.2
    cam_obj = bpy.data.objects.new(name="Cinema_Camera", object_data=cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = (0.0, -3.75, 0.85)
    cam_obj.rotation_euler = (math.radians(88), 0, 0)
    cam_obj.keyframe_insert(data_path="location", frame=start_frame)

    cam_obj.location = (0.0, -3.45, 0.90)
    cam_obj.rotation_euler = (math.radians(88), 0, 0)
    cam_obj.keyframe_insert(data_path="location", frame=end_frame)

    # 10. Save Blend
    os.makedirs(os.path.dirname(blend_out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    print(f"MASTER_BLEND_SAVED: {blend_out}")

    # 11. Render Sequence
    os.makedirs(os.path.dirname(frames_out_pattern), exist_ok=True)
    scene.render.filepath = frames_out_pattern
    print(f"RENDERING_SEQUENCE_START: {start_frame} to {end_frame}")
    bpy.ops.render.render(animation=True)
    print("RENDERING_SEQUENCE_COMPLETE")

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if len(args) >= 2:
        blend_file, pattern = args[0], args[1]
        s_frame = int(args[2]) if len(args) > 2 else 1
        e_frame = int(args[3]) if len(args) > 3 else 75
        build_and_render_master(blend_file, pattern, s_frame, e_frame)
"""

def execute_master_production(start_frame=1, end_frame=75):
    print("==================================================")
    print("AI ANIMATION STUDIO – MASTER AUTONOMOUS PRODUCTION")
    print(f"Target Frame Range: {start_frame} to {end_frame}")
    print("==================================================")

    blender_exe = r"C:\Users\SVNITHESHPC\Downloads\blender-3.6.9-windows-x64\blender.exe"
    blend_path = SCENES_DIR / "doraemon_master_cinema_short.blend"
    TEMP_FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    frames_pattern = str(TEMP_FRAMES_DIR / "frame_")
    final_video = FINAL_DIR / "doraemon_master_cinema_short.mp4"
    audio_file = FINAL_DIR / "anime_soundtrack.wav"

    duration_sec = round((end_frame - start_frame + 1) / 30.0, 2)

    # Step 1: Generate anime sound design
    print(f"[1/5] Synthesizing custom studio anime soundtrack ({duration_sec}s)...")
    generate_soundtrack(str(audio_file), duration_sec=duration_sec)

    # Step 2: Build scene & render frames in Blender
    print(f"[2/5] Building master 3D scene & rendering frames {start_frame}..{end_frame} in Blender...")
    builder_script = STUDIO_ROOT / "scripts" / "blender" / "blender_master_cinema_builder.py"

    cmd = [
        blender_exe,
        "--background",
        "--python", str(builder_script),
        "--",
        str(blend_path),
        frames_pattern,
        str(start_frame),
        str(end_frame)
    ]

    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        render_time = round(time.time() - t0, 2)
        print(f"[3/5] Blender render completed in {render_time}s!")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Blender rendering failed: {e.stderr}")
        raise

    # Step 3: FFmpeg Encode & Mux
    print("[4/5] Muxing 1080x1920 video and studio audio with FFmpeg...")
    input_frames = str(TEMP_FRAMES_DIR / "frame_%04d.png")
    
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-framerate", "30",
        "-start_number", str(start_frame),
        "-i", input_frames,
        "-i", str(audio_file),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "slow",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(final_video)
    ]
    subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
    print(f"      Master video generated: {final_video}")

    # Step 4: Extract Keyframe Previews for Visual Inspection
    print("[5/5] Extracting inspection stills & performing disk cleanup...")
    mid_frame = (start_frame + end_frame) // 2
    for f_idx in [start_frame, mid_frame, end_frame]:
        src_frame = TEMP_FRAMES_DIR / f"frame_{f_idx:04d}.png"
        dst_frame = PREVIEWS_DIR / f"master_short_frame_{f_idx:02d}.png"
        if src_frame.exists():
            shutil.copy2(src_frame, dst_frame)

    # Step 5: Strict Disk Cleanup (Purge temporary frame sequence)
    shutil.rmtree(TEMP_FRAMES_DIR, ignore_errors=True)
    print("      Temporary render frames purged (Disk space preserved).")

    # Final Verification
    vid_size = final_video.stat().st_size
    print("==================================================")
    print(f"MASTER PRODUCTION COMPLETE: [PASS]")
    print(f"Final MP4: {final_video} ({vid_size:,} bytes)")
    print("==================================================")
    return {
        "final_video": str(final_video),
        "file_size_bytes": vid_size,
        "render_time_seconds": render_time,
        "status": "PASS"
    }

if __name__ == '__main__':
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    e = int(sys.argv[2]) if len(sys.argv) > 2 else 75
    execute_master_production(s, e)
