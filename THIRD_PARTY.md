# Runtime dependencies and original asset provenance

All character meshes, anatomy, hair guides and fibers, clothing, materials, lighting, and studio presentation are authored by this project's procedural Blender source. No existing character models, scanned faces, hair assets, photo textures, or environment maps are used.

The user-supplied reference is used only for human visual inspection and optional side-by-side comparison. Blender never loads it. The reference is not included in the source repository.

The web preview uses Google `<model-viewer>` 4.0.0 as a rendering library, vendored in `preview/vendor/model-viewer.min.js`. It is runtime code, not a character asset. Copyright and license notices embedded in that distribution are retained. Blender, Python, Playwright/Chromium, and Cloudflare Tunnel are development/runtime tools, not supplied artwork.
