"""
Sampling Strategy Module

This module provides scientific spatial sampling strategies for street view
imagery studies. All strategies are designed to be reproducible and documented.

Available Strategies:
    - GridSampling: Regular grid-based sampling (implemented)
    - RoadNetworkSampling: Road network-aware sampling (coming soon)
    - RandomSampling: Stratified random sampling (planned)
    - OptimizedSampling: Coverage-optimized sampling (planned)

Example:
    >>> from svipro import GridSampling, SamplingConfig
    >>> from shapely.geometry import box
    >>> strategy = GridSampling(SamplingConfig(spacing=100))  # 100m spacing
    >>> points = strategy.generate(box(0, 0, 1000, 1000))
"""

from svipro.sampling.base import SamplingStrategy
from svipro.sampling.grid import GridSampling

__all__ = [
    "SamplingStrategy",
    "GridSampling",
]
