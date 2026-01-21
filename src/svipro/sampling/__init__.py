"""
Sampling Strategy Module

This module provides scientific spatial sampling strategies for street view
imagery studies. All strategies are designed to be reproducible and documented.

Available Strategies:
    - GridSampling: Regular grid-based sampling
    - RoadNetworkSampling: Road network-aware sampling
    - RandomSampling: Stratified random sampling
    - OptimizedSampling: Coverage-optimized sampling

Example:
    >>> from svipro import GridSampling
    >>> strategy = GridSpacing(spacing=100)  # 100m spacing
    >>> points = strategy.generate(aoi_boundary)
"""

from svipro.sampling.base import SamplingStrategy
from svipro.sampling.grid import GridSampling
from svipro.sampling.road_network import RoadNetworkSampling

__all__ = [
    "SamplingStrategy",
    "GridSampling",
    "RoadNetworkSampling",
]
