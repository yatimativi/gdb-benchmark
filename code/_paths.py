"""Repo-relative path constants for the analysis scripts.

All scripts in this directory resolve data locations through the constants
exported here. No absolute paths are hardcoded; everything is anchored at
the repository root via ``Path(__file__).resolve().parent.parent``.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "unified_dataset" / "unified_dataset.csv"
ANN = REPO / "annotations"
EXT = ANN / "external_raters"
LLM = ANN / "llm_judges"
PROBE1 = REPO / "probe1_post_training"
DISCRIM = REPO / "discriminant_2x2"

__all__ = ["REPO", "DATA", "ANN", "EXT", "LLM", "PROBE1", "DISCRIM"]
