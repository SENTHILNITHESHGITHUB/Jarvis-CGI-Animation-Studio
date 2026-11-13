"""
================================================================================
⚡ MASTER ASTRAVERSE 3D VIRTUAL STUDIO BUILDER // HOLLYWOOD CINEMATIC GRADE ⚡
================================================================================
Unified articulated 3D warrior with vertex groups deformed by Armature,
epic wide-angle camera framing, glowing pillars, flaming braziers,
and towering Celestial Agni Titan with blazing Trishul.
================================================================================
"""

import bpy
import math
import os
import sys

def create_material(name, diffuse_color=(0.1, 0.1, 0.1, 1.0), roughness=0.5, metallic=0.0, emission_color=(0, 0, 0, 1.0), emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    
    node_bsdf.inputs['Base Color'].default_value = diffuse_color
    node_bsdf.inputs['Roughness'].default_value = roughness
    node_bsdf.inputs['Metallic'].default_value = metallic
    
    if emission_strength > 0.0:
        if 'Emission' in node_bsdf.inputs:
            node_bsdf.inputs['Emission'].default_value = emission_color
        if 'Emission Strength' in node_bsdf.inputs:
            node_bsdf.inputs['Emission Strength'].default_value = emission_strength
            
    mat.node_tree.links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    return mat

def create_photoreal_stone_material():
    mat = bpy.data.materials.new(name="M_AncientStone_AstraFissures")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_mix = nodes.new(type='ShaderNodeMixShader')
    
    # 1. Dark Basalt Stone BSDF (Wet reflective granite)
    node_stone = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_stone.inputs['Base Color'].default_value = (0.015, 0.016, 0.020, 1.0)
    node_stone.inputs['Roughness'].default_value = 0.32
    node_stone.inputs['Metallic'].default_value = 0.25
    
    # 2. Blazing Molten Lava Core (Ruby to Saffron)
    node_emit = nodes.new(type='ShaderNodeEmission')
    node_emit.inputs['Color'].default_value = (1.0, 0.32, 0.03, 1.0)
    node_emit.inputs['Strength'].default_value = 8.5
    
    # 3. Procedural Thin Voronoi Cracks
    node_texcoord = nodes.new(type='ShaderNodeTexCoord')
    node_mapping = nodes.new(type='ShaderNodeMapping')
    node_mapping.inputs['Scale'].default_value = (5.5, 5.5, 5.5)
    
    node_voronoi = nodes.new(type='ShaderNodeTexVoronoi')
    node_voronoi.feature = 'DISTANCE_TO_EDGE'
    node_voronoi.inputs['Scale'].default_value = 3.8
    
    # Razor-thin glowing crack lines
    node_ramp = nodes.new(type='ShaderNodeValToRGB')
    node_ramp.color_ramp.elements[0].position = 0.00
    node_ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    node_ramp.color_ramp.elements[1].position = 0.020
    node_ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    
    links = mat.node_tree.links
    links.new(node_texcoord.outputs['Generated'], node_mapping.inputs['Vector'])
    links.new(node_mapping.outputs['Vector'], node_voronoi.inputs['Vector'])
    links.new(node_voronoi.outputs['Distance'], node_ramp.inputs['Fac'])
    links.new(node_ramp.outputs['Color'], node_mix.inputs['Fac'])
    links.new(node_stone.outputs['BSDF'], node_mix.inputs[1])
    links.new(node_emit.outputs['Emission'], node_mix.inputs[2])
    links.new(node_mix.outputs['Shader'], node_out.inputs['Surface'])
    
    return mat

def create_fire_plasma_material(name="M_Astra_FirePlasma", strength=25.0, color=(1.0, 0.45, 0.08, 1.0)):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_emit = nodes.new(type='ShaderNodeEmission')
    node_emit.inputs['Color'].default_value = color
    node_emit.inputs['Strength'].default_value = strength
    
    mat.node_tree.links.new(node_emit.outputs['Emission'], node_out.inputs['Surface'])
    mat.blend_method = 'BLEND'
    return mat

def clean_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m, do_unlink=True)

