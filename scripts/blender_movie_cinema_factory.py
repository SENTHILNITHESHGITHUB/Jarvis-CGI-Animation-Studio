import bpy
import os
import math

def build_movie_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # 1. 1080x1920 9:16 Vertical Cinema Settings
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 120  # 4 seconds

    # Eevee Cinematic PBR
    eevee = scene.eevee
    eevee.use_bloom = True
    eevee.bloom_threshold = 0.85
    eevee.bloom_intensity = 0.04
    eevee.use_gtao = True
    eevee.gtao_distance = 1.2
    eevee.gtao_factor = 1.3
    eevee.use_ssr = True
    eevee.use_ssr_refraction = True
    eevee.use_motion_blur = True
    eevee.taa_render_samples = 32  # Fast & sharp on Haswell i5

    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = 0.12

    # 2. World Lighting (Atmospheric Japanese Afternoon Sky)
    world = bpy.data.worlds.new("Tokyo_Sky")
    scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()
    bg = nodes.new(type='ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.50, 0.72, 0.98, 1.0)
    bg.inputs['Strength'].default_value = 1.15
    out = nodes.new(type='ShaderNodeOutputWorld')
    links.new(bg.outputs['Background'], out.inputs['Surface'])

    # 3. Three-Point Movie Lighting (Illuminating the Front Face)
    # Key Sun Light (Warm golden sunlight hitting the front face)
    sun_data = bpy.data.lights.new(name="Sun_Key", type='SUN')
    sun_data.energy = 5.2
    sun_data.color = (1.0, 0.96, 0.90)
    sun_data.angle = math.radians(3.5)
    sun_obj = bpy.data.objects.new(name="Sun_Key", object_data=sun_data)
    sun_obj.rotation_euler = (math.radians(50), math.radians(-20), math.radians(35))
    bpy.context.collection.objects.link(sun_obj)

    # Rim Backlight (Accentuates Doraemon's silhouette from behind)
    rim_data = bpy.data.lights.new(name="Rim_Light", type='SPOT')
    rim_data.energy = 260.0
    rim_data.color = (0.7, 0.92, 1.0)
    rim_data.spot_size = math.radians(70)
    rim_data.spot_blend = 0.4
    rim_obj = bpy.data.objects.new(name="Rim_Light", object_data=rim_data)
    rim_obj.location = (1.5, 2.4, 2.8)
    rim_obj.rotation_euler = (math.radians(-135), math.radians(15), math.radians(40))
    bpy.context.collection.objects.link(rim_obj)

    # 4. Import Tokyo Street Environment
    street_path = r"C:\Users\SVNITHESHPC\Downloads\models_decompressed\streets_blender_ready.glb"
    if os.path.exists(street_path):
        bpy.ops.import_scene.gltf(filepath=street_path)
        for obj in bpy.context.selected_objects:
            obj.location = (0, 0, -0.05)

    # 5. Import Blooming Sakura Cherry Blossom Tree in Background
    sakura_path = r"C:\Users\SVNITHESHPC\Downloads\models_decompressed\sakura_blender_ready.glb"
    if os.path.exists(sakura_path):
        bpy.ops.import_scene.gltf(filepath=sakura_path)
        for obj in bpy.context.selected_objects:
            obj.location = (-2.8, -4.5, 0)
            obj.scale = (1.3, 1.3, 1.3)

    # 6. Import Doraemon Rig
    dora_path = r"C:\Users\SVNITHESHPC\Downloads\models_decompressed\doraemon_blender_ready.glb"
    bpy.ops.import_scene.gltf(filepath=dora_path)
    armature = None
    for obj in bpy.context.selected_objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break

    if armature:
        armature.location = (0, 0, 0)
        # Rotate 180 degrees to FACE the camera!
        armature.rotation_euler = (0, 0, math.radians(180))
        
        # Pick high-energy animation: 'dance', 'walk', 'wave', 'cheer'
        target_act = None
        for name in ['dance', 'victory', 'cheer', 'walk', 'wave']:
            for act in bpy.data.actions:
                if name in act.name.lower():
                    target_act = act
                    break
            if target_act:
                break
        
        if target_act and armature.animation_data:
            armature.animation_data.action = target_act
            print(f"[ANIMATION] Assigned Action: {target_act.name}")

    # 7. Add 3D Bamboo Copter (Take-copter) on Doraemon's Head
    copter_mat = bpy.data.materials.new(name="Bamboo_Copter_Gold")
    copter_mat.use_nodes = True
    c_bsdf = copter_mat.node_tree.nodes.get('Principled BSDF')
    if c_bsdf:
        c_bsdf.inputs['Base Color'].default_value = (1.0, 0.84, 0.0, 1.0) # Vibrant anime gold
        c_bsdf.inputs['Roughness'].default_value = 0.25
        c_bsdf.inputs['Metallic'].default_value = 0.35

    # Suction Base
    bpy.ops.mesh.primitive_cylinder_add(radius=0.065, depth=0.04, location=(0, 0, 1.22))
    suction = bpy.context.active_object
    suction.name = "Copter_Base"
    suction.data.materials.append(copter_mat)

    # Shaft
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.14, location=(0, 0, 1.30))
    shaft = bpy.context.active_object
    shaft.name = "Copter_Shaft"
    shaft.data.materials.append(copter_mat)

    # Rotor Blade (Animate Rotation)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.38))
    rotor = bpy.context.active_object
    rotor.name = "Copter_Rotor"
    rotor.scale = (0.50, 0.05, 0.014)
    rotor.data.materials.append(copter_mat)

    # Animate Rotor Spin across timeline
    for f in range(1, 121, 5):
        rotor.rotation_euler.z = f * 1.8
        rotor.keyframe_insert(data_path="rotation_euler", frame=f)

    # 8. Cinematic Movie Camera (Positioned on the front side facing Doraemon's face!)
    cam_data = bpy.data.cameras.new(name="Cinema_Camera")
    cam_data.lens = 52.0  # 52mm portrait lens
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = 2.80
    cam_data.dof.aperture_fstop = 2.4 # Gorgeous soft background bokeh
    cam_obj = bpy.data.objects.new(name="Cinema_Camera", object_data=cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Frame 1: Hero eye-level framing directly facing Doraemon
    cam_obj.location = (0.05, -2.85, 0.95)
    cam_obj.rotation_euler = (math.radians(88), math.radians(0), math.radians(2))
    cam_obj.keyframe_insert(data_path="location", frame=1)
    cam_obj.keyframe_insert(data_path="rotation_euler", frame=1)

    # Frame 60: Dynamic upward tilt
    cam_obj.location = (-0.08, -2.60, 0.88)
    cam_obj.rotation_euler = (math.radians(91), math.radians(0), math.radians(-3))
    cam_obj.keyframe_insert(data_path="location", frame=60)
    cam_obj.keyframe_insert(data_path="rotation_euler", frame=60)

    # Frame 120: Dynamic close-up finish
    cam_obj.location = (0.02, -2.45, 0.92)
    cam_obj.rotation_euler = (math.radians(89), math.radians(0), math.radians(1))
    cam_obj.keyframe_insert(data_path="location", frame=120)
    cam_obj.keyframe_insert(data_path="rotation_euler", frame=120)

    # Output & Save
    out_dir = r"C:\Users\SVNITHESHPC\Desktop\Jarvis_Studios\blender_renders"
    os.makedirs(out_dir, exist_ok=True)
    blend_path = os.path.join(out_dir, "doraemon_movie_grade_master.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"[SAVED] Blend file: {blend_path}")

    # Render Still Benchmark Frame 25
    scene.frame_set(25)
    bench_png = os.path.join(out_dir, "movie_grade_frame_25.png")
    scene.render.filepath = bench_png
    print(f"[RENDERING] Benchmark frame 25 to {bench_png}...")
    bpy.ops.render.render(write_still=True)
    print(f"[SUCCESS] Movie grade benchmark frame ready: {bench_png}")

if __name__ == '__main__':
    build_movie_scene()
