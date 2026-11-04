"""
Module 2: Character Integrity and Geometry Inspector
---------------------------------------------------
Automated inspection of 3D character meshes, bounding boxes, topology,
manifold integrity, disconnected components, material assignments,
armature modifiers, bone hierarchies, and proportion baselines.

Complies strictly with AI Animation Studio AGENTS.md rules:
- Does NOT automatically alter the character mesh.
- Compares measurements against reference baselines.
- Generates detailed JSON and HTML reports.
- Recommends non-destructive corrective actions for human approval.
"""

import os
import sys
import json
import math
import time
import subprocess
from pathlib import Path

STUDIO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = STUDIO_ROOT / "characters" / "models"
REPORTS_DIR = STUDIO_ROOT / "reports"
REFERENCES_DIR = STUDIO_ROOT / "characters" / "references"

BLENDER_INSPECTOR_CODE = """
import bpy
import bmesh
import math
import sys
import json
import os

def inspect_character(model_path, baseline_path=None):
    # 1. Clear scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # 2. Import model
    ext = os.path.splitext(model_path)[1].lower()
    if ext in ['.glb', '.gltf']:
        bpy.ops.import_scene.gltf(filepath=model_path)
    elif ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=model_path)
    elif ext == '.obj':
        bpy.ops.import_scene.obj(filepath=model_path)
    else:
        raise ValueError(f"Unsupported format: {ext}")

    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    armatures = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']

    report = {
        "model_file": os.path.basename(model_path),
        "mesh_count": len(meshes),
        "armature_count": len(armatures),
        "meshes": [],
        "armatures": [],
        "proportions": {},
        "integrity_alerts": [],
        "suggested_corrections": []
    }

    # Inspect Armatures
    for arm in armatures:
        arm_data = {
            "name": arm.name,
            "bone_count": len(arm.data.bones),
            "deform_bones": [b.name for b in arm.data.bones if b.use_deform],
            "root_bones": [b.name for b in arm.data.bones if b.parent is None],
            "has_head": any('head' in b.name.lower() for b in arm.data.bones),
            "has_hands": any('hand' in b.name.lower() for b in arm.data.bones),
            "has_feet": any('foot' in b.name.lower() for b in arm.data.bones),
            "finger_bones": [b.name for b in arm.data.bones if 'index' in b.name.lower() or 'thumb' in b.name.lower() or 'finger' in b.name.lower()]
        }
        report["armatures"].append(arm_data)

    primary_mesh = meshes[0] if meshes else None
    primary_arm = armatures[0] if armatures else None

    # Inspect Meshes
    for m in meshes:
        bm = bmesh.new()
        bm.from_mesh(m.data)
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # Non-manifold analysis
        non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
        boundary_edges = [e for e in bm.edges if e.is_boundary]
        wire_edges = [e for e in bm.edges if e.is_wire]

        # Connected components / loose parts
        visited_verts = set()
        components = 0
        for v in bm.verts:
            if v not in visited_verts:
                components += 1
                queue = [v]
                visited_verts.add(v)
                while queue:
                    curr = queue.pop()
                    for edge in curr.link_edges:
                        other = edge.other_vert(curr)
                        if other not in visited_verts:
                            visited_verts.add(other)
                            queue.append(other)

        # Materials check
        materials = []
        missing_materials = False
        if not m.data.materials or len(m.data.materials) == 0:
            missing_materials = True
        else:
            for mat in m.data.materials:
                if mat:
                    has_nodes = mat.use_nodes
                    has_texture = False
                    if has_nodes and mat.node_tree:
                        has_texture = any(n.type == 'TEX_IMAGE' for n in mat.node_tree.nodes)
                    materials.append({
                        "name": mat.name,
                        "has_nodes": has_nodes,
                        "has_texture": has_texture
                    })
                else:
                    materials.append({"name": "Empty Material Slot", "has_nodes": False, "has_texture": False})
                    missing_materials = True

        # Armature Modifiers
        arm_mods = []
        dqs_enabled = False
        for mod in m.modifiers:
            if mod.type == 'ARMATURE':
                arm_mods.append({
                    "name": mod.name,
                    "target_armature": mod.object.name if mod.object else None,
                    "preserve_volume": mod.use_deform_preserve_volume
                })
                if mod.use_deform_preserve_volume:
                    dqs_enabled = True

        # Custom split normals
        has_custom_split_normals = m.data.has_custom_normals

        # Bounding box & dimensions
        dims = m.dimensions
        bbox_min = [min(v.co[i] for v in m.data.vertices) for i in range(3)] if m.data.vertices else [0,0,0]
        bbox_max = [max(v.co[i] for v in m.data.vertices) for i in range(3)] if m.data.vertices else [0,0,0]

        mesh_info = {
            "name": m.name,
            "vertex_count": len(m.data.vertices),
            "polygon_count": len(m.data.polygons),
            "edge_count": len(m.data.edges),
            "dimensions_m": {"width_x": round(dims.x, 3), "depth_y": round(dims.y, 3), "height_z": round(dims.z, 3)},
            "bounding_box_local": {"min": [round(x, 3) for x in bbox_min], "max": [round(x, 3) for x in bbox_max]},
            "non_manifold_edge_count": len(non_manifold_edges),
            "boundary_edge_count": len(boundary_edges),
            "wire_edge_count": len(wire_edges),
            "connected_components": components,
            "materials": materials,
            "missing_materials": missing_materials,
            "armature_modifiers": arm_mods,
            "dqs_preserve_volume": dqs_enabled,
            "has_custom_split_normals": has_custom_split_normals,
            "shape_keys": [sk.name for sk in m.data.shape_keys.key_blocks] if m.data.shape_keys else []
        }
        report["meshes"].append(mesh_info)
        bm.free()

    # Proportion measurements
    if primary_mesh and primary_arm:
        bones = primary_arm.data.bones
        def get_bone_len(b_name):
            b = bones.get(b_name)
            return round(b.length, 3) if b else 0.0

        # Overall height
        total_height = round(primary_mesh.dimensions.z, 3)
        
        # Bones based proportions
        head_bone = next((b for b in bones if 'head' in b.name.lower()), None)
        neck_bone = next((b for b in bones if 'neck' in b.name.lower()), None)
        spine_bone = next((b for b in bones if 'spine' in b.name.lower()), None)
        hips_bone = next((b for b in bones if 'hip' in b.name.lower()), None)

        left_arm_bones = [b for b in bones if 'leftarm' in b.name.lower() or 'leftforearm' in b.name.lower()]
        right_arm_bones = [b for b in bones if 'rightarm' in b.name.lower() or 'rightforearm' in b.name.lower()]
        left_leg_bones = [b for b in bones if 'leftupleg' in b.name.lower() or 'leftleg' in b.name.lower()]
        right_leg_bones = [b for b in bones if 'rightupleg' in b.name.lower() or 'rightleg' in b.name.lower()]

        proportions = {
            "overall_height_m": total_height,
            "overall_width_m": round(primary_mesh.dimensions.x, 3),
            "overall_depth_m": round(primary_mesh.dimensions.y, 3),
            "head_bone_length_m": round(head_bone.length, 3) if head_bone else 0.0,
            "left_arm_length_m": round(sum(b.length for b in left_arm_bones), 3),
            "right_arm_length_m": round(sum(b.length for b in right_arm_bones), 3),
            "left_leg_length_m": round(sum(b.length for b in left_leg_bones), 3),
            "right_leg_length_m": round(sum(b.length for b in right_leg_bones), 3),
            "arm_symmetry_diff_m": round(abs(sum(b.length for b in left_arm_bones) - sum(b.length for b in right_arm_bones)), 4),
            "leg_symmetry_diff_m": round(abs(sum(b.length for b in left_leg_bones) - sum(b.length for b in right_leg_bones)), 4),
        }
        report["proportions"] = proportions

    # Automated Integrity Alerts & Quality Gates
    for m_info in report["meshes"]:
        # Seam / boundary vertices alert
        if m_info["boundary_edge_count"] > 100:
            report["integrity_alerts"].append({
                "severity": "WARNING",
                "mesh": m_info["name"],
                "issue": f"High boundary edge count ({m_info['boundary_edge_count']}). Indicates disconnected UV boundary seams prone to cracking when subdivided."
            })
            report["suggested_corrections"].append({
                "target": m_info["name"],
                "action": "WELD_SEAMS",
                "code": "bpy.ops.mesh.remove_doubles(threshold=0.0005)",
                "reason": "Welds disconnected seam vertices to eliminate black star-holes and edge separation."
            })

        # Dual Quaternion Skinning (Volume Preservation)
        if not m_info["dqs_preserve_volume"] and m_info["armature_modifiers"]:
            report["integrity_alerts"].append({
                "severity": "WARNING",
                "mesh": m_info["name"],
                "issue": "Dual Quaternion Skinning (use_deform_preserve_volume) is DISABLED on Armature modifier. Limbs and wrists will collapse/pinch under rotation."
            })
            report["suggested_corrections"].append({
                "target": m_info["name"],
                "action": "ENABLE_DQS",
                "code": "modifier.use_deform_preserve_volume = True",
                "reason": "Prevents candy-wrapper wrist pinching and preserves limb volume during animation."
            })

        # Corrupted split normals
        if m_info["has_custom_split_normals"]:
            report["integrity_alerts"].append({
                "severity": "WARNING",
                "mesh": m_info["name"],
                "issue": "Custom split normals detected on game-ripped model. Often causes dark star shading punctures on stylized surfaces."
            })
            report["suggested_corrections"].append({
                "target": m_info["name"],
                "action": "CLEAR_SPLIT_NORMALS",
                "code": "bpy.ops.mesh.customdata_custom_splitnormals_clear()",
                "reason": "Cleans shading interpolation and enables smooth cartoon lighting."
            })

    # Finger bone alert for spherical cartoon mittens (Doraemon style)
    if report["armatures"]:
        arm = report["armatures"][0]
        if len(arm["finger_bones"]) > 0 and 'doraemon' in report['model_file'].lower():
            report["integrity_alerts"].append({
                "severity": "WARNING",
                "armature": arm["name"],
                "issue": f"Rig contains {len(arm['finger_bones'])} finger bones, but character has solid spherical mittens. Finger rotations will distort round hand geometry."
            })
            report["suggested_corrections"].append({
                "target": arm["name"],
                "action": "UNIFY_HAND_WEIGHTS",
                "code": "Transfer finger vertex group weights to main mixamorig:LeftHand and mixamorig:RightHand, then remove finger vertex groups.",
                "reason": "Guarantees pristine, round, uncollapsed white spherical mittens across all animations."
            })

    # Compare with Baseline if provided
    report["baseline_comparison"] = {"has_baseline": False}
    if baseline_path and os.path.exists(baseline_path):
        with open(baseline_path, 'r', encoding='utf-8') as f:
            baseline = json.load(f)
        report["baseline_comparison"]["has_baseline"] = True
        report["baseline_comparison"]["reference_name"] = baseline.get("model_file")
        
        diffs = {}
        for k, v in report.get("proportions", {}).items():
            base_v = baseline.get("proportions", {}).get(k)
            if base_v is not None and isinstance(base_v, (int, float)):
                delta = round(v - base_v, 4)
                pct = round((delta / base_v) * 100, 2) if base_v != 0 else 0
                diffs[k] = {"current": v, "baseline": base_v, "delta": delta, "pct_change": pct}
                if abs(pct) > 5.0: # Greater than 5% shift
                    report["integrity_alerts"].append({
                        "severity": "CRITICAL",
                        "issue": f"Proportion shift in {k}: changed by {pct}% ({delta}m) from baseline."
                    })
        report["baseline_comparison"]["differences"] = diffs

    print("INSPECTION_JSON_START")
    print(json.dumps(report))
    print("INSPECTION_JSON_END")

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if args:
        m_path = args[0]
        b_path = args[1] if len(args) > 1 else None
        inspect_character(m_path, b_path)
"""