def setup_eevee_renderer():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    ee = scene.eevee
    
    ee.use_bloom = True
    ee.bloom_intensity = 0.10
    ee.bloom_threshold = 1.15
    ee.bloom_radius = 5.0
    ee.use_gtao = True
    ee.gtao_distance = 2.5
    ee.use_ssr = True
    ee.use_ssr_refraction = True
    ee.use_volumetric_lights = True
    ee.use_volumetric_shadows = True
    ee.volumetric_tile_size = '4'
    ee.use_motion_blur = True
    ee.use_soft_shadows = True
    ee.taa_render_samples = 16
    
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 804  # 2.39:1 Cinemascope
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 120

    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Very High Contrast'
    scene.view_settings.exposure = -0.15

def setup_world_atmosphere():
    world = bpy.context.scene.world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    
    node_out = nt.nodes.new(type='ShaderNodeOutputWorld')
    node_bg = nt.nodes.new(type='ShaderNodeBackground')
    node_bg.inputs['Color'].default_value = (0.003, 0.005, 0.012, 1.0)
    node_bg.inputs['Strength'].default_value = 0.4
    
    node_vol = nt.nodes.new(type='ShaderNodeVolumePrincipled')
    node_vol.inputs['Color'].default_value = (0.2, 0.3, 0.5, 1.0)
    node_vol.inputs['Density'].default_value = 0.0012
    node_vol.inputs['Anisotropy'].default_value = 0.55
    
    nt.links.new(node_bg.outputs['Background'], node_out.inputs['Surface'])
    nt.links.new(node_vol.outputs['Volume'], node_out.inputs['Volume'])

def build_temple_arena():
    # 1. Main Octagonal Stone Dais with Fissures
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=8.5, depth=0.6, location=(0, 0, -0.3))
    dais = bpy.context.active_object
    dais.name = "Astraverse_Sanctum_Dais"
    mat_stone = create_photoreal_stone_material()
    dais.data.materials.append(mat_stone)
    
    # Outer Stepped Rim
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=11.5, depth=0.4, location=(0, 0, -0.7))
    rim = bpy.context.active_object
    rim.name = "Dais_Outer_Step"
    mat_dark_rock = create_material("M_DarkGranite", diffuse_color=(0.015, 0.015, 0.02, 1.0), roughness=0.65)
    rim.data.materials.append(mat_dark_rock)
    
    # 2. Ring of 8 Colossal Stone Monolith Pillars
    num_pillars = 8
    radius_colonnade = 10.5
    mat_pillar = create_material("M_CarvedPillarStone", diffuse_color=(0.025, 0.028, 0.035, 1.0), roughness=0.75)
    mat_glyph = create_fire_plasma_material("M_PillarGlyphEmission", strength=18.0, color=(1.0, 0.35, 0.06, 1.0))
    
    for i in range(num_pillars):
        theta = i * (2 * math.pi / num_pillars)
        px = radius_colonnade * math.cos(theta)
        py = radius_colonnade * math.sin(theta)
        
        # Pillar Base Pedestal
        bpy.ops.mesh.primitive_cube_add(size=1.8, location=(px, py, 0.4))
        pbase = bpy.context.active_object
        pbase.name = f"Pillar_Base_{i+1}"
        pbase.scale = (1.0, 1.0, 0.5)
        pbase.data.materials.append(mat_pillar)
        
        # Main Column Shaft
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.65, depth=8.5, location=(px, py, 4.6))
        pshaft = bpy.context.active_object
        pshaft.name = f"Pillar_Column_{i+1}"
        pshaft.data.materials.append(mat_pillar)
        
        # Glowing Astra Ring Capital
        bpy.ops.mesh.primitive_torus_add(major_radius=0.72, minor_radius=0.08, location=(px, py, 7.5))
        pring = bpy.context.active_object
        pring.name = f"Pillar_Astra_Ring_{i+1}"
        pring.data.materials.append(mat_glyph)

    # 3. 4 Flaming Braziers (Agni Kunds)
    brazier_coords = [(-4.8, -3.8), (4.8, -3.8), (-4.8, 4.8), (4.8, 4.8)]
    mat_brazier = create_material("M_BronzeBrazier", diffuse_color=(0.08, 0.06, 0.03, 1.0), roughness=0.35, metallic=0.85)
    mat_flame = create_fire_plasma_material("M_BrazierFlame", strength=32.0, color=(1.0, 0.48, 0.08, 1.0))
    
    for b_idx, (bx, by) in enumerate(brazier_coords):
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.55, depth=1.4, location=(bx, by, 0.7))
        ped = bpy.context.active_object
        ped.name = f"Brazier_Pedestal_{b_idx+1}"
        ped.data.materials.append(mat_brazier)
        
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.8, radius2=0.35, depth=0.6, location=(bx, by, 1.6))
        bowl = bpy.context.active_object
        bowl.name = f"Brazier_Chalice_{b_idx+1}"
        bowl.data.materials.append(mat_brazier)
        
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.45, location=(bx, by, 2.05))
        flame = bpy.context.active_object
        flame.name = f"Brazier_Flame_Mesh_{b_idx+1}"
        flame.scale = (0.7, 0.7, 1.5)
        flame.data.materials.append(mat_flame)
        
        bpy.ops.object.light_add(type='POINT', radius=0.35, location=(bx, by, 2.3))
        light = bpy.context.active_object
        light.name = f"Brazier_Fire_Light_{b_idx+1}"
        light.data.color = (1.0, 0.45, 0.10)
        light.data.energy = 360.0
        light.data.shadow_soft_size = 0.25

