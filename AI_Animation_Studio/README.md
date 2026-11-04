# AI Animation & VFX Studio

Modular AI-assisted 3D animation, rigging validation, motion quality inspection, and VFX production system powered by Google Antigravity, Blender Python API, and automated quality control pipelines.

---

## Architecture Overview

```
AI_Animation_Studio/
├── AGENTS.md                   # Studio production rules and safety constraints
├── README.md                   # Project documentation & operational runbook
├── characters/                 # 3D character assets & deformation baselines
│   ├── references/             # Turnarounds, blueprints & proportion sheets
│   ├── models/                 # Decompressed & cleaned .glb/.fbx meshes
│   ├── textures/               # PBR diffuse, normal, roughness, metallic maps
│   ├── rigs/                   # Rigified/Mixamo armatures & bone hierarchies
│   └── shape_keys/             # Corrective shape keys & blend shapes
├── animation/                  # Motion capture & keyframe sequences
│   ├── mocap/                  # Raw BVH/FBX mocap trajectories
│   ├── keyframes/              # Interpolated pose libraries & action blocks
│   └── sequences/              # Multi-shot timeline actions & walk/wave cycles
├── scenes/                     # 3D environments, stages & lighting
│   ├── environments/           # PBR streets, yards, interiors, backgrounds
│   ├── cameras/                # Lens configs (38mm/50mm portrait), dolly tracks
│   └── lighting/               # 3-point studio setups, HDRI skies, rim spots
├── vfx/                        # Visual effects & simulations
│   ├── particles/              # Sparks, dust, cherry blossom petals
│   ├── cloth/                  # Garment dynamics, collision meshes
│   ├── fluids/                 # Water splashes, smoke, energy auras
│   └── simulations/            # Baked physics caches (.bphys / OpenVDB)
├── scripts/                    # Automation & validation engines
│   ├── blender/                # Blender background runner & scene builders
│   ├── automation/             # Render queue, pipeline orchestrator, SQLite DB
│   └── quality_control/        # Geometry, rigging, motion & render validators
├── renders/                    # Render output tiers
│   ├── previews/               # Fast low-res inspection stills & animations
│   ├── final/                  # Master broadcast-grade exports (1080x1920 / 4K)
│   └── failed/                 # Quarantined bad frames with error metadata
├── reports/                    # Machine-readable JSON & HTML validation audits
└── backups/                    # Automated snapshot revisions of scenes and rigs
```

---

## Modular Implementation Roadmap

- [x] **Module 1: Blender Integration Engine** (Executable discovery, background IPC, scene synthesis, test render & automated audit).
- [ ] **Module 2: Character Integrity & Geometry Inspector** (Non-manifold detection, seam welding, volume preservation, proportion baseline).
- [ ] **Module 3: Rigging & Deformation Validator** (Pose deformation suite, dual quaternion skinning, corrective shape keys).
- [ ] **Module 4: Animation & Motion Inspector** (Discontinuity detector, foot sliding check, ground intersection, root motion).
- [ ] **Module 5: Physics & VFX Validator** (Cloth intersection, simulation stability, cache integrity, material validation).
- [ ] **Module 6: Automated Render Manager** (Multi-tier rendering, render queue, missing frame recovery, disk budget watchdog).
- [ ] **Module 7: Unified Quality-Control Dashboard** (Real-time inspection UI, PASS/WARN/FAIL status, production audit logs).
- [ ] **Module 8: AI Generation Integration** (ComfyUI backend, image-to-video workflow, concept art generation).
- [ ] **Module 9: Motion Capture Pipeline** (BVH/FBX bone retargeting, joint limits, pose smoothing).
