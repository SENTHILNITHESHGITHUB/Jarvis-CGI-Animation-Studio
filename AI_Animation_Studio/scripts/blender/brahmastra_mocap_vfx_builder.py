import bpy
import os
import math
import sys
from pathlib import Path

STUDIO_ROOT = Path(r"C:\Users\SVNITHESHPC\Downloads\AI_Animation_Studio")
ASSETS_DIR = Path(r"C:\Users\SVNITHESHPC\Downloads\AI_VFX_Realtime_Suite")
MANDALA_TEXTURE = ASSETS_DIR / "Doctor-Strange-Hands" / "magic_circles" / "magic_circle_1.png"
FIRE_TEXTURE = ASSETS_DIR / "assets" / "clean_brahmastra_fire_feathered.jpg"
WARRIOR_MODEL = Path(r"C:\Users\SVNITHESHPC\Downloads\models_decompressed\jaian_blender_ready.glb")

def build_brahmastra_scene(blend_out, render_out_pattern=None, still_frame=20):
    print("[BRAHMASTRA ENGINE] Initializing 3D Mesh MoCap Scene...")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # 1. 1080x1920 9:16 Vertical Cinema Settings
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 60

    # Eevee Cinematic PBR & Bloom (for radiant fire glow)
    eevee = scene.eevee
    eevee.use_bloom = True
    eevee.bloom_threshold = 0.80
    eevee.bloom_intensity = 0.08
    eevee.bloom_radius = 6.5
    eevee.bloom_color = (1.0, 0.72, 0.2) # Warm golden-saffron bloom
    eevee.use_gtao = True
    eevee.gtao_distance = 1.2
    eevee.gtao_factor = 1.3
    eevee.use_ssr = True
    eevee.use_ssr_refraction = True
    eevee.taa_render_samples = 16

    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'High Contrast'
    scene.view_settings.exposure = 0.10

    # 2. Celestial Cosmic Atmosphere (Himalayan Night Sky)
    world = bpy.data.worlds.new("Brahmastra_Cosmic_Sky")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.02, 0.03, 0.07, 1.0) # Deep cosmic indigo void
        bg.inputs['Strength'].default_value = 0.6

    # 3. Cinematic Rim & Backlight
    # Cool Cyan Rim Light (Sharp silhouette separation)
    rim_data = bpy.data.lights.new(name="Rim_Cyan", type='SPOT')
    rim_data.energy = 550.0
    rim_data.color = (0.2, 0.65, 1.0) # Celestial Astra cyan
    rim_data.spot_size = math.radians(70)
    rim_data.spot_blend = 0.35
    rim_obj = bpy.data.objects.new(name="Rim_Cyan", object_data=rim_data)
    rim_obj.location = (0.0, 3.2, 3.0)
    rim_obj.rotation_euler = (math.radians(-145), 0, 0)
    bpy.context.collection.objects.link(rim_obj)

    # Ambient Top Fill
    top_data = bpy.data.lights.new(name="Top_Fill", type='SUN')
    top_data.energy = 1.2
    top_data.color = (0.4, 0.5, 0.8)
    top_obj = bpy.data.objects.new(name="Top_Fill", object_data=top_data)
    top_obj.rotation_euler = (math.radians(65), math.radians(10), 0)
    bpy.context.collection.objects.link(top_obj)

    # 4. Reflective Temple Stone Floor
    bpy.ops.mesh.primitive_plane_add(size=25.0, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Temple_Floor"
    floor_mat = bpy.data.materials.new(name="Stone_Temple_Mat")
    floor_mat.use_nodes = True
    f_bsdf = floor_mat.node_tree.nodes.get('Principled BSDF')
    if f_bsdf:
        f_bsdf.inputs['Base Color'].default_value = (0.05, 0.06, 0.09, 1.0)
        f_bsdf.inputs['Roughness'].default_value = 0.25 # Polished reflective dark stone
        f_bsdf.inputs['Metallic'].default_value = 0.40
    floor.data.materials.append(floor_mat)

    # 5. Import 3D Humanoid Warrior Rig & Mesh
    bpy.ops.import_scene.gltf(filepath=str(WARRIOR_MODEL))
    armature = next((o for o in bpy.context.selected_objects if o.type == 'ARMATURE'), None)
    mesh_obj = next((o for o in bpy.context.selected_objects if o.type == 'MESH'), None)

    # A. Weld Seams & Recalculate Normals (Zero cracks!)
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0005)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    mesh_obj.data.use_auto_smooth = True
    mesh_obj.data.auto_smooth_angle = math.radians(60)
    bpy.ops.mesh.customdata_custom_splitnormals_clear()

    # B. Dual Quaternion Skinning (DQS Volume Preservation)
    for mod in mesh_obj.modifiers:
        if mod.type == 'ARMATURE':
            mod.use_deform_preserve_volume = True

    # C. Assign Celestial Shiva Warrior Armor Material
    armor_mat = bpy.data.materials.new(name="Celestial_Shiva_Armor")
    armor_mat.use_nodes = True
    bsdf = armor_mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.08, 0.09, 0.12, 1.0) # Sleek obsidian nano-armor
        bsdf.inputs['Metallic'].default_value = 0.85
        bsdf.inputs['Roughness'].default_value = 0.22
    mesh_obj.data.materials.clear()
    mesh_obj.data.materials.append(armor_mat)

    # D. Assign Dynamic Combat Action
    combat_act = bpy.data.actions.get('victory_jaian_rig')
    if combat_act and armature.animation_data:
        armature.animation_data.action = combat_act
        print(f"[ACTION ASSIGNED] {combat_act.name} (length: {combat_act.frame_range})")

    # 6. Build Sacred Revolving 3D Brahmāstra Mandalas
    mandala_mat = bpy.data.materials.new(name="Brahmastra_Mandala_Gold")
    mandala_mat.use_nodes = True
    mandala_mat.blend_method = 'BLEND'
    m_nodes = mandala_mat.node_tree.nodes
    m_links = mandala_mat.node_tree.links
    m_nodes.clear()

    out_node = m_nodes.new(type='ShaderNodeOutputMaterial')
    emit_node = m_nodes.new(type='ShaderNodeEmission')
    emit_node.inputs['Color'].default_value = (1.0, 0.72, 0.10, 1.0) # Incandescent Solar Gold
    emit_node.inputs['Strength'].default_value = 16.0 # Intensely emissive bloom

    tex_node = m_nodes.new(type='ShaderNodeTexImage')
    if MANDALA_TEXTURE.exists():
        tex_node.image = bpy.data.images.load(str(MANDALA_TEXTURE))

    mix_node = m_nodes.new(type='ShaderNodeMixShader')
    trans_node = m_nodes.new(type='ShaderNodeBsdfTransparent')

    m_links.new(tex_node.outputs['Alpha'], mix_node.inputs['Fac'])
    m_links.new(trans_node.outputs['BSDF'], mix_node.inputs[1])
    m_links.new(emit_node.outputs['Emission'], mix_node.inputs[2])
    m_links.new(mix_node.outputs['Shader'], out_node.inputs['Surface'])

    # Helper function to create tracked mandala
    def create_tracked_mandala(name, hand_bone_name, clockwise=True):
        bpy.ops.mesh.primitive_circle_add(radius=0.42, fill_type='NGON', location=(0, 0, 0))
        mandala = bpy.context.active_object
        mandala.name = name
        mandala.data.materials.append(mandala_mat)

        c = mandala.constraints.new(type='CHILD_OF')
        c.target = armature
        c.subtarget = hand_bone_name
        c.use_rotation_x = True
        c.use_rotation_y = True
        c.use_rotation_z = True

        # Add Dynamic Point Light attached to hand!
        p_data = bpy.data.lights.new(name=f"{name}_Light", type='POINT')
        p_data.energy = 260.0
        p_data.color = (1.0, 0.60, 0.08) # Warm 2000K flame light
        p_light = bpy.data.objects.new(name=f"{name}_Light", object_data=p_data)
        bpy.context.collection.objects.link(p_light)
        
        lc = p_light.constraints.new(type='CHILD_OF')
        lc.target = armature
        lc.subtarget = hand_bone_name

        # Animate continuous 360-degree spin across frames 1..60
        mandala.animation_data_create()
        spin_dir = 1.0 if clockwise else -1.0
        for f in range(1, 61, 3):
            mandala.rotation_euler.z = f * 0.18 * spin_dir
            mandala.keyframe_insert(data_path="rotation_euler", frame=f)

        return mandala

    mandala_left = create_tracked_mandala("Mandala_Left_Hand", "mixamorig:LeftHand", clockwise=True)
    mandala_right = create_tracked_mandala("Mandala_Right_Hand", "mixamorig:RightHand", clockwise=False)

    # 7. Add 3D Volumetric Agnyāstra Fire Plume Emitters (Following Hands)
    fire_mat = bpy.data.materials.new(name="Agnyastra_Fire_Shader")
    fire_mat.use_nodes = True
    fire_mat.blend_method = 'BLEND'
    f_nodes = fire_mat.node_tree.nodes
    f_links = fire_mat.node_tree.links
    f_nodes.clear()

    f_out = f_nodes.new(type='ShaderNodeOutputMaterial')
    f_emit = f_nodes.new(type='ShaderNodeEmission')
    f_emit.inputs['Color'].default_value = (1.0, 0.45, 0.05, 1.0) # Fiery Orange-Red
    f_emit.inputs['Strength'].default_value = 14.0

    f_tex = f_nodes.new(type='ShaderNodeTexImage')
    if FIRE_TEXTURE.exists():
        f_tex.image = bpy.data.images.load(str(FIRE_TEXTURE))

    f_mix = f_nodes.new(type='ShaderNodeMixShader')
    f_trans = f_nodes.new(type='ShaderNodeBsdfTransparent')

    f_links.new(f_tex.outputs['Color'], f_emit.inputs['Color'])
    f_links.new(f_tex.outputs['Color'], f_mix.inputs['Fac'])
    f_links.new(f_trans.outputs['BSDF'], f_mix.inputs[1])
    f_links.new(f_emit.outputs['Emission'], f_mix.inputs[2])
    f_links.new(f_mix.outputs['Shader'], f_out.inputs['Surface'])

    def create_tracked_fire_plume(name, hand_bone_name):
        bpy.ops.mesh.primitive_plane_add(size=0.75, location=(0, 0, 0))
        plume = bpy.context.active_object
        plume.name = name
        plume.scale = (0.55, 1.10, 1.0)
        plume.data.materials.append(fire_mat)

        c = plume.constraints.new(type='CHILD_OF')
        c.target = armature
        c.subtarget = hand_bone_name

        plume.animation_data_create()
        for f in range(1, 61, 2):
            pulse = 1.0 + 0.12 * math.sin(f * 0.7)
            plume.scale = (0.55 * pulse, 1.10 * pulse, 1.0)
            plume.keyframe_insert(data_path="scale", frame=f)
        return plume

    fire_left = create_tracked_fire_plume("Agnyastra_Fire_Left", "mixamorig:LeftHand")
    fire_right = create_tracked_fire_plume("Agnyastra_Fire_Right", "mixamorig:RightHand")

    # 8. Chest Surya Astra Core (Arc Reactor Glyph on mixamorig:Spine2)
    core_mat = bpy.data.materials.new(name="Surya_Astra_Core_Mat")
    core_mat.use_nodes = True
    c_bsdf = core_mat.node_tree.nodes.get('Principled BSDF')
    if c_bsdf:
        c_bsdf.inputs['Emission'].default_value = (1.0, 0.85, 0.3, 1.0)
        c_bsdf.inputs['Emission Strength'].default_value = 22.0

    bpy.ops.mesh.primitive_circle_add(radius=0.10, fill_type='NGON', location=(0, 0, 0))
    chest_core = bpy.context.active_object
    chest_core.name = "Surya_Astra_Core"
    chest_core.data.materials.append(core_mat)

    cc = chest_core.constraints.new(type='CHILD_OF')
    cc.target = armature
    cc.subtarget = "mixamorig:Spine2"

    c_light_data = bpy.data.lights.new(name="Chest_Core_Light", type='POINT')
    c_light_data.energy = 180.0
    c_light_data.color = (1.0, 0.80, 0.25)
    c_light = bpy.data.objects.new(name="Chest_Core_Light", object_data=c_light_data)
    bpy.context.collection.objects.link(c_light)
    clc = c_light.constraints.new(type='CHILD_OF')
    clc.target = armature
    clc.subtarget = "mixamorig:Spine2"

    # 9. Cinematic Camera with Anamorphic Framing
    cam_data = bpy.data.cameras.new(name="Cinema_Camera")
    cam_data.lens = 42.0
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = 3.30
    cam_data.dof.aperture_fstop = 2.8
    cam_obj = bpy.data.objects.new(name="Cinema_Camera", object_data=cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = (0.0, -3.60, 0.85)
    cam_obj.rotation_euler = (math.radians(88), 0, 0)
    cam_obj.keyframe_insert(data_path="location", frame=1)

    cam_obj.location = (0.0, -3.20, 0.95)
    cam_obj.rotation_euler = (math.radians(88), 0, 0)
    cam_obj.keyframe_insert(data_path="location", frame=60)

    # 10. Save Master Blend File
    os.makedirs(os.path.dirname(blend_out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    print(f"[SAVED] Master Brahmastra Blend: {blend_out}")

    # 11. Render Benchmark Frame
    if render_out_pattern:
        scene.frame_set(still_frame)
        scene.render.filepath = render_out_pattern
        print(f"[RENDERING] Benchmark still frame {still_frame} -> {render_out_pattern}...")
        bpy.ops.render.render(write_still=True)
        print(f"[SUCCESS] Benchmark render saved: {render_out_pattern}")

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    b_out = args[0] if len(args) > 0 else r"C:\Users\SVNITHESHPC\Downloads\AI_Animation_Studio\scenes\brahmastra_mesh_mocap_master.blend"
    r_out = args[1] if len(args) > 1 else r"C:\Users\SVNITHESHPC\Downloads\AI_Animation_Studio\renders\previews\brahmastra_mocap_frame_20.png"
    f_num = int(args[2]) if len(args) > 2 else 20
    build_brahmastra_scene(b_out, r_out, f_num)