def build_celestial_agni_titan():
    # Celestial Agni Titan & Trishul in Background (y = 6.8m, z = 3.8m)
    mat_trishul = create_fire_plasma_material("M_Trishul_WhiteHotCore", strength=18.0, color=(1.0, 0.68, 0.20, 1.0))
    mat_titan_aura = create_fire_plasma_material("M_Agni_Titan_Plasma", strength=4.5, color=(0.95, 0.24, 0.04, 1.0))
    
    tx, ty, tz = 0.0, 6.8, 3.8
    
    # 1. 3D Flaming Trishul (Trident)
    # Main Staff
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.18, depth=9.5, location=(tx, ty, tz + 0.5))
    staff = bpy.context.active_object
    staff.name = "Agni_Trishul_Staff"
    staff.data.materials.append(mat_trishul)
    
    # Central Spear Blade
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.55, radius2=0.02, depth=2.8, location=(tx, ty, tz + 5.5))
    center_blade = bpy.context.active_object
    center_blade.name = "Trishul_Center_Blade"
    center_blade.data.materials.append(mat_trishul)
    
    # Curved Side Prongs
    for side, sign in [("L", -1), ("R", 1)]:
        bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.14, location=(tx + sign * 1.0, ty, tz + 4.8))
        prong = bpy.context.active_object
        prong.name = f"Trishul_Prong_{side}"
        prong.scale = (1.0, 0.45, 1.35)
        prong.rotation_euler = (0, sign * 0.32, 0)
        prong.data.materials.append(mat_trishul)
        
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.32, depth=1.5, location=(tx + sign * 1.6, ty, tz + 5.8))
        tip = bpy.context.active_object
        tip.name = f"Trishul_Tip_{side}"
        tip.rotation_euler = (0, sign * 0.22, 0)
        tip.data.materials.append(mat_trishul)
        
    # Agni Celestial Mandala Ring behind Trident
    bpy.ops.mesh.primitive_torus_add(major_radius=2.8, minor_radius=0.14, location=(tx, ty + 0.3, tz + 4.2))
    mandala = bpy.context.active_object
    mandala.name = "Agni_Celestial_Mandala"
    mandala.rotation_euler = (math.radians(90), 0, 0)
    mandala.data.materials.append(mat_titan_aura)

    # 2. Celestial Titan Torso & Head Silhouette
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=2.2, location=(tx, ty + 0.8, tz + 0.8))
    torso = bpy.context.active_object
    torso.name = "Agni_Titan_Torso"
    torso.scale = (1.4, 0.8, 1.5)
    torso.data.materials.append(mat_titan_aura)
    
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.1, location=(tx, ty + 0.5, tz + 3.2))
    head = bpy.context.active_object
    head.name = "Agni_Titan_Head"
    head.scale = (1.0, 1.0, 1.2)
    head.data.materials.append(mat_titan_aura)
    
    # Horned Astral Crown
    for sign in [-1, 1]:
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.30, depth=2.0, location=(tx + sign * 0.9, ty + 0.3, tz + 4.4))
        horn = bpy.context.active_object
        horn.rotation_euler = (0.2, sign * 0.50, 0)
        horn.data.materials.append(mat_titan_aura)
        
    # Celestial Rim Backlight
    bpy.ops.object.light_add(type='POINT', radius=1.5, location=(tx, ty + 1.2, tz + 5.5))
    rim_light = bpy.context.active_object
    rim_light.name = "Agni_Titan_RimLight"
    rim_light.data.color = (1.0, 0.55, 0.15)
    rim_light.data.energy = 380.0

    # Cinematic Front Key/Fill Light (Illuminates Warrior Chest & Armor)
    bpy.ops.object.light_add(type='POINT', radius=0.8, location=(0.0, -4.2, 2.2))
    key_light = bpy.context.active_object
    key_light.name = "Warrior_Front_KeyLight"
    key_light.data.color = (1.0, 0.82, 0.65)
    key_light.data.energy = 160.0
    key_light.data.shadow_soft_size = 0.35

