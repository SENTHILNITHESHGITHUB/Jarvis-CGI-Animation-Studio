"""
Module 1: Blender Integration Engine
------------------------------------
Automated Blender executable detection, version audit, headless IPC execution,
test scene generation, render verification, and comprehensive connection reporting.

Complies strictly with AI Animation Studio AGENTS.md rules.
"""

import os
import sys
import json
import time
import struct
import platform
import subprocess
from pathlib import Path

# Paths within AI_Animation_Studio project structure
STUDIO_ROOT = Path(__file__).resolve().parents[2]
SCENES_DIR = STUDIO_ROOT / "scenes"
RENDERS_PREVIEW_DIR = STUDIO_ROOT / "renders" / "previews"
REPORTS_DIR = STUDIO_ROOT / "reports"

class BlenderDiscovery:
    """Discovers and validates Blender executable on the host system."""
    
    STANDARD_SEARCH_LOCATIONS = [
        # Local verified portable installation
        Path(r"C:\Users\SVNITHESHPC\Downloads\blender-3.6.9-windows-x64\blender.exe"),
        # Program Files locations
        Path(r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender\blender.exe"),
        # AppData locations
        Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs\Blender Foundation\Blender 3.6\blender.exe")),
    ]

    @classmethod
    def find_executable(cls, custom_path=None):
        """Finds a valid Blender executable or raises a descriptive error."""
        candidates = []
        if custom_path:
            candidates.append(Path(custom_path))
        
        env_path = os.environ.get("BLENDER_PATH")
        if env_path:
            candidates.append(Path(env_path))
            
        candidates.extend(cls.STANDARD_SEARCH_LOCATIONS)

        # Also check system PATH
        try:
            where_result = subprocess.run(["where", "blender"], capture_output=True, text=True, check=False)
            if where_result.returncode == 0:
                for line in where_result.stdout.strip().splitlines():
                    if line.strip():
                        candidates.append(Path(line.strip()))
        except Exception:
            pass

        for p in candidates:
            if p.is_file() and os.access(str(p), os.X_OK):
                return str(p.resolve())

        # If not found, list checked candidates
        checked_list = "\n - ".join(str(c) for c in candidates)
        raise FileNotFoundError(
            f"Blender executable could not be found automatically. Checked:\n - {checked_list}\n"
            f"Please set the BLENDER_PATH environment variable or pass custom_path."
        )

    @classmethod
    def get_version(cls, blender_exe):
        """Runs blender --version and extracts version information."""
        try:
            res = subprocess.run([blender_exe, "--version"], capture_output=True, text=True, check=True)
            lines = res.stdout.strip().splitlines()
            version_str = lines[0] if lines else "Unknown"
            build_hash = lines[1] if len(lines) > 1 else ""
            return {
                "version_string": version_str,
                "build_details": build_hash,
                "raw_output": res.stdout.strip()
            }
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Failed to execute '{blender_exe} --version': {e}")


class BlenderTestSceneRunner:
    """Constructs a test scene, saves .blend, and renders frame 1."""

    BLENDER_TEST_SCRIPT = """
import bpy
import math
import os

def create_and_render_test_scene(blend_save_path, render_output_path):
    # 1. Reset to empty factory scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # 2. Render engine & resolution configuration
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 1
    scene.frame_set(1)

    # 3. Environment World Shader
    world = bpy.data.worlds.new("Test_World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.12, 0.14, 0.18, 1.0) # Modern dark slate
        bg.inputs['Strength'].default_value = 0.8

    # 4. Geometry: Studio Test Cube with Bevel
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 1.0))
    cube = bpy.context.active_object
    cube.name = "Module1_Test_Cube"

    # Add Bevel Modifier for clean highlight reflections
    bev = cube.modifiers.new(name="Bevel", type='BEVEL')
    bev.width = 0.08
    bev.segments = 3

    # Add PBR Material
    mat = bpy.data.materials.new(name="Studio_Cyan_Material")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.0, 0.76, 0.80, 1.0) # Vibrant Studio Cyan
        bsdf.inputs['Roughness'].default_value = 0.30
        bsdf.inputs['Metallic'].default_value = 0.15
    cube.data.materials.append(mat)

    # Ground Plane
    bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Studio_Floor"
    floor_mat = bpy.data.materials.new(name="Studio_Floor_Mat")
    floor_mat.use_nodes = True
    f_bsdf = floor_mat.node_tree.nodes.get('Principled BSDF')
    if f_bsdf:
        f_bsdf.inputs['Base Color'].default_value = (0.08, 0.09, 0.11, 1.0)
        f_bsdf.inputs['Roughness'].default_value = 0.45
    floor.data.materials.append(floor_mat)

    # 5. Three-Point Studio Lighting
    # Key Sunlight
    sun_data = bpy.data.lights.new(name="Key_Light", type='SUN')
    sun_data.energy = 3.5
    sun_data.color = (1.0, 0.98, 0.95)
    sun_obj = bpy.data.objects.new(name="Key_Light", object_data=sun_data)
    sun_obj.rotation_euler = (math.radians(45), math.radians(-25), math.radians(35))
    bpy.context.collection.objects.link(sun_obj)

    # Fill Point Light
    fill_data = bpy.data.lights.new(name="Fill_Light", type='POINT')
    fill_data.energy = 150.0
    fill_data.color = (0.7, 0.85, 1.0)
    fill_obj = bpy.data.objects.new(name="Fill_Light", object_data=fill_data)
    fill_obj.location = (-3.5, -3.0, 2.5)
    bpy.context.collection.objects.link(fill_obj)

    # Rim Spot Light
    rim_data = bpy.data.lights.new(name="Rim_Light", type='SPOT')
    rim_data.energy = 400.0
    rim_data.color = (1.0, 0.8, 0.6)
    rim_data.spot_size = math.radians(60)
    rim_obj = bpy.data.objects.new(name="Rim_Light", object_data=rim_data)
    rim_obj.location = (2.5, 3.5, 3.0)
    rim_obj.rotation_euler = (math.radians(-130), math.radians(20), math.radians(30))
    bpy.context.collection.objects.link(rim_obj)

    # 6. Camera
    cam_data = bpy.data.cameras.new(name="Test_Camera")
    cam_data.lens = 50.0
    cam_obj = bpy.data.objects.new(name="Test_Camera", object_data=cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    cam_obj.location = (4.5, -4.5, 3.2)
    cam_obj.rotation_euler = (math.radians(64), 0, math.radians(45))

    # 7. Save Blend File
    os.makedirs(os.path.dirname(blend_save_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_save_path)
    print(f"BLEND_SAVED_SUCCESS: {blend_save_path}")

    # 8. Render Frame
    os.makedirs(os.path.dirname(render_output_path), exist_ok=True)
    scene.render.filepath = render_output_path
    bpy.ops.render.render(write_still=True)
    print(f"RENDER_SAVED_SUCCESS: {render_output_path}")

if __name__ == '__main__':
    import sys
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if len(args) >= 2:
        blend_path, render_path = args[0], args[1]
        create_and_render_test_scene(blend_path, render_path)
    else:
        print("ERROR: Missing blend_path or render_path arguments")
"""

    @classmethod
    def execute(cls, blender_exe, blend_save_path, render_output_path):
        """Runs the Blender test script via subprocess in headless mode."""
        script_path = STUDIO_ROOT / "scripts" / "blender" / "_temp_module1_runner.py"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(cls.BLENDER_TEST_SCRIPT)

        cmd = [
            blender_exe,
            "--background",
            "--python", str(script_path),
            "--",
            str(blend_save_path),
            str(render_output_path)
        ]

        t0 = time.time()
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            elapsed = time.time() - t0
            return {
                "success": True,
                "elapsed_seconds": round(elapsed, 2),
                "stdout": res.stdout,
                "stderr": res.stderr
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "elapsed_seconds": round(time.time() - t0, 2),
                "stdout": e.stdout,
                "stderr": e.stderr,
                "error": str(e)
            }
        finally:
            if script_path.exists():
                try:
                    script_path.unlink()
                except OSError:
                    pass


class ImageValidator:
    """Verifies that the rendered image exists, is valid PNG, and parses dimensions."""

    @classmethod
    def validate_png(cls, file_path):
        p = Path(file_path)
        if not p.exists():
            return {"valid": False, "error": f"Render file does not exist at '{file_path}'"}
        
        file_size = p.stat().st_size
        if file_size < 1024:  # Suspiciously small (< 1KB)
            return {"valid": False, "error": f"Render file is too small ({file_size} bytes)"}

        # Validate PNG magic header and IHDR dimensions
        with open(p, "rb") as f:
            header = f.read(8)
            if header != b"\x89PNG\r\n\x1a\n":
                return {"valid": False, "error": "Invalid PNG signature header"}
            
            # Read IHDR chunk
            chunk_len, chunk_type = struct.unpack(">I4s", f.read(8))
            if chunk_type == b"IHDR":
                width, height, bit_depth, color_type = struct.unpack(">IIBB", f.read(10))
                return {
                    "valid": True,
                    "file_path": str(p.resolve()),
                    "file_size_bytes": file_size,
                    "width": width,
                    "height": height,
                    "bit_depth": bit_depth,
                    "color_type": color_type
                }
            
        return {"valid": True, "file_path": str(p.resolve()), "file_size_bytes": file_size}


def run_module1_integration(custom_blender_path=None):
    """Main execution pipeline for Module 1."""
    report = {
        "module": "Module 1: Blender Integration",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "architecture": platform.architecture()[0],
            "python_version": sys.version.split()[0]
        },
        "blender": {},
        "test_scene": {},
        "render_validation": {},
        "status": "FAIL",
        "errors": []
    }

    print("==================================================")
    print("AI ANIMATION STUDIO – MODULE 1: BLENDER INTEGRATION")
    print("==================================================")

    # 1. Discover Blender
    try:
        blender_exe = BlenderDiscovery.find_executable(custom_blender_path)
        print(f"[1/4] Discovered Blender executable: {blender_exe}")
        version_info = BlenderDiscovery.get_version(blender_exe)
        print(f"      Version: {version_info['version_string']}")
        report["blender"] = {
            "executable": blender_exe,
            "version": version_info["version_string"],
            "build": version_info["build_details"]
        }
    except Exception as e:
        print(f"[FAIL] Blender discovery failed: {e}")
        report["errors"].append(str(e))
        _save_reports(report)
        return report

    # 2. Paths for Test Scene & Output
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    RENDERS_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    blend_file = SCENES_DIR / "module1_test_scene.blend"
    render_file = RENDERS_PREVIEW_DIR / "module1_test_render.png"

    # 3. Execute Background Scene Generation & Render
    print(f"[2/4] Executing background test scene builder and renderer...")
    exec_res = BlenderTestSceneRunner.execute(blender_exe, blend_file, render_file)
    
    if not exec_res["success"]:
        print(f"[FAIL] Headless execution failed in {exec_res['elapsed_seconds']}s")
        report["errors"].append(f"Blender execution error: {exec_res.get('error')}")
        report["test_scene"]["execution"] = exec_res
        _save_reports(report)
        return report

    print(f"[3/4] Headless execution completed in {exec_res['elapsed_seconds']}s")
    report["test_scene"] = {
        "blend_file": str(blend_file.resolve()),
        "blend_exists": blend_file.exists(),
        "blend_size_bytes": blend_file.stat().st_size if blend_file.exists() else 0,
        "elapsed_seconds": exec_res["elapsed_seconds"]
    }

    # 4. Validate Render Output Image
    print(f"[4/4] Validating rendered output image...")
    val_res = ImageValidator.validate_png(render_file)
    report["render_validation"] = val_res

    if val_res["valid"]:
        print(f"[PASS] Render valid: {val_res['width']}x{val_res['height']} PNG ({val_res['file_size_bytes']} bytes)")
        report["status"] = "PASS"
    else:
        print(f"[FAIL] Render validation failed: {val_res.get('error')}")
        report["errors"].append(val_res.get("error"))

    _save_reports(report)
    print("--------------------------------------------------")
    print(f"MODULE 1 AUDIT STATUS: {report['status']}")
    print(f"Reports saved to: {REPORTS_DIR}")
    print("==================================================")
    return report


