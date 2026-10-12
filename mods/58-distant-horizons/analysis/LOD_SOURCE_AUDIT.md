# Distant Horizons — GitLab and offline LOD audit

Official upstream: https://gitlab.com/distant-horizons-team/distant-horizons .

Implemented code: tools/distant_horizons_source_audit.py classifies actual GitLab source paths into renderer/GPU, LOD data, caching and world generation; tools/distant_horizons_lod.py builds a weighted min/max/mean heightfield pyramid for offline study from caller-provided heights. Run: https://github.com/murilosuporte5-rgb/Minizin/actions/workflows/distant-horizons-audit.yml .

This is **not** a port of the native Distant Horizons renderer. The original API uses client-side rendering interfaces (OpenGL and Blaze3D); standard Bedrock behavior/resource packs do not expose equivalent native rendering hooks. The generated LOD pyramid is independent of DH's proprietary/internal save format and does not automatically load Minecraft worlds. Further work: map precise source classes and memory budgets, then determine any supported mobile rendering approximation.
