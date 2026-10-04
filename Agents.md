# Continuation context — original Blender upper-body portrait

## Identity and requirements

Model identity: GPT-6 Astra Pro. Agent/environment: ColabDev. Key tool: Blender 4.0.2, headless EEVEE. User requests a faithful upper-body reconstruction from the supplied reference, no pre-existing character assets, no photo projection, and natural unseen sides. Do not use image-generation tools. View reference/renders visually rather than analyzing the reference with code.

The user requested 20,000 iterations and a score above 95. Neither is currently achieved. Count only real completed build/render/review cycles, and never mislabel a geometry test as a visual likeness review. The manifest is the authority for completed review count and subjective score.

## Working state

Project: `/home/dev/project/3d/GPT6AstraPro_ColabDev_Blender_RgirlBust`
Build: `/build/GPT6AstraPro_ColabDev_Blender_RgirlBust` (project/build is a symlink).
Branch: `gpt6-astra-pro-colabdev/blender-upper-body`.
Reusable Colab terminal: 1581 in the project workspace. Reuse it with `webterm write 1581 --enter` then `webterm read 1581`; creating extra run terminals can exhaust the shared 32-session limit. Do not stop other projects or the Colab instance.
Task label: `Astra Blender upper-body portrait`.

Development server: port 4326, src/server.py.
Temporary tunnel: https://proceedings-cedar-mentioned-sunset.trycloudflare.com
Logs: logs/server.log, logs/cloudflared.log, logs/rNNN.log.

At the time of this checkpoint, revision 5 is reviewed at 48/100 and revision 6 is rendering. Read the manifest and newest render log to update this state. Revision 6 fixes reversed normals on the orbital rims, irises, volumetric locks, sleeves, and one collar leaf; creates real recessed nostril holes in the constrained face mesh; and lifts the natural hairline.

## Render and inspect

Use `bash src/render.sh --revision N --quality draft --views front,face,three-quarter,side,back --export`. Do not launch the same build twice just to obtain output. Rendering is CPU EEVEE through Xvfb, not Cycles. Draft frames take around a few minutes per view.

Blender requires the Colab resource variables in render.sh. Bare `blender -b` may crash because the relocated scripts/datafiles are not found. BLENDER_SYSTEM_SCRIPTS=/home/dev/.local/sysroot/usr/share/blender/scripts and BLENDER_SYSTEM_DATAFILES=/home/dev/.local/sysroot/usr/share/blender/datafiles.

For native image review, mcp_colabdev.get_image must use workspace_id=/build/GPT6AstraPro_ColabDev_Blender_RgirlBust for images under /build. The project workspace cannot access a symlink escaping into /build through get_image.

`src/publish.py` publishes only after front.png exists and requires a supplied honest visual score and review. Preserve earlier review images under build/revisions, rather than replacing the history. Run browser tests after meaningful GLB or UI updates.

## Geometry and remaining issues

Front=-Y, up=Z. Original face topology uses Blender's constrained Delaunay triangulation with actual eye and nostril loops, merged with lid surfaces. Head and body have separate pose roots. All assets are procedural meshes/materials; reference is for visual inspection only.

Latest reviewed defects (r5): overly stylized face, visible eyelid shading seams, low helmet-like scalp coverage, rigid hair-tip patterns, and insufficient realistic skin/hair detail. Several normals were inward; revision 6 corrects their winding. Do not assume these corrections succeeded before inspecting the render. Earlier back view showed a rear-hair curvature kink, which revision 5 smooths but needs renewed side/back verification.

## Persistence and deployment

GitHub CLI is authenticated as ecooxai. Source repository creation is being performed at this checkpoint. Never print authentication tokens. Store compressed build artifacts inside the project's archive directory before backing up Colab, because /build is outside /home/dev. Do not assume the symlink target is included in a home archive. Do not stop Colab without verifying backup success.