def build_hero_warrior():
    # 1. Armature Rig
    arm_data = bpy.data.armatures.new("Astraverse_Hero_Rig")
    arm_obj = bpy.data.objects.new("Astraverse_Hero_Rig", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones
    
    b_hips = eb.new("Hips")
    b_hips.head = (0.0, 0.0, 0.95)
    b_hips.tail = (0.0, 0.0, 1.15)
    
    b_spine = eb.new("Spine")
    b_spine.head = (0.0, 0.0, 1.15)
    b_spine.tail = (0.0, 0.0, 1.35)
    b_spine.parent = b_hips
    
    b_chest = eb.new("Chest")
    b_chest.head = (0.0, 0.0, 1.35)
    b_chest.tail = (0.0, 0.0, 1.55)
    b_chest.parent = b_spine
    
    b_neck = eb.new("Neck")
    b_neck.head = (0.0, 0.0, 1.55)
    b_neck.tail = (0.0, 0.0, 1.63)
    b_neck.parent = b_chest
    
    b_head = eb.new("Head")
    b_head.head = (0.0, 0.0, 1.63)
    b_head.tail = (0.0, 0.0, 1.88)
    b_head.parent = b_neck
    
    for side, sign in [("L", -1), ("R", 1)]:
        b_sh = eb.new(f"Shoulder_{side}")
        b_sh.head = (0.0, 0.0, 1.50)
        b_sh.tail = (sign * 0.22, 0.0, 1.50)
        b_sh.parent = b_chest
        
        b_ua = eb.new(f"UpperArm_{side}")
        b_ua.head = (sign * 0.22, 0.0, 1.50)
        b_ua.tail = (sign * 0.48, 0.0, 1.28)
        b_ua.parent = b_sh
        
        b_fa = eb.new(f"ForeArm_{side}")
        b_fa.head = (sign * 0.48, 0.0, 1.28)
        b_fa.tail = (sign * 0.72, 0.08, 1.08)
        b_fa.parent = b_ua
        
        b_hand = eb.new(f"Hand_{side}")
        b_hand.head = (sign * 0.72, 0.08, 1.08)
        b_hand.tail = (sign * 0.84, 0.16, 0.98)
        b_hand.parent = b_fa
        
        b_thigh = eb.new(f"UpperLeg_{side}")
        b_thigh.head = (sign * 0.18, 0.0, 0.92)
        b_thigh.tail = (sign * 0.20, 0.04, 0.48)
        b_thigh.parent = b_hips
        
        b_shin = eb.new(f"LowerLeg_{side}")
        b_shin.head = (sign * 0.20, 0.04, 0.48)
        b_shin.tail = (sign * 0.22, 0.0, 0.10)
        b_shin.parent = b_thigh
        
        b_foot = eb.new(f"Foot_{side}")
        b_foot.head = (sign * 0.22, 0.0, 0.10)
        b_foot.tail = (sign * 0.22, 0.22, 0.02)
        b_foot.parent = b_shin
        
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 2. Unified Warrior Mesh with Vertex Groups
    mat_armor = create_material("M_Shiva_ObsidianArmor", diffuse_color=(0.025, 0.025, 0.032, 1.0), roughness=0.25, metallic=0.95)
    mat_conduit = create_fire_plasma_material("M_Astra_ArmorConduit", strength=32.0, color=(1.0, 0.42, 0.06, 1.0))
    mat_skin = create_material("M_WarriorSkin", diffuse_color=(0.35, 0.24, 0.18, 1.0), roughness=0.55)
    
    created_parts = []
    
    def create_body_part(mesh_type, name, loc, scale, rot, mat, bone_group):
        if mesh_type == 'cylinder':
            bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.5, depth=1.0, location=loc)
        elif mesh_type == 'cube':
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
        elif mesh_type == 'sphere':
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.5, location=loc)
        obj = bpy.context.active_object
        obj.name = name
        obj.scale = scale
        obj.rotation_euler = rot
        obj.data.materials.append(mat)
        
        # Assign all vertices to bone group
        vg = obj.vertex_groups.new(name=bone_group)
        vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
        created_parts.append(obj)
        return obj

    # Torso & Chest
    create_body_part('cylinder', "Part_Torso", (0, 0, 1.45), (0.52, 0.36, 0.42), (0, 0, 0), mat_armor, "Chest")
    create_body_part('cylinder', "Part_ChestMandala", (0, 0.18, 1.48), (0.18, 0.18, 0.04), (math.radians(90), 0, 0), mat_conduit, "Chest")
    create_body_part('cylinder', "Part_Pelvis", (0, 0, 1.05), (0.46, 0.32, 0.22), (0, 0, 0), mat_armor, "Hips")
    
    # Head & Visor
    create_body_part('sphere', "Part_Head", (0, 0, 1.76), (0.28, 0.32, 0.34), (0, 0, 0), mat_skin, "Head")
    create_body_part('cube', "Part_Visor", (0, 0.14, 1.78), (0.22, 0.05, 0.06), (0, 0, 0), mat_conduit, "Head")
    
    # Limbs
    for side, sign in [("L", -1), ("R", 1)]:
        create_body_part('sphere', f"Part_Puldron_{side}", (sign * 0.28, 0, 1.52), (0.22, 0.22, 0.18), (0, 0, 0), mat_armor, f"Shoulder_{side}")
        create_body_part('cylinder', f"Part_Bicep_{side}", (sign * 0.35, 0, 1.39), (0.14, 0.14, 0.26), (0, 0, 0), mat_armor, f"UpperArm_{side}")
        create_body_part('cylinder', f"Part_Gauntlet_{side}", (sign * 0.60, 0.04, 1.18), (0.13, 0.13, 0.28), (0, 0, 0), mat_armor, f"ForeArm_{side}")
        create_body_part('cylinder', f"Part_Conduit_{side}", (sign * 0.60, 0.04, 1.18), (0.15, 0.15, 0.05), (0, 0, 0), mat_conduit, f"ForeArm_{side}")
        create_body_part('sphere', f"Part_Fist_{side}", (sign * 0.78, 0.12, 1.03), (0.12, 0.12, 0.12), (0, 0, 0), mat_armor, f"Hand_{side}")
        
        create_body_part('cylinder', f"Part_Thigh_{side}", (sign * 0.19, 0.02, 0.70), (0.18, 0.18, 0.40), (0, 0, 0), mat_armor, f"UpperLeg_{side}")
        create_body_part('cylinder', f"Part_Shin_{side}", (sign * 0.21, 0.02, 0.29), (0.15, 0.15, 0.36), (0, 0, 0), mat_armor, f"LowerLeg_{side}")
        create_body_part('cube', f"Part_Boot_{side}", (sign * 0.21, 0.10, 0.06), (0.16, 0.26, 0.12), (0, 0, 0), mat_armor, f"Foot_{side}")

    # Merge all parts into one unified master Warrior mesh
    bpy.ops.object.select_all(action='DESELECT')
    for p in created_parts:
        p.select_set(True)
    master_mesh = created_parts[0]
    bpy.context.view_layer.objects.active = master_mesh
    bpy.ops.object.join()
    master_mesh.name = "Warrior_Hero_MasterMesh"
    
    # Add Armature Modifier
    mod_arm = master_mesh.modifiers.new(name="AstraverseRigMod", type='ARMATURE')
    mod_arm.object = arm_obj
    master_mesh.parent = arm_obj
    
    return arm_obj

