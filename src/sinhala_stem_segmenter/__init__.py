"""Sinhala data-driven stem/rest segmentation."""

from .model import DEFAULT_MODEL_RESOURCE, SegmentResult, SinhalaStemSegmenter
from .unicode import (
    SinhalaCluster,
    is_sinhala_char,
    iter_sinhala_clusters,
    legal_split_offsets,
    normalize_sinhala,
    split_sinhala_clusters,
)

__all__ = [
    "SegmentResult",
    "DEFAULT_MODEL_RESOURCE",
    "SinhalaCluster",
    "SinhalaStemSegmenter",
    "is_sinhala_char",
    "iter_sinhala_clusters",
    "legal_split_offsets",
    "normalize_sinhala",
    "split_sinhala_clusters",
]