def inspect_character_asset(blender_exe, model_file, baseline_file=None):
    """Runs the Blender character inspection tool and saves reports."""
    model_path = Path(model_file).resolve()
    baseline_path = Path(baseline_file).resolve() if baseline_file else None

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    runner_script = STUDIO_ROOT / "scripts" / "quality_control" / "_temp_character_inspector.py"
    with open(runner_script, "w", encoding="utf-8") as f:
        f.write(BLENDER_INSPECTOR_CODE)

    cmd = [
        blender_exe,
        "--background",
        "--python", str(runner_script),
        "--",
        str(model_path)
    ]
    if baseline_path and baseline_path.exists():
        cmd.append(str(baseline_path))

    t0 = time.time()
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        elapsed = round(time.time() - t0, 2)
        stdout = res.stdout

        # Extract JSON
        if "INSPECTION_JSON_START" in stdout and "INSPECTION_JSON_END" in stdout:
            json_str = stdout.split("INSPECTION_JSON_START")[1].split("INSPECTION_JSON_END")[0].strip()
            data = json.loads(json_str)
            data["execution_time_seconds"] = elapsed
            data["status"] = "PASS" if not any(a["severity"] == "CRITICAL" for a in data.get("integrity_alerts", [])) else "FAIL"
            _save_reports(data, model_path.stem)
            return data
        else:
            raise RuntimeError(f"Failed to parse inspection JSON from output:\n{stdout}")
    finally:
        if runner_script.exists():
            try:
                runner_script.unlink()
            except OSError:
                pass


