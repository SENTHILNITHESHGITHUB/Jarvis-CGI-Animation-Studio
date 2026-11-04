# AI ANIMATION STUDIO - PROJECT RULES

## Main Objective
Build a professional AI-assisted 3D animation and VFX production system.

## Core Software
- Blender for 3D production.
- Python for automation.
- ComfyUI for supported AI generation workflows.
- DaVinci Resolve for final editing.

## Character Integrity
- Maintain fixed character identity.
- Preserve original mesh geometry.
- Preserve body proportions.
- Preserve facial structure.
- Maintain consistent materials and textures.
- Never replace a master character without approval.

## Rigging
- Validate bone hierarchy.
- Validate joint positioning.
- Check skin weights.
- Check deformation in extreme poses.
- Identify collapsing geometry.
- Support corrective shape keys.

## Animation
- Check motion continuity.
- Check foot contact.
- Check joint limits.
- Check root motion.
- Check body proportions between frames.
- Detect sudden position changes.

## Physics
- Check collisions.
- Check cloth intersections.
- Check rigid-body stability.
- Check simulation cache validity.

## Rendering
- Always render a low-resolution preview first.
- Inspect frames before final rendering.
- Keep original scene files.
- Never overwrite master assets.
- Resume interrupted renders where possible.
- Save error reports.

## Quality Control
- Run geometry checks.
- Run animation checks.
- Run material checks.
- Run render checks.
- Record detected errors.
- Attempt safe automatic fixes.
- Recheck every attempted fix.

## Development Safety
- Work in small stages.
- Back up files before modifications.
- Do not delete user assets.
- Do not install packages without explaining why.
- Do not execute destructive commands without permission.
- Do not claim that a test passed unless it was actually executed.

## Final Requirement
Every production stage must have a validation report. Do not mark a scene production-ready if critical checks fail.