def attach_reactive_hand_fire(arm_obj):
    mat_particle = create_fire_plasma_material("M_Hand_Fire_Particle", strength=65.0, color=(1.0, 0.55, 0.12, 1.0))
    
    for side, sign in [("L", -1), ("R", 1)]:
        # 1. Emitter Sphere
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.10, location=(0, 0, 0))
        emitter = bpy.context.active_object
        emitter.name = f"Hand_Fire_Emitter_{side}"
        emitter.data.materials.append(mat_particle)
        
        emitter.parent = arm_obj
        emitter.parent_type = 'BONE'
        emitter.parent_bone = f"Hand_{side}"
        emitter.location = (0, 0, 0.10) # Centered on hand
        
        # 2. Particle System (3D Fluid Fire)
        ps_mod = emitter.modifiers.new(name="FluidFireSystem", type='PARTICLE_SYSTEM')
        ps = ps_mod.particle_system
        pset = ps.settings
        pset.count = 350
        pset.frame_start = 1
        pset.frame_end = 120
        pset.lifetime = 16.0
        pset.lifetime_random = 0.4
        pset.factor_random = 0.55
        pset.normal_factor = 0.35
        pset.effector_weights.gravity = -0.30
        pset.object_factor = 0.60
        pset.brownian_factor = 0.50
        pset.particle_size = 0.06
        pset.size_random = 0.5
        
        # 3. Dynamic Palm Fire Point Light
        bpy.ops.object.light_add(type='POINT', radius=0.20, location=(0, 0, 0))
        plight = bpy.context.active_object
        plight.name = f"Hand_Fire_Light_{side}"
        plight.data.color = (1.0, 0.48, 0.10)
        plight.data.energy = 180.0
        plight.data.shadow_soft_size = 0.18
        plight.parent = arm_obj
        plight.parent_type = 'BONE'
        plight.parent_bone = f"Hand_{side}"
        plight.location = (0, 0, 0.10)

