"""UI bootstrap for the synthetic physical runtime: scenario identity + exact scene bytes.

Shared by the Vite dev launcher (frontend/scripts/serve_physical.py) and the single-origin
server (physical_server --frontend-dist). The scene asset is read through the registry's
rights check for public display; the UI verifies its SHA-256 against the SiteBundle before
drawing anything. Every number shown still comes from API jobs, never from this file.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone

LABEL = "Synthetic physical runtime takeover-v1 (authored geometry; not Sheffield)"


def build_session(runtime) -> dict:
    service = runtime.app.state.service
    ref = runtime.scenario_ref
    scenario = service.scenarios.get_scenario(ref)
    inp = scenario.input
    site = service.scenarios.get_site(inp.site_id, inp.scene_revision, inp.semantic_revision)
    asset = next(a for a in site.assets if a.kind == "canopy_physical_scene_v1")
    # Rights-checked read: refused unless the source permits public display.
    scene_bytes = service.assets.read(asset.ref.registry_id, "public_display_status")
    return dict(
        kind="canopy-dev-session",
        label=LABEL,
        scenario_ref=ref.model_dump(mode="json"),
        declaration_asset_id=asset.asset_id,
        declaration_b64=base64.b64encode(scene_bytes).decode("ascii"),
        numerical_source_commit="physical runtime (no external numerical source)",
        started_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