def _save_reports(data, asset_name):
    """Writes JSON and rich HTML/Markdown inspection reports."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. JSON Report
    json_path = REPORTS_DIR / f"character_{asset_name}_integrity_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # 2. Markdown / HTML Report
    md_path = REPORTS_DIR / f"character_{asset_name}_integrity_report.md"
    status_emoji = "✅ PASS" if data["status"] == "PASS" else "❌ FAIL"

    alerts_md = ""
    if data["integrity_alerts"]:
        for a in data["integrity_alerts"]:
            sev = a.get("severity", "WARNING")
            badge = "⚠️ WARN" if sev == "WARNING" else "🚨 CRITICAL"
            alerts_md += f"- **{badge}**: {a.get('issue', '')}\n"
    else:
        alerts_md = "*No integrity alerts detected. Mesh topology is pristine.*\n"

    fixes_md = ""
    if data["suggested_corrections"]:
        for c in data["suggested_corrections"]:
            fixes_md += f"### Recommended Fix: `{c['action']}` (Target: `{c['target']}`)\n"
            fixes_md += f"> **Reason**: {c['reason']}\n\n"
            fixes_md += f"```python\n{c['code']}\n```\n\n"
    else:
        fixes_md = "*No corrections required. Character complies with all studio standards.*\n"

    proportions = data.get("proportions", {})
    props_md = f"""