def animate_mocap_hero_sequence(arm_obj):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')
    pb = arm_obj.pose.bones
    
    for bone_name in pb.keys():
        pb[bone_name].rotation_mode = 'XYZ'
        
    keyframes_data = [
        # Frame 1: Hero Stance
        (1, {
            "Hips": ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
            "UpperArm_L": (None, (0.35, -0.25, 0.20)),
            "ForeArm_L": (None, (0.85, 0.0, -0.45)),
            "UpperArm_R": (None, (0.35, 0.25, -0.20)),
            "ForeArm_R": (None, (0.85, 0.0, 0.45)),
            "Head": (None, (-0.05, 0.0, 0.0))
        }),
        # Frame 30: Deep Combat Crouch
        (30, {
            "Hips": ((0.0, 0.0, -0.15), (0.12, 0.0, 0.0)),
            "Spine": (None, (0.15, 0.0, 0.0)),
            "Chest": (None, (0.12, 0.0, 0.0)),
            "UpperArm_L": (None, (0.65, -0.55, 0.40)),
            "ForeArm_L": (None, (1.20, 0.0, -0.75)),
            "UpperArm_R": (None, (0.55, 0.45, -0.30)),
            "ForeArm_R": (None, (1.10, 0.0, 0.65)),
            "Head": (None, (0.05, 0.0, 0.0))
        }),
        # Frame 48: Mid-Swipe Arc (Right arm whips across chest)
        (48, {
            "Hips": ((0.06, 0.0, -0.08), (0.05, 0.15, 0.25)),
            "Spine": (None, (0.08, 0.12, 0.35)),
            "Chest": (None, (0.08, 0.15, 0.45)),
            "UpperArm_L": (None, (-0.25, -0.40, 0.65)),
            "ForeArm_L": (None, (0.55, 0.0, -0.30)),
            "UpperArm_R": (None, (1.45, -0.35, -0.85)),
            "ForeArm_R": (None, (0.45, 0.0, -0.20)),
            "Head": (None, (-0.05, 0.10, 0.35))
        }),
        # Frame 82: Explosive Dual Palm Blast
        (82, {
            "Hips": ((0.0, 0.12, -0.16), (0.18, 0.0, 0.0)),
            "Spine": (None, (0.22, 0.0, 0.0)),
            "Chest": (None, (0.18, 0.0, 0.0)),
            "UpperArm_L": (None, (1.65, -0.15, 0.10)),
            "ForeArm_L": (None, (0.15, 0.0, 0.0)),
            "UpperArm_R": (None, (1.65, 0.15, -0.10)),
            "ForeArm_R": (None, (0.15, 0.0, 0.0)),
            "Head": (None, (-0.15, 0.0, 0.0))
        }),
        # Frame 108: Celestial Summoning Pose
        (108, {
            "Hips": ((0.0, -0.05, 0.02), (-0.08, 0.0, 0.0)),
            "Spine": (None, (-0.15, 0.0, 0.0)),
            "Chest": (None, (-0.20, 0.0, 0.0)),
            "UpperArm_L": (None, (2.85, -0.55, 0.35)),
            "ForeArm_L": (None, (0.35, 0.0, 0.0)),
            "UpperArm_R": (None, (2.85, 0.55, -0.35)),
            "ForeArm_R": (None, (0.35, 0.0, 0.0)),
            "Head": (None, (-0.45, 0.0, 0.0))
        }),
        (120, {
            "Hips": ((0.0, -0.05, 0.05), (-0.10, 0.0, 0.0)),
            "Head": (None, (-0.48, 0.0, 0.0))
        })
    ]
    
    for f_num, bones_dict in keyframes_data:
        for b_name, (loc, rot) in bones_dict.items():
            if b_name in pb:
                bone = pb[b_name]
                if loc is not None:
                    bone.location = loc
                    bone.keyframe_insert(data_path="location", frame=f_num)
                if rot is not None:
                    bone.rotation_euler = rot
                    bone.keyframe_insert(data_path="rotation_euler", frame=f_num)
                    
    bpy.ops.object.mode_set(mode='OBJECT')