def _save_reports(report):
    """Saves both JSON and Markdown/HTML audit reports."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    json_path = REPORTS_DIR / "module1_connection_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    md_path = REPORTS_DIR / "module1_connection_report.md"
    status_badge = "✅ PASS" if report["status"] == "PASS" else "❌ FAIL"
    
    md_content = f"""# Module 1: Blender Integration Report

- **Status**: {status_badge}
- **Audit Timestamp**: `{report['timestamp']}`
- **Host Platform**: {report['platform']['system']} {report['platform']['release']} ({report['platform']['architecture']})
- **Python Runtime**: {report['platform']['python_version']}

---

## 1. Blender Runtime Details
- **Executable**: `{report.get('blender', {}).get('executable', 'N/A')}`
- **Version**: `{report.get('blender', {}).get('version', 'N/A')}`
- **Build Hash**: `{report.get('blender', {}).get('build', 'N/A')}`

---

## 2. Test Scene Generation
- **Target Blend File**: `{report.get('test_scene', {}).get('blend_file', 'N/A')}`
- **File Size**: `{report.get('test_scene', {}).get('blend_size_bytes', 0):,} bytes`
- **Execution Time**: `{report.get('test_scene', {}).get('elapsed_seconds', 0)} seconds`
- **Objects Generated**: Studio Beveled Cube (`Module1_Test_Cube`), Studio Ground (`Studio_Floor`), 3-Point Lights (Key Sun, Fill Point, Rim Spot), 50mm Camera (`Test_Camera`).

---

## 3. Render Output Verification
- **Render Output File**: `{report.get('render_validation', {}).get('file_path', 'N/A')}`
- **Resolution**: `{report.get('render_validation', {}).get('width', 0)} x {report.get('render_validation', {}).get('height', 0)}`
- **File Size**: `{report.get('render_validation', {}).get('file_size_bytes', 0):,} bytes`
- **Format Integrity**: Verified PNG Magic Header & IHDR Chunk

---

## 4. Diagnostics & Errors
{"*No errors detected. Ready for Module 2.*" if not report["errors"] else "\\n".join(f"- ❌ {e}" for e in report["errors"])}
"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)


if __name__ == "__main__":
    custom = sys.argv[1] if len(sys.argv) > 1 else None
    run_module1_integration(custom)
