# GPT-6 Astra Pro · ColabDev · Blender EEVEE — Rgirl upper-body portrait

An original procedural upper-body character study, authored in Blender from one user-supplied visual reference. The project includes editable geometry, head and body pose roots, procedural materials, a portrait lighting setup, EEVEE review renders, a GLB web export, and a responsive revision gallery.

**Status: work in progress.** The live manifest records actual completed visual reviews and subjective scores. The requested 20,000 iterations and above-95 likeness target are not claimed as achieved. Technical rendering checks are separate from visual likeness assessment.

## Original asset provenance

`src/build_portrait.py` constructs the character from mathematical surfaces and original guide curves. No imported character meshes, face scans, hair assets, image textures, or HDRIs are used. The reference is never opened by Blender and is not projected onto the face. Unseen sides are original interpretations.

Runtime dependency details are in `THIRD_PARTY.md`. The web viewer library is third-party code, not a supplied character asset.

## Build

Tested with Blender 4.0.2, Python 3, Xvfb, and Mesa llvmpipe on the ColabDev CPU instance.

```bash
bash src/render.sh --revision 7 --quality draft --views front,face,three-quarter,side,back --export
```

Use a new revision number for a genuine build/render/review cycle. Inspect the output images before publishing a score:

```bash
python src/publish.py 7 --score 50 --title 'Describe the actual revision' --review 'Describe what the actual render shows, including remaining defects.'
```

The example score above is only command syntax, not an assessment of an unbuilt revision. Do not invent review counts or scores. `src/config.json` contains the current shape and lighting parameters; the Git history preserves earlier source milestones.

## Preview

```bash
python src/server.py
```

The gallery serves on port 4326. It refreshes `progress.json` every five seconds, displays the latest render first, and provides an orbitable original GLB, reference comparison, multi-angle renders, review history, download links, and absolute project/build paths.

```bash
python src/test_preview.py
```

Browser tests cover desktop and mobile layouts, image loading, GLB loading, JavaScript errors, and horizontal overflow.

## Paths in the development instance

- Project: `/home/dev/project/3d/GPT6AstraPro_ColabDev_Blender_RgirlBust`
- Build: `/build/GPT6AstraPro_ColabDev_Blender_RgirlBust`
- Latest editable scene: `build/latest/GPT6AstraPro_ColabDev_Blender_RgirlBust.blend`
- Latest web model: `build/latest/GPT6AstraPro_ColabDev_Blender_RgirlBust.glb`

Build artifacts are not tracked on the source branch. Reproduction and continuation context is maintained in `Agents.md`.