def setup_cinematic_camera(arm_obj):
    # Position camera for majestic scale (28mm lens, looking slightly up at warrior and Trishul)
    bpy.ops.object.camera_add(location=(0.0, -7.5, 1.85))
    cam_obj = bpy.context.active_object
    cam_obj.name = "Astraverse_Cinematic_Camera"
    bpy.context.scene.camera = cam_obj
    
    cam = cam_obj.data
    cam.lens = 28.0 # 28mm Hollywood wide-angle
    cam.dof.use_dof = True
    cam.dof.focus_object = arm_obj
    cam.dof.focus_subtarget = "Chest"
    cam.dof.aperture_fstop = 2.8
    
    # Camera Tracks smoothly toward the warrior during action
    cam_obj.rotation_euler = (math.radians(80), 0, 0)
    cam_obj.keyframe_insert(data_path="location", frame=1)
    cam_obj.keyframe_insert(data_path="rotation_euler", frame=1)
    
    # Frame 60 (Mid-swipe push)
    cam_obj.location = (0.25, -6.2, 1.65)
    cam_obj.rotation_euler = (math.radians(81), 0, math.radians(2.0))
    cam_obj.keyframe_insert(data_path="location", frame=60)
    cam_obj.keyframe_insert(data_path="rotation_euler", frame=60)
    
    # Frame 120 (Dramatic low-angle push looking up at warrior and celestial Titan)
    cam_obj.location = (0.0, -5.2, 1.35)
    cam_obj.rotation_euler = (math.radians(75), 0, 0)
    cam_obj.keyframe_insert(data_path="location", frame=120)
    cam_obj.keyframe_insert(data_path="rotation_euler", frame=120)

def main():
    print("=" * 70)
    print("⚡ BUILDING MASTER ASTRAVERSE 3D VIRTUAL STUDIO // HOLLYWOOD GRADE ⚡")
    print("=" * 70)
    
    clean_scene()
    setup_eevee_renderer()
    setup_world_atmosphere()
    build_temple_arena()
    build_celestial_agni_titan()
    hero_rig = build_hero_warrior()
    attach_reactive_hand_fire(hero_rig)
    animate_mocap_hero_sequence(hero_rig)
    setup_cinematic_camera(hero_rig)
    
    out_dir = r"C:\Users\SVNITHESHPC\Downloads\Astraverse_Blender_Studio"
    os.makedirs(out_dir, exist_ok=True)
    blend_path = os.path.join(out_dir, "Astraverse_3D_Virtual_Studio.blend")
    
    print(f"[*] Saving master Blender production scene to: {blend_path}")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("⚡ [SUCCESS] MASTER 3D VIRTUAL STUDIO SAVED! ⚡\n")

if __name__ == "__main__":
    main()
