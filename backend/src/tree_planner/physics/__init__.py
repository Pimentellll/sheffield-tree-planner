"""CPU direct-solar geometry producers. No runtime-agent shell/network capability."""

from .evaluator import (
    compute,
    evaluate_masks,
    build_masks,
    validate_masks,
    source_manifest,
    PhysicsStopped,
    EVALUATOR,
    EVALUATOR_VERSION,
    SOLAR_ALGORITHM,
    SOLAR_VERSION,
)

__all__ = [
    "compute",
    "evaluate_masks",
    "build_masks",
    "validate_masks",
    "source_manifest",
    "PhysicsStopped",
    "EVALUATOR",
    "EVALUATOR_VERSION",
    "SOLAR_ALGORITHM",
    "SOLAR_VERSION",
]