| Dimension / Limb | Measurement (Meters) | Status |
|---|---|---|
| **Overall Height** | `{proportions.get('overall_height_m', 0)} m` | Standard Baseline |
| **Overall Width (Span)** | `{proportions.get('overall_width_m', 0)} m` | Standard Baseline |
| **Head Bone Length** | `{proportions.get('head_bone_length_m', 0)} m` | Standard Baseline |
| **Left Arm Span** | `{proportions.get('left_arm_length_m', 0)} m` | Symmetry Delta: `{proportions.get('arm_symmetry_diff_m', 0)} m` |
| **Right Arm Span** | `{proportions.get('right_arm_length_m', 0)} m` | Symmetry Delta: `{proportions.get('arm_symmetry_diff_m', 0)} m` |
| **Left Leg Span** | `{proportions.get('left_leg_length_m', 0)} m` | Symmetry Delta: `{proportions.get('leg_symmetry_diff_m', 0)} m` |
| **Right Leg Span** | `{proportions.get('right_leg_length_m', 0)} m` | Symmetry Delta: `{proportions.get('leg_symmetry_diff_m', 0)} m` |
"""

    md_content = f"""# Module 2: Character Integrity & Geometry Audit
**Target Asset**: `{data['model_file']}` | **Status**: {status_emoji} | **Audit Time**: `{data.get('execution_time_seconds', 0)}s`

---

## 1. Mesh & Topology Summary
- **Meshes Found**: `{data['mesh_count']}`
- **Armatures Found**: `{data['armature_count']}`
- **Total Vertices**: `{data['meshes'][0]['vertex_count'] if data['meshes'] else 0:,}`
- **Total Polygons**: `{data['meshes'][0]['polygon_count'] if data['meshes'] else 0:,}`
- **Boundary Edges**: `{data['meshes'][0]['boundary_edge_count'] if data['meshes'] else 0:,}`
- **Connected Components (Islands)**: `{data['meshes'][0]['connected_components'] if data['meshes'] else 0}`
- **Dual Quaternion Skinning (DQS)**: `{'ENABLED' if data['meshes'] and data['meshes'][0]['dqs_preserve_volume'] else 'DISABLED'}`

---

## 2. Character Proportion Baseline
{props_md}

---

## 3. Detected Integrity Alerts
{alerts_md}

---

## 4. Suggested Non-Destructive Corrections (Requires Human Approval)
{fixes_md}
"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"[AUDIT COMPLETE] Saved reports to {json_path} and {md_path}")


if __name__ == '__main__':
    blender_bin = r"C:\Users\SVNITHESHPC\Downloads\blender-3.6.9-windows-x64\blender.exe"
    target = MODELS_DIR / "doraemon.glb"
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    inspect_character_asset(blender_bin, target)
